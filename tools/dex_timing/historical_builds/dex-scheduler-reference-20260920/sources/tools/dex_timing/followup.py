"""Five-stop owner-loop comparison, retaining timer and scanline uncertainty."""

from dataclasses import asdict, replace
import re

from .assets import sha256
from .costs import machine, run_to
from .cpu import ModelError
from .model import Profile, FRAME, LINE, CPU_HZ, simulate
from .replay import OwnerReplay, captured_state_differences, matching_div_phases


STOPS = ("Publication", "Stage Entry", "Producer Entry", "Frame Wait", "First Miss")


def read_debugger_clock(section):
    """Read a normal-speed SameBoy counter without treating the reset as elapsed time."""
    match = re.search(r"(?m)^ticks( keep)?:\s*\nT-cycles: (\d+)\s*\nM-cycles: (\d+)\s*\nAbsolute 8MHz ticks: (\d+)", section)
    if not match:
        return None
    keep, t, m, absolute = match.groups()
    t, m, absolute = int(t), int(m), int(absolute)
    if absolute != 2*t or m != t//4:
        raise ModelError("Debugger clocks disagree or capture is not normal speed")
    if not keep and "Tick count reset." not in section[match.end():]:
        raise ModelError("Initial debugger clock must report a reset")
    return {"keep": bool(keep), "t_cycles": t, "absolute_8mhz_ticks": absolute}


def read_stops(text, symbols):
    result = []
    for section in text.replace("&#x20;", " ").split("-----"):
        if "registers:" not in section:
            continue
        label = section.strip().splitlines()[0].rstrip(":")
        memory = {}
        for bank, address, values in re.findall(
                r"(?im)^\s*([\da-f]{2}):([\da-f]{4}):\s+((?:[\da-f]{2}(?:[ \t]+|$))+)", section):
            for i, value in enumerate(values.split()):
                memory[int(bank, 16), int(address, 16)+i] = int(value, 16)
        regs = {int(a, 16): int(v, 16) for a, v in re.findall(
            r"(?i)print/x \[\$([\da-f]+)\]:\s*=\$([\da-f]+)", section)}
        cpu_regs = {name.upper(): int(value, 16) for name, value in re.findall(
            r"(?im)^\s*(AF|BC|DE|HL|SP|PC)\s*=\s*\$([\da-f]+)", section)}
        source_label = label
        if label == "Frame Miss":
            miss_pc = symbols.get("Pokedex_CountAnimationUnderflow", (None, None))[1]
            if miss_pc is None or cpu_regs.get("PC") != miss_pc:
                raise ModelError("Frame Miss alias must stop at the linked underrun breakpoint")
            label = "First Miss"

        def word(name, bank=0):
            address = symbols[name][1]
            return memory[bank, address] + 256*memory[bank, address+1]

        try:
            ly, stat = regs[0xff44], regs[0xff41]
            if regs[0xffff] != 15 or memory[0, 0xff06] != 56 or memory[0, 0xff07] & 7 != 6:
                raise ModelError("Five-stop comparison requires IE $0f and the normal-pitch sample timer")
            result.append({"label": label, "source_label": source_label,
                           "debugger_clock": read_debugger_clock(section),
                           "counter": regs[symbols["hVBlankCounter"][1]],
                           "ly": ly, "stat": stat, "physical_line": 153 if ly == 0 and stat & 3 == 1 else ly,
                           "div": memory[0, 0xff04], "tima": memory[0, 0xff05],
                           "cache": memory[4, symbols["wSampledCryCacheCount"][1]],
                           "remaining": word("hSampledCryBlocks"),
                           "compressed": word("wSampledCryCompressedBlocks", 4),
                           "read_address": word("hSampledCryAddress"),
                           "write_address": word("wSampledCryCacheWriteAddress", 4),
                           "source_address": word("wSampledCryCompressedAddress", 4),
                           "capture": {"memory": [[b, a, v] for (b, a), v in sorted(memory.items())],
                                       "hardware": {str(a): v for a, v in regs.items()},
                                       "registers": cpu_regs}})
        except KeyError as error:
            raise ModelError(f"Incomplete hardware/audio capture at {label}: {error}") from error
    if tuple(r["label"] for r in result) != STOPS:
        raise ModelError("Expected Publication -> Stage Entry -> Producer Entry -> Frame Wait -> First Miss")
    clocks = [s["debugger_clock"] for s in result]
    if any(clocks) and (not all(clocks) or clocks[0]["keep"] or not all(c["keep"] for c in clocks[1:])):
        raise ModelError("Exact timing requires an initial ticks reset and ticks keep at all four later stops")
    return result


def observed_legs(stops):
    origin = (stops[0]["counter"]+1) & 255  # Counter increments after this first VBlank stop.
    positions = [((s["counter"]-origin) & 255)*FRAME + ((s["physical_line"]-144) % 154)*LINE
                 for s in stops]
    positions[0] = ((stops[0]["physical_line"]-144) % 154)*LINE
    result = []
    for i, (a, b) in enumerate(zip(stops, stops[1:])):
        line_t = positions[i+1]-positions[i]
        candidates = []
        for ticks in range((b["tima"]-a["tima"]) % 200, (line_t+LINE)//64+2, 200):
            t = ticks*64
            # DIV gives a second, independent clock modulo 65536 T.
            div_error = (t-((b["div"]-a["div"]) & 255)*256+32768) % 65536-32768
            if abs(t-line_t) <= LINE+62 and abs(div_error) <= 318:
                candidates.append(t)
        if len(candidates) != 1:
            raise ModelError("Ambiguous/inconsistent DIV, TIMA and scanline interval")
        t = candidates[0]
        result.append({"from": a["label"], "to": b["label"], "nominal_t": t,
                       "min_t": max(0, t-63), "max_t": t+63,
                       "blocks_consumed": a["remaining"]-b["remaining"],
                       "blocks_decoded": a["compressed"]-b["compressed"]})
        if a.get("debugger_clock"):
            start = a["debugger_clock"]["t_cycles"] if i else 0
            exact = b["debugger_clock"]["t_cycles"]-start
            if not max(0, t-63) <= exact <= t+63:
                raise ModelError("Exact debugger interval disagrees with DIV/TIMA bounds")
            result[-1].update(timer_nominal_t=t, nominal_t=exact, min_t=exact, max_t=exact,
                              measurement="debugger_cycles")
    return result


def compare_followup(repo, report, path, species):
    for key in ("rom_sha256", "sym_sha256"):
        if report["manifest"][key] != repo.hashes[key]:
            raise ModelError("Follow-up report and linked build differ")
    asset = repo.load([species])[0]
    if len(asset.events) < 2:
        raise ModelError("This focused replay requires at least two events")
    costs = next(e["costs"] for e in report["entries"] if e["asset"]["name"] == species)
    stops = read_stops(path.read_text(), repo.symbols)
    legs = observed_legs(stops)
    shared = report["shared_costs"]
    # Count from the same LY read used by the outer VBlank fixture to the
    # captured PC. Do not substitute a fitted startup delay.
    cpu = machine(repo)
    cpu.record_writes = True
    cpu.field("wPokedexAnimFlags", 0x2f)
    cpu.field("wPokedexAnimDeadline", 1)
    cpu.ram[0xff44] = 145
    run_to(cpu, "Pokedex_VBlankAnimationFrontpicMap", "Pokedex_VBlankAnimationFrontpicMap.deadline_reached")
    ly_read = next(t for t, address, _ in cpu.io_reads if address == 0xff44)
    prefix = shared["publication"]["vblank"]["publish_check_t"]+cpu.cycles-ly_read
    if not 144 <= stops[0]["ly"] < 146 or stops[0]["remaining"] > asset.sample_blocks:
        raise ModelError("Follow-up must begin at the first normal publication")
    played = asset.sample_blocks-stops[0]["remaining"]
    if stops[0]["cache"] != 32-played or stops[0]["compressed"] != asset.sample_blocks-32:
        raise ModelError("Follow-up has a refill before publication; this initial fixture does not cover it")
    # Include a timer request already pending at publication. TIMA and DIV
    # constrain one phase for the entire replay, not separate offsets per leg.
    phases = [phase for phase in range(4, 12801, 4)
              if matching_div_phases([{"t": prefix}], stops[:1], phase)]
    profile = Profile(**dict(report["profile"], audio_played_at_publication=played))
    trials = []
    for phase in phases if species == "weavile" else []:
        for variant in range(8):
            run = simulate(asset, costs, **shared, profile=replace(profile, audio_phase_t=phase, owner_variant=variant))
            miss = run["animation_miss"]
            same = bool(miss and miss["event"] == 1 and miss["frame"] == asset.events[1].frame and
                        miss["uploaded"] == 0 and miss["deadline_t"] == asset.events[0].duration*FRAME)
            times = None
            if same:
                call = run["recent_calls"][0]
                if call["frame_wait_t"] is not None:
                    times = [prefix, call["stage_begin_t"], call["producer_begin_t"],
                             call["frame_wait_t"], miss["observed_t"]]
            elapsed = [b-a for a, b in zip(times, times[1:])] if times else None
            trials.append({"phase_t": phase, "owner_variant": variant, "same_first_miss": same,
                           "elapsed_t": elapsed, "all_legs_inside_timer_bounds": bool(elapsed and
                               all(l["min_t"] <= t <= l["max_t"] for l, t in zip(legs, elapsed)))})
    for i, leg in enumerate(legs):
        values = [t["elapsed_t"][i] for t in trials if t["elapsed_t"]]
        leg["predicted_min_t"] = min(values) if values else None
        leg["predicted_max_t"] = max(values) if values else None
    linked = compare_linked_replay(repo, asset, stops, profile, prefix, phases, legs)
    return {"status": "PARTIAL_NOT_CALIBRATED", "capture_sha256": sha256(path.read_bytes()),
            "rom_sha256": repo.hashes["rom_sha256"], "species": species,
            "profile": asdict(profile), "publication_prefix_t": prefix,
            "stops": stops, "legs": legs, "trials": trials, "linked_replay": linked,
            "limits": ["The aggregate first-turn comparison remains Weavile-only; other supported species use the linked replay",
                       "Captured timer phase is bounded, not measured to a CPU cycle",
                       "Constant HBlank profile is not a reconstruction of per-line PPU behavior",
                       "Timer/refill use conservative fixtures, not exact cache-address paths",
                       "Stage/producer instructions still use aggregate IRQ timing",
                       "The first undelayed publication origin is a fixture, not a measured IRQ-entry timestamp",
                       "Agreement of separate leg ranges does not imply one jointly matching replay"]}


def captured_trace_differences(repo, points, stops):
    base = repo.symbols["wPokedexAnimDebug"][1]
    differences = []
    for point, stop in zip(points, stops):
        memory = {(b, a): v for b, a, v in stop["capture"]["memory"]}
        differences.append({"stop": stop["label"], "bytes": [
            {"address": base+i, "captured": memory[0, base+i], "modeled": value}
            for i, value in enumerate(point["trace"]) if value != memory[0, base+i]]})
    return differences


def compare_linked_replay(repo, asset, stops, profile, prefix, phases, legs):
    trials, example, closest, diagnostic = [], None, None, None
    best_trace_count, closest_rank, diagnostic_rank = float("inf"), None, None
    memory = {(b, a): v for b, a, v in stops[0]["capture"]["memory"]}
    known_owner = all(repo.symbols[name] in memory for name in (
        "wDexArrowCursorBlinkCounter", "wTextDelayFrames", "wDexArrowCursorDelayCounter"))
    variants = [0] if known_owner else range(8)
    for phase in phases:
        for div_low in matching_div_phases([{"t": prefix}], stops[:1], phase):
            for variant in variants:
                run = OwnerReplay(repo, asset, stops,
                                  replace(profile, audio_phase_t=phase, owner_variant=variant), prefix, div_low).run()
                timer_match = div_low in matching_div_phases(run["points"], stops, phase)
                state_diffs = captured_state_differences(repo, run["points"], stops)
                state_match = not state_diffs
                intervals_match = all(leg["min_t"] <= t <= leg["max_t"]
                                      for leg, t in zip(legs, run["elapsed_t"]))
                match = bool(timer_match and state_match and intervals_match)
                trace_count = sum(len(stop["bytes"]) for stop in captured_trace_differences(repo, run["points"], stops))
                trial = {"phase_t": phase, "owner_variant": variant, "elapsed_t": run["elapsed_t"],
                         "state_match": state_match, "timer_match": timer_match,
                         "intervals_match": intervals_match, "joint_match": match,
                         "trace_difference_count": trace_count, "joint_trace_match": match and not trace_count,
                         "initial_div_low": div_low}
                trials.append(trial)
                candidate = dict(run, **{k: trial[k] for k in (
                    "phase_t", "owner_variant", "initial_div_low", "timer_match", "intervals_match")})
                if match and trace_count < best_trace_count:
                    example = candidate
                    best_trace_count = trace_count
                if timer_match and intervals_match:
                    rank = (sum(len(stop["fields"]) for stop in state_diffs), trace_count,
                            sum(abs(t-leg["nominal_t"]) for leg, t in zip(legs, run["elapsed_t"])))
                    if closest_rank is None or rank < closest_rank:
                        closest_rank = rank
                        closest = candidate
                rank = (sum(abs(t-leg["nominal_t"]) for leg, t in zip(legs, run["elapsed_t"])),
                        sum(len(stop["fields"]) for stop in state_diffs), trace_count)
                if diagnostic_rank is None or rank < diagnostic_rank:
                    diagnostic_rank = rank
                    diagnostic = candidate
    selected = example or closest or diagnostic
    return {"status": "CAPTURE_CONSISTENT" if example else "RESIDUAL_MISMATCH",
            "trials": trials, "example": example, "closest": closest if not example else None,
            "diagnostic": diagnostic if not example and not closest else None,
            "state_differences": captured_state_differences(repo, selected["points"], stops) if selected else [],
            "trace_differences": captured_trace_differences(repo, selected["points"], stops) if selected else [],
            "owner_state": "captured" if known_owner else "eight fixture variants",
            "limits": ["Supported first-publication through first-miss cases only, not full animation coverage",
                       "One capture-seeded memory state; later stops are comparisons, not re-seeding points",
                       "No-input owner fixture and fixed HBlank profile, not captured per-line pixels",
                       "DMA uses 32 T per tile with actual linked polling; sub-instruction bus arbitration is not emulated",
                       "Map and tile pixel contents at initial publication are not captured or certified",
                       "Linked CPU and IRQ execution share the instruction counter, not an independent emulator",
                       "Unknown DIV low byte and timer/owner phase are swept, not measured",
                       "The bulk all-species model retains conservative/aggregate component fixtures"]}


def render_followup(result):
    ms = lambda t: f"{t/CPU_HZ*1000:.3f}"
    lines = ["# Owner-Loop Follow-Up", "", "**PARTIAL_NOT_CALIBRATED**", "",
             f"Species: {result['species']}; HBlank start: dot {result['profile']['hblank_dot']}.",
             f"ROM SHA-256: `{result['rom_sha256']}`", "",
             "Only host code changed. Interval bounds below use the captured DIV/TIMA plus scanline/counter readings."]
    trials = result["trials"]
    if trials:
        lines += ["", "## Aggregate First-Turn Comparison", "",
                  "| Interval | Captured ms (+/- 0.015 ms) | Predicted range ms |", "|---|---:|---:|"]
        for leg in result["legs"]:
            predicted = (f"{ms(leg['predicted_min_t'])}-{ms(leg['predicted_max_t'])}"
                         if leg["predicted_min_t"] is not None else "no matching first miss")
            lines.append(f"| {leg['from']} -> {leg['to']} | {ms(leg['nominal_t'])} | {predicted} |")
        lines += ["", f"Matching first-miss states: {sum(t['same_first_miss'] for t in trials)}/{len(trials)}.",
                  f"Single replays inside all four timer bounds: {sum(t['all_legs_inside_timer_bounds'] for t in trials)}/{len(trials)}.",
                  "These are finite phase/owner-state samples, not probabilities or a proof."]
        lines += [f"- {limit}." for limit in result["limits"]]
    linked = result["linked_replay"]
    matched = sum(t["joint_match"] for t in linked["trials"])
    lines += ["", "## Capture-Seeded Linked Replay", "", f"**{linked['status']}**", "",
              f"Joint state/timer matches: {matched}/{len(linked['trials'])} sampled initial states.",
              f"Also matching all captured trace bytes: {sum(t['joint_trace_match'] for t in linked['trials'])}/{len(linked['trials'])}.",
              f"Initial owner state: {linked['owner_state']}.",
              "This supplementary replay executes the actual linked owner, stage, producer, upload polling, refill and interrupt instructions.",
              "It compares every stop's enabled IF bits, LY/mode, display counter, all 27 animation-state bytes, audio counts, and both timer readings.",
              "The captured later states do not drive the replay. One initial state runs through all five stops."]
    if linked["example"] or linked["closest"] or linked["diagnostic"]:
        example = linked["example"] or linked["closest"] or linked["diagnostic"]
        if not linked["example"]:
            description = ("The following is the closest state comparison among timer-compatible candidates, NOT a passing replay."
                           if linked["closest"] else
                           "No jointly timer/interval-compatible candidate was found. The following is the nearest elapsed-time diagnostic candidate, NOT a passing replay.")
            lines += ["", description]
            for stop in linked["state_differences"]:
                for field in stop["fields"]:
                    lines.append(f"- {stop['stop']}, {field['field']}: captured {field['captured']}, modeled {field['modeled']}.")
        lines += ["", "| Interval | Captured nominal T | Linked replay T | Difference T |",
                  "|---|---:|---:|---:|"]
        for leg, t in zip(result["legs"], example["elapsed_t"]):
            lines.append(f"| {leg['from']} -> {leg['to']} | {leg['nominal_t']} | {t} | {t-leg['nominal_t']:+d} |")
        exact = all(leg.get("measurement") == "debugger_cycles" for leg in result["legs"])
        timing_note = ("All four differences fall within the timer's +/-63 T observation uncertainty."
                       if example["intervals_match"] else
                       "One or more intervals exceed the timer's +/-63 T observation uncertainty; these differences remain unexplained.")
        if exact:
            timing_note = ("All four intervals match the exact debugger cycle counts." if example["intervals_match"] else
                           "One or more intervals differ from the exact debugger cycle counts; these differences remain unexplained.")
        lines += ["", timing_note,
                  f"One initial phase matches every DIV/TIMA pair: {example['timer_match']}.",
                  f"Example initial phase: {example['phase_t']} T; owner variant {example['owner_variant']}; initial DIV low byte: {example['initial_div_low']}.",
                  f"Only the initial decoded dictionary prefix is seeded: {example['initial_dictionary_tiles']} tiles.",
                  f"Executed interrupt costs, T (including entry/vector): {example['irq_costs_t']}."]
        differences = [item for stop in linked["trace_differences"] for item in stop["bytes"]]
        lines += ["", f"Additional 139-byte trace comparison: {len(differences)} differing byte observations across all five stops."]
        if differences:
            lines.append("Trace equality is an additional check beyond the core-state/timer verdict; do not call this byte-identical replay.")
        for stop in linked["trace_differences"]:
            if stop["bytes"]:
                values = ", ".join(f"${d['address']:04x}: ${d['captured']:02x} -> ${d['modeled']:02x}" for d in stop["bytes"])
                lines.append(f"- {stop['stop']} (captured -> modeled): {values}.")
        lines += ["", "## Modeled Work Sequence", "",
                  "Intervening events below are predictions from the selected replay, not additional captured breakpoints.",
                  "Interval zero is the first publication VBlank. Queueing and actual publication are distinct.", "",
                  "| Event | Frame | Operation | Hardware interval | LY | Uploaded / stage tiles |",
                  "|---|---:|---|---:|---:|---:|"]
        for point in example["observations"]:
            if point["kind"] == "Pokedex_RecordAnimationTrace":
                operation = {0x80: "stage prepared", 0x81: "map queued", 0x82: "deadline miss"}.get(point["trace"][25])
            else:
                operation = {"Pokedex_VBlankAnimationFrontpicMap.deadline_reached": "publication",
                             "HDMATransfer_Exact_NoDI_Arbitrary": "upload helper entry",
                             "HDMATransfer_Exact_NoDI_Arbitrary.wait": "upload armed"}.get(point["kind"])
            if operation:
                anim, trace = point["anim"], point["trace"]
                lines.append(f"| {trace[5]} | {anim[6]} | {operation} | {point['t']//FRAME} | {point['ly']} | {anim[9]} / {anim[5]} |")
    conclusion = ("This is consistency with this capture, not exact-cycle hardware calibration or a deadline guarantee."
                  if linked["example"] else
                  "Residuals remain: this comparison does not certify capture agreement, exact hardware timing, or deadlines.")
    lines += ["", conclusion, ""]
    lines += [f"- {limit}." for limit in linked["limits"]]
    return "\n".join(lines)+"\n"
