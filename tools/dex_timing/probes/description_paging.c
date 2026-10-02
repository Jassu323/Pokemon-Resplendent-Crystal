/* Host-only DEX-DESC-01 instrumentation. No emulated memory or cycle writes. */
#include DEX_DESCRIPTION_PAGING_SYMBOLS

static void snapshot(int hit);

static FILE *dp_log;
static char dp_prefix[2048];
static unsigned dp_frames, dp_pc, dp_bank;
static bool dp_images;
static bool dp_wait_seen;

static uint32_t dp_pixel_hash(unsigned x0, unsigned y0, unsigned width, unsigned height)
{
    uint32_t hash = 2166136261u;
    for (unsigned y = y0; y < y0 + height; y++) for (unsigned x = x0; x < x0 + width; x++) {
        uint32_t pixel = pixels[y * 160 + x];
        for (unsigned shift = 0; shift < 24; shift += 8) {
            hash ^= (pixel >> shift) & 255;
            hash *= 16777619u;
        }
    }
    return hash;
}

static uint64_t dp_now(void)
{
    return (ticks + (unsigned)(gb.cycles_since_run - step_origin)) / 2;
}

static void dp_hex(const uint8_t *data, unsigned size)
{
    fputc('"', dp_log);
    for (unsigned i = 0; i < size; i++) fprintf(dp_log, "%02x", data[i]);
    fputc('"', dp_log);
}

static void dp_snapshot(const char *event, const char *phase)
{
    if (!dp_log) return;
    uint8_t map[21 * 18], attrs[21 * 18], picture[49 * 16];
    for (unsigned y = 0; y < 18; y++) for (unsigned x = 0; x < 21; x++) {
        map[y * 21 + x] = gb.vram[0x1800 + y * 32 + x];
        attrs[y * 21 + x] = gb.vram[0x3800 + y * 32 + x];
    }
    for (unsigned y = 0; y < 7; y++) for (unsigned x = 0; x < 7; x++) {
        unsigned i = y * 7 + x, cell = (y + 1) * 21 + x + 1;
        unsigned attr = attrs[cell];
        unsigned address = 0x1000 + (int8_t)map[cell] * 16 + ((attr & 8) ? 0x2000 : 0);
        for (unsigned row = 0; row < 8; row++) for (unsigned plane = 0; plane < 2; plane++) {
            uint8_t value = gb.vram[address + ((attr & 64) ? 7 - row : row) * 2 + plane];
            if (attr & 32) {
                value = (value & 0x55) << 1 | (value >> 1 & 0x55);
                value = (value & 0x33) << 2 | (value >> 2 & 0x33);
                value = value << 4 | value >> 4;
            }
            picture[i * 16 + row * 2 + plane] = value;
        }
    }
    fprintf(dp_log, "{\"event\":\"%s\",\"phase\":\"%s\",\"t\":%" PRIu64
        ",\"display\":%u,\"pc\":%u,\"bank\":%u,\"ly\":%u,\"stat\":%u,"
        "\"physical_line\":%u,\"ime\":%u,\"page\":%u,\"tick\":%u,\"vblank\":%u,"
        "\"bg_mode\":%u,\"flags\":%u,\"deadline\":%u,\"stage_frame\":%u,"
        "\"playback\":%u,\"loaded\":%u,\"remaining\":%u,\"audio\":%u,\"map\":",
        event, phase, dp_now(), dp_frames, dp_pc, dp_bank, byte(0xff44), byte(0xff41),
        gb.current_line, gb.ime, byte(S_wPokedexDescriptionPage), byte(S_hVBlankCounter),
        byte(D_hVBlank), byte(D_hBGMapMode), byte(D_wPokedexAnimFlags),
        byte(D_wPokedexAnimDeadline), byte(S_wPokedexAnimStageFrameID),
        byte(S_wPokedexAnimPlaybackState),
        (word(S_wPokedexAnimDictionaryDestination) - 0xd000) / 16,
        word(S_hSampledCryBlocks), byte(S_hSampledCryTimer));
    dp_hex(map, sizeof(map)); fprintf(dp_log, ",\"attrs\":"); dp_hex(attrs, sizeof(attrs));
    fprintf(dp_log, ",\"picture\":"); dp_hex(picture, sizeof(picture));
    fprintf(dp_log, ",\"backing\":"); dp_hex(gb.ram + D_wTilemap - 0xc000, 360);
    fprintf(dp_log, ",\"backing_attrs\":"); dp_hex(gb.ram + D_wAttrmap - 0xc000, 360);
    fprintf(dp_log, ",\"palettes\":"); dp_hex(gb.background_palettes_data, 64);
    fprintf(dp_log, ",\"portrait_hash\":%u,\"header_hash\":%u,\"text_hash\":%u,\"portrait_rgb\":[%u,%u,%u,%u]",
        dp_pixel_hash(3, 8, 56, 56), dp_pixel_hash(60, 8, 92, 56),
        dp_pixel_hash(0, 64, 160, 56),
        gb.background_palettes_rgb[4], gb.background_palettes_rgb[5],
        gb.background_palettes_rgb[6], gb.background_palettes_rgb[7]);
    fprintf(dp_log, ",\"owner_request\":%u,\"text_state\":%u}\n",
        byte(D_wPokedexOwnerTransition), D_wPokedexDescriptionTextState ?
            gb.ram[0x3000 + D_wPokedexDescriptionTextState - 0xd000] : 0);
}

static void description_paging_observe(unsigned bank, unsigned pc)
{
    dp_bank = bank;
    dp_pc = pc;
    if (!dp_log) return;
    if (bank == D_TIMER_BANK && pc == D_TIMER_PC && byte(S_hSampledCryTimer)) {
        fprintf(dp_log, "{\"event\":\"audio_tick\",\"t\":%" PRIu64
            ",\"display\":%u,\"remaining\":%u}\n", dp_now(), dp_frames,
            word(S_hSampledCryBlocks));
    }
    for (unsigned i = 0; i < sizeof(dp_points) / sizeof(*dp_points); i++) {
        if (bank == dp_points[i].bank && pc == dp_points[i].pc) {
            if (!strcmp(dp_points[i].name, "copy_full")) dp_wait_seen = false;
            if (!strcmp(dp_points[i].name, "copy_complete")) {
                if (dp_wait_seen) continue;
                dp_wait_seen = true;
            }
            dp_snapshot("phase", dp_points[i].name);
        }
    }
}

static bool description_paging_write(GB_gameboy_t *g, uint16_t address, uint8_t value)
{
    (void)g;
    if (dp_log && ((address >= 0x9800 && address < 0x9a40) ||
        address == 0xff40 || address == 0xff4f || address == 0xff55 ||
        address == D_hVBlank || address == D_wPokedexAnimFlags)) {
        fprintf(dp_log, "{\"event\":\"write\",\"t\":%" PRIu64
            ",\"display\":%u,\"pc\":%u,\"bank\":%u,\"ly\":%u,\"stat\":%u,"
            "\"physical_line\":%u,\"address\":%u,\"value\":%u,\"vbk\":%u,"
            "\"vram_blocked\":%u}\n", dp_now(), dp_frames, dp_pc, dp_bank,
            byte(0xff44), byte(0xff41), gb.current_line, address, value,
            gb.cgb_vram_bank, gb.vram_write_blocked);
    }
    return true;
}

static void description_paging_line(GB_gameboy_t *g, uint8_t line)
{
    if (!dp_log || (line != 0 && line != 127 && line != 144)) return;
    uint64_t now = ticks + (unsigned)(g->cycles_since_run - step_origin);
    fprintf(dp_log, "{\"event\":\"line\",\"t\":%" PRIu64
        ",\"boundary_t\":%" PRIu64 ",\"display\":%u,\"line\":%u}\n",
        now / 2, (now - g->display_cycles) / 2, dp_frames, line);
}

static void description_paging_frame(GB_gameboy_t *g, GB_vblank_type_t type)
{
    (void)g;
    if (!dp_log) return;
    dp_frames++;
    char phase[24];
    snprintf(phase, sizeof(phase), "%u", type);
    dp_snapshot("frame", phase);
    if (!dp_images) return;
    char path[2100];
    snprintf(path, sizeof(path), "%s-%03u.ppm", dp_prefix, dp_frames);
    FILE *file = fopen(path, "wb");
    if (!file) { perror(path); exit(12); }
    fprintf(file, "P6\n160 144\n255\n");
    for (unsigned i = 0; i < 160 * 144; i++) {
        uint8_t p[] = {pixels[i] >> 16, pixels[i] >> 8, pixels[i]};
        fwrite(p, 1, 3, file);
    }
    if (fclose(file)) exit(12);
}

static void description_paging_close(void)
{
    if (dp_log) fclose(dp_log);
    dp_log = NULL;
}

static bool description_paging_command(char *line)
{
    unsigned images, bank, pc, keys;
    uint64_t budget;
    if (!strcmp(line, "dpstatus\n")) {
        printf("{\"event\":\"ok\",\"footer\":%u,\"owner_request\":%u,\"text_state\":%u,\"vblank\":%u}\n",
            byte(D_wDexArrowCursorPosIndex), byte(D_wPokedexOwnerTransition),
            D_wPokedexDescriptionTextState ? gb.ram[0x3000 + D_wPokedexDescriptionTextState - 0xd000] : 0,
            byte(D_hVBlank));
        return true;
    }
    if (sscanf(line, "dptrace %2047s %u", dp_prefix, &images) == 2) {
        description_paging_close();
        char path[2100];
        snprintf(path, sizeof(path), "%s.jsonl", dp_prefix);
        dp_log = fopen(path, "w");
        if (!dp_log) { perror(path); exit(12); }
        dp_frames = 0;
        dp_images = images != 0;
        dp_snapshot("start", "start");
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (!strcmp(line, "dpstop\n")) {
        dp_snapshot("end", "end");
        description_paging_close();
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (sscanf(line, "dprun %u %u %" SCNu64 " %u", &bank, &pc, &budget, &keys) == 4) {
        GB_set_key_mask(&gb, keys);
        uint64_t start = ticks;
        do {
            unsigned before = gb.cycles_since_run;
            step_origin = before;
            GB_cpu_run(&gb);
            ticks += (unsigned)(gb.cycles_since_run - before);
        } while (!at(bank, pc) && ticks - start < budget * 2);
        snapshot(-1);
        return true;
    }
    return false;
}
