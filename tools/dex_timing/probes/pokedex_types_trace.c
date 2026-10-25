/* Read-only raster timing observer. It never changes ROM or game memory. */
static unsigned types_writes, types_bad_modes, types_bad_indexes, types_bad_registers;
static unsigned types_frames, types_irq_count, types_max_irq;
static uint64_t types_irq_start;
static unsigned types_bc, types_de, types_hl, types_sp, types_bank, types_svbk;
static bool types_in_irq;
static unsigned types_af, types_counter, types_sound, types_joypad, types_clock;

static bool types_active(void);

static void types_observe(unsigned bank, unsigned pc, uint64_t now)
{
#ifndef DEX_TYPES_MODE7_TRACE
    if (bank == 0 && pc == P_TYPES_LCD) {
        types_in_irq = true;
        types_irq_start = now;
        types_bc = gb.bc; types_de = gb.de; types_hl = gb.hl; types_sp = gb.sp;
        types_bank = gb.mbc_rom_bank; types_svbk = gb.cgb_ram_bank;
    }
    if (bank == 0 && pc == P_LCD_DONE && types_in_irq) {
        unsigned dots = (unsigned)(now - types_irq_start) / 2;
        if (dots > types_max_irq) types_max_irq = dots;
        types_irq_count++;
        if (gb.bc != types_bc || gb.de != types_de || gb.hl != types_hl || gb.sp != types_sp ||
                gb.mbc_rom_bank != types_bank || gb.cgb_ram_bank != types_svbk) types_bad_registers++;
        types_in_irq = false;
    }
#else
    if (bank == 0 && pc == P_TYPES_FRAME_ENTRY && types_active()) {
        types_in_irq = true;
        types_irq_start = now;
        types_af = gb.af; types_bc = gb.bc; types_de = gb.de; types_hl = gb.hl;
        types_sp = gb.sp; types_bank = gb.mbc_rom_bank; types_svbk = gb.cgb_ram_bank;
        types_counter = byte(S_hVBlankCounter);
    }
    if (types_in_irq && bank == P_TYPES_SOUND_BANK && pc == P_TYPES_SOUND) types_sound++;
    if (types_in_irq && bank == 0 && pc == P_TYPES_JOYPAD) types_joypad++;
    if (types_in_irq && bank == 0 && pc == P_TYPES_CLOCK) types_clock++;
    if (types_in_irq && bank == 0 && pc == P_TYPES_FRAME_RETURN) {
        unsigned dots = (unsigned)(now - types_irq_start) / 2;
        if (dots > types_max_irq) types_max_irq = dots;
        types_irq_count++;
        if (gb.af != types_af || gb.bc != types_bc || gb.de != types_de || gb.hl != types_hl ||
                gb.sp != types_sp || gb.mbc_rom_bank != types_bank || gb.cgb_ram_bank != types_svbk ||
                byte(S_hVBlankCounter) != ((types_counter + 1) & 255)) types_bad_registers++;
        types_in_irq = false;
    }
#endif
}

static bool types_active(void)
{
#ifdef DEX_TYPES_MODE7_TRACE
    return byte(S_wPokedexWRAM0Scratch + 0x180) && (byte(S_hVBlank) & 31) == 23;
#else
    return byte(S_hLCDCPointer) == 255;
#endif
}

static bool types_write(GB_gameboy_t *g, uint16_t address, uint8_t value)
{
    (void)value;
    if (address == 0xff69 && types_active()) {
        types_writes++;
        if ((g->io_registers[0x41] & 3) == 3) types_bad_modes++;
        unsigned index = g->io_registers[0x68] & 63;
        if (index < 12 || index > 37 || (index & 7) < 4 || (index & 7) > 5)
            types_bad_indexes++;
    }
    return true;
}

static void types_frame(GB_gameboy_t *g, GB_vblank_type_t kind)
{
#ifdef DEX_PERFORMANCE_TRACE
    perf_frame(g, kind);
#else
    (void)g; (void)kind;
#endif
    if (types_active()) {
        printf("{\"event\":\"types_frame\",\"frame\":%u,\"selection\":%u,\"writes\":%u,"
               "\"bad_modes\":%u,\"bad_indexes\":%u,\"bad_registers\":%u,"
               "\"irq_count\":%u,\"max_irq_dots\":%u,\"sound_updates\":%u,"
               "\"input_updates\":%u,\"clock_updates\":%u,\"mode7\":%s}\n",
               ++types_frames, byte(S_wPokedexWRAM0Scratch), types_writes, types_bad_modes,
               types_bad_indexes, types_bad_registers, types_irq_count, types_max_irq,
               types_sound, types_joypad, types_clock,
#ifdef DEX_TYPES_MODE7_TRACE
               "true"
#else
               "false"
#endif
               );
    }
    types_writes = types_bad_modes = types_bad_indexes = types_bad_registers = 0;
    types_irq_count = types_max_irq = 0;
    types_sound = types_joypad = types_clock = 0;
}
