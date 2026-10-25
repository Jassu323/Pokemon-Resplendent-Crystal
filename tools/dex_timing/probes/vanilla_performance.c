/* Read-only normal-input vanilla comparison, using its own linked symbols. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include VANILLA_SYMBOLS

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static uint64_t ticks;
static unsigned step_origin;

static uint32_t rgb(GB_gameboy_t *g, uint8_t r, uint8_t v, uint8_t b)
{
    (void)g;
    return (uint32_t)r << 16 | (uint32_t)v << 8 | b;
}

static unsigned byte(unsigned address)
{
    return GB_read_memory(&gb, address);
}

static unsigned word(unsigned address)
{
    return byte(address) | byte(address + 1) << 8;
}

static void hex(const uint8_t *data, unsigned size)
{
    putchar('"');
    for (unsigned i = 0; i < size; i++) printf("%02x", data[i]);
    putchar('"');
}

#include "performance.c"

static void observe(GB_gameboy_t *g, uint16_t pc, uint8_t opcode)
{
    (void)g; (void)opcode;
    if (!gb.halted) perf_observe(pc < 0x4000 ? 0 : gb.mbc_rom_bank, pc);
}

static bool at(unsigned bank, unsigned pc)
{
    return gb.pc == pc && (pc < 0x4000 || gb.mbc_rom_bank == bank) && !gb.halted;
}

static void snapshot(int hit)
{
    printf("{\"event\":\"stop\",\"hit\":%d,\"t\":%" PRIu64 ",\"pc\":%u,\"bank\":%u,"
           "\"index\":%u,\"menu\":%u,\"mode\":%u,\"cursor\":%u,\"species\":%u,\"ly\":%u}\n",
           hit, ticks / 2, gb.pc, gb.mbc_rom_bank,
           byte(S_wDexListingScrollOffset) + byte(S_wDexListingCursor),
           byte(S_wMenuCursorPosition), byte(S_wCurDexMode),
           byte(S_wDexArrowCursorPosIndex), byte(S_wCurPartySpecies), byte(0xff44));
}

int main(int argc, char **argv)
{
    if (argc != 4) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_turbo_mode(&gb, true, true);
    GB_set_pixels_output(&gb, pixels);
    GB_set_rgb_encode_callback(&gb, rgb);
    GB_set_execution_callback(&gb, observe);
    GB_set_vblank_callback(&gb, perf_frame);
    if (GB_load_rom(&gb, argv[1]) || GB_load_boot_rom(&gb, argv[2]) ||
        GB_load_battery(&gb, argv[3])) return 2;
    setvbuf(stdout, NULL, _IOLBF, 0);
    char line[4096];
    while (fgets(line, sizeof(line), stdin)) {
        unsigned bank, pc, keys;
        uint64_t budget, mask;
        bool direct = sscanf(line, "restorerun %u %u %" SCNu64 " %u", &bank, &pc, &budget, &keys) == 4;
        if (direct || sscanf(line, "run %" SCNu64 " %" SCNu64 " %u", &mask, &budget, &keys) == 3) {
            GB_set_key_mask(&gb, keys);
            uint64_t start = ticks;
            int hit = -1;
            do {
                unsigned before = gb.cycles_since_run;
                step_origin = before;
                GB_cpu_run(&gb);
                ticks += (unsigned)(gb.cycles_since_run - before);
                if (direct && at(bank, pc)) hit = 0;
                else if (!direct) for (unsigned i = 0; i < sizeof(points) / sizeof(*points); i++) {
                    if ((mask & (UINT64_C(1) << i)) && at(points[i].bank, points[i].pc)) { hit = i; break; }
                }
            } while (hit < 0 && ticks - start < budget * 2);
            snapshot(hit);
        } else if (perf_command(line)) {
        } else if (!strcmp(line, "peek\n")) snapshot(-1);
        else if (!strcmp(line, "rawcolor\n")) {
            GB_set_color_correction_mode(&gb, GB_COLOR_CORRECTION_DISABLED);
            puts("{\"event\":\"ok\"}");
        } else if (!strncmp(line, "save ", 5) || !strncmp(line, "load ", 5)) {
            line[strcspn(line, "\r\n")] = 0;
            int error = line[0] == 's' ? GB_save_state(&gb, line + 5) : GB_load_state(&gb, line + 5);
            if (line[0] == 'l') ticks = 0;
            printf("{\"event\":\"ok\",\"error\":%d}\n", error);
        } else if (!strncmp(line, "image ", 6)) {
            line[strcspn(line, "\r\n")] = 0;
            FILE *file = fopen(line + 6, "wb");
            if (!file) return 2;
            fprintf(file, "P6\n160 144\n255\n");
            for (unsigned i = 0; i < 160 * 144; i++) {
                uint8_t p[] = {pixels[i] >> 16, pixels[i] >> 8, pixels[i]};
                fwrite(p, 1, 3, file);
            }
            printf("{\"event\":\"ok\",\"error\":%d}\n", fclose(file));
        } else if (!strcmp(line, "quit\n")) break;
        else return 2;
    }
    GB_free(&gb);
    return 0;
}
