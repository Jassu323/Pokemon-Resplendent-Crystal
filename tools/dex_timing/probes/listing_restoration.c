/* Optional host-only instrumentation for Listing restoration investigations.
 * Included by cold_listing.c only in the separate diagnostic runner build. */
#include DEX_LISTING_RESTORE_SYMBOLS

static FILE *restoration_log;
static char restoration_prefix[2048];
static unsigned restoration_frames, restoration_pc, restoration_bank;
static bool restoration_images;
static unsigned restoration_admission_delay;

static uint64_t restoration_now(void)
{
    return (ticks + (unsigned)(gb.cycles_since_run - step_origin)) / 2;
}

static void restoration_hex(const uint8_t *data, unsigned length)
{
    fputc('"', restoration_log);
    for (unsigned i = 0; i < length; i++) fprintf(restoration_log, "%02x", data[i]);
    fputc('"', restoration_log);
}

static void restoration_snapshot(const char *kind, const char *phase, bool full)
{
    if (!restoration_log) return;
    bool white = true;
    for (unsigned i = 0; i < 160 * 144 && white; i++) white = pixels[i] == 0xffffff;
    fprintf(restoration_log, "{\"event\":\"%s\",\"phase\":\"%s\",\"t\":%" PRIu64
        ",\"display\":%u,\"pc\":%u,\"bank\":%u,\"ly\":%u,\"stat\":%u,"
        "\"physical_line\":%u,\"lcd_state\":%d,\"lcd_pending_ticks\":%d,"
        "\"lcd\":%u,\"scroll\":[%u,%u,%u,%u],\"mirrors\":[%u,%u,%u,%u],"
        "\"state\":%u,\"view\":%u,\"selected\":%u,\"index\":%u,\"listing_scroll\":%u,\"cursor\":%u,"
        "\"owner_transition\":%u,\"bg_dirty\":%u,\"obj_dirty\":%u,"
        "\"vblank\":%u,\"bg_mode\":%u,\"pal_update\":%u,\"oam_update\":%u,"
        "\"grid_top\":%u,\"grid_phase\":%u,\"white\":%u,\"bg_pal\":",
        kind, phase, restoration_now(), restoration_frames, restoration_pc, restoration_bank,
        byte(0xff44), byte(0xff41), gb.current_line, gb.display_state, gb.display_cycles,
        byte(0xff40), byte(0xff43), byte(0xff42), byte(0xff4b), byte(0xff4a),
        byte(R_hSCX), byte(R_hSCY), byte(R_hWX), byte(R_hWY),
        byte(S_wPokedexSelectedState), byte(S_wPokedexSelectedView), word(S_wPokedexSelectedIndex),
        word(S_wDexListingScrollOffset) + byte(S_wDexListingCursor),
        word(S_wDexListingScrollOffset), byte(S_wDexListingCursor),
        byte(R_wPokedexOwnerTransition), byte(R_wPokedexSelectedBGPaletteDirty),
        byte(R_wPokedexSelectedOBJPaletteDirty), byte(R_hVBlank), byte(R_hBGMapMode),
        byte(R_hCGBPalUpdate), byte(R_hOAMUpdate), byte(R_wPokedexGridTopPhysicalRow),
        byte(R_wPokedexGridIconAnimFrame), white);
    restoration_hex(gb.background_palettes_data, 64);
    fprintf(restoration_log, ",\"obj_pal\":"); restoration_hex(gb.object_palettes_data, 64);
    fprintf(restoration_log, ",\"target_bg\":"); restoration_hex(gb.ram + 0x5000 + (R_wBGPals2 & 4095), 64);
    fprintf(restoration_log, ",\"target_obj\":"); restoration_hex(gb.ram + 0x5000 + (R_wOBPals2 & 4095), 64);
    fprintf(restoration_log, ",\"grid_tags\":"); restoration_hex(gb.ram + R_wPokedexGridCacheRowOffsets - 0xc000, 10);
    fprintf(restoration_log, ",\"grid_storage\":\"%s\",\"grid_cells\":",
            R_GRID_USES_PRESENCE ? "presence" : "temporary_ids");
    restoration_hex(gb.ram + R_wPokedexGridCells - 0xc000, 9);
    fprintf(restoration_log, ",\"grid_presence\":\"");
    for (unsigned i = 0; i < 9; i++) {
        unsigned value = byte(R_wPokedexGridCells + i);
        fprintf(restoration_log, "%02x", R_GRID_USES_PRESENCE ? value : !!value);
    }
    fputc('"', restoration_log);
#if !R_GRID_USES_PRESENCE
    /* Old-ROM comparisons retain the identity audit; presence bytes are never IDs. */
    fprintf(restoration_log, ",\"grid_indices\":[");
    for (unsigned i = 0; i < 9; i++) {
        unsigned id = byte(R_wPokedexGridCells + i), species = 0;
        if (id) {
            unsigned at = 2 * 4096 + (R_wPokemonIndexTableEntries & 4095) + (id - 1) * 2;
            species = gb.ram[at] | gb.ram[at + 1] << 8;
        }
        fprintf(restoration_log, "%s%u", i ? "," : "", species);
    }
    fprintf(restoration_log, "]");
#endif
    fprintf(restoration_log, ",\"grid_flags\":"); restoration_hex(gb.ram + R_wPokedexGridFlags - 0xc000, 9);
    fprintf(restoration_log, ",\"grid_palettes\":"); restoration_hex(gb.ram + R_wPokedexGridIconPalettes - 0xc000, 9);
    fprintf(restoration_log, ",\"oam\":"); restoration_hex(gb.oam, 160);
    fprintf(restoration_log, ",\"shadow_oam\":"); restoration_hex(gb.ram + R_wShadowOAM - 0xc000, 160);
    if (full) {
        fprintf(restoration_log, ",\"vram\":"); restoration_hex(gb.vram, 0x4000);
    }
    fprintf(restoration_log, "}\n");
}

static void restoration_observe(unsigned bank, unsigned pc)
{
    /* Optional synthetic CPU-stall stress, separate from normal-input replays.
     * Advance the actual core's devices without editing ROM, RAM or registers. */
    if (restoration_admission_delay && byte(R_wPokedexOwnerTransition) == 2) {
        for (unsigned i = 0; i < sizeof(restoration_points) / sizeof(*restoration_points); i++) {
            if (bank == restoration_points[i].bank && pc == restoration_points[i].pc &&
                !strcmp(restoration_points[i].name, "owner_dispatch")) {
                unsigned delay = restoration_admission_delay;
                restoration_admission_delay = 0;
                if (gb.ime || gb.cgb_double_speed) { fputs("Unexpected admission test state\n", stderr); exit(12); }
                if (restoration_log) fprintf(restoration_log,
                    "{\"event\":\"admission_delay\",\"t\":%" PRIu64 ",\"cycles\":%u}\n",
                    restoration_now(), delay);
                while (delay) { GB_advance_cycles(&gb, 4); delay -= 4; }
                break;
            }
        }
    }
    restoration_bank = bank;
    restoration_pc = pc;
    if (!restoration_log) return;
    for (unsigned i = 0; i < sizeof(restoration_points) / sizeof(*restoration_points); i++) {
        if (bank == restoration_points[i].bank && pc == restoration_points[i].pc) {
            restoration_snapshot("phase", restoration_points[i].name, true);
        }
    }
}

static bool restoration_write(GB_gameboy_t *g, uint16_t address, uint8_t value)
{
    (void)g;
    if (restoration_log && (address == 0xff40 || address == 0xff43 || address == 0xff42 ||
        address == 0xff4a || address == 0xff4b || address == 0xff69 || address == 0xff6b ||
        address == 0xff55 || address == 0xff46)) {
        fprintf(restoration_log, "{\"event\":\"write\",\"t\":%" PRIu64
            ",\"display\":%u,\"pc\":%u,\"bank\":%u,\"ly\":%u,\"stat\":%u,"
            "\"physical_line\":%u,\"address\":%u,\"value\":%u,\"bgpi\":%u,\"obpi\":%u,"
            "\"pal_blocked\":%u,\"vram_blocked\":%u}\n",
            restoration_now(), restoration_frames, restoration_pc, restoration_bank,
            byte(0xff44), byte(0xff41), gb.current_line, address, value, byte(0xff68), byte(0xff6a),
            gb.cgb_palettes_blocked, gb.vram_write_blocked);
    }
    return true;
}

static void restoration_line(GB_gameboy_t *g, uint8_t line)
{
    if (!restoration_log || !(byte(0xff40) & 0x80) || (line != 0 && line != 144)) return;
    /* Display callbacks run at the end of a CPU batch. The display coroutine's
     * remaining 8MHz ticks locate the physical event within that batch. */
    uint64_t now = ticks + (unsigned)(g->cycles_since_run - step_origin);
    fprintf(restoration_log, "{\"event\":\"line\",\"t\":%" PRIu64
        ",\"boundary_t\":%" PRIu64 ",\"display\":%u,\"physical_line\":%u,"
        "\"lcd_pending_ticks\":%d}\n",
        now / 2, (now - g->display_cycles) / 2, restoration_frames, line, g->display_cycles);
}

static void restoration_frame(GB_gameboy_t *g, GB_vblank_type_t type)
{
    (void)g;
    if (!restoration_log) return;
    restoration_frames++;
    char phase[32];
    snprintf(phase, sizeof(phase), "%u", type);
    restoration_snapshot("frame", phase, true);
    if (!restoration_images) return;
    char name[2100];
    snprintf(name, sizeof(name), "%s-%03u.ppm", restoration_prefix, restoration_frames);
    FILE *file = fopen(name, "wb");
    if (!file) { perror(name); exit(12); }
    fprintf(file, "P6\n160 144\n255\n");
    for (unsigned i = 0; i < 160 * 144; i++) {
        uint8_t p[] = {pixels[i] >> 16, pixels[i] >> 8, pixels[i]};
        fwrite(p, 1, 3, file);
    }
    fclose(file);
}

static void restoration_close(void)
{
    if (restoration_log) fclose(restoration_log);
    restoration_log = NULL;
}

static bool restoration_command(const char *line)
{
    unsigned images;
    char prefix[2048];
    if (sscanf(line, "restoreadmission %u", &images) == 1) {
        if (images > 512 || images % 4) { fputs("Invalid admission delay\n", stderr); exit(12); }
        restoration_admission_delay = images;
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (sscanf(line, "restoretrace %2047s %u", prefix, &images) == 2) {
        restoration_close();
        snprintf(restoration_prefix, sizeof(restoration_prefix), "%s", prefix);
        char path[2100];
        snprintf(path, sizeof(path), "%s.jsonl", prefix);
        restoration_log = fopen(path, "w");
        if (!restoration_log) { perror(path); exit(12); }
        restoration_frames = 0;
        restoration_images = images != 0;
        restoration_snapshot("phase", "trace_start", true);
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (!strcmp(line, "restorestop\n")) {
        restoration_snapshot("phase", "trace_end", true);
        restoration_close();
        puts("{\"event\":\"ok\"}");
        return true;
    }
    return false;
}
