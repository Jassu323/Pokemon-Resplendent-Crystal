"""One-capture diagnostic replay; not a runtime change or calibrated model."""

import copy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from dex_timing.assets import Repository, offset, sha256
from dex_timing.costs import machine, run_to
from dex_timing.model import Clock, Profile, LINE, FRAME, CPU_HZ, simulate


def captures(path):
    result = []
    for section in path.read_text().split("-----"):
        if "registers:" not in section:
            continue
        memory = {}
        for bank, address, values in re.findall(
                r"(?m)^([0-9a-f]{2}):([0-9a-f]{4}): ((?:[0-9a-f]{2}(?: |$))+)", section):
            for n, value in enumerate(values.split()):
                memory[int(bank, 16), int(address, 16) + n] = int(value, 16)
        regs = {int(a, 16): int(v, 16) for a, v in re.findall(
            r"print/x \[\$(\w+)\]:\s*=\$(\w+)", section)}
        result.append({"label": section.strip().splitlines()[0].rstrip(":"),
                       "memory": memory, "registers": regs})
    return result


def publication_prefix(repo):
    cpu = machine(repo)
    cpu.allowed_io.update([0xff00, 0xff04, 0xff40, 0xff42, 0xff43,
                           0xff46, 0xff4a, 0xff4b, *range(0xff51, 0xff56)])
    cpu.io_read_values[0xff00] = 15
    cpu.ram[0xff44] = 145
    for name, value in [("hSampledCryTimer", 1), ("wGameTimerPaused", 1),
                        ("wPokedexSelectedState", 1), ("hVBlank", 7),
                        ("wPokedexAnimFlags", 0x2f), ("hVBlankCounter", 0xaa),
                        ("wPokedexAnimDeadline", 0xab), ("wPokedexAnimStageFrameID", 1)]:
        cpu.field(name, value)
    start, end = offset(repo.symbols["OAMDMACode"]), offset(repo.symbols["OAMDMACode.End"])
    cpu.block(repo.symbols["hTransferShadowOAM"][1], repo.rom[start:end])
    cpu.symbols = dict(cpu.symbols, vector=(0, 0x40))
    return run_to(cpu, "vector", "Pokedex_VBlankAnimationFrontpicMap.deadline_reached") + 20


def owner_prefix(repo, clock, dynamic_stat, blink, text_delay, cursor_delay):
    cpu = machine(repo)
    cpu.allowed_io.add(0xff41)
    for name, value in [("hInMenu", 1), ("wJumptableIndex", 3),
                        ("wDexArrowCursorBlinkCounter", blink),
                        ("wTextDelayFrames", text_delay),
                        ("wDexArrowCursorDelayCounter", cursor_delay),
                        ("wPokedexAnimPlaybackState", 2), ("wPokedexAnimFlags", 0x4f),
                        ("wPokedexAnimStageFrameID", 1), ("wPokedexAnimDeadline", 0xab),
                        ("wPokedexAnimDisplaySlot", 0), ("wPokedexAnimStageSlot", 0)]:
        cpu.field(name, value)
    cpu.bank, cpu.pc = repo.symbols["Pokedex.main"]
    cpu.field("hROMBank", cpu.bank)
    cpu.push(0xffff)
    stop = repo.symbols["Pokedex_PrepareNextAnimationStage"]
    begin, polls, busy = clock.t, 0, 0
    while (cpu.bank, cpu.pc) != stop:
        if cpu.steps > 20000 or cpu.pc == 0xffff:
            raise RuntimeError("Owner fixture did not reach stage entry")
        clock._due()
        mode = 1 if clock.ly >= 144 else (2 if clock.dot < 80 else
                                          3 if clock.dot < clock.p.hblank_dot else 0)
        cpu.io_read_values[0xff41] = mode if dynamic_stat else 0
        cpu.field("hVBlankCounter", 0xab + clock.vblank_count)
        # Scope this fixture to the no-input owner. Interrupt register state is
        # preserved by the actual handlers; IRQ CPU costs remain aggregate.
        if cpu.read(cpu.pc) == 0xf0 and cpu.read(cpu.pc + 1) == 0x41:
            polls += 1
            busy += bool(mode & 2) if dynamic_stat else 0
        previous = cpu.cycles
        cpu.step()
        clock.work(cpu.cycles - previous, masked=True)
        clock._due()
    return {"begin_t": begin, "end_t": clock.t, "cpu_t": cpu.cycles,
            "polls": polls, "busy_polls": busy}


def main():
    source = Path("/Users/jakeadams/Downloads/Weavile Follow-Up Capture.txt")
    observations = captures(source)
    report = json.loads((ROOT / "build/dex-timing-lcd/report.json").read_text())
    repo = Repository(ROOT, ROOT / "pokecrystal.gbc", ROOT / "pokecrystal.sym")
    assert repo.hashes["rom_sha256"] == report["manifest"]["rom_sha256"]
    assert len(observations) == 5
    audio, publication = report["shared_costs"]["audio"], report["shared_costs"]["publication"]
    asset = repo.load(["weavile"])[0]
    costs = next(e["costs"] for e in report["entries"] if e["asset"]["name"] == "weavile")
    prefix = publication_prefix(repo)
    decoded = []
    for o in observations:
        m, r = o["memory"], o["registers"]
        physical = 153 if r[0xff44] == 0 and r[0xff41] & 3 == 1 else r[0xff44]
        decoded.append({"label": o["label"], "counter": r[0xff9b], "ly": r[0xff44],
                        "physical_line": physical, "stat": r[0xff41], "if": r[0xff0f],
                        "div": m[0, 0xff04], "tima": m[0, 0xff05],
                        "cache": m[4, 0xdff4],
                        "compressed": m[4, 0xdff5] + 256 * m[4, 0xdff6],
                        "remaining": m[0, 0xfff2] + 256 * m[0, 0xfff3]})
    # The first counter increments later in this publication ISR.
    positions = [((d["counter"] - 0xab) & 255) * FRAME +
                 ((d["physical_line"] - 144) % 154) * LINE for d in decoded]
    positions[0] = (decoded[0]["physical_line"] - 144) * LINE
    legs = []
    for i in range(4):
        a, b = decoded[i:i+2]
        line_t = positions[i+1] - positions[i]
        ticks = (b["tima"] - a["tima"]) % 200
        count = min(range(ticks, ticks + 3000, 200), key=lambda n: abs(n * 64 - line_t))
        legs.append({"from": a["label"], "to": b["label"], "scanline_nominal_t": line_t,
                     "timer_nominal_t": count * 64, "timer_quantization_t": 63,
                     "timer_nominal_ms": count * 64 / CPU_HZ * 1000,
                     "blocks_consumed": a["remaining"] - b["remaining"],
                     "blocks_decoded": a["compressed"] - b["compressed"]})
    # TIMA FE: overflow is 64..128 T away at the first stop (plus reload latency).
    # 600 T is measured from the linked publishing interrupt, not fit to a miss.
    # LY145 also allows a delayed IRQ entry. Include the rest of that scanline
    # and four T of reload uncertainty in this phase-only experiment.
    phase_runs = []
    for phase in range(prefix + 64, 2 * LINE + 128 + 5, 4):
        p = Profile(**dict(report["profile"], audio_phase_t=phase))
        run = simulate(asset, costs, audio, publication, p)
        phase_runs.append({"phase_t": phase, "miss": run["animation_miss"],
                           "calls": run["recent_calls"]})
    owner_trials = []
    for phase in (prefix + 64, prefix + 96, prefix + 128):
        for hb in (252, 300, 340, 369):
            p = Profile(**dict(report["profile"], audio_phase_t=phase, hblank_dot=hb))
            c = Clock(p, audio, asset.sample_blocks)
            c.t, c.remaining, c.cache, c.compressed = prefix, 201, 28, 173
            c.min_cache = 28
            c.on_vblank = lambda: publication["vblank"]["idle_t"]
            c.work(publication["vblank"]["publish_t"] + publication["gdma_t"] - prefix,
                   masked=True)
            c.work(56, "delay_return_to_refill")
            c.refill()
            c.work(28, "refill_return_to_owner")
            for dynamic in (False, True):
                for blink in (0, 8):
                    for text_delay in (0, 1):
                        for cursor_delay in (0, 1):
                            trial = copy.deepcopy(c)
                            result = owner_prefix(repo, trial, dynamic, blink, text_delay, cursor_delay)
                            owner_trials.append(dict(result, phase_t=phase, hblank_dot=hb,
                                                     dynamic_stat=dynamic, blink=blink,
                                                     text_delay=text_delay, cursor_delay=cursor_delay,
                                                     timer_irqs=trial.irq_counts["timer"]["delivered"]))
    result = {"status": "FOCUSED_DIAGNOSTIC_NOT_EXACT_CALIBRATION", "rom": repo.hashes,
              "capture_sha256": sha256(source.read_bytes()), "publication_prefix_t": prefix,
              "observations": decoded, "legs": legs, "phase_runs": phase_runs,
              "owner_trials": owner_trials,
              "limits": ["Timer bounds retain reload/sub-instruction uncertainty",
                         "Phase-only sweep does not reconstruct a delayed initial VBlank handler",
                         "Constant HBlank lengths are an envelope, not a reconstructed per-line PPU",
                         "Owner fixture clock executes IRQ costs but not their memory effects",
                         "Audio refill remains the existing upper fixture, not exact Weavile cache state"]}
    target = ROOT / "build/dex-timing-lcd/weavile-followup-analysis.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"observations": decoded, "legs": legs,
                      "prefix_t": prefix, "phase_cases": len(phase_runs),
                      "matching_first_misses": sum(r["miss"]["event"] == 1 and
                          r["miss"]["uploaded"] == 0 for r in phase_runs),
                      "owner_ranges": {str(dynamic): {
                          "stage_entry_t": [min(x["end_t"] for x in owner_trials if x["dynamic_stat"] == dynamic),
                                            max(x["end_t"] for x in owner_trials if x["dynamic_stat"] == dynamic)],
                          "cpu_t": sorted({x["cpu_t"] for x in owner_trials if x["dynamic_stat"] == dynamic})}
                          for dynamic in (False, True)}}, indent=2))


if __name__ == "__main__":
    main()
