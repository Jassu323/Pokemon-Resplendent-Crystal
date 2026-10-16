/* Generated contexts at a matching-link native registration call boundary.
 * Only the species allocator, declared identity/seen flags and form DVs change.
 * No renderer, ready flag, clock, dictionary or playback state is repaired. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include INTERACTIVE_FIXTURE_SYMBOLS

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static void discard_sample(GB_gameboy_t *g, GB_sample_t *s) { (void)g; (void)s; }
static void put(unsigned bank, unsigned at, unsigned value)
{ gb.ram[(at < 0xd000 ? 0 : bank) * 4096 + (at & 4095)] = value; }

int main(int argc, char **argv)
{
    if (argc != 6 || !strcmp(argv[2], argv[5])) return 2;
    unsigned index = strtoul(argv[3], NULL, 10), form = strtoul(argv[4], NULL, 10);
    if (!index || index > 373 || form > 26 || (form && index != 201)) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_pixels_output(&gb, pixels);
    GB_set_sample_rate(&gb, 44100);
    GB_apu_set_sample_callback(&gb, discard_sample);
    GB_set_turbo_mode(&gb, true, true);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    if (gb.pc != P_ENTRY || gb.mbc_rom_bank != B_ENTRY || !gb.cgb_double_speed) return 4;
    uint16_t registers[GB_REGISTERS_16_BIT];
    memcpy(registers, gb.registers, sizeof(registers));
    unsigned sp = gb.sp, bank = gb.mbc_rom_bank, wram = gb.cgb_ram_bank;
    gb.sp -= 2;
    put(0, gb.sp, P_ENTRY & 255); put(0, gb.sp + 1, P_ENTRY >> 8);
    gb.hl = index; gb.pc = P_ALLOCATE;
    uint64_t cycles = 0;
    do {
        unsigned before = gb.cycles_since_run;
        GB_cpu_run(&gb);
        cycles += (unsigned)(gb.cycles_since_run - before);
    } while (!(gb.pc == P_ENTRY && gb.sp == sp && gb.mbc_rom_bank == bank) &&
             cycles < 70224 * 2 * 120);
    if (gb.pc != P_ENTRY || gb.sp != sp || gb.cgb_ram_bank != wram || !gb.cgb_double_speed) return 5;
    unsigned id = gb.af >> 8;
    unsigned at = 2 * 4096 + (S_wPokemonIndexTableEntries & 4095) + 2 * (id - 1);
    if (!id || id >= 0xfd || (gb.ram[at] | gb.ram[at + 1] << 8) != index) return 6;
    memcpy(gb.registers, registers, sizeof(registers)); gb.pc = P_ENTRY;
    for (unsigned i = 0; i < sizeof(identity_fields) / sizeof(*identity_fields); i++)
        put(identity_fields[i].bank, identity_fields[i].address, id);
    unsigned mask = 1u << ((index - 1) % 8);
    gb.ram[B_wPokedexCaught * 4096 + (S_wPokedexCaught & 4095) + (index - 1) / 8] |= mask;
    gb.ram[B_wPokedexSeen * 4096 + (S_wPokedexSeen & 4095) + (index - 1) / 8] |= mask;
    if (form) {
        /* The game divides the packed middle DV bits by ten to select A-Z. */
        unsigned value = (form - 1) * 10;
        unsigned a = (value >> 6 & 3) << 1, d = (value >> 4 & 3) << 1;
        unsigned s = (value >> 2 & 3) << 1, c = (value & 3) << 1;
        put(B_wEnemyMonDVs, S_wEnemyMonDVs, a << 4 | d);
        put(B_wEnemyMonDVs, S_wEnemyMonDVs + 1, s << 4 | c);
        put(B_wUnownLetter, S_wUnownLetter, form);
    }
    if (GB_save_state(&gb, argv[5])) return 7;
    printf("{\"generated\":true,\"index\":%u,\"form\":%u,\"id\":%u,\"allocator_t\":%" PRIu64 "}\n",
           index, form, id, cycles / 2);
    GB_free(&gb);
    return 0;
}
