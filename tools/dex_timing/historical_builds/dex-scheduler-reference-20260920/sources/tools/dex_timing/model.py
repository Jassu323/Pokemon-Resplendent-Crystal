"""Display-clock experiment, deliberately not a calibrated hardware verdict.

Known CPU paths come from the linked ROM. A profile supplies external workload
and PPU phase assumptions. Missing costs remain listed in every report; zero is
only an optimistic experiment, never evidence that the omitted work is free.
"""

from dataclasses import dataclass, field
import heapq

from .cpu import ModelError

LINE, FRAME, VISIBLE = 456, 70224, 144
CPU_HZ = 4194304


@dataclass
class Profile:
    hblank_dot: int = 369
    lcd_stat_enabled: bool = True
    outer_loop_t: int = 0
    vblank_other_t: int = 0
    vblank_dispatch_t: int = 0
    service_extra_t: int = 0
    refill_wrapper_t: int = 0
    audio_period_t: int = 12800
    audio_phase_t: int = 12800
    audio_played_at_publication: int = 1
    owner_variant: int = 0
    prefill: int = 32
    startup_tail: int = 96
    unknown: list = field(default_factory=lambda: [
        "owner input/blink state and actual per-line PPU mode lengths beyond the no-input fixtures",
        "VBlank state-dependent transfers, timer rollover and active synth sound beyond the idle fixture",
        "producer non-idle branch/wrapper beyond the idle and schedule-reader fixtures",
        "audio source-borrow/cache-boundary branches beyond refill fixtures",
        "sample timer phase and blocks already consumed at first publication unless captured",
        "HDMA polling alignment and interrupt-entry instruction granularity",
        "cold/warm/paging UI preparation and reveal outside animation priming",
    ])

    def validate(self):
        if type(self.lcd_stat_enabled) is not bool:
            raise ModelError("lcd_stat_enabled must be a boolean")
        values = (self.hblank_dot, self.outer_loop_t, self.vblank_other_t,
                  self.vblank_dispatch_t, self.service_extra_t, self.refill_wrapper_t,
                  self.audio_period_t, self.audio_phase_t, self.audio_played_at_publication,
                  self.owner_variant, self.prefill, self.startup_tail)
        if any(type(value) is not int for value in values):
            raise ModelError("Timing-profile values must be integer T-cycle counts")
        if not 252 <= self.hblank_dot <= 369:
            raise ModelError("HBlank start must be within the modeled 252..369-dot envelope")
        if min(self.outer_loop_t, self.vblank_other_t, self.vblank_dispatch_t,
               self.service_extra_t, self.refill_wrapper_t) < 0:
            raise ModelError("Negative CPU workload")
        if self.vblank_other_t+self.vblank_dispatch_t >= FRAME:
            raise ModelError("Multi-frame masked interrupts are outside this model")
        if self.audio_period_t != 12800 or self.prefill != 32 or self.startup_tail != 96:
            raise ModelError("This experiment pins normal-speed/normal-pitch, prefill 32 and startup tail 96")
        if not 1 <= self.audio_phase_t <= self.audio_period_t:
            raise ModelError("Audio phase must be within the first timer period")
        if not 1 <= self.audio_played_at_publication <= self.prefill:
            raise ModelError("Initial audio consumption must fit the startup cache")
        if not 0 <= self.owner_variant < 8:
            raise ModelError("Owner variant must select one of the eight no-input fixtures")


class Clock:
    """IRQ execution consumes CPU, but does not pause the PPU or an HDMA train."""

    def __init__(self, profile, audio, sample_blocks=0):
        self.p, self.audio = profile, audio
        self.t = 0
        self.vblank_count = 0
        self.next_vblank = FRAME
        self.next_timer = profile.audio_phase_t if sample_blocks else float("inf")
        self.next_lcd = 10*LINE+profile.hblank_dot if profile.lcd_stat_enabled else float("inf")
        self.pending = set()
        self.irq_counts = {name: {"requested": 0, "delivered": 0, "coalesced": 0}
                           for name in ("vblank", "lcd", "timer")}
        self.dma = []
        played = min(sample_blocks, profile.audio_played_at_publication)
        self.remaining = sample_blocks-played
        self.cache = min(sample_blocks, profile.prefill)-played
        self.compressed = max(0, sample_blocks-profile.prefill)
        self.min_cache = self.cache
        self.audio_underrun = None
        self.on_vblank = lambda: 0
        self.totals = {}
        self.events = []
        self.wait_armed_count = None

    @property
    def ly(self):
        # CGB line 153 reports LY zero before the PPU leaves VBlank. The few
        # revision-dependent leading dots remain an explicit boundary limit.
        return 0 if self.physical_line == 153 and self.dot >= 8 else self.physical_line

    @property
    def physical_line(self):
        return (144 + self.t // LINE) % 154

    @property
    def mode(self):
        if self.physical_line >= VISIBLE:
            return 1
        return 2 if self.dot < 80 else 3 if self.dot < self.p.hblank_dot else 0

    @property
    def dot(self):
        return self.t % LINE

    def record(self, kind, cycles):
        self.totals[kind] = self.totals.get(kind, 0) + cycles

    def _next(self, masked=False):
        if self.pending and not masked:
            return self.t
        return min(self.dma[0] if self.dma else float("inf"),
                   self.next_vblank, self.next_lcd, self.next_timer)

    def _request(self, name):
        self.irq_counts[name]["requested"] += 1
        if name in self.pending:
            self.irq_counts[name]["coalesced"] += 1
        self.pending.add(name)

    def _collect(self):
        # Hardware continues while IME is clear. IF holds one bit per source,
        # not a queue of all scanlines missed inside another handler.
        while self.dma and self.dma[0] <= self.t:
            heapq.heappop(self.dma)
            self.t += 32
            self.record("dma_cpu_halt", 32)
        while self.next_vblank <= self.t:
            self.next_vblank += FRAME
            self._request("vblank")
        while self.next_lcd <= self.t:
            ly = (144 + self.next_lcd // LINE) % 154
            self.next_lcd += (11 if ly == 143 else 1)*LINE
            self._request("lcd")
        while self.next_timer <= self.t:
            self.next_timer += self.p.audio_period_t
            self._request("timer")

    def _due(self, masked=False):
        while True:
            self._collect()
            if masked or not self.pending:
                return
            name = next(n for n in ("vblank", "lcd", "timer") if n in self.pending)
            self.pending.remove(name)
            self.irq_counts[name]["delivered"] += 1
            if name == "vblank":
                self.work(self.p.vblank_dispatch_t, "vblank_dispatch", masked=True)
                extra = self.on_vblank()
                self.work(extra+self.p.vblank_other_t, "vblank", masked=True)
                self.vblank_count += 1
            elif name == "lcd":
                self.work(self.audio["lcd_irq_t"], "lcd_irq", masked=True)
            else:
                if not self.remaining:
                    self.next_timer = float("inf")
                    continue
                if not self.cache:
                    self.audio_underrun = self.t
                    self.next_timer = float("inf")
                    self.events.append({"kind": "audio_underrun", "t": self.t, "remaining": self.remaining})
                    continue
                self.cache -= 1
                self.remaining -= 1
                self.min_cache = min(self.min_cache, self.cache)
                self.work(max(self.audio["timer_irq_t"]), "timer_irq", masked=True)

    def work(self, cycles, kind="mainline", masked=False, defer_boundary_irq=False):
        self.record(kind, cycles)
        while cycles:
            self._due(masked)
            amount = min(cycles, self._next(masked)-self.t)
            self.t += amount
            cycles -= amount
        # An event on the last instruction boundary is serviced before the caller
        # can publish new work. Masked IRQs are drained by the enclosing context.
        if not masked and not defer_boundary_irq:
            self._due()

    def wait(self, until, kind="wait"):
        start = self.t
        while self.t < until:
            self._due()
            self.t = max(self.t, min(until, self._next()))
        self._due()
        self.record(kind, self.t-start)

    def instruction(self, cycles, kind):
        self._due()
        self.work(cycles, kind, masked=True)
        self._due()

    def read_instruction(self, cycles, read_offset, read, kind):
        self._due()
        self.work(read_offset, kind, masked=True)
        value = read()
        self.work(cycles-read_offset, kind, masked=True)
        self._due()
        return value

    def footer_wait(self):
        begin, repeats = self.t, 0
        while True:
            # LDH's data read is in its third M-cycle. An interrupt after the
            # read does not change the saved mode tested by AND/JR.
            busy = self.read_instruction(12, 8, lambda: self.mode & 2, "footer_poll")
            self.instruction(8, "footer_poll")
            self.instruction(12 if busy else 8, "footer_poll")
            if not busy:
                break
            repeats += 1
            if self.t-begin > 2*FRAME:
                raise ModelError("Footer polling failed to find a VRAM access window")
        self.events.append({"kind": "footer_wait", "entry_t": begin, "done_t": self.t,
                            "busy_polls": repeats})

    def run_path(self, steps, kind):
        for step in steps:
            if step == "stat":
                self.footer_wait()
            elif step == "arm":
                self._due()
                self.wait_armed_count = self.vblank_count
                self.work(16, kind, masked=True)
                self._due()
            else:
                self.instruction(step, kind)

    def deadline_due(self, paths, deadline):
        upcoming = self.read_instruction(12, 8, lambda: self.vblank_count+1, "deadline_check")
        name = "future" if upcoming*FRAME < deadline else "equal" if upcoming*FRAME == deadline else "late"
        self.run_path(paths[name][1:], "deadline_check")
        return name != "future"

    def delay_frame(self, paths, resume_after_irq=False):
        """Execute HALT wakes, the flag read/branch, audio service and owner return.

        A VBlank before the arm store cannot satisfy the new wait. A VBlank
        after that store can, even if it interrupts the path to HALT.
        """
        if self.wait_armed_count is None:
            raise ModelError("DelayFrame reached without arming its wait")
        begin, wakes = self.t, 0
        while True:
            if not resume_after_irq:
                # A pending interrupt serviced before HALT cannot wake a HALT
                # that has not executed yet.
                self._due()
                before = sum(v["delivered"] for v in self.irq_counts.values())
                self.instruction(paths["halt_t"], "delay_glue")
                while sum(v["delivered"] for v in self.irq_counts.values()) == before:
                    self.t = max(self.t, self._next())
                    self._due()
            resume_after_irq = False
            wakes += 1
            self.instruction(paths["after_vblank"][0], "delay_glue")  # NOP
            waiting = self.read_instruction(16, 12,
                lambda: self.vblank_count <= self.wait_armed_count, "delay_glue")
            self.run_path(paths["after_other_irq" if waiting else "after_vblank"][2:], "delay_glue")
            if not waiting:
                break
            if self.t-begin > 2*FRAME:
                raise ModelError("DelayFrame did not observe its next VBlank")
        self.refill()
        self.run_path(paths["after_service"], "delay_glue")
        self.events.append({"kind": "delay_frame", "entry_t": begin, "done_t": self.t,
                            "wake_count": wakes, "armed_counter": self.wait_armed_count,
                            "returned_counter": self.vblank_count})
        self.wait_armed_count = None

    def refill(self):
        if not self.remaining or self.audio_underrun is not None:
            return
        count = min(8, self.compressed, 191-self.cache)
        if not count:
            return
        self.work(self.p.refill_wrapper_t+self.audio.get("service_prefix_t", 0), "refill_wrapper")
        variant = max(self.audio["refill"][str(count)], key=lambda v: v["t"])
        previous = 0
        for publication in variant["publish_t"]:
            self.work(publication-previous, "audio_decode", defer_boundary_irq=True)
            self.cache += 1
            self.compressed -= 1
            self._due()
            previous = publication
        self.work(variant["t"]-previous, "audio_decode")
        self.work(self.audio.get("service_suffix_t", 0), "refill_wrapper")

    def hdma(self, count):
        if not 1 <= count <= 20:
            raise ModelError("Invalid bounded HDMA tile count")
        begin = self.t
        self.work(124, "hdma_setup")
        while self.ly >= 128-count:
            self.work(28, "hdma_launch_poll")
        self.work(24, "hdma_launch_poll")
        while self.mode == 0:
            self.work(32, "hdma_launch_poll")
        self.work(44, "hdma_setup")
        launch = self.t
        line_start = self.t - self.dot
        hblank = line_start + self.p.hblank_dot
        if hblank <= self.t:
            hblank += LINE
        blocks = []
        while len(blocks) < count:
            ly = (144 + hblank // LINE) % 154
            if ly < VISIBLE:
                blocks.append(hblank)
            hblank += LINE
        for tick in blocks:
            heapq.heappush(self.dma, tick)
        self.wait(blocks[-1]+32, "hdma_poll_elapsed")
        self.work(44, "hdma_finish")
        self.events.append({"kind": "hdma", "tiles": count, "entry_t": begin,
                            "launch_t": launch, "first_block_t": blocks[0], "done_t": self.t})


def expand_loop(items, loop, repetitions):
    if loop is None:
        return list(enumerate(items))
    return list(enumerate(items[:loop])) + list(enumerate(items[loop:], loop))*repetitions


def simulate(asset, costs, audio, publication, profile, initial_ly=144, loops=2, audio_enabled=True, path="cold"):
    """Model CURRENT call-index scheduling, not a proposed corrected scheduler.

    Stop at the first animation deadline miss. The runtime intentionally draws
    an underflow map there; continuing would require modeling that new state.
    Startup is reported separately as CPU work, not total input-to-reveal time.
    """
    profile.validate()
    if path not in ("cold", "warm", "paging"):
        raise ModelError("Unknown entry path")
    if not 0 <= initial_ly < 154 or not 1 <= loops <= 16:
        raise ModelError("Invalid initial phase or loop bound")
    events = expand_loop(asset.events, asset.event_loop, loops)
    schedule = expand_loop(asset.actions, asset.action_loop, loops+2)
    actions = [action for _, action in schedule]
    schedule_extra = [costs["schedule_action_extra_t"][index] for index, _ in schedule]
    shell = costs["owner_shell_t"]
    owner = costs["owner_prefix_paths"][profile.owner_variant]
    base, loaded, chunk = asset.width**2, asset.width**2, 1
    initial_target = min(asset.total, max(base+profile.startup_tail, asset.plans[events[0][1].frame].high_water))
    prime_cpu = costs["decode"][0]["service_t"]
    while loaded < initial_target:
        prime_cpu += costs["decode"][chunk]["service_t"]
        loaded += costs["decode"][chunk]["tiles"]
        chunk += 1
    startup_loaded = loaded
    initial_frame = events[0][1].frame
    prime_cpu += costs["event_t"][0][0]["new"] + costs["queue_t"][initial_frame][0]
    for start in range(0, len(asset.plans[initial_frame].sources), 20):
        prime_cpu += costs["gather_t"][initial_frame][0][str(start)]
    if path == "warm":
        # Warming stops at the first event's high-water target; it does not
        # automatically decode the entire dictionary (notably for Dusknoir).
        target = max(initial_target, asset.events[0].target)
        while loaded < target:
            loaded += costs["decode"][chunk]["tiles"]
            chunk += 1
        startup_loaded = loaded
        prime_cpu = costs["queue_t"][initial_frame][0]
    clock = Clock(profile, audio, asset.sample_blocks if audio_enabled else 0)
    residents = [initial_frame if initial_frame else -1, -1]
    slot, displayed, current = 1 if initial_frame else 0, 0 if initial_frame else None, 1
    deadline = events[0][1].duration*FRAME
    authored_end = sum(e.duration for _, e in events)*FRAME
    state = {"queued": False, "published": False, "miss": None, "frame": None,
             "slot": slot, "ready": False, "uploaded": 0}
    publishes = [{"event": 0, "frame": initial_frame, "t": 0, "deadline_t": 0}]
    calls, action_index = 0, 0
    recent_calls = []

    def vblank():
        vb = publication["vblank"]
        if not state["queued"] or current >= len(events) or state["published"]:
            return vb["idle_t"]
        prefix = vb["publish_check_t"]
        clock.work(prefix, "vblank_publish_check", masked=True)
        if (clock.vblank_count+1)*FRAME < deadline or clock.ly >= 146:
            # The ROM defers publication here; this is NOT the mainline
            # CountAnimationUnderflow breakpoint. Keep late publishes separate.
            return vb["pending_early_t"]-prefix
        state["published"] = True
        state["queued"] = False
        publishes.append({"event": current, "frame": state["frame"], "t": clock.t, "deadline_t": deadline,
                          "late_intervals": clock.vblank_count+1-deadline//FRAME})
        return vb["publish_t"]-prefix + publication["gdma_t"]

    clock.on_vblank = vblank
    clock.work(publication["vblank"]["publish_t"]+publication["gdma_t"]+profile.vblank_other_t,
               "initial_publication", masked=True)
    entry = ((initial_ly-144) % 154)*LINE
    clock.wait(max(clock.t, entry), "initial_phase")
    # The first publication interrupted the existing DelayFrame HALT. Resume
    # its flag check rather than inventing another whole-frame wait.
    clock.wait_armed_count = -1
    clock.delay_frame(shell["delay"], resume_after_irq=True)
    while current < len(events) and not state["miss"]:
        if calls > 10000 or clock.t > 4000*FRAME:
            raise ModelError(f"Simulation did not progress: {asset.name}")
        clock.run_path(owner["steps"], "outer_loop")
        clock.work(profile.outer_loop_t, "outer_loop_extra")
        if state["published"]:
            displayed = state["slot"] if state["frame"] else None
            if displayed is not None:
                slot = displayed ^ 1
            deadline += events[current][1].duration*FRAME
            current += 1
            state.update(queued=False, published=False, frame=None, ready=False, uploaded=0)
            if current == len(events):
                break
        event_id, event = events[current]
        plan = asset.plans[event.frame]
        stage_begin = clock.t
        if state["frame"] is None:
            clock.run_path(shell["steps"]["turnover_prefix"], "stage_turnover")
            stage_begin = clock.t
            resident = event.frame != 0 and event.frame in residents
            if resident:
                slot = residents.index(event.frame)
            elif event.frame:
                if slot == displayed:
                    raise ModelError("Attempt to overwrite displayed animation slot")
                residents[slot] = -1
            state.update(frame=event.frame, slot=slot)
            clock.work(costs["event_t"][event_id][slot]["resident" if resident else "new"], "stage_build")
            clock.run_path(shell["steps"]["turnover_suffix"], "stage_turnover")
            state["ready"] = resident or not plan.sources
            if state["ready"] and event.frame:
                residents[slot] = event.frame
        else:
            clock.run_path(shell["steps"]["pending_prepare" if state["queued"] else "waiting_prepare"],
                           "stage_turnover")
        producer_begin = clock.t
        action = actions[action_index] if action_index < len(actions) else 0
        read_extra = schedule_extra[action_index] if action_index < len(schedule_extra) else 0
        action_index += 1
        calls += 1
        clock.work(costs["idle_service_t"]+read_extra+profile.service_extra_t, "producer_envelope")
        if action == 1 and chunk < len(costs["decode"]):
            clock.work(costs["decode"][chunk]["service_t"], "dictionary_decode")
            loaded += costs["decode"][chunk]["tiles"]
            chunk += 1
        elif action == 3 and not state["ready"]:
            start = state["uploaded"]
            available = 0
            for source in plan.sources[start:start+20]:
                if source >= loaded:
                    break
                available += 1
            if available:
                full = min(20, len(plan.sources)-start)
                termination = "not_ready" if available < full else (
                    "stage_end" if start+available == len(plan.sources) else "upload_cap")
                gather = costs["gather_paths_t"][termination][available]
                clock.work(gather, "tile_gather")
                clock.hdma(available)
                state["uploaded"] += available
                if state["uploaded"] == len(plan.sources):
                    state["ready"] = True
                    residents[slot] = event.frame
        recent_calls.append({"event": current+1, "frame": event.frame, "action": action,
                             "stage_begin_t": stage_begin, "producer_begin_t": producer_begin,
                             "producer_done_t": clock.t, "uploaded": state["uploaded"]})
        recent_calls = recent_calls[-5:]
        if not state["ready"] and not state["queued"]:
            clock.run_path(shell["steps"]["deadline_prefix"], "owner_return")
            due = clock.deadline_due(shell["deadline_steps"], deadline)
            if due:
                clock.run_path(shell["steps"]["underflow_after_deadline"], "underflow_trace")
                state["miss"] = {"event": current, "frame": event.frame, "deadline_t": deadline,
                                 "observed_t": clock.t, "loaded": loaded, "uploaded": state["uploaded"],
                                 "required_uploads": len(plan.sources), "ready": False, "queued": False,
                                 "action_index": action_index, "reason": "stage_not_ready"}
            else:
                clock.run_path(shell["steps"]["waiting_after_deadline"], "owner_return")
        elif state["ready"] and not state["queued"]:
            clock.run_path(shell["steps"]["queue_prefix"], "owner_return")
            clock.work(costs["queue_t"][event.frame][slot], "map_queue")
            state["queued"] = True
            clock.run_path(shell["steps"]["queue_suffix"], "owner_return")
        else:
            clock.run_path(shell["steps"]["pending_commit"], "owner_return")
        recent_calls[-1]["frame_wait_t"] = None if state["miss"] else clock.t
        if state["miss"]:
            break
        clock.delay_frame(shell["delay"])
    if not state["miss"]:
        # Preserve the authored final hold. No silent timeline stretching.
        while clock.t < authored_end or (clock.remaining and clock.audio_underrun is None):
            clock.instruction(8, "delay_glue")
            clock.run_path(["arm"], "delay_glue")
            clock.delay_frame(shell["delay"])
            if clock.t > max(authored_end, asset.sample_blocks*profile.audio_period_t)+4*FRAME:
                break
    return {"species": asset.name, "path": path, "initial_ly": initial_ly,
            "audio": "sampled" if asset.sample_blocks and audio_enabled else "synth_or_disabled",
            "startup_loaded_tiles": initial_target, "startup_actual_loaded_tiles": startup_loaded,
            "startup_cpu_component_t": prime_cpu,
            "startup_exclusions": ["UI/transition/basepic upload", "HDMA wait", "cry arm/prefill", "interrupts"],
            "authored_intervals": authored_end//FRAME, "producer_calls": calls,
            "elapsed_t": clock.t, "animation_miss": state["miss"],
            "audio_underrun_t": clock.audio_underrun, "audio_min_cache": clock.min_cache,
            "publishes": publishes, "operations": clock.events, "time_accounting": clock.totals,
            "interrupts": clock.irq_counts,
            "recent_calls": recent_calls,
            "status": "MODEL_MISS" if state["miss"] or clock.audio_underrun is not None or
                       any(p.get("late_intervals", 0) for p in publishes) else "UNVALIDATED_NO_MISS",
            "unknown_costs": profile.unknown,
            "limits": ["bounded loop/phase coverage", "no calibrated end-to-end startup timing",
                       "instruction counts are not an independently validated SM83 emulator",
                       "final stop/base-map cleanup is outside measured animation events",
                       "synth sound-driver cost is part of the unspecified VBlank envelope"]}
