/* Catch-through-registration runner. Never writes the user's battery/state. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static uint64_t ticks, finish_ticks;
static unsigned step_origin;
static bool entered, finished, saved;
static bool follow_through, catch_returned;

static uint32_t rgb(GB_gameboy_t *g, uint8_t r, uint8_t v, uint8_t b)
{
    (void)g;
    return (uint32_t)r << 16 | (uint32_t)v << 8 | b;
}

static unsigned ram(unsigned bank, unsigned address)
{
    return gb.ram[bank * 0x1000 + (address & 0xfff)];
}

static unsigned byte(unsigned address)
{
    if (address >= 0xff80 && address < 0xffff) return gb.hram[address - 0xff80];
    if (address >= 0xff00 && address < 0xff80) return gb.io_registers[address - 0xff00];
    if (address >= 0xc000 && address < 0xd000) return gb.ram[address - 0xc000];
    if (address >= 0xd000 && address < 0xe000)
        return ram(gb.cgb_ram_bank, address);
    fprintf(stderr, "Unsupported observation address: %04x\n", address);
    exit(11);
}

static unsigned remaining(void)
{
    return byte(S_hSampledCryBlocks) | byte(S_hSampledCryBlocks + 1) << 8;
}

static void hex(const uint8_t *p, unsigned length)
{
    putchar('"');
    for (unsigned i = 0; i < length; i++) printf("%02x", p[i]);
    putchar('"');
}

static void record(const char *event, uint64_t now, unsigned pc)
{
    printf("{\"event\":\"%s\",\"t\":%" PRIu64 ",\"pc\":%u,\"bank\":%u,"
           "\"tick\":%u,\"ly\":%u,\"mode\":%u,\"scene\":%u,\"idle\":%u,"
           "\"command\":%u,\"parameter\":%u,\"wait\":%u,\"audio\":%u,"
           "\"remaining\":%u,\"cache\":%u,\"frame_counter\":%u}\n",
           event, now / 2, pc, pc < 0x4000 ? 0 : gb.mbc_rom_bank, byte(0xff9b), byte(0xff44),
           byte(0xff41) & 3, ram(2, S_wPokeAnimSceneIndex), ram(2, S_wPokeAnimIdleFlag),
           ram(2, S_wPokeAnimCommand), ram(2, S_wPokeAnimParameter),
           ram(2, S_wPokeAnimWaitCounter), byte(S_hSampledCryTimer), remaining(),
           ram(4, 0xdff4), ram(0, S_wFrameCounter));
}

static void observe(GB_gameboy_t *g, uint16_t pc, uint8_t opcode)
{
    (void)g; (void)opcode;
    uint64_t now = ticks + (unsigned)(gb.cycles_since_run - step_origin);
    unsigned bank = pc < 0x4000 ? 0 : gb.mbc_rom_bank;
    for (unsigned i = 0; i < sizeof(points) / sizeof(*points); i++) {
        if (points[i].pc != pc || points[i].bank != bank) continue;
        if (!strcmp(points[i].name, "entry")) entered = true;
        if (points[i].owner_only && !entered) continue;
        if (!strcmp(points[i].name, "animation_finished")) {
            finished = true;
            finish_ticks = now;
        }
        if (!strcmp(points[i].name, "catch_return")) catch_returned = true;
        record(points[i].name, now, pc);
    }
}

int main(int argc, char **argv)
{
    if (argc != 5 && argc != 6) return 2;
    follow_through = argc == 6 && !strcmp(argv[5], "follow-through");
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_turbo_mode(&gb, true, true);
    GB_set_pixels_output(&gb, pixels);
    GB_set_rgb_encode_callback(&gb, rgb);
    GB_set_execution_callback(&gb, observe);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    if (gb.pc != P_START || gb.mbc_rom_bank != B_START || gb.cgb_double_speed) return 4;
    unsigned id = ram(0, S_wWildMon);
    unsigned table = S_wPokemonIndexTableEntries - 2 + id * 2;
    unsigned species = ram(2, table) | ram(2, table + 1) << 8;
    if (!species || species > 373) return 5;
    printf("{\"event\":\"initial\",\"pc\":%u,\"bank\":%u,\"af\":%u,\"bc\":%u,"
           "\"de\":%u,\"hl\":%u,\"sp\":%u,\"ime\":%u,\"runtime_id\":%u,"
           "\"species\":%u,\"item\":%u,\"temp_enemy\":%u,\"enemy\":%u,\"party\":%u,"
           "\"seen\":%u,\"caught\":%u,\"double_speed\":%u}\n",
           gb.pc, gb.mbc_rom_bank, gb.af, gb.bc, gb.de, gb.hl, gb.sp, gb.ime,
           id, species, ram(1, S_wCurItem), ram(1, S_wTempEnemyMonSpecies),
           ram(1, S_wEnemyMonSpecies), ram(1, S_wPartyCount),
           !!(ram(1, S_wPokedexSeen + (species - 1) / 8) & (1 << ((species - 1) % 8))),
           !!(ram(1, S_wPokedexCaught + (species - 1) / 8) & (1 << ((species - 1) % 8))),
           gb.cgb_double_speed);
    unsigned last_keys = 256;
    while (ticks < UINT64_C(70224) * 2 * 2400) {
        unsigned keys = entered ? 0 : ((ticks / (70224 * 2) / 12) % 2 ? 16 : 0);
        if (follow_through && finished && ticks - finish_ticks > 70224 * 2 * 12)
            keys = (ticks / (70224 * 2) / 12) % 2 ? GB_KEY_B_MASK : 0;
        if (keys != last_keys) { GB_set_key_mask(&gb, keys); last_keys = keys; }
        if (!saved && gb.pc == P_ENTRY && gb.mbc_rom_bank == B_ENTRY && !gb.halted) {
            GB_set_key_mask(&gb, 0);
            last_keys = 0;
            if (GB_save_state(&gb, argv[3])) return 6;
            saved = true;
        }
        unsigned before = gb.cycles_since_run;
        step_origin = before;
        GB_cpu_run(&gb);
        ticks += (unsigned)(gb.cycles_since_run - before);
        if (follow_through ? catch_returned :
            finished && ticks - finish_ticks > 70224 * 2 * 120 && !byte(S_hSampledCryTimer)) break;
    }
    record("final", ticks, gb.pc);
    printf("{\"event\":\"final_audio\",\"wram4\":");
    hex(gb.ram + 4 * 4096 + 0xff4, 8);
    printf(",\"hram\":"); hex(gb.hram + 0x6e, 6); puts("}");
#ifdef FOLLOW_THROUGH_AUDIT
    unsigned party = ram(1, S_wPartyCount);
    unsigned last_id = ram(1, S_wPartySpecies + party - 1);
    unsigned box_id = gb.mbc_ram[B_sBoxCount * 0x2000 + (S_sBoxSpecies & 0x1fff)];
    unsigned last_at = S_wPokemonIndexTableEntries - 2 + last_id * 2;
    unsigned box_at = S_wPokemonIndexTableEntries - 2 + box_id * 2;
    printf("{\"event\":\"catch_result\",\"returned\":%u,\"party\":%u,\"last_party_species\":%u,"
           "\"box_count\":%u,\"first_box_species\":%u,\"hvblank\":%u,\"frame_counter\":%u,"
           "\"map_anims\":%u,\"scx\":%u,\"caught\":%u}\n",
           catch_returned, party, ram(2, last_at) | ram(2, last_at + 1) << 8,
           gb.mbc_ram[B_sBoxCount * 0x2000 + (S_sBoxCount & 0x1fff)],
           ram(2, box_at) | ram(2, box_at + 1) << 8, byte(S_hVBlank), ram(0, S_wFrameCounter),
           byte(S_hMapAnims), byte(S_hSCX),
           !!(ram(1, S_wPokedexCaught + (species - 1) / 8) & (1 << ((species - 1) % 8))));
#endif
    FILE *image = fopen(argv[4], "wb");
    if (!image) return 7;
    fprintf(image, "P6\n160 144\n255\n");
    for (unsigned i = 0; i < 160 * 144; i++) {
        uint8_t p[] = {pixels[i] >> 16, pixels[i] >> 8, pixels[i]};
        fwrite(p, 1, 3, image);
    }
    fclose(image);
    GB_free(&gb);
    return entered && finished && (!follow_through || catch_returned) ? 0 : 8;
}
