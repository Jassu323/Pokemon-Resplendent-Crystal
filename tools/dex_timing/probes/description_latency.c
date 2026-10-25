/* Read-only admission tracing; no cartridge instrumentation or state writes. */
#include DEX_DESCRIPTION_LATENCY_SYMBOLS

static unsigned description_byte(unsigned bank, unsigned address)
{
    if (address >= 0xd000 && address < 0xe000)
        return gb.ram[bank * 4096 + (address & 4095)];
    return byte(address);
}

static void description_observe(unsigned bank, unsigned pc, uint64_t now)
{
    for (unsigned i = 0; i < sizeof(perf_points) / sizeof(*perf_points); i++) {
        if (bank != perf_points[i].bank || pc != perf_points[i].pc ||
            (strncmp(perf_points[i].name, "text_", 5) &&
             strncmp(perf_points[i].name, "portrait_", 9))) continue;
        unsigned state = description_byte(D_wPokedexDescriptionTextState_bank, D_wPokedexDescriptionTextState);
        unsigned owner = description_byte(D_wPokedexOwnerTransition_bank, D_wPokedexOwnerTransition);
        unsigned playback = description_byte(D_wPokedexAnimPlaybackState_bank, D_wPokedexAnimPlaybackState);
        unsigned flags = description_byte(D_wPokedexAnimFlags_bank, D_wPokedexAnimFlags);
        unsigned deadline = description_byte(D_wPokedexAnimDeadline_bank, D_wPokedexAnimDeadline);
        unsigned source = description_byte(D_wPokedexDescriptionTextSource_bank, D_wPokedexDescriptionTextSource) |
            description_byte(D_wPokedexDescriptionTextSource_bank, D_wPokedexDescriptionTextSource + 1) << 8;
        unsigned row = description_byte(D_wPokedexDescriptionTextRow_bank, D_wPokedexDescriptionTextRow);
        unsigned control = description_byte(D_wPokedexAnimSchedulerControl_bank, D_wPokedexAnimSchedulerControl);
        unsigned restore = description_byte(D_wPokedexInfoRestoreDescription_bank, D_wPokedexInfoRestoreDescription);
        printf("{\"event\":\"description_admission\",\"point\":\"%s\",\"t\":%" PRIu64
               ",\"ly\":%u,\"state\":%u,\"owner\":%u,\"playback\":%u,"
               "\"flags\":%u,\"deadline\":%u,\"source\":%u,\"row\":%u,"
               "\"control\":%u,\"restore\":%u,\"counter\":%u}\n",
               perf_points[i].name, now, gb.io_registers[0x44], state, owner,
               playback, flags, deadline, source, row, control, restore, byte(S_hVBlankCounter));
    }
}
