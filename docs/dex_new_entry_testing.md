# New Dex Entry Testing

## Current Implementation Test

Updated 2026-09-21. The resident scheduler and registration-local batch uploader
are now implemented. See [the system reference](new_dex_entry_animation_scheduler.md)
for the exact ownership, memory, timing and cleanup contract. Stats Screen is
unchanged. The earlier preflight/capture records below are historical, not the
current runtime procedure.

Current build identities:

```text
ROM d736de2d8215c8365dd8ec8a5d2f01ff7e3cefdf387ed8f4b510015d3f018675
SYM 4c26771293d8a3d119f7da55b0ae66b33f4fe8e0214b34e00510fa9675cd4a86
MAP 691de7b2c15ec1b74516b8324f4ca8b10aa153b1f4048e4451c0b66c98be6e7e
```

This build adds the acknowledged, single-VBlank description update. It retains
the faster picture copies and their LY < 150 cutoff; the disjoint 91-cell text
copy has its own LY < 149 cutoff. Audio, prefill, authored animation deadlines
and startup loading are unchanged. The original Master Ball, ordinary Route
29/30 encounters and instrumentation remain. The animation-miss address is now
**$a5:$775e**; entry, RAM and audio-miss addresses are unchanged.

All eight catches / 24 basic variants and **8,570 input cases** pass, including
all eleven previously failing Mewtwo text timings. They now show complete page-2
text after three display intervals from A instead of nine to eleven, with no
mixed text frames. See [current results](new_dex_entry_regression_results.md#acknowledged-description-publication).
The user accepted the manual result on 2026-09-21, noting a perceived one- or
two-frame text-before-page-number offset. That estimate is unmeasured and not
reproduced by the automated fixtures; it is accepted without further changes.
The separate battle cry issue remains deferred.

Use the root `pokecrystal.gbc` and matching symbols. The installed SameBoy ROM
has not been replaced automatically. Re-resolve addresses after any relink.
The eight named **pre-catch** states have passed cross-build compatibility
checks; unrelated old states, especially ones already inside registration,
have not. Their saved not-caught flags permit repeating the New Entry path.

### Available Catch Fixtures

| Existing slot | Species | Expected uninterrupted menu intervals | Capture branch |
| --- | --- | ---: | --- |
| 1 | Luxray | 92 | Level-up/stat prompt |
| 2 | Caterpie | 111 | Synthesized-cry control |
| 3 | Metagross | 228 | Level-up/stat prompt |
| 4 | Dusknoir | 174 | Largest resident dictionary |
| 5 | Garchomp | 110 | Level-up/stat prompt; short holds |
| 6 | Exeggcute | 113 | Level-up/stat prompt; synthesized cry |
| 7 | Vibrava | 83 | 6x6 picture; sent to PC |
| 8 | Mewtwo | 111 | Synthesized cry; sent to PC |

Intervals run from first publication to final base restoration, including main,
the 18-interval transition hold, and idle. Dusknoir's main-only 107 intervals
are not the full menu sequence's 174. Timing is checked automatically; manual
testing need not count frames.

### Optional Manual Regression

Both the faster-copy and description-fix manual passes are accepted. The steps
below are retained for future regression testing, not outstanding requirements.
Mewtwo's A-to-page-2 transition during quick motion and after it stops covers
description publication; Dusknoir adds sampled audio coverage.

Test **Dusknoir (slot 4), Metagross (slot 3), and Mewtwo (slot 8)** with the
original Master Ball animation. Dusknoir covers the phase-sensitive first
publication, Metagross covers long audio and level-up prompts, and Mewtwo covers
synthesized audio and PC return. Caterpie is an optional simpler control. There
is no need to manually repeat the full automated input or phase matrix.

For each:

1. Load its validated pre-catch state with the new ROM, or make a fresh catch of
   a not-caught species. Let the catch/experience/stat prompts run normally.
2. First pass: leave New Entry untouched through the complete animation and
   cry. Then A to description page 2, B to leave, and check battle/PC return.
3. Second pass: press A while the picture is moving. Check both the picture and
   description text while animation/cry finish on page 2.
4. Third pass: press A and then B early. Check prompt responsiveness, clean
   return, correct party/box result, and absence of a stuck animation owner.

For the second pass, vary A between early and later motion. Look for a held or
mixed frontpic, fragments of page-1 text, an incorrect page number, changed
header/dimensions, or an audible cry cutoff. Both miss breakpoints can remain
silent on a graphics-only defect, so inspect the picture and text too. A video
is only needed if something looks or sounds wrong. The remaining original
fixtures are optional presentation checks, not an outstanding timing sweep.

Mewtwo's formerly reproducible partial refresh is now fixed in automated tests.
The slight text/page-number offset perceived during manual testing is an
accepted caveat, not a pending fix. New persistent corruption or a larger delay
still warrants capture even if neither miss breakpoint fires. Battle Dusknoir
cry underruns remain separately deferred.

### Breakpoints

To avoid stopping on an earlier **battle** cry, first stop on registration entry:

```text
delete
breakpoint $3e:$57f0
continue
```

This is `NewPokedexEntry`, starting `LDH a, [$de]`, `PUSH af`. Once stopped,
replace it with the two failure breakpoints:

```text
delete
breakpoint $a5:$775e
breakpoint $0:$3cb3
continue
```

- `$a5:$775e` = `NewDexEntryAnimationMiss`, first instruction `INC [hl]`.
  It has already stored the miss reason but has not yet incremented its count.
- `$00:$3cb3` = sampled timer's empty-cache/nonzero-remaining path, starting
  `POP af; LDH [$70], a; JP $0063`. **Not** the normal completion path.

Verify linked bytes if in doubt:

```text
x/6 $a5:$775e
x/6 $0:$3cb3
```

Expected: `34 e1 c9 e1 c9 06` and `f1 e0 70 c3 63 00` respectively.
The acceptance target is neither failure breakpoint triggering during
registration, including advancing to page 2 while animation and cry are active.
The restored Master Ball Dusknoir replay no longer hits either breakpoint.
Capture any manual hit rather than treating it as expected animation behavior.
If the audio one triggers after early exit, report the stack and whether the
page was already gone; do not assume every outgoing-cry exhaustion is harmless.

### Capture At Either Failure

Leave the emulator paused and capture this entire block, plus the species,
state slot, input just taken, and whether description page 1 or 2 was visible:

```text
registers
backtrace
ticks keep
lcd
x/41 $2:$d168
x/49 $2:$d191
x/98 $2:$d000
x/8 $4:$dff4
x/6 $0:$ffee
x/1 $0:$cf64
x/1 $0:$ff9e
x/1 $0:$ffd8
x/2 $0:$ffd4
print/x [$ff9b]
print/x [$ff9d]
print/x [$ff4f]
print/x [$ff70]
print/x [$ffff]
```

Save a separate failure state without overwriting the eight starting states.
The new flags/count/reason are in **WRAMX 2**, not Selected's WRAM0 telemetry.
`$d17e` is the miss count; `$d185` is reason 1 (not ready), 2 (late deadline),
or 3 (unsafe publication window). `$d181` is the due display-counter value.
Bit 6 of `$d168` means a complete description is waiting for publication; it
must clear after the copy. For a text-only fault, additionally capture
`x/118 $0:$c556` (page number through description backing cells) and a failure
state/video; do not interpret a temporarily pending request as an animation miss.
The `$d000` pair buffer's unused trailing bytes may be stale; its entire length
is not an active pair count. No legacy audio `$dbe0` instrumentation exists.

If graphics look wrong without a breakpoint, capture the same state and a short
video. Video is otherwise optional for this pass. After natural completion,
the owner flags and `wFrameCounter` should be zero and the previous VBlank owner
restored; after the cry also ends, HRAM active/remaining should be zero.

### Automated Results And Reproduction

These results cover the current acknowledged-description build, with the
original Master Ball opening and ordinary Route 29/30 encounters. They are not
inferred from the preceding picture-copy or encounter-cleanup builds:

- **8 authentic catch flows** and **24 representative registration variants**.
- **20 species / 8,570 input-timing cases: all pass every check**, including
  all eleven formerly failing Mewtwo cases.
- **1,207,645 displayed frontpics** match physical VRAM and rendered pixels;
  animation deadlines and exit cleanup pass in every case.
- **7,104 sampled-cry runs** finish with correct block accounting and no underrun.
- **5,571 complete animation sequences** meet exact event deadlines; early
  cancellation is checked against its expected timeline prefix.
- **6,492 description advances / 579,345 description display checks** have
  no mixed text or later reversion. Paired Mewtwo cases improve from 9-11
  intervals after A to 3, without moving their observation point.
- **56 contract/regression tests**, including publication between flag reads,
  text acknowledgement/atomicity and exact PPU-boundary clock checks.
- **9,600 synthetic timer-phase cases / 1,122,800 display checks** pass for
  sixteen sampled species. Each runs completion, description advance and early
  exit at all 200 first-overflow offsets. This is a 64-T grid, not every hardware
  phase. The full suites were rerun after correcting CPU/PPU callback timestamp
  accounting, with zero allowed drift at actual PPU display boundaries.
- Structural checks cover **399 assets / 2,121 pictures**.

See [the regression report](new_dex_entry_regression_results.md#acknowledged-description-publication)
for current evidence and the separately labeled historical failures/prototypes.
Twelve added species use explicitly generated registration-entry fixtures;
they are not additional authentic catch-flow coverage.

```sh
make -j8 pokecrystal.gbc
python3 -B tools/test_new_dex_entry.py
python3 -B -m tools.dex_timing.new_entry \
  --fixtures build/new-dex-entry-catches \
  --fixtures build/new-dex-entry-expanded \
  --output build/new-dex-entry-text-publication/verified/catches
python3 -B -m tools.dex_timing.new_entry_sweep \
  --registration build/new-dex-entry-text-publication/verified/catches \
  --output build/new-dex-entry-text-publication/verified/full --jobs 8
python3 -B -m tools.dex_timing.new_entry_phase_sweep \
  --registration build/new-dex-entry-text-publication/verified/catches \
  --sweep build/new-dex-entry-text-publication/verified/full \
  --output build/new-dex-entry-text-publication/verified/phases --all-input-modes --jobs 8
```

The old Mewtwo failure assertions remain covered, alongside new per-display
description checks; the suite has not been weakened or its snapshot postponed.
`--smoke` runs representative inputs only. Without `--all-input-modes`, the
phase sweep uses all three input modes only for Dusknoir.

Fixtures are local frozen ROM/symbol/manifest/state copies, not repository
assets. The reusable runner rejects incompatible inputs and records ROM,
SameBoy core/source, runner, and state identities. It writes reports, traces,
registration checkpoints and UI images only under ignored `build/` by default.
See the system reference for limits: this is not all-species New Entry playback.
The original Master Ball opening is restored. The phase sweep's optional first
TIMA write is an explicitly synthetic host fixture, not a runtime modification.

**Commit cleanup:** Route 29/30 encounters, trainer parties and the Master Ball
animation match the committed branch baseline. The superseded private page-2
patch builder and its assembly prototype were removed; their historical findings
remain documented. Current animation miss auditing, reusable host runners and
their contract tests are intentionally retained. Generated artifacts remain
under ignored `build/`. No live save or installed emulator ROM was changed.

## Historical Preflight And Captures

The following records describe the pre-implementation fixture builds and
investigation. Their runtime statements and breakpoint addresses are historical.

## Checkpoint And Setup

The addresses below apply to accepted baseline ROM SHA-256
`412527bdecc0c55c90a63b1d268ee7f7812788649e6936035dfd86a437e9dff7`.
Verify the matching ROM/symbols using the [validation guide](dex_scheduler_validation.md#build-identity);
re-resolve the labels after any relink.

### Temporary Capture-Fixture Build

The 2026-09-21 capture-fixture build has ROM SHA-256
`407c4d29e08a47c5e5cce165eb4d171b62d4afbced665938950aa0a21b5d9fd3`.
It changes the Master Ball animation branch target and Route 30 grass encounters,
plus the cartridge checksum. All existing code/data addresses are unchanged.
The Master Ball source is marked
`TEMPORARY NEW DEX ENTRY TEST` in `data/moves/animations.asm`; restore the branch
target from `.StandardBall` to `.MasterBall` after these tests. Guaranteed capture,
item graphics/colors and ordinary-ball behavior are unchanged.

Route 30 has Dusknoir, Metagross, Luxray and Caterpie at level 3, with a 25% share
each in morning/day/night grass. Its 10% overall encounter rate is unchanged.
The seven-slot table size is retained, and Route 29 is unchanged. This block in
`data/wild/johto_grass.asm` is delimited by
`TEMPORARY NEW DEX ENTRY TEST ENCOUNTERS` and explicitly marked
`REMOVE BEFORE COMMIT`. Restore its normal encounters and remove the Master Ball
override before committing production changes.

Master Ball skips catch-odds calculation, then joins the common successful-catch
path before the 20-frame delay and animation. Its original special animation
also reaches `.Shake`, after its additional opening effects. Proposed background
preparation can start at that shared boundary, but no such hook is implemented
yet. Restoring the special opening will still require an ownership/timing smoke
test; this build does not certify future preloading.

With SameBoy closed, both save records were updated to clear caught flags for
Dusknoir, Metagross, Luxray and Caterpie. Only Dusknoir and Luxray were previously
caught. Six bytes changed: four caught-flag bytes and two checksum bytes. Both
main and conversion-table checksums validate; all seen flags, unrelated caught
flags, party/box data and the 48-byte RTC trailer are unchanged.

- Backup: `/Applications/SameBoy/Games/pokecrystal.before-new-dex-entry-tests-20260921-072644-397394.sav`
- Before SHA-256: `f680e9230f5ce81653194cc52238c290a379efb51a9ff21967a4f2858c72471e`
- After SHA-256: `25ff669313ae5b4a43b61a116181052922fada2f2d4f84470263960338603458`

Use the new test ROM and normal Continue, not a pre-edit save state. The build
does not automatically replace the ROM installed in SameBoy. Verify the override:

```text
x/4 $7f:$4024
```

Expected bytes: `f8 01 28 40`.

For one authentic starting state per species, set this before using Master Ball:

```text
breakpoint $3:$6a8c
```

The first instruction is `LD c, $14`, followed by `CALL $0490`. The successful
catch result is already stored; the 20-frame delay and throw animation have not
run. At the stop:

```text
registers
backtrace
ticks
lcd
x/1 $0:$c64e
x/1 $1:$d108
x/1 $1:$d206
x/1 $1:$d208
```

`$c64e` must be nonzero and `$d108` must be `01` (Master Ball). The species bytes
are runtime IDs, not fixed extended species indexes. Save a distinct SameBoy
state at this stop, record species and slot number, then resume. Also note party
capacity and any level-up/move-learning sequence. The headless runner can derive
a second checkpoint at `NewPokedexEntry` from each early capture state; there is
no need to manually gather every intermediate boundary. Its existing Selected
audit needs a registration-specific adapter before it can validate this owner.

### Expanded Route 29 Capture Build

The follow-up 2026-09-21 capture build has ROM SHA-256
`02e49d8db9186ceae4efe2634d19121398a22f0a40eaf30c7e961dd8a9acb224`.
Relative to the four-species fixture above, only Route 29 encounter bytes and
the cartridge checksum changed. Every linked symbol is unchanged, including
the `$03:$6a8c` catch-start breakpoint and the output addresses above. The
ordinary `pokecrystal.gbc` is a capture build, not the private scheduler prototype.

Route 29 now has Mewtwo, Exeggcute, Garchomp and Vibrava at level 3, 25% each in
all three time periods. The overall encounter rate remains 10%, and each period
still has seven slots. The block is marked `REMOVE BEFORE COMMIT`. Route 30's
earlier four-species override and the standard-ball Master Ball animation remain
active and also need to be restored before committing production changes.

Use the same Master Ball catch-start procedure and complete debugger output
block above. One starting state per species is sufficient for this preflight:

| Captured state slot | Species | Added coverage |
| --- | --- | --- |
| 5 | Garchomp | Sampled cry, 35 changed cells after a two-interval hold |
| 6 | Exeggcute | Synthesized cry, 25 changed cells after a one-interval hold |
| 7 | Vibrava | Sampled cry, 6x6 frontpic layout |
| 8 | Mewtwo | Synthesized cry, 36 changed cells after a one-interval hold |

This table records the user's actual encounter/save order, replacing the earlier
suggested slot assignment. Use species names and fixture hashes, not the old
suggestion, when selecting these states for replay.

Keep slots 1-4 for the previous captures. Save each state at `LD c, $14`, before
continuing the catch. Note the species/slot, party capacity, level-ups, learned
moves and any PC/box prompts. Let the registration animation/cry finish without
input; no video or manual per-miss capture is needed for this initial expansion.
The host runner can derive and audit the later registration checkpoint.

After the user confirmed SameBoy was closed, its battery save was backed up and
both save records were updated so these four species are seen but not caught.
Only Mewtwo was previously caught. Four bytes changed: its two caught-flag bytes
and two main-checksum bytes. Main and conversion-table checksums validate; seen
flags, unrelated caught flags, party/box data and the RTC trailer are unchanged.

- Backup: `/Applications/SameBoy/Games/pokecrystal.before-new-dex-entry-tests-20260921-094433-118738.sav`
- Before SHA-256: `ebc0c52b33c3eda0bf62fc6df8af77f29f77b5455f2217783c84c01feff15ec6`
- After SHA-256: `3e603b4a6dd2343effe6c68f583619105ef85104130f3af2572f0ea19a1417c8`

Boot with normal Continue, not an older save state that restores the old caught
flags. The installed SameBoy ROM was not replaced automatically. The original
four-species fixture ROM/states remain frozen separately for reproducible replays.

### Accepted Capture Fixtures And Initial Replay

The four 2026-09-21 captures and their actual SameBoy states were checked against
the capture-fixture ROM above. All stop at `$03:$6a8c`, with the supplied
register values, normal CPU speed, Master Ball selected, four party members,
and the intended species seen but not caught. Caterpie and Metagross both use
runtime ID `$24` in their separate states; their WRAMX-2 conversion tables
correctly resolve that ID to different species. This is not a fixture mismatch.

| State | Species | 16-bit index | Runtime ID | Post-catch branch |
| --- | --- | --- | --- | --- |
| 1 | Luxray | `$0152` | `$13` | Level-up/stat display, no move learned |
| 2 | Caterpie | `$000a` | `$24` | No level-up |
| 3 | Metagross | `$0149` | `$24` | Level-up/stat display, no move learned |
| 4 | Dusknoir | `$013c` | `$11` | No level-up |

State SHA-256 identities, in that order:

```text
8368a435931c058ba76e00c37c6a5709959501cafdc277ec33dd962c2b5c9208
b9461e2260c34413e6422e0ff3437ce00f249af6b3e93df887501dc48d8e7e1d
0289ff9b6b2c260fd028046d1a5597bd1b9831daab7c67f38b8e295b7b0a263a
d32a8648c8b9d4da6dee73e0c7769c74d7d48889238285390c6599e52963d969
```

A temporary **host-only** probe used the unmodified SameBoy core at commit
`213a12ce93d66b105a113debd9396306066a7cfc` to replay each copied state. It pulses
A for 12 display-interval equivalents, releases for 12, and repeats until
`NewPokedexEntry`; all input is released there for uninterrupted registration.
Both recorded level-ups were reproduced. Each replay reached both script ends
and `PokeAnim_Finish`, then ran another 120 intervals with no input. Final page
images were checked to confirm the correct registration species and first
description page. This is not yet per-frame graphics correctness certification.

The probe made no ROM/RAM patches and did not write the live battery save or
original numbered states. It derived separate checkpoints immediately before
`NewPokedexEntry` for faster follow-up tests. Frozen input copies, probe source,
compiler output, registration states, JSON traces, images and the identity
manifest are local-only under ignored `build/new-dex-entry-catches/`.

Initial **software-boundary** timings (normal speed, 70,224 T-cycles per nominal
display interval):

| Species | Owner entry to animation wait entry | Wait entry to `PokeAnim_Finish` | Registration sampled cry |
| --- | --- | --- | --- |
| Caterpie | 3,703,684 T / 52.741 intervals | 8,848,776 T / 126.008 intervals | Synthesized control |
| Luxray | 4,661,260 T / 66.377 intervals | 8,919,116 T / 127.010 intervals | Normal completion |
| Metagross | 4,174,180 T / 59.441 intervals | 19,101,408 T / 272.007 intervals | Normal completion |
| Dusknoir | 5,992,936 T / 85.340 intervals | 17,064,900 T / 243.007 intervals | Empty cache with 69 blocks unplayed |

These two timing columns deliberately exclude preceding catch/EXP/input waits.
The first includes the registration fade, UI setup, frontpic/dictionary loading
and palette work. LCD is briefly disabled during setup, so these are elapsed
cycle equivalents, not counts of visible frames or input-to-reveal measurements.
The second includes animation/cry startup and scene-command overhead; its end
precedes the caller's final map transfer. Do **not** compare it directly against
the authored first-frame-to-final-publication deadline as if the boundaries were
identical. The publication-aware follow-up below supplies that comparison.

Dusknoir reached the shared `$00:$3cb3` empty-cache branch during uninterrupted
registration with active playback, decoded count zero and `$0045` (69) blocks
remaining. No input/cancellation was involved. The in-progress producer later
finished another eight blocks, explaining final WRAMX-4 bytes
`08 3d 00 72 51 20 d7 c8`; this does not undo the underrun. Luxray and Metagross
reached normal stop with zero remaining and never hit the empty-cache branch.
The synthetic Caterpie run does not validate sampled audio through its stale
WRAMX-4 bytes; only actual audio events are interpreted.

These fixtures are sufficient to start the registration-owner baseline audit.
No additional manual debugger capture is required yet. They do not cover the
original special Master Ball opening, move-learning prompts, full-party/PC
handling, early description-page input or exit restoration. Preserve the early
capture states as well as the derived owner-entry states: the level-up branches
are important future tests of graphics ownership during any ahead-of-time prep.

Selected-page playback has passed all-species cold/internal testing, but New
Dex Entry uses a different owner. The previous Selected-test encounter overrides
and dormant A/B branches are removed; Routes 29 and 30 now have the new
capture-fixture overrides above. Existing Selected instrumentation and active Listing warming
remain. Their retained RAM must not be interpreted as this owner's diagnostics.

Use a backed-up test save and normal Continue. Before any separately approved
save replacement, close the ROM so SameBoy cannot overwrite it from memory.
Do not load an older save state that restores pre-edit flags. The earlier
all-seen/Unown correction, backup identities and completed Seviper investigation
are preserved in the [historical setup record](archived/dex-scheduler/dex_seviper_new_entry_testing.md).
There is no need to repeat those edits for an already valid save.

## Registration Baseline Findings

### Rendered-Frame Audit (2026-09-21)

The second host-only probe starts from the four derived registration-entry
states, releases all controls and runs through animation completion. It observes
the actual SameBoy core; it does not patch the game, synthesize instruction costs
or add in-ROM instrumentation. There are no runtime changes in this investigation.

At each normal display boundary it checks both the resident VRAM tilemap picture
and the rendered 56x56 frontpic pixels against independently reconstructed asset
pictures. Publication serials associate those checks with the legacy script's
frame/end commands. Adjacent identical pictures are coalesced when comparing the
observed sequence with the linked exact timeline. Timing is counted in hardware
display intervals, not producer calls or the software `PokeAnim_Finish` boundary.

All 816 inspected playback/tail display intervals contain valid pictures. Every
script publication matches its expected picture, and all four sequences have
the correct order. The common script, finish and audio-stop/empty boundaries
also match the initial probe **exactly in T-cycles** after subtracting owner
entry. The extra observation has not changed the emulated execution schedule.
Display callbacks occasionally arrive at the end of a four-T CPU step; their
timestamps stay within four T of the counted display clock. That callback
granularity is not an extra/missing display interval.

Full-sequence timing, from the first scheduled picture's publication through
the final base-picture restoration, including main animation, 18-interval base
hold and idle animation:

| Species | Exact timeline | Displayed | Excess | Target / actual seconds | Sampled audio |
| --- | ---: | ---: | ---: | --- | --- |
| Caterpie | 111 | 122 | 11 | 1.858 / 2.043 | Synthesized control |
| Luxray | 92 | 120 | 28 | 1.540 / 2.009 | Complete |
| Metagross | 228 | 265 | 37 | 3.817 / 4.437 | Complete |
| Dusknoir | 174 | 235 | 61 | 2.913 / 3.935 | Underrun, 69 blocks unplayed |

Seconds use 70,224 T per display interval at 4,194,304 T/sec. They are not
input-to-page-open measurements. The target uses the existing exact timeline's
script/repeat-exit accounting, not a newly invented speed setting. Dusknoir's
**main animation alone** takes 163 intervals against the established 107-interval
target (2.729 versus 1.791 seconds). Its repeated three-interval poses commonly
remain on screen for five intervals. The longer total is not missing images or
an animation dictionary underrun: the correct images are held too long.

### Why The Legacy Loop Falls Behind

The relevant call chain is:

1. `NewPokedexEntry.AnimateFrontpicFrame` calls `SetUpPokeAnim`.
2. `PokeAnim_DoAnimScript` decrements a wait counter once per foreground call,
   rather than accounting for elapsed hardware display intervals.
3. On a picture change, `PokeAnim_GetFrame` places the base picture, scans a
   bitmask to count changed tiles, copies the tile-index list, then scans again
   and computes destination coordinates for each changed tile.
4. Even when the picture is unchanged, the caller pads/copies the entire 20x18
   screen tilemap into a 32x18 (576-byte) transfer buffer and queues its upload.
5. `WaitDMATransfer` calls `DelayFrame`. The sampled-cry refill runs on the return
   from that frame wait. Long preceding map work can span additional display
   intervals before this service opportunity is reached.

The full animation dictionary is already resident in VRAM before this loop.
`PokeAnim_GetFrame` is expensive **tilemap construction**, not graphic tile
decompression or dictionary uploading. No new tile-streaming producer is needed
to explain or address this particular bottleneck.

Observed inclusive wall-clock costs, in normal-speed T-cycles (interrupt time is
included):

| Operation | Caterpie median | Luxray median | Metagross median | Dusknoir median |
| --- | ---: | ---: | ---: | ---: |
| `PokeAnim_GetFrame` | 41,552 | 103,772 | 87,052 | 124,492 |
| Full-screen tilemap padding/copy | 26,712 | 29,940 | 26,712 | 26,712 |
| Actual queued map-transfer routine | 1,228 | 1,228 | 1,228 | 1,228 |

The last row is the actual `DMATransfer` call including its small instruction
overhead, not the surrounding wait or padding. Dusknoir's largest `GetFrame`
call is 133,400 T, almost two display intervals, before the full-screen copy and
wait. Its median bit-counting and bitmask-application subcalls are 31,500 T and
78,956 T respectively. These are nested within `GetFrame`, not additional
independent charges. A typical eight-block audio refill costs another 25,508 T.

Thus the expensive portion is CPU map preparation plus repeated whole-screen
work and its scheduling, not the raw GDMA transfer. During Dusknoir's playback
the wrapper completes 179 full-screen map copies before `PokeAnim_Finish`, for
only 35 script-frame/end publications. Held pictures do not need this work.

### Dusknoir Audio Failure

This is a genuine uninterrupted-playback underrun, not rapid paging or input
cancellation. Playback starts with 557 blocks total and 32 decoded. Before the
failure, 57 completed refills produce another 456 blocks. Therefore only 488
blocks play, leaving 69. A 58th service starts but does not publish a decoded
block before the timer finds the cache empty.

The final sequence, in T-cycles relative to registration owner entry:

| Boundary | T | Decoded blocks / playback blocks remaining |
| --- | ---: | --- |
| Previous refill returns | 12,124,000 | 14 / 83 |
| Next `GetFrame` starts | 12,127,996 | 14 / 83 |
| `GetFrame` returns | 12,259,220 | 4 / 73 |
| Full-screen padding starts | 12,260,680 | 4 / 73 |
| Padding returns | 12,292,180 | 1 / 70 |
| Next audio service starts | 12,306,812 | 0 / 69 |
| Timer takes empty-cache branch | 12,313,400 | 0 / 69 |
| In-progress service returns after stop | 12,330,484 | 8 / 0 in HRAM |

The eight late blocks do not rescue playback. WRAMX-4 still has 61 compressed
blocks plus eight decoded/unplayed blocks, matching the 69 lost at the stop.
The maximum service-start gap is 212,360 T (3.024 intervals), and comparable
gaps recur through the rapid pose changes. Completed runtime production averages
about 5.125 blocks per interval up to the stop, below consumption near 5.46.

Only about 4.4% of that active span is actual CPU HALT time. There is not a large
unused-idle budget in the current path. However, much of its busy time is the
avoidable map work above. Both work cost and refill placement matter; the result
does not justify simply adding unbounded refill calls or increasing global
startup prefill. Luxray and Metagross complete with the same 32-block startup;
their different distribution of frame work allows their reserves to survive.
A single worst service gap is not sufficient to rank a whole sequence.

### Startup Is A Separate Bottleneck

`_NewPokedexEntry` enables the LCD and waits for the background before calling
`GetAnimatedFrontpic`. Consequently its `Get2bpp` calls take the queued
`Request2bpp` path. The entire dictionary is decoded and uploaded synchronously
before animation initialization, using multiple frame-sized requests.

| Species | Whole `GetAnimatedFrontpic` | LZ decompression | Inside queued `Request2bpp` calls | Frame waits inside loader |
| --- | ---: | ---: | ---: | ---: |
| Caterpie | 1,188,800 T | 65,112 T | 1,068,468 T | 16 |
| Luxray | 2,172,184 T | 317,796 T | 1,709,044 T | 25 |
| Metagross | 1,678,192 T | 170,080 T | 1,397,884 T | 21 |
| Dusknoir | 3,503,956 T | 501,396 T | 2,738,836 T | 40 |

Request time includes waiting, so it is not a measure of VRAM copy bandwidth.
For Dusknoir, the whole loader costs about 49.9 interval equivalents, of which
39.0 are inside queued upload requests and 7.14 inside LZ decoding. Nested frame
waits must not be added again. These costs occur before the registration cry
starts, so the sampled-cry startup prefill is not their cause.

This points to a registration-owned bulk/bounded upload path during hidden page
staging as a separate optimization. Simply keeping the LCD off longer deserves
caution: it changes VBlank/music servicing and is not automatically a free win.
Ahead-of-time preparation during the common post-ball/caught-jingle path remains
an option, but has not been validated by this baseline. Neither VRAM nor WRAM
contents may be assumed to survive the intervening level-up/stat displays.
The preserved Luxray/Metagross early checkpoints cover precisely that risk.

### Recommended Direction And Limits

Use a **registration-specific resident-dictionary owner**, reusing the existing
exact timelines and generated frame plans rather than copying Selected Mon's
two-slot tile producer wholesale:

1. Keep the full dictionary resident. Build the next 7x7 map from generated
   plans instead of the legacy repeated bitmask/coordinate scans.
2. Anchor animation events to the hardware display clock, track preparation
   separately, and publish prepared maps at their exact deadlines.
3. Update the frontpic region at publication, not all 576 screen bytes on every
   hold. Establish stable frontpic attributes once where possible; coordinate
   cursor/text/page updates explicitly instead of relying on the old full-map
   transfer as an incidental UI update mechanism.
4. Budget bounded sampled-audio service during each display interval. Keep the
   global 32-block startup/eight-block refill policy unchanged for this trial.
5. Treat initial dictionary loading as its own measured step. First eliminate
   unnecessary queued upload latency locally; evaluate earlier catch-time work
   only with explicit ownership across EXP, level-up and registration.

The measurements show substantial avoidable work, not proof that normal-speed
hardware cannot meet these deadlines. They also do not certify a future owner
before it exists. Next preflight should cost the concrete map builder,
publication, audio and UI work together, then replay the same frozen states
through complete sequences and description/exit cases. Existing generated ROMX
assets appear reusable; exact code/state costs require that preflight.

No additional user capture or second hardware emulator is required for the
next investigation. The current SameBoy-core adapter supplies real execution,
pixels, deadlines and audio results; an owner-specific adapter to the existing
host timing model can be added for costed experiments if useful. Selected Mon's
old calibration must not be treated as certification of this different owner.

Local reproduction and detailed evidence are under the ignored fixture folder:
`trace.py`, `registration_trace.c`, `analyze_trace.py`, per-species `*-trace.jsonl`
and `registration-baseline-audit.json`. These are diagnostic artifacts, not new
production build dependencies. The authored timeline/order, rendered pictures,
unchanged baseline boundaries and audio-block accounting are asserted by the
analysis script. Broader species/phase/input coverage remains future validation.

## Executable Resident-Owner Preflight (2026-09-21)

### Scope And Method

This is a **host-only executable preflight**, not a production implementation.
RGBDS assembled a concrete resident-dictionary owner and, separately, a bounded
startup uploader into private copies of the frozen ROM. The same normal-speed
SameBoy core replayed the four derived registration-entry states. The installed
ROM, original saves/states, game source and production build outputs were not
changed. The only tracked changes from this pass are this documentation update;
the existing Master Ball/Route 30 testing edits remain untouched.

Unlike an assumed instruction-cost discount, these runs execute the actual
draft SM83 instructions, interrupts, sampled-audio player and hardware transfers.
They reuse the prior host runner and actual-core timing oracle; this is not a
second hardware emulator or certification inherited from Selected Mon's model.

Two variants were tested independently:

- `resident`: new publication/preparation owner; original dictionary loader.
- `resident-bulk`: same owner, plus aligned, at-most-32-tile queued GDMA chunks
  during registration page setup. No catch-time preparation or larger audio
  prefill is introduced.

Each variant runs four species in three conditions: uninterrupted playback;
A five intervals after the first publication to change description pages; and
that same A followed by B at interval 15 to exit early. **All 24 final replays
pass.** The observer checks physical VRAM and rendered pixels without issuing
bus reads that could advance the PPU. Assertions cover every event's picture,
hardware display interval, audio completion, early-page responsiveness and owner
release. In total, 2,732 playback/tail display intervals were checked with no
frontpic mismatch. Early exits deliberately cancel the remaining animation;
only publications before cancellation are required to match the timeline.

The page-change test reaches the second input loop within 5-6 display intervals,
while animation deadlines continue to be met. The exit test reaches the real
registration return, with the owner disabled and prior status restored. The
combined variant also snapshots both description pages and the return boundary;
non-frontpic/non-cursor tilemap cells match the backing map, including the page
number changing from tile `$57` to `$58`. These are focused checks, not exhaustive
UI/palette certification. The cry is not forcibly cut off on early exit in this
draft; it follows the existing caller's behavior and completes in these runs.

### Animation And Audio Results

Intervals are measured from the first scheduled picture to final base-picture
restoration, including main animation, the 18-interval base hold and idle:

| Species | Original displayed | Authored target | Both preflight variants |
| --- | ---: | ---: | ---: |
| Caterpie | 122 | 111 | 111 |
| Luxray | 120 | 92 | 92 |
| Metagross | 265 | 228 | 228 |
| Dusknoir | 235 | 174 | 174 |

Every individual event matches its authored interval, not merely the final
total. Dusknoir's main sequence therefore also meets 107 intervals, rather than
the original 163. All publications complete in VBlank; the latest observed
completion is LY 152. The smallest observed prepared-map lead before its due
display boundary is 156,160 T (2.22 intervals), measured after the map-builder
returns and excluding the separately armed
first publication. That is observed headroom for these fixtures, not a universal
minimum for all species or entry phases.

The global sampled-cry policy is unchanged: 32 startup blocks, up to eight per
runtime refill. Dusknoir completes all 557 blocks (32 startup + 525 produced);
Luxray completes 508 (32 + 476); Metagross completes 612 (32 + 580). No empty-cache
branch is taken in any final replay. Caterpie remains the synthesized control.

For uninterrupted Dusknoir in the owner-only run, the maximum service-start gap
falls from 212,360 to 73,100 T (3.024 to 1.041 display intervals). Actual HALT idle
time during its cry rises from about 4.4% to 34.3%. This is evidence that removing
avoidable map work restores refill opportunities, without changing audio format,
decoder, refill quota or synchronous prefill. It is not a promise that every
other owner or cry-start phase has the same reserve.

### Concrete Owner And Measured Cost

The draft keeps the full animation dictionary in its current VRAM layout:

1. Reuse the existing metadata initializer, exact timeline and generated frame
   plans. Translate each plan's source indices to the resident layout, including
   padded small frontpics and the loader's skipped tile `$7f`.
2. Build one pending 49-cell tilemap in existing WRAMX-2 animation storage. No
   graphic tiles need decoding/uploading during playback, so the plan's
   high-water byte is skipped by this owner, not removed from shared metadata.
3. Publish the ready 7x7 map in VBlank when the shared display counter reaches
   its deadline. First/final publications include the 49 frontpic attributes.
   Other publications leave those stable attributes alone.
4. After publication, acknowledge it in the foreground, synchronize the backing
   map, and prepare the next event. Never advance the publication deadline based
   on how many producer calls occurred.
5. Service preparation after the existing audio service on `DelayFrame` return,
   gated by this owner's value in the existing `hVBlank` byte. This also covers
   description-page `WaitBGMap` calls. Preserve BC/DE/HL at this boundary.
6. Explicitly handle cursor publication, page-map updates, natural completion
   and early cancellation; restore the prior VBlank/OAM ownership before exit.

Uninterrupted owner-only wall-clock T-cycle costs, including intervening
interrupts where applicable:

| Operation | Caterpie | Luxray | Metagross | Dusknoir |
| --- | ---: | ---: | ---: | ---: |
| Legacy frame build, median | 41,552 | 103,772 | 87,052 | 124,492 |
| Draft map build, median | 5,844 | 12,324 | 8,100 | 18,576 |
| Draft map build, largest | 8,596 | 24,156 | 12,724 | 20,208 |
| Foreground owner service, largest | 12,612 | 26,560 | 15,568 | 24,280 |

The largest publication routine is 3,304 T, including map plus first/final
attributes. Normal map-only publication is cheaper. Admission distinguishes
these cases: first/final work must begin before LY 146; map-only work before
LY 149. Cursor work is also guarded against being entered outside the safe
VBlank portion. The following sound/joypad operations remain in the ordinary
VBlank handler; an animation publication takes priority over its other graphics
work for that interval.

Static resident-index reconstruction additionally passes **2,121 pictures across
all 399 linked species/forms**. The largest plan has 49 pairs, the longest event
hold is 65 intervals, and the largest resident tile ID is 247. Thus the current
data fit the scratch capacity and byte-clock comparison range. This static audit
does **not** prove runtime deadlines/audio for all 399 forms.

### Separate Startup Improvement

The owner by itself essentially preserves startup cost (only 56-88 T of wrapper
overhead at the measured boundary). The second variant replaces small queued
tile requests during page setup with up to 32 tiles per VBlank. It preserves
normal interrupt/music/input servicing and does not extend an LCD-off section.

There is an important alignment requirement: `sPaddedEnemyFrontPic` starts at
`$00:$a001`, which cannot be used directly as a GDMA source. The draft copies
each unaligned chunk into existing SRAM scratch at `$a320-$a51f` first. That
512-byte staging region is beyond the padded picture and within the already
allocated `$a000-$a5ff` scratch union. No save data, allocation or dictionary
contents are displaced. Already aligned WRAM dictionary chunks use direct DMA.
The results below include this staging cost.

| Species | Original dictionary load | Batched dictionary load | Page-setup saving |
| --- | ---: | ---: | --- |
| Caterpie | 1,188,800 T | 485,400 T | about 10 intervals / 167 ms |
| Luxray | 2,172,184 T | 1,048,744 T | about 16 intervals / 268 ms |
| Metagross | 1,678,192 T | 696,036 T | about 14 intervals / 234 ms |
| Dusknoir | 3,503,956 T | 1,468,480 T | about 29 intervals / 486 ms |

Page-setup saving compares `NewPokedexEntry` entry to its first input/animation
wait, rather than summing nested routine costs. Whole-owner startup becomes
3,001,616 / 3,537,764 / 3,191,016 / 3,956,444 T respectively (Caterpie, Luxray,
Metagross, Dusknoir). These are not ball-throw-to-page timings or input latency.
This optimization does not hide the remaining LZ decompression. It also does
not depend on a buffer surviving the intervening level-up screen: all loading
still begins inside registration.

### Footprint And Integration Requirements

Assembled **gross draft** additions, before replacing old wrappers or integrating
into the link layout:

| Resource | Resident owner | Optional startup uploader | Combined |
| --- | ---: | ---: | ---: |
| ROM0 wrappers | 74 bytes | 18 bytes | 92 bytes |
| ROMX code/local table | 714 bytes | 117 bytes | 831 bytes |
| New WRAM0 / WRAMX / HRAM / VRAM / SRAM allocation | 0 | 0 | 0 |
| New per-species metadata | 0 | 0 | 0 |

The owner aliases existing legacy animation fields, the 49-byte frame map and
98 bytes of the 360-byte temporary tilemap in WRAMX-2. The uploader temporarily
uses the 512-byte SRAM scratch region described above. This is reuse with an
explicit owner/lifetime, not a claim that the work needs no storage. No padding
or extra HRAM byte is used; the draft distinguishes the owner with existing
`hVBlank` bits and saves/restores its previous value.

The frozen link map has 656 bytes free in ROM0 and 2,777 bytes free in timeline
bank `$a5`; these gross additions fit without repacking or adding another data
bank. The private prototype uses empty bank `$a6` for isolation, which is not a
recommendation to dedicate a bank in the production link. Exact net production
cost must be re-linked and remeasured after integration. The legacy animation
engine remains needed by other callers and cannot be removed globally.

Two implementation hazards were caught and corrected in this preflight: a
`DelayFrame` service clobbering the C register used by `DelayFrames`, and direct
DMA rounding the unaligned padded base down to `$a000`. The final 24 replays,
not the earlier drafts, are the results reported above. Keep explicit register
contracts, source-alignment assertions and the early-input cases in regression.

For production, scope the new owner and bulk upload to **New Dex Entry only**.
The private uploader experiment patches the relevant generic loader call sites
but replays only registration-entry checkpoints; it is not evidence that those
patches can safely be shipped globally. Use a registration-local entry/adapter,
retain full ownership restoration, and rerun from the original pre-catch states
through EXP/level-up, registration and return after the source integration.
Actual Master Ball effects were temporarily replaced in the captured build, so
restoring and testing that animation also remains part of final integration.

Recommendation: the resident owner is supported by the executable evidence, and
the scoped startup uploader is a worthwhile separable addition. Earlier
ball/jingle preparation is not required to achieve the measured deadlines or
the measured startup reduction; defer it until after this narrower path works
in the real build. No more user captures are needed for the next implementation
step. Broad species/phase/button-boundary regressions are still required before
calling the new production owner fully validated.

Local evidence/reproduction remains in ignored `build/new-dex-entry-catches/`:
`resident_preflight.asm`, `preflight.py`, `preflight-manifest.json`, `trace.py`,
`registration_trace.c`, `analyze_preflight.py`, `registration-preflight-audit.json`,
`resident-mapping-audit.json`, and the per-variant traces/screens. Run `trace.py`
with each `--variant resident|resident-bulk` and `--input none|description|exit`,
then `analyze_preflight.py`. The manifest records private-image identities; none
of those images is a new user testing build.

### Expanded Preflight Results (2026-09-21)

The four additional catch states were copied into ignored
`build/new-dex-entry-expanded/` with their text captures and matching Route 29
fixture ROM/symbols. The original four-species fixture set was not overwritten.
All registers in the text captures match the actual states at `$03:$6a8c`;
Master Ball is selected, normal CPU speed is active, and every target is seen
but not caught. Runtime IDs resolve through each state's conversion table:

| Slot | Species | Index / runtime ID | Party before catch | Replayed branch |
| --- | --- | --- | ---: | --- |
| 5 | Garchomp | `$0160` / `$24` | 4 | Level-up, added as party member 5 |
| 6 | Exeggcute | `$0066` / `$25` | 5 | Level-up, added as party member 6 |
| 7 | Vibrava | `$0124` / `$26` | 6 | No level-up, sent to PC |
| 8 | Mewtwo | `$0096` / `$12` | 6 | No level-up, sent to PC |

State SHA-256 identities, in that order:

```text
b5107cf9cd393cca31111d37d55f8c829afacbe65160aadc0108192ca647587d
13a455041d310b2fcc6d995c442421394548fe3920e27216a6a0ed0deb5615b7
91fdffe017c593e98c75e3ba13578ef419760bf2ff81c84e73711c32e2366db5
f20d0e767780930358d08676ae79f05166d2211a7865cb503ce4a89414510bbe
```

The same unmodified SameBoy core and the same assembled resident-owner draft
were used. No new scheduler correction, speed change, extra allocation, metadata
change or increased audio prefill was needed. The private images differ from the
earlier prototype images only in the new base ROM's Route 29/checksum bytes.
Their identities are:

- Resident owner: `3954868d3a0148afd33c9120fbffff579774ae82572ff859afb9a1ff9ceacc5a`
- Resident owner plus bulk startup: `88c87081959b70042d43f42cfd07dba721545c58933cb80e39a29b1be41ad8eb`

Full-sequence timing uses the same first-picture-to-final-base-restoration
display boundaries as the original preflight. It includes main animation,
the 18-interval base hold and idle animation, not catch or page-setup time:

| Species | Authored target | Current game | Resident owner | Resident + bulk startup |
| --- | ---: | ---: | ---: | ---: |
| Garchomp | 110 | 131 | 110 | 110 |
| Exeggcute | 113 | 144 | 113 | 113 |
| Vibrava | 83 | 106 | 83 | 83 |
| Mewtwo | 111 | 149 | 111 | 111 |

Every individual publication in both prototypes meets its authored deadline,
not merely the total duration. This includes the one-interval Exeggcute/Mewtwo
holds and the two-interval Garchomp case. The baseline rendered-picture audit
checked 603 display intervals with no invalid pictures; it is holding correct
pictures too long. Its software frame/end/audio boundaries also exactly match
the initial catch-to-registration probe after subtracting owner entry.

The two prototype variants were each tested with no input, A at interval 5,
and A at 5 followed by B at 15: 24 runs and 1,980 checked animation display
intervals. All rendered pictures and tilemap reconstructions match the assets,
with zero deadline misses. Description changes preserve timing and take 5-6
intervals to return to their wait loop. Early exit cancels the owner and restores
its previous VBlank selection; the sampled cry is allowed to finish as before.
Vibrava's 6x6 picture padding/layout also passes. Combined with the original
four species, the private-owner suite now covers eight species, 48 runs and
4,712 checked display intervals. This is not an all-species runtime proof.

Minimum measured next-map preparation lead in the uninterrupted bulk-startup
runs, measured to the deadline's display boundary:

| Species | Lead, T-cycles | Display-interval equivalents |
| --- | ---: | ---: |
| Mewtwo | 38,720 | 0.55 |
| Exeggcute | 39,876 | 0.57 |
| Garchomp | 87,144 | 1.24 |
| Vibrava | 160,432 | 2.28 |

The minimum across all 24 runs is also 38,720 T. The latest publication finishes
on LY 152, still in VBlank. These are measured margins for the supplied states
and input patterns, not universal worst-case guarantees. Map construction is
still foreground work; only completed maps are published at the display
deadline. There is no need for a second producer to meet these tested cases.

Sampled audio retains the global 32-block startup prefill:

| Species | Total blocks | Current-game outcome | Both prototype outcomes |
| --- | ---: | --- | --- |
| Garchomp | 306 | Complete | Complete, no empty-cache branch |
| Vibrava | 217 | Underrun with 17 unplayed | Complete, no empty-cache branch |

Garchomp produces 274 runtime blocks and Vibrava 185, which, with the initial
32, exactly account for each complete cry. Maximum service-start gaps in the
uninterrupted bulk runs are 73,100 and 73,104 T respectively, about 1.04 display
intervals. Synthesized-cry controls do not interpret stale sampled-audio cache
bytes as results. As with Dusknoir in the original four-species suite, removing
the legacy animation-loop delay is sufficient to fix the observed Vibrava
underrun in these replays without changing the sampled player.

Optional bulk startup reduces owner-entry-to-first-wait cost by another
12-18 display-interval equivalents in these four fixtures:

| Species | Saving, T-cycles | Approximate elapsed saving |
| --- | ---: | ---: |
| Garchomp | 1,263,976 | 301 ms |
| Exeggcute | 912,960 | 218 ms |
| Vibrava | 906,464 | 216 ms |
| Mewtwo | 842,632 | 201 ms |

These are page-setup savings, not reduced authored animation duration or
ball-throw-to-page timings. All decompression/upload work still starts inside
registration; the preflight does not add work to the ball animation or jingle.

A further 12 host-only catch-flow runs start from the actual early states,
using the baseline and both private variants. They reproduce the two level-ups,
wait for animation completion, advance both descriptions, decline nicknames
with B, and reach `PokeBallEffect.return_from_capture`. The resulting party
counts, last party species, box counts/first species, caught flag, VBlank owner,
frame counter, map-animation flag and scroll position match the baseline in
each case. Vibrava becomes the first boxed mon; Mewtwo becomes the second,
with the party remaining full. This verifies the normal non-full-PC catch
return branch, not full-box handling, move learning or nickname entry itself.

No further user captures are needed before source integration. The gross cost
estimate and narrow-owner recommendation above are unchanged. Production must
still scope upload changes to registration, preserve register/ownership
contracts, rerun the retained fixtures against the linked implementation,
restore/test the original Master Ball animation, and perform broader regression.
The live save, original numbered states, installed ROM and production scheduler
were not changed by these replays.

Local output includes `manifest.json`, `registration-baseline-audit.json`,
`registration-preflight-audit.json`, `follow-through-audit.json`, copied states,
derived owner checkpoints, per-run traces and screenshots. The shared private
drivers in `build/new-dex-entry-catches/` now accept `REGISTRATION_OUT`,
`REGISTRATION_ROM_SHA256`, `REGISTRATION_SPECIES` and, for initial capture replay,
`REGISTRATION_CASES`. The expanded values are:

```text
REGISTRATION_OUT=build/new-dex-entry-expanded
REGISTRATION_ROM_SHA256=02e49d8db9186ceae4efe2634d19121398a22f0a40eaf30c7e961dd8a9acb224
REGISTRATION_SPECIES=garchomp,exeggcute,vibrava,mewtwo
REGISTRATION_CASES=[[5,"Garchomp",352],[6,"Exeggcute",102],[7,"Vibrava",292],[8,"Mewtwo",150]]
```

With those variables, run `trace.py --variant baseline`, both prototype variants
with the three input modes above, then `analyze_trace.py` and
`analyze_preflight.py`. `build/new-dex-entry-expanded/follow_through.py` runs the
catch-storage checks from the frozen copied states. Initial `run.py` copies
from the installed ROM/numbered states and should not be rerun after those have
changed; its input identities are recorded in the manifest.

## What Is And Is Not Shared

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

## Initial Suite

Start with three uninterrupted registrations each for Dusknoir and Metagross,
plus a synthesized control such as Caterpie. Add one each of Luxray, Weavile
and Groudon once those establish the baseline. Test early A-to-description-2
and B/exit separately, with species, timing and audio ownership recorded.
Seviper's Selected script-fix retest has already passed; it is not a prerequisite
for this separate owner timing suite.

Registration requires the species to be **uncaught**, not unseen. The two
four-species test-save edits above provide this setup without changing seen
flags. Current encounter overrides are Routes 29 and 30, described above. This procedure does not
authorize further save edits or restoration of old testing encounters. Preserve
an uncaught starting state per case so repeated captures test registration rather
than only battle.

## Boundary Captures Without New ROM Instrumentation

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

## After The Baseline

Compare the legacy script boundaries, shared sampled-cry state and uninterrupted
video before proposing runtime changes. If per-frame timing remains ambiguous,
add an owner-safe host trace or separately approved instrumentation, not reads
of Selected-only counters. Keep the reusable model/auditing sources.

Instrumentation cleanup and Listing warming removal remain separate later
work. Exclude raw captures, saves/states, compiled runners and copied cartridges
from commits; use ignored `build/` for generated output.
