/* Generated species contexts on matching native, post-Dex checkpoints.
 * The real index allocator runs before changing only declared species/flags.
 * This tool never touches a battery save, timing counters or ready flags. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include PERF_AUDIO_FIXTURE_SYMBOLS

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static void discard_sample(GB_gameboy_t *g, GB_sample_t *sample) { (void)g; (void)sample; }
static void put(unsigned bank, unsigned address, unsigned value)
{ gb.ram[bank * 4096 + (address & 4095)] = value; }

int main(int argc, char **argv)
{
    if (argc != 6 || !strcmp(argv[2], argv[5])) return 2;
    unsigned index = atoi(argv[3]);
    const char *mode = argv[4];
    if (!index || index > 373) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_pixels_output(&gb, pixels);
    GB_set_sample_rate(&gb, 44100);
    GB_apu_set_sample_callback(&gb, discard_sample);
    GB_set_turbo_mode(&gb, true, true);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    if (gb.sp < 0xc020 || gb.sp > 0xc0ff) return 4;
    bool speed = gb.cgb_double_speed;
    unsigned pc = gb.pc, sp = gb.sp, bank = gb.mbc_rom_bank, wram = gb.cgb_ram_bank;
    bool party = !strcmp(mode, "party") || !strcmp(mode, "blocking") || !strcmp(mode, "stereo") || !strcmp(mode, "altered");
    bool enemy = !strcmp(mode, "encounter") || !strcmp(mode, "player");
    if ((!party && !enemy) || (party && (pc != P_PARTY || bank != B_PARTY)) ||
        (enemy && (pc != P_ENEMY || bank != B_ENEMY))) return 5;
    uint16_t registers[GB_REGISTERS_16_BIT];
    memcpy(registers, gb.registers, sizeof(registers));
    gb.sp -= 2;
    put(0, gb.sp, pc & 255);
    put(0, gb.sp + 1, pc >> 8);
    gb.hl = index;
    gb.pc = P_ALLOCATE;
    uint64_t cycles = 0;
    while (cycles < 70224 * 2 * 120) {
        unsigned before = gb.cycles_since_run;
        GB_cpu_run(&gb);
        cycles += (unsigned)(gb.cycles_since_run - before);
        if (gb.pc == pc && gb.sp == sp && gb.mbc_rom_bank == bank) break;
    }
    if (gb.pc != pc || gb.sp != sp || gb.cgb_ram_bank != wram || gb.cgb_double_speed != speed) return 6;
    unsigned id = gb.af >> 8;
    unsigned at = 2 * 4096 + (S_wPokemonIndexTableEntries & 4095) + 2 * (id - 1);
    if (!id || (gb.ram[at] | gb.ram[at + 1] << 8) != index) return 7;
    memcpy(gb.registers, registers, sizeof(registers));
    gb.pc = pc;
    if (party || !strcmp(mode, "player")) {
        put(B_wPartySpecies, S_wPartySpecies, id);
        put(B_wPartyMon1Species, S_wPartyMon1Species, id);
    } else if (!strcmp(mode, "encounter")) {
        put(B_wTempEnemyMonSpecies, S_wTempEnemyMonSpecies, id);
        put(B_wWildMon, S_wWildMon, id);
    } else return 8;
    unsigned mask = 1u << ((index - 1) % 8);
    gb.ram[B_wPokedexCaught * 4096 + (S_wPokedexCaught & 4095) + (index - 1) / 8] &= ~mask;
    gb.ram[B_wPokedexSeen * 4096 + (S_wPokedexSeen & 4095) + (index - 1) / 8] |= mask;
    if (index == 201) put(B_wUnlockedUnowns, S_wUnlockedUnowns, 1);
    if (!strcmp(mode, "blocking") || !strcmp(mode, "stereo")) {
        /* Exercise the real blocking wrapper from a native menu donor. This
         * is shared-routine coverage, not a fabricated hatch/PC UI replay. */
        gb.sp -= 2;
        put(0, gb.sp, pc & 255);
        put(0, gb.sp + 1, pc >> 8);
        gb.af = (id << 8) | (gb.af & 255);
        gb.pc = !strcmp(mode, "blocking") ? P_CRY : P_STEREO;
    }
#ifdef P_LOAD
    if (!strcmp(mode, "altered")) {
        /* Shared-routine odd-period coverage at double speed, not a claim
         * that fainting normally occurs in an overworld party menu. */
        gb.sp -= 2;
        put(0, gb.sp, pc & 255);
        put(0, gb.sp + 1, pc >> 8);
        gb.af = (id << 8) | (gb.af & 255);
        gb.pc = P_LOAD;
        cycles = 0;
        while (cycles < 70224 * 2 * 120) {
            unsigned before = gb.cycles_since_run;
            GB_cpu_run(&gb);
            cycles += (unsigned)(gb.cycles_since_run - before);
            if (gb.pc == pc && gb.sp == sp && gb.mbc_rom_bank == bank) break;
        }
        if (gb.pc != pc || gb.sp != sp || !(gb.af & 0x10) || (gb.af >> 8) != 1) return 10;
        gb.sp -= 2;
        put(0, gb.sp, pc & 255);
        put(0, gb.sp + 1, pc >> 8);
        gb.sp -= 2;
        put(0, gb.sp, P_WAIT & 255);
        put(0, gb.sp + 1, P_WAIT >> 8);
        gb.bc = (gb.bc & 0xff00) | 213;
        gb.pc = P_PERIOD;
    }
#endif
    if (GB_save_state(&gb, argv[5])) return 9;
    printf("{\"generated\":true,\"index\":%u,\"id\":%u,\"allocator_t\":%" PRIu64
           ",\"apu_lf_div\":%u,\"speed\":%u}\n", index, id, cycles / 2, gb.apu.lf_div, gb.cgb_double_speed);
    GB_free(&gb);
    return 0;
}
