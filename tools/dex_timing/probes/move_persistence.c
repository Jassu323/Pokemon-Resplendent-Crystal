/* Private native storage/source harness. Calls execute actual ROM routines.
 * Every battery recovery is a fresh instance; source probes may use checkpoints. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static uint64_t ticks, frames;
static FILE *trace;
static FILE *cpu_trace;
static unsigned cpu_trace_remaining;
static uint16_t pending_pc, pending_sp;
static unsigned pending_bank;
static bool pending;
static unsigned watch_bank[32], watch_pc[32], watch_hits[32], watches;
static struct { unsigned bank, pc, ram_bank, address, table_bank, table; } witnesses[8];
static unsigned witness_count;
static unsigned actor_turn, actor_bank[2], actor_address[2];

static void execution(GB_gameboy_t *g, uint16_t pc, uint8_t opcode)
{
    for (unsigned i = 0; i < watches; i++)
        if (pc == watch_pc[i] && (pc < 0x4000 || g->mbc_rom_bank == watch_bank[i])) watch_hits[i]++;
    for (unsigned i = 0; i < witness_count; i++) {
        if (pc != witnesses[i].pc || (pc >= 0x4000 && g->mbc_rom_bank != witnesses[i].bank)) continue;
        unsigned index = g->bc, live = 0, actor = 0;
        if (witnesses[i].address) {
            unsigned bank = witnesses[i].ram_bank, address = witnesses[i].address;
            if (address == 0xffff) {
                actor = GB_read_memory(g, actor_turn) != 0;
                bank = actor_bank[actor]; address = actor_address[actor];
            }
            live = g->ram[bank * 4096 + (address & 4095)];
            index = 0;
            if (live && live <= 254) {
                unsigned at = witnesses[i].table_bank * 4096 + (witnesses[i].table & 4095) + (live - 1) * 2;
                index = g->ram[at] | g->ram[at + 1] << 8;
            }
        }
        printf("{\"event\":\"witness\",\"point\":%u,\"index\":%u,\"live\":%u,\"actor\":%u,\"ticks\":%" PRIu64 "}\n",
               i, index, live, actor, ticks);
    }
    if (cpu_trace && cpu_trace_remaining) {
        fprintf(cpu_trace, "%u,%u,%u,%u,%u,%u,%u,%u\n", pc < 0x4000 ? 0 : g->mbc_rom_bank,
                pc, opcode, g->af, g->bc, g->de, g->hl, g->sp);
        cpu_trace_remaining--;
    }
}

static uint32_t rgb(GB_gameboy_t *g, uint8_t r, uint8_t v, uint8_t b)
{
    (void)g;
    return (uint32_t)r << 16 | (uint32_t)v << 8 | b;
}

static void frame(GB_gameboy_t *g, GB_vblank_type_t type)
{
    (void)g; (void)type;
    frames++;
}

static bool write_memory(GB_gameboy_t *g, uint16_t address, uint8_t value)
{
    if (trace && address >= 0xa000 && address < 0xc000 &&
            g->mbc_ram_enable && g->mbc_ram_bank < 4) {
        fprintf(trace, "%u,%u,%u,%u,%u\n", g->mbc_ram_bank, address, value,
                g->pc < 0x4000 ? 0 : g->mbc_rom_bank, g->pc);
    }
    return true;
}

static void step(void)
{
    unsigned before = gb.cycles_since_run;
    GB_cpu_run(&gb);
    ticks += (unsigned)(gb.cycles_since_run - before);
}

static bool at(unsigned bank, unsigned pc)
{
    return gb.pc == pc && (pc < 0x4000 || gb.mbc_rom_bank == bank) && !gb.halted;
}

static void hex(const uint8_t *data, unsigned length)
{
    putchar('"');
    for (unsigned i = 0; i < length; i++) printf("%02x", data[i]);
    putchar('"');
}

static void snapshot(uint64_t start, uint64_t first_frame, bool hit)
{
    printf("{\"event\":\"ok\",\"hit\":%s,\"ticks\":%" PRIu64
           ",\"elapsed\":%" PRIu64 ",\"frames\":%" PRIu64
           ",\"pc\":%u,\"bank\":%u,\"svbk\":%u,\"af\":%u,\"bc\":%u,\"de\":%u,"
           "\"hl\":%u,\"sp\":%u,\"sram_enabled\":%s,\"sram_bank\":%u,\"double_speed\":%u}\n",
           hit ? "true" : "false", ticks, ticks - start, frames - first_frame,
           gb.pc, gb.pc < 0x4000 ? 0 : gb.mbc_rom_bank, gb.io_registers[0x70],
           gb.af, gb.bc, gb.de, gb.hl, gb.sp, gb.mbc_ram_enable ? "true" : "false",
           gb.mbc_ram_bank, gb.cgb_double_speed);
}

int main(int argc, char **argv)
{
    if (argc != 4) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_turbo_mode(&gb, true, true);
    GB_set_pixels_output(&gb, pixels);
    GB_set_rgb_encode_callback(&gb, rgb);
    GB_set_vblank_callback(&gb, frame);
    GB_set_write_memory_callback(&gb, write_memory);
    GB_set_execution_callback(&gb, execution);
    if (GB_load_rom(&gb, argv[1]) || GB_load_boot_rom(&gb, argv[2]) ||
            GB_load_battery(&gb, argv[3])) return 2;
    setvbuf(stdout, NULL, _IOLBF, 0);
    char line[4096], path[3500];
    while (fgets(line, sizeof(line), stdin)) {
        unsigned bank, pc, key, count, value, bc, de, extra;
        uint64_t budget;
        if (sscanf(line, "until %u %u %" SCNu64 " %u", &bank, &pc, &budget, &key) == 4) {
            uint64_t start = ticks, first_frame = frames;
            GB_set_key_mask(&gb, key);
            do { step(); } while (!at(bank, pc) && ticks - start < budget * 140448);
            snapshot(start, first_frame, at(bank, pc));
        } else if (sscanf(line, "run %u %u", &count, &key) == 2) {
            uint64_t start = ticks, first_frame = frames;
            GB_set_key_mask(&gb, key);
            while (ticks - start < (uint64_t)count * 140448) step();
            snapshot(start, first_frame, true);
        } else if (sscanf(line, "cycles %" SCNu64 " %u", &budget, &key) == 2) {
            uint64_t start = ticks, first_frame = frames;
            GB_set_key_mask(&gb, key);
            while (ticks - start < budget) step();
            snapshot(start, first_frame, true);
        } else if (sscanf(line, "regs %u %u %u %u", &value, &bc, &de, &count) == 4) {
            gb.af = value & 0xfff0; gb.bc = bc; gb.de = de; gb.hl = count;
            puts("{\"event\":\"ok\"}");
        } else if (!strcmp(line, "follow\n")) {
            /* Observe the existing native caller; do not inject a call frame. */
            pending_pc = GB_read_memory(&gb, gb.sp) | GB_read_memory(&gb, gb.sp + 1) << 8;
            pending_sp = gb.sp + 2;
            pending_bank = gb.mbc_rom_bank;
            pending = true;
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "begin %u %u %u %u", &bank, &pc, &bc, &de) == 4) {
            pending_pc = gb.pc; pending_sp = gb.sp; pending_bank = gb.mbc_rom_bank; pending = true;
            gb.sp -= 2;
            GB_write_memory(&gb, gb.sp, pending_pc & 255);
            GB_write_memory(&gb, gb.sp + 1, pending_pc >> 8);
            gb.af = bank << 8; gb.bc = bc; gb.de = de; gb.hl = pc; gb.pc = S_FarCall_hl;
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "resume %u %u", &count, &key) == 2 && pending) {
            uint64_t start = ticks, first_frame = frames;
            GB_set_key_mask(&gb, key);
            do { step(); } while (!(gb.pc == pending_pc && gb.sp == pending_sp &&
                                    (gb.pc < 0x4000 || gb.mbc_rom_bank == pending_bank)) &&
                                  ticks - start < (uint64_t)count * 140448);
            bool returned = gb.pc == pending_pc && gb.sp == pending_sp;
            snapshot(start, first_frame, returned);
            if (returned) pending = false;
        } else if (sscanf(line, "begin %u %u", &bank, &pc) == 2) {
            uint16_t old_pc = gb.pc;
            gb.sp -= 2;
            GB_write_memory(&gb, gb.sp, old_pc & 255);
            GB_write_memory(&gb, gb.sp + 1, old_pc >> 8);
            gb.af = bank << 8;
            gb.hl = pc;
            gb.pc = S_FarCall_hl;
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "call %u %u %u %u", &bank, &pc, &bc, &de) == 4) {
            uint16_t old_pc = gb.pc, old_sp = gb.sp, old_af = gb.af;
            uint16_t old_bc = gb.bc, old_de = gb.de, old_hl = gb.hl;
            uint64_t start = ticks, first_frame = frames;
            GB_set_key_mask(&gb, 0);
            gb.sp -= 2;
            GB_write_memory(&gb, gb.sp, old_pc & 255);
            GB_write_memory(&gb, gb.sp + 1, old_pc >> 8);
            gb.af = bank << 8;
            gb.bc = bc;
            gb.de = de;
            gb.hl = pc;
            gb.pc = S_FarCall_hl;
            do { step(); } while ((gb.pc != old_pc || gb.sp != old_sp) &&
                                  ticks - start < 1200 * UINT64_C(140448));
            bool returned = gb.pc == old_pc && gb.sp == old_sp;
            snapshot(start, first_frame, returned);
            gb.af = old_af; gb.bc = old_bc; gb.de = old_de; gb.hl = old_hl;
            if (!returned) return 3;
        } else if (sscanf(line, "read %u %u %u", &bank, &pc, &count) == 3 &&
                   bank < 8 && pc >= 0xc000 && pc + count <= 0xe000) {
            printf("{\"event\":\"ok\",\"bytes\":");
            hex(gb.ram + bank * 4096 + (pc & 4095), count);
            puts("}");
        } else if (sscanf(line, "romfixture %u %3499s", &pc, path) == 2 && !(strlen(path) & 1)) {
            unsigned length = (unsigned)strlen(path) / 2;
            if (pc + length > gb.rom_size) return 4;
            for (unsigned i = 0; i < length; i++) {
                unsigned byte;
                if (sscanf(path + i * 2, "%2x", &byte) != 1) return 4;
                gb.rom[pc + i] = byte;
            }
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "fixture %u %u %3499s", &bank, &pc, path) == 3 &&
                   bank < 8 && pc >= 0xa000 && pc < 0xe000 && !(strlen(path) & 1)) {
            /* Explicit fixture injection only; normal calls still execute the ROM. */
            unsigned length = (unsigned)strlen(path) / 2;
            if (pc + length > (pc < 0xc000 ? 0xc000 : 0xe000)) return 4;
            for (unsigned i = 0; i < length; i++) {
                unsigned byte;
                if (sscanf(path + i * 2, "%2x", &byte) != 1) return 4;
                if (pc < 0xc000) gb.mbc_ram[bank * 8192 + pc - 0xa000 + i] = byte;
                else gb.ram[bank * 4096 + (pc & 4095) + i] = byte;
            }
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "direct %u %u %u %u %u", &pc, &value, &bc, &de, &count) == 5 && pc < 0x4000) {
            uint16_t old_pc = gb.pc, old_sp = gb.sp, old_af = gb.af;
            uint16_t old_bc = gb.bc, old_de = gb.de, old_hl = gb.hl;
            uint64_t start = ticks, first_frame = frames;
            GB_set_key_mask(&gb, 0);
            gb.sp -= 2;
            GB_write_memory(&gb, gb.sp, old_pc & 255);
            GB_write_memory(&gb, gb.sp + 1, old_pc >> 8);
            gb.af = value; gb.bc = bc; gb.de = de; gb.hl = count; gb.pc = pc;
            do { step(); } while ((gb.pc != old_pc || gb.sp != old_sp) &&
                                  ticks - start < 1200 * UINT64_C(140448));
            bool returned = gb.pc == old_pc && gb.sp == old_sp;
            snapshot(start, first_frame, returned);
            gb.af = old_af; gb.bc = old_bc; gb.de = old_de; gb.hl = old_hl;
            if (!returned) return 3;
        } else if (sscanf(line, "io %u %u", &pc, &value) == 2 &&
                   (pc == 0xff70 || pc == 0 || pc == 0x4000)) {
            GB_write_memory(&gb, pc, value);
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "hram %u %u", &pc, &value) == 2 && pc >= 0xff80 && pc < 0xffff) {
            GB_write_memory(&gb, pc, value);
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "watch %u %u", &bank, &pc) == 2 && watches < 32) {
            watch_bank[watches] = bank; watch_pc[watches] = pc; watch_hits[watches++] = 0;
            puts("{\"event\":\"ok\"}");
        } else if (!strcmp(line, "watchcounts\n")) {
            printf("{\"event\":\"ok\",\"hits\":[");
            for (unsigned i = 0; i < watches; i++) printf("%s%u", i ? "," : "", watch_hits[i]);
            puts("]}");
        } else if (!strcmp(line, "watchclear\n")) {
            watches = 0;
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "witness %u %u %u %u %u %u", &bank, &pc, &value, &bc, &de, &extra) == 6 && witness_count < 8) {
            witnesses[witness_count].bank = bank; witnesses[witness_count].pc = pc;
            witnesses[witness_count].ram_bank = value; witnesses[witness_count].address = bc;
            witnesses[witness_count].table_bank = de; witnesses[witness_count++].table = extra;
            puts("{\"event\":\"ok\"}");
        } else if (!strcmp(line, "witnessclear\n")) {
            witness_count = 0;
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "actors %u %u %u %u %u", &pc, &bank, &value, &bc, &de) == 5) {
            actor_turn = pc; actor_bank[0] = bank; actor_address[0] = value;
            actor_bank[1] = bc; actor_address[1] = de;
            puts("{\"event\":\"ok\"}");
        } else if (sscanf(line, "cpulog %3499s %u", path, &count) == 2) {
            if (cpu_trace) fclose(cpu_trace);
            cpu_trace = fopen(path, "w");
            cpu_trace_remaining = count;
            printf("{\"event\":\"ok\",\"error\":%d}\n", !cpu_trace);
        } else if (sscanf(line, "trace %3499s", path) == 1) {
            if (trace) fclose(trace);
            trace = !strcmp(path, "off") ? NULL : fopen(path, "w");
            printf("{\"event\":\"ok\",\"error\":%d}\n", !trace && strcmp(path, "off") != 0);
        } else if (sscanf(line, "load %3499s", path) == 1) {
            pending = false;
            printf("{\"event\":\"ok\",\"error\":%d}\n", GB_load_state(&gb, path));
        } else if (sscanf(line, "battery %3499s", path) == 1) {
            printf("{\"event\":\"ok\",\"error\":%d}\n", GB_save_battery(&gb, path));
        } else if (!strcmp(line, "peek\n")) {
            snapshot(ticks, frames, true);
        } else if (!strcmp(line, "quit\n")) break;
        else return 4;
    }
    if (trace) fclose(trace);
    if (cpu_trace) fclose(cpu_trace);
    GB_free(&gb);
    return 0;
}
