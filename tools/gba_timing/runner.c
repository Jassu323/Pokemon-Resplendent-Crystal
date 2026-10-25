/* Host-only mGBA replay/instrumentation. The cartridge remains unmodified. */
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/timing.h>
#include <mgba/debugger/debugger.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/arm/arm.h>
#include <mgba-util/vfs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

static struct mCore *core;
static struct mDebugger debugger;
static struct mDebuggerModule observer;
static mColor pixels[240 * 160];
static FILE *events, *video, *audio;
static uint32_t sprites, tasks, main_addr, script_addr, active_addr;
static uint32_t attacker_addr, target_addr;
static uint32_t stop_addr;
static int stopped;
static struct { uint32_t address; char name[80]; } points[100];
static unsigned npoints;

static uint64_t now(void) { return mTimingGlobalTime(&((struct GBA *)core->board)->timing); }
static void bytes(FILE *out, uint32_t address, unsigned count) {
    fputc('"', out);
    for (unsigned i = 0; i < count; ++i) fprintf(out, "%02x", core->rawRead8(core, address + i, -1));
    fputc('"', out);
}
static void entered(struct mDebuggerModule *module, enum mDebuggerEntryReason reason, struct mDebuggerEntryInfo *info) {
    (void)module;
    if (reason == DEBUGGER_ENTER_BREAKPOINT && info) {
        if (info->address == stop_addr) stopped = 1;
        if (events) for (unsigned i = 0; i < npoints; ++i) if (info->address == points[i].address) {
            struct ARMCore *cpu = core->cpu;
            fprintf(events, "{\"event\":\"point\",\"name\":\"%s\",\"t\":%" PRIu64 ",\"frame\":%u,\"r\":[%u,%u,%u,%u],\"lr\":%u,\"script\":%u,\"active\":%u,\"attacker\":%u,\"target\":%u}\n",
                    points[i].name, now(), core->frameCounter(core), cpu->gprs[0], cpu->gprs[1], cpu->gprs[2], cpu->gprs[3], cpu->gprs[14],
                    core->rawRead32(core, script_addr, -1), core->rawRead8(core, active_addr, -1),
                    core->rawRead8(core, attacker_addr, -1), core->rawRead8(core, target_addr, -1));
        }
    }
    observer.isPaused = false;
    debugger.state = DEBUGGER_RUNNING;
}
static void video_frame(struct mAVStream *stream, const mColor *buffer, size_t stride) {
    (void)stream;
    if (video) for (unsigned y = 0; y < 160; ++y) for (unsigned x = 0; x < 240; ++x) {
        mColor c = buffer[y * stride + x];
        unsigned char rgb[] = {c & 255, c >> 8 & 255, c >> 16 & 255};
        fwrite(rgb, 1, 3, video);
    }
    if (!events) return;
    uint32_t hash=2166136261u;
    for(unsigned y=0;y<160;y++) for(unsigned x=0;x<240;x++) hash=(hash^buffer[y*stride+x])*16777619u;
    fprintf(events, "{\"event\":\"frame\",\"t\":%" PRIu64 ",\"frame\":%u,\"pixels\":%u,\"script\":%u,\"active\":%u,\"sprites\":",
            now(), core->frameCounter(core),hash, core->rawRead32(core, script_addr, -1), core->rawRead8(core, active_addr, -1));
    bytes(events, sprites, 68 * 64);
    fputs(",\"tasks\":", events); bytes(events, tasks, 40 * 16);
    fputs(",\"shadow_oam\":", events); bytes(events, main_addr + 0x38, 1024);
    fputs(",\"hardware_oam\":", events); bytes(events, 0x07000000, 1024);
    fputs(",\"palettes\":", events); bytes(events, 0x05000000, 1024);
    fputs("}\n", events);
}
static void audio_frame(struct mAVStream *stream, int16_t left, int16_t right) {
    (void)stream;
    if (audio) { int16_t sample[] = {left, right}; fwrite(sample, sizeof(sample), 1, audio); }
}
static struct mAVStream av = {.postVideoFrame=video_frame, .postAudioFrame=audio_frame};
static void quiet_log(struct mLogger *logger, int category, enum mLogLevel level, const char *format, va_list args) {
    (void)logger; (void)category;
    if (level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN)) { vfprintf(stderr, format, args); fputc('\n',stderr); }
}
static struct mLogger logger = {.log=quiet_log};
static ssize_t breakpoint(uint32_t addr) {
    struct mBreakpoint bp = {.address=addr & ~1u, .segment=-1, .type=BREAKPOINT_HARDWARE};
    return debugger.platform->setBreakpoint(debugger.platform, &observer, &bp);
}
static void run_frame(void) { mDebuggerRunFrame(&debugger); }
static void status(void) {
    struct ARMCore *cpu = core->cpu;
    printf("{\"ok\":true,\"t\":%" PRIu64 ",\"frame\":%u,\"pc\":%u,\"r0\":%u,\"audio_rate\":%u}\n", now(), core->frameCounter(core), cpu->gprs[15], cpu->gprs[0], core->audioSampleRate(core));
    fflush(stdout);
}
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    mLogSetDefaultLogger(&logger);
    core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) return 3;
    mCoreInitConfig(core, "timing-replay");
    mCoreConfigSetDefaultIntValue(&core->config, "idleOptimization", -1);
    mCoreConfigSetDefaultIntValue(&core->config, "sampleRate", 44100);
    mCoreConfigSetDefaultIntValue(&core->config, "logLevel", 7);
    mCoreLoadConfig(core);
    core->setVideoBuffer(core, pixels, 240);
    core->setAVStream(core, &av);
    if (!mCoreLoadFile(core, argv[1])) return 4;
    mDebuggerInit(&debugger);
    observer.type = DEBUGGER_CUSTOM; observer.entered = entered;
    mDebuggerAttachModule(&debugger, &observer);
    mDebuggerAttach(&debugger, core);
    core->reset(core); debugger.state = DEBUGGER_RUNNING;
    status();
    char line[2048], command[40], path[1024]; unsigned a, b, c;
    while (fgets(line, sizeof(line), stdin)) {
        if (sscanf(line, "%39s", command) != 1) continue;
        if (!strcmp(command, "quit")) break;
        if (sscanf(line, "run %u %u", &a, &b) == 2) { core->setKeys(core, b); while (a--) run_frame(); }
        else if (sscanf(line, "until %x %u", &a, &b) == 2) {
            stop_addr = a & ~1u; stopped = 0; ssize_t id = breakpoint(a);
            uint64_t deadline = now() + (uint64_t)b * 280896;
            while (!stopped && now() < deadline) mDebuggerRun(&debugger);
            debugger.platform->clearBreakpoint(debugger.platform, id); stop_addr = 0;
            if (!stopped) fprintf(stderr, "Breakpoint timeout at %08x\n", a);
        }
        else if (sscanf(line, "write %x %x %u", &a, &b, &c) == 3) {
            if (c == 1) core->busWrite8(core, a, b);
            if (c == 2) core->busWrite16(core, a, b);
            if (c == 4) core->busWrite32(core, a, b);
        }
        else if (sscanf(line, "read %x %u", &a, &b) == 2) { fputs("{\"bytes\":", stdout); bytes(stdout, a, b); puts("}"); fflush(stdout); continue; }
        else if (sscanf(line, "reg %39s %x", command, &a) == 2) core->writeRegister(core, command, a);
        else if (!strncmp(line, "call ", 5)) {
            struct ARMCore *cpu = core->cpu;
            int32_t regs[16]; memcpy(regs, cpu->gprs, sizeof(regs));
            uint32_t cpsr = cpu->cpsr.packed, args[8] = {0};
            unsigned count = sscanf(line + 5, "%x %x %x %x %x %x %x %x %x", &a,
                &args[0], &args[1], &args[2], &args[3], &args[4], &args[5], &args[6], &args[7]) - 1;
            core->writeRegister(core, "cpsr", 0x3f);
            uint32_t sp = (regs[13] - 128) & ~7u;
            core->writeRegister(core, "sp", sp);
            for (unsigned i=0;i<4;i++) cpu->gprs[i]=args[i];
            for (unsigned i=4;i<count;i++) core->busWrite32(core, sp + 4*(i-4), args[i]);
            core->writeRegister(core, "lr", 0x03007d01);
            core->writeRegister(core, "pc", a & ~1u);
            stop_addr=0x03007d00; stopped=0; ssize_t id=breakpoint(stop_addr);
            uint64_t deadline=now()+280896*120;
            while(!stopped && now()<deadline) mDebuggerRun(&debugger);
            debugger.platform->clearBreakpoint(debugger.platform,id); stop_addr=0;
            uint32_t returned=cpu->gprs[0];
            core->writeRegister(core,"cpsr",cpsr);
            for(unsigned i=0;i<15;i++) cpu->gprs[i]=regs[i];
            core->writeRegister(core,"pc",regs[15]-(cpsr&32?2:4));
            printf("{\"ok\":%s,\"return\":%u}\n",stopped?"true":"false",returned); fflush(stdout); continue;
        }
        else if (sscanf(line, "save %1023s", path) == 1) {
            size_t n = core->stateSize(core); void *state = malloc(n); core->saveState(core, state);
            FILE *f = fopen(path, "wb"); fwrite(state, 1, n, f); fclose(f); free(state);
        }
        else if (sscanf(line, "load %1023s", path) == 1) {
            size_t n = core->stateSize(core); void *state = malloc(n); FILE *f = fopen(path, "rb");
            if (!f || fread(state, 1, n, f) != n || !core->loadState(core, state)) return 5;
            fclose(f); free(state);
        }
        else if (sscanf(line, "image %1023s", path) == 1) {
            FILE *f = fopen(path, "wb"); fprintf(f, "P6\n240 160\n255\n");
            for (unsigned i=0;i<240*160;i++) { unsigned char p[]={pixels[i]&255,pixels[i]>>8&255,pixels[i]>>16&255}; fwrite(p,1,3,f); } fclose(f);
        }
        else if (sscanf(line, "symbols %x %x %x %x %x", &sprites, &tasks, &main_addr, &script_addr, &active_addr) == 5) {}
        else if (sscanf(line, "owners %x %x", &attacker_addr, &target_addr) == 2) {}
        else if (sscanf(line, "point %x %79s", &a, points[npoints].name) == 2 && npoints < 99) {
            points[npoints++].address = a & ~1u; breakpoint(a);
        }
        else if (sscanf(line, "events %1023s", path) == 1) { if(events) fclose(events); events = strcmp(path,"-") ? fopen(path,"w") : NULL; }
        else if (sscanf(line, "video %1023s", path) == 1) { if(video) fclose(video); video = strcmp(path,"-") ? fopen(path,"wb") : NULL; }
        else if (sscanf(line, "audio %1023s", path) == 1) { if(audio) fclose(audio); audio = strcmp(path,"-") ? fopen(path,"wb") : NULL; }
        status();
    }
    if(events) fclose(events); if(video) fclose(video); if(audio) fclose(audio);
    core->deinit(core); mDebuggerDeinit(&debugger); free(core);
    return 0;
}
