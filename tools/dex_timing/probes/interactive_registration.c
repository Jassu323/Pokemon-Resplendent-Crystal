/* Host-only extension of the established native input observer. */
#include "Core/gb.h"
#include <stdio.h>
static void interactive_execution(GB_gameboy_t *, GB_execution_callback_t);
static void interactive_vblank(GB_gameboy_t *, GB_vblank_callback_t);
static char *interactive_fgets(char *, int, FILE *);
#define GB_set_execution_callback interactive_execution
#define GB_set_vblank_callback interactive_vblank
#define main interactive_base_main
#define fgets interactive_fgets
#include "cold_listing.c"
#undef fgets
#undef main
#undef GB_set_execution_callback
#undef GB_set_vblank_callback
#include INTERACTIVE_SYMBOLS

static GB_execution_callback_t original_execution;
static GB_vblank_callback_t original_vblank;
static unsigned interactive_reference_count;
static uint8_t (*interactive_references)[49 * 16];

static char *interactive_fgets(char *line, int size, FILE *stream)
{
    while (fgets(line, size, stream)) {
        char path[2048];
        if (sscanf(line, "interactive_refs %2047s", path) != 1) return line;
        FILE *input = fopen(path, "rb");
        if (!input) { perror(path); exit(12); }
        int count = fgetc(input);
        if (count < 1 || count > 255) exit(12);
        free(interactive_references);
        interactive_references = malloc((unsigned)count * 49 * 16);
        if (!interactive_references || fread(interactive_references, 49 * 16, count, input) != (unsigned)count ||
                fgetc(input) != EOF) exit(12);
        fclose(input);
        interactive_reference_count = count;
        puts("{\"event\":\"ok\"}");
    }
    return NULL;
}

static bool interactive_rendered_picture(void)
{
    int x0 = 8 - byte(0xff43), y0 = 8 - byte(0xff42);
    if (!interactive_reference_count || x0 < 0 || y0 < 0 || x0 + 56 > 160 || y0 + 56 > 144)
        return false;
    for (unsigned frame = 0; frame < interactive_reference_count; frame++) {
        bool matches = true;
        for (unsigned y = 0; matches && y < 56; y++) for (unsigned x = 0; x < 56; x++) {
            unsigned tile = y / 8 * 7 + x / 8, bit = 7 - x % 8;
            unsigned a = interactive_references[frame][tile * 16 + y % 8 * 2];
            unsigned b = interactive_references[frame][tile * 16 + y % 8 * 2 + 1];
            unsigned color = (a >> bit & 1) | (b >> bit & 1) << 1;
            if (pixels[(y0 + y) * 160 + x0 + x] != gb.background_palettes_rgb[4 + color]) {
                matches = false;
                break;
            }
        }
        if (matches) return true;
    }
    return false;
}

static unsigned interactive_read(unsigned bank, unsigned address, unsigned size)
{
    unsigned result = 0;
    for (unsigned i = 0; i < size; i++) {
        unsigned at = address + i;
        unsigned value = at >= 0xd000 && at < 0xe000 ?
            gb.ram[bank * 4096 + (at & 4095)] : byte(at);
        result |= value << (i * 8);
    }
    return result;
}

static uint32_t interactive_pixel_hash(unsigned kind)
{
    uint32_t hash = 2166136261u;
    bool minis = byte(S_wPokedexSelectedView) == 1 &&
        gb.ram[3 * 4096 + (S_wPokedexInfoPage & 4095)] != 0;
    for (unsigned y = 0; y < 132; y++) for (unsigned x = 0; x < 160; x++) {
        /* Footer End/Area is intentionally different. Keep the complete shell,
         * right edge, type objects and footprint; omit only animated objects. */
        if (x >= 3 && x < 59 && y >= 8 && y < 64) continue;
        if (kind == 0 && y >= 69) continue;
        if (kind == 1 && y < 69) continue;
        if (kind == 1 && minis && x < 32 && y >= 88 && y < 128) continue;
        uint32_t value = pixels[y * 160 + x];
        for (unsigned shift = 0; shift < 24; shift += 8)
            hash = (hash ^ (value >> shift & 255)) * 16777619u;
    }
    return hash;
}

static void interactive_snapshot(const char *event, const char *point)
{
    uint8_t map[98], picture[49 * 16];
    frontpic(map, picture);
    printf("{\"event\":\"%s\",\"point\":\"%s\",\"t\":%" PRIu64
           ",\"display\":%u,\"speed\":%u,\"ly\":%u,\"upper\":%u,\"panel\":%u,\"picture\":%u",
           event, point, perf_now(), perf_frames, gb.cgb_double_speed, byte(0xff44),
           interactive_pixel_hash(0), interactive_pixel_hash(1),
           perf_bytes_hash(picture, sizeof(picture)));
    for (unsigned i = 0; i < sizeof(interactive_fields) / sizeof(*interactive_fields); i++)
        printf(",\"%s\":%u", interactive_fields[i].name,
               interactive_read(interactive_fields[i].bank, interactive_fields[i].address,
                                interactive_fields[i].size));
    puts("}");
}

static void interactive_observe(GB_gameboy_t *g, uint16_t pc, uint8_t opcode)
{
    original_execution(g, pc, opcode);
    if (!perf_enabled || g->halted) return;
    unsigned bank = pc < 0x4000 ? 0 : g->mbc_rom_bank;
    for (unsigned i = 0; i < sizeof(interactive_points) / sizeof(*interactive_points); i++)
        if (interactive_points[i].bank == bank && interactive_points[i].pc == pc)
            interactive_snapshot("interactive_phase", interactive_points[i].name);
}

static void interactive_frame(GB_gameboy_t *g, GB_vblank_type_t type)
{
    original_vblank(g, type);
    if (perf_enabled) {
        interactive_snapshot("interactive_frame", "display");
        printf("{\"event\":\"interactive_pixels\",\"t\":%" PRIu64
               ",\"display\":%u,\"references\":%u,\"valid\":%s}\n",
               perf_now(), perf_frames, interactive_reference_count,
               interactive_rendered_picture() ? "true" : "false");
    }
}

static void interactive_execution(GB_gameboy_t *g, GB_execution_callback_t callback)
{
    original_execution = callback;
    GB_set_execution_callback(g, interactive_observe);
}

static void interactive_vblank(GB_gameboy_t *g, GB_vblank_callback_t callback)
{
    original_vblank = callback;
    GB_set_vblank_callback(g, interactive_frame);
}

int main(int argc, char **argv)
{
    int result = interactive_base_main(argc, argv);
    free(interactive_references);
    return result;
}
