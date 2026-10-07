/* Host-only display latency/profiling. No cartridge instrumentation or writes. */
#include DEX_PERFORMANCE_SYMBOLS

#ifndef PERF_ANIM_OBJECT_BYTES
#define PERF_ANIM_OBJECT_BYTES (14 * 20)
#endif

static bool perf_enabled;
static unsigned perf_frames;
static char perf_image_prefix[768];
static struct {
    unsigned id, sp, return_pc, bank;
    uint64_t start;
} perf_spans[64];
static unsigned perf_span_count;
static FILE *perf_audio_file;
#ifdef DEX_SEARCH_ICON_TRACE
static unsigned perf_search_last_ly = 255;
#endif
#ifdef DEX_SEARCH_RESULTS_TRACE
static unsigned perf_results_last_ly = 255;
#endif
#ifdef DEX_BATTLE_SPEED_TRACE
static bool perf_speed_valid, perf_last_speed;
#endif

static void perf_audio_sample(GB_gameboy_t *g, GB_sample_t *sample)
{
    if (perf_audio_file) fwrite(sample, sizeof(*sample), 1, perf_audio_file);
}

static uint64_t perf_now(void)
{
    return (ticks + (unsigned)(gb.cycles_since_run - step_origin)) / 2;
}

static uint32_t perf_hash(unsigned kind)
{
    uint32_t hash = 2166136261u;
    for (unsigned y = 0; y < 144; y++) for (unsigned x = 0; x < 160; x++) {
        /* Ignore portrait/mini animation and the footer cursor when measuring
         * lower-panel replacement. These are independent ongoing changes. */
        if (kind == 1 && !(y >= 72 && y < 128 && x >= 32 && x < 155)) continue;
        if (kind == 2 && ((x < 60 && y < 64) || (x < 32 && y >= 72 && y < 128))) continue;
        uint32_t value = pixels[y * 160 + x];
        for (unsigned shift = 0; shift < 24; shift += 8) {
            hash ^= value >> shift & 255;
            hash *= 16777619u;
        }
    }
    return hash;
}

static uint32_t perf_bytes_hash(const uint8_t *data, unsigned size)
{
    uint32_t hash = 2166136261u;
    for (unsigned i = 0; i < size; i++) hash = (hash ^ data[i]) * 16777619u;
    return hash;
}

#ifdef DEX_SURF_CLEANUP_TRACE
/* Host-only ownership/cleanup audit; never changes cartridge state or time. */
static unsigned surf_wrong_bank_reads;
static void perf_surf_cleanup(const char *point)
{
    const uint8_t *objects = gb.ram + S_wActiveAnimObjects_bank * 4096 + (S_wActiveAnimObjects & 4095);
    unsigned slot = 0;
    while (slot < 14 && !(objects[slot * 20] && objects[slot * 20 + 5] == 0x0d)) slot++;
    const uint8_t *obj = slot < 14 ? objects + slot * 20 : NULL;
    printf("{\"event\":\"surf_cleanup\",\"point\":\"%s\",\"t\":%" PRIu64
           ",\"display\":%u,\"lcd_pointer\":%u,\"start\":%u,\"end\":%u,"
           "\"scy\":%u,\"pending_scy\":%u,\"svbk\":%u,\"stat\":%u,"
           "\"surf_slot\":%u,\"surf_state\":%u,\"surf_y\":%u,\"divider\":%u,"
           "\"wrong_bank_reads\":%u}\n",
           point, perf_now(), perf_frames, byte(S_hLCDCPointer), byte(S_hLYOverrideStart),
           byte(S_hLYOverrideEnd), gb.io_registers[0x42], byte(S_hSCY), gb.cgb_ram_bank,
           gb.io_registers[0x41], slot, obj ? obj[15] : 255, obj ? obj[9] : 255,
           obj ? obj[17] : 255, surf_wrong_bank_reads);
}
#endif

static void perf_frame(GB_gameboy_t *g, GB_vblank_type_t type)
{
    if (!perf_enabled) return;
    perf_frames++;
    unsigned black = 0, white = 0;
    for (unsigned i = 0; i < 160 * 144; i++) {
        black += (pixels[i] & 0xffffff) == 0;
        white += (pixels[i] & 0xffffff) == 0xffffff;
    }
    uint64_t now = perf_now();
#ifdef DEX_SURF_CLEANUP_TRACE
    perf_surf_cleanup("display");
#endif
    if (perf_image_prefix[0]) {
        char path[832];
        snprintf(path, sizeof(path), "%s-%03u.ppm", perf_image_prefix, perf_frames);
        FILE *file = fopen(path, "wb");
        if (!file) { fprintf(stderr, "Cannot write performance image\n"); exit(2); }
        fprintf(file, "P6\n160 144\n255\n");
        for (unsigned i = 0; i < 160 * 144; i++) {
            uint8_t p[] = {pixels[i] >> 16, pixels[i] >> 8, pixels[i]};
            fwrite(p, 1, 3, file);
        }
        fclose(file);
    }
    /* SameBoy delivers the callback at the end of the CPU batch. */
    int pending = g->display_cycles;
    uint64_t boundary = pending >= 0 && now >= (unsigned)pending / 2 ? now - pending / 2 : now;
    printf("{\"event\":\"perf_frame\",\"t\":%" PRIu64 ",\"boundary_t\":%" PRIu64
           ",\"display\":%u,\"type\":%u,\"full\":%u,\"lower\":%u,\"stable\":%u,"
           "\"black\":%u,\"white\":%u,\"lcdc\":%u,\"wx\":%u,\"wy\":%u,"
           "\"speed\":%u,\"oam\":%u,\"bgpals\":%u,\"objpals\":%u,\"anim_id\":%u,\"turn\":%u}\n",
           now, boundary, perf_frames, type, perf_hash(0), perf_hash(1), perf_hash(2),
           black, white, gb.io_registers[0x40], gb.io_registers[0x4b], gb.io_registers[0x4a],
           gb.cgb_double_speed, perf_bytes_hash(gb.oam, 160),
           perf_bytes_hash(gb.background_palettes_data, 64), perf_bytes_hash(gb.object_palettes_data, 64),
           word(S_wFXAnimID), byte(S_hBattleTurn));
#ifdef DEX_BATTLE_TIMING_TRACE
    printf("{\"event\":\"hardware_oam\",\"t\":%" PRIu64 ",\"display\":%u,\"bytes\":\"", now, perf_frames);
    for (unsigned i = 0; i < 160; i++) printf("%02x", gb.oam[i]);
    puts("\"}");
#endif
#ifdef DEX_BATTLE_INTRO_TRACE
    printf("{\"event\":\"intro_display\",\"t\":%" PRIu64 ",\"display\":%u,"
           "\"scx\":%u,\"pending_scx\":%u,\"producer\":%u,\"dma\":%u,\"oam\":\"",
           now, perf_frames, gb.io_registers[0x43], byte(S_hSCX),
           byte(S_wBattleFrontpicProducerState), byte(S_hDMATransfer));
    for (unsigned i = 0; i < 160; i++) printf("%02x", gb.oam[i]);
    puts("\"}");
#endif
}

static void perf_observe(unsigned bank, unsigned pc)
{
    if (!perf_enabled) return;
    uint64_t now = perf_now();
#ifdef DEX_SEARCH_RESULTS_TRACE
    unsigned results_ly = gb.io_registers[0x44];
    if (byte(S_wJumptableIndex) == 10 && bank == RESULTS_DMA_BANK && pc == RESULTS_DMA_PC) {
        printf("{\"event\":\"results_dma_start\",\"t\":%" PRIu64
               ",\"ly\":%u,\"length\":%u}\n", now, results_ly, gb.af >> 8);
    }
    if (results_ly == 0 && perf_results_last_ly != 0 && byte(S_wJumptableIndex) == 10) {
        unsigned position = word(S_wDexListingScrollOffset) + byte(S_wDexListingCursor);
        const uint8_t *entry = gb.ram + 5 * 4096 + RESULTS_ORDER_OFFSET + position * 2;
        printf("{\"event\":\"results_scanout\",\"t\":%" PRIu64
               ",\"position\":%u,\"permanent\":%u,\"oam\":", now, position,
               entry[0] | entry[1] << 8);
        hex(gb.oam, 160);
        printf(",\"palettes\":");
        hex(gb.object_palettes_data, 32);
        printf(",\"bgpal\":");
        hex(gb.background_palettes_data + 8, 8);
        printf(",\"portrait\":");
        hex(gb.vram + 0x1000, 49 * 16);
        printf(",\"name\":");
        unsigned visible_row = (gb.oam[0] - 24) / 16;
        hex(gb.vram + 0x1c00 + (2 + visible_row * 2) * 32 + 1, 10);
        puts("}");
    }
    perf_results_last_ly = results_ly;
#endif
#ifdef DEX_SEARCH_ICON_TRACE
    unsigned search_ly = gb.io_registers[0x44];
    if (search_ly == 0 && perf_search_last_ly != 0) {
        /* Observe the completed VBlank transaction before visible scanout,
         * not a mid-interrupt palette/OAM snapshot at the VBlank boundary. */
        printf("{\"event\":\"search_icon_scanout\",\"t\":%" PRIu64 ",\"oam\":", now);
        hex(gb.oam + 36, 32);
        printf(",\"palettes\":");
        hex(gb.object_palettes_data + 8, 16);
        printf(",\"tiles\":");
        hex(gb.vram + 8192 + 0x280, 256);
        printf(",\"fields\":\"");
        for (unsigned row = 4; row <= 6; row += 2)
            for (unsigned column = 9; column < 17; column++)
                printf("%02x", gb.vram[0x1800 + row * 32 + column]);
        printf("\",\"committed\":");
        hex(gb.ram + 3 * 4096 + 0xc05, 2);
        puts("}");
    }
    perf_search_last_ly = search_ly;
#endif
    unsigned sampled_blocks = 0;
#ifdef S_hSampledCryBlocks
    sampled_blocks = word(S_hSampledCryBlocks);
#endif
#ifdef DEX_BATTLE_SPEED_TRACE
    if (!perf_speed_valid || perf_last_speed != gb.cgb_double_speed) {
        printf("{\"event\":\"speed_change\",\"t\":%" PRIu64
               ",\"speed\":%u,\"pc\":%u,\"bank\":%u,\"lcdc\":%u,"
               "\"nr52\":%u,\"ie\":%u,\"if\":%u,\"tac\":%u,"
               "\"sampled_active\":%u,\"battle_mode\":%u,\"initial\":%u}\n",
               now, gb.cgb_double_speed, pc, bank, gb.io_registers[0x40],
               gb.io_registers[0x26], gb.interrupt_enable, gb.io_registers[0x0f],
               gb.io_registers[0x07], byte(S_hSampledCryTimer), byte(S_wBattleMode), !perf_speed_valid);
        perf_speed_valid = true;
        perf_last_speed = gb.cgb_double_speed;
    }
#endif
#ifdef DEX_SURF_CLEANUP_TRACE
    if (pc == S_LCD && byte(S_hLCDCPointer) == 0x42 && gb.cgb_ram_bank != S_wActiveAnimObjects_bank) {
        surf_wrong_bank_reads++;
        if (surf_wrong_bank_reads <= 16) {
            unsigned line = gb.io_registers[0x44];
            unsigned address = (S_wLYOverrides & 0xff00) | line;
            printf("{\"event\":\"surf_wrong_bank\",\"t\":%" PRIu64
                   ",\"line\":%u,\"bank\":%u,\"actual_value\":%u,\"intended_value\":%u}\n",
                   now, line, gb.cgb_ram_bank, byte(address),
                   gb.ram[S_wActiveAnimObjects_bank * 4096 + (address & 4095)]);
        }
    }
#endif
    for (unsigned i = 0; i < perf_span_count;) {
        if (gb.sp == perf_spans[i].sp + 2 && pc == perf_spans[i].return_pc &&
            (pc < 0x4000 || bank == perf_spans[i].bank)) {
#ifdef DEX_SURF_CLEANUP_TRACE
            const char *name = perf_points[perf_spans[i].id].name;
            if (!strcmp(name, "battle_script") || !strcmp(name, "battle_anim") ||
                !strcmp(name, "anim_owner")) perf_surf_cleanup(name);
#endif
            printf("{\"event\":\"perf_cost\",\"name\":\"%s\",\"t\":%" PRIu64
                   ",\"elapsed\":%" PRIu64 "}\n", perf_points[perf_spans[i].id].name,
                   perf_spans[i].start, now - perf_spans[i].start);
            perf_spans[i] = perf_spans[--perf_span_count];
        } else i++;
    }
    for (unsigned i = 0; i < sizeof(perf_points) / sizeof(*perf_points); i++) {
        if (bank != perf_points[i].bank || pc != perf_points[i].pc) continue;
        bool already_active = false;
        for (unsigned j = 0; j < perf_span_count; j++) {
            already_active |= perf_spans[j].id == i && perf_spans[j].sp == gb.sp;
        }
        if (already_active) continue;
#ifdef DEX_SURF_CLEANUP_TRACE
        if (!strncmp(perf_points[i].name, "surf_", 5)) perf_surf_cleanup(perf_points[i].name);
#endif
        printf("{\"event\":\"perf_phase\",\"name\":\"%s\",\"t\":%" PRIu64
               ",\"ly\":%u,\"bc\":%u,\"de\":%u,\"hl\":%u,\"svbk\":%u,\"vbk\":%u,"
               "\"speed\":%u,\"lcdc\":%u,\"tma\":%u,\"tac\":%u,\"remaining\":%u,\"anim_id\":%u,\"turn\":%u}\n",
               perf_points[i].name, now, gb.io_registers[0x44], gb.bc, gb.de, gb.hl,
               gb.cgb_ram_bank, gb.cgb_vram_bank, gb.cgb_double_speed,
               gb.io_registers[0x40], gb.io_registers[0x06], gb.io_registers[0x07],
               sampled_blocks, word(S_wFXAnimID), byte(S_hBattleTurn));
#ifdef DEX_BATTLE_TIMING_TRACE
        if (!strcmp(perf_points[i].name, "anim_ready")) {
            unsigned peak = 0, over = 0, height = gb.io_registers[0x40] & 4 ? 16 : 8;
            for (unsigned y = 0; y < 144; y++) {
                unsigned count = 0;
                for (unsigned obj = 0; obj < 40; obj++) {
                    unsigned oy = byte(S_wShadowOAM + obj * 4);
                    count += y + 16 >= oy && y + 16 < oy + height;
                }
                if (count > peak) peak = count;
                over += count > 10;
            }
            printf("{\"event\":\"anim_state\",\"t\":%" PRIu64
                   ",\"display\":%u,\"anim_id\":%u,\"turn\":%u,\"script\":%u,"
                   "\"delay\":%u,\"param\":%u,\"peak\":%u,\"over_lines\":%u,\"shadow\":\"",
                   now, perf_frames, word(S_wFXAnimID), byte(S_hBattleTurn),
                   word(S_wBattleAnimAddress), byte(S_wBattleAnimDelay),
                   byte(S_wBattleAnimParam), peak, over);
            for (unsigned obj = 0; obj < 160; obj++) printf("%02x", byte(S_wShadowOAM + obj));
            puts("\"}");
#if defined(DEX_THUNDERBOLT_OBJECT_TRACE) || defined(DEX_ANIMATION_REFERENCE_TRACE)
            printf("{\"event\":\"anim_objects\",\"t\":%" PRIu64 ",\"bytes\":\"", now);
            for (unsigned n = 0; n < PERF_ANIM_OBJECT_BYTES; n++) printf("%02x", byte(S_wActiveAnimObjects + n));
            puts("\"}");
#endif
#ifdef DEX_ANIMATION_REFERENCE_TRACE
            printf("{\"event\":\"anim_background\",\"t\":%" PRIu64 ",\"bytes\":\"", now);
            for (unsigned n = 0; n < 5 * 4; n++) printf("%02x", byte(S_wBGEffect1 + n));
            printf("\",\"lcd_pointer\":%u,\"nr52\":%u,\"sfx\":%u}\n",
                   byte(S_hLCDCPointer), gb.io_registers[0x26],
                   (byte(S_wChannel5Flags1) | byte(S_wChannel6Flags1) |
                    byte(S_wChannel7Flags1) | byte(S_wChannel8Flags1)) & 1);
#endif
#ifdef DEX_BATTLE_PACING_TRACE
            printf("{\"event\":\"pace_state\",\"t\":%" PRIu64 ",\"data\":\"", now);
            for (unsigned n = 0; n < 10; n++) printf("%02x", byte(S_wBattleAnimPaceExtra + n));
            puts("\"}");
#endif
        }
#endif
        if (!strcmp(perf_points[i].name, "wave_block")) {
            uint8_t wave[32];
            GB_get_apu_wave_table(&gb, wave);
            printf("{\"event\":\"wave_block\",\"t\":%" PRIu64 ",\"speed\":%u,"
                   "\"remaining\":%u,\"tma\":%u,\"tac\":%u,\"frequency\":%u,\"wave\":",
                   now, gb.cgb_double_speed, sampled_blocks,
                   gb.io_registers[6], gb.io_registers[7],
                   gb.io_registers[0x1d] | (gb.io_registers[0x1e] & 7) << 8);
            hex(wave, sizeof(wave));
            puts("}");
        }
        if (!perf_points[i].span || perf_span_count == 64 || gb.sp < 0xc000 || gb.sp >= 0xdfff) continue;
        unsigned return_pc = GB_read_memory(&gb, gb.sp) | GB_read_memory(&gb, gb.sp + 1) << 8;
        unsigned at = perf_span_count++;
        perf_spans[at].id = i;
        perf_spans[at].sp = gb.sp;
        perf_spans[at].return_pc = return_pc;
        perf_spans[at].bank = gb.mbc_rom_bank;
        perf_spans[at].start = now;
    }
}

static bool perf_command(const char *line)
{
    if (!strcmp(line, "searchui\n")) {
        printf("{\"event\":\"ok\",\"bg_palettes\":");
        hex(gb.background_palettes_data, 64);
        printf(",\"obj_palettes\":");
        hex(gb.object_palettes_data, 64);
        printf(",\"oam\":");
        hex(gb.oam, sizeof(gb.oam));
        printf(",\"map\":");
        hex(gb.vram + 0x1800, 18 * 32);
        printf(",\"attrs\":");
        hex(gb.vram + 0x3800, 18 * 32);
        printf(",\"bgp\":%u,\"obp0\":%u,\"obp1\":%u,\"lcdc\":%u,"
               "\"scx\":%u,\"scy\":%u,\"wx\":%u,\"wy\":%u,\"speed\":%u}\n",
               byte(0xff47), byte(0xff48), byte(0xff49), byte(0xff40),
               byte(0xff43), byte(0xff42), byte(0xff4b), byte(0xff4a),
               gb.cgb_double_speed);
        return true;
    }
    char battery_path[768];
    if (sscanf(line, "perfbattery %767s", battery_path) == 1) {
        printf("{\"event\":\"ok\",\"error\":%u}\n", GB_save_battery(&gb, battery_path));
        return true;
    }
    unsigned enabled;
    unsigned bank, address, size;
    char audio_path[768];
    char pixel_action[8], pixel_path[768];
    if (sscanf(line, "perfpixels %7s %767s", pixel_action, pixel_path) == 2) {
        bool save = !strcmp(pixel_action, "save");
        if (!save && strcmp(pixel_action, "load")) return false;
        FILE *file = fopen(pixel_path, save ? "wb" : "rb");
        if (!file) { fprintf(stderr, "Cannot access observer pixel checkpoint\n"); exit(2); }
        size_t n = save ? fwrite(pixels, sizeof(pixels), 1, file) : fread(pixels, sizeof(pixels), 1, file);
        fclose(file);
        if (n != 1) { fprintf(stderr, "Invalid observer pixel checkpoint\n"); exit(2); }
        /* The host's output buffer is not emulator state. Restore only the
         * already-rendered pixels when replaying the matching CPU/PPU state. */
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (sscanf(line, "perfram %u %u %u", &bank, &address, &size) == 3) {
        if (bank > 7 || !size || size > 1024 || address + size > 65536) return false;
        printf("{\"event\":\"ok\",\"bytes\":\"");
        for (unsigned i = 0; i < size; i++) {
            unsigned at = address + i;
            unsigned value = at >= 0xc000 && at < 0xe000 ?
                gb.ram[(at < 0xd000 ? 0 : bank) * 4096 + (at & 4095)] : GB_read_memory(&gb, at);
            printf("%02x", value);
        }
        printf("\",\"apu_enabled\":%u,\"apu_lf_div\":%u,\"speed\":%u}\n",
               gb.apu.global_enable, gb.apu.lf_div, gb.cgb_double_speed);
        return true;
    }
    if (sscanf(line, "perfaudio %767s", audio_path) == 1) {
        if (perf_audio_file) fclose(perf_audio_file);
        perf_audio_file = NULL;
        if (strcmp(audio_path, "-")) {
            perf_audio_file = fopen(audio_path, "wb");
            if (!perf_audio_file) { fprintf(stderr, "Cannot write audio recording\n"); exit(2); }
            GB_set_sample_rate(&gb, 44100);
            GB_apu_set_sample_callback(&gb, perf_audio_sample);
        }
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (sscanf(line, "perfimages %767s", perf_image_prefix) == 1) {
        if (!strcmp(perf_image_prefix, "-")) perf_image_prefix[0] = 0;
        puts("{\"event\":\"ok\"}");
        return true;
    }
    unsigned count;
    if (sscanf(line, "inspect %u %u %u", &bank, &address, &count) == 3 &&
        bank < 8 && count <= 4096 && (address & 4095) + count <= 4096) {
        printf("{\"event\":\"ok\",\"svbk\":%u,\"bytes\":", gb.cgb_ram_bank);
        hex(gb.ram + bank * 4096 + (address & 4095), count);
        puts("}");
        return true;
    }
    if (sscanf(line, "inspectvram %u %u %u", &bank, &address, &count) == 3 &&
        bank < 2 && count <= 8192 && (address & 8191) + count <= 8192) {
        printf("{\"event\":\"ok\",\"bytes\":");
        hex(gb.vram + bank * 8192 + (address & 8191), count);
        puts("}");
        return true;
    }
    if (sscanf(line, "perf %u", &enabled) == 1) {
        perf_enabled = enabled != 0;
        perf_frames = perf_span_count = 0;
#ifdef DEX_SEARCH_ICON_TRACE
        perf_search_last_ly = 255;
#endif
        printf("{\"event\":\"ok\",\"t\":%" PRIu64 ",\"full\":%u,\"lower\":%u,\"stable\":%u}\n",
               ticks / 2, perf_hash(0), perf_hash(1), perf_hash(2));
        return true;
    }
    return false;
}
