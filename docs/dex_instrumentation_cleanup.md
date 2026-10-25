# Dex Instrumentation Cleanup

2026-09-21. Current-link cleanup of the accepted Selected Description and New
Dex Entry schedulers. This is not another scheduler redesign. No commit, live
save edit, installed-ROM replacement or unrelated bug fix is part of this pass.

## Runtime Changes

1. Removed Selected telemetry initialization, timestamps, service/publication
   counters, late/miss counters, circular trace records and trace routines.
2. Preserved all production scheduler state. First-publication anchoring now
   uses bit 7 of `wPokedexAnimFlags`, set before the first queue and cleared only
   when that map is published. Subsequent deadlines retain their authored
   timeline; they are not re-anchored to late work. No new byte is allocated.
3. Moved `wPokedexAnimLoopTick`, `wPokedexAnimWorkTick` and
   `wPokedexAnimSchedulerControl` to `$c758-$c75a`. These remain outside the
   cancellation-cleared owner extent. The two retired counter bytes at `$c73b`
   remain reserved to preserve the established owner/pointer layout.
4. Removed New Entry's publication/miss/reason aliases, recorder and bit-5 miss
   latch. The underlying legacy animation bytes remain for other owners.
5. Retained actual deadline, readiness, window, acknowledgement, cancellation
   and visible underflow fallback behavior. Named observation labels add no
   machine instructions. No cry codec, refill, prefill, asset, warming, encounter
   or Master Ball behavior changed.

## Host Observation

Observers count executed production boundaries and inspect physical memory;
they do not perform bus reads that advance the PPU, write cartridge diagnostic
state, or infer success from a now-missing counter. Selected tests independently
check every publication's hardware interval, tilemap, attributes and tile pixels,
plus natural cry completion and return ownership.

For New Entry, the host observes the deadline subtraction and the rejected
publication-window branch. It records reason 1 (not ready when due), 2 (already
late), or 3 (unsafe window), latching once per deadline in host memory. Negative
fixtures execute these linked branches and confirm that failures remain visible.
Independent publication/display comparisons remain enabled as well.

The Selected observer counts uploads at the animation-specific transfer call,
not the shared HDMA helper also used by Listing minisprites. An initial observer
version falsely classified row navigation as warming; that run is not acceptance
evidence. Its replacement retains the strict cold-entry check.

Current-link admission/contracts and full-core runners are maintained. Historical
capture models still need their exact frozen ROM/assets/initial memory. In
particular, the older `integrated_replay` fixture refuses the current changed
timeline targets; that rejection is retained rather than weakening its asset
identity checks. It is not a current-link cycle-exact replay result. Current
full-sequence evidence below comes from the headless SameBoy core, complemented
by linked-instruction cost/contract tests.

## Resource Comparison

Compared with the committed instrumented ROM preserved locally under
`build/dex-instrumentation-cleanup/before/`:

| Resource | Change |
| --- | --- |
| ROMX bank `$14` | -50 bytes |
| ROMX bank `$77` | -72 bytes |
| ROMX bank `$a0` | -575 bytes |
| ROMX bank `$a5` | -50 bytes |
| Total occupied ROMX | **-747 bytes** |
| ROM0 | Unchanged; 582 bytes free |
| WRAM0 global allocation | Unchanged; 13 bytes free |
| WRAMX, HRAM, SRAM, VRAM | No allocation change |

The Dex union arm shrinks by 140 bytes: 136 bytes of diagnostics and four
alignment/filler bytes disappear, while the three production bytes move down.
Another union member still determines the global allocation, so this is not
140 bytes of newly free global WRAM0. New Entry removes aliases, not the legacy
storage. The ROM remains 4 MiB.

## Remeasured Costs

| Linked path / bound | Instrumented | Clean |
| --- | ---: | ---: |
| 20-tile upload prefix, raw T | 14,916 | 14,740 |
| Upload suffix, raw T | 552 | 416 |
| Queue construction, raw T | 9,624 | 8,100 |
| 20-tile finishing chain, raw T | 35,208 | 33,372 |
| Active-audio response bound, T | 55,892 | 53,516 |

The 8,192-T reserve and all shipped LY/audio gates are unchanged. The checker
now accepts equally or more conservative tables, rejecting later LY admission,
insufficient audio runway or truncated tables. It still checks all 216,000
recomputed inequalities. Lower costs are retained as margin, not spent on more
aggressive scheduling. Selected publication's measured critical VRAM portion
remains at most 1,436 T, with at least 845 T at the latest admitted LY sample.
New Entry map/first/final critical writes remain 1,108/1,704/1,708 T.

## Automated Results

| Suite | Result |
| --- | --- |
| Selected cold Listing, all 373 species | Exact timelines, no animation/audio misses; 372 fully pass |
| Selected settled internal paging, all 373 species | Exact timelines, no animation/audio misses; 372 fully pass |
| Selected logical B-return | 373/373 per path |
| Existing Drapion static reveal | Fails both paths; still deliberately reported |
| Pre-cleanup Drapion control | Same static map and pixel bytes as the clean cold-entry failure |
| Eight authentic catch fixtures | 24 runs, 2,356 checked displays; pass |
| New Entry 20-species input sweep | 8,570 cases, 1,207,645 checked displays; zero failures |
| New Entry synthetic timer phases | 16 sampled species, 9,600 cases, 1,122,800 checked displays; zero failures |
| Current linked unit/contracts | 58 tests pass |
| Frozen-reference model unit suite | 197 tests pass (historical ROM, not a new current-link replay) |
| Finishing inequalities | 216,000 pass; shipped gates remain conservative |
| Animation structures | 399 timelines validated |
| Sample decoder correctness | 65,536 table combinations and all 122 cries / 37,655 blocks match |

The Selected aggregate intentionally exits nonzero for `DEX-UI-02`, not for a
scheduler failure. Do not suppress or relabel that check. All 373 cold entries
actually qualify as cold. Internal paging waits for the predecessor's animation
and cry to finish before moving; this is not a rapid-cancellation stress claim.
Warm Listing, arbitrary input phases, every Unown form and non-Dex owners are
not certified by these suites. Existing B-return palette, description-toggle,
rapid-axis input and outgoing-cry issues remain deferred.

Raw evidence stays under ignored `build/dex-instrumentation-cleanup/`. An early
phase attempt overlapped a ROM relink and aborted while parsing runner output;
it is excluded. The final phase suite uses the completed link with no concurrent
ROM build. The ordinary input suite was rerun against the final symbols.

Reproduction (local SameBoy checkout, boot ROM, copied all-seen battery save
and the eight documented catch fixtures are prerequisites):

```sh
make -j8 pokecrystal.gbc
make verify-dex-animations verify-sampled-cries
PYTHONPATH=tools python3 -B -m unittest test_dex_scheduler test_dex_cold_listing test_dex_target_regression test_new_dex_entry
PYTHONPATH=tools python3 -B -m dex_timing.finish_bounds --output build/dex-instrumentation-cleanup/finishing-bounds.json
PYTHONPATH=tools python3 -B -m dex_timing.cold_listing --battery build/dex-cold-listing/input-copy.sav --output build/dex-instrumentation-cleanup/selected-final --jobs 8
PYTHONPATH=tools python3 -B -m dex_timing.cold_listing --battery build/dex-cold-listing/input-copy.sav --output build/dex-instrumentation-cleanup/paging-final --paging --jobs 8
PYTHONPATH=tools python3 -B -m dex_timing.new_entry --fixtures build/new-dex-entry-catches --fixtures build/new-dex-entry-expanded --output build/dex-instrumentation-cleanup/catches
PYTHONPATH=tools python3 -B -m dex_timing.new_entry_sweep --registration build/dex-instrumentation-cleanup/catches --output build/dex-instrumentation-cleanup/full-final --jobs 8
PYTHONPATH=tools python3 -B -m dex_timing.new_entry_phase_sweep --registration build/dex-instrumentation-cleanup/catches --sweep build/dex-instrumentation-cleanup/full-final --output build/dex-instrumentation-cleanup/phases-final --all-input-modes --jobs 8
```

Build once before starting any runner. Do not relink its input ROM during a
sweep. The two Selected commands are expected to exit nonzero solely for the
unsuppressed Drapion reveal issue; inspect their summaries, not just exit codes.

## Build And Manual Observation

```text
ROM 18ec28c84656ee26e6f705b81982b12bd1fdc62a5efa7ba994ef7b1de77965ea
SYM e8e29d612bb180daba45b2e5c3b310829ff119814cb2d55f7f6bab0413771fc2
MAP b1884c4ed70433336524a1b9900fe77c880b8438aa53c44022ec50388cc5e0af
```

Fresh-boot the normal root `pokecrystal.gbc`; do not resume pre-cleanup states.
Briefly observe cold selection and internal paging for Dusknoir, Weavile, Luxray
and a synth control such as Mewtwo. Let each finish, then B-return. For New
Entry, observe a sampled cry and a synth control, including A description
advance and early exit. Known deferred symptoms are not claimed fixed.

Selected animation failure and global sampled-cry exhaustion:

```text
breakpoint $a0:$666a
breakpoint $0:$3cb3
```

The former begins `CALL Pokedex_BuildAnimationUnderflowMap`; the latter is the
existing empty-cache/nonzero-remaining branch. To avoid the known battle cry
issue when testing registration, first stop at `NewPokedexEntry`, `$3e:$57f0`,
then replace that entry breakpoint with:

```text
breakpoint $a5:$76bc if (a & $80) || ((a == 0) && (([$d168] & 2) == 0))
breakpoint $a5:$76d8
breakpoint $0:$3cb3
```

At `$76bc`, A is deadline minus display counter and WRAMX 2 is already selected.
`$76d8` is the rejected publication-window branch. These replace the removed
recorder breakpoint; a persistent failure may stop more than once now.

At any hit record species, inputs, visible/transition state, registers,
backtrace, `ticks keep`, `lcd`, `x/8 $4:$dff4`, and `x/6 $0:$ffee`. For Selected
also capture `x/27 $0:$c72e` and `x/3 $0:$c758`; `$c73b-$c73c` is no longer a
miss counter. For New Entry capture `x/41 $2:$d168`, `x/49 $2:$d191` and
`x/98 $2:$d000`; `$d17d/$d17e/$d185` are no longer diagnostic fields.
Save a new-build failure state and record a short video for visual-only issues.

Selected first-publication capture remains `$77:$5edb`. Resolve all labels
again after any future relink; these addresses apply only to the hashes above.
