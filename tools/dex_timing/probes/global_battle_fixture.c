/* Private native-battle checkpoint factory. Only declared battle/party fields
 * change; actual indexed-move allocation runs on the unmodified cartridge. */
#include "Core/gb.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include GLOBAL_BATTLE_SYMBOLS

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static void discard(GB_gameboy_t *g, GB_sample_t *s) { (void)g; (void)s; }
static void put(unsigned bank, unsigned at, unsigned v)
{ gb.ram[(at < 0xd000 ? 0 : bank) * 4096 + (at & 4095)] = v; }
static unsigned get(unsigned bank, unsigned at)
{ return gb.ram[(at < 0xd000 ? 0 : bank) * 4096 + (at & 4095)]; }
static void word(unsigned bank, unsigned at, unsigned v)
{ put(bank, at, v >> 8); put(bank, at + 1, v & 255); }
static unsigned allocate(unsigned index)
{
    unsigned pc = gb.pc, sp = gb.sp, bank = gb.mbc_rom_bank;
    unsigned wram = gb.cgb_ram_bank;
    bool speed = gb.cgb_double_speed;
    uint16_t registers[GB_REGISTERS_16_BIT];
    memcpy(registers, gb.registers, sizeof(registers));
    gb.sp -= 2;
    put(0, gb.sp, pc & 255); put(0, gb.sp + 1, pc >> 8);
    gb.hl = index; gb.pc = P_ALLOCATE;
    for (unsigned i = 0; i < 300000; i++) {
        GB_cpu_run(&gb);
        if (gb.pc == pc && gb.sp == sp && gb.mbc_rom_bank == bank) break;
    }
    if (gb.pc != pc || gb.sp != sp || gb.cgb_ram_bank != wram || gb.cgb_double_speed != speed) exit(6);
    unsigned id = gb.af >> 8;
    unsigned at = S_wMoveIndexTableEntries + 2 * (id - 1);
    if (!id || (get(B_wMoveIndexTableEntries, at) | get(B_wMoveIndexTableEntries, at + 1) << 8) != index) exit(7);
    memcpy(gb.registers, registers, sizeof(registers));
    return id;
}

int main(int argc, char **argv)
{
    if ((argc != 6 && argc != 7) || !strcmp(argv[2], argv[5])) return 2;
    bool coherent = argc == 7 && !strcmp(argv[6], "coherent");
    if (argc == 7 && !coherent) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_pixels_output(&gb, pixels);
    GB_set_sample_rate(&gb, 44100);
    GB_apu_set_sample_callback(&gb, discard);
    GB_set_turbo_mode(&gb, true, true);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    if (gb.sp < 0xc020 || gb.sp > 0xc0ff || !get(B_wBattleMode, S_wBattleMode)) return 4;
    unsigned target = allocate(atoi(argv[3]));
    put(B_wBattleMonMoves, S_wBattleMonMoves, target);
    unsigned idle = allocate(150); /* Splash is the harmless other-side control. */
    bool foe = !strcmp(argv[4], "foe");
    unsigned player_move = foe ? idle : target, foe_move = foe ? target : idle;
    for (unsigned i = 0; i < 4; i++) {
        put(B_wBattleMonMoves, S_wBattleMonMoves + i, i ? 0 : player_move);
        put(B_wEnemyMonMoves, S_wEnemyMonMoves + i, i ? 0 : foe_move);
        put(B_wPartyMon1Moves, S_wPartyMon1Moves + i, i ? 0 : player_move);
        put(B_wBattleMonPP, S_wBattleMonPP + i, i ? 0 : 60);
        put(B_wEnemyMonPP, S_wEnemyMonPP + i, i ? 0 : 60);
        put(B_wPartyMon1PP, S_wPartyMon1PP + i, i ? 0 : 60);
    }
    put(B_wBattleMonLevel, S_wBattleMonLevel, 50);
    put(B_wEnemyMonLevel, S_wEnemyMonLevel, 50);
    put(B_wPartyMon1Level, S_wPartyMon1Level, 50);
    put(B_wBattleMonStatus, S_wBattleMonStatus, 0);
    put(B_wEnemyMonStatus, S_wEnemyMonStatus, 0);
    put(B_wPartyMon1Status, S_wPartyMon1Status, 0);
    word(B_wBattleMonHP, S_wBattleMonHP, 900);
    word(B_wEnemyMonHP, S_wEnemyMonHP, 900);
    word(B_wPartyMon1HP, S_wPartyMon1HP, 900);
    word(B_wBattleMonMaxHP, S_wBattleMonMaxHP, 1000);
    word(B_wEnemyMonMaxHP, S_wEnemyMonMaxHP, 1000);
    word(B_wPartyMon1MaxHP, S_wPartyMon1MaxHP, 1000);
    for (unsigned i = 0; i < 5; i++) {
        word(B_wBattleMonStats, S_wBattleMonStats + 2 * i, i == 2 ? 200 : (i % 3 == 1 ? 200 : 80));
        word(B_wEnemyMonStats, S_wEnemyMonStats + 2 * i, i == 2 ? 100 : (i % 3 == 1 ? 200 : 80));
        /* Critical hits read the unmodified stats, not just the battle copy. */
        if (coherent) {
            unsigned player = i == 2 ? 200 : (i % 3 == 1 ? 200 : 80);
            unsigned enemy = i == 2 ? 100 : (i % 3 == 1 ? 200 : 80);
            word(B_wPlayerStats, S_wPlayerStats + 2 * i, player);
            word(B_wEnemyStats, S_wEnemyStats + 2 * i, enemy);
            word(B_wPartyMon1Stats, S_wPartyMon1Stats + 2 * i, player);
        }
        put(B_wPlayerSubStatus1, S_wPlayerSubStatus1 + i, 0);
        put(B_wEnemySubStatus1, S_wEnemySubStatus1 + i, 0);
    }
    for (unsigned i = 0; i < 8; i++) {
        put(B_wPlayerStatLevels, S_wPlayerStatLevels + i, i == 5 ? 13 : 7);
        put(B_wEnemyStatLevels, S_wEnemyStatLevels + i, i == 5 ? 13 : 7);
    }
    for (unsigned i = 0; i < 2; i++) {
        put(B_wBattleMonType, S_wBattleMonType + i, 21); /* Water: no Ghost immunity. */
        put(B_wEnemyMonType, S_wEnemyMonType + i, 21);
    }
    put(B_wBattleWeather, S_wBattleWeather, 0);
    if (GB_save_state(&gb, argv[5])) return 8;
    printf("{\"fixture\":true,\"move_index\":%u,\"target_id\":%u,\"foe\":%u,\"speed\":%u}\n",
           (unsigned)atoi(argv[3]), target, foe, gb.cgb_double_speed);
    GB_free(&gb);
}
