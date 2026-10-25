# Dusknoir And Bastiodon: Owner Follow-Up Captures

> Historical investigation record, archived 2026-09-21. Measurements, addresses,
> "current" statements and proposed fixes below refer to the builds described
> in this report, not necessarily the current game. See the
> [archive index](README.md) for context and the
> [current validation guide](../../dex_scheduler_validation.md) for testing.

Prepared 2026-09-19 for the unchanged, instrumented Selected Dex build.
This extends the [scheduler investigation](dex_scheduler_investigation.md);
it does not change the game or claim the host already supports these cases.

## Purpose And Scope

Start with **one cold Listing-to-Selected capture per species**. Each is one
continuous run with five consecutive stops, matching the Weavile/Luxray method.
Do not restart, change species, or select a different run between those stops.

- Dusknoir adds partially decoded initial state. Whether additional dictionary
  decoding occurs before the captured miss must be established by the data.
  The existing 27-byte animation dump includes the compressed source pointer,
  dictionary destination, total/remaining tile counts, and upload progress.
- Bastiodon broadens the stage/transfer/deadline case beyond Luxray. Whether it
  has exactly the same failure chain is a question, not a premise of this test.

No three-repeat suite, warm entry, internal paging, or video is required yet.
No additional ROM instrumentation is needed. Keep normal speed and the existing
audio settings; do not use fast-forward or change Description text pages.

Follow-up result: neither captured species decoded additional dictionary tiles
between first publication and first miss. See the investigation record for the
distinction between partial initial state and active decoder coverage.

## Build Identity

Both the repository ROM and `/Applications/SameBoy/Games/pokecrystal.gbc` were
verified with this SHA-256:

```text
7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f
```

All addresses below come from that ROM's symbol file. Do not rebuild or replace
the ROM between captures. If another image is loaded, confirm its identity before
using these addresses. No new build or reinstall is required for this test.

## Procedure

Use one active breakpoint at a time. `delete` below clears debugger breakpoints;
it does not delete a file or save. It will also remove other breakpoints you may
have wanted to retain, so record those first if needed.

Start on the Listing with the cursor on another entry. Pause the debugger and
set stop 1 below. Continue, move onto the target Pokemon, and immediately press A
instead of waiting over it. Release all controls at the first stop. From there,
use only debugger commands until the five stops are collected.

At every stop, record its heading, debugger breakpoint/disassembly output, and
the **Common Dump** below. At stop 1, also record **Publication Extras**.
Then replace the breakpoint with the next one and continue.

### Stop 1: Publication

```text
delete
breakpoint $77:$5ea5
continue
```

This is `Pokedex_VBlankAnimationFrontpicMap.deadline_reached`, just before the
first queued map is published. Its first instruction is `LDH a, [$70]`.
The map-publication counter at `$c75e`, already included in the common trace
dump, should still be zero for this first stop. Record the data rather than
editing any memory if something looks unexpected.

After taking the Common Dump and Publication Extras, move to stop 2.

### Stop 2: Stage Entry

```text
delete
breakpoint $a0:$6483
continue
```

This is `Pokedex_PrepareNextAnimationStage`; first instruction `LD hl, $c72f`.
It captures the next stage's construction entry after the first publication.
Take the Common Dump, then move to stop 3.

### Stop 3: Producer Entry

```text
delete
breakpoint $a0:$6282
continue
```

This is `Pokedex_ServiceAnimationProducer`; first instruction `LDH a, [$e6]`.
Take the Common Dump, then move to stop 4.

### Stop 4: Frame Wait

```text
delete
breakpoint $0:$047e
continue
```

This is `DelayFrame.halt`; first instruction `HALT`. The new frame-wait flag has
already been set. Take the Common Dump, then move to stop 5.

### Stop 5: First Miss

```text
delete
breakpoint $a0:$67fc
continue
```

This is `Pokedex_CountAnimationUnderflow`; first instruction `LD hl, $c73b`.
Take the Common Dump at the **first** hit. Later underruns from the same run are
not needed yet. The stop can occur before a visible error; that is expected.

If it never hits, allow playback to finish, then Break Debugger manually and
take the same Common Dump. Label this `Completed - no First Miss breakpoint`
instead of claiming it is a First Miss capture. Note any visual problem that
did occur. A queued-but-late publication need not trip this breakpoint, so a
non-hit is not by itself proof of correct animation timing.

If the initial four breakpoints do not appear in this sequence, or their
instructions differ, stop and send the last capture; do not substitute another
run or guess a new address.

## Common Dump: Every Stop

Run while paused, before continuing:

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

The timer registers and pending-interrupt flags are essential. They let the host
check one continuous elapsed-time sequence instead of matching scanlines alone.
The audio dump includes the block period, cached-block count, remaining compressed
data, and read/write positions; please include it even when the cry sounds fine.

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

These capture the cursor/text owner state, game-timer/menu/Selected state, bank
and VBlank owner, map/OAM/LCD controls, frame-plan pointer, LCD configuration,
horizontal scroll, window position, and CPU speed. They reduce assumptions when
constructing the initial replay state. `$ff4d` bit 7 should be clear.

No full WRAM or VRAM dump is requested. For Dusknoir, `$c742` in the 27-byte
block identifies whether dictionary work remains at first publication. If it is
zero despite an immediate selection, note a possible warmed entry and finish
the sequence unchanged; the actual captured state is more useful than forcing a
desired value. Do not set or clear RAM through the debugger.

## Returning The Results

Use separate text files for Dusknoir and Bastiodon. Preserve the commands, their
outputs, registers, and backtraces. Use these section names and a line of five
hyphens between sections, as in the existing follow-ups:

```text
Publication:
[outputs]
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

Only use the final `First Miss` heading when that breakpoint actually hit.
Label the file/message with species, cold entry, attempt number, and whether an
obvious error was visible. It is fine to send Dusknoir first before starting
Bastiodon. No video or precise visual-corruption timestamp is needed for this
pass. Additional capture requests should be driven by a concrete missing state
or replay discrepancy, not a blanket repeat of the entire suite.
