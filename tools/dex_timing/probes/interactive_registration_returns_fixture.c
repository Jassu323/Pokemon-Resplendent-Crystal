/* Private data fixtures and explicitly labeled direct GC coverage only. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include RETURNS_FIXTURE_SYMBOLS

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static void discard(GB_gameboy_t *g, GB_sample_t *s) { (void)g; (void)s; }
static void put(unsigned bank, unsigned at, unsigned value)
{ gb.ram[(at < 0xd000 ? 0 : bank) * 4096 + (at & 4095)] = value; }

static uint64_t invoke(unsigned pc, unsigned bank, unsigned af, unsigned hl)
{
    uint16_t registers[GB_REGISTERS_16_BIT];
    memcpy(registers, gb.registers, sizeof(registers));
    unsigned origin = gb.pc, sp = gb.sp, rom = gb.mbc_rom_bank, wram = gb.cgb_ram_bank;
    bool speed = gb.cgb_double_speed;
    gb.sp -= 2;
    put(0, gb.sp, origin & 255); put(0, gb.sp + 1, origin >> 8);
    gb.af = af; gb.hl = hl;
    if (bank) { gb.af = bank << 8; gb.hl = pc; gb.pc = P_FARCALL; }
    else gb.pc = pc;
    uint64_t cycles = 0;
    do {
        unsigned before = gb.cycles_since_run;
        GB_cpu_run(&gb);
        cycles += (unsigned)(gb.cycles_since_run - before);
    } while (!(gb.pc == origin && gb.sp == sp && gb.mbc_rom_bank == rom) &&
             cycles < 70224 * 2 * 120);
    if (gb.pc != origin || gb.sp != sp || gb.mbc_rom_bank != rom ||
        gb.cgb_ram_bank != wram || gb.cgb_double_speed != speed) exit(10);
    unsigned result = gb.af;
    memcpy(gb.registers, registers, sizeof(registers));
    gb.pc = origin;
    return ((uint64_t)result << 48) | cycles;
}

int main(int argc, char **argv)
{
    if (argc != 8 || !strcmp(argv[2], argv[7])) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_pixels_output(&gb, pixels); GB_set_sample_rate(&gb, 44100);
    GB_apu_set_sample_callback(&gb, discard); GB_set_turbo_mode(&gb, true, true);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    unsigned bank = strtoul(argv[3], NULL, 0), pc = strtoul(argv[4], NULL, 0);
    if (gb.pc != pc || (pc >= 0x4000 && gb.mbc_rom_bank != bank) ||
        !((pc == P_ENCOUNTER && bank == B_ENCOUNTER) ||
          (pc == P_OVERWORLD && bank == B_OVERWORLD) ||
          (pc == P_INPUT && bank == B_INPUT))) return 4;
    uint64_t elapsed = 0;
    if (!strcmp(argv[5], "history")) {
        uint64_t allocated = invoke(P_ALLOCATE, 0, 0, 373);
        unsigned id = allocated >> 56;
        if (!id || id >= 0xfd) return 5;
        elapsed += allocated & UINT64_C(0xffffffffffff);
        elapsed += invoke(P_LOCK, 0, id << 8, LOCK_POSITION) & UINT64_C(0xffffffffffff);
        if (pc == P_OVERWORLD && bank == B_OVERWORLD)
            elapsed += invoke(P_VISIBLE, B_VISIBLE, 0, 0) & UINT64_C(0xffffffffffff);
    } else if (!strcmp(argv[5], "gc")) {
        if (pc != P_INPUT || bank != B_INPUT) return 5;
        for (unsigned index = 300; index < 373; index++)
            elapsed += invoke(P_ALLOCATE, 0, 0, index) & UINT64_C(0xffffffffffff);
        elapsed += invoke(P_GC, B_GC, 0, 0) & UINT64_C(0xffffffffffff);
    } else if (strcmp(argv[5], "patch")) return 5;
    FILE *patch = fopen(argv[6], "rb");
    if (!patch) return 6;
    uint8_t header[5]; unsigned records = 0; size_t n;
    while ((n = fread(header, 1, 5, patch))) {
        unsigned b = header[0], at = header[1] | header[2] << 8;
        unsigned size = header[3] | header[4] << 8;
        if (n != 5 || b > 7 || !size || at < 0xc000 || at + size > 0xe000 ||
            (at < 0xd000 && at + size > 0xd000)) return 7;
        uint8_t *target = gb.ram + (at < 0xd000 ? at - 0xc000 : b * 4096 + at - 0xd000);
        if (fread(target, 1, size, patch) != size) return 8;
        records++;
    }
    if (!feof(patch)) return 8;
    fclose(patch);
    if (GB_save_state(&gb, argv[7])) return 9;
    printf("{\"records\":%u,\"direct_routine_cpu_cycles\":%" PRIu64
           ",\"registers_stack_banks_restored\":true}\n", records, elapsed);
    GB_free(&gb);
}
