# New Dex Entry Input-Timing Regression

Updated 2026-09-21. The acknowledged description publisher is integrated on top
of the fixed-rectangle picture-publication correction. It resolves all eleven
Mewtwo text-refresh reproductions without stretching animation holds or changing
audio. **All 8,570 real-input cases pass**, including per-display description
atomicity and exact animation deadlines. The user accepts the manual result,
with a slight perceived text/page-number offset noted below. The separate
battle-cry issue is deferred.

Current evidence is first. Earlier failures and prototypes below are historical,
not descriptions of the current runtime. The root ROM was rebuilt; no live save,
installed emulator ROM or original capture state was changed.

Companions: [system contract](new_dex_entry_animation_scheduler.md),
[manual testing and breakpoints](dex_new_entry_testing.md).

## Acknowledged Description Publication

```text
ROM SHA-256 d736de2d8215c8365dd8ec8a5d2f01ff7e3cefdf387ed8f4b510015d3f018675
SYM SHA-256 4c26771293d8a3d119f7da55b0ae66b33f4fe8e0214b34e00510fa9675cd4a86
MAP SHA-256 691de7b2c15ec1b74516b8324f4ca8b10aa153b1f4048e4451c0b66c98be6e7e
```

### Scoped Runtime Change

`NewDexEntry_DisplayPage2` still builds the second description in WRAM, with its
existing foreground animation-service boundaries. Once all source cells are
ready, it sets bit 6 in the existing animation flags and waits through
`DelayFrame` for an actual publication acknowledgement. The fixed page-2
`WaitBGMap` call is removed; shared BG-map timing is unchanged.

The New Entry VBlank owner gives picture publication priority, then checks live
LY again before a disjoint **91-cell text/page-number copy**. It admits only
LY 144-148 and clears the request after the final store. A pending picture ACK
does not prevent this independent rectangle from publishing. If animation has
ended, the page borrows/restores this owner solely for text; if the final picture
ACK coincides with pending text, cleanup retains ownership until both finish.
No partial description becomes visible and no next animation deadline moves.

The linked last text store finishes **1,984 T** after its LY read. Even the end
of LY 148 leaves **2,280 T**, a **296-T** write margin. Original picture-store
bounds are unchanged. With no text request the extra publication-tail check
costs 84 T; broad full-core regressions cover that phase change too.

Cost versus the cleanup ROM below: **405 net ROMX bytes**, no added ROM0, WRAM0,
WRAMX, HRAM, SRAM or VRAM. The owner grows 408 bytes in bank `$a5`, while the
caller shrinks three bytes in `$3e`. Bank `$a5` retains 1,230 free bytes; ROM0
retains 582. No new metadata/bank or extra flag byte is required. The current
animation-miss breakpoint is `$a5:$775e`; audio remains `$00:$3cb3`.

### Paired Mewtwo Results

Read-only replay of each ROM with its own matching registration checkpoint:

| A offset from first picture | Previous input-to-complete-text intervals | New intervals | Previous mixed-text displays | New mixed displays |
| --- | ---: | ---: | ---: | ---: |
| 32 | 10 | 3 | 6 | 0 |
| 33 | 9 | 3 | 6 | 0 |
| 34 | 11 | 3 | 6 | 0 |
| 35 | 10 | 3 | 6 | 0 |
| 36 | 9 | 3 | 6 | 0 |
| 37 | 11 | 3 | 6 | 0 |
| 38 | 10 | 3 | 6 | 0 |
| 39 | 9 | 3 | 6 | 0 |
| 40 | 10 | 3 | 5 | 0 |
| 41 | 9 | 3 | 5 | 0 |
| 43 | 9 | 3 | 4 | 0 |

At the hardware display rate, 9-11 intervals are about 151-184 ms, versus about
50 ms for 3. All cases retain Mewtwo's exact **111-interval** animation sequence.
The observer checks physical tilemaps and rendered text every display, beginning
before drawing; old and new complete rectangles are the only accepted states.
It still performs the earlier whole-UI snapshots. These results do not come
from postponing a snapshot until the UI eventually catches up.

Evidence: `build/new-dex-entry-text-publication/mewtwo-comparison/report.json`,
with before/after traces and ROM/state hashes. The `before/` folder preserves
the prior ROM, symbols, map and changed source files as a local rollback record.

### Broader Regression

Current observer results live under `build/new-dex-entry-text-publication/verified/`:

- **8 authentic catch flows / 24 representative registration variants** pass,
  including level-up/stat prompts, party/PC return and 2,356 picture displays.
- **20 species / 8,570 input cases pass all checks**, with 1,207,645 picture
  displays, 5,571 complete animations, 3,260 restored returns and 7,104 sampled
  cries completing with correct block accounting.
- **6,492 description advances / 579,345 description displays** have no mixed
  or reverted text. Accepted page taps take 2-5 intervals from input to visible
  completion, predominantly 2-3; already-prepared text takes 2-3. Held input
  beginning before screen setup includes that setup in its input latency.
- All twenty uninterrupted baselines keep the same first-publication interval,
  publication count and total duration as the preceding build. Quicker page-2
  acknowledgement permits some B inputs earlier, changing the number of natural
  completions versus early returns without changing animation deadlines.
- **56 unit/contract tests**, 399 timeline structures and all **399 resident
  assets / 2,121 pictures** pass. Negative controls reject mixed/reverted text,
  missing ready/completion observations, leaked owners, missed deadlines and
  incorrect picture pixels. Adding a later wait event cannot alter the measured
  input-to-visible latency.
- **9,600 / 9,600 synthetic timer-phase cases** pass with **1,122,800 picture
  display checks**. All sixteen sampled species now run completion, description
  advance and A-then-B exit at every first-overflow offset, not just Dusknoir.
  Every animation, audio, text, cleanup and exact PPU-clock check passes.
  This is a 200-offset, 64-T phase grid, not exhaustive 4-T hardware coverage.

### Observer Clock Investigation

The first expanded 9,600-case phase run had two clock-assertion failures:
Yanmega phase 182 with A, and A then B. Both had correct picture/text, animation
deadlines, owner cleanup and audio, but one CPU-clock callback timestamp was
six T later than expected. The report is retained under `phases/`, not erased.

SameBoy's `GB_advance_cycles` advances `cycles_since_run` for a whole batch
before `GB_display_run` consumes it. At a normal-frame callback the positive
`display_cycles` field is the unconsumed portion, in 8 MHz ticks. Observing
`ppu_t = (callback_ticks - display_cycles) / 2` removes that batching remainder,
not actual game execution or display time. The first observed frame had 2 ticks
remaining; the outlier had 14. Their six-T difference explains the entire error.

Replaying both cases with this additional read-only field reproduces **every
previous trace record identically** after removing the new clock fields. Their
PPU boundaries are exactly 70,224 T apart. The audit now requires zero drift in
`ppu_t`, rather than widening the old four-T CPU-callback tolerance. A unit
negative control rejects even one T of actual PPU drift. Evidence:
`build/new-dex-entry-text-publication/ppu-clock-control/report.json`.
The entire authentic-catch, input and expanded phase suites were rerun with this
strict boundary check; final reports are under `verified/`. No game instruction
or timing threshold changed in response to the observer-only discrepancy.

### Manual Acceptance

On 2026-09-21, the user accepted the description fix. They perceived the text
updating slightly before the page number, estimating one or two frames, and
explicitly considered that acceptable. This is an unmeasured manual observation,
not reproduced by the automated fixtures above; those passing results do not
disprove it. Retain it as an accepted presentation caveat, with no further
runtime change or mandatory manual pass requested for `NEWDEX-UI-01`.
Instrumentation remains in place. The separate battle-cry issue remains open.

## Previous Manual Acceptance And Commit Cleanup

The following cleanup and picture-copy results precede the description fix
above. Their build identities and previously open UI failure remain historical.

After the full input/phase sweep, the user repeated the focused manual targets
several times with different input permutations. Neither animation nor sampled
cry miss breakpoint was hit on the New Dex Entry page. This closes the requested
manual confirmation of `NEWDEX-ANIM-01`; it does not close `NEWDEX-UI-01` or the
separate battle-cry issue. No additional manual pass is required for this commit.

Route 29/30 encounters are restored to the committed branch baseline. Trainer
parties and the original Master Ball animation already match that baseline.
The superseded page-two private patch builder and assembly prototype are removed;
their findings below remain historical evidence, not alternate runtime paths.
Instrumentation, maintained host runners and tests remain intentionally present.

```text
Cleanup ROM SHA-256 e8358d4888e0964cb43eda4c2bda73b2a96cfae8b0fcc227f10133a983e6f73e
SYM SHA-256         e58bf14d9f201277161ece5ef3b84f4193f07260dfc300d7570d0716e3e96cb9
MAP SHA-256         c07fd89da7e12c21b23f849066f91802fe4f74a43593081092d79a9f67b1dbe4
```

Binary comparison against the accepted faster-copy build finds exactly **131
changed bytes**: 129 in the two encounter tables and two cartridge checksum
bytes. All code, symbols, allocations and breakpoint addresses are identical.
The full input/phase evidence below remains bound to its original test ROM;
cleanup replays are stored separately under `build/new-dex-entry-commit-cleanup/`.
No save, installed emulator ROM, commit or push is modified by cleanup.

Cleanup verification passes: the rebuilt ROM's **8 authentic catches / 24
registration variants / 2,356 display checks**, all **50 contract tests**, and
**399 timeline structures**. The catch audit also validates all **399 resident
assets / 2,121 pictures**. The full 8,570-case input and 3,600-case phase sweeps
were not repeated for encounter-only changes; their earlier scoped results,
including the eleven open Mewtwo text failures, remain unchanged evidence.

## Integrated Results

### Publication Copy Correction

```text
ROM SHA-256 448af700280b5af6f25563d0f1b342d0ac70c83490a2e4da9744f92eacdaa77b
SYM SHA-256 e58bf14d9f201277161ece5ef3b84f4193f07260dfc300d7570d0716e3e96cb9
MAP SHA-256 c07fd89da7e12c21b23f849066f91802fe4f74a43593081092d79a9f67b1dbe4
```

`NewDexEntry_CopyVRAMMap` fully unrolls the fixed seven-row rectangle;
`NewDexEntry_FillVRAMAttrs` uses sequential `LD [HL+], A` stores. A link-time
assertion protects the shared high byte of all destination cells. Both helpers
have one caller, and the caller does not consume their final pointer values.
Backing-map service, audio, startup loading, timeline and ownership are unchanged.
All publication types now use the proven LY < 150 admission check.

The exact cost is **148 additional ROMX bytes** in existing bank `$a5`, leaving
**1,638 bytes** there. The helpers add 154 bytes, while merging the identical
admission checks removes six bytes. No ROM0, RAM, SRAM, VRAM or metadata allocation
is added. This differs from the earlier 154-byte estimate only because the
integrated version removes that redundant cutoff branch.

From the LY-read instruction through the final VRAM store, map/first/final costs
are **1,108 / 1,704 / 1,708 T**. First/final writes are 732 T cheaper. Even at the
end of LY 149, their conservative write margins are 120/116 T. These are safety
margins for the last store, not spare time for unrelated work. Normal startup
loading and the 32-block sampled-cry prefill are not increased.

Current-link results under `build/new-dex-entry-copy-integration/`:

- `catches/report.json`: **8 authentic catch flows / 24 registration variants**
  pass, including level-up/stat prompts and party/PC return; 2,356 display checks.
- The previously failing Dusknoir entry publishes first on display 59, holds
  the first picture for all seven intervals, and completes its 35 publications
  in exactly **174 intervals**. All 557 audio blocks complete, with no underrun.
- `full/report.json`: **8,559 / 8,570 cases pass every check** across 20 species.
  The eleven failures are exclusively the Mewtwo text checks detailed below.
  All **1,222,463 frontpic display checks**, exact deadlines, audio accounting
  and ownership checks pass. There are **5,690 complete sequences**, 3,156
  checked returns and 7,104 sampled-cry runs, with neither miss breakpoint hit.
- Structural validation covers **399 assets / 2,121 pictures**. The rebuilt
  New Entry, Selected scheduler and host audit contracts pass.

### Synthetic Interrupt-Phase Stress

`tools/dex_timing/new_entry_phase_sweep.py` is an explicitly synthetic host test,
separate from real-input acceptance. It changes only the first disabled-timer
TIMA write, making the first overflow occur after 1 through 200 timer clocks.
TMA and all subsequent periods remain unchanged. Each step shifts the timer
phase by 64 normal-speed T-cycles; no ROM, producer state or input fixture is
patched. This does not exhaust every 4-T alignment or all entry hardware states.

`phases/report.json` records **3,600 / 3,600 passing runs**: 200 phases for each
of 16 sampled species, plus A-to-page-2 and A-then-B exit variants at all 200
Dusknoir phases. All **577,600 display checks** pass with no animation/audio
misses. First and final publications are both included. A no-op 200-clock
injection reproduces all **615 ordinary Dusknoir trace records identically**,
including timestamps, after removing its one explicit synthetic-fixture event.

The phase test exposed a host-checker error, not a game defect: LY can read zero
during the tail of physical line 153 while STAT still reports mode 1. Nine runs
were initially rejected by a `144 <= LY <= 153` check despite being in VBlank.
The checker now accepts `(LY == 0, mode == 1)` and still rejects visible-line
zero in modes 0/2/3. A negative-control unit test covers that distinction. The
complete phase suite was rerun after the correction, not merely reclassified.

### Remaining Mewtwo Text Refresh

The eleven failing real-input cases are Mewtwo `page-032` through `page-041`,
and `page-043`, where the number is the A-press offset from first publication.
At the page-2 snapshot, fourteen UI cells still differ from the backing map,
including the page number (`$57` still in VRAM, `$58` in backing memory).
They later converge without a picture mismatch, missed animation deadline,
audio failure or lock. The frontpic still completes in exactly 111 intervals.

Every case was replayed on the previous restored-Master-Ball ROM using its own
matching registration state. **All eleven fail identically**, including the
exact display intervals and counts of stale UI cells. Evidence is in
`mewtwo-ui-comparison/report.json` and its before-change traces. This is not a
regression introduced by the copy optimization. The older fully green sweep
used checkpoints derived with the standard-ball opening override and did not
cover this entry phase.

The existing four-interval `WaitBGMap` is not a completion acknowledgement:
ordinary BG updates copy one third per eligible VBlank, and due animation
publications or an outstanding ACK take priority. Mewtwo's short 1/2-interval
holds can postpone the middle third, leaving the page number and upper text
behind the already-refreshed bottom third. The failing snapshots are taken
three intervals after the second input wait begins; in these cases the observed
remaining mismatch clears one to three intervals later. Do not weaken that
test or call the entire input suite green.

Logged as `NEWDEX-UI-01`. A follow-up should give description refresh an explicit
completion/budget contract instead of relying on a fixed delay. No additional
runtime fix was made here; it needs its own scoped review. The separate battle
cry regression `BATTLE-CRY-01` also remains deferred.

## Historical Diagnosis And Builds

### Master Ball Restoration Follow-Up

Only the temporary Master Ball branch override was removed from game source.
It now branches to the existing `.MasterBall` script, including its original
sparkle sequence, before joining the common catch path. Route 29/30 test
encounters, instrumentation, scheduler code and memory layout are unchanged.

```text
ROM SHA-256 546f053f8137bf7d1f780268762d431d00e1f0ae4c8edf0dec789e9aeb1a7a10
SYM SHA-256 1e77e507706b3adfaadc4e48e8b58c46f8fbd6602aecc5f11ae5c83a8e0714ea
MAP SHA-256 f72913203cc5bc995134725f00518d4deadc864b1fc5f12b89ddeebaadceab40
```

The rebuild and all 13 New Entry contract tests pass. Seven authentic catch
flows and their 21 representative registration variants pass: Luxray,
Caterpie, Metagross, Garchomp, Exeggcute, Vibrava and Mewtwo.

**Dusknoir fails on its first New Dex Entry publication**, not sampled audio
and not the battle playback issue `BATTLE-CRY-01`. The full catch trace reaches
the page normally, then hits `$a5:$7754`. A registration-only replay of its
newly derived state reproduces the same event:

- At T=4,089,212 after entry, display 59, reason 3 (unsafe publication window)
  is recorded at LY 149, mode 1, with flags `$2b` (ACTIVE/READY/FIRST/MISSED).
- The first map also needs attrs, whose current admission bound is LY < 148.
  The map is ready; it is the late arrival at this check that rejects the copy.
- First publication occurs at display 60, one interval late. The next event
  occurs at display 66, so the first seven-interval hold is shortened to six.
- The cry completes with zero remaining blocks, with no audio-empty hit.
  Animation cleanup and the catch/party return still complete.

This initially identified the failing boundary, not the full cause of the late
arrival. No timing fix or scheduler change was attempted during the restoration request.
All manual miss breakpoints and capture addresses remain unchanged. The user
subsequently tested all four Route 30 targets (Dusknoir, Metagross, Luxray and
Caterpie) and reported no New Dex Entry breakpoint hits. The only reported hit
was Dusknoir's battle cry, the separate deferred `BATTLE-CRY-01`.

The installed `/Applications/SameBoy/Games/pokecrystal.gbc` was hash-verified
against the restored build above. Replaying the saved Dusknoir registration
checkpoint with that installed ROM reproduces the same reason-3 animation miss
at T=4,089,212 and LY 149; audio still finishes with zero remaining. Trace:
`build/new-dex-entry-master-ball-restored/dusknoir-diagnostic-repeat.jsonl`.
This rules out a different cartridge file for this comparison, but does not
establish that the manual and automated runs entered registration at the same
CPU/PPU/audio phase. The subsequent instruction-level investigation below proves
the interrupt collision in the automated fixture. The user's unrecorded manual
phase is still unknown. Retain the automated counterexample as an open issue;
no additional manual capture was required.

Evidence: `build/new-dex-entry-master-ball-restored/dusknoir-catch.jsonl`,
`dusknoir-registration.s0`, and `dusknoir-diagnostic.jsonl`. The catch command
correctly aborts on Dusknoir, so that directory's partial `report.json` contains
only the preceding three species. The other four passing catches/12 variants
are in `build/new-dex-entry-master-ball-restored-expanded/report.json`.
These restored-opening results do not replace or broaden the older full sweep.

### Timer Collision Diagnosis

The optional host-only instruction observer runs the same installed ROM and
captured entry state without changing hardware registers, interrupts or game
state. All 1,892 ordinary trace records of the failing replay remain identical
with and without instruction logging, including every T-cycle timestamp. The
old passing Dusknoir entry also passes with the **current installed ROM**; its
1,888 common records match the old trace after excluding optional screenshot
events. The failure is not an instrumentation artifact or a mismatched ROM.

**The sampled-cry timer ISR is already executing when VBlank begins.** IME is
disabled throughout that handler, so the pending VBlank interrupt cannot enter
until the audio handler returns. This is the periodic 16-byte Wave RAM upload,
CH3 restart and pointer/count updates, not cache decoding or refill work.

Timing in T-cycles from the restored Dusknoir registration checkpoint:

| Event | T | Relative to VBlank start | LY |
| --- | ---: | ---: | ---: |
| First animation map prepared | 3,988,004 | -98,804 | 81 |
| Sampled playback arm | 4,059,200 | -27,608 | 83 |
| LCD interrupt vector | 4,086,632 | -176 | 143 |
| Timer interrupt vector | 4,086,740 | -68 | 143 |
| Display 59 / VBlank begins | 4,086,808 | 0 | 144 |
| Timer RETI instruction | 4,088,156 | +1,348 | 146 |
| VBlank interrupt vector | 4,088,192 | +1,384 | 147 |
| Animation publisher entry | 4,088,700 | +1,892 | 148 |
| Publication cutoff LY read | 4,089,048 | +2,240 | 148 |
| Animation-miss breakpoint | 4,089,212 | +2,404 | 149 |

The timer vector through RETI completion occupies 1,432 T-cycles. An HBlank
interrupt immediately precedes it, but the long delay across the boundary is
the sampled playback handler. VBlank is pending in IF while that handler runs.
The ISR dispatch follows normal priority rules; it cannot preempt an ISR that
has already disabled IME.

**LY 149 in the old report is the breakpoint location, not the cutoff sample.**
The cutoff actually reads 148 and rejects it because the first map also changes
49 attributes and requires LY < 148. In the passing entry checkpoint, no timer
handler overlaps that boundary: the cutoff executes at VBlank +880 T, LY 145.
The two runs differ by 1,360 T at the check. Both have the first map ready and
use the same resident dictionary, timeline and publication code.

The safety check is correct for the existing copy cost. From its LY-read
instruction, the first publication needs 2,436 T through the last VRAM write.
At the failing read only about 2,320 T remain before visible scanning resumes;
merely relaxing the cutoff would overrun that interval. The repeatable result
is a one-interval deferred first picture and a six-interval first hold instead
of seven. Final publication remains at display 233, giving 173 intervals from
the late first picture instead of the authored 174. Audio completes all 557
blocks, with zero remaining and no audio-empty event.

This is a publication-window budget issue, not a decompression/producer
shortage, a need for more upfront dictionary loading, or the separate battle
cry regression. Master Ball's restored opening exposes a different entry phase;
there is no evidence that its animation script itself corrupts registration.
The earlier 8,570 cases varied inputs for their entry fixtures, not every
possible interrupt phase. The headless core detects this correctly; the
frozen-LY instruction test only proves safety **after admission**, not that all
real executions will arrive early enough to be admitted.

### Private Publication Preflight

No game-source correction was applied. A private ROM under ignored
`build/new-dex-entry-master-ball-restored/investigation/` tests one scoped
direction: fully unroll the fixed seven-row VRAM copies, use `LD [HL+], A` for
constant attributes, and admit the cheaper first/final copies through LY 149
(LY < 150). The backing-map helpers, resident loader, startup audio, timer ISR,
deadlines, ACK/READY protocol and Master Ball script are unchanged. Both VRAM
helpers have exactly one caller and always target the 7x7 rectangle at $9821.

| Publication | Current last-write cost T | Private last-write cost T | Saving |
| --- | ---: | ---: | ---: |
| Map only | 1,356 | 1,108 | 248 |
| First map + attrs | 2,436 | 1,704 | 732 |
| Final map + attrs | 2,440 | 1,708 | 732 |

Costs are measured from the cutoff read through the last VRAM write using the
linked instructions. Even a read at the end of LY 149 leaves at least 1,824 T,
so the private worst-case write margins are 716/120/116 T respectively. The
actual failing fixture's first copy now has approximately 616 T of write
headroom. This is a cost-backed admission change, not removal of a safety gate.

The prototype occupies 217 bytes of verified empty bank $a5 and redirects only
the two existing calls plus the first/final cutoff operand. Replacing the old
34-byte map helper and 29-byte attribute helper in the actual source would mean
**154 net ROMX bytes**, with no new ROM0, WRAM0, WRAMX, HRAM, SRAM, VRAM or metadata.
Exact integrated placement must still be verified after linking.

Private ROM SHA-256:
`b3a34c54440ff8fe710d0f5a642052fdf17cdbb0a220bc2860cc7ff31e195d0a`.

Results:

- The failing Dusknoir fixture now publishes on display 59, holds its first
  picture for seven intervals, and completes all 35 publications in exactly
  174 intervals. Its cry finishes with zero remaining.
- **63 / 63 representative registration replays pass** across 20 species and
  21 entry fixtures, including both Dusknoir phases. The cases are no input,
  A to page 2, and A then B to return.
- **7,139 display checks** match physical VRAM and rendered pixels; 42 complete
  sequences meet every authored deadline. Early exits match the expected
  prefix and restore the caller/owner.
- All **51 sampled-cry runs** have complete block accounting and no audio-empty
  event. Synthesized controls also pass.

This is a promising preflight, **not** a new full acceptance sweep or an installed
fix. Next, if approved, integrate the two fixed-destination helper replacements
and their measured cutoff together, re-run current-link contracts, authentic
catch flows, the full input matrix and a targeted interrupt-phase stress pass.
Include final restoration as well as first publication; both use map + attrs.
No new manual save state is needed before that work.

Evidence in the investigation directory: `dusknoir-failing.jsonl`,
`dusknoir-passing.jsonl`, `publication-preflight.asm`, `publication_preflight.py`,
`private-preflight-report.json`, and `private-*.jsonl`. The report binds the
private image, helper source, builder and fixture hashes. Original saves and
the installed ROM remain unchanged. Only the optional host observer and these
diagnostic records/docs were added to the working investigation.

### Page-Two Correction Acceptance Build

```text
ROM SHA-256 aed56075b76f2387395842d2616e6497dda123327950aa464cb1346719274057
SYM SHA-256 0cae4de96213f43e06aac9f1b5f27188de1f63ff8a1f4db2e20f9618b3618ba0
MAP SHA-256 9c70b631a0aac2290ddddb23292eafe50c3cdae55d5e0bd900fa699ee508f63e
SameBoy commit 213a12ce93d66b105a113debd9396306066a7cfc
Core source SHA-256 ba12c3150d5f27e68da05323a8d3f4bf47f0343474741c4f95f69d35ee2b5989
```

`NewPokedexEntry` now calls the New Entry-only `NewDexEntry_DisplayPage2`.
It skips unchanged header/dimensions/page-1 rendering, supplies three bounded
foreground map-service opportunities, and services audio once at entry. The
map producer rechecks ACK and READY from one snapshot before reusing its
buffer. The [system reference](new_dex_entry_animation_scheduler.md) describes
the implementation and why both sides of the interruption window are safe.

The integrated correction adds **100 ROMX bytes** in existing bank `$a5`:
96-byte renderer/helper plus a four-byte inline ACK guard. No ROM0, RAM, SRAM,
VRAM or metadata allocation was added. Bank `$a5` has 1,786 trailing bytes free.
The existing 32-block audio startup, eight-block refill, resident dictionary,
timeline, publication cutoffs, input/exit semantics and shared renderer remain.

All checks below ran against this newly linked build, not the private patch:

- **8 authentic catches** complete through experience, four level-up/stat
  prompts, registration, and the expected party/PC result. Their **24 basic
  registration variants** pass with 2,356 display checks.
- **8,570 / 8,570 combined cases pass** on the same 20-species/input matrix
  detailed below. This includes all 28 original failures and Dusknoir A+18.
- **1,222,471 displayed pictures** match physical VRAM and rendered pixels.
  Description refresh checks have no failures.
- **5,690 complete sequences** meet every authored event deadline; early exits
  match the expected timeline prefix. All **3,155 checked returns** restore
  owner/caller state, with no locks.
- **7,104 sampled-cry runs** have correct block accounting, zero remaining on
  natural completion and no empty-cache/nonzero-remaining events.
- **49 contract/regression tests pass**, including new register/audio-service
  and injected ACK-interruption tests. Publication timing bounds are unchanged.
- Structural validation covers **399 assets / 2,121 pictures**.
- Fresh boot and **9 Selected Description cold entries/returns** pass:
  Chikorita, Mewtwo, Dusknoir, Luxray, Metagross, Weavile, Garchomp, Unown A and
  Seviper. This is a shared-hook regression smoke test, not a new all-Dex sweep.

Twenty-seven paired full-profile replays also pass on the integrated ROM.
Every first-publication T-cycle exactly matches the frozen baseline. Page-2
rendered number/text pixels match its settled reference, including the six
representative original failures and the Dusknoir race input. The candidate is
labeled `prototype` by the reusable comparison tool, but the input here is the
root ROM with the hash above, not an experimental cartridge.

| Case | Baseline redraw T | Integrated redraw T | Baseline service gap T | Integrated service gap T |
| --- | ---: | ---: | ---: | ---: |
| Mewtwo A+11 | 179,156 | 106,928 | 210,376 | 72,676 |
| Mewtwo A+30 | 185,676 | 93,120 | 270,928 | 74,784 |
| Mewtwo A+36 | 190,124 | 107,184 | 279,756 | 74,280 |
| Exeggcute A+23 | 185,592 | 102,120 | 212,748 | 77,392 |
| Dusknoir A+5 | 87,564 | 62,404 | 142,168 | 78,764 |
| Dusknoir A+18 | 88,912 | 86,060 | 139,988 | 71,708 |
| Metagross A+5 | 88,800 | 62,584 | 145,600 | 81,908 |

The service-gap definition is entry-to-entry spacing overlapping redraw through
page-2 wait entry, as in the private comparison below. Across all 27 pairs,
input-to-page-2-wait readiness changes by **-164,132 to +208 T-cycles**: up to
2.337 display intervals faster, at most 0.003 interval (about 50 us) slower.
This measures foreground readiness, not the first visible text pixel; existing
BG refresh waits remain. No initial-entry timing penalty was observed.

Current evidence lives under ignored `build/new-dex-entry-page2-integration/`:

- `baseline/`: frozen pre-correction ROM/symbol/map copies.
- `catches/report.json`: authentic catches and representative registration tests.
- `full/report.json`, `full/results.jsonl`: full matrix and exact provenance.
- `diagnostic/comparison.json`: paired timing, pixel checks and full traces.
- `selected-regression/`: fresh-boot, normal-input Selected smoke test.

The user subsequently reported successful natural completion and premature
A, A+B and B inputs without registration animation/audio misses. The prior
manual pass targeted Mewtwo, Exeggcute, Dusknoir and Metagross for presentation,
audio quality and real-input responsiveness. Use the
[current guide](dex_new_entry_testing.md#focused-manual-pass): animation miss
is now `$a5:$7754`, audio miss remains `$00:$3cb3`. The coverage limits at the
end of this report still apply. Temporary encounters remain; Master Ball's
opening is now restored and its separate follow-up is recorded above.

## Historical Baseline Build And Evidence

The following baseline and prototype sections record the investigation before
the integrated correction. Their older build hashes and failures are intentional.

```text
ROM SHA-256 13e85ecf5d6986fbb38e62af0b3e0ea9f3a191fdc38e5c249a57e5eeba3e7a3a
SYM SHA-256 88f3d4cac9ff85c3d81efa6207bf31fabc0ccbf484a9e5410636e40fa21ef6b4
SameBoy commit 213a12ce93d66b105a113debd9396306066a7cfc
Core source SHA-256 ba12c3150d5f27e68da05323a8d3f4bf47f0343474741c4f95f69d35ee2b5989
```

The tests execute the actual linked ROM through the headless SameBoy CGB core
at normal speed. They do not substitute a host scheduler or patch the game's
deadlines. The observer reads physical RAM/VRAM and rendered pixels without
emulated bus reads. Observer CPU time does not advance emulated time.

The original eight pre-catch fixtures were replayed through their real capture,
experience and registration paths. Four include level-up/stat prompts; Vibrava
and Mewtwo go to the PC. All eight completed correctly. Their matching-build
registration-entry checkpoints seed the timing sweep.

For the additional twelve species, the fixture factory starts from Caterpie's
registration-entry checkpoint, runs the game's actual runtime-ID allocator,
and substitutes the incoming species context and seen/caught bits. Unown uses
form A and valid DVs. CPU/PPU time spent allocating advances normally. No ready
flags, VRAM tiles, producer progress or deadline phase are fabricated. These
are explicitly **generated entry fixtures**, not twelve additional authentic
captures. They test page setup, playback, input and return-state restoration,
not the ball/party/PC branches for those additional species.

Machine-readable evidence is local and ignored:

- `build/new-dex-entry-integration/results/report.json`: authentic catch replays.
- `build/new-dex-entry-sweep-verified/report.json`: final 20-species sweep,
  including ROM/core/host-source/binary/state hashes and per-case assertions.
- `build/new-dex-entry-sweep-verified/results.jsonl`: incremental sweep results.
- Each species subdirectory retains all input plans and compressed traces for
  every failure plus selected passing controls.
- `build/new-dex-entry-sweep-final/diagnostic/`: full-profile failure replays
  and page-text screenshots; these reproduce the same miss timing as the
  compact sweep. Earlier smoke/initial sweep outputs are not acceptance records.

## Baseline Coverage

The twelve additions were Groudon, Weavile, Bastiodon, Unown, Seviper,
Rampardos, Kyogre, Rayquaza, Spheal, Milotic, Yanmega and Rhyperior.

The last five extend coverage beyond previously troublesome species:
Rayquaza has a longer multi-event sequence; Spheal combines a 5x5 native base
with a large tail; Milotic crosses the eight-bit display-counter wrap during
its 275-interval sequence and has a long cry; Yanmega has dense frame changes;
Rhyperior combines large map changes with short holds. Rampardos and Kyogre
were explicitly requested controls from the Selected Description investigation.

| Species | Entry fixture | Authored/observed uninterrupted intervals | Cases | Failed cases |
| --- | --- | ---: | ---: | ---: |
| Luxray | Authentic | 92 / 92 | 319 | 0 |
| Caterpie | Authentic | 111 / 111 | 341 | 0 |
| Metagross | Authentic | 228 / 228 | 581 | 0 |
| Dusknoir | Authentic | 174 / 174 | 495 | 0 |
| Garchomp | Authentic | 110 / 110 | 353 | 0 |
| Exeggcute | Authentic | 113 / 113 | 347 | 5 |
| Vibrava | Authentic | 83 / 83 | 287 | 0 |
| Mewtwo | Authentic | 111 / 111 | 347 | 23 |
| Groudon | Generated | 211 / 211 | 563 | 0 |
| Weavile | Generated | 78 / 78 | 289 | 0 |
| Bastiodon | Generated | 205 / 205 | 555 | 0 |
| Unown A | Generated | 156 / 156 | 431 | 0 |
| Seviper | Generated | 122 / 122 | 369 | 0 |
| Rampardos | Generated | 139 / 139 | 411 | 0 |
| Kyogre | Generated | 113 / 113 | 357 | 0 |
| Rayquaza | Generated | 175 / 175 | 477 | 0 |
| Spheal | Generated | 166 / 166 | 469 | 0 |
| Milotic | Generated | 275 / 275 | 675 | 0 |
| Yanmega | Generated | 169 / 169 | 461 | 0 |
| Rhyperior | Generated | 155 / 155 | 443 | 0 |
| **Total** | | | **8,570** | **28** |

Intervals include main, transition hold, idle and final base restoration.
For example, Dusknoir's full menu sequence is 174, not its main-only 107.
Every uninterrupted intermediate publication also meets its exact deadline;
the table is not merely an end-to-end duration comparison.

Input families:

| Family | Cases | Procedure |
| --- | ---: | --- |
| Uninterrupted | 20 | No input until both animation and cry finish |
| Page advance | 3,046 | Two-interval A pulse, shifted one display interval at a time from first publication through completion + 2 |
| Exit | 3,046 | A at first publication + 5; two-interval B pulse shifted one interval at a time from page-2 wait entry |
| Startup | 2,018 | A/B pulses shifted across registration setup, before first publication |
| Sustained/rapid input | 440 | Held A/B/both, repeated A/alternating A-B, and closely spaced A-B at beginning/middle/end |

The original catch context can still have A held from the catch prompt. A pulse
at first publication is not necessarily a new press. The runner records this
separately only when the first input-poll values confirm the existing edge
semantics; it does not silently excuse missed later page/exit taps.

Checks cover authored event order and deadlines, publication in VBlank,
physical VRAM and rendered frontpic pixels, display-clock progression,
description backing-map refresh, owner/caller-state restoration, both miss
breakpoints and sampled block accounting. Expected early cancellation checks
only the timeline prefix before exit, not nonexistent later publications.

## Baseline Results

- **8,542 pass / 28 fail**, with **1,224,844 displayed frontpics checked**.
- **All 20 uninterrupted sequences pass**, including every event deadline.
- **18 species pass every scheduled case**, including Rampardos and Kyogre.
- **25 cases hit animation deadlines late**: 20 Mewtwo, 5 Exeggcute.
- **3 additional Mewtwo cases fail only the page-2 UI refresh check**.
  Fourteen cases in total have a delayed UI refresh, eleven overlapping the
  animation failures. These are not fourteen additional failing cases.
- No mismatched frontpic pixels or dictionary corruption were observed.
  A held old animation pose during a missed deadline is still a timing failure.
- **Zero sampled-cry underruns across 7,104 sampled-cry runs** (16 species).
  All account for 32 startup blocks plus subsequent production and natural
  completion at zero remaining, including the tested exits.
- **3,126 returns** restore the checked caller/owner state. No soft locks.

All failures are page-advance cases; startup, exit and sustained/rapid-input
cases passed. This illustrates why a few button-mashing trials are not a
substitute for a one-display-interval input sweep.

Additional checks passed: 11 New Entry contracts, 11 Selected scheduler tests,
14 cold-listing tests, 11 target-regression tests, 399 timeline assets,
65,536 pair-lookup combinations and all 122 sampled-cry assets (37,655 encoded
blocks / 602,480 decoded bytes). Structural asset validation is distinct from
playing every species through this screen.

## Reproduced Failures

Offsets below are decimal display intervals after the first published frame.
The test holds A for two intervals, then releases it.

| Species / failure | A offsets |
| --- | --- |
| Mewtwo animation miss | 11, 20, 22, 24, 26, 28, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 47 |
| Exeggcute animation miss | 23, 24, 25, 43, 44 |
| Mewtwo UI-only failure | 30, 31, 32 |

The first missed publication has reason 1 (map not ready); some Mewtwo cases
subsequently record reason 2 (late deadline). The reason-3 unsafe-window gate
is not the cause of these failures. Whole-sequence duration can still end at
the authored interval after recovery, so duration alone would miss the defect.

### Foreground Service Gap

`NewPokedexEntry` sets page 2, calls shared `DisplayDexEntry`, then calls
`WaitBGMap`. `DisplayDexEntry` redraws the name/category/number/height/weight,
clears and writes **page 1**, and only then clears it and writes page 2. The
traced redraw has no foreground animation-service or `DelayFrame` call inside
it. Interrupts continue, so the authored deadline clock continues too.

Representative full-core measurements (normal-speed T-cycles):

| Case | `DisplayDexEntry` time | Display intervals | Gap between producer service entries |
| --- | ---: | ---: | ---: |
| Mewtwo A+11 | 179,156 | 2.55 | 210,216 |
| Mewtwo A+30 | 185,676 | 2.64 | 251,900 |
| Mewtwo A+35 | 179,660 | 2.56 | 210,484 |
| Exeggcute A+23 | 185,592 | 2.64 | 212,480 |

One display interval is 70,224 T-cycles. The service gap includes surrounding
work and can exceed three intervals. The single prepared-map lead cannot
cover all of Mewtwo's and Exeggcute's one-/two-interval holds across this gap.
Full dictionary residency removes tile decoding/upload work during playback;
it does **not** eliminate the requirement to build and acknowledge each map.
This evidence points to foreground scheduling around description redraw, not
insufficient dictionary capacity or the sampled decoder. Both failing species
use synthesized cries.

### Description Refresh

During dense publications the quiet VBlank/ACK barrier correctly protects the
frontpic from stale software backing maps, but can delay ordinary BG-map
refreshes. At Mewtwo A+30, page-2 text still has 33 tilemap/backing mismatches
after the expected refresh period; A+35 has 47. Rendered screenshots confirm
fragments of page 1 remain with page-2 text. Later settled snapshots have zero
mismatches. Exeggcute A+24 also has a delayed 16-cell refresh, overlapping its
animation miss. This is a transient text-update problem, not corrupt frontpic
tiles, and is separate from the deferred Selected Description A-button bug.

## Initial Fix Direction

Keep the resident dictionary and deadline-controlled publisher. Investigate a
New Entry-specific page-2 redraw that avoids rebuilding unchanged header data
and drawing page 1 only to erase it. Ensure bounded foreground animation/audio
service opportunities while constructing text, with explicit backing-map and
refresh ownership. Do not simply insert an unbounded wait or relax deadlines:
that can hide one failure while extending another operation.

Retain the ACK protection and prove that final page-2 text reaches VRAM without
overwriting a newer frontpic. Re-run these exact failing offsets first, then
the full combined matrix. The current evidence does not call for another
scheduler rewrite, larger upfront dictionary/audio fill, or more manual
captures before scoping that change. This direction was investigated in the
private prototypes below, then integrated and revalidated as recorded above.

## Isolated Page-Two Prototype

Follow-up measured 2026-09-21. This executes a private, patched copy of the
same linked ROM in headless SameBoy, not simulated host-side deadlines. The
prototype builder pins the baseline hash, verifies unused ROMX space and
asserts that only the intended call/guard sites, added helpers and cartridge
checksums differ. Existing code/data/state addresses do not move. The original
captures and root ROM are read-only.

The host-only assembly was `tools/dex_timing/preflight/new_entry_page2.asm`;
`tools/dex_timing/new_entry_page_experiment.py` built and compared it. Both
superseded prototype sources were removed during commit cleanup; only the
integrated runtime and maintained regression tools remain. No game
source includes that assembly. At this stage production integration still
required a separate reviewed edit, relink and regression pass; those are now
recorded under Integrated Results.

### Redraw Scope

Only New Entry's page-2 call is redirected. The helper obtains the existing
dex-entry pointer, scans past the category/dimensions/page-1 bytes without
rendering them, clears the five description rows, changes the page number,
and draws page 2 using the existing `PlaceFarString`. It does not rebuild the
header, dimensions, divider or frontpic, and does not modify shared
`DisplayDexEntry` or Selected Description behavior.

Animation acknowledgement/preparation runs at three foreground boundaries:
before the scan, after locating page 2, and after drawing its text. The final
candidate services sampled audio once at the first boundary. Inner boundaries
service only animation; ordinary `DelayFrame` audio opportunities remain.
The 32-block startup, 8-block refill limit, resident dictionary, exact timeline,
VBlank publisher/admission cutoffs, ACK ownership, `WaitBGMap` and input semantics
are otherwise unchanged.

### Why There Were Three Private Candidates

1. The first candidate called the existing audio-plus-animation wrapper at all
   three points. All 8,570 cases passed, including the 28 baseline failures, but
   paired Dusknoir/Metagross page changes took about one extra display interval.
   Extra audio decoding at the inner points was unnecessary for this workload.
2. Servicing audio only once removed that extra interval. Its full sweep
   passed 8,569 cases but exposed **one Dusknoir map-corruption case at A+18**.
   Neither animation nor sampled-audio miss breakpoint fired. The picture
   checker caught two displays with mixed tiles. This is not an acceptable
   candidate despite its passing timeline counters.
3. The final candidate retains the faster redraw and adds a consistent flag
   recheck before reusing the single map buffer. It addresses the race below
   rather than adding delay to shift the failing phase out of view.

### ACK Check Race

The existing service first checks `ACK` through `[hl]`, then later loads the
flags again at `.build` to test `READY`. VBlank can publish between those two
reads: the first check sees no ACK; publication clears READY and sets ACK; the
second read sees not-ready and builds over the just-published map before it
has been acknowledged. A later call then copies the *next* map into the
software backing map. Ordinary three-part BG refresh can reveal it early and
in mixed rows, even though every explicit animation publication is on time.

The Dusknoir A+18 full trace proves this order (normal-speed T-cycles since the
registration checkpoint):

| Event | T-cycle |
| --- | ---: |
| Animation service enters | 5,423,140 |
| Frame 4 publishes during that call | 5,425,664 |
| Frame 5 construction begins, without a backing-map copy | 5,427,076 |
| Frame 5 is prepared | 5,446,896 |
| Later service copies that buffer into the backing map | 5,466,768 |
| First mixed-picture display (number 80) | 5,563,660 |

Display 81 is also mixed. Frame 5 is not due until display 83. The intended ACK
barrier exists, but the foreground's two different flag snapshots break its
invariant. This is a latent service race exposed by the changed scheduling,
not a need for a second map buffer or more dictionary capacity.

The private guard replaces `.build`'s flag load with a short ROMX trampoline:
load the flags, test ACK on that same snapshot, and return to the existing
acknowledgement block if set; otherwise resume the existing READY/ACTIVE tests
with the same `a`. For source integration, two inline instructions
(`bit NEW_DEX_ANIM_ACK_F, a` / `jr nz, .ack`) after the flag load suffice.
There is no `di`, interrupt wait, extra state or changed publication deadline.
If publication occurs *after* that snapshot, READY was set in the snapshot,
so the producer returns without overwriting the buffer and acknowledges on
its next service call.

### Paired Timing And Cost

Twenty-seven paired full-profile replays cover six failing baseline offsets,
the exposed Dusknoir A+18 case and A+5 for all 20 species. All final-candidate
cases pass, and rendered page-number/description pixels match the baseline's
settled page-2 reference. The first-publication T-cycle is unchanged in every
pair. Page-1 preparation and resident loading are not part of the redraw edit.

| Case | Baseline redraw T | Candidate redraw T | Baseline maximum service gap T | Candidate maximum service gap T |
| --- | ---: | ---: | ---: | ---: |
| Mewtwo A+11 | 179,156 | 106,928 | 210,376 | 72,676 |
| Mewtwo A+30 | 185,676 | 93,228 | 270,928 | 74,784 |
| Mewtwo A+36 | 190,124 | 107,400 | 279,756 | 74,316 |
| Exeggcute A+23 | 185,592 | 102,228 | 212,748 | 77,536 |
| Dusknoir A+5 | 87,564 | 62,512 | 142,168 | 78,548 |
| Dusknoir A+18 | 88,912 | 86,168 | 139,988 | 71,708 |
| Metagross A+5 | 88,800 | 62,800 | 145,600 | 81,800 |

Here service gap means the largest **entry-to-entry** spacing overlapping
redraw through page-2 wait entry. These consistently paired measurements
supersede the earlier illustrative gap column, whose boundaries were not
uniform. A display interval is 70,224 T. Gaps a little over one interval are
not an unconditional deadline bound; the actual phase and prepared-map lead
still matter, and are checked by the replay.

Input-to-page-2-wait time improves by up to 164,096 T (2.337 intervals), with
the largest increase only 244 T (0.0035 interval, about 58 microseconds). This
is a foreground readiness measurement, not a claim of the exact first visible
text pixel. Existing BG refresh waits remain. The prototype avoids the
one-interval penalty of the first all-audio candidate without padding waits.

The private image adds **107 ROMX bytes**: 96 for the redraw/helper and 11 for
the no-relocation ACK trampoline. Direct source integration should need about
100 additional ROMX bytes (96 plus a four-byte inline guard), subject to final
placement/linking. No additional ROM0, WRAM0, WRAMX, HRAM, SRAM, VRAM or animation
metadata is allocated. Temporary stack saves preserve the caller's registers.

### Final Regression

The final `start-audio-ack-guard` candidate passes:

- **8,570 / 8,570 combined cases**, using the same 20 species and input families
  as the baseline. All 28 original failures and the exposed Dusknoir A+18 race
  case pass. There are no animation miss/deadline errors or UI snapshot failures.
- **1,222,471 displayed pictures** checked against both rendered pixels and
  physical VRAM, with no mismatches. The checked-picture total differs from the
  baseline because some input paths now reach page 2 or exit sooner.
- **7,104 sampled-cry runs**, all with correct block accounting and zero
  nonzero-remaining empty-cache events. No prefill or decoder change was used.
- **5,690 complete natural animation sequences**, with exact authored event
  deadlines. Early exits are validated against the expected timeline prefix.
- **3,155 returns** with the checked owner/caller state restored. No locks.
- All **eight authentic catch/experience/party-or-PC flows**, plus their 24
  representative registration variants, pass on the candidate ROM.
- **27 paired full-profile cases** pass with correct rendered description
  content. Their first-publication T-cycles match the baseline exactly.
- The **47 existing contract/regression unit tests** pass; the shared
  publication bounds are unchanged. Structural validation again covers
  399 assets and 2,121 pictures.

These results support integrating the page-2-only redraw and the consistent
ACK/READY recheck together, not another scheduler redesign. No additional
manual capture is needed to scope that edit. After integration, re-link and
re-run the suite against the actual final addresses; do not treat the private
107-byte trampoline layout as the production layout. The same coverage limits
below still apply, including the twelve generated entry fixtures and the
unrestored Master Ball opening override.

### Private Evidence And Reproduction

The recommended private candidate has:

```text
ROM SHA-256 3769a79cbcdeaeb43fb7f095b7c338806b204d07acd3291280b4d5f515412e91
SYM SHA-256 48fba5201da005c503fcf39e23e6a66843dcc722eb928900a00bf3166edb7fe9
```

All experiment artifacts remain under ignored `build/new-entry-page-experiment/`:

- `redraw/`: three audio-service points; passing but slower control.
- `start-audio/`: faster unguarded control; one Dusknoir corruption failure.
- `start-audio/diagnostic/dusknoir-018.jsonl`: full race trace.
- `start-audio-ack-guard/prototype.json`: final candidate identity and patch bounds.
- `start-audio-ack-guard/diagnostic/comparison.json`: 27 paired timing/pixel checks.
- `start-audio-ack-guard/catches/report.json`: eight authentic catches and 24 registration variants.
- `start-audio-ack-guard/full/report.json`: complete combined input sweep.

```sh
python3 -B -m tools.dex_timing.new_entry \
  --rom build/new-entry-page-experiment/start-audio-ack-guard/pokecrystal-page2-experiment.gbc \
  --sym build/new-entry-page-experiment/start-audio-ack-guard/pokecrystal-page2-experiment.sym \
  --fixtures build/new-dex-entry-catches \
  --fixtures build/new-dex-entry-expanded \
  --output build/new-entry-page-experiment/start-audio-ack-guard/catches
python3 -B -m tools.dex_timing.new_entry_sweep \
  --rom build/new-entry-page-experiment/start-audio-ack-guard/pokecrystal-page2-experiment.gbc \
  --sym build/new-entry-page-experiment/start-audio-ack-guard/pokecrystal-page2-experiment.sym \
  --registration build/new-entry-page-experiment/start-audio-ack-guard/catches \
  --output build/new-entry-page-experiment/start-audio-ack-guard/full --jobs 8
```

These commands replay retained artifacts from the historical private trial,
not the current root ROM. The retired builder was pinned to the old baseline;
its sources are no longer needed after integration. The retained private
artifacts and frozen baseline identify that experiment independently. Current
validation uses the maintained commands in the testing guide.

The paired comparison uses the recorded baseline registration checkpoints,
including the twelve generated fixtures from the initial verified sweep.
Changing the pinned root ROM requires reviewing those bindings and fixture
compatibility rather than disabling the identity checks.

## Reproduction And Limits

```sh
make -j8 pokecrystal.gbc
python3 -B tools/test_new_dex_entry.py
python3 -B -m tools.dex_timing.new_entry \
  --fixtures build/new-dex-entry-catches \
  --fixtures build/new-dex-entry-expanded \
  --output build/new-dex-entry-page2-integration/catches
python3 -B -m tools.dex_timing.new_entry_sweep \
  --registration build/new-dex-entry-page2-integration/catches \
  --output build/new-dex-entry-page2-integration/full --jobs 8
```

The page-2 correction build passed these checks. The restored Master Ball
build now stops at the distinct Dusknoir first-publication miss described above.
The earlier 28 failures belong only to the original baseline. Checkpoints must match the
ROM/symbol hashes and their recorded state hashes. `--species mewtwo exeggcute` narrows the timing
sweep; `--smoke` is only a short representative-input check, not full acceptance.

The suite does not exhaust all CPU/PPU entry phases, arbitrary input strings,
all 373 species, all Unown forms, all catch/party/box contexts, or every emulator.
Its expanded fixtures are generated at registration entry, not by twelve
new catches. The original Master Ball special opening is restored, and its
newly exposed Dusknoir timing case remains open. Marked Route 29/30 test changes
remain intentionally present. Use the updated manual
guide's build-bound breakpoints; the animation miss label moved during relinking.
