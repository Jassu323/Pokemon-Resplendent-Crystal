#include "Core/gb.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static FILE *trace;
static unsigned trace_origin;

/* The historical calibration remains the default. Integrated validation
 * supplies these addresses from the new link, not from stale breakpoints. */
#ifndef DEX_PUBLICATION_PC
#define DEX_PUBLICATION_PC 0x5ea5
#define DEX_STAGE_PC 0x6483
#define DEX_PRODUCER_PC 0x6282
#define DEX_WAIT_PC 0x047e
#define DEX_WAIT_BANK 0
#define DEX_MISS_PC 0x67fc
#define DEX_STOP_PC 0x0063
#endif

static void trace_instruction(GB_gameboy_t *gb, uint16_t pc, uint8_t opcode)
{
    if (opcode == 0x76) return; /* HALT idle cycles are not executed instructions. */
    fprintf(trace, "%u %02x %04x %04x %04x %04x %04x %04x %u %u %u\n",
        (gb->cycles_since_run-trace_origin)/2, pc<0x4000?0:gb->mbc_rom_bank, pc,
        gb->af,gb->bc,gb->de,gb->hl,gb->sp,gb->ime,GB_read_memory(gb,0xff44),
        gb->io_registers[GB_IO_IF]&15);
}

/* Independent host diagnostic. ROM, synthetic fixtures, and optional captured
 * emulator states are read-only. This program never saves emulated state. */
static void read_exact(FILE *file, void *data, size_t size)
{
    if (fread(data, 1, size, file) != size) {
        fprintf(stderr, "Truncated diagnostic fixture\n");
        exit(2);
    }
}

static void snapshot(GB_gameboy_t *gb, unsigned index, unsigned origin)
{
    const unsigned char *w4 = gb->ram + 4 * 4096;
    printf("stop=%u t=%u pc=%04x bank=%02x af=%04x bc=%04x de=%04x hl=%04x sp=%04x "
           "ly=%u mode=%u if=%u div=%04x tima=%02x display=%d remain=%d "
           "pixel=%u oam_index=%u scx=%u wx=%u wy=%u counter=%u "
           "cache=%u remaining=%u compressed=%u read_address=%04x "
           "write_address=%04x source_address=%04x ime=%u model=%u "
           "div_state=%u div_cycles=%d pending_cycles=%u if_raw=%u ie=%u ",
           index, (gb->cycles_since_run-origin)/2, gb->pc, gb->mbc_rom_bank,
           gb->af, gb->bc, gb->de, gb->hl, gb->sp,
           GB_read_memory(gb, 0xff44), GB_read_memory(gb, 0xff41)&3,
           gb->io_registers[GB_IO_IF]&15, gb->div_counter,
           GB_read_memory(gb, 0xff05), gb->display_state, -gb->display_cycles/2,
           gb->position_in_line, gb->oam_search_index,
           gb->io_registers[GB_IO_SCX], gb->io_registers[GB_IO_WX], gb->io_registers[GB_IO_WY],
           GB_read_memory(gb, 0xff9b), w4[0xff4],
           GB_read_memory(gb, 0xfff2) + 256 * GB_read_memory(gb, 0xfff3),
           w4[0xff5] + 256 * w4[0xff6],
           GB_read_memory(gb, 0xffef) + 256 * GB_read_memory(gb, 0xfff0),
           w4[0xff9] + 256 * w4[0xffa], w4[0xff7] + 256 * w4[0xff8],
           gb->ime, gb->model, gb->div_state, gb->div_cycles, gb->pending_cycles,
           GB_read_memory(gb,0xff0f), gb->interrupt_enable);
    printf("audio=");
    for (unsigned a=0xffee; a<0xfff4; a++) printf("%02x",GB_read_memory(gb,a));
    printf(" audio_cache=");
    for (unsigned i=0xff4; i<0xffc; i++) printf("%02x",w4[i]);
    printf(" timers=");
    for (unsigned a=0xff04; a<0xff08; a++) printf("%02x",GB_read_memory(gb,a));
    puts("");
    for (unsigned a = 0xc72e; a < 0xc72e + 27; a++) printf("%02x", GB_read_memory(gb, a));
    puts("");
    for (unsigned a = 0xc758; a < 0xc758+139; a++) printf("%02x", GB_read_memory(gb, a));
    puts("");
}

static int export_fixture(GB_gameboy_t *gb, const char *path)
{
    /* Physical RAM/VRAM must not be sampled through a currently blocked bus.
     * This export omits PPU internals; it is not a replacement save state. */
    unsigned char memory[65536];
    for (unsigned a=0; a<65536; a++) memory[a]=GB_read_memory(gb, a);
    memcpy(memory+0xc000, gb->ram, 4096);
    unsigned h[]={606, gb->af, gb->bc, gb->de, gb->hl, gb->sp, gb->pc,
        gb->mbc_rom_bank, gb->cgb_ram_bank, gb->cgb_vram_bank, gb->div_counter,
        gb->io_registers[GB_IO_TIMA], gb->io_registers[GB_IO_TMA],
        gb->io_registers[GB_IO_TAC], gb->io_registers[GB_IO_IF]&15, gb->interrupt_enable};
    FILE *file=fopen(path, "wb");
    if (!file) return 2;
    bool ok=fwrite("DEXCORE1", 1, 8, file)==8;
    for (unsigned i=0; i<16; i++) {
        unsigned char word[]={h[i],h[i]>>8,h[i]>>16,h[i]>>24};
        ok &= fwrite(word, 1, 4, file)==4;
    }
    ok &= fwrite(memory, 1, sizeof(memory), file)==sizeof(memory);
    ok &= fwrite(gb->ram, 1, 32768, file)==32768;
    ok &= fwrite(gb->vram, 1, 16384, file)==16384;
    ok &= fclose(file)==0;
    return ok?0:2;
}

static int load_fixture(GB_gameboy_t *gb, const char *path, int div_subphase)
{
    FILE *fixture = fopen(path, "rb");
    if (!fixture) return 2;
    unsigned char magic[8], raw_header[64], memory[65536], banks[32768], vram[16384];
    read_exact(fixture, magic, sizeof(magic));
    if (memcmp(magic, "DEXCORE1", 8)) return 2;
    read_exact(fixture, raw_header, sizeof(raw_header));
    unsigned h[16];
    for (unsigned i=0; i<16; i++) h[i]=(unsigned)raw_header[i*4] | (unsigned)raw_header[i*4+1]<<8 |
        (unsigned)raw_header[i*4+2]<<16 | (unsigned)raw_header[i*4+3]<<24;
    read_exact(fixture, memory, sizeof(memory));
    read_exact(fixture, banks, sizeof(banks));
    read_exact(fixture, vram, sizeof(vram));
    fclose(fixture);

    gb->cgb_mode = true;
    gb->boot_rom_finished = true;
    gb->disable_rendering = true;
    GB_write_memory(gb, 0xff40, 0);
    GB_write_memory(gb, 0xff43, 5);
    GB_write_memory(gb, 0xff4a, 0);
    GB_write_memory(gb, 0xff4b, 167);
    GB_write_memory(gb, 0xff41, 8);
    GB_write_memory(gb, 0xff40, 0xe3);
    unsigned reference=0, frames=0;
    for (unsigned t=1;;t++) {
        GB_advance_cycles(gb, 1);
        if (gb->io_registers[GB_IO_IF]&1) { reference=t; frames++; }
        gb->io_registers[GB_IO_IF]=0;
        if (frames==3 && t-reference==h[0]) break;
        if (t>4*70224) return 2;
    }
    memcpy(gb->ram, memory+0xc000, 4096);
    memcpy(gb->ram+4096, banks+4096, 7*4096);
    memcpy(gb->vram, vram, sizeof(vram));
    memcpy(gb->hram, memory+0xff80, sizeof(gb->hram));
    memset(gb->oam, 0, sizeof(gb->oam));
    gb->af=h[1]; gb->bc=h[2]; gb->de=h[3]; gb->hl=h[4]; gb->sp=h[5]; gb->pc=h[6];
    GB_write_memory(gb, 0x2000, h[7]);
    GB_write_memory(gb, 0xff70, h[8]);
    GB_write_memory(gb, 0xff4f, h[9]);
    gb->div_counter=h[10]; gb->div_state=2;
    gb->div_cycles=div_subphase;
    if (gb->div_cycles < -3 || gb->div_cycles > 0) return 2;
    gb->tima_reload_state=GB_TIMA_RUNNING;
    gb->io_registers[GB_IO_TIMA]=h[11];
    gb->io_registers[GB_IO_TMA]=h[12];
    gb->io_registers[GB_IO_TAC]=h[13];
    gb->io_registers[GB_IO_IF]=h[14] | (memory[0xff0f]&0x10);
    gb->interrupt_enable=h[15];
    gb->ime=0;
    gb->halted=gb->stopped=gb->ime_toggle=gb->halt_bug=gb->just_halted=false;
    gb->pending_cycles=0;
    gb->io_registers[GB_IO_SC]=0;
    /* Restore CPU-visible sound controls for the resumed music engine. This
     * does not reconstruct oscillator/envelope phase or validate audio output. */
    GB_write_memory(gb, 0xff26, memory[0xff26]);
    for (unsigned a=0xff10; a<0xff26; a++) GB_write_memory(gb, a, memory[a]);
    return 0;
}

int main(int argc, char **argv)
{
    bool end_to_end=argc>=2 && !strcmp(argv[1], "--end-to-end");
    bool full=end_to_end || (argc>=2 && !strcmp(argv[1], "--full"));
    if (full) { argc--; argv++; }
    bool saved_state=argc>=2 && !strcmp(argv[1], "--state");
    unsigned offset=saved_state?1:0;
    if (argc < 3+offset || argc > (saved_state?6:5)) {
        fprintf(stderr, "Usage: %s ROM fixture [trace|-] [div_subphase]\n"
                        "       %s --state ROM state [trace|-] [export_fixture]\n", argv[0], argv[0]);
        return 2;
    }
    GB_gameboy_t *gb=calloc(1, sizeof(*gb));
    GB_init(gb, GB_MODEL_CGB_E);
    if (GB_load_rom(gb, argv[1+offset])) return 2;
    int result=saved_state? GB_load_state(gb, argv[2+offset]) :
        load_fixture(gb, argv[2], argc==5?atoi(argv[4]):-3);
    if (result) {
        fprintf(stderr, "Could not load diagnostic input: %d\n", result);
        return 2;
    }
    gb->disable_rendering=true;
    if (gb->pc!=DEX_PUBLICATION_PC || gb->mbc_rom_bank!=0x77 || gb->cgb_double_speed) {
        fprintf(stderr, "Expected normal-speed publication entry at 77:%04x\n", DEX_PUBLICATION_PC);
        return 2;
    }
    if (saved_state && argc==6 && export_fixture(gb, argv[5])) return 2;

    unsigned origin=gb->cycles_since_run, stop=1;
    const unsigned pcs[]={DEX_PUBLICATION_PC,DEX_STAGE_PC,DEX_PRODUCER_PC,DEX_WAIT_PC,DEX_MISS_PC};
    const unsigned rombanks[]={0x77,0xa0,0xa0,DEX_WAIT_BANK,0xa0};
    const unsigned end_pcs[]={DEX_PUBLICATION_PC,DEX_MISS_PC,DEX_STOP_PC};
    const unsigned end_banks[]={0x77,0xa0,0};
    const unsigned *targets=end_to_end?end_pcs:pcs;
    const unsigned *target_banks=end_to_end?end_banks:rombanks;
    unsigned target_count=end_to_end?3:5;
    trace=argc>=4+offset && strcmp(argv[3+offset], "-")? fopen(argv[3+offset], "w") : NULL;
    trace_origin=origin;
    if (trace) GB_set_execution_callback(gb, trace_instruction);
    snapshot(gb, 0, origin);
    bool completed=false;
    while ((full || stop<5) && gb->cycles_since_run-origin < (full?40:8)*4194304u) {
        GB_cpu_run(gb);
        if (stop<target_count && gb->pc==targets[stop] &&
                (!target_banks[stop] || gb->mbc_rom_bank==target_banks[stop])) {
            snapshot(gb, stop++, origin);
        }
        if (full && gb->pc==DEX_WAIT_PC && (!DEX_WAIT_BANK || gb->mbc_rom_bank==DEX_WAIT_BANK) &&
                gb->ime && GB_read_memory(gb,0xc738)==3 &&
                !GB_read_memory(gb,0xfff1)) {
            snapshot(gb,stop++,origin);
            completed=true;
            break;
        }
    }
    if (trace) fclose(trace);
    GB_free(gb);
    free(gb);
    return (full?completed:stop==5)?0:1;
}
