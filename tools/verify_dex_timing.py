#!/usr/bin/env python3
"""Host-only Selected Dex timing audit. See docs/dex_timing_model.md."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from dex_timing.assets import Repository, sha256
from dex_timing.costs import benchmark, audio_benchmark, publication_benchmark, verify_hdma_contract
from dex_timing.cpu import ModelError
from dex_timing.model import Profile, simulate, FRAME
from dex_timing.traces import decode_trace, read_captures
from dex_timing.calibration import compare, render_comparison
from dex_timing.followup import compare_followup, render_followup

ROOT = Path(__file__).resolve().parents[1]
WORKER = None


def init_worker(root, rom, sym, shared, options):
    global WORKER
    WORKER = Repository(root, rom, sym), shared, options


def measure_asset(asset):
    repo, shared, options = WORKER
    costs = benchmark(repo, asset)
    profile = Profile(**options["profile"])
    runs = []
    for path in options["paths"]:
        for ly in options["phases"]:
            modes = (True, False) if asset.sample_blocks and options["audio"] == "both" else (options["audio"] != "off",)
            for audio_enabled in modes:
                runs.append(simulate(asset, costs, shared["audio"], shared["publication"], profile,
                                     ly, options["loops"], audio_enabled, path))
    return {"asset": {"name": asset.name, "size": asset.sizes, "event_loop": asset.event_loop,
                      "event_count": len(asset.events), "schedule_calls": len(asset.actions)},
            "costs": costs, "runs": runs}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def check_assumptions(root):
    contracts = {
        "constants/gfx_constants.asm": ["DEF FRONTPIC_ANIM_DICTIONARY_CHUNK_TILES EQU 6"],
        "constants/audio_constants.asm": ["DEF SAMPLED_CRY_STARTUP_PREFILL_BLOCKS EQU 32",
                                          "DEF SAMPLED_CRY_CACHE_REFILL_BLOCKS EQU 8"],
        "engine/pokedex/pokedex.asm": ["DEF POKEDEX_ANIM_UPLOAD_CHUNK_TILES EQU 20",
                                       "DEF POKEDEX_ANIM_STARTUP_STREAMS EQU 16"],
    }
    for name, needles in contracts.items():
        lines = {" ".join(line.split(";", 1)[0].split()) for line in (root/name).read_text().splitlines()}
        for needle in needles:
            if needle not in lines:
                raise ModelError(f"Timing contract changed: expected {needle} in {name}; update the host model deliberately")


def render_summary(report):
    entries = report["entries"]
    runs = [run for e in entries for run in e["runs"]]
    misses = [r for r in runs if r["animation_miss"]]
    audio_misses = [r for r in runs if r["audio_underrun_t"] is not None]
    late = [r for r in runs if any(p.get("late_intervals", 0) for p in r["publishes"])]
    shared = report["shared_costs"]
    lines = ["# Selected Dex Timing Experiment", "", "**Status: UNCALIBRATED. Not a timing certification.**", "",
             f"ROM SHA-256: `{report['manifest']['rom_sha256']}`", "",
             f"Validated {len(entries)} linked asset sets; ran {len(runs)} bounded scenarios.",
             f"Model animation misses: {len(misses)}. Model audio underruns: {len(audio_misses)}.",
             f"Scenarios with late publication: {len(late)} (can overlap the miss counts).",
             "These counts describe the configured model, not observations of this ROM in SameBoy.", "",
             "## Measured Instruction Paths", "",
             "T-cycles below exclude interruptions unless stated. Normal speed: 4,194,304 T/s; 70,224 T/display interval.", "",
             f"- Eight-block audio refill: {max(v['t'] for v in shared['audio']['refill']['8']):,} T (cache-wrap fixture).",
             f"- 32-block prefill body: {max(v['t'] for v in shared['audio']['refill']['32']):,} T; excludes cry setup/arming.",
             f"- Sample timer interrupt: {max(shared['audio']['timer_irq_t']):,} T including vector JP and hardware entry.",
             f"- Short LCD STAT interrupt: {shared['audio']['lcd_irq_t']:,} T including vector JP and hardware entry.",
             f"- Idle sampled-playback VBlank fixture: {shared['publication']['vblank']['idle_t']:,} T including OAM wait and housekeeping.",
             f"- Inner map publication: {shared['publication']['software_t']:,} CPU T + {shared['publication']['gdma_t']:,} GDMA T.", "",
             "## Per-Species Summary", "",
             "Startup is only the measured animation CPU component, NOT selection/paging latency. Warm means the first-event dictionary target and first stage are prepared, not necessarily the full dictionary.", "",
             "| Species | Tiles (base + tail) | Max 6-tile decode service T | Max new-stage T | Cold startup CPU intervals | Misses / cases |",
             "|---|---:|---:|---:|---:|---:|"]
    for entry in entries:
        c, r = entry["costs"], entry["runs"]
        startup = next((x["startup_cpu_component_t"] for x in r if x["path"] != "warm"), 0)
        lines.append(f"| {c['name']} | {c['base_tiles']} + {c['total_tiles']-c['base_tiles']} | "
                     f"{max((x['service_t'] for x in c['decode'][1:]), default=0):,} | "
                     f"{max(x for pair in c['build_t'] for x in pair):,} | {startup/FRAME:.2f} | "
                     f"{sum(bool(x['animation_miss']) for x in r)} / {len(r)} |")
    lines += ["", "## Model Boundaries", "",
              "The current compact schedule advances by producer calls; deadlines advance by display intervals. That mismatch is modeled, not corrected.",
              "CPU decoding and gathering run during visible scanout too. Only VRAM access/publication is constrained by the modeled display windows.",
              "Audio cache count increases after each decoded block, not after an imaginary instantaneous refill.",
              "HDMA advances while interrupts execute; interrupt time is not blindly added to the whole transfer train.",
              "LCD mode-0 requests continue while interrupts are masked, coalesce in IF, and use VBlank > LCD > timer priority.",
              "A late publication is recorded separately; the underrun breakpoint is the mainline unfinished-stage check.",
              "Stops at the first missed animation deadline. Audio behavior after that miss is not simulated.",
              "Time-accounting wait entries are elapsed intervals that INCLUDE interrupt and DMA time; they must not be summed with CPU totals.", "",
              "Historical Weavile/Luxray captures are retained with their original bytes. Their ROM hash is unknown, so they are observations, not calibration. A phase sweep matching an observed frame does not establish the actual phase or explain missing CPU time.", "",
              "## Still Required Before Runtime Changes", ""]
    lines += [f"- {x}." for x in report["profile"]["unknown"]]
    lines += ["- Match component timings and first-miss events against build-bound SameBoy captures.",
              "- Reconcile any model/measurement discrepancy before treating a no-miss scenario as evidence.",
              "- Expand the phase/loop sweep as needed; finite sampling is not a universal deadline proof.", ""]
    return "\n".join(lines)


def capture_directions(repo):
    bank, address = repo.symbols["Pokedex_CountAnimationUnderflow"]
    debug = repo.symbols["wPokedexAnimDebug"][1]
    anim = repo.symbols["wPokedexAnimOwner"][1]
    counter = repo.symbols["hVBlankCounter"][1]
    lcd_pointer = repo.symbols["hLCDCPointer"][1]
    # A format change must be handled explicitly, not silently decoded as v6.
    if repo.symbols["wPokedexAnimTraceRecords"][1]-debug != 46 or repo.symbols["wPokedexAnimScheduleRun"][1]-debug != 138:
        raise ModelError("Capture schema moved; update the version-6 decoder before using these directions")
    return f"""# Build-Bound SameBoy Calibration Capture

ROM SHA-256: `{repo.hashes['rom_sha256']}`

This is the existing instrumented game build, not a new scheduler implementation.
Use only a ROM matching this hash. These addresses were read from its symbol file.

## First Capture Set

1. Cold Listing -> Weavile, three attempts. Record the first underrun stop in each attempt.
2. Cold Listing -> Luxray, three attempts, again stopping on the first underrun.
3. One warm Listing -> each of those two, then one internal-paging entry to each.
4. Cold Listing -> Dusknoir and Metagross, one attempt each; Chikorita as a synth control.

Do not change Description text pages during playback. That is a separately logged bug.
Keep each dump labeled with species, cold/warm/paging, attempt number, and whether a visible error occurred.
If there is no stop, let the animation finish, Break Debugger manually, and capture the same fields.
No video is needed for this first timing calibration; a recording is useful later for checking visible publication timing.

## Breakpoint

Remove old breakpoints that would interfere, then set:

```text
breakpoint ${bank:x}:${address:04x}
```

At the stop, capture the following BEFORE continuing:

```text
registers
backtrace
x/27 $0:${anim:04x}
x/139 $0:${debug:04x}
print/x [${counter:04x}]
print/x [$ff44]
print/x [$ff41]
print/x [$ff4f]
print/x [$ff70]
print/x [$ff4d]
print/x [$ffff]
x/1 $0:${lcd_pointer:04x}
```

KEY1 ($ff4d) bit 7 must be clear for this normal-speed model. Do not switch CPU speed.
IE, STAT and hLCDCPointer identify whether the short mode-0 interrupt fixture applies.
The 139-byte dump contains the existing five-record trace ring and compact-schedule cursor.
It records entry, post-stage, post-decode, post-gather, HDMA-entry and HDMA-exit timestamps.
Each timestamp has scanline resolution, not dot resolution; comparisons retain a +/-455 T uncertainty.
The tool reconstructs ring order and 8-bit counter wrap. It rejects incomplete or incompatible dumps.

## Import

```sh
python3 -B tools/verify_dex_timing.py trace /absolute/path/to/capture.txt \\
  --base 0x{debug:04x} \\
  --report build/dex-timing/report.json \\
  --rom-sha256 {repo.hashes['rom_sha256']} \\
  --output build/dex-timing/capture.json
```

Only supply the hash after confirming the captured ROM matches. Omitting it explicitly leaves the observation unbound.
Keep the report and manifest with the captures. Regenerating a report after code changes is not calibration of the old build.

## Acceptance Gate

First reconcile the observed first-miss event, producer gaps, and component elapsed ranges with the model.
Do not tune arbitrary overhead until an aggregate miss count matches. Identify the missing path/work instead.
LY-only measurements cannot separate instruction work from IRQ time on their own. If the existing trace cannot bound that
difference, propose a focused follow-up measurement before changing runtime instrumentation.
Then expand to repeated Dusknoir, Metagross, Bastiodon and Rampardos cases and the remaining entry paths.
Only after component costs, phase behavior and first-miss replay agree should the model guide scheduler changes.
"""


def audit(args):
    root = args.root.resolve()
    check_assumptions(root)
    repo = Repository(root, args.rom, args.sym)
    verify_hdma_contract(repo)
    assets = repo.load(args.species)
    profile = Profile()
    if args.profile:
        values = json.loads(args.profile.read_text())
        if not isinstance(values, dict) or "unknown" in values:
            raise ModelError("A scenario profile cannot remove unknown-cost warnings")
        profile = Profile(**values)
    profile.validate()
    manifest = repo.manifest()
    manifest["host_tools"] = {str(p.relative_to(root)): sha256(p.read_bytes()) for p in
                              sorted((root/"tools/dex_timing").glob("*.py"))}
    manifest["host_tools"]["tools/verify_dex_timing.py"] = sha256(Path(__file__).read_bytes())
    if args.reference_manifest and json.loads(args.reference_manifest.read_text()) != manifest:
        raise ModelError("Reference manifest does not match this ROM, symbols, sources, tools or selected assets")
    shared = {"audio": audio_benchmark(repo), "publication": publication_benchmark(repo)}
    options = {"profile": asdict(profile), "paths": args.paths, "phases": args.phases,
               "loops": args.loops, "audio": args.audio}
    init_worker(root, args.rom.resolve(), args.sym.resolve(), shared, options)
    if args.jobs == 1:
        entries = [measure_asset(a) for a in assets]
    else:
        with ProcessPoolExecutor(max_workers=args.jobs, initializer=init_worker,
                                 initargs=(root, args.rom.resolve(), args.sym.resolve(), shared, options)) as pool:
            entries = list(pool.map(measure_asset, assets))
    fixtures = json.loads((root/"tools/dex_timing/fixtures/known_misses.json").read_text())
    observed = [{"species": f["species"], "trace": decode_trace(bytes.fromhex(f["hex"]))}
                for f in fixtures["captures"]]
    report = {"schema": 1, "status": "UNCALIBRATED", "units": "normal-speed SM83 T-cycles",
              "manifest": manifest, "profile": asdict(profile), "coverage": options,
              "shared_costs": shared, "entries": entries,
              "historical_observations": {"provenance": fixtures["provenance"], "captures": observed}}
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output/"report.json", report)
    write_json(args.output/"manifest.json", manifest)
    (args.output/"summary.md").write_text(render_summary(report))
    (args.output/"sameboy_capture.md").write_text(capture_directions(repo))
    print(f"Validated {len(assets)} linked asset sets and their executed decode/build/gather outputs.")
    print(f"Results: {args.output.resolve() / 'summary.md'}")
    print("UNCALIBRATED: model misses/no-misses are diagnostic, not hardware certification.")
    return 2 if args.strict else 0


def trace(args):
    captures = read_captures(args.capture.read_text(), args.base)
    if args.rom_sha256:
        if not args.report:
            raise ModelError("A capture hash requires --report for build comparison")
        report = json.loads(args.report.read_text())
        if args.rom_sha256 != report["manifest"]["rom_sha256"]:
            raise ModelError("Capture ROM hash differs from the timing report")
        for c in captures:
            c["calibration_status"] = "BUILD_BOUND_OBSERVATION_NOT_YET_CALIBRATED"
            c["rom_sha256"] = args.rom_sha256
    result = {"captures": captures,
              "warning": "A matching hash binds the observation; it does not validate the cost model automatically."}
    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, indent=2))
    return 0


def comparison(args):
    repo = Repository(ROOT, ROOT/"pokecrystal.gbc", ROOT/"pokecrystal.sym")
    report, baseline = (json.loads(p.read_text()) for p in (args.report, args.baseline))
    if args.rom_sha256 != repo.hashes["rom_sha256"]:
        raise ModelError("Confirm the captured ROM hash before comparing")
    result = compare(repo, report, baseline, args.captures, args.hblank_dots)
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output/"comparison.json", result)
    (args.output/"comparison.md").write_text(render_comparison(result))
    print(f"Comparison: {args.output.resolve() / 'comparison.md'}")
    print("PARTIAL_NOT_CALIBRATED: phase-envelope overlap is not exact replay.")
    return 0


def followup(args):
    repo = Repository(ROOT, ROOT/"pokecrystal.gbc", ROOT/"pokecrystal.sym")
    if args.rom_sha256 != repo.hashes["rom_sha256"]:
        raise ModelError("Confirm the captured ROM hash before comparing")
    result = compare_followup(repo, json.loads(args.report.read_text()), args.capture, args.species)
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output/"followup.json", result)
    (args.output/"followup.md").write_text(render_followup(result))
    print(f"Follow-up: {args.output.resolve() / 'followup.md'}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("audit", help="validate linked assets, count routines and simulate bounded scenarios")
    run.add_argument("--root", type=Path, default=ROOT)
    run.add_argument("--rom", type=Path, default=ROOT/"pokecrystal.gbc")
    run.add_argument("--sym", type=Path, default=ROOT/"pokecrystal.sym")
    run.add_argument("--species", nargs="+")
    run.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
    run.add_argument("--paths", nargs="+", choices=("cold", "warm", "paging"), default=["cold", "warm", "paging"])
    run.add_argument("--phases", nargs="+", type=int, default=[0, 64, 107, 108, 128, 143, 144, 153])
    run.add_argument("--loops", type=int, default=2)
    run.add_argument("--audio", choices=("native", "off", "both"), default="both")
    run.add_argument("--profile", type=Path, help="explicit exploratory workload envelope; not calibration")
    run.add_argument("--reference-manifest", type=Path)
    run.add_argument("--output", type=Path, default=ROOT/"build/dex-timing")
    run.add_argument("--strict", action="store_true", help="exit 2 for uncalibrated results, even without a predicted miss")
    run.set_defaults(handler=audit)
    capture = commands.add_parser("trace", help="decode existing version-6 SameBoy memory captures")
    capture.add_argument("capture", type=Path)
    capture.add_argument("--base", type=lambda x: int(x, 0), default=0xC758)
    capture.add_argument("--rom-sha256")
    capture.add_argument("--report", type=Path)
    capture.add_argument("--output", type=Path)
    capture.set_defaults(handler=trace)
    calibration = commands.add_parser("compare", help="compare build-bound captures with old/new host reports")
    calibration.add_argument("captures", nargs="+", help="species=/absolute/path/to/capture.txt")
    calibration.add_argument("--report", type=Path, required=True)
    calibration.add_argument("--baseline", type=Path, required=True)
    calibration.add_argument("--rom-sha256", required=True)
    calibration.add_argument("--output", type=Path, default=ROOT/"build/dex-timing-lcd")
    calibration.add_argument("--hblank-dots", type=int, nargs="+", help="explicit PPU profiles; default uses report profile")
    calibration.set_defaults(handler=comparison)
    focused = commands.add_parser("followup", help="compare the five-stop owner/DelayFrame capture")
    focused.add_argument("capture", type=Path)
    focused.add_argument("--species", default="weavile")
    focused.add_argument("--report", type=Path, required=True)
    focused.add_argument("--rom-sha256", required=True)
    focused.add_argument("--output", type=Path, default=ROOT/"build/dex-timing-owner")
    focused.set_defaults(handler=followup)
    args = parser.parse_args()
    try:
        if getattr(args, "jobs", 1) < 1:
            raise ModelError("--jobs must be positive")
        return args.handler(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
