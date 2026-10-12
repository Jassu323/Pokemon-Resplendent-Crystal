/* Explicit test fixture: call a real ROM0 audio entry point on the live Type
 * owner. Only the synthetic caller's registers/return address are supplied;
 * interrupts, PPU phase, sound state, and the owner continue normally. */
static bool types_audio_command(const char *line)
{
    unsigned pc, de;
    if (sscanf(line, "typesaudio %u %u", &pc, &de) != 2) return false;
    if (pc >= 0x4000 || de > 65535 || !types_active()) return false;
    uint64_t start = ticks;
    while ((!at(P_TYPES_OWNER_BANK, P_TYPES_OWNER) || byte(0xff44) < 128) &&
           ticks - start < 140448 * 4) {
        unsigned before = gb.cycles_since_run;
        step_origin = before;
        GB_cpu_run(&gb);
        ticks += (unsigned)(gb.cycles_since_run - before);
    }
    if (!at(P_TYPES_OWNER_BANK, P_TYPES_OWNER) || byte(0xff44) < 128) {
        puts("{\"event\":\"ok\",\"error\":1,\"fixture\":true}");
        return true;
    }
    unsigned af = gb.af, bc = gb.bc, original_de = gb.de, hl = gb.hl;
    unsigned return_pc = gb.pc, sp = gb.sp, bank = gb.mbc_rom_bank, svbk = gb.cgb_ram_bank;
    gb.sp -= 2;
    GB_write_memory(&gb, gb.sp, return_pc & 255);
    GB_write_memory(&gb, gb.sp + 1, return_pc >> 8);
    gb.pc = pc;
    gb.de = de;
    start = ticks;
    do {
        unsigned before = gb.cycles_since_run;
        step_origin = before;
        GB_cpu_run(&gb);
        ticks += (unsigned)(gb.cycles_since_run - before);
    } while ((gb.pc != return_pc || gb.sp != sp || gb.mbc_rom_bank != bank) &&
             ticks - start < 140448 * 2);
    bool returned = gb.pc == return_pc && gb.sp == sp && gb.mbc_rom_bank == bank &&
                    gb.cgb_ram_bank == svbk;
    if (returned) {
        gb.af = af; gb.bc = bc; gb.de = original_de; gb.hl = hl;
    }
    printf("{\"event\":\"ok\",\"error\":%u,\"fixture\":true,\"returned\":%s}\n",
           !returned, returned ? "true" : "false");
    return true;
}
