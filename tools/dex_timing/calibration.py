"""Compare scanline-resolution observations without fitting workload constants."""

from functools import lru_cache
from pathlib import Path

from .assets import sha256
from .costs import upload_trace_benchmark
from .cpu import ModelError
from .model import Clock, Profile, LINE, FRAME, CPU_HZ, simulate
from .traces import read_captures


def component_envelope(cpu_costs, ly, audio, vblank_t, lcd=True, hdma_tiles=0):
    """A declared finite phase sweep, NOT a continuous conservative proof.

    Start/end LY readings lack dot and timer phase. Sweep three dot positions,
    every 64-T timer phase, and both HBlank-start extremes. Each case starts
    mainline with no pending interrupt; no hidden initial work is invented.
    """
    elapsed = []
    for hblank in (252, 369):
        for dot in (0, 228, 455):
            for timer in range(64, 12801, 64):
                for cpu_t in set(cpu_costs):
                    p = Profile(hblank_dot=hblank, lcd_stat_enabled=lcd, vblank_other_t=vblank_t)
                    c = Clock(p, audio, 1000)
                    c.t = ((ly-144) % 154)*LINE+dot
                    c.next_timer = c.t+timer
                    c.next_lcd = c.t-c.dot+hblank if ly < 144 else 10*LINE+hblank
                    if c.next_lcd < c.t:
                        c.next_lcd += LINE if ly != 143 else 11*LINE
                    if not lcd:
                        c.next_lcd = float("inf")
                    begin = c.t
                    c.work(cpu_t)
                    if hdma_tiles:
                        c.hdma(hdma_tiles)
                    elapsed.append(c.t-begin)
    return {"min_t": min(elapsed), "max_t": max(elapsed), "cases": len(elapsed)}


def compare(repo, report, baseline, specifications, hblank_dots=None):
    for key in ("rom_sha256", "sym_sha256"):
        if report["manifest"][key] != repo.hashes[key] or baseline["manifest"][key] != repo.hashes[key]:
            raise ModelError("Comparison requires reports and captures from the same linked build")
    names = sorted({item.split("=", 1)[0] for item in specifications})
    assets = {a.name: a for a in repo.load(names)}
    entries = {e["asset"]["name"]: e for e in report["entries"]}
    previous = {e["asset"]["name"]: e for e in baseline["entries"]}
    components, captures = [], []
    audio = report["shared_costs"]["audio"]

    @lru_cache(None)
    def envelope(cpu_costs, ly, version, tiles):
        source = baseline if version == "before" else report
        shared = source["shared_costs"]
        lcd = source["profile"].get("lcd_stat_enabled", False)
        vblank = shared["publication"].get("vblank", {}).get("idle_t", 0)
        return component_envelope(cpu_costs, ly, shared["audio"], vblank, lcd, tiles)

    @lru_cache(None)
    def upload(name, frame, slot, start, reload):
        return upload_trace_benchmark(repo, assets[name], frame, slot, start, reload)

    def add_component(name, path, attempt, record, kind, cpu_costs, stamps, tiles=0):
        measured = record["phases"][kind]
        if not measured["nominal_t"]:
            return
        dma = tiles if kind == "hdma" else 0
        old = envelope(tuple(cpu_costs), stamps[0][1], "before", dma)
        new = envelope(tuple(cpu_costs), stamps[0][1], "after", dma)
        components.append({"species": name, "file": str(path), "snapshot": attempt,
                           "event": record["event"], "frame": record["frame"], "operation": kind,
                           "tiles": tiles, "start": stamps[0], "end": stamps[1],
                           "cpu_costs_t": sorted(set(cpu_costs)), "observed": measured,
                           "before": old, "after": new,
                           "overlaps_after": new["max_t"] >= measured["min_t"] and
                                             new["min_t"] <= measured["max_t"]})

    for spec in specifications:
        name, filename = spec.split("=", 1)
        path = Path(filename)
        text = path.read_text()
        raw = read_captures(text)
        asset, costs = assets[name], entries[name]["costs"]
        seen_snapshots, seen_records = set(), set()
        unique = []
        for attempt, capture in enumerate(raw, 1):
            signature = repr(capture)
            if signature in seen_snapshots:
                continue
            seen_snapshots.add(signature)
            unique.append(capture)
            for record in capture["records"]:
                signature = repr(record)
                if signature in seen_records:
                    continue
                seen_records.add(signature)
                event = record["event"]-1
                frame, stamps = record["frame"], record["timestamps"]
                if record["action"] == 0x80:
                    cpu_costs = [slot["new"] for slot in costs["event_trace_t"][event]]
                    add_component(name, path, attempt, record, "stage", cpu_costs, stamps[:2])
                elif record["action"] < 128 and record["action"] & 2:
                    if record["loaded_tiles"] != asset.total:
                        raise ModelError("Calibration upload fixture requires a complete dictionary")
                    end = record["upload_offset"]
                    if not end:
                        continue
                    start = (end-1)//20*20
                    fixtures = [upload(name, frame, slot, start, reload)
                                for slot in (0, 1) for reload in (False, True)]
                    add_component(name, path, attempt, record, "gather",
                                  [v["gather_trace_t"] for v in fixtures], stamps[2:4], end-start)
                    add_component(name, path, attempt, record, "hdma",
                                  [v["hdma_entry_to_helper_t"] for v in fixtures], stamps[4:6], end-start)
        first = next(r for r in unique[0]["records"] if r["action"] == 0x82)
        captures.append({"species": name, "file": str(path), "sha256": sha256(path.read_bytes()),
                         "raw_snapshots": len(raw), "distinct_snapshots": len(unique),
                         "first_miss": {"event": first["event"], "frame": first["frame"],
                                        "deadline": (first["deadline"]-unique[0]["start_tick"]) & 255,
                                        "loaded": first["loaded_tiles"], "uploaded": first["upload_offset"]}})
    scenarios = {}
    phase_sweep = {}
    for name in names:
        scenarios[name] = {}
        for label, source in (("before", previous), ("after", entries)):
            scenarios[name][label] = [{"initial_ly": r["initial_ly"], "first_miss": r["animation_miss"],
                                      "late_publications": [p for p in r["publishes"] if p.get("late_intervals", 0)],
                                      "recent_calls": r.get("recent_calls", [])}
                                     for r in source[name]["runs"] if r["path"] == "cold" and r["audio"] == "sampled"]
        observations = [c["first_miss"] for c in captures if c["species"] == name]
        if any(c != observations[0] for c in observations):
            raise ModelError("Phase summary requires a repeatable first-miss state")
        expected = observations[0]
        cases = []
        for hblank in hblank_dots or [report["profile"]["hblank_dot"]]:
            for phase in range(64, 12801, 64):
                profile = Profile(**dict(report["profile"], audio_phase_t=phase, hblank_dot=hblank))
                run = simulate(assets[name], entries[name]["costs"], audio, report["shared_costs"]["publication"],
                               profile, initial_ly=144, path="cold")
                miss = run["animation_miss"]
                matches = bool(miss and miss["event"]+1 == expected["event"] and
                               miss["frame"] == expected["frame"] and miss["uploaded"] == expected["uploaded"] and
                               miss["loaded"] == expected["loaded"] and miss["deadline_t"]//FRAME == expected["deadline"])
                cases.append({"audio_phase_t": phase, "hblank_dot": hblank, "first_miss": miss,
                              "matches_first_state": matches, "recent_calls": run["recent_calls"]})
        phase_sweep[name] = cases
    return {"status": "PARTIAL_NOT_CALIBRATED", "rom_sha256": repo.hashes["rom_sha256"],
            "captures": captures, "components": components, "scenarios": scenarios, "timer_phase_sweep": phase_sweep,
            "scenario_profiles": {"before": baseline["profile"], "after": report["profile"]},
            "assumptions": ["IE $0f, STAT mode-0 enabled, hLCDCPointer zero, normal CPU speed",
                            "new-stage construction; both slots swept, no resident fast path",
                            "complete dictionaries; gather schedule-run reload and continuation both swept",
                            "three dot positions and 200 timer phases, not an exhaustive continuous bound",
                            "HDMA component stops at helper return; small outer return path is unmodeled",
                            "idle VBlank fixture applies; no palette/tile requests or active synth music",
                            "component envelopes are independent, not one reconstructed IRQ history",
                            "end-to-end entry phase is not established by a late first-miss dump"]}


def render_comparison(result):
    def ms(t):
        return f"{t/CPU_HZ*1000:.3f}"

    lines = ["# Host-Model Capture Comparison", "", "**Status: PARTIAL, NOT CALIBRATED.**", "",
             f"ROM SHA-256: `{result['rom_sha256']}`", "",
             "The game/ROM was not changed. These are host-only corrections and phase experiments.", "",
             "## First Misses in SameBoy", "",
             "| Capture | Event | Frame | Deadline | Uploaded |",
             "|---|---:|---:|---:|---:|"]
    for capture in result["captures"]:
        m = capture["first_miss"]
        lines.append(f"| {Path(capture['file']).name} | {m['event']} | {m['frame']} | +{m['deadline']} | {m['uploaded']} |")
    lines += ["", "## Component Comparison", "",
              "Ranges are independently swept dot/timer/HBlank phases, not an exact replay or proof. Observations have +/- one scanline uncertainty (~0.109 ms).", "",
              "| Species / operation | Samples | Observed ms | Before ms | Corrected ms | Overlap |",
              "|---|---:|---:|---:|---:|---:|"]
    groups = {}
    for c in result["components"]:
        key = c["species"], c["operation"], c["frame"] if c["operation"] == "stage" else c["tiles"]
        groups.setdefault(key, []).append(c)
    for (name, op, detail), items in sorted(groups.items()):
        ranges = []
        for label in ("observed", "before", "after"):
            lo = min(c[label]["nominal_t" if label == "observed" else "min_t"] for c in items)
            hi = max(c[label]["nominal_t" if label == "observed" else "max_t"] for c in items)
            ranges.append(f"{ms(lo)}-{ms(hi)}")
        suffix = f"frame {detail}" if op == "stage" else f"{detail} tiles" if detail else ""
        lines.append(f"| {name} {op} {suffix} | {len(items)} | {' | '.join(ranges)} | {sum(c['overlaps_after'] for c in items)}/{len(items)} |")
    lines += ["", "## Full-Replay First Misses", "",
              "These remain phase experiments. Do not choose a phase just because it matches a failure.", "",
              "| Species / model | Initial LY | First event | Frame | Uploaded / required | Deadline |",
              "|---|---:|---:|---:|---:|---:|"]
    for name, scenarios in result["scenarios"].items():
        for version, rows in scenarios.items():
            for row in rows:
                m = row["first_miss"]
                values = f"{m['event']+1} | {m['frame']} | {m['uploaded']}/{m['required_uploads']} | +{m['deadline_t']//FRAME}" if m else "none | - | - | -"
                lines.append(f"| {name} {version} | {row['initial_ly']} | {values} |")
    profiles = result["scenario_profiles"]
    lines += ["", f"Report profiles: before HBlank dot {profiles['before']['hblank_dot']}; after dot {profiles['after']['hblank_dot']}.",
              "If these profiles differ, the report rows are not a single-change A/B. The explicit phase sweep below separates the PPU assumptions."]
    lines += ["", "## Remaining Limits", ""] + [f"- {s}." for s in result["assumptions"]]
    lines += ["", "## Initial Timer Phase Sensitivity", "",
              "Native cold path, initial LY 144; timer delays 64..12800 T in steps of 64, separately for each listed HBlank profile. No per-species workload is fitted. A matching state is not proof of the actual phase.", ""]
    for name, cases in result["timer_phase_sweep"].items():
        for hblank in sorted({c["hblank_dot"] for c in cases}):
            subset = [c for c in cases if c["hblank_dot"] == hblank]
            matches = sum(c["matches_first_state"] for c in subset)
            lines.append(f"- {name}, HBlank dot {hblank}: {matches}/{len(subset)} sampled phases reproduce the event/frame/deadline/loaded/uploaded first-miss state.")
    return "\n".join(lines)+"\n"
