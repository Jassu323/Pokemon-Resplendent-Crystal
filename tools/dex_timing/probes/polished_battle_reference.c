/* Host-only Polished comparison. Fixture commands run before move capture;
 * animation execution, CPU speed, PPU timing and audio are never patched. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include POLISHED_SYMBOLS

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static uint64_t ticks;
static unsigned step_origin;
static uint32_t rgb(GB_gameboy_t *g, uint8_t r, uint8_t v, uint8_t b)
{ (void)g; return (uint32_t)r << 16 | (uint32_t)v << 8 | b; }
static unsigned byte(unsigned address) { return GB_read_memory(&gb, address); }
static unsigned word(unsigned address) { return byte(address) | byte(address + 1) << 8; }
static void hex(const uint8_t *p, unsigned n)
{ putchar('"'); for (unsigned i = 0; i < n; i++) printf("%02x", p[i]); putchar('"'); }
#include "performance.c"

static void observe(GB_gameboy_t *g, uint16_t pc, uint8_t opcode)
{ (void)g; (void)opcode; if (!gb.halted) perf_observe(pc < 0x4000 ? 0 : gb.mbc_rom_bank, pc); }
static bool at(unsigned bank, unsigned pc)
{ return !gb.halted && gb.pc == pc && (pc < 0x4000 || gb.mbc_rom_bank == bank); }
static void step(void)
{
    unsigned before = gb.cycles_since_run;
    step_origin = before;
    GB_cpu_run(&gb);
    ticks += (unsigned)(gb.cycles_since_run - before);
}
static void put(unsigned bank, unsigned address, unsigned value)
{
    if (address >= 0xc000 && address < 0xe000)
        gb.ram[(address < 0xd000 ? 0 : bank) * 4096 + (address & 4095)] = value;
    else if (address >= 0xff80 && address < 0xffff) gb.hram[address - 0xff80] = value;
    else { fprintf(stderr, "Fixture write outside WRAM/HRAM\n"); exit(3); }
}
static void snapshot(int hit)
{
    printf("{\"event\":\"stop\",\"hit\":%d,\"t\":%" PRIu64
           ",\"pc\":%u,\"bank\":%u,\"double_speed\":%u,\"sp\":%u,\"ly\":%u,"
           "\"party\":%u,\"menu\":%u,\"battle\":%u,\"crash\":%u}\n",
           hit, ticks / 2, gb.pc, gb.mbc_rom_bank, gb.cgb_double_speed, gb.sp,
           byte(0xff44), gb.ram[B_wPartyCount * 4096 + (S_wPartyCount & 4095)],
           byte(S_wMenuCursorPosition), byte(S_wBattleMode), byte(S_hCrashCode));
}
static void enter(unsigned bank, unsigned pc)
{
    gb.sp -= 2;
    put(0, gb.sp, gb.pc & 255);
    put(0, gb.sp + 1, gb.pc >> 8);
    GB_write_memory(&gb, 0x2000, bank);
    put(0, S_hROMBank, bank);
    gb.pc = pc;
}

int main(int argc, char **argv)
{
    if (argc != 4) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_turbo_mode(&gb, true, true);
    GB_set_color_correction_mode(&gb, GB_COLOR_CORRECTION_DISABLED);
    GB_set_pixels_output(&gb, pixels);
    GB_set_rgb_encode_callback(&gb, rgb);
    GB_set_execution_callback(&gb, observe);
    GB_set_vblank_callback(&gb, perf_frame);
    if (GB_load_rom(&gb, argv[1]) || GB_load_boot_rom(&gb, argv[2]) ||
        GB_load_battery(&gb, argv[3])) return 2;
    setvbuf(stdout, NULL, _IOLBF, 0);
    char line[4096];
    while (fgets(line, sizeof(line), stdin)) {
        unsigned bank, pc, keys, address, value;
        uint64_t budget, mask;
        bool direct = sscanf(line, "restorerun %u %u %" SCNu64 " %u", &bank, &pc, &budget, &keys) == 4;
        if (direct || sscanf(line, "run %" SCNu64 " %" SCNu64 " %u", &mask, &budget, &keys) == 3) {
            GB_set_key_mask(&gb, keys);
            uint64_t start = ticks;
            int hit = -1;
            do { step(); if (direct && at(bank, pc)) hit = 0; }
            while (hit < 0 && ticks - start < budget * 2);
            snapshot(hit);
        } else if (sscanf(line, "put %u %u %u", &bank, &address, &value) == 3) {
            if (perf_enabled) return 4;
            put(bank, address, value);
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "invoke %u %u", &bank, &pc) == 2) {
            if (perf_enabled) return 4;
            unsigned old_pc = gb.pc, old_sp = gb.sp, old_bank = gb.mbc_rom_bank;
            uint16_t registers[GB_REGISTERS_16_BIT];
            memcpy(registers, gb.registers, sizeof(registers));
            enter(bank, pc);
            uint64_t start = ticks;
            while (!(gb.pc == old_pc && gb.sp == old_sp) && ticks - start < 70224 * 2 * 600) step();
            unsigned error = !(gb.pc == old_pc && gb.sp == old_sp);
            GB_write_memory(&gb, 0x2000, old_bank);
            put(0, S_hROMBank, old_bank);
            memcpy(gb.registers, registers, sizeof(registers));
            printf("{\"event\":\"ok\",\"error\":%u}\n", error);
        } else if (sscanf(line, "enter %u %u", &bank, &pc) == 2) {
            if (perf_enabled) return 4;
            enter(bank, pc);
            puts("{\"event\":\"ok\"}");
        } else if (perf_command(line)) {
        } else if (!strcmp(line, "m\n") || !strcmp(line, "peek\n")) snapshot(-1);
        else if (!strncmp(line, "save ", 5) || !strncmp(line, "load ", 5)) {
            line[strcspn(line, "\r\n")] = 0;
            int error = line[0] == 's' ? GB_save_state(&gb, line + 5) : GB_load_state(&gb, line + 5);
            if (line[0] == 'l') ticks = 0;
            printf("{\"event\":\"ok\",\"error\":%d}\n", error);
        } else if (!strncmp(line, "image ", 6)) {
            line[strcspn(line, "\r\n")] = 0;
            FILE *file = fopen(line + 6, "wb");
            if (!file) return 2;
            fprintf(file, "P6\n160 144\n255\n");
            for (unsigned i = 0; i < 160 * 144; i++) {
                uint8_t p[] = {pixels[i] >> 16, pixels[i] >> 8, pixels[i]};
                fwrite(p, 1, 3, file);
            }
            printf("{\"event\":\"ok\",\"error\":%d}\n", fclose(file));
        } else if (!strcmp(line, "quit\n")) break;
        else return 2;
    }
    if (perf_audio_file) fclose(perf_audio_file);
    GB_free(&gb);
    return 0;
}
