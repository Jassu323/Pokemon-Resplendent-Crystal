/* Generated registration-entry fixtures, NOT authentic catch captures.
 * Allocate an ID through the game's real allocator, then replace only the
 * incoming species context. No animation-ready flags, VRAM, or timing repairs.
 * Never run this tool against a live battery save or overwrite its donor. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static GB_gameboy_t gb;
static void put(unsigned bank, unsigned address, unsigned value)
{ gb.ram[bank * 4096 + (address & 4095)] = value; }

int main(int argc, char **argv)
{
    if (argc != 5 || !strcmp(argv[2], argv[4])) return 2;
    unsigned index = atoi(argv[3]);
    if (!index || index > 373) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_turbo_mode(&gb, true, true);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    if (gb.pc != P_ENTRY || gb.mbc_rom_bank != B_ENTRY || gb.cgb_double_speed) return 4;
    uint16_t registers[GB_REGISTERS_16_BIT];
    memcpy(registers, gb.registers, sizeof(registers));
    unsigned sp = gb.sp, bank = gb.mbc_rom_bank, wram_bank = gb.cgb_ram_bank;
    /* A real CALL with the entry PC as its return sentinel. */
    gb.sp -= 2;
    put(0, gb.sp, P_ENTRY & 255);
    put(0, gb.sp + 1, P_ENTRY >> 8);
    gb.hl = index;
    gb.pc = P_ALLOCATE;
    uint64_t cycles = 0;
    while (cycles < 70224 * 2 * 120) {
        unsigned before = gb.cycles_since_run;
        GB_cpu_run(&gb);
        cycles += (unsigned)(gb.cycles_since_run - before);
        if (gb.pc == P_ENTRY && gb.sp == sp && gb.mbc_rom_bank == bank) break;
    }
    if (gb.pc != P_ENTRY || gb.sp != sp || gb.cgb_ram_bank != wram_bank) return 5;
    unsigned id = gb.af >> 8;
    unsigned at = 2 * 4096 + (S_wPokemonIndexTableEntries & 4095) + 2 * (id - 1);
    if (!id || (gb.ram[at] | gb.ram[at + 1] << 8) != index) return 6;
    memcpy(gb.registers, registers, sizeof(registers));
    gb.pc = P_ENTRY;
#define SPECIES(field) put(B_##field, S_##field, id)
    SPECIES(wCurSpecies); SPECIES(wCurPartySpecies); SPECIES(wTempSpecies);
    SPECIES(wNamedObjectIndex); SPECIES(wTempEnemyMonSpecies); SPECIES(wEnemyMonSpecies);
    SPECIES(wWildMon);
#undef SPECIES
    unsigned mask = 1u << ((index - 1) % 8);
    gb.ram[B_wPokedexCaught * 4096 + (S_wPokedexCaught & 4095) + (index - 1) / 8] |= mask;
    gb.ram[B_wPokedexSeen * 4096 + (S_wPokedexSeen & 4095) + (index - 1) / 8] |= mask;
    if (index == 201) {
        put(B_wUnownLetter, S_wUnownLetter, 1);
        put(B_wEnemyMonDVs, S_wEnemyMonDVs, 0);
        put(B_wEnemyMonDVs, S_wEnemyMonDVs + 1, 0);
    }
    if (GB_save_state(&gb, argv[4])) return 7;
    printf("{\"generated\":true,\"index\":%u,\"id\":%u,\"allocator_t\":%" PRIu64 "}\n",
           index, id, cycles / 2);
    GB_free(&gb);
    return 0;
}
