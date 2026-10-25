/* Declared RAM-data fixtures on a matching native encounter checkpoint. */
#include "Core/gb.h"
#include <stdio.h>
#include <stdlib.h>
#include GOTCHA_FIXTURE_SYMBOLS
static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static void discard(GB_gameboy_t *g, GB_sample_t *s) { (void)g; (void)s; }
int main(int argc, char **argv)
{
    if (argc != 5) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_pixels_output(&gb, pixels);
    GB_set_sample_rate(&gb, 44100);
    GB_apu_set_sample_callback(&gb, discard);
    if (GB_load_rom(&gb, argv[1]) || GB_load_state(&gb, argv[2])) return 3;
    if (gb.pc != P_ENCOUNTER || gb.mbc_rom_bank != B_ENCOUNTER || gb.cgb_double_speed) return 4;
    FILE *patch = fopen(argv[3], "rb");
    if (!patch) return 5;
    unsigned records = 0;
    uint8_t header[5];
    size_t header_size;
    while ((header_size = fread(header, 1, 5, patch))) {
        if (header_size != 5) return 8;
        unsigned bank = header[0], at = header[1] | header[2] << 8;
        unsigned size = header[3] | header[4] << 8;
        if (bank > 7 || !size || at < 0xc000 || at + size > 0xe000 ||
            (at < 0xd000 && at + size > 0xd000)) return 6;
        uint8_t *target = gb.ram + (at < 0xd000 ? at - 0xc000 : bank * 4096 + at - 0xd000);
        if (fread(target, 1, size, patch) != size) return 7;
        records++;
    }
    if (!feof(patch)) return 8;
    fclose(patch);
    if (GB_save_state(&gb, argv[4])) return 9;
    printf("{\"records\":%u,\"cpu_ppu_audio_clock_unchanged\":true}\n", records);
    GB_free(&gb);
}
