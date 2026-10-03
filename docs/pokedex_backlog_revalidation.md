# Pokedex Return and Exit Revalidation

Investigation completed 2026-10-02 against the committed Description-paging
fix. This is a diagnostic report, not an integrated game change. Three older
Listing reports did not reproduce in the current link. `DEX-EXIT-01` did:
viewport restoration exposes one displaced outgoing Dex frame before the
normal white exit mask. A private early-mask trial removes that frame without
adding a transition interval.

Disposition 2026-10-02: the user deferred the narrow exit fix and merged
`DEX-EXIT-01` into
[DEX-PERF-01, Dex opening and closing optimization](pokedex_selected_bug_backlog.md#dex-perf-01-optimize-pokedex-opening-and-closing).
The findings and private trials below are retained as evidence for that broader
work, not approval to integrate the early-mask candidate. Production remains
unchanged and the confirmed exit defect remains unfixed.

## Results

| Issue | Current result | Recommended disposition |
| --- | --- | --- |
| `DEX-RETURN-02`, vertically displaced outgoing Description | Not reproduced | Retain as historical/unreproduced pending manual revalidation; no speculative patch |
| `DEX-RETURN-04`, unseen portrait, `-----` or intermediate Listing cursor | Not reproduced | Same; the first revealed Listing already matches its real selection |
| `DEX-GRID-02`, wrong caught-ball OBJ palette | Not reproduced | Same; actual hardware palette, OAM and tile graphics pass |
| `DEX-EXIT-01`, Dex-to-menu shell shift | Confirmed in all 88 exit cases | Deferred and merged into `DEX-PERF-01`; retain the tested early-mask candidate for comparison |

No production assembly, root ROM/symbol/map, live battery save or installed
cartridge was changed. The new instrumentation lives in the host runner under
`DEX_BACKLOG_REVALIDATION_TRACE`; it allocates no cartridge state. The only
modified cartridge is the private exit counterfactual under ignored `build/`.

## Provenance

- Commit: `9f89227efd33a56e064fc010a9ebb4c7d0666d7f`.
- Production ROM SHA-256:
  `7bd5442840f4f190b426d3dbd54bf3e0aa840c087c78f93263c41a8a59862a2a`.
- Symbols SHA-256:
  `a472b6709640e240a2d84f2a52d4df83d01afde56232bd31524f43160430656a`.
- Map SHA-256:
  `418b299843fde9dd8d39a89586b96517bc877de3e79b35cedb7eda2c3dc0e452`.
- SameBoy revision: `213a12ce93d66b105a113debd9396306066a7cfc`.
- Local artifacts: `build/dex-backlog-revalidation-20261002/`.

Fresh matching Listing checkpoints were generated through normal input. The
copied all-seen battery has initialized Unown state and only the first three
species caught. Separate private sparse-seen and all-caught fixtures broaden
coverage without changing the user's save. The all-caught fixture changes
only the caught flags and corresponding save checksums.

## Coverage and Validation

| Suite | Coverage | Result |
| --- | --- | --- |
| Targeted returns | 63 normal and 12 sparse-seen cases | No restoration, viewport, selection or marker issues |
| All-species returns | 373 entry/playback/B-return cases | No return issues; exact authored playback timing and natural completion of all 122 sampled cries |
| Return presentation | 7,211 completed display frames across 448 returns | No displaced Description or placeholder Listing state |
| Caught markers | 746 stable Listing viewports, 3,382 visible marker instances | Correct actual hardware palette, OAM attributes/bank/tile and tile pixels |
| Exit baseline | 88 cases | One displaced colored Dex frame in every case |
| Private early-mask trial | Same 88 exit cases | No displaced frames or rejected palette writes |
| Host/contract unit tests | 161 current tests, including eight new negative controls | Pass |

The targeted returns include six direct species; 1, 8, 9 and 12 internal pages;
active Dusknoir/Weavile cancellation at offsets 0, 4, 16 and 40; A-page-2 then
B; and the final partial Listing row. Conditions are repeated three times.
Sparse fixtures exercise missing entries and caught/uncaught mixtures. Their
follow-up navigation, cache-row, boundary-wrap and reopen checks also pass.

The 373-species return pass additionally audits the complete animation and cry
before B-return. It does not replace the separate active-cancellation conditions
or establish Search/Area/Options behavior. The caught-marker sweeps inspect
stable Listing views; transient B-return frames are checked separately.

Read-only observer controls for direct, one-page and nine-page returns match
unobserved execution exactly in cycles, game state, palettes, maps and rendered
pixels. Hardware palette writes are checked for rejection, rather than treating
correct target buffers as proof of a correct display.

Raw tile-ID differences initially looked suspicious but were legitimate dynamic
digit allocations and animated grid icons. The new checker resolves the actual
selection-header pixels, independently reached selection and static frontpic;
it does not require unrelated animated minisprites to occupy identical tiles.
Negative controls detect real header changes, wrong hardware colors, wrong OAM
palette selection, missing caught markers and an intermediate cursor. Equivalent
physical tiles and legitimate grid animation do not produce false failures.

An indiscriminate `test_*.py` discovery also ran the historical
`test_dex_timing.py` against the current ROM. Its old linked-instrumentation and
cost assertions are incompatible with this link (six failures and sixteen
errors); that invocation is not a current scheduler verdict. The explicit
maintained 161-test suite above passes. Historical tests require the frozen
reference described in [Host timing tools](dex_timing_model.md#historical-reproduction).

## Listing Reports That Did Not Reproduce

### DEX RETURN 02

The former reproducer was an internally paged Description, B-return, a white
cache-rebuild interval, then the old Description appearing eight pixels too low
and moving upward. The current LCD-on cache repair no longer creates that
white/reappearance interval. Across the targeted and all-species return frames,
both hardware `SCY` and its mirror stay zero. The outgoing Description remains
the owner until a complete Listing is revealed.

This supports absence of the reported displacement in the tested paths; it
does not establish the cause of the older eight-pixel screenshot. Retain the
historical report without changing scroll code on speculation.

### DEX RETURN 04

Direct returns, internally paged returns, active cancellation and page-2
returns reveal the correct actual selection. The header is compared as rendered
pixels, the portrait as its uploaded bytes, and the cursor as both logical
selection and actual OAM corner geometry. No unseen portrait, `-----` header
or intermediate cursor is exposed in the observed completed frames.

No current reproduction means there is no supported new cause or fix. The
existing atomic Listing handoff already publishes the tested selection state
together; do not add another placeholder-repair transaction without evidence.

### DEX GRID 02

The caught ball uses OBJ palette 1, tile `$41` in bank 0, with attribute `$01`.
The linked `PokedexListCaughtBallPalette` is checked against the real hardware
palette, not just `wOBPals2`. Its four RGB555 entries are `(0,0,0)`,
`(31,31,31)`, `(31,20,10)` and `(31,7,1)`. The actual `$8410` tile pixels also
match `PokedexCaughtBallGFX`.

All visible caught markers pass, including first/last rows and the private
all-caught roster. The confirmed former palette-3 rejected-write bug is not
assumed to explain a palette-1 report. No marker-specific fix is justified.

If any of these three reports recurs manually, capture a state before the
return, species/text-page selection, internal-page count, whether the animation
or cry is active, and an uninterrupted video. That would permit replay of the
actual failing path instead of extending an already passing synthetic matrix.

## Confirmed Exit Shift

### Reproduction

1. Open the Dex Listing from the Start menu.
2. Press B to leave. Alternatively, open a Description, B-return, then B again;
   internally paging nine entries before returning also reproduces it.
3. Immediately before the normal white transition, the old Dex shell moves five
   pixels right and the right-hand window content disappears into dark BG.
4. The white transition and normal Start menu follow.

The artifact lasts one completed hardware interval, about 16.74 ms at normal
speed. Chikorita, Dusknoir and Weavile were tested on all three routes, and
Regigigas on direct Listing and direct Description-return routes. Eight idle
interval offsets per route give 88 cases; all reproduce the bad frame.

### Cause

The ordering spans three owners:

1. `Pokedex_Exit` in `engine/pokedex/pokedex.asm` marks the Dex for exit and
   selects ordinary VBlank. It does not request the exit mask.
2. `Pokedex.exit` waits for the exit sound, clears sprites/locked IDs, then pops
   the saved `hSCX`, `hWX` and `hWY` before returning.
3. `StartMenu_Pokedex` in `engine/menus/start_menu.asm` rebuilds overworld block
   data through `ReturnToMapFromSubmenu`, because Dex scratch uses that union.
4. Only afterward does `CloseSubmenu` in `home/map.asm` call `ClearBGPalettes`.

The Dex Listing viewport is `SCX=5, SCY=0, WX=71, WY=0`. The saved Start-menu
viewport is `0,0,7,144`. Normal VBlank copies the restored shadow registers
while the old Dex tilemaps and colored palettes are still visible. The measured
map rebuild takes 76,660-84,004 T cycles, more than one 70,224-T display interval.
The delayed white-palette request therefore cannot hide that mixed-owner frame.

This is a cleanup/viewport ownership ordering error, not a palette-throughput
failure, animation miss, audio underrun or missing minisprite cache row. No
palette writes are rejected in these exit traces. The required map rebuild
must remain; removing it would expose the overwritten overworld scratch.

Representative Chikorita direct-Listing trace, relative runner cycle counter:

| Event | T cycles |
| --- | ---: |
| Exit state accepted | 338,348 |
| Dex cleanup begins | 408,432 |
| Saved viewport mirrors restored | 1,607,820-1,607,864 |
| Map restoration begins | 1,608,188 |
| Normal VBlank applies restored viewport | About 1,662,436 |
| CloseSubmenu reached | 1,684,932 |
| White-palette preparation begins | 1,684,980 |

Completed display frame 21 is still the correct Dex; frame 22 exposes the
restored viewport with old colors; frame 23 is white. The generated visual
contact sheet is under
`exit-smoke/chikorita-pages-1-phase0/exit-contact.png` in the artifact directory.

### Private Fix Trial

The trial requests the existing white mask in `Pokedex_Exit`, before cleanup
can restore the viewport. Existing owner-loop and exit-sound waits provide the
publication opportunity; it adds no `DelayFrame` or new global publisher.

Bank `$10` is full, so the trial replaces its nine-byte exit-state body with a
seven-byte farcall/return entry. An eleven-byte helper in the existing Dex
animation bank `$a0` performs the original state updates, then tail-jumps to
the existing `ClearPalettes`. The private binary retains two padding bytes
only to preserve all addresses/checkpoint compatibility. A source integration
could reclaim those two bytes, giving a **net nine ROMX bytes**. No padding
would be taken from RAM or HRAM.

Private ROM SHA-256:
`4c22efd0936463dea45db1c75862bc308edb6afec56bbeece06b9222f276fcab`.
The overlay uses verified free ROMX at `$a0:$7a7c`, leaves all linked observation
points unchanged, and adjusts the cartridge checksum. Only the exit entry,
unused helper space and checksum differ from production.

All 88 matched trials remove the bad frame. Final VRAM, BG/OBJ hardware and
target palettes, actual/shadow OAM, viewport/mirrors, LCD state and Start-menu
cursor/jumptable state match the original. Eighty-four cases have identical
menu-ready cycles; the other four differ by four T cycles. No extra displayed
transition interval or rejected palette write is introduced.

The whole exit remains 59.966-60.259 interval equivalents from exit-state
acceptance to the Start-menu input loop. The first white frame moves from
20.685-20.850 intervals to 1.685-1.850: **19 intervals, about 318 ms, earlier**.
That is a presentation tradeoff, not a navigation slowdown: white replaces
the previous static-Dex dwell. Exit-sound and map/fade sequencing stay intact.

### Alternatives and Recommendation

| Direction | Cost | Complexity and risk |
| --- | --- | --- |
| Early Dex-local mask, tested | Net +9 ROMX bytes, freeing two bytes in bank `$10`; no new ROM0, WRAM0, WRAMX, HRAM or VRAM | Low. Existing waits publish the mask before cleanup. Longer visible white portion is the main tradeoff; all matched trials pass. |
| Keep Dex visible longer, then hide and wait immediately before viewport restoration | About six ROMX bytes for `ClearPalettes` plus `DelayFrame`, before any relocation/helper cost; no new memory | Low-to-moderate. Bank `$10` has no space; code must move or use a helper. Expected extra wait of up to one interval needs measurement, and cleanup order must be re-audited. Not tested in this pass. |

Recommend the tested early Dex-local request if the earlier white appearance
is acceptable. It fixes the proven ownership gap without modifying shared
map/menu cleanup or adding a wait. If retaining the outgoing page longer is
preferred, measure the second option rather than assuming its extra wait is
free. Neither option requires new ROM0, WRAM0 or HRAM allocations; the
recommended one reuses existing `ClearPalettes` and palette-dirty state.

That is the narrow fix recommendation from this investigation. The subsequent
user decision is to defer it and optimize entry/exit together under
`DEX-PERF-01`; the broader design may choose different sequencing.

Before integration acceptance, rerun the exit matrix and focused Listing
restoration tests on the actual relinked ROM, then manually compare the earlier
white transition. Options, Search, Unown and Area owners are outside this
focused Listing-exit matrix and require targeted controls if their exit routes
are included in a production change.

## Reproduction Tools

The reusable host-only entry point is
`tools/dex_timing/backlog_revalidation.py`. It verifies ROM/symbol provenance
before consuming saved Listing checkpoints. Output must remain under ignored
`build/`; success exit status means the diagnostic ran, so inspect report
`issues` and `shifted_frames` rather than treating exit status alone as a pass.

With fresh matching checkpoints prepared by the existing cold-Listing runner:

```sh
PYTHONPATH=tools:. python3 -B -m dex_timing.listing_restoration \
  --checkpoints build/dex-backlog-revalidation-20261002/checkpoints \
  --output build/dex-backlog-revalidation-20261002/returns-all \
  --repeat 3 --follow-up --verify-observer --expect-fixed

PYTHONPATH=tools:. python3 -B -m dex_timing.backlog_revalidation \
  --checkpoints build/dex-backlog-revalidation-20261002/checkpoints \
  --output build/dex-backlog-revalidation-20261002/return-frames \
  --mode returns --verify-observer \
  --return-suite build/dex-backlog-revalidation-20261002/returns-all

PYTHONPATH=tools:. python3 -B -m dex_timing.backlog_revalidation \
  --checkpoints build/dex-backlog-revalidation-20261002/checkpoints \
  --output build/dex-backlog-revalidation-20261002/returns-373 \
  --mode return-sweep --jobs 6

PYTHONPATH=tools:. python3 -B -m dex_timing.backlog_revalidation \
  --checkpoints build/dex-backlog-revalidation-20261002/checkpoints \
  --output build/dex-backlog-revalidation-20261002/exit-baseline \
  --mode exit --phases 8
```

For sparse returns, give `listing_restoration` a new output directory and
`--sparse`, then include that directory as another `--return-suite`. For marker
checks use `--mode markers`, with a separate output for the `--caught-all`
fixture. For the private exit trial use another output and `--mode exit
--phases 8 --prototype`. Do not load a production game/save from these fixture
directories. All reported addresses belong to the provenance link above and
must be resolved again after relinking.
