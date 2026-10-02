/* Host-only direction/edge/repeat observation; never writes to game memory. */
#include DEX_DIRECTION_SYMBOLS

static FILE *direction_log;
static unsigned direction_keys;

static void direction_snapshot(FILE *stream, const char *event, const char *phase,
                               unsigned bank, unsigned pc, bool executing)
{
    uint64_t now = ticks + (executing ? (unsigned)(gb.cycles_since_run - step_origin) : 0);
    fprintf(stream, "{\"event\":\"%s\",\"phase\":\"%s\",\"t\":%" PRIu64
        ",\"bank\":%u,\"pc\":%u,\"ly\":%u,\"tick\":%u,\"keys\":%u,"
        "\"physical\":%u,\"physical_pressed\":%u,\"physical_released\":%u,"
        "\"down\":%u,\"pressed\":%u,\"released\":%u,\"last\":%u,"
        "\"menu_mode\":%u,\"repeat_delay\":%u,\"index\":%u,\"scroll\":%u,"
        "\"cursor\":%u,\"selected\":%u,\"pending\":%u,\"footer\":%u,"
        "\"footer_delay\":%u,\"owner_state\":%u,\"jumptable\":%u}\n",
        event, phase, now / 2, bank, pc, byte(0xff44), byte(S_hVBlankCounter), direction_keys,
        byte(N_hJoypadDown), byte(N_hJoypadPressed), byte(N_hJoypadReleased),
        byte(S_hJoyDown), byte(N_hJoyPressed), byte(N_hJoyReleased), byte(N_hJoyLast),
        byte(N_hInMenu), byte(N_wTextDelayFrames),
        word(S_wDexListingScrollOffset) + byte(S_wDexListingCursor),
        word(S_wDexListingScrollOffset), byte(S_wDexListingCursor),
        word(S_wPokedexSelectedIndex), word(N_wPokedexSelectedPendingIndex),
        byte(N_wDexArrowCursorPosIndex), byte(N_wDexArrowCursorDelayCounter),
        byte(S_wPokedexSelectedState), byte(S_wJumptableIndex));
}

static void direction_observe(unsigned bank, unsigned pc)
{
    if (!direction_log) return;
    for (unsigned i = 0; i < sizeof(direction_points) / sizeof(*direction_points); i++) {
        if (bank == direction_points[i].bank && pc == direction_points[i].pc)
            direction_snapshot(direction_log, "phase", direction_points[i].name, bank, pc, true);
    }
}

static void direction_input(unsigned keys)
{
    if (keys == direction_keys) return;
    direction_keys = keys;
    if (direction_log)
        direction_snapshot(direction_log, "input", "pins", gb.mbc_rom_bank, gb.pc, false);
}

static void direction_close(void)
{
    if (direction_log) fclose(direction_log);
    direction_log = NULL;
}

static bool direction_command(const char *line)
{
    char path[2048];
    if (sscanf(line, "dirtrace %2047s", path) == 1) {
        direction_close();
        direction_log = fopen(path, "w");
        if (!direction_log) { perror(path); exit(12); }
        direction_snapshot(direction_log, "phase", "trace_start", gb.mbc_rom_bank, gb.pc, false);
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (!strcmp(line, "dirstop\n")) {
        if (direction_log)
            direction_snapshot(direction_log, "phase", "trace_end", gb.mbc_rom_bank, gb.pc, false);
        direction_close();
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (!strcmp(line, "dir\n")) {
        direction_snapshot(stdout, "ok", "snapshot", gb.mbc_rom_bank, gb.pc, false);
        return true;
    }
    return false;
}
