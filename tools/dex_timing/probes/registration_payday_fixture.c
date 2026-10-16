/* Declared pre-enemy data fixture. The real move-ID allocator is executed;
 * no PPU/APU clock, speed, battle-result or readiness state is fabricated. */
#include "Core/gb.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include PAYDAY_FIXTURE_SYMBOLS
static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static void discard(GB_gameboy_t *g, GB_sample_t *s) { (void)g; (void)s; }
static void put(unsigned bank, unsigned at, unsigned value)
{ gb.ram[(at < 0xd000 ? 0 : bank) * 4096 + (at & 4095)] = value; }
int main(int argc, char **argv)
{
    if (argc != 6) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_pixels_output(&gb, pixels); GB_set_sample_rate(&gb, 44100);
    GB_apu_set_sample_callback(&gb, discard); GB_set_turbo_mode(&gb, true, true);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    if (gb.pc != P_ENEMY || gb.mbc_rom_bank != B_ENEMY || gb.cgb_double_speed) return 4;
    uint16_t regs[GB_REGISTERS_16_BIT]; memcpy(regs, gb.registers, sizeof(regs));
    unsigned pc = gb.pc, sp = gb.sp, bank = gb.mbc_rom_bank, wram = gb.cgb_ram_bank;
    gb.sp -= 2; put(0, gb.sp, pc & 255); put(0, gb.sp + 1, pc >> 8);
    gb.hl = 6; gb.pc = P_ALLOCATE;
    unsigned cycles = 0;
    do {
        unsigned before = gb.cycles_since_run; GB_cpu_run(&gb);
        cycles += (unsigned)(gb.cycles_since_run - before);
    } while ((gb.pc != pc || gb.sp != sp || gb.mbc_rom_bank != bank) && cycles < 70224 * 240);
    if (gb.pc != pc || gb.sp != sp || gb.cgb_ram_bank != wram || gb.cgb_double_speed) return 5;
    unsigned id = gb.af >> 8;
    unsigned table = B_wMoveIndexTableEntries * 4096 + (S_wMoveIndexTableEntries & 4095) + 2 * (id - 1);
    if (!id || (gb.ram[table] | gb.ram[table + 1] << 8) != 6) return 6;
    memcpy(gb.registers, regs, sizeof(regs)); gb.pc = pc;
    put(B_wPartyMon1Moves, S_wPartyMon1Moves, id);
    put(B_wPartyMon1PP, S_wPartyMon1PP, 20);
    put(B_wPartyMon1Item, S_wPartyMon1Item, atoi(argv[3]) ? 0x5b : 0);
    put(B_wCurPartyLevel, S_wCurPartyLevel, 10);
    unsigned money = strtoul(argv[4], NULL, 10);
    for (unsigned i = 0; i < 3; i++) put(B_wMoney, S_wMoney + i, (money >> (16 - i * 8)) & 255);
    if (GB_save_state(&gb, argv[5])) return 7;
    printf("{\"move_index\":6,\"allocated_id\":%u,\"allocator_cpu_t\":%u,\"enemy_level\":10,\"coin\":%u,\"balance\":%u}\n",
           id, cycles / 2, !!atoi(argv[3]), money);
    GB_free(&gb);
}
