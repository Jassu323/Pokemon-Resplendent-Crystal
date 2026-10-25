/* Host-only menu/overworld observer. Never included in a cartridge build. */
#include SHARED_MENU_INPUT_SYMBOLS
static FILE *shared_trace;
static bool shared_pending;
static bool shared_executing;
static unsigned shared_return_pc, shared_return_bank, shared_entry_bc;
static unsigned shared_entry_de, shared_entry_hl, shared_entry_sp;
static uint64_t shared_entry_t;

static uint64_t shared_now(void)
{
    return (ticks + (shared_executing ? (unsigned)(gb.cycles_since_run-step_origin) : 0))/2;
}

static unsigned shared_value(unsigned bank, unsigned address)
{
    if (address >= 0xd000 && address < 0xe000)
        return gb.ram[bank * 4096 + (address & 4095)];
    return byte(address);
}

static void shared_snapshot(FILE *out, const char *event)
{
    fprintf(out, "{\"event\":\"%s\",\"t\":%" PRIu64 ",\"pc\":%u,\"bank\":%u,"
                 "\"sp\":%u,\"ime\":%u,\"af\":%u,\"bc\":%u,\"de\":%u,\"hl\":%u",
            event, shared_now(), gb.pc, gb.mbc_rom_bank, gb.sp, gb.ime,
            gb.registers[GB_REGISTER_AF], gb.registers[GB_REGISTER_BC],
            gb.registers[GB_REGISTER_DE], gb.registers[GB_REGISTER_HL]);
    fprintf(out, ",\"lcdc\":%u,\"ly\":%u,\"bgp\":%u,\"bg_rgb0\":%u,\"double_speed\":%u",
            byte(0xff40), byte(0xff44), byte(0xff47), gb.background_palettes_rgb[0], gb.cgb_double_speed);
    for (unsigned i=0; i<sizeof(shared_fields)/sizeof(*shared_fields); i++) {
        unsigned value=0;
        for (unsigned n=0; n<shared_fields[i].size; n++)
            value |= shared_value(shared_fields[i].bank, shared_fields[i].address+n) << (8*n);
        fprintf(out, ",\"%s\":%u", shared_fields[i].name, value);
    }
    fputs("}\n", out);
}

static void shared_menu_observe(unsigned bank, unsigned pc)
{
    if (!shared_trace) return;
    shared_executing=true;
    if (!bank && pc == M_JoyTextDelay) {
        if (shared_pending) { fputs("{\"event\":\"nested_poll\"}\n",shared_trace); exit(21); }
        shared_pending=true;
        shared_return_pc=word(gb.sp);
        shared_return_bank=gb.mbc_rom_bank;
        shared_entry_bc=gb.registers[GB_REGISTER_BC]; shared_entry_de=gb.registers[GB_REGISTER_DE];
        shared_entry_hl=gb.registers[GB_REGISTER_HL];
        shared_entry_sp=gb.sp; shared_entry_t=shared_now();
        shared_snapshot(shared_trace,"poll_entry");
    } else if (shared_pending && pc == shared_return_pc &&
               (pc < 0x4000 || bank == shared_return_bank)) {
        unsigned pressed=byte(M_hJoyPressed), down=byte(M_hJoyDown), last=byte(M_hJoyLast);
        bool policy=byte(M_hInMenu) && (pressed & 0xf0);
        bool correct=!policy || last == ((down & 15) | (pressed & 0xf0));
        bool registers=gb.registers[GB_REGISTER_BC]==shared_entry_bc &&
            gb.registers[GB_REGISTER_DE]==shared_entry_de && gb.registers[GB_REGISTER_HL]==shared_entry_hl &&
            gb.sp==shared_entry_sp+2;
        shared_snapshot(shared_trace,"poll_return");
        fprintf(shared_trace,"{\"event\":\"contract\",\"t\":%" PRIu64 ",\"elapsed_t\":%" PRIu64
                ",\"fresh_direction\":%u,\"correct\":%s,\"registers\":%s}\n",
                shared_now(),shared_now()-shared_entry_t,policy,correct?"true":"false",registers?"true":"false");
        shared_pending=false;
    }
    shared_executing=false;
}

static bool shared_menu_command(char *line)
{
    if (!strcmp(line,"m\n")) {
        shared_snapshot(stdout,"ok"); return true;
    }
    if (!strncmp(line,"mtrace ",7)) {
        line[strcspn(line,"\r\n")]=0;
        if (shared_trace) fclose(shared_trace);
        shared_trace=fopen(line+7,"w"); shared_pending=false;
        printf("{\"event\":\"ok\",\"error\":%u}\n",shared_trace==NULL); return true;
    }
    if (!strcmp(line,"mstop\n")) {
        if (shared_trace) fclose(shared_trace);
        shared_trace=NULL; shared_pending=false;
        puts("{\"event\":\"ok\"}"); return true;
    }
    unsigned bank,pc,keys; uint64_t budget;
    if (sscanf(line,"mr %u %u %" SCNu64 " %u",&bank,&pc,&budget,&keys)==4) {
        GB_set_key_mask(&gb,keys);
        uint64_t start=ticks;
        do {
            unsigned before=gb.cycles_since_run;
            step_origin=before; GB_cpu_run(&gb);
            ticks+=(unsigned)(gb.cycles_since_run-before);
        } while (!at(bank,pc) && ticks-start<budget*2);
        shared_snapshot(stdout,"ok"); return true;
    }
    return false;
}

static void shared_menu_close(void)
{
    if (shared_trace) fclose(shared_trace);
}
