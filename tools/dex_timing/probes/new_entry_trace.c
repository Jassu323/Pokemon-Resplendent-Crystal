/* Headless New Dex Entry audit. Read-only unless a synthetic phase test is requested. */
#include "Core/gb.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static GB_gameboy_t gb;
static uint32_t pixels[160 * 144];
static uint8_t reference[32][49 * 16];
static unsigned references, frame_number, serial, displayed_serial, phase;
static uint64_t ticks, last_clock, finish_ticks;
static uint64_t idle_ticks;
static unsigned step_origin, calls;
static bool finished, executed;
static unsigned input_mode, first_publication, return_pc, return_sp, last_keys;
static bool returned;
static const char *screen_prefix;
static unsigned screens;
static unsigned bad_pictures;
static unsigned waits, second_wait_display;
/* HOST-ONLY presentation audit: check every displayed old/new text rectangle,
 * not just a snapshot scheduled relative to the return of the page routine. */
static uint8_t description_old[91], description_new[91];
static bool description_started, description_ready;
static bool compact, planned;
/* HOST-ONLY instrumentation: optional bounded instruction trace, in T-cycles. */
static uint64_t instruction_from, instruction_to;
/* HOST-ONLY fault fixture: alter one initial TIMA write, never the reload period. */
static unsigned timer_first_clocks;
static bool timer_phase_armed, timer_phase_applied;
static bool interesting[65536];
static struct { unsigned anchor, start, duration, keys; } inputs[2048];
static unsigned input_count, last_input_display;
static struct {
    unsigned function, sp, ret, bank, id, serial, phase, cache, remaining, b;
    unsigned source, dest, vbk, requested;
    uint64_t start, self;
} active[128];
static unsigned depth;
static uint64_t self[3][64], inclusive[3][64], counts[3][64], other[3];

static uint32_t rgb(GB_gameboy_t *g, uint8_t r, uint8_t v, uint8_t b)
{ (void)g; return (uint32_t)r << 16 | (uint32_t)v << 8 | b; }
/* Bus reads may synchronize the PPU, including re-entering a display callback.
 * Observation must use physical storage and must not advance any device. */
static unsigned byte(unsigned a)
{
    if (a>=0xff80 && a<0xffff) return gb.hram[a-0xff80];
    if (a==0xff4f) return gb.cgb_vram_bank;
    if (a>=0xff00 && a<0xff80) return gb.io_registers[a-0xff00];
    if (a>=0xc000 && a<0xd000) return gb.ram[a-0xc000];
    if (a>=0xd000 && a<0xe000) return gb.ram[gb.cgb_ram_bank*4096+(a&4095)];
    fprintf(stderr,"Unsupported observation address: %04x\n",a);exit(11);
}
static unsigned word(unsigned a) { return byte(a) | byte(a+1) << 8; }
static unsigned ram(unsigned bank, unsigned a) { return gb.ram[bank*4096 + (a & 4095)]; }
static uint64_t now(void) { return ticks + (unsigned)(gb.cycles_since_run - step_origin); }
static unsigned cache(void) { return ram(4, 0xdff4); }
static unsigned remain(void) { return word(S_hSampledCryBlocks); }
static unsigned bank_for(unsigned pc) { return pc < 0x4000 ? 0 : gb.mbc_rom_bank; }

static void event(const char *name, uint64_t t, unsigned pc)
{
    printf("{\"event\":\"%s\",\"t\":%" PRIu64 ",\"pc\":%u,\"bank\":%u,"
           "\"display\":%u,\"serial\":%u,\"phase\":%u,\"scene\":%u,\"idle\":%u,"
           "\"command\":%u,\"duration\":%u,\"wait\":%u,\"ly\":%u,\"mode\":%u,"
           "\"cache\":%u,\"remaining\":%u,\"audio\":%u,\"idle_t\":%" PRIu64 ","
           "\"hvblank\":%u,\"frame_counter\":%u,\"dex_status\":%u,\"misses\":%u,"
           "\"joy_down\":%u,\"joy_last\":%u,\"joy_hardware\":%u,"
           "\"oam_lock\":%u,\"map_anims\":%u,\"scx\":%u,\"miss_reason\":%u}\n",
           name,t/2,pc,bank_for(pc),frame_number,serial,phase,
           ram(2,S_wPokeAnimSceneIndex),ram(2,S_wPokeAnimIdleFlag),
           ram(2,S_wPokeAnimCommand),ram(2,S_wPokeAnimParameter),ram(2,S_wPokeAnimWaitCounter),
           byte(0xff44),byte(0xff41)&3,cache(),remain(),byte(S_hSampledCryTimer),idle_ticks/2,
           byte(S_hVBlank),byte(S_wFrameCounter),byte(S_wPokedexStatus),ram(2,S_wPokeAnimJumptableIndex),
           byte(S_hJoyDown),byte(S_hJoyLast),byte(S_hJoypadDown),
           byte(S_hOAMUpdate),byte(S_hMapAnims),byte(S_hSCX),ram(2,S_wNewDexEntryAnimMissReason));
}

static unsigned map_match(void)
{
    uint8_t picture[49*16];
    unsigned map = (byte(0xff40)&8) ? 0x1c00 : 0x1800;
    for (unsigned y=0;y<7;y++) for (unsigned x=0;x<7;x++) {
        unsigned i=y*7+x, cell=map+33+y*32+x;
        unsigned tile=gb.vram[cell], attr=gb.vram[0x2000+cell];
        unsigned address=((byte(0xff40)&16) ? tile*16 : 0x1000+(int8_t)tile*16) + ((attr&8)?0x2000:0);
        for (unsigned row=0;row<8;row++) for (unsigned plane=0;plane<2;plane++) {
            uint8_t value=gb.vram[address+((attr&64)?7-row:row)*2+plane];
            if (attr&32) {
                value=(value&0x55)<<1 | (value>>1&0x55);
                value=(value&0x33)<<2 | (value>>2&0x33);
                value=value<<4 | value>>4;
            }
            picture[i*16+row*2+plane]=value;
        }
    }
    unsigned mask=0;
    for (unsigned i=0;i<references;i++) if (!memcmp(picture,reference[i],sizeof(picture))) mask|=1u<<i;
    return mask;
}

static unsigned pixel_match(void)
{
    int x0=8-byte(0xff43), y0=8-byte(0xff42);
    if (x0<0 || y0<0 || x0+56>160 || y0+56>144) return 0;
    unsigned mask=0;
    for (unsigned frame=0;frame<references;frame++) {
        bool matches=true;
        for (unsigned y=0;matches && y<56;y++) for (unsigned x=0;x<56;x++) {
            unsigned tile=(y/8)*7+x/8, bit=7-x%8;
            unsigned a=reference[frame][tile*16+(y%8)*2];
            unsigned b=reference[frame][tile*16+(y%8)*2+1];
            unsigned color=((a>>bit)&1) | (((b>>bit)&1)<<1);
            if (pixels[(y0+y)*160+x0+x] != gb.background_palettes_rgb[4+color]) { matches=false; break; }
        }
        if (matches) mask|=1u<<frame;
    }
    return mask;
}

static unsigned ui_mismatches(void)
{
    unsigned mismatches=0;
    for (unsigned y=0;y<18;y++) for (unsigned x=0;x<20;x++) {
        if ((x>=1 && x<8 && y>=1 && y<8) || (x==18 && y==17)) continue;
        if (gb.vram[0x1800+y*32+x] != byte(S_wTilemap+y*20+x)) mismatches++;
    }
    return mismatches;
}

static unsigned description_cell(unsigned i)
{
    return i==90 ? 9*20+2 : (10+i/18)*20+2+i%18;
}

static bool description_map_matches(const uint8_t *expected)
{
    for (unsigned i=0;i<91;i++) {
        unsigned cell=description_cell(i), x=cell%20, y=cell/20;
        if (gb.vram[0x1800+y*32+x]!=expected[i]) return false;
    }
    return true;
}

static bool description_pixels_match(const uint8_t *expected)
{
    for (unsigned i=0;i<91;i++) {
        unsigned cell=description_cell(i), x=cell%20, y=cell/20;
        unsigned attr=gb.vram[0x3800+y*32+x], tile=expected[i];
        unsigned address=((byte(0xff40)&16)?tile*16:0x1000+(int8_t)tile*16)+((attr&8)?0x2000:0);
        for (unsigned py=0;py<8;py++) for (unsigned px=0;px<8;px++) {
            int sx=(int)(x*8+px)-byte(0xff43), sy=(int)(y*8+py)-byte(0xff42);
            if (sx<0 || sy<0 || sx>=160 || sy>=144) continue;
            unsigned row=(attr&64)?7-py:py, bit=(attr&32)?px:7-px;
            unsigned color=((gb.vram[address+2*row]>>bit)&1)|(((gb.vram[address+2*row+1]>>bit)&1)<<1);
            if (pixels[sy*160+sx]!=gb.background_palettes_rgb[(attr&7)*4+color]) return false;
        }
    }
    return true;
}

static void snapshot(const char *suffix)
{
    unsigned mismatches=ui_mismatches();
    printf("{\"event\":\"ui_snapshot\",\"name\":\"%s\",\"display\":%u,"
           "\"mismatches\":%u,\"page_backing\":%u,\"page_vram\":%u,\"status\":%u}\n",
           suffix,frame_number,mismatches,byte(S_wTilemap+9*20+2),gb.vram[0x1800+9*32+2],byte(S_wPokedexStatus));
    if (!screen_prefix) return;
    char path[2048];snprintf(path,sizeof(path),"%s-%s.ppm",screen_prefix,suffix);
    FILE *file=fopen(path,"wb");if (!file) exit(12);
    fprintf(file,"P6\n160 144\n255\n");
    for (unsigned i=0;i<160*144;i++) {
        uint8_t p[]={pixels[i]>>16,pixels[i]>>8,pixels[i]};fwrite(p,1,3,file);
    }
    fclose(file);
}

static void vblank(GB_gameboy_t *g, GB_vblank_type_t type)
{
    (void)g;
    /* The CPU clock includes the whole advance_cycles batch. At this callback
     * the display state machine still has display_cycles left in that batch.
     * Subtract that unconsumed time to timestamp the actual PPU boundary. */
    uint64_t callback_t=now(), ppu_t=callback_t;
    if (type==GB_VBLANK_TYPE_NORMAL_FRAME) {
        if (gb.display_cycles<0 || (uint64_t)gb.display_cycles>callback_t) exit(14);
        ppu_t-=gb.display_cycles;
    }
    frame_number++;
    if (phase==1 && displayed_serial && !map_match() && bad_pictures++<3) {
        printf("{\"event\":\"bad_picture\",\"display\":%u,\"cells\":[",frame_number);
        for (unsigned y=0;y<7;y++) for (unsigned x=0;x<7;x++) {
            unsigned i=y*7+x, cell=0x1821+y*32+x;
            printf("%s[%u,%u,%u]",i?",":"",gb.vram[cell],gb.vram[0x2000+cell],byte(S_wTilemap+21+y*20+x));
        }
        puts("]}");
    }
    if (phase==1 && waits==1 && !byte(S_wPokedexStatus) && first_publication && frame_number==first_publication+3)
        snapshot("page1");
    if (phase==1 && second_wait_display && frame_number==second_wait_display+3) snapshot("page2");
    if (returned && !(screens&1)) { snapshot("returned");screens|=1; }
    if (phase==1 && description_started && type==GB_VBLANK_TYPE_NORMAL_FRAME) {
        printf("{\"event\":\"description_display\",\"t\":%" PRIu64 ",\"ppu_t\":%" PRIu64 ",\"display\":%u,"
               "\"ready\":%u,\"old_map\":%u,\"new_map\":%u,\"old_pixels\":%u,\"new_pixels\":%u}\n",
               callback_t/2,ppu_t/2,frame_number,description_ready,
               description_map_matches(description_old),description_ready && description_map_matches(description_new),
               description_pixels_match(description_old),description_ready && description_pixels_match(description_new));
    }
    printf("{\"event\":\"display\",\"t\":%" PRIu64 ",\"ppu_t\":%" PRIu64 ","
           "\"ppu_pending_8mhz\":%d,\"number\":%u,\"type\":%u,"
           "\"phase\":%u,\"serial\":%u,\"map_mask\":%u,\"pixel_mask\":%u,"
           "\"cache\":%u,\"remaining\":%u,\"audio\":%u,\"lcdc\":%u,\"scx\":%u,\"scy\":%u,"
           "\"ui_mismatches\":%u,\"idle_t\":%" PRIu64 "}\n",
           callback_t/2,ppu_t/2,gb.display_cycles,frame_number,type,phase,displayed_serial,map_match(),pixel_match(),
           cache(),remain(),byte(S_hSampledCryTimer),byte(0xff40),byte(0xff43),byte(0xff42),
           phase==1 && second_wait_display ? ui_mismatches() : 0,idle_ticks/2);
}

static bool write_memory(GB_gameboy_t *g, uint16_t address, uint8_t value)
{
    if (timer_phase_armed && address==0xff05) {
        unsigned period=256-byte(0xff06);
        if ((byte(0xff07)&4) || value!=byte(0xff06) || timer_first_clocks>period) exit(13);
        timer_phase_armed=false;timer_phase_applied=true;
        unsigned replacement=256-timer_first_clocks;
        printf("{\"event\":\"synthetic_timer_phase\",\"t\":%" PRIu64 ",\"first_clocks\":%u,"
               "\"period\":%u,\"original\":%u,\"replacement\":%u,\"div\":%u}\n",
               now()/2,timer_first_clocks,period,value,replacement,gb.div_counter);
        GB_set_write_memory_callback(g,NULL);
        GB_write_memory(g,address,replacement);
        GB_set_write_memory_callback(g,write_memory);
        return false;
    }
    if (address==0xff55 && !compact) {
        printf("{\"event\":\"dma_start\",\"t\":%" PRIu64 ",\"phase\":%u,\"serial\":%u,"
               "\"source\":%u,\"dest\":%u,\"vbk\":%u,\"svbk\":%u,\"blocks\":%u,"
               "\"hblank\":%u,\"ly\":%u,\"mode\":%u}\n",
               now()/2,phase,serial,gb.hdma_current_src,0x8000+(gb.hdma_current_dest&0x1fff),
               byte(0xff4f)&1,byte(0xff70)&7,(value&127)+1,value>>7,byte(0xff44),byte(0xff41)&3);
    }
    return true;
}

static void observe(GB_gameboy_t *g, uint16_t pc, uint8_t opcode)
{
    (void)g;
    executed=true;
    uint64_t t=now();
    unsigned bank=bank_for(pc);
    /* HOST-ONLY optional instruction trace. Physical reads do not advance the core. */
    if (instruction_to && t/2>=instruction_from && t/2<instruction_to) {
        printf("{\"event\":\"instruction\",\"t\":%" PRIu64 ",\"pc\":%u,\"bank\":%u,"
               "\"opcode\":%u,\"af\":%u,\"bc\":%u,\"de\":%u,\"hl\":%u,\"sp\":%u,"
               "\"ime\":%u,\"ie\":%u,\"if\":%u,\"ly\":%u,\"stat\":%u,"
               "\"div\":%u,\"tima\":%u,\"tma\":%u,\"tac\":%u,\"display\":%u,"
               "\"cache\":%u,\"remaining\":%u,\"owner\":%u,\"flags\":%u}\n",
               t/2,pc,bank,opcode,gb.af,gb.bc,gb.de,gb.hl,gb.sp,gb.ime,
               gb.interrupt_enable,byte(0xff0f),byte(0xff44),byte(0xff41),
               gb.div_counter,byte(0xff05),byte(0xff06),byte(0xff07),frame_number,
               cache(),remain(),byte(S_hVBlank),ram(2,S_wPokeAnimSceneIndex));
    }
    if (!returned && pc==return_pc && gb.sp==return_sp && pc<0x4000) {
        returned=true;phase=2;finished=true;finish_ticks=t;
        event("registration_return",t,pc);
    }
    if (compact && !depth && !interesting[pc]) return;
    if (depth) active[depth-1].self += t-last_clock;
    else other[phase] += t-last_clock;
    last_clock=t;
    for (int i=(int)depth-1;i>=0;i--) {
        if (active[i].ret!=pc || gb.sp!=active[i].sp+2 || (pc>=0x4000 && bank!=active[i].bank)) continue;
        unsigned f=active[i].function,p=active[i].phase;
        uint64_t elapsed=t-active[i].start;
        self[p][f]+=active[i].self; inclusive[p][f]+=elapsed; counts[p][f]++;
        if (functions[f].log) {
            printf("{\"event\":\"span\",\"name\":\"%s\",\"id\":%u,\"start\":%" PRIu64
                   ",\"end\":%" PRIu64 ",\"self\":%" PRIu64 ",\"phase\":%u,\"serial\":%u,"
                   "\"cache_start\":%u,\"cache_end\":%u,\"remaining_start\":%u,\"remaining_end\":%u,\"b\":%u}\n",
                   functions[f].name,active[i].id,active[i].start/2,t/2,active[i].self/2,p,active[i].serial,
                   active[i].cache,cache(),active[i].remaining,remain(),active[i].b);
        }
        if (functions[f].kind==F_DMA && active[i].requested && active[i].source==0xd000 &&
                (active[i].dest&0x1fff)==0x1800 && active[i].vbk==0) {
            displayed_serial=active[i].serial;
            printf("{\"event\":\"map_commit\",\"t\":%" PRIu64 ",\"serial\":%u,\"mask\":%u,\"ly\":%u}\n",
                   t/2,displayed_serial,map_match(),byte(0xff44));
        }
        memmove(active+i,active+i+1,(depth-i-1)*sizeof(*active));depth--;
    }
    for (unsigned i=0;i<sizeof(events)/sizeof(*events);i++) {
        if (pc!=events[i].pc || bank!=events[i].bank) continue;
        if (events[i].kind==E_WAIT) {
            phase=1;
            if (++waits==2) second_wait_display=frame_number;
        }
        if (events[i].kind==E_FRAME || events[i].kind==E_END) serial++;
        if (events[i].kind==E_PUBLISH) {
            displayed_serial=serial;
            if (!first_publication) first_publication=frame_number;
        }
        if (events[i].kind==E_EXIT) phase=2;
        if (events[i].kind==E_AUDIO && timer_first_clocks && !timer_phase_applied)
            timer_phase_armed=true;
        if (events[i].kind==E_DESCRIPTION && byte(S_wPokedexStatus)==1) {
            description_started=true;
            for (unsigned j=0;j<91;j++) {
                unsigned cell=description_cell(j);
                description_old[j]=gb.vram[0x1800+(cell/20)*32+cell%20];
            }
        }
        if (events[i].kind==E_DESCRIPTION_READY) {
            description_ready=true;
            for (unsigned j=0;j<91;j++) description_new[j]=byte(S_wTilemap+description_cell(j));
        }
        if (events[i].kind==E_FINISH) { finished=true;finish_ticks=t; }
        event(events[i].name,t,pc);
    }
    for (unsigned f=0;f<sizeof(functions)/sizeof(*functions);f++) {
        if (functions[f].pc!=pc || functions[f].bank!=bank) continue;
        if (compact && strcmp(functions[f].name,"SampledCry_FillRollingCache")) continue;
        if (depth>=128) { fputs("Profile stack overflow\n",stderr);exit(10); }
        unsigned ret=word(gb.sp);
        active[depth].function=f;active[depth].sp=gb.sp;active[depth].ret=ret;
        active[depth].bank=gb.mbc_rom_bank;active[depth].id=++calls;active[depth].serial=serial;
        active[depth].phase=phase;active[depth].start=t;active[depth].self=0;
        active[depth].cache=cache();active[depth].remaining=remain();active[depth].b=gb.bc>>8;
        active[depth].source=gb.hdma_current_src;active[depth].dest=gb.hdma_current_dest;
        active[depth].vbk=byte(0xff4f)&1;active[depth].requested=byte(S_hDMATransfer);
        depth++;
    }
}

int main(int argc,char **argv)
{
    if (argc<4 || argc>6) return 2;
    screen_prefix=getenv("REGISTRATION_FRAMES");
    compact=getenv("REGISTRATION_COMPACT")!=NULL;
    const char *first_clocks=getenv("REGISTRATION_TIMER_FIRST_CLOCKS");
    if (first_clocks) {
        char *end;
        unsigned long value=strtoul(first_clocks,&end,10);
        if (end==first_clocks || *end || value<1 || value>256) return 2;
        timer_first_clocks=value;
    }
    const char *from=getenv("REGISTRATION_INSTRUCTION_FROM_T");
    const char *to=getenv("REGISTRATION_INSTRUCTION_TO_T");
    if (from || to) {
        if (!from || !to) return 2;
        char *end;
        instruction_from=strtoull(from,&end,10);if (*end) return 2;
        instruction_to=strtoull(to,&end,10);if (*end || instruction_to<=instruction_from) return 2;
    }
    input_mode=argc==5?atoi(argv[4]):0;
    planned=argc==6;
    if (planned) {
        FILE *file=fopen(argv[5],"r");if (!file) return 2;
        while (input_count<2048 && fscanf(file,"%u %u %u %u",&inputs[input_count].anchor,
            &inputs[input_count].start,&inputs[input_count].duration,&inputs[input_count].keys)==4) {
            if (inputs[input_count].anchor>2 || !inputs[input_count].duration) return 2;
            input_count++;
        }
        if (!feof(file)) return 2;
        fclose(file);
    }
    for (unsigned i=0;i<sizeof(events)/sizeof(*events);i++) interesting[events[i].pc]=true;
    for (unsigned i=0;i<sizeof(functions)/sizeof(*functions);i++)
        if (!strcmp(functions[i].name,"SampledCry_FillRollingCache")) interesting[functions[i].pc]=true;
    FILE *refs=fopen(argv[3],"rb");if (!refs) return 2;
    references=fgetc(refs);
    if (!references || references>32 || fread(reference,49*16,references,refs)!=references) return 3;
    fclose(refs);
    GB_init(&gb,GB_MODEL_CGB_E);GB_set_turbo_mode(&gb,true,true);
    GB_set_pixels_output(&gb,pixels);GB_set_rgb_encode_callback(&gb,rgb);
    if (GB_load_rom(&gb,argv[1]) || GB_load_state(&gb,argv[2])) return 4;
    if (gb.pc!=P_ENTRY || gb.mbc_rom_bank!=B_ENTRY || gb.cgb_double_speed) return 5;
    return_pc=word(gb.sp);return_sp=gb.sp+2;
    GB_set_key_mask(&gb,0);
    GB_set_vblank_callback(&gb,vblank);GB_set_execution_callback(&gb,observe);
    GB_set_write_memory_callback(&gb,write_memory);
    while (ticks<UINT64_C(70224)*2*1200) {
        unsigned delta=first_publication?frame_number-first_publication:0;
        unsigned keys=input_mode && first_publication && delta>=5 && delta<7 ? GB_KEY_A_MASK :
            input_mode==2 && first_publication && delta>=15 && delta<17 ? GB_KEY_B_MASK : 0;
        bool pending=false;
        if (planned) {
            keys=0;
            for (unsigned i=0;i<input_count;i++) {
                unsigned origin=inputs[i].anchor==1 ? first_publication :
                    inputs[i].anchor==2 ? second_wait_display : 0;
                if (inputs[i].anchor && !origin) { pending=true;continue; }
                unsigned start=origin+inputs[i].start, end=start+inputs[i].duration;
                if (frame_number<end) pending=true;
                if (frame_number>=start && frame_number<end) keys|=inputs[i].keys;
            }
            if (returned) keys=0;
        }
        if (keys!=last_keys) {
            GB_set_key_mask(&gb,keys);last_keys=keys;
            last_input_display=frame_number;
            printf("{\"event\":\"input\",\"t\":%" PRIu64 ",\"display\":%u,\"keys\":%u}\n",ticks/2,frame_number,keys);
        }
        unsigned before=gb.cycles_since_run;step_origin=before;
        unsigned old_pc=gb.pc,old_sp=gb.sp;
        bool halted=gb.halted;executed=false;
        GB_cpu_run(&gb);ticks+=(unsigned)(gb.cycles_since_run-before);
        if (halted && !executed && old_pc==gb.pc && old_sp==gb.sp)
            idle_ticks+=(unsigned)(gb.cycles_since_run-before);
        if (finished && (input_mode!=2 || returned) && (phase!=2 || returned) && ticks-finish_ticks>70224*2*12 &&
            (!planned || returned || (!pending && frame_number>=last_input_display+6)) && !byte(S_hSampledCryTimer)) break;
    }
    if (screen_prefix && phase==1) snapshot("settled");
    event("final",ticks,gb.pc);
    for (unsigned p=0;p<3;p++) for (unsigned f=0;f<sizeof(functions)/sizeof(*functions);f++) {
        if (!counts[p][f]) continue;
        printf("{\"event\":\"profile\",\"name\":\"%s\",\"phase\":%u,\"count\":%" PRIu64
               ",\"self\":%" PRIu64 ",\"inclusive\":%" PRIu64 "}\n",
               functions[f].name,p,counts[p][f],self[p][f]/2,inclusive[p][f]/2);
    }
    printf("{\"event\":\"profile_end\",\"open_spans\":%u,\"total_t\":%" PRIu64 "}\n",depth,ticks/2);
    GB_free(&gb);
    if (timer_first_clocks && !timer_phase_applied) return 13;
    return ticks<UINT64_C(70224)*2*1200 && finished && (input_mode!=2 || returned)?0:6;
}
