/* Explicit private scenario fields only. CPU, PPU, speed and APU are retained. */
#include "Core/gb.h"
#include <stdio.h>
#include <string.h>
#include GLOBAL_GAMEPLAY_SYMBOLS
static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static void discard(GB_gameboy_t *g, GB_sample_t *s) { (void)g; (void)s; }
static void put(unsigned bank, unsigned at, unsigned value)
{ gb.ram[(at < 0xd000 ? 0 : bank) * 4096 + (at & 4095)] = value; }
static unsigned get(unsigned bank, unsigned at)
{ return gb.ram[(at < 0xd000 ? 0 : bank) * 4096 + (at & 4095)]; }
int main(int argc, char **argv)
{
    if (argc != 5 || !strcmp(argv[2], argv[4])) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_pixels_output(&gb, pixels);
    GB_set_sample_rate(&gb, 44100);
    GB_apu_set_sample_callback(&gb, discard);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    if (!strcmp(argv[3], "phone")) {
        put(B_wReceiveCallDelay_MinsRemaining, S_wReceiveCallDelay_MinsRemaining, 0);
        put(B_wTimeCyclesSinceLastCall, S_wTimeCyclesSinceLastCall, 3);
        for (unsigned i = 0; i < 10; i++)
            put(B_wPhoneList, S_wPhoneList + i, i == 0 ? 15 : (i == 1 ? 16 : 0));
    } else if (!strcmp(argv[3], "postbattle-level")) {
        put(B_wPartyMon1Level, S_wPartyMon1Level, 6);
        put(B_wPartyMon1Exp, S_wPartyMon1Exp, 0);
        put(B_wPartyMon1Exp, S_wPartyMon1Exp + 1, 1);
        put(B_wPartyMon1Exp, S_wPartyMon1Exp + 2, 86); /* 342: one below level 7. */
    } else if (!strcmp(argv[3], "level") || !strcmp(argv[3], "egg")) {
        bool egg = !strcmp(argv[3], "egg");
        put(B_wPartyMon1Level, S_wPartyMon1Level, egg ? 5 : 6);
        for (unsigned i = 0; i < 3; i++)
            put(B_wPartyMon1Exp, S_wPartyMon1Exp + i, i == 2 ? (egg ? 125 : 216) : 0);
        if (egg) {
            put(B_wPartySpecies, S_wPartySpecies, 0xfd);
            put(B_wPartyMon1Happiness, S_wPartyMon1Happiness, 1);
            put(B_wStepCount, S_wStepCount, 127);
            put(B_wRepelEffect, S_wRepelEffect, 200);
        }
    } else if (!strcmp(argv[3], "full-party")) {
        put(B_wPartyCount, S_wPartyCount, 6);
        unsigned size = S_wPartyMon2 - S_wPartyMon1;
        unsigned species = get(B_wPartyMon1Species, S_wPartyMon1Species);
        for (unsigned n = 4; n < 6; n++) {
            put(B_wPartySpecies, S_wPartySpecies + n, species);
            for (unsigned i = 0; i < size; i++)
                put(B_wPartyMon1, S_wPartyMon1 + n * size + i, get(B_wPartyMon1, S_wPartyMon1 + i));
            for (unsigned i = 0; i < 11; i++) {
                put(B_wPartyMon1Nickname, S_wPartyMon1Nickname + n * 11 + i,
                    get(B_wPartyMon1Nickname, S_wPartyMon1Nickname + i));
                put(B_wPartyMon1OT, S_wPartyMon1OT + n * 11 + i,
                    get(B_wPartyMon1OT, S_wPartyMon1OT + i));
            }
        }
        put(B_wPartySpecies, S_wPartySpecies + 6, 255);
    } else if (!strcmp(argv[3], "loss")) {
        /* Native one-Pokemon defeat: low HP and sleep, not an injected result. */
        put(B_wPartyCount, S_wPartyCount, 1);
        put(B_wPartySpecies, S_wPartySpecies + 1, 255);
        put(B_wPartyMon1, S_wPartyMon1 + 34, 0);
        put(B_wPartyMon1, S_wPartyMon1 + 35, 1);
        put(B_wPartyMon1, S_wPartyMon1 + 32, 3);
#ifdef S_wBattleMonHP
        put(B_wBattleMonHP, S_wBattleMonHP, 0);
        put(B_wBattleMonHP, S_wBattleMonHP + 1, 1);
        put(B_wBattleMonStatus, S_wBattleMonStatus, 3);
#endif
    } else return 4;
    if (GB_save_state(&gb, argv[4])) return 5;
    printf("{\"fixture\":\"%s\",\"speed\":%u}\n", argv[3], gb.cgb_double_speed);
    GB_free(&gb);
}
