"""Capture-seeded Selected-owner replay, not a general-purpose GB emulator.

This supplementary calibration runs the linked mainline and interrupt paths
with one memory state. PPU pixels, DMA bus conflicts and serial are not modeled.
Only the captured BG-only/no-input/normal-pitch path is supported. Full runs
continue through animation and cry completion, not merely the first miss.
"""

from copy import deepcopy
import heapq

from .assets import offset
from .costs import machine, run_to
from .cpu import CounterCPU, ModelError
from .model import Clock, FRAME, LINE
from .sound_registers import SoundRegisters


def seed_capture(cpu, stop, registers=False):
    for bank, address, value in stop["capture"]["memory"]:
        if 0xd000 <= address < 0xe000:
            cpu.wram[bank][address-0xd000] = value
        elif 0xc000 <= address < 0xd000 or address >= 0xff80:
            cpu.ram[address] = value
    for address, value in stop["capture"]["hardware"].items():
        if int(address) >= 0xff80:
            cpu.ram[int(address)] = value
    if registers:
        regs = stop["capture"]["registers"]
        for i, name in enumerate(("BC", "DE", "HL")):
            cpu.set_pair(i, regs[name])
        cpu.r[7], cpu.f = regs["AF"] >> 8, regs["AF"] & 0xf0
        # Keep the fixture's real call stack. Its absolute address affects no
        # branch here, whereas inventing uncaptured stack bytes would.


class ReplayCPU(CounterCPU):
    def read(self, address):
        if getattr(getattr(self,'replay',None),'sound_registers',None) and 0xff10 <= address < 0xff40:
            return self.replay.sound_registers.read(address)
        if address == 0xff00:
            return 0xc0 | (self.ram[address] & 0x30) | 0x0f
        if getattr(self, "replay", None) and address in (0xff04, 0xff05, 0xff0f, 0xff41, 0xff44, 0xff55):
            return self.replay.hardware_read(address)
        return super().read(address) | {0xff70: 0xf8, 0xff4f: 0xfe,
                                      0xff4d: 0x7e, 0xff07: 0xf8}.get(address, 0)

    def write(self, address, value):
        if getattr(getattr(self,'replay',None),'sound_registers',None) and 0xff10 <= address < 0xff40:
            self.replay.sound_registers.write(address,value)
        if getattr(self, "replay", None) and address in (0xff05, 0xff06, 0xff07, 0xff0f, 0xffff):
            self.replay.timer_write(address, value)
        super().write(address, value)
        if getattr(self, "replay", None):
            self.replay.audit_audio_write(address,value)
        if getattr(self, "replay", None) and address == 0xff55:
            self.replay.start_dma(value)


class ReplayClock(Clock):
    dma_due = 0
    timer_period = 12800
    enabled = 15

    def pending_enabled(self):
        return {name for bit, name in ((1, "vblank"), (2, "lcd"), (4, "timer"))
                if self.enabled & bit and name in self.pending}

    @property
    def mode(self):
        line, dot = (144+(self.t+1)//LINE) % 154, (self.t+1) % LINE
        return 1 if line >= 144 else 2 if dot < 80 else 3 if dot < self.p.hblank_dot else 0

    @property
    def ly(self):
        line, dot = (144+self.t//LINE) % 154, self.t % LINE
        if line == 153 and dot >= 3:
            return 0
        next_line = (line+1) % 154
        change = LINE-(3 if next_line >= 144 else 2)
        return next_line if dot >= change else line

    def _collect(self):
        while self.dma and self.dma[0] <= self.t:
            heapq.heappop(self.dma)
            self.dma_due = 1
        timer, self.next_timer = self.next_timer, float("inf")
        super()._collect()
        self.next_timer = timer
        while self.next_timer <= self.t:
            self.next_timer += self.timer_period
            self._request("timer")

    def _due(self, masked=False):
        while True:
            self._collect()
            if masked or not self.pending_enabled():
                return
            self.executor(None)


class OwnerReplay:
    def __init__(self, repo, asset, stops, profile, publication_t, div_low=None, timer_state=None):
        profile.validate()
        if asset.name not in ("weavile", "luxray", "dusknoir", "bastiodon", "garchomp", "rampardos",
                              "rayquaza", "kyogre", "metagross", "exeggcute", "groudon",
                              "milotic", "drapion", "rhyperior", "yanmega", "spheal", "sealeo",
                              "snorlax") or stops[0]["capture"]["registers"].get("PC") != repo.symbols[
                "Pokedex_VBlankAnimationFrontpicMap.deadline_reached"][1]:
            raise ModelError("Focused owner replay requires a supported first-publication capture")
        if not profile.lcd_stat_enabled:
            raise ModelError("Focused replay requires short LCD interrupts")
        self.repo, self.stops, self.p = repo, stops, profile
        cpu = machine(repo, asset, cpu_class=ReplayCPU)
        self.cpu = cpu
        cpu.allowed_io.update((0xff00, 0xff04, 0xff05, 0xff06, 0xff07, 0xff0f, 0xff40, 0xff41, 0xff42, 0xff43,
                               0xff46, 0xff4a, 0xff4b, *range(0xff51, 0xff56),
                               *range(0xff10, 0xff40)))
        cpu.io_read_values[0xff00] = 15
        cpu.ram[0xff40] = 0xe3  # Selected screen remains LCD-on throughout this capture.
        for name, value in (("hInMenu", 1), ("wJumptableIndex", 3), ("wPokedexAnimFlags", 0),
                            ("wPokedexAnimPlaybackState", 2), ("hSampledCryTimer", 1),
                            ("wGameTimerPaused", 1), ("wPokedexSelectedState", 1),
                            ("wSampledCryBlockPeriod", 200)):
            cpu.field(name, value)
        # Construct the existing owner's call/interrupt stack, without guessing
        # its contents from a backtrace. Start with no producer work to reach HALT.
        run_to(cpu, "Pokedex.main", "DelayFrame.halt")
        cpu.pc += 1
        returning = cpu.pc
        cpu.field("hVBlank", 7)
        seed_capture(cpu, stops[0])
        # The captured hROMBank is already inside the VBlank dispatcher. Its
        # saved return bank must instead come from the interrupted owner.
        cpu.field("hROMBank", cpu.bank)
        cpu.field("wDexArrowCursorBlinkCounter", 8 if profile.owner_variant & 4 else 0)
        cpu.field("wTextDelayFrames", 1 if profile.owner_variant & 2 else 0)
        cpu.field("wDexArrowCursorDelayCounter", profile.owner_variant & 1)
        begin, end = (offset(repo.symbols[n]) for n in ("OAMDMACode", "OAMDMACode.End"))
        cpu.block(repo.symbols["hTransferShadowOAM"][1], repo.rom[begin:end])
        cpu.ram[0xff44] = stops[0]["ly"]
        saved_return = cpu.sp-2
        run_to(cpu, "VBlank", "Pokedex_VBlankAnimationFrontpicMap.deadline_reached")
        if cpu.read(saved_return) | cpu.read(saved_return+1) << 8 != 0xffff:
            raise ModelError("Unexpected owner interrupt return")
        cpu.write(saved_return, returning & 255)
        cpu.write(saved_return+1, returning >> 8)
        seed_capture(cpu, stops[0], registers=True)
        self.initial_dictionary_tiles = self.seed_dictionary(asset)
        self.clock = ReplayClock(profile, {}, asset.sample_blocks)
        self.clock.t = publication_t
        self.clock.executor = self.interrupt
        self.clock.next_timer = profile.audio_phase_t
        while self.clock.next_timer <= publication_t:
            self.clock.next_timer += profile.audio_period_t
        flags = stops[0]["capture"]["hardware"][str(0xff0f)] & 15
        if flags & 8:
            raise ModelError("Serial interrupt is outside this focused replay")
        self.clock.pending = {name for bit, name in ((1, "vblank"), (2, "lcd"), (4, "timer")) if flags & bit}
        self.clock.dma_block = self.dma_block
        self.dma_remaining = 0
        self.dma_events = []
        self.masked, self.advanced = True, 0
        self.gdma_due = 0
        self.gdma_transfer = None
        self.allow_hdma_on_wake = False
        self.opcode = None
        if div_low is None:
            div_low = (4-profile.audio_phase_t+publication_t) % 64
        if not 0 <= div_low <= 255 or (timer_state is None and
                (div_low+profile.audio_phase_t-publication_t-4) % 64):
            raise ModelError("DIV low byte is inconsistent with the sample timer edge")
        self.div_origin = stops[0]["div"]*256+div_low-publication_t
        self.irq_cycles = {name: [] for name in ("vblank", "lcd", "timer")}
        self.observations = []
        self.in_interrupt = False
        self.timer_tma, self.timer_tac, self.timer_tima = 56, 6, stops[0]["tima"]
        if timer_state is not None:
            divider,tima,tma,tac = timer_state
            if not 0 <= divider <= 65535 or any(not 0 <= v <= 255 for v in (tima,tma,tac)):
                raise ModelError("Invalid captured timer registers")
            self.timer_tima,self.timer_tma,self.timer_tac = tima,tma,tac & 7
            self.div_origin = divider-publication_t
            step = (1024,16,64,256)[tac & 3]
            self.clock.timer_period = (256-tma)*step
            self.clock.next_timer = (publication_t+(256-tima)*step-divider%step+4
                                     if tac & 4 else float('inf'))
        cpu.replay = self
        self.points = [self.snapshot("Publication")]
        self.start_steps = cpu.steps
        self.asset = asset
        self.reset_audio_audit()
        self.lifecycle = []
        self.operations = []
        self.open_operations = []
        self.full = False
        self.operation_hooks = {repo.symbols[name]:name for name in (
            "Pokedex_ServiceAnimationProducer", "Pokedex_PrepareNextAnimationStage",
            "Pokedex_LoadAnimationDictionaryChunk", "Pokedex_BuildAnimationStage",
            "Pokedex_GatherReadyAnimationTiles", "HDMATransfer_Exact_NoDI_Arbitrary",
            "SampledCry_FillRollingCache", "Pokedex_GetNextAnimationScheduleAction",
            "Pokedex_ChooseAnimationWork", "Pokedex_TryFinishAnimationStage") if name in repo.symbols}

    def synth_flags(self):
        return [self.cpu.ram[self.repo.symbols[f'wChannel{i}Flags1'][1]] for i in range(5,9)]

    def synth_active(self):
        return any(value & 0x21 == 0x21 for value in self.synth_flags())

    def reset_audio_audit(self):
        self.track_synth = not self.asset.sample_blocks
        self.sound_registers = SoundRegisters(self.cpu.ram) if self.track_synth else None
        self.synth_initial_flags = self.synth_flags()
        self.synth_writes,self.synth_changes,self.sound_updates = [],[],[]

    def audit_audio_write(self,address,value):
        if not self.track_synth:
            return
        if 0xff10 <= address < 0xff40:
            self.synth_writes.append((self.clock.t,address,value))
        if address in [self.repo.symbols[f'wChannel{i}Flags1'][1] for i in range(5,9)]:
            self.synth_changes.append((self.clock.t,address,value))

    def seed_dictionary(self, asset):
        """Restore only the asset-verified decoded prefix, never the future tail."""
        cpu, repo = self.cpu, self.repo
        def field(name, size=1):
            return int.from_bytes(cpu.data(repo.symbols[name][1], size), "little")
        total = field("wPokedexAnimDictionaryTileCount")
        remaining = field("wPokedexAnimDictionaryTilesRemaining")
        if total != asset.total or remaining > total:
            raise ModelError("Captured dictionary counts disagree with linked asset")
        loaded = (total-remaining)*16
        produced, end = 0, 1
        for stream in asset.streams:
            if produced >= loaded:
                break
            produced += len(stream.output)
            end = stream.end
        bank, base = repo.symbols[asset.labels["front"]]
        if produced != loaded or loaded < asset.width**2*16:
            raise ModelError("Captured dictionary prefix is not a completed stream boundary")
        if (field("wPokedexAnimDictionaryBank") != bank or
                field("wPokedexAnimDictionaryAddress", 2) != base+end or
                field("wPokedexAnimDictionaryDestination", 2) != 0xd000+loaded):
            raise ModelError("Captured dictionary pointers disagree with decoded prefix")
        cpu.wram[6][:loaded] = asset.dictionary[:loaded]
        return loaded//16

    def start_dma(self, value):
        if self.clock.dma or self.dma_remaining:
            raise ModelError("Overlapping/cancelled DMA is outside this replay")
        if not value & 128:
            self.gdma_due += (value+1)*32+4
            cpu = self.cpu
            self.gdma_transfer = (cpu.ram[0xff51]*256+(cpu.ram[0xff52] & 0xf0),
                0x8000+(cpu.ram[0xff53] & 31)*256+(cpu.ram[0xff54] & 0xf0), (value+1)*16)
            return
        if self.opcode != 0xe0:
            raise ModelError("HDMA launch requires the linked LDH write")
        # LDH writes in its third M-cycle, not at instruction entry.
        self.clock.work(8, "hdma_register_write", masked=True)
        self.advanced = 8
        cpu, clock = self.cpu, self.clock
        self.dma_remaining = (value & 127)+1
        self.dma_source = cpu.ram[0xff51]*256+(cpu.ram[0xff52] & 0xf0)
        self.dma_dest = 0x8000+(cpu.ram[0xff53] & 31)*256+(cpu.ram[0xff54] & 0xf0)
        self.dma_events.append({"launch_t": clock.t, "tiles": self.dma_remaining,
                                "source": self.dma_source, "destination": self.dma_dest,
                                "blocks_t": []})
        tick = clock.t-clock.dot+self.p.hblank_dot
        immediate = clock.mode == 0
        if tick <= clock.t:
            tick += LINE
        for index in range(self.dma_remaining):
            if index == 0 and immediate:
                heapq.heappush(clock.dma, clock.t)
                continue
            while (144+tick//LINE) % 154 >= 144:
                tick += LINE
            # CGB-E display states 22 -> 33 separate STAT from HDMA by two T.
            heapq.heappush(clock.dma, tick+2)
            tick += LINE

    def dma_block(self):
        cpu = self.cpu
        self.dma_events[-1]["blocks_t"].append(self.clock.t)
        for i in range(16):
            cpu.write(self.dma_dest+i, cpu.read(self.dma_source+i))
        self.dma_source += 16
        self.dma_dest += 16
        self.dma_remaining -= 1
        if not self.dma_remaining:
            self.dma_events[-1]["done_t"] = self.clock.t+36
            self.clock.dma.clear()
            self.clock.dma_due = 0

    def hardware_read(self, address):
        if self.opcode not in (0xf0, 0xfa, 0xf2):
            raise ModelError("Unsupported clock-sensitive data-read instruction")
        delta = {0xf0: 8, 0xfa: 12, 0xf2: 4}[self.opcode]
        if self.advanced:
            raise ModelError("Multiple clock-sensitive reads in one instruction")
        self.clock.work(delta, "data_read", masked=True)
        self.advanced = delta
        if address == 0xff44:
            return self.clock.ly
        if address == 0xff41:
            return 0x88 | self.clock.mode | (4 if self.clock.ly == 0 else 0)
        if address == 0xff55:
            return self.dma_remaining-1 if self.dma_remaining else 255
        if address == 0xff0f:
            return 0xe0 | (self.cpu.ram[0xff0f] & 0x10) | sum(bit for bit, name in ((1,"vblank"),(2,"lcd"),(4,"timer"))
                              if name in self.clock.pending)
        if address == 0xff05:
            return self.read_tima()
        return ((self.clock.t+self.div_origin)//256) & 255

    def read_tima(self):
        if not self.timer_tac & 4:
            return self.timer_tima
        step = (1024, 16, 64, 256)[self.timer_tac & 3]
        until = self.clock.next_timer-self.clock.t
        return 0 if until <= 4 else (256-((until-4+step-1)//step)) & 255

    def timer_write(self, address, value):
        if self.opcode not in (0xe0, 0xea):
            raise ModelError("Unsupported timer/interrupt register write")
        delta = 8 if self.opcode == 0xe0 else 12
        if self.advanced:
            raise ModelError("Multiple clock-sensitive operations in one instruction")
        self.clock.work(delta, "timer_register_write", masked=True)
        self.advanced = delta
        if address == 0xff0f:
            if value & 8:
                raise ModelError("Serial IF is outside this replay")
            self.clock.pending = {name for bit, name in ((1,"vblank"),(2,"lcd"),(4,"timer")) if value & bit}
        elif address == 0xffff:
            self.clock.enabled = value & 15
        elif address == 0xff06:
            self.timer_tma = value
        elif address == 0xff05:
            if self.timer_tac & 4:
                raise ModelError("Live TIMA writes require separate overflow-edge validation")
            self.timer_tima = value
        else:
            if self.timer_tac & 4:
                self.timer_tima = self.read_tima()
            self.timer_tac = value & 7
            if value & 4:
                step = (1024, 16, 64, 256)[value & 3]
                div = (self.clock.t+self.div_origin) & 65535
                self.clock.next_timer = self.clock.t+(256-self.timer_tima)*step-(div % step)+4
                self.clock.timer_period = (256-self.timer_tma)*step
            else:
                self.clock.next_timer = float("inf")

    def step(self, kind="mainline"):
        cpu, clock = self.cpu, self.clock
        clock._collect()
        if self.gdma_due:
            length, self.gdma_due = self.gdma_due, 0
            source, destination, size = self.gdma_transfer
            for i in range(size):
                cpu.write(destination+i, cpu.read(source+i))
            self.gdma_transfer = None
            clock.work(length, "gdma", masked=True)
        while clock.dma_due:
            clock.dma_due -= 1
            clock.dma_block()
            clock.work(36, "hdma", masked=True)
        self.opcode, self.advanced = cpu.read(cpu.pc), 0
        if self.opcode == 0x76:
            if self.masked or self.dma_remaining:
                raise ModelError("Masked HALT or HALT during HDMA is outside this replay")
            cpu.pc += 1
            halt_mode = clock.mode
            clock.work(4, "halt", masked=True)
            clock._collect()
            # A request arriving during HALT causes a re-fetch after the ISR.
            # A request waking an already halted CPU instead costs four T.
            if clock.pending_enabled():
                cpu.pc -= 1
                clock.record("halt_request_during_instruction", 0)
                return
            self.allow_hdma_on_wake = bool(halt_mode)
            wake = clock._next(masked=True)
            clock.t += ((wake-clock.t+3)//4)*4
            clock._collect()
            clock.work(4, "halt_wake", masked=True)
            return
        before = cpu.cycles
        cpu.step()
        clock.work(cpu.cycles-before-self.advanced, kind, masked=True)
        clock._collect()
        if self.opcode == 0xf3:
            self.masked, self.ei_delay = True, 0
        elif self.opcode == 0xfb:
            self.ei_delay = 2
        if getattr(self, 'ei_delay', 0):
            self.ei_delay -= 1
            if not self.ei_delay:
                self.masked = False

    def interrupt(self, ignored):
        cpu, clock = self.cpu, self.clock
        self.in_interrupt = True
        returning, stack = cpu.pc, cpu.sp
        cycles = cpu.cycles
        # SameBoy's IRQ wake path can re-arm a block during the same HBlank.
        # The latch comes from the last successful HALT, not a species rule.
        if self.dma_remaining and clock.mode == 0 and self.allow_hdma_on_wake:
            clock.dma_due = max(clock.dma_due, 1)
        cpu.push(returning)
        # IF priority is sampled during entry, not before its first 16 T.
        clock.work(16, "irq_pre_ack", masked=True)
        name = next(n for n in ("vblank", "lcd", "timer") if n in clock.pending_enabled())
        clock.work(2, "irq_ack", masked=True)
        clock.pending.remove(name)
        clock.irq_counts[name]["delivered"] += 1
        cpu.pc = {"vblank": 0x40, "lcd": 0x48, "timer": 0x50}[name]
        clock.work(2, "irq_entry_tail", masked=True)
        while True:
            op = cpu.read(cpu.pc)
            self.observe()
            self.step(name)
            if op == 0xd9:
                break
            if cpu.cycles-cycles > FRAME:
                raise ModelError(f"Unexpected {name} interrupt path")
        if cpu.pc != returning or cpu.sp != stack:
            raise ModelError("Interrupt failed to restore the mainline stack")
        self.irq_cycles[name].append(cpu.cycles-cycles+20)
        if name == "vblank":
            clock.vblank_count += 1
        self.in_interrupt = False

    def snapshot(self, label):
        cpu, clock = self.cpu, self.clock
        def field(name, size=1):
            bank, address = cpu.symbols[name]
            data = cpu.wram[bank][address-0xd000:address-0xd000+size] if 0xd000 <= address < 0xe000 else cpu.ram[address:address+size]
            return int.from_bytes(data, "little")
        return {"label": label, "t": clock.t, "ly": clock.ly, "dot": clock.dot,
                "pc": cpu.pc, "bank": cpu.bank if cpu.pc >= 0x4000 else 0,
                "af": cpu.r[7]*256+cpu.f, "bc": cpu.pair(0), "de": cpu.pair(1),
                "hl": cpu.pair(2), "sp": cpu.sp,
                "ime": int(not (self.masked or self.in_interrupt)),
                "if_raw": 0xe0 | (cpu.ram[0xff0f] & 0x10) | sum(
                    bit for bit, name in ((1,"vblank"),(2,"lcd"),(4,"timer")) if name in clock.pending),
                "ie": clock.enabled,
                "audio": list(cpu.data(0xffee, 6)),
                "audio_cache": list(cpu.wram[4][0xff4:0xffc]),
                "timers": [((clock.t+self.div_origin)//256) & 255, self.read_tima(), self.timer_tma,
                           self.timer_tac | 0xf8],
                "mode": clock.mode, "counter": field("hVBlankCounter"),
                "pending": sorted(clock.pending), "cache": field("wSampledCryCacheCount"),
                "remaining": field("hSampledCryBlocks", 2),
                "compressed": field("wSampledCryCompressedBlocks", 2),
                "read_address": field("hSampledCryAddress", 2),
                "write_address": field("wSampledCryCacheWriteAddress", 2),
                "source_address": field("wSampledCryCompressedAddress", 2),
                "dictionary_remaining": field("wPokedexAnimDictionaryTilesRemaining"),
                "stage_tiles": field("wPokedexAnimStageTileCount"),
                "irq_count": {k: len(v) for k, v in self.irq_cycles.items()},
                "irq_total_t": {k: sum(v) for k, v in self.irq_cycles.items()},
                "anim": list(cpu.data(cpu.symbols["wPokedexAnimOwner"][1], 27)),
                "trace": list(cpu.data(cpu.symbols["wPokedexAnimDebug"][1], 139))}

    def observe(self):
        cpu = self.cpu
        labels = ("Pokedex_RecordAnimationTrace", "Pokedex_VBlankAnimationFrontpicMap.deadline_reached",
                  "HDMATransfer_Exact_NoDI_Arbitrary", "HDMATransfer_Exact_NoDI_Arbitrary.wait",
                  "DelayFrame.halt")
        key = (cpu.bank if cpu.pc >= 0x4000 else 0, cpu.pc)
        if self.track_synth and key == self.repo.symbols['_UpdateSound']:
            self.sound_updates.append(dict(t=self.clock.t,flags=self.synth_flags()))
        if self.full:
            while self.open_operations:
                span = self.open_operations[-1]
                if cpu.pc != span['return_pc'] or cpu.sp != span['return_sp']:
                    break
                self.open_operations.pop()
                irq_t = sum(sum(v) for v in self.irq_cycles.values())-span.pop('irq_t')
                irq_count = sum(len(v) for v in self.irq_cycles.values())-span.pop('irq_count')
                span.update(end_t=self.clock.t, elapsed_t=self.clock.t-span['start_t'],
                            interrupt_t=irq_t,
                            instruction_t=cpu.cycles-span.pop('cpu_t')-irq_t+20*irq_count)
                self.operations.append(span)
            if key in self.operation_hooks:
                self.open_operations.append({'kind':self.operation_hooks[key],
                    'start_t':self.clock.t,'cpu_t':cpu.cycles,
                    'irq_t':sum(sum(v) for v in self.irq_cycles.values()),
                    'irq_count':sum(len(v) for v in self.irq_cycles.values()),
                    'return_pc':cpu.read(cpu.sp) | cpu.read(cpu.sp+1)<<8,'return_sp':cpu.sp+2})
            hooks = ("Pokedex_CountAnimationUnderflow", "Pokedex_QueueReadyAnimationStage",
                     "Pokedex_VBlankAnimationFrontpicMap.deadline_reached",
                     "Pokedex_VBlankAnimationFrontpicMap.display_recorded",
                     "Pokedex_LoadAnimationDictionaryChunk", "Pokedex_GatherReadyAnimationTiles",
                     "Pokedex_FinalizePublishedAnimationStage.finished",
                     "StopSampledCryAsync_NoInterruptControl")
            for name in hooks:
                if key == self.repo.symbols[name]:
                    self.lifecycle.append(dict(self.snapshot(name), kind=name))
        for name in labels:
            if key != self.repo.symbols[name]:
                continue
            if name.endswith(".wait") and self.observations and self.observations[-1]["kind"] == name:
                return
            if name == "DelayFrame.halt" and self.observations and self.observations[-1]["kind"] == name:
                if self.observations[-1]["counter"] == cpu.ram[self.repo.symbols["hVBlankCounter"][1]]:
                    return
            point = self.snapshot(name)
            point["kind"] = name
            self.observations.append(point)
            return

    def run(self, full=False, max_frames=1024):
        self.full = full
        names = ("Pokedex_PrepareNextAnimationStage", "Pokedex_ServiceAnimationProducer",
                 "DelayFrame.halt", "Pokedex_CountAnimationUnderflow")
        targets = [self.repo.symbols[n] for n in names]
        while True:
            cpu, clock = self.cpu, self.clock
            index = len(self.points)-1
            bank, address = targets[index] if index < len(targets) else (-1, -1)
            # SameBoy can stop with IF pending. Observe PC before delivering it.
            if cpu.pc == address and (not bank or cpu.bank == bank):
                self.points.append(self.snapshot(self.stops[index+1]["label"]))
                if len(self.points) == 5 and not full:
                    break
            wait_points = {self.repo.symbols[n] for n in
                           ("DelayFrame.halt", "Pokedex_EndOwnerLoop.wait") if n in self.repo.symbols}
            if (full and not self.masked and (cpu.bank if cpu.pc >= 0x4000 else 0, cpu.pc) in wait_points
                    and cpu.ram[self.repo.symbols["wPokedexAnimPlaybackState"][1]] == 3
                    and not cpu.ram[self.repo.symbols["hSampledCryTimer"][1]]
                    and (not self.track_synth or not self.synth_active())):
                self.points.append(self.snapshot("Completed"))
                break
            if not self.masked:
                clock._due()
            self.observe()
            op = cpu.read(cpu.pc)
            self.step()
            if self.masked and op == 0xd9:
                self.masked = False
            if (cpu.steps-self.start_steps > 20000000 or
                    clock.t-self.points[0]["t"] > (max_frames if full else 64)*FRAME or cpu.pc == 0xffff):
                raise ModelError("Owner replay did not reach its bounded completion condition")
        return {"points": self.points, "elapsed_t": [b["t"]-a["t"] for a, b in zip(self.points, self.points[1:])],
                "initial_dictionary_tiles": self.initial_dictionary_tiles,
                "irq_costs_t": {k: sorted(set(v)) for k, v in self.irq_cycles.items()},
                "interrupts": deepcopy(self.clock.irq_counts), "hdma": self.dma_events,
                "observations": self.observations, "lifecycle": self.lifecycle,
                "operations": self.operations,
                "synth_audio": None if not self.track_synth else dict(
                    initial_flags=self.synth_initial_flags,final_flags=self.synth_flags(),
                    completed=not self.synth_active(),channel_writes=self.synth_changes,
                    hardware_writes=self.synth_writes,sound_updates=self.sound_updates),
                "scope": "full_animation_and_cry" if full else "first_miss",
                "totals_t": dict(self.clock.totals)}


def matching_div_phases(points, stops, timer_phase):
    """One divider phase must explain both timers at every stop.

    The normal timer increments every 64 T. The interrupt/reload follows the
    overflow edge by four T; TIMA is zero during that short pending-reload gap.
    The captured high DIV byte leaves its low byte unknown, not unconstrained
    independently of TIMA at each stop.
    """
    publication_t = points[0]["t"]
    for point, stop in zip(points, stops):
        since_reload = (point["t"]-timer_phase) % 12800
        tima = 0 if since_reload >= 12796 else 56+(since_reload+4)//64
        if tima != stop["tima"]:
            return []
    return [low for low in range(256)
            if (low+timer_phase-publication_t-4) % 64 == 0 and
            all(((stops[0]["div"]*256+low+p["t"]-publication_t)//256) & 255 == s["div"]
                for p, s in zip(points, stops))]


def captured_state_differences(repo, points, stops):
    masks = {"vblank": 1, "lcd": 2, "timer": 4}
    base = repo.symbols["wPokedexAnimOwner"][1]
    differences = []
    for point, stop in zip(points, stops):
        memory = {(b, a): v for b, a, v in stop["capture"]["memory"]}
        expected_anim = [memory[0, base+i] for i in range(27)]
        flags = int(stop["capture"]["hardware"].get(str(0xff0f), -1)) & 15
        pending = sum(masks[name] for name in point["pending"])
        expected = {key: stop[key] for key in ("ly", "counter", "cache", "remaining", "compressed",
                                              "read_address", "write_address", "source_address")}
        expected.update(mode=stop["stat"] & 3, anim=expected_anim, enabled_if=flags)
        actual = dict(point, enabled_if=pending)
        fields = [{"field": key, "captured": value, "modeled": actual[key]}
                  for key, value in expected.items() if actual[key] != value]
        if fields:
            differences.append({"stop": stop["label"], "fields": fields})
    return differences


def matches_captured_states(repo, points, stops):
    return not captured_state_differences(repo, points, stops)
