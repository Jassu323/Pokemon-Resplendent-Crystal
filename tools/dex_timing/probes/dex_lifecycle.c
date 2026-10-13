/* Read-only lifecycle observation. Never linked into the game cartridge. */
static unsigned life_sfx_last = 255;

static unsigned life_sfx_mask(void)
{
    const uint8_t *ram = gb.ram + LIFE_AUDIO_BANK * 4096;
    return ((ram[S_wChannel5Flags1 & 4095] & 1) != 0) |
           (((ram[S_wChannel6Flags1 & 4095] & 1) != 0) << 1) |
           (((ram[S_wChannel7Flags1 & 4095] & 1) != 0) << 2) |
           (((ram[S_wChannel8Flags1 & 4095] & 1) != 0) << 3);
}

static void life_step(uint64_t now)
{
    unsigned mask = life_sfx_mask();
    if (mask == life_sfx_last) return;
    printf("{\"event\":\"life_sfx\",\"t\":%" PRIu64 ",\"mask\":%u,\"lcdc\":%u,"
           "\"pc\":%u,\"bank\":%u}\n", now, mask, gb.io_registers[0x40], gb.pc, gb.mbc_rom_bank);
    life_sfx_last = mask;
}

static void life_frame(uint64_t now, unsigned frame)
{
    printf("{\"event\":\"life_frame\",\"t\":%" PRIu64 ",\"display\":%u,"
           "\"scx\":%u,\"scy\":%u,\"wx\":%u,\"wy\":%u,"
           "\"pending_scx\":%u,\"pending_wx\":%u,\"pending_wy\":%u,\"sfx\":%u}\n",
           now, frame, gb.io_registers[0x43], gb.io_registers[0x42], gb.io_registers[0x4b],
           gb.io_registers[0x4a], byte(LIFE_hSCX), byte(LIFE_hWX), byte(LIFE_hWY), life_sfx_mask());
}
