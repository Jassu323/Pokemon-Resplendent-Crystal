# Build-Bound SameBoy Calibration Capture

ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

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
breakpoint $a0:$67fc
```

At the stop, capture the following BEFORE continuing:

```text
registers
backtrace
x/27 $0:$c72e
x/139 $0:$c758
print/x [$ff9b]
print/x [$ff44]
print/x [$ff41]
print/x [$ff4f]
print/x [$ff70]
print/x [$ff4d]
```

KEY1 ($ff4d) bit 7 must be clear for this normal-speed model. Do not switch CPU speed.
The 139-byte dump contains the existing five-record trace ring and compact-schedule cursor.
It records entry, post-stage, post-decode, post-gather, HDMA-entry and HDMA-exit timestamps.
Each timestamp has scanline resolution, not dot resolution; comparisons retain a +/-455 T uncertainty.
The tool reconstructs ring order and 8-bit counter wrap. It rejects incomplete or incompatible dumps.

## Import

```sh
python3 -B tools/verify_dex_timing.py trace /absolute/path/to/capture.txt \
  --base 0xc758 \
  --report build/dex-timing/report.json \
  --rom-sha256 7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f \
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
