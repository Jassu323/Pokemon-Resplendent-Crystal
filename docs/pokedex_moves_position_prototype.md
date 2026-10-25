# Moves Dex Shared Position Prototype

The [combined Dex session position implementation](pokedex_session_position_prototype.md#production-integration)
was manually accepted and integrated into production on 2026-10-15, byte-for-byte
matching the fully qualified review build. It includes Modern/Legacy remembrance
and the independent Moves bookmark. Earlier Moves-only binaries and evidence
below remain historical; their pending-promotion notes no longer describe production.

## Accepted Moves-Only Session Revision

The user revised `DEX-PREF-02` on 2026-10-14: position survives leaving Moves
Mode and closing the Dex during play, but **not** restarting the game. The
Type/Alphabet sort preference still survives normal Save/Continue. Search
Results remain separate from the ordinary-list bookmark.
The user accepted this revised prototype; it was subsequently included in the
fully qualified combined build and production integration linked above.

- Review ROM and matching all-333-moves-seen private save:
  `build/dex-moves-position-session-20261014/review/pokecrystal-dex-moves-position.*`.
- Revised ROM SHA-256:
  `4143902901b43a33b19dc9a901261ee35f2844e435796473d2fd468333ba5192`.
- Current source and full production-relative patch: that build directory's
  `candidate/` and `candidate.diff`. Apply the original tracked
  `tools/dex_timing/probes/moves_position.diff` followed by
  `tools/dex_timing/probes/moves_position_session.diff` to reproduce the source
  changes over the frozen production baseline, then build the private copy.
- Successful Continue clears all four bookmark bytes **after** save loading,
  confirmation and the RTC check. New Game already clears the same region.
  Keep this reset in the actual new-session path, not generic loading or save
  validation that can run during play. Do not clear `wLastMovesDexSort`.
- The four bytes remain in existing saved-player padding to avoid relocating
  fields or allocating new RAM. Normal Save may copy them, but Continue always
  discards them. There is no custom SRAM write or save-format change.
- Increment over the previous prototype: **8 ROMX bytes**, zero RAM or other
  allocation growth. Total over production: **243 ROMX bytes**, four existing
  padding bytes assigned, zero additional ROM0/WRAM0/WRAMX/SRAM/HRAM.
- Focused normal-input checks pass in all four Modern/Legacy-origin and
  Type/Alphabet combinations: session close/reopen, Search isolation, normal
  saving without losing the live bookmark, actual A+B+Select+Start reset,
  fresh-launch Continue, retained sort, first-entry visuals and a new bookmark
  after reset. Four soft resets and four cold reloads start at row/scroll zero.
  Existing RAM addresses and protected production files remain unchanged.
- Evidence: `session-manifest.json` and
  `focused-tests-attempt-3/results.json` in the new build directory. Earlier
  attempts are retained: the test driver needed longer start-menu key polls
  after Save; no game fix was needed. Re-run the focused observer with
  `PYTHONPATH=.:tools python3 -m tools.dex_timing.moves_position_session` from
  the repository root, using a fresh review output directory.
- **The full regression suite was not rerun**, as requested. The extensive
  results below apply only to the earlier persistent-position ROM, not this
  revised link. Production is not integrated.
- Previous root-folder review files were relocated intact into
  `build/dex-moves-position-20261014/root-review-archive/`, preserving any
  review-save changes. New prototypes and their review bundles stay in `build/`.

## Historical Persistent-Position Build

Everything below documents the earlier fully qualified implementation and its
frozen evidence. Its across-reset position behavior is superseded above.

2026-10-14. Private implementation of `DEX-PREF-02` over production commit
`b439cf4e89b39187af6e5937e0f960ab2267a740`. One bookmark remembers the current
ordinary Moves list's permanent move identity and viewport. Changing sort still
starts at the beginning; Search Results do not replace this bookmark.

Targeted qualification and the full standard/supplementary campaigns pass with
no new game regressions. The private prototype is ready for manual review;
production remains unchanged.

## Frozen Inputs And Review

- Production SHA-256:
  `942d1495404ac2ee41793ee4871ac5c4b4f57016102a50ef4fda8a0a161095bc`.
- Candidate SHA-256:
  `28e0f080aec15caee3f6cbffc056aa2bef91aa13d000f1a6df1d63505a618340`.
- Evidence and frozen sources: `build/dex-moves-position-20261014/`.
- Candidate source: that directory's `candidate/`; production control:
  `baseline-source/`, matching `rollback/` binaries and `rollback-source.tar`.
- Complete source patch: `tools/dex_timing/probes/moves_position.diff`, also
  retained as `candidate.diff` with the build.
- No production source, ROM, save or emulator-library file is updated by this
  prototype. Review saves are private fixtures, not the player's battery.
- Archived former root review ROM: `root-review-archive/pokecrystal-dex-moves-position.gbc`, with matching
  `.sym`, `.map` and `.sav`. The private save has all 333 moves seen and a
  normally saved Alphabet bookmark at scroll 152 / row 5. Cold Continue of the
  published bundle restores permanent move 67 and passes the complete visual
  audit; the source save hash is unchanged by that check.
- Final acceptance: `position-manifest.json` in the evidence root records
  `full_regression_passed: true`, `production_integrated: false`.

## Full Regression Results

All sixteen standard phases pass, including the explicitly retained timing
retry described below. `runtime-regression/full-regression.json` reports
`merge_ready: true` with no new issues; that flag does not authorize production
promotion. Finalization separately requires all targeted and supplementary
reports, exact ROM identities, unchanged existing RAM addresses and exactly
the two intended assembly owners.

| Coverage | Result |
| --- | --- |
| Pokemon Dex, orders, Search, layout and owner returns | 4,479 cases, no failures |
| Existing Moves/Search/sort preference coverage | Filtering, UI, visuals, navigation, keyboard, cursor, footer, save and preference checks pass |
| Discovery persistence | 2,380 helpers, 1,490 cold boots, 152 interrupted writes, 150 interrupted repairs and five lifecycle cases pass |
| Acquisition/learning | 12,276 contracts, 59 positive/negative sources and migration/interruption checks pass |
| Battle-use discovery | 4,724 contracts, 400 semantic cases and eight Bide cases pass |
| Battle rendering | 7,312 calls / 3,656 pairs across all 333 moves and 28 auxiliaries; exact timing, logical sequence and rendered frames |
| Ordinary battle-input matrix | 1,332 rows / 666 pairs; identical exception identities |
| Separate 100-move matrix | 1,600 rows / 800 pairs; exact animation durations |
| Gameplay, clocks and menus | 22 paired gameplay scenarios, 24 transitions, 1,792 menu input contracts and 464 custom-menu cases pass |
| Sampled audio | 960 rows / 480 pairs accepted; 32 pre-existing misses per link remain identical |
| Selected animation playback | 2,238 cold/paging/warm cases across both presentations pass |
| Current host contracts | 87 pass, zero skips; ten additional bookmark/retention tests and 22 Description/ancestor contracts on each link also pass |

Supplementary Selected Info/Moves sweeps, input stress, 1,056 feature cases,
115 panel returns and font-reuse checks pass. All 1,492 active Info-to-Description
returns pass, maximum 5.612 frames, below the eight-frame ceiling. Six-model
active returns add 1,536 passing cases. All six CGB revisions pass Type visuals,
Unown paging/returns and decoder checks; both 122-song music/SFX stress runs,
including held navigation, pass.

New Entry passes all 746 generated-species cases, 60 visual cases, the full
8,272-case historical input-identity union explained below, four return flows
and four nickname flows. Dex lifecycle passes 336 cases, 36 secondary routes
and 88 hardware exit-publication cases: no early colored reveal, completed-screen
corruption or rejected palette writes. Twelve button-cue register comparisons
match exactly and all twelve duration checks pass their physical-tick contract.

No new cartridge defect requires a fix before review. Known baseline limitations
remain, rather than being relabeled as passes: the 666 ordinary battle pairs
include 632 clean pairs and 34 identical exceptions per link (19 conditional
move fixtures, 13 ending/KO/switch return cases and two Sand Tomb hangs).
Historical host reports retain the same six failures, sixteen errors and 103
skips across 187 tests on each link; their detailed normalized reports match.
The existing sampled-audio and capture-startup observations also match the
production control. Sand Tomb and the separate Battle Tower backlog are not
fixed here. The independent Tower addendum and physical hardware/manual audio
acceptance are outside this standard campaign.

## Behavior And Ownership

The initial 48-byte shared Info workspace clear and the existing sort restore
remain. After Search reset, `PokedexMovesMode_RestorePosition` reads the saved
bookmark, checks its tag/sort and row, and searches the active permanent-ID order
table. Missing or invalid records start at cursor/scroll zero in the current
sort. No transient ID is allocated and no discovery flag is written.

For a valid move at ordinal `i` and saved row `r`, derive
`scroll = clamp(i - r, 0, NUM_ATTACKS - 8)` and `cursor = i - scroll`.
The current build asserts at least eight moves. This reproduces an unchanged
order's exact viewport, while future insertions/reordering keep the selected
identity and its row where possible. Existing move IDs must remain stable;
arbitrarily renumbering permanent identities is not a supported save migration.

`PokedexMovesMode_RememberPosition` runs only after list drawing/publication.
It rejects active Search Results and invalid sort, ID or row values. It stores
the current selected identity and row, with the tag last. It is not called from
the generic form/input loop, because Search forms clear their active flag while
the selected scratch may still describe a result. Existing Search backup/cancel
logic retains the ordinary cursor/scroll. Direct Select exit from Results leaves
the ordinary bookmark intact.

Changed-sort reset already redraws the first entry, naturally replacing the one
shared bookmark. Same-sort confirmation and popup cancellation redraw the same
position. Unknown entries can be restored without exposing their names, icons,
stats or description. Normal Save persists progress; merely browsing does not
write SRAM. Power-off or declined Save retains the previously saved bookmark.

Both helpers preserve AF/BC/DE/HL and the incoming raw WRAM bank selection,
including bank zero's alias. They add no VBlank, timer, LCD, palette, DMA or sound
work, and require no additional shared restoration/display buffer.
Build-time assertions keep both order tables resident with the restore helper
and enforce the bookmark's bank/word-row layout. These assertions add zero ROM
bytes; a later bank split must update the lookup rather than silently reading
the wrong bank. Rebuilding with them retains the exact qualified ROM hash.

## Exact Resource Cost

| Resource | Increment, decimal bytes |
| --- | ---: |
| ROMX | 235 |
| Existing saved-player padding newly assigned | 4 |
| Allocated WRAMX / SRAM | 0 / 0 |
| ROM0 / WRAM0 / HRAM | 0 / 0 / 0 |
| Graphics / VRAM / OAM allocations | 0 / 0 / 0 |

WRAMX bank 1 fields: tag/sort at `$d9e4`, permanent move word at `$d9e5-$d9e6`,
cursor row at `$d9e7`. Tags `$b0` and `$b1` associate Type and Alphabet with this
format. Eight padding bytes remain. Existing `wLastMovesDexSort` stays at
`$d9e3` and the following scene field at `$d9f0`. All old RAM symbols retain
their addresses, and all save copy lengths/checksum coverage stay unchanged.
Normal player-data saving, backup recovery, Continue and New Game already
cover this region; no discovery-record version or migration changes.

The linked game delta is confined to `engine/pokedex/pokedex_moves_mode.asm`
and `ram/wram.asm` in the private source. Existing order tables and artwork are
unchanged. The 235-byte cost is within the scoped 200-350-byte estimate.

## Targeted Qualification

Native SameBoy helper tests pass 12,641 cases:

- 5,216 exact legal viewport round trips across both sorts, covering every row
  and scroll offset, with incoming WRAM banks varied.
- 5,328 remember contracts across all 333 identities, both sorts and eight raw
  WRAM selections; registers, workspace and adjacent saved bytes preserved.
- 764 invalid/mismatched tag, ID and row restore cases default safely.
- 1,332 valid-identity boundary-clamp cases.
- Active-results guard plus unchanged discovery/garbage-collection state and
  zero helper SRAM writes.

Normal-input and persistence checks also pass:

- 32 complete contexts: Modern/Legacy origin, Type/Alphabet and every cursor
  row; Modes exit/reentry, full Dex close/reopen, same/changed/canceled sort,
  Search cancellation and direct Results exit.
- 16 unseen-entry restores after Selected Info, Selected Moves, Unown and Type
  Matchups. Names remain dashes and the detail/icon panel remains empty.
- Four keyboard/zero-results navigation/return cases, both sorts and both exit
  paths; no result, query or keyboard cursor replaces the ordinary bookmark.
- 16 normal Save/cold-Continue and primary/backup/legacy/malformed-value cases,
  plus the existing five-case New Game/overwrite/deletion lifecycle.
- Fourteen interrupted-save prefixes at both copies' five preference/bookmark
  bytes and two checksum bytes: cold boot recovers a complete old or new record,
  never a partial bookmark. Save cancellation and unsaved New Game preserve the
  previously saved preference/bookmark.
- Ten focused host tests pass, including source/memory limits, exhaustive
  evidence identities and lossless trace-compression controls.

Counts overlap; they are not a single independent total. Helpers and replayed
write prefixes are distinguished from ordinary-button integration cases.

## Performance

Forty-eight fresh entry captures form 24 production/candidate pairs: both sorts,
top/middle/bottom positions and four input phases. The prototype restores the
requested identity/viewport, while the production control starts at the first
entry. All sampled complete-entry deltas are **0 ms / 0 display frames**.
This is a bounded sample, not a claim about every input phase or future catalog.

Native helper measurements over the exhaustive valid restore sweep are
0.093-5.325 ms, median 1.603 ms, including incidental interrupts. These are
approximately 0.006-0.318 display frames, median 0.096. The scan runs on entry,
not each frame. It fits within the existing publication schedule in the paired
sample. Physical display frames are 70,224 ticks at 4,194,304 Hz, 16.742706 ms.

Other measured differences against the production control:

| Measurement | Difference, ms / display frames |
| --- | ---: |
| Selected entry, first/complete display and reveal, 512 pairs | 0 / 0 |
| All-move renderer and 100-move animation duration pairs | 0 / 0 |
| Valid load, legacy migration, full migration, recovery | 0 / 0 |
| Save routine, four-sample fixture median | +0.025034 / +0.001495 |
| Full Dex opening, lifecycle paired median | +0.000477 / +0.0000285 |
| Full Dex closing, lifecycle paired median | -0.000477 / -0.0000285 |

These sub-millisecond differences do not indicate a visible display-frame
regression. Save/load measurements are named procedure bodies, not the entire
dialogue/sound sequence. Button-cue register/duration checks are separate.

## Test Harness Corrections And Retention

The first host driver setup omitted the battery path and selected the native
helper core instead of the visual core. This was corrected before successful
UI/save/timing runs. Failed output folders are retained; successful retries
use fresh directories. A new edge test initially treated B on an empty keyboard
as cancellation; existing naming parity instead keeps B as backspace. The test
now checks that state, then uses START to highlight End and A to accept.
No cartridge change was required after the first successful 235-byte link.

One parallel save/load timing job initially started before the full legacy-save
fixture existed, so its observer exited before loading the cartridge. Repeating
that unchanged job after persistence/migration fixture generation succeeds.
Its initial failure log and phase record are retained alongside the explicit
retry; other completed timing subcommands are not relabeled as reruns. Future
parallel campaigns must finish fixture generation before starting this job.

The New Entry sweep generates its startup taps from each fresh catch donor's
observed first publication. Groudon now starts at interval 48 on both the
unchanged production control and candidate, versus 49 in the preceding
campaign. All other generated baseline durations/startup positions match that
campaign. The normal sweep therefore generates 8,270 cases, not 8,272; the only
absent identities are Groudon's startup A/B taps at interval 48. Both are
explicitly replayed and pass on each current link, four additional calls total.
Final qualification checks unique generated identities and equality of the
candidate's union with the prior 8,272-case set. No historical input boundary
is skipped, and the matching current production/candidate startup is not a
new feature timing regression.

The initial assembly attempt used an unsupported `MAX` expression. Replacing it
with the explicit catalog-size assertion and existing count-minus-eight bound
produced the qualified link. The retained source patch is that linked version.

To avoid another multi-gigabyte uncompressed menu-trace expansion, the optional
`DEX_COMPRESS_TRACE_ROOT` setting losslessly gzips consumed JSONL traces only
inside this fresh run. `load_trace` transparently reopens the `.jsonl.gz` sibling
when the original path is absent. Reports and checks retain their original
coverage; old evidence and files outside the configured directory are untouched.
Trace rows referencing `.jsonl` should be replayed through `load_trace` or their
adjacent gzip file. The compression mode has positive, replay and outside-root
negative controls.

## Reproduction

Use a fresh output for a new run; the builder deliberately rejects an existing
campaign directory. No old emulator CPU checkpoints may be reused for a new link.

```sh
python3 -B tools/build_moves_position_prototype.py prepare --jobs 6
python3 -B tools/build_moves_position_prototype.py apply
python3 -B tools/build_moves_position_prototype.py build --jobs 6
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.moves_position_campaign prepare
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.moves_position_campaign standard --phases setup
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.moves_position prepare
```

Then run `moves_position` actions `helpers`, `ui`, `saves`, `save_edges`, `owners`,
`search_edges`, and `timing`. `save_edges` requires completed `saves`; visual
actions require standard setup. Run the standard campaign phases and separate
supplementary actions through `moves_position_campaign`, as defined by the
[full regression suite](full_regression_suite.md). Full reporting requires the
exhaustive animation and six-model Type/audio evidence. Finish with current-link
host tests, `report` and `finalize`; do not treat partial output as acceptance.
The New Entry boundary union and additional Description/ancestor contracts are
explicit finalization prerequisites for this frozen run. Use `publish` only
after successful finalization; it refuses to overwrite existing review files.
