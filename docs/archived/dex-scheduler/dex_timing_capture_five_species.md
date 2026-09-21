# Five Additional Species: Selected Dex Captures

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Prepared 2026-09-19 for Garchomp, Rampardos, Rayquaza, Kyogre, and Metagross.
This extends the [scheduler investigation](dex_scheduler_investigation.md).
It changes neither the game nor the host's timing assumptions.

## Test Scope

Collect **one cold Listing-to-Selected run per species**, in any convenient order.
Use the same five consecutive stops as the Dusknoir/Bastiodon follow-ups. Each
file must describe one uninterrupted run, not stops combined from multiple runs.

No warm entry, internal paging, three-repeat suite, or video is needed initially.
Keep sampled cries enabled and CPU/emulation speed unchanged. Do not fast-forward,
press A to change Description text, cancel, or page to another Pokemon during
the captured playback. Do not change debugger memory values.

The linked assets add these useful contrasts:

| Species | Total dictionary tiles | Normal cold-start decoded tiles | Remaining | Useful distinction |
|---|---:|---:|---:|---|
| Garchomp | 140 | 140 | 0 | 29-tile second stage; later two-interval holds and repeated frames |
| Rampardos | 155 | 145 | 10 | 38-tile second stage after a four-interval hold; partially decoded dictionary |
| Rayquaza | 115 | 115 | 0 | Timed static opening, followed by 15/20/31-tile stages |
| Kyogre | 124 | 124 | 0 | Timed static opening and repeated 10-tile frames before larger stages |
| Metagross | 97 | 97 | 0 | Timed static opening, initially just three upload tiles per frame, long sampled cry |

These counts describe independently checked linked frame plans and the startup
rule, not measured outcomes of the new captures. Decoded tiles are in **WRAM**,
not necessarily uploaded to the next **VRAM** slot. The startup allowance is 96
tail tiles plus the 49-tile base picture, capped at the full dictionary size.

Zero remaining tiles is therefore expected for four species even on a cold
entry; it does not imply that the entry was warmed. Rampardos' later stages need
the last 10 tiles, but its second stage only requires a prefix of 118, already
within the initial 145. A first miss may occur before those late decoding calls.
These five tests will not necessarily close the ongoing-decompression coverage
gap identified in the investigation record.

At preparation, the linked owner replay supported the previous four captured
species. All five additional captures have since been received and added as
fixtures. See the [recorded results](dex_scheduler_investigation.md#five-additional-species-2026-09-19-results)
for two capture-consistent comparisons and three remaining timing residuals.
No repeat of these five species is currently requested; the directions below
remain their historical procedure for this unchanged build. The later
[boundary investigation](dex_timing_boundary_investigation.md#focused-next-capture-luxray-historical)
requests one focused Luxray recapture using the same stops plus exact debugger
cycle counts and LCD state.

## Build Identity

The repository and `/Applications/SameBoy/Games/pokecrystal.gbc` were verified
equal when preparing these directions:

```text
ROM SHA-256
7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
Symbols SHA-256
1f791264f9ef3d8bc87a430a6333d3bea24c465017c10bb51e257303cbc6ded5
```

No rebuild, new instrumentation, or replacement ROM is needed. These addresses
apply only to that build. Leave the current ROM unchanged throughout the suite.

## Start Each Run

Start on the Dex Listing with the cursor over a different entry. Break into the
debugger, install stop 1, continue, move onto the target and immediately press A.
Release all controls when the breakpoint stops the game. From then on, use only
debugger commands until the capture is complete.

Use **one active breakpoint at a time**. `delete` clears debugger breakpoints,
not files or saves; note any unrelated breakpoints first if you need them later.
At each stop, save the breakpoint/disassembly output and the Common Dump. At
stop 1 also save Publication Extras, then replace the breakpoint with stop 2.

### Stop 1: Publication

```text
delete
breakpoint $77:$5ea5
continue
```

`Pokedex_VBlankAnimationFrontpicMap.deadline_reached`, first instruction
`LDH a, [$70]`. Capture the **first** hit. The publication count at `$c75e`,
inside the common trace dump, should still be zero.

**Rayquaza, Kyogre, and Metagross begin with a timed frame 0 (static frontpic).**
This first publication is still the correct stop even if no visual movement
has occurred. Do not continue to a later publication to find a moving frame.
Their initial holds are six, six, and four display intervals respectively.

Take Common Dump and Publication Extras, then install stop 2.

### Stop 2: Stage Entry

```text
delete
breakpoint $a0:$6483
continue
```

`Pokedex_PrepareNextAnimationStage`, first instruction `LD hl, $c72f`.
Take Common Dump, then install stop 3.

### Stop 3: Producer Entry

```text
delete
breakpoint $a0:$6282
continue
```

`Pokedex_ServiceAnimationProducer`, first instruction `LDH a, [$e6]`.
Take Common Dump, then install stop 4.

### Stop 4: Frame Wait

```text
delete
breakpoint $0:$047e
continue
```

`DelayFrame.halt`, first instruction `HALT`. The frame-wait flag has been armed.
Take Common Dump, then install stop 5.

### Stop 5: First Miss

```text
delete
breakpoint $a0:$67fc
continue
```

`Pokedex_CountAnimationUnderflow`, first instruction `LD hl, $c73b`.
Capture the **first** hit after stop 4. Do not gather every subsequent miss.
This may stop before visible corruption appears; no precise visual timestamp
is needed.

If playback finishes without a hit, Break Debugger manually and take Common
Dump. Label that section `Completed - no First Miss breakpoint`, not `First Miss`.
Note any visible error: late publication does not always reach the unfinished
stage breakpoint, so a non-hit is not a timing pass by itself.

If an earlier stop does not appear, its instruction differs, or visible trouble
has already appeared before stop 4, send the stops collected so far and explain
what happened. Do not substitute a different run or keep cycling through the
animation trying to make the expected sequence fit.

## Common Dump: Every Stop

Run these while paused, before continuing:

```text
registers
backtrace
x/27 $0:$c72e
x/139 $0:$c758
x/4 $0:$ff04
print/x [$ff0f]
print/x [$ffff]
print/x [$ff9b]
print/x [$ff44]
print/x [$ff41]
print/x [$ff4f]
print/x [$ff70]
x/6 $0:$ffee
x/8 $4:$dff4
```

Keep the timer, interrupt, and audio outputs even when the cry sounds healthy.
They distinguish execution time, frame waits, pending interrupts, and audio
production/consumption. A scanline alone is not sufficient to reconstruct
elapsed time. No separate tilemap or full VRAM/WRAM dump is needed initially.

## Publication Extras: Stop 1 Only

```text
x/2 $0:$c6dc
x/1 $0:$cfb2
x/1 $0:$cfbc
x/1 $0:$c727
x/1 $0:$cf63
x/2 $0:$ff9d
x/1 $0:$ffaa
x/1 $0:$ffd4
x/1 $0:$ffd8
x/1 $0:$ffc6
x/1 $2:$d184
x/2 $2:$d18f
print/x [$ff40]
print/x [$ff43]
print/x [$ff4b]
print/x [$ff4d]
```

These are the same initial owner, frame-plan, banking, display, and speed fields
used for the preceding follow-ups. `$ff4d` bit 7 should remain clear. If a value
is unexpected, record it; do not edit RAM to make it agree with a fixture.

## Send The Results

Use one text file per species, identified as cold entry and with an attempt
number. Include the commands and their outputs, registers and backtraces at
every stop. Use these headings with five hyphens between sections:

```text
Publication:
[outputs, including Publication Extras]
-----
Stage Entry:
[outputs]
-----
Producer Entry:
[outputs]
-----
Frame Wait:
[outputs]
-----
First Miss:
[outputs]
```

Send them individually or together. One valid continuous capture per species
is enough for this pass. We will request repeats or a video only if a concrete
state mismatch, missing path, or unexplained visual symptom warrants it.
