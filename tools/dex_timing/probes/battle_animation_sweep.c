/* Private animation-call fixtures. Executes the linked engine, not a model. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include SWEEP_SYMBOLS

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static uint64_t ticks, start, previous_tick, logical_hash, pixel_hash;
static unsigned origin, updates, intervals[8], displays, lcd_active;
static unsigned lcd_entries, vblank_entries;
static bool tracing;

static unsigned read_field(unsigned bank, unsigned address)
{
    if (address >= 0xff80) return gb.hram[address - 0xff80];
    return gb.ram[(address < 0xd000 ? 0 : bank) * 4096 + (address & 4095)];
}

static void put_field(unsigned bank, unsigned address, unsigned value)
{
    if (address >= 0xff80) gb.hram[address - 0xff80] = value;
    else gb.ram[(address < 0xd000 ? 0 : bank) * 4096 + (address & 4095)] = value;
}

static uint64_t now(void)
{
    return (ticks + (unsigned)(gb.cycles_since_run - origin)) / 2;
}

static void hash_byte(unsigned value)
{
    logical_hash = (logical_hash ^ (value & 255)) * UINT64_C(1099511628211);
}

static void observe(GB_gameboy_t *g, uint16_t pc, uint8_t opcode)
{
    (void)opcode;
    if (!tracing || g->halted) return;
    unsigned bank = pc < 0x4000 ? 0 : g->mbc_rom_bank;
    if (!bank && pc == SW_LCD) lcd_entries++;
    if (!bank && pc == SW_VBlank) vblank_entries++;
    if (bank != SW_RunBattleAnimScript_done_bank || pc != SW_RunBattleAnimScript_done) return;
    uint64_t t = now();
    if (updates) {
        unsigned frames = (unsigned)((t - previous_tick + 35112) / 70224);
        intervals[frames < 7 ? frames : 7]++;
    }
    previous_tick = t;
    updates++;
    unsigned script = read_field(SWB_wBattleAnimAddress, SW_wBattleAnimAddress) |
                      read_field(SWB_wBattleAnimAddress, SW_wBattleAnimAddress + 1) << 8;
    script -= SW_BattleAnimationScriptsStart;
    hash_byte(script); hash_byte(script >> 8);
    hash_byte(read_field(SWB_wBattleAnimDelay, SW_wBattleAnimDelay));
    hash_byte(read_field(SWB_wBattleAnimParam, SW_wBattleAnimParam));
    for (unsigned i = 0; i < 160; i++)
        hash_byte(read_field(SWB_wShadowOAM, SW_wShadowOAM + i));
    for (unsigned i = 0; i < 280; i++)
        hash_byte(read_field(SWB_wActiveAnimObjects, SW_wActiveAnimObjects + i));
    for (unsigned i = 0; i < 20; i++)
        hash_byte(read_field(SWB_wBGEffect1, SW_wBGEffect1 + i));
    lcd_active += read_field(SWB_hLCDCPointer, SW_hLCDCPointer) != 0;
}

static void frame(GB_gameboy_t *g, GB_vblank_type_t type)
{
    (void)g; (void)type;
    if (tracing) {
        displays++;
        /* The first partial frame precedes the call boundary. Its host output
         * buffer is not restored by GB_load_state; compare full later frames. */
        if (displays > 1) {
            for (unsigned i = 0; i < 160 * 144; i++) {
                for (unsigned channel = 0; channel < 4; channel++)
                    pixel_hash = (pixel_hash ^ ((pixels[i] >> (channel * 8)) & 255)) *
                                 UINT64_C(1099511628211);
            }
        }
    }
}

static void discard(GB_gameboy_t *g, GB_sample_t *sample) { (void)g; (void)sample; }
static void host_log(GB_gameboy_t *g, const char *message, GB_log_attributes_t attributes)
{ (void)g; (void)attributes; fputs(message, stderr); }

static void step(void)
{
    unsigned before = gb.cycles_since_run;
    origin = before;
    GB_cpu_run(&gb);
    ticks += (unsigned)(gb.cycles_since_run - before);
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    GB_init(&gb, GB_MODEL_CGB_E);
    GB_set_pixels_output(&gb, pixels);
    GB_set_sample_rate(&gb, 44100);
    GB_apu_set_sample_callback(&gb, discard);
    GB_set_turbo_mode(&gb, true, true);
    GB_set_log_callback(&gb, host_log);
    GB_set_execution_callback(&gb, observe);
    GB_set_vblank_callback(&gb, frame);
    if (GB_load_rom(&gb, argv[1])) return 3;
    setvbuf(stdout, NULL, _IOLBF, 0);
    char line[2048], state[1536];
    unsigned id, side, param, phase;
    while (fgets(line, sizeof(line), stdin)) {
        if (sscanf(line, "%1535s %u %u %u %u", state, &id, &side, &param, &phase) != 5) return 4;
        tracing = false;
        if (GB_load_state(&gb, state)) return 5;
        unsigned park_pc = gb.pc, park_bank = gb.mbc_rom_bank, park_sp = gb.sp;
        ticks = 0;
        uint64_t until = phase;
        while (ticks / 2 < until) step();
        /* A phase delay can land inside an interrupt. Finish it naturally and
         * rejoin the original caller boundary before invoking another routine. */
        while (!(gb.pc == park_pc && gb.mbc_rom_bank == park_bank && gb.sp == park_sp && gb.ime) &&
                ticks / 2 < phase + 60 * UINT64_C(70224)) step();
        if (gb.pc != park_pc || gb.sp != park_sp || !gb.ime) return 7;
        unsigned sp = gb.sp, wram = gb.cgb_ram_bank, vblank = read_field(SWB_hVBlank, SW_hVBlank);
        bool speed = gb.cgb_double_speed;
        if (sp < 0xc020 || sp > 0xc0ff || !read_field(SWB_wBattleMode, SW_wBattleMode)) return 6;
        /* Only explicit inputs and the native call boundary change. The PPU,
         * CPU speed, interrupt state, RNG and animation counters are untouched. */
        put_field(SWB_hBattleTurn, SW_hBattleTurn, side);
        put_field(SWB_wBattleAnimParam, SW_wBattleAnimParam, param);
        put_field(SWB_wBattleAfterAnim, SW_wBattleAfterAnim, 0);
        if (id == SW_ThrowPokeBall_id) {
            put_field(SWB_wThrownBallWobbleCount, SW_wThrownBallWobbleCount, 0);
            put_field(SWB_wFinalCatchRate, SW_wFinalCatchRate, 255);
            put_field(SWB_wWildMon, SW_wWildMon, 1);
        }
        GB_write_memory(&gb, 0x2000, SW_Call_PlayBattleAnim_bank);
        put_field(SWB_hROMBank, SW_hROMBank, SW_Call_PlayBattleAnim_bank);
        gb.sp -= 2;
        put_field(0, gb.sp, 0);
        put_field(0, gb.sp + 1, 1);
        gb.de = id;
        gb.pc = SW_Call_PlayBattleAnim;
        gb.halted = false;
        updates = displays = lcd_active = lcd_entries = vblank_entries = 0;
        memset(intervals, 0, sizeof(intervals));
        previous_tick = 0;
        logical_hash = UINT64_C(14695981039346656037);
        pixel_hash = UINT64_C(14695981039346656037);
        start = ticks / 2;
        unsigned start_ly = gb.io_registers[0x44];
        tracing = true;
        while (!(gb.pc == 0x100 && gb.sp == sp) && ticks / 2 - start < 3000 * UINT64_C(70224)) step();
        tracing = false;
        bool returned = gb.pc == 0x100 && gb.sp == sp;
        printf("{\"id\":%u,\"side\":%u,\"param\":%u,\"phase\":%u,\"elapsed_t\":%" PRIu64
               ",\"returned\":%s,\"wram_restored\":%s,\"speed_restored\":%s,"
               "\"vblank_restored\":%s,\"rom_restored\":%s,\"updates\":%u,\"displays\":%u,"
               "\"lcd_active_updates\":%u,\"lcd_interrupts\":%u,\"vblank_interrupts\":%u,"
               "\"start_ly\":%u,\"start_t\":%" PRIu64 ",\"logical_hash\":\"%016" PRIx64
               "\",\"pixel_hash\":\"%016" PRIx64 "\",\"full_pixel_frames\":%u,\"intervals\":[",
               id, side, param, phase, ticks / 2 - start, returned ? "true" : "false",
               gb.cgb_ram_bank == wram ? "true" : "false", gb.cgb_double_speed == speed ? "true" : "false",
               read_field(SWB_hVBlank, SW_hVBlank) == vblank ? "true" : "false",
               gb.mbc_rom_bank == SW_Call_PlayBattleAnim_bank ? "true" : "false",
               updates, displays, lcd_active, lcd_entries, vblank_entries, start_ly, start, logical_hash,
               pixel_hash, displays ? displays - 1 : 0);
        for (unsigned i = 0; i < 8; i++) printf("%s%u", i ? "," : "", intervals[i]);
        printf("],\"pc\":%u,\"bank\":%u,\"sp\":%u}\n", gb.pc, gb.mbc_rom_bank, gb.sp);
    }
    GB_free(&gb);
}
