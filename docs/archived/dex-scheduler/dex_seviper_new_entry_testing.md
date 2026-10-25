# Seen-Only Save, Seviper And New Dex Entry Testing

> Historical test-save and Seviper record, archived 2026-09-21. Save paths,
> hashes and debugger addresses belong to the checkpoint described below.
> Seviper and Unown retests are complete; use the maintained
> [New Dex Entry procedure](../../dex_new_entry_testing.md) for the next owner
> audit and [Selected validation](../../dex_scheduler_validation.md) for current
> Selected-page diagnostics. Do not repeat the save edits merely to run tests.

## Current Checkpoint

This is the instrumented scheduler checkpoint with the temporary Route 29/30
encounters removed and Seviper's repeat target corrected. No instrumentation,
warming, scheduler or cry-runtime code was changed for this script fix. No
commit was made.

- Rebuilt `pokecrystal.gbc` SHA-256:
  `412527bdecc0c55c90a63b1d268ee7f7812788649e6936035dfd86a437e9dff7`.
- Previous encounter-cleaned ROM SHA-256:
  `83648b1c1bf9f7cf2b01ea58404c37b2081b57ab0bc92b1e0ebe164a94d2b86a`.
- Relative to that build, Seviper's repeat operand and generated timeline
  changed. The timeline grew from 31 to 44 bytes, shifting later bank-$a5
  addresses by 13 bytes. General animation/audio miss breakpoints and legacy
  interpreter addresses below are unchanged; timeline loop/finish addresses
  below have been updated. Do not reuse old bank-$a5 code breakpoints.
- The build was originally emitted in the repository root. The user subsequently
  moved it to SameBoy; its installed hash now matches the value above. It was
  not replaced automatically by the host regression suite.

The save edit was made with SameBoy closed. A byte-verified backup is beside
the original: `pokecrystal.before-all-seen-20260920-212729.sav`.
Both the primary and backup SRAM records now mark all **373 species seen**.
Their original six caught flags are unchanged: Mewtwo, Chikorita, Bayleef,
Meganium, Dusknoir and Luxray. Party, boxes, conversion tables, reserved flag
bits and the 48-byte RTC trailer are unchanged. Both main save checksums were
recomputed and verified; exactly 98 bytes changed, all within seen bitsets or
their checksums. This edit does not unlock every Unown form.

### Unown Display-Form Correction

The original all-seen edit left `wFirstUnownSeen=0`. Paging upward from Onix
therefore selected Unown with an invalid zero form. The loader expects forms
1-26; zero indexes before `UnownPicPointers`. The paused capture confirmed both
`wFirstUnownSeen` and `wUnownLetter` were zero, overwritten producer state, and
execution stuck in `RandomRange` with a zero divisor. This is inconsistent
test-save setup, not evidence of an animation scheduling deadline miss.

With SameBoy closed and user approval, the primary and backup save records now
set only the first-seen display form to `01` (Unown A), with both main checksums
recomputed. Exactly four bytes changed: file offsets `$1cb5`, `$1f10`, `$2ab5`
and `$2d10`. All other bytes are identical, including seen/caught flags, Unown
form collection/unlocks, party, boxes, conversion tables and the RTC trailer.
Both original main and move-conversion checksums were validated before editing;
the replacement and backup were read back and verified byte-for-byte.

- Backup: `/Applications/SameBoy/Games/pokecrystal.before-unown-form-fix-20260920-230946-423084.sav`
- Before SHA-256: `06bcb0a45b00fab42f87fc8b46251dede60d7901921f40aeb00d50d00ed303e0`
- After SHA-256: `2699b66c27f361d044921193f11d3f051654aaf871abcb3520287421574ed37c`

No loader fallback or other game-code change was made for this correction.
The user confirms both Listing entry and internal paging now pass without the
Unown loop/crash. The automated normal-input cold suite also passes Unown A.

Load through the title screen's normal Continue option. Loading a pre-edit
save state can restore old in-memory/save data and defeat this setup. Keep the
backup until these tests are finished. Being seen but not caught still permits
Selected Mon animation testing, but does not unlock caught-only description
content or suppress first-catch registration for an uncaught species.

## Selected Mon Miss Breakpoints

Use the following in the SameBoy debugger, at normal emulation speed:

```text
breakpoint $a0:$6805
breakpoint $0:$3cb3
```

The first is `Pokedex_CountAnimationUnderflow`, starting `LD hl, $c73b`.
The second is the timer's empty-cache branch with nonzero remaining playback,
starting `POP af`, then `LDH [$70], a`, then `JP $0063`.
It excludes natural completion and explicit stop calls. It can still expose
the known outgoing-cry exhaustion during rapid paging's black staging screen;
identify which species and screen were active rather than dismissing that hit
as an intentional cancellation.

Opcode checks when unsure which ROM is loaded:

```text
x/8 $a0:$6805
x/6 $0:$3cb3
```

Expected bytes are `21 3b c7 34 c0 23 34 c9` and `f1 e0 70 c3 63 00`.
Do not use a breakpoint on the common stop routine as an underrun detector.

### Capture At Either Miss

Remain paused and capture before continuing:

```text
registers
backtrace
ticks keep
lcd
x/27 $0:$c72e
x/139 $0:$c758
x/8 $4:$dff4
x/6 $0:$ffee
x/1 $0:$c727
print/x [$ff9b]
print/x [$ff44]
print/x [$ff41]
print/x [$ff4f]
print/x [$ff70]
print/x [$ffff]
x/1 $0:$ffc6
```

Also record the species, cold entry versus internal paging, whether input was
held, and whether the page was visible or in a black transition. For an
animation miss with visible wrong tiles, add:

```text
x/49 $0:$cb9c
x/49 $0:$cbfe
x/49 $0:$cc60
```

Number repeated hits in the same run; do not overwrite the first. Once the
animation/cry completes, manually break and repeat the four `x/27`, `x/139`,
`x/8` and `x/6` dumps as an end snapshot. The stop cleanup clears HRAM state,
so the at-breakpoint audio dump is the important one.

## Seviper: Verify The Repeat-Target Fix

Perform a cold entry and an internal page into Seviper without A/B or further
direction input. Leave both miss breakpoints enabled and allow its full
animation and cry to finish. The main animation should play the frame-4/frame-5
pair twice, return to its base hold, run the four-event idle script once, then
stop. Check paging away and B-return afterward. A separate uninterrupted
recording is useful for measuring duration; debugger pauses invalidate that
measurement.

The current linked main script is at `$34:$5bb6`:

```text
x/21 $34:$5bb6
```

Expected: `fe 03 00 04 01 04 02 04 03 04 fd 01 fe 02 04 06 05 07 fd 07 ff`.
The final `dorepeat 7` targets `frame 4`, after `setrepeat 2`, so the repeat
counter can expire. The user confirmed the old `dorepeat 6` version kept moving
for over a minute; it jumped onto the counter reset instead.

The rebuilt timeline at `$a5:$4e42` has 21 events and a finite end marker:
76 main intervals, 18 base-hold intervals and 28 idle intervals, for **122
display intervals (about 2.04 seconds)**, excluding entry/setup time. The main
duration includes the interpreter's terminal-repeat timing. Structural checks
confirm both repeat groups terminate, all 399 linked timelines are now finite,
and all 11 scheduler contract tests pass. This is not a live timing or
underrun signoff by itself. The user has since confirmed cold entry and internal
paging finish correctly. The automated cold suite independently verifies all
122 intervals, correct frame pixels, and natural cry completion. See
[the complete cold-entry results](../../dex_cold_listing_results.md).

### Optional Completion Check

For an unexpected loop or incomplete sequence, capture the common dump plus:

```text
x/44 $a5:$4e42
x/21 $34:$5bb6
```

To confirm completion independently of visible motion, set these on a fresh
Seviper entry:

```text
breakpoint $a5:$74ff
breakpoint $a5:$750b
```

- `$74ff` is the timeline loop-marker handler, starting `LD e, [hl]`. It should
  not fire for the corrected Seviper timeline. If it does, capture the common
  dump and both ROM byte ranges before continuing.
- `$750b` is the timeline finish-marker handler, starting `LD a, l`. It should
  fire once when Seviper's full sequence finishes. Continue to let final
  cleanup run. Do not change species while testing this point; another species
  finishing is not evidence about Seviper.

If neither fires after motion stops, capture the common dump to distinguish
cancellation, owner loss or a service stall. Remove these extra breakpoints
before any uninterrupted timing recording.

### Comparing Battle Or Party Stats

Those owners use the legacy script interpreter, not the generated Dex timeline.
For a dedicated Seviper run, set these only immediately before its animation:

```text
breakpoint $34:$42b7
breakpoint $34:$42c9
```

The first is `PokeAnim_DoAnimScript.DoRepeat`; the second is `PokeAnim_End`.
At a hit, capture:

```text
registers
backtrace
ticks keep
lcd
x/41 $2:$d168
x/21 $34:$5bb6
x/8 $4:$dff4
x/6 $0:$ffee
print/x [$ff70]
```

In the 41-byte legacy state dump, `$d174-$d176` identify the script bank and
pointer, `$d17d` is the next command index, `$d17f` the repeat timer and
`$d182-$d183` the current command/parameter. The first repeat group has parameter
`01`; the corrected later group has parameter `07`. Two visits to the later
group should exhaust its repeat timer and allow `PokeAnim_End`. Record the
script pointer to distinguish the main and idle scripts. The script correction
also applies to these owners, but does not change their scheduling behavior.

Remove repeat/finish breakpoints before a normal recording. Do not interpret
the Selected Mon debug overlay in battle or Stats: those owners reuse its RAM.

## New Dex Entry: Next Owner To Audit

### What Is And Is Not Shared

`_NewPokedexEntry` loads `GetAnimatedFrontpic` before playback, then initializes
`ANIM_MON_MENU`. `NewPokedexEntry.WaitPressAorB_AnimateFrontpic` advances
`SetUpPokeAnim` and `HDMATransferTilemapToWRAMBank3` in its own foreground loop.
It continues checking text input and can advance description pages before the
animation completes.

It does not use Selected Mon's streaming slots, hardware-deadline publication,
miss counter, quiet owner or telemetry. There is no corresponding legacy
animation-deadline-miss breakpoint. Slow animation can therefore occur without
ever hitting `$a0:$6805`. Its dictionary is preloaded, so an animation issue
here is not automatically a streaming tile underrun.

The sampled cry player and its `$0:$3cb3` empty-cache breakpoint are shared.
The six-byte HRAM/eight-byte WRAMX-4 dumps are valid; the Selected Mon debug
overlay is not. `$04:$dbe0` is audio data, not the old removed audio probe.

Keep the reusable host timing model and its calibration/auditing. Its current
Selected Mon replays do not certify this owner. If deeper timing data is needed,
extend it with this loop and actual legacy publication boundaries; do not
pretend its frames pass through `Pokedex_VBlankAnimationFrontpicMap`.

### Initial Suite

Start with three uninterrupted registrations each for Dusknoir and Metagross,
plus a synthesized control such as Caterpie. Add one each of Luxray, Weavile
and Groudon once those establish the baseline. Test early A-to-description-2
and B/exit separately, with species, timing and audio ownership recorded.
Keep Seviper's script-fix retest separate from the initial owner timing suite.

Registration requires the species to be **uncaught**, not unseen. The all-seen
save is suitable for currently uncaught species. Dusknoir and Luxray remain
caught; a later separately authorized, backed-up test-save edit is needed to
clear those specific caught flags. No caught flags or additional encounter
overrides were changed for this setup. Establish an uncaught save/state per
case so three captures test registration three times rather than only battle.

### Boundary Captures Without New ROM Instrumentation

First arm only the owner entry point, so the preceding battle cry cannot be
confused with registration playback:

```text
breakpoint $3e:$57f0
```

At that stop, capture registers/backtrace and the audio dump below. Then remove
that breakpoint and arm the registration wait-loop entry:

```text
breakpoint $3e:$5871
```

At its first hit, run `ticks` to reset the cycle counter, capture the legacy
state below, and remove this breakpoint. This is before the registration's
animation/cry sequence starts, so it includes startup overhead. Set:

```text
breakpoint $0:$3cb3
breakpoint $34:$42c9
breakpoint $34:$4171
```

- `$34:$42c9` marks an animation script reaching `endanim`. For `ANIM_MON_MENU`,
  expect one main-script and then one idle-script stop. The state/pointer dump
  distinguishes them; do not reset `ticks` between these stops.
- `$34:$4171` is the final `PokeAnim_Finish` setup command. Capture its state and
  `ticks keep`. It marks software completion before the caller's final transfer,
  not the exact LCD publication of the final pixels.
- `$0:$3cb3` is a genuine empty-cache hit. Capture immediately, then continue;
  animation may keep running after the cry stops.

Use this at each stop:

```text
registers
backtrace
ticks keep
lcd
x/41 $2:$d168
x/1 $0:$cf64
x/8 $4:$dff4
x/6 $0:$ffee
print/x [$ff9b]
print/x [$ff4f]
print/x [$ff70]
print/x [$ffff]
```

After the final animation stop, continue without pressing a button until the
cry also finishes, then manually break for a final audio dump. A cry ending
later than the animation is not by itself a failure. Do not use a breakpoint
on the shared stop function, which also catches normal completion.

Record one uninterrupted normal-speed run per baseline species separately
from debugger captures, with the UI/input overlay visible. These software
boundary captures reveal coarse phase costs and audio failure, while video
establishes visible frame durations. Exact per-frame auditing would then add
legacy frame-ID/publication timestamps and cache/service timing with an
owner-safe buffer or host trace. No new ROM telemetry is required for the
initial triage, and none was added in this checkpoint.

## Commit Scope

Commit the scheduler/generator, existing marked instrumentation, reusable tests
and documentation as the requested instrumented checkpoint. Leave instrumentation
cleanup and warm-caching removal for separate work. Exclude local `build/`
captures, emulator saves/states and generated ROMs. The current Selected Mon
telemetry is not a prerequisite for New Dex Entry's baseline captures, but the
auditing/model sources remain useful and should be kept.
