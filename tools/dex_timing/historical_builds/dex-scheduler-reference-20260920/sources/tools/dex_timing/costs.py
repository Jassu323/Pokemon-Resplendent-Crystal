"""Measure executable paths with controlled memory; validate the produced bytes."""

from .assets import offset
from .cpu import CounterCPU, ModelError


def instruction_path(cpu, stop, footer=False, arm_wait=False):
    """Retain instruction boundaries and the two clock-dependent owner operations."""
    stop_bank, address = cpu.symbols[stop]
    poll = cpu.symbols["PokedexSelectedMon_CopyBackingTileToVRAM.wait_vram"]
    arm = cpu.symbols["DelayFrame.halt"][1] - 3
    steps, initial = [], cpu.steps
    while cpu.pc != address or (stop_bank and cpu.bank != stop_bank):
        if cpu.pc == 0xffff or cpu.steps - initial > 100000:
            raise ModelError(f"Instruction fixture failed to reach {stop}")
        if footer and (cpu.bank, cpu.pc) == poll:
            if cpu.data(cpu.pc, 6) != bytes([0xf0, 0x41, 0xe6, 2, 0x20, 0xfa]):
                raise ModelError("Footer STAT-poll contract changed")
            for _ in range(3):
                cpu.step()  # Frozen ready path; the clock executes repeats.
            steps.append("stat")
        else:
            before, pc = cpu.cycles, cpu.pc
            cpu.step()
            if arm_wait and pc == arm:
                flag = cpu.symbols["wVBlankOccurred"][1]
                if cpu.data(pc, 3) != bytes([0xea, flag & 255, flag >> 8]):
                    raise ModelError("DelayFrame wait-arming contract changed")
                steps.append("arm")
            else:
                steps.append(cpu.cycles - before)
    return steps


def path_cost(path):
    return sum(28 if step == "stat" else 16 if step == "arm" else step for step in path)


def machine(repo, asset=None, cpu_class=CounterCPU):
    cpu = cpu_class(repo.rom, repo.symbols)
    # Frozen fixture registers: these routines only log LY; they must not poll it.
    cpu.allowed_io.add(0xFF44)
    cpu.field("hCGB", 1)
    cpu.field("wPokedexAnimFlags", 3)
    cpu.field("wPokedexAnimResidentFrameIDs", 0xFFFF, 2)
    if asset:
        cpu.field("wPokedexAnimFrontpicDim", asset.width)
        bank, address = repo.symbols[asset.labels["plan"]]
        cpu.field("wPokeAnimDexPlanBank", bank)
        cpu.field("wPokeAnimDexPlanAddr", address, 2)
        cpu.field("wPokedexAnimDictionaryTileCount", asset.total)
    return cpu


def read_field(cpu, name):
    return cpu.read(cpu.symbols[name][1])


def run_to(cpu, start, stop):
    bank, cpu.pc = cpu.symbols[start]
    if bank:
        cpu.bank = bank
    cpu.field("hROMBank", cpu.bank)
    cpu.push(0xFFFF)
    return continue_to(cpu, stop)


def continue_to(cpu, stop):
    cycles, steps = cpu.cycles, cpu.steps
    stop_bank, address = cpu.symbols[stop]
    while cpu.pc != address or (stop_bank and cpu.bank != stop_bank):
        if cpu.pc == 0xFFFF or cpu.steps-steps > 100000:
            raise ModelError(f"Fixture failed to reach {stop}")
        cpu.step()
    return cpu.cycles-cycles


def owner_prefix_benchmark(repo):
    """No-input main loop through footer writes, with VRAM immediately available."""
    costs = []
    for blink in (0, 8):
        for text_delay in (0, 1):
            for cursor_delay in (0, 1):
                cpu = machine(repo)
                cpu.allowed_io.add(0xFF41)
                cpu.field("hInMenu", 1)
                cpu.field("wJumptableIndex", 3)
                cpu.field("wDexArrowCursorBlinkCounter", blink)
                cpu.field("wDexArrowCursorDelayCounter", cursor_delay)
                cpu.field("wTextDelayFrames", text_delay)
                cpu.bank, cpu.pc = cpu.symbols["Pokedex.main"]
                cpu.field("hROMBank", cpu.bank)
                cpu.push(0xffff)
                path = instruction_path(cpu, "Pokedex_PrepareDescriptionAnimation", footer=True)
                if path.count("stat") != 4:
                    raise ModelError("Selected owner no longer writes four footer tiles")
                costs.append({"blink": blink, "text_delay": text_delay, "cursor_delay": cursor_delay,
                              "steps": path, "ready_t": path_cost(path)})
    return costs


def owner_shell_benchmark(repo):
    """Count caller/return paths around separately measured stage/producer work.

    Return from a callee without executing its body only where that body's full
    cost (including RET) is measured separately. Never bypass a hardware wait.
    """
    def fixture(flags):
        cpu = machine(repo)
        cpu.allowed_io.add(0xFF41)
        cpu.field("hInMenu", 1)
        cpu.field("wJumptableIndex", 3)
        cpu.field("wPokedexAnimPlaybackState", 2)
        cpu.field("wPokedexAnimFlags", flags)
        cpu.field("wPokedexAnimDeadline", 127)
        return cpu

    result = {"steps": {}}

    def measure(name, cpu, stop, arm_wait=False):
        path = instruction_path(cpu, stop, arm_wait=arm_wait)
        result[name+"_t"] = path_cost(path)
        result["steps"][name] = path

    cpu = fixture(0x47)
    run_to(cpu, "Pokedex.main", "Pokedex_PrepareDescriptionAnimation")
    measure("turnover_prefix", cpu, "Pokedex_PrepareNextAnimationStage")
    cpu.field("wPokedexAnimFlags", 7)
    cpu.pc = cpu.pop()  # Stage RET is included in event_t.
    measure("turnover_suffix", cpu, "Pokedex_ServiceAnimationProducer")
    for name, flags in (("waiting", 7), ("pending", 0x2F), ("ready", 15)):
        cpu = fixture(flags)
        run_to(cpu, "Pokedex.main", "Pokedex_PrepareDescriptionAnimation")
        measure(name+"_prepare", cpu, "Pokedex_ServiceAnimationProducer")
        cpu.pc = cpu.pop()  # Producer RET is included in idle_service_t.
        if name == "ready":
            measure("queue_prefix", cpu, "Pokedex_QueueReadyAnimationStage")
            cpu.pc = cpu.pop()  # Queue RET is included in queue_t.
            measure("queue_suffix", cpu, "DelayFrame.halt", arm_wait=True)
        else:
            measure(name+"_commit", cpu, "DelayFrame.halt", arm_wait=True)
    for deadline, name in ((127, "waiting"), (1, "underflow")):
        cpu = fixture(7)
        cpu.field("wPokedexAnimDeadline", deadline)
        run_to(cpu, "Pokedex.main", "Pokedex_ServiceAnimationProducer")
        cpu.pc = cpu.pop()
        measure("deadline_prefix", cpu, "Pokedex_AnimationDeadlineDue")
        # Execute the predicate with its existing caller stack, stopping at RET.
        returning = cpu.read(cpu.sp) | cpu.read(cpu.sp + 1) << 8
        cpu.symbols = dict(cpu.symbols, __deadline_return=(cpu.bank, returning))
        instruction_path(cpu, "__deadline_return")
        measure(name+"_after_deadline", cpu,
                "DelayFrame.halt" if name == "waiting" else "Pokedex_CountAnimationUnderflow",
                arm_wait=name == "waiting")
    result["deadline_steps"] = {}
    for deadline, name in ((127, "future"), (1, "equal"), (0, "late")):
        cpu = fixture(7)
        cpu.field("wPokedexAnimDeadline", deadline)
        cpu.bank, cpu.pc = repo.symbols["Pokedex_AnimationDeadlineDue"]
        cpu.push(0xffff)
        cpu.symbols = dict(cpu.symbols, __predicate_end=(0, 0xffff))
        result["deadline_steps"][name] = instruction_path(cpu, "__predicate_end")
    result["delay"] = delay_frame_benchmark(repo)
    return result


def delay_frame_benchmark(repo):
    """Count both wake branches and the return to the actual Dex owner."""
    address = repo.symbols["DelayFrame.halt"][1]
    if repo.rom[address] != 0x76 or repo.rom[address + 1] != 0:
        raise ModelError("DelayFrame HALT/NOP contract changed")
    result = {"halt_t": 4, "after_vblank": [], "after_other_irq": []}
    for flag, name, stop in ((0, "after_vblank", "ServiceSampledCryAsync"),
                             (1, "after_other_irq", "DelayFrame.halt")):
        cpu = machine(repo)
        cpu.pc = address + 1  # HALT is handled by the clock, not CounterCPU.
        cpu.field("wVBlankOccurred", flag)
        result[name] = instruction_path(cpu, stop)
    cpu = machine(repo)
    cpu.allowed_io.add(0xff41)
    cpu.field("hInMenu", 1)
    cpu.field("wJumptableIndex", 3)
    cpu.field("wPokedexAnimFlags", 0)
    run_to(cpu, "Pokedex.main", "DelayFrame.halt")
    cpu.pc = address + 1
    cpu.field("wVBlankOccurred", 0)
    continue_to(cpu, "ServiceSampledCryAsync")
    cpu.pc = cpu.pop()  # Audio body includes its RET.
    result["after_service"] = instruction_path(cpu, "Pokedex.main")
    return result


def gather_benchmark(repo):
    """Exact gather termination paths; no assumed per-tile slope in the model."""
    result = {"stage_end": [], "upload_cap": [], "not_ready": []}
    scratch = repo.symbols["wPokedexWRAM0Scratch"][1]
    for reason in result:
        for count in range(21):
            cpu = machine(repo)
            cpu.ram[0xFF70] = 6
            cpu.field("wPokedexAnimFlags", 7)
            cpu.field("wPokedexAnimStageTileCount", count if reason == "stage_end" else 49)
            cpu.field("wPokedexAnimDictionaryTileCount", 255)
            # Equality is the longer of the two failed-readiness branches.
            cpu.field("wPokedexAnimDictionaryTilesRemaining", 255-count if reason == "not_ready" else 0)
            cpu.block(scratch+0x460, bytes(range(49)))
            cost = cpu.run("Pokedex_GatherReadyAnimationTiles")
            actual = cpu.r[1]
            if actual != (20 if reason == "upload_cap" else count):
                raise ModelError("Gather termination contract changed")
            result[reason].append(cost)
    return result


def benchmark(repo, asset):
    """Counts include callee RETs, not the caller's CALL unless stated.

    Every stream and every frame is checked against independent host output.
    Costs include the CURRENT temporary tracing instructions where executed.
    No clock/interrupt/DMA time is included in these CPU-only measurements.
    """
    decode = []
    bank, base_address = repo.symbols[asset.labels["front"]]
    produced = 0
    for stream in asset.streams:
        cpu = machine(repo, asset)
        cpu.ram[0xFF70] = 6
        cpu.r[7] = bank
        cpu.set_pair(2, base_address + stream.start)
        cpu.set_pair(1, 0xD000+produced)
        cycles = cpu.run("FarDecompress")
        if cpu.data(0xD000+produced, len(stream.output)) != stream.output:
            raise ModelError(f"Linked decoder differs from reference: {asset.name}, stream {len(decode)}")
        if cpu.pair(2) != base_address+stream.end-1:
            raise ModelError("Linked decoder terminator position mismatch")
        service_cycles = cycles
        if produced:
            cpu = machine(repo, asset)
            cpu.field("wPokedexAnimDictionaryBank", bank)
            cpu.field("wPokedexAnimDictionaryAddress", base_address+stream.start, 2)
            cpu.field("wPokedexAnimDictionaryDestination", 0xD000+produced, 2)
            cpu.field("wPokedexAnimDictionaryTilesRemaining", asset.total-produced//16)
            service_cycles = cpu.run("Pokedex_ServiceAnimationDictionaryChunk")
            if cpu.wram[6][produced:produced+len(stream.output)] != stream.output:
                raise ModelError("Dictionary service produced incorrect bytes")
        decode.append({"tiles": len(stream.output)//16, "far_decompress_t": cycles,
                       "service_t": service_cycles, "commands": stream.commands})
        produced += len(stream.output)

    builds, gathers, queues = [], [], []
    gather_paths = gather_benchmark(repo)
    scratch = repo.symbols["wPokedexWRAM0Scratch"][1]
    for frame, plan in enumerate(asset.plans):
        slots, slot_gathers, slot_queues = [], [], []
        for slot in (0, 1):
            cpu = machine(repo, asset)
            cpu.field("wPokedexAnimStageSlot", slot)
            cpu.field("wPokedexAnimStageFrameID", frame)
            cycles = cpu.run("Pokedex_BuildAnimationStage")
            slots.append(cycles)
            if read_field(cpu, "wPokedexAnimStageTileCount") != len(plan.sources):
                raise ModelError(f"Linked stage count mismatch: {asset.name} frame {frame}")
            if cpu.data(scratch+0x460, len(plan.sources)) != bytes(plan.sources):
                raise ModelError(f"Linked stage sources mismatch: {asset.name} frame {frame}")
            if frame:
                address = scratch+(0x39C if slot == 0 else 0x3FE)
                expected = [x*7+y for y in range(7) for x in range(7)]
                attrs = [1]*49
                tail = 0
                for pos, source in plan.pairs:
                    if pos & 128:
                        expected[pos & 127] = source
                    else:
                        expected[pos] = (0x80 if slot == 0 else 0x33)+tail
                        attrs[pos] = 9
                        tail += 1
                if cpu.data(address, 98) != bytes(expected+attrs):
                    raise ModelError(f"Linked stage maps mismatch: {asset.name} frame {frame}")
            cpu.ram[0xFF70] = 6
            cpu.block(0xD000, asset.dictionary)
            cpu.field("wPokedexAnimFlags", 7)
            per_offset = {}
            # All offsets, not just 0/20/40: a dictionary shortage can split a gather.
            for start in range(len(plan.sources)+1):
                cpu.field("wPokedexAnimUploadOffset", start)
                count = min(20, len(plan.sources)-start)
                cost = cpu.run("Pokedex_GatherReadyAnimationTiles")
                if cpu.r[1] != count:
                    raise ModelError("Unexpected gather length")
                termination = "stage_end" if start+count == len(plan.sources) else "upload_cap"
                if cost != gather_paths[termination][count]:
                    raise ModelError("Gather cost depends on an unmodeled path")
                expected = b"".join(asset.dictionary[s*16:s*16+16] for s in plan.sources[start:start+count])
                if cpu.data(scratch+start*16, count*16) != expected:
                    raise ModelError("Gather output mismatch")
                per_offset[str(start)] = cost
            slot_gathers.append(per_offset)
            cpu.field("wPokedexAnimFlags", 15)
            slot_queues.append(cpu.run("Pokedex_QueueReadyAnimationStage"))
        builds.append(slots)
        gathers.append(slot_gathers)
        queues.append(slot_queues)

    # Event turnover includes reading the real timeline, resident lookup and trace.
    cursor = repo.symbols[asset.labels["timeline"]][1]
    event_costs = []
    event_trace = []
    for event in asset.events:
        alternatives = []
        trace_alternatives = []
        next_cursor = None
        for slot in (0, 1):
            paths = {}
            trace_paths = {}
            for resident in (False, True):
                cpu = machine(repo, asset)
                cpu.field("wPokedexAnimTimelineAddress", cursor, 2)
                cpu.field("wPokedexAnimStageSlot", slot)
                if resident and event.frame:
                    cpu.field("wPokedexAnimResidentFrameIDs", event.frame if slot == 0 else event.frame << 8, 2)
                cpu.record_writes = True
                key = "resident" if resident else "new"
                paths[key] = cpu.run("Pokedex_PrepareNextAnimationStage")
                trace_paths[key] = trace_span(cpu, "StageEntry", "StageChecked")
                next_cursor = int.from_bytes(cpu.data(repo.symbols["wPokedexAnimTimelineAddress"][1], 2), "little")
                if read_field(cpu, "wPokedexAnimStageFrameID") != event.frame:
                    raise ModelError("Linked timeline reader differs from reference")
            alternatives.append(paths)
            trace_alternatives.append(trace_paths)
        event_costs.append(alternatives)
        event_trace.append(trace_alternatives)
        cursor = next_cursor

    cpu = machine(repo, asset)
    cpu.field("wPokedexAnimFlags", 15)
    cpu.field("wPokedexAnimPlaybackState", 2)
    cpu.field("wPokedexAnimScheduleRun", 2)
    idle = cpu.run("Pokedex_ServiceAnimationProducer")
    # The branch that refills a schedule run executes a farcall as well.
    cpu.field("wPokedexAnimScheduleRun", 0)
    cpu.field("wPokedexAnimScheduleAddress", repo.symbols[asset.labels["schedule"]][1], 2)
    schedule_read = cpu.run("Pokedex_GetNextAnimationScheduleAction")
    cpu.field("wPokedexAnimScheduleRun", 2)
    continuation = cpu.run("Pokedex_GetNextAnimationScheduleAction")
    cpu.field("wPokedexAnimScheduleRun", 0)
    cpu.field("wPokedexAnimScheduleAddress", repo.symbols[asset.labels["schedule"]][1], 2)
    schedule_costs = []
    for action in asset.actions:
        schedule_costs.append(cpu.run("Pokedex_GetNextAnimationScheduleAction"))
        if cpu.r[7] != action << 6:
            raise ModelError("Linked schedule reader differs from expanded host schedule")

    owner = owner_prefix_benchmark(repo)
    return {"name": asset.name, "total_tiles": asset.total, "base_tiles": asset.width**2,
            "sample_blocks": asset.sample_blocks, "decode": decode, "build_t": builds,
            "gather_t": gathers, "queue_t": queues, "event_t": event_costs, "event_trace_t": event_trace,
            "idle_service_t": idle, "schedule_read_t": schedule_read,
            "owner_prefix_t": sorted({p["ready_t"] for p in owner}),
            "owner_prefix_paths": owner,
            "owner_shell_t": owner_shell_benchmark(repo),
            "schedule_action_extra_t": [t-continuation for t in schedule_costs],
            "gather_paths_t": gather_paths}


def trace_span(cpu, start, end):
    """Use the LY read behind each stored timestamp, not the later store time."""
    stamps = []
    for field in (start, end):
        address = cpu.symbols["wPokedexAnimTrace"+field+"LY"][1]
        written = [t for t, a, _ in cpu.writes if a == address][-1]
        stamps.append([t for t, a, _ in cpu.io_reads if a == 0xFF44 and t < written][-1])
    return stamps[1]-stamps[0]


def upload_trace_benchmark(repo, asset, frame, slot, start, reload_run=False):
    """Measure through the gather stamp, stopping before the hardware helper.

    This fixture has a complete dictionary, matching the Weavile/Luxray captures.
    The ROM's HDMA wrapper is counted up to helper entry; no hardware call is
    stubbed out as if free, and this is not a complete producer measurement.
    """
    cpu = machine(repo, asset)
    cpu.field("wPokedexAnimStageSlot", slot)
    cpu.field("wPokedexAnimStageFrameID", frame)
    cpu.run("Pokedex_BuildAnimationStage")
    cpu.field("wPokedexAnimFlags", 7)
    cpu.field("wPokedexAnimPlaybackState", 2)
    cpu.field("wPokedexAnimDictionaryTilesRemaining", 0)
    cpu.field("wPokedexAnimUploadOffset", start)
    cpu.field("wPokedexAnimScheduleRun", 0 if reload_run else 0xC1)
    if reload_run:
        bank, address = repo.symbols[asset.labels["schedule"]]
        # The first run with the upload action exercises the real farcall path.
        raw = repo.rom[offset((bank, address)):offset((bank, address))+asset.sizes["schedule"]]
        upload = next(i for i, value in enumerate(raw) if value & 0xC0 == 0xC0)
        cpu.field("wPokedexAnimScheduleAddress", address+upload, 2)
    cpu.wram[6][:len(asset.dictionary)] = asset.dictionary
    cpu.allowed_io.add(0xFF40)
    cpu.ram[0xFF40] = 0x80
    cpu.bank, cpu.pc = repo.symbols["Pokedex_ServiceAnimationProducer"]
    cpu.field("hROMBank", cpu.bank)
    cpu.push(0xFFFF)
    cpu.record_writes = True
    stop_bank, stop = repo.symbols["HDMATransfer_Exact_NoDI_Arbitrary"]
    initial_steps = cpu.steps
    while (cpu.bank, cpu.pc) != (stop_bank, stop):
        if cpu.pc == 0xFFFF or cpu.steps-initial_steps > 100000:
            raise ModelError("Upload fixture failed to reach the HDMA helper")
        cpu.step()
    entry_write = [t for t, a, _ in cpu.writes if a == cpu.symbols["wPokedexAnimTraceHDMAEntryLY"][1]][-1]
    entry_read = [t for t, a, _ in cpu.io_reads if a == 0xFF44 and t < entry_write][-1]
    return {"gather_trace_t": trace_span(cpu, "Dictionary", "Gather"),
            "hdma_entry_to_helper_t": cpu.cycles-entry_read}


def audio_benchmark(repo):
    """Real pair-decoder and the interrupts active during sampled playback."""
    sample = "DusknoirSampledCry"
    bank, address = repo.symbols[sample]
    blocks = int.from_bytes(repo.rom[offset(repo.symbols[sample]):offset(repo.symbols[sample])+2], "little")
    result = {"refill": {}, "timer_irq_t": []}
    end = repo.symbols["wSampledCryDecodedBufferEnd"][1]
    for count in list(range(1, 9)) + [32]:
        variants = []
        for wrap in (False, True):
            cpu = machine(repo)
            cpu.bank = bank
            cpu.ram[0xFF70] = 4
            cpu.field("hSampledCryBank", bank)
            cpu.field("hSampledCryTimer", 1)
            cpu.field("wSampledCryCompressedAddress", address+2, 2)
            cpu.field("wSampledCryCompressedBlocks", blocks, 2)
            cpu.field("wSampledCryCacheWriteAddress", end-16 if wrap else 0xD000, 2)
            cpu.r[0] = count
            cpu.record_writes = True
            cost = cpu.run("SampledCry_FillRollingCache")
            cache = repo.symbols["wSampledCryCacheCount"][1]
            publication = [t+12 for t, a, v in cpu.writes if a == cache and v]
            if len(publication) != count or cpu.read(cache) != count:
                raise ModelError("Audio refill did not publish the expected number of blocks")
            source = offset(repo.symbols[sample])+2
            destination = end-16 if wrap else 0xD000
            for block in range(count):
                encoded = repo.rom[source+block*9:source+(block+1)*9]
                low, high = encoded[0] >> 4, encoded[0] & 15
                delta = high-low
                levels = (low, low+(delta+1)//3, low+(2*delta+1)//3, high) if delta >= 0 else (low,)*4
                expected = bytes(value for selectors in encoded[1:] for value in
                                 ((levels[selectors >> 6] << 4) | levels[(selectors >> 4) & 3],
                                  (levels[(selectors >> 2) & 3] << 4) | levels[selectors & 3]))
                if cpu.data(destination, 16) != expected:
                    raise ModelError("Executed pair-decoder output differs from independent reference")
                destination += 16
                if destination == end:
                    destination = 0xD000
            variants.append({"t": cost, "publish_t": publication, "wrap": wrap})
        result["refill"][str(count)] = variants
    for wrap in (False, True):
        cpu = machine(repo)
        cpu.allowed_io.update(range(0xFF10, 0xFF40))
        cpu.field("hSampledCryTimer", 1)
        cpu.field("hSampledCryBlocks", blocks, 2)
        cpu.field("hSampledCryAddress", end-16 if wrap else 0xD000, 2)
        cpu.field("wSampledCryCacheCount", 32)
        cpu.field("wSampledCryBlockPeriod", 200)
        result["timer_irq_t"].append(interrupt_cost(cpu, 0x50, "SampledCryTimer"))
    cpu = machine(repo)
    cpu.field("hLCDCPointer", 0)
    result["lcd_irq_t"] = interrupt_cost(cpu, 0x48, "LCD")
    wrapper_costs = []
    for prefix_only in (False, True):
        cpu = machine(repo)
        cpu.field("hSampledCryTimer", 1)
        cpu.field("hSampledCryBank", bank)
        cpu.field("wSampledCryCompressedAddress", address+2, 2)
        cpu.field("wSampledCryCompressedBlocks", blocks, 2)
        cpu.field("wSampledCryCacheWriteAddress", 0xD000, 2)
        wrapper_costs.append(run_to(cpu, "ServiceSampledCryAsync", "SampledCry_FillRollingCache")
                             if prefix_only else cpu.run("ServiceSampledCryAsync"))
    full, prefix = wrapper_costs
    body = result["refill"]["8"][0]["t"]
    result["service_prefix_t"] = prefix
    result["service_suffix_t"] = full-body-prefix
    return result


def interrupt_cost(cpu, vector, handler):
    """Execute the linked vector JP too; only hardware entry is added manually."""
    address = cpu.symbols[handler][1]
    if cpu.rom[vector:vector+3] != bytes([0xC3, address & 255, address >> 8]):
        raise ModelError(f"Interrupt vector ${vector:04x} no longer jumps to {handler}")
    cpu.symbols = dict(cpu.symbols, __timing_vector=(0, vector))
    return cpu.run("__timing_vector") + 20


def publication_benchmark(repo):
    cpu = machine(repo)
    cpu.allowed_io.update(range(0xFF51, 0xFF56))
    cpu.ram[0xFF44] = 144
    cpu.field("wPokedexAnimFlags", 0x23)
    cpu.field("wPokedexAnimDeadline", 1)
    cpu.record_writes = True
    software = cpu.run("Pokedex_VBlankAnimationFrontpicMap")
    transfers = [v+1 for _, a, v in cpu.writes if a == 0xFF55]
    if transfers != [14, 14]:
        raise ModelError(f"Publication DMA contract changed: {transfers}")
    return {"software_t": software, "gdma_blocks": sum(transfers),
            "gdma_t": sum(transfers)*32,
            "vblank": vblank_benchmark(repo),
            "note": "Inner publication cost above; separate VBlank fixtures include the outer handler."}


def vblank_benchmark(repo):
    """Selected idle/publish paths: OAM enabled, no input, sampled sound active.

    The HRAM OAM busy wait is executed, not charged again as a CPU halt. These
    fixtures do not model queued palette/tile transfers or active synth music.
    """
    result = {}
    for path in ("idle", "pending_early", "publish"):
        cpu = machine(repo)
        cpu.allowed_io.update([0xFF00, 0xFF04, 0xFF40, 0xFF42, 0xFF43,
                               0xFF46, 0xFF4A, 0xFF4B, *range(0xFF51, 0xFF56)])
        cpu.io_read_values[0xFF00] = 0x0F  # Released buttons, despite JOYP writes.
        cpu.ram[0xFF44] = 144
        cpu.field("hSampledCryTimer", 1)
        cpu.field("wGameTimerPaused", 1)
        cpu.field("wPokedexSelectedState", 1)
        begin = offset(repo.symbols["OAMDMACode"])
        end = offset(repo.symbols["OAMDMACode.End"])
        cpu.block(repo.symbols["hTransferShadowOAM"][1], repo.rom[begin:end])
        if path != "idle":
            cpu.field("hVBlank", 7)
            cpu.field("wPokedexAnimFlags", 0x23)
            cpu.field("wPokedexAnimDeadline", 2 if path == "pending_early" else 1)
        cpu.record_writes = True
        result[path+"_t"] = interrupt_cost(cpu, 0x40, "VBlank")
        if path == "publish":
            # Time to the map handler's LY read, including vector and HW entry.
            result["publish_check_t"] = next(t+20 for t, a, _ in cpu.io_reads if a == 0xFF44)
    return result


def verify_hdma_contract(repo):
    start = repo.symbols["HDMATransfer_Exact_NoDI_Arbitrary"]
    loop = repo.symbols["HDMATransfer_Exact_NoDI_Arbitrary.ly_loop"][1]
    for count in range(1, 21):
        cpu = machine(repo)
        cpu.allowed_io.update(range(0xFF51, 0xFF55))
        cpu.bank, cpu.pc = start
        cpu.r[1] = count
        cpu.set_pair(2, 0xC800)
        cpu.set_pair(1, 0x8800)
        while cpu.pc != loop and cpu.steps < 100:
            cpu.step()
        if cpu.pc != loop or cpu.cycles != 124 or cpu.r[2] != 128-count or cpu.r[0] != (count-1) | 128:
            raise ModelError("HDMA setup/launch contract changed; update the clock model")
