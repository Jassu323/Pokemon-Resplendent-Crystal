/* Optional host-only IF/clock tracing. No game memory or execution is changed. */
static void clock_observe(unsigned bank, unsigned pc, uint64_t now)
{
    static unsigned last_counter;
    unsigned counter = byte(S_hVBlankCounter);
    bool timer_clear = bank == B_TIMER_IF_CLEAR &&
        pc >= P_TIMER_IF_CLEAR && pc <= P_TIMER_IF_CLEAR + 6;
    if (auditing && (counter != last_counter || timer_clear)) {
        printf("{\"event\":\"clock_trace\",\"t\":%" PRIu64
            ",\"counter\":%u,\"pc\":%u,\"bank\":%u,\"ly\":%u,\"ime\":%u,"
            "\"if\":%u,\"ie\":%u}\n", now / 2, counter, pc, bank,
            byte(0xff44), gb.ime, byte(0xff0f), gb.interrupt_enable);
    }
    last_counter = counter;
}
