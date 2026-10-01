/* Host-only cry ownership instrumentation. No game state or cycles are changed.
 * Included by cold_listing.c only with DEX_CRY_OWNER_TRACE. */
#include DEX_CRY_OWNER_SYMBOLS

static FILE *cry_owner_log;

static void cry_owner_snapshot(FILE *stream, const char *event, const char *phase,
                               unsigned bank, unsigned pc, bool executing)
{
    uint64_t now = ticks + (executing ? (unsigned)(gb.cycles_since_run - step_origin) : 0);
    unsigned active_channels = 0;
    for (unsigned i = 0; i < GB_N_CHANNELS; i++)
        active_channels |= gb.apu.is_active[i] ? 1u << i : 0;
    fprintf(stream, "{\"event\":\"%s\",\"phase\":\"%s\",\"t\":%" PRIu64
        ",\"bank\":%u,\"pc\":%u,\"ly\":%u,\"ime\":%u,\"state\":%u,"
        "\"selected\":%u,\"pending\":%u,\"audio\":%u,\"remaining\":%u,"
        "\"sample_bank\":%u,\"read_address\":%u,\"cache\":%u,\"compressed\":%u,"
        "\"volume\":%u,\"last_volume\":%u,\"priority\":%u,\"music_playing\":%u,"
        "\"cur_channel\":%u,\"pitch_sweep\":%u,\"nr50\":%u,\"nr51\":%u,"
        "\"nr52_latch\":%u,\"apu_active_mask\":%u,\"ie\":%u,\"tac\":%u,\"af\":%u,\"bc\":%u,"
        "\"de\":%u,\"hl\":%u,\"sp\":%u,\"sfx_flags\":[",
        event, phase, now / 2, bank, pc, byte(0xff44), gb.ime,
        byte(S_wPokedexSelectedState), word(S_wPokedexSelectedIndex),
        word(C_wPokedexSelectedPendingIndex), byte(S_hSampledCryTimer),
        word(S_hSampledCryBlocks), byte(C_hSampledCryBank), word(C_hSampledCryAddress),
        gb.ram[0x4000 + (C_wSampledCryCacheCount & 4095)],
        gb.ram[0x4000 + (C_wSampledCryCompressedBlocks & 4095)] |
            gb.ram[0x4000 + ((C_wSampledCryCompressedBlocks + 1) & 4095)] << 8,
        byte(C_wVolume), byte(C_wLastVolume), byte(C_wSFXPriority),
        byte(C_wMusicPlaying), byte(C_wCurChannel), byte(C_wPitchSweep),
        byte(0xff24), byte(0xff25), byte(0xff26), active_channels, gb.interrupt_enable,
        byte(0xff07), gb.registers[GB_REGISTER_AF], gb.registers[GB_REGISTER_BC],
        gb.registers[GB_REGISTER_DE], gb.registers[GB_REGISTER_HL], gb.sp);
    for (unsigned i = 0; i < 4; i++)
        fprintf(stream, "%s%u", i ? "," : "", byte(cry_flags[i]));
    fprintf(stream, "],\"sfx_address\":[");
    for (unsigned i = 0; i < 4; i++)
        fprintf(stream, "%s%u", i ? "," : "", word(cry_addresses[i]));
    fprintf(stream, "],\"sfx_duration\":[");
    for (unsigned i = 0; i < 4; i++)
        fprintf(stream, "%s%u", i ? "," : "", byte(cry_durations[i]));
    fprintf(stream, "],\"sfx_bank\":[");
    for (unsigned i = 0; i < 4; i++)
        fprintf(stream, "%s%u", i ? "," : "", byte(cry_banks[i]));
    fprintf(stream, "],\"music_address\":[");
    for (unsigned i = 0; i < 4; i++)
        fprintf(stream, "%s%u", i ? "," : "", word(cry_music_addresses[i]));
    fprintf(stream, "],\"channel_regs\":[");
    const unsigned registers[] = {0xff10, 0xff12, 0xff14, 0xff17, 0xff19,
        0xff1a, 0xff1c, 0xff1e, 0xff21, 0xff23};
    for (unsigned i = 0; i < sizeof(registers) / sizeof(*registers); i++)
        fprintf(stream, "%s%u", i ? "," : "", byte(registers[i]));
    fprintf(stream, "]}\n");
}

static void cry_owner_observe(unsigned bank, unsigned pc)
{
    if (!cry_owner_log) return;
    for (unsigned i = 0; i < sizeof(cry_owner_points) / sizeof(*cry_owner_points); i++) {
        if (bank != cry_owner_points[i].bank || pc != cry_owner_points[i].pc) continue;
        const char *name = cry_owner_points[i].name;
        /* Timer copies during steady playback are uninteresting here. Copies
         * during an owner handoff can race the incoming header lookup. */
        if (!strcmp(name, "timer_copy") && byte(S_wPokedexSelectedState) == 1) continue;
        cry_owner_snapshot(cry_owner_log, "phase", name, bank, pc, true);
    }
}

static void cry_owner_close(void)
{
    if (cry_owner_log) fclose(cry_owner_log);
    cry_owner_log = NULL;
}

static bool cry_owner_command(const char *line)
{
    char path[2048];
    if (sscanf(line, "crytrace %2047s", path) == 1) {
        cry_owner_close();
        cry_owner_log = fopen(path, "w");
        if (!cry_owner_log) { perror(path); exit(12); }
        cry_owner_snapshot(cry_owner_log, "phase", "trace_start", gb.mbc_rom_bank, gb.pc, false);
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (!strcmp(line, "crystop\n")) {
        if (cry_owner_log)
            cry_owner_snapshot(cry_owner_log, "phase", "trace_end", gb.mbc_rom_bank, gb.pc, false);
        cry_owner_close();
        puts("{\"event\":\"ok\"}");
        return true;
    }
    if (!strcmp(line, "cry\n")) {
        cry_owner_snapshot(stdout, "ok", "snapshot", gb.mbc_rom_bank, gb.pc, false);
        return true;
    }
    return false;
}
