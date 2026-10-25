# Pokedex Egg Page Qualification Prototype

Date: 2026-10-17. The private prototype and full regression excluding Battle
Tower are complete, with no new correctness failure identities. This does not
mean every raw diagnostic is clean: matching production exceptions and the
separate TM-inheritance bug remain explicit below. Production and the player's
main save are protected and unchanged. The user authorized disposal after
qualification on October 17; the prototype and its recordings/raw evidence
are now retired, not promoted. See [build retirement](pokedex_build_retirement.md).
The artificial egg lists are not approved production species data. Paths below
identify the original run; they are no longer retained review downloads.

## Review Build

- ROM: `build/dex-egg-placeholder-20261017/pokecrystal-dex-egg-placeholder.gbc`.
- Adjacent `.sav`: private all-species review battery, retaining 99 Master Balls.
- Candidate source: `build/dex-egg-placeholder-20261017/candidate/`.
- Frozen production source: `build/dex-egg-placeholder-20261017/baseline-source/`.
- Production baseline commit: `aa5a89dd4`.
- Production SHA-256: `302099f5836115c776de6606379820fbc661c82824aee438364afd4e7f7834e9`.
- Prototype SHA-256: `d76657ba00cb3b24b4126dbf552890e3b6b2c73d4a11a67e3d0fd43286ebef5b`.

The native figures below refer to generated, declared test contexts or ordinary
Dex controls as identified. Direct breeding helper calls do not claim a
complete natural daycare breeding session. No cross-link checkpoint is reused.

## Temporary Data

42 currently empty, suitable families receive clearly marked temporary lists.
Their 91 members share those lists through the existing family graph, including
the Hoenn starters, Ralts/Gallade, Snorunt/Glalie/Froslass and Riolu/Lucario.
Existing nonempty lists remain untouched. Empty genderless/legendary controls
remain empty. Suitability is fixture selection, not final species-data approval.

| List Length | Breeding Pages | Families |
| --- | ---: | ---: |
| 6 | 2, with a one-row last page | 11 |
| 10 | 2 full pages | 11 |
| 11 | 3, with a one-row last page | 10 |
| 15 | 3 full pages | 10 |

The 436 temporary move words plus 42 terminators add 956 decimal ROMX bytes.
There are 226 added Breeding pages per complete base-species owner traversal.
The lists deliberately include indices 1, 255, 256 and 333, so a visually
successful test also has to handle the 16-bit move/index boundary. They are
not attempts at canonical egg sets or move balance.

## Findings

### Custom Egg Data Needs More Bank Capacity

The initial unrelocated build fails: ROMX bank `$12` has only 248 spare bytes,
and the 956-byte addition pushes the following TM/HM Case past its bank by
708 bytes. This is a real layout constraint, not a Dex renderer failure.
The failed linker output remains in `build.log`.

The prototype relocates the complete existing `Egg Moves 3` section, including
its 16-bit pointer table, into available bank `$bc` space after the custom Dex
entries. `ORG $517b` preserves the unrelated Night Songs/menu addresses in
bank `$12` without allocating filler bytes. Strict controls compare the
surrounding bytes, RAM addresses and ROM0 bytes except the checksum. The old
246-byte location becomes free; linked net allocation growth is only the
956 bytes of artificial lists. No additional bank is counted as occupied data.
The lists use bank-relative word pointers, so the pointer table and its local
lists move together; scattering only the new lists across banks would need
a different pointer/reader arrangement.

No renderer, animation, interrupt, save-format or gameplay algorithm is changed.
ROM0, WRAM0, WRAMX, HRAM and SRAM growth is zero. The data relocation and
build-after-relocation log are retained with the private candidate. Expanded
legitimate data will need its own placement check rather than assuming the
old bank has room.

### Existing Gameplay TM Inheritance Bug

The focused probe also identifies `BREED-MOVE-01`, documented separately in
[Breeding Bug Backlog](breeding_bug_backlog.md). The TM fallback uses an AND
test where a 16-bit zero check is required, so it stops on DynamicPunch 223,
the first TM entry. Rest is not inherited through that fallback in either
production or the prototype. Four strict raw reproduction checks remain
failed in `tm-fallback/report.json`; no new failure identity is introduced.

The explicit egg-list path is separate and passes, including indices above
255. The old TM fallback has not been fixed or silently included in a clean
breeding claim. The initial probe that assumed correct TM fallback is retained
in `egg-checks.log`; corrected scope and separate baseline reproduction are
recorded under `egg-checks-v2/` and `tm-fallback/`.

## Completed Focused Checks

- Independent source/family/page checks cover all 373 species, including all
  91 changed members and unchanged streams for the other species.
- Nine private boundary/isolation controls pass, including list lengths
  6/10/11/15, acceptance at 19 total Mov pages, rejection at 20, invalid moves,
  relocated-bank isolation and unchanged surrounding code/RAM.
- 1,040 native `GetEggMove`/`InitEggMoves` calls complete with no new explicit
  egg-list failure. These include every temporary list entry, absent-move
  controls and all four inherited move slots with indices 1/255/256/333.
  The one TM-overlap exception is recorded, not treated as correct TM behavior.
- 252 additional caller-state checks cover each family's first/last lookup and
  four-slot initialization on both links. They preserve ROM bank, owning WRAM
  bank, stack and SRAM enable/active-bank state; `GetEggMove` preserves BC/DE.
  These use the valid owning WRAM bank, not arbitrary-bank entry fixtures.
- Four reusable host tests in `tools/test_pokedex_egg_pages.py` generate and
  discard their own fixtures, covering long lists, category preservation,
  family sharing, 19/20-page bounds, unknown moves and conflicting descendant
  lists. No dummy species data must be retained in the normal game source.
- Modern/Legacy Description regression: 746 species/presentation cases,
  2,482 captured screens and 732 late-page Area cases pass unchanged.
- Each link passes 87 standard host cases and four reusable long-list controls.
  Eight additional Description controls pass on the candidate. The
  pre-relocation numeric-copy reference is kept separate from production.

## Review Evidence

`review/egg-pages.png` contains exact native panels for Treecko (6 moves),
Ralts (10), Mightyena (15) and Froslass (11). The agent inspected the contact
sheet: page badges, headings, all rows, partial-page clearing, borders, type
icons and footprints show no anomaly. The data choices remain artificial.

The ten captured Breeding-page requests have a median accepted-input-to-full-
display latency of 48.546 ms / 2.900 display frames. Their range is 31.804-
49.202 ms / 1.900-2.939 frames. These are ten illustrative ready-paced requests,
not the full-catalog timing distribution or a production speedup claim;
production has no matching new Breeding pages.

`review/production-mightyena.mp4` and `review/candidate-mightyena.mp4` retain
actual display-rate playback and native audio. Unmodified WAVs and per-page
captures remain beside each native run. Recordings are for manual review;
automated waveform/playback checks are not listening approval.

The complete ready-paced traversal contains 452 added Breeding-page requests,
226 each in Selected and registration. Median accepted-input-to-complete-display
latency is 48.548 ms / 2.900 display frames; the range is 30.607-82.193 ms /
1.828-4.909 display frames. The maximum is Garchomp's first Breeding page in
registration (82.193 ms / 4.909 frames); Selected's matching page takes
82.031 ms / 4.899 frames. These are new-page measurements, not matched
production deltas. The earlier ten-panel values are separate recorded samples.

The continuous scan also retains four phase-sensitive Info differences between
Selected and registration. Fresh production controls replay all eight named
operations, with exactly zero candidate-versus-production timing delta:

| Species And Info Operation | Selected ms / Frames | Registration ms / Frames |
| --- | ---: | ---: |
| Blissey, first page | 64.396 / 3.846 | 97.959 / 5.851 |
| Cyndaquil, second page | 81.923 / 4.893 | 115.571 / 6.903 |
| Stantler, first page | 64.530 / 3.854 | 98.285 / 5.870 |
| Togekiss, wrap to Stats | 65.507 / 3.913 | 99.021 / 5.914 |

These are existing active-playback admission differences, not new placeholder
regressions. The comparison is scoped to these eight exact operations, not a
claim of an exhaustive production latency sweep. The candidate also passes
144 active/settled input-phase probes without content/playback failures.
Raw evidence is under `alert-baseline/` and `additional.json`.

## Full Regression And Retention

The established full regression completed under
`build/dex-egg-placeholder-20261017/full-regression/`, with current production
as the frozen baseline and Battle Tower explicitly excluded. All 37 action
gates pass. `qualification.json` reconciles the fresh native results, protected
inputs, focused controls and final harness snapshot. The standard report is
`full-regression/runtime-regression/full-regression.json`. Coverage counts
overlap and must not be summed into a grand total.

| Coverage | Completed Result |
| --- | --- |
| Main Dex | 4,479 cases; Modern/Legacy listings, search, popovers, navigation and Selected handoffs pass |
| Moves Search | 1,692 filters, 1,406 visuals, 2,686 navigation and 3,840 naming-cursor cases pass, plus form/return controls |
| Selected | 746 Info, 746 Mov and 400 stress cases pass; six emulated CGB revisions pass |
| Portrait playback | 2,238 cold/paging/warm cases across both presentations pass |
| Description | 746 presentation cases, 2,482 captured screens and 732 late-page Area returns pass |
| Extra Legacy/phase coverage | All 91 affected species, 1,605 operations and 144 active/settled probes pass |
| Registration and Selected catalog | 398 registration species/forms and 373 Selected species; 15,134 page/tab operations, 17,638 exit replays and 12,736 stress cases pass |
| All move animations | All 333 moves; 7,312 renderer calls and 666 native production/candidate pairs; no new issue identities and exact physical animation timing |
| Ordinary battle loop | 1,600 contexts covering 100 moves, both sides, both links and multiple input phases pass |
| Sampled audio | 960 cases / 480 pairs; waveform segments and known-miss identities match production |
| Capture and continuation | 104 main cases, eight supplemental cases, 104 delivery cases and eight Pay Day controls pass |
| Persistence | 2,380 helpers, 1,490 cold boots, 152 interrupted writes and 150 interrupted repairs pass, plus lifecycle controls |
| Surrounding systems | Acquisition/discovery, custom menus, PC/daycare, hatch, learning, evolutions, Unown, Type Matchups, bookmarks and return paths pass their established gates |

Ordinary listing entry has 512 matched production/candidate pairs across both
presentations, four hover durations and four input phases. First-pixel and
complete-display deltas are exactly 0.000 ms / 0.000 display frames in every
pair. Valid load, legacy load, full migration and recovery helper timings also
match at 0.000 ms / 0.000 frames. The save helper measures 0.028372 ms /
0.001695 frames faster, a subframe observation rather than an optimization
claim. Accepted and canceled normal save menus both survive cold reload.

Retained raw exceptions and coverage limits:

- `BREED-MOVE-01`: four strict raw failures, two per link, with identical
  identities. The explicit egg-list path passes; the TM fallback is not fixed.
- Native animations retain 34 matching issue pairs out of 666, with no
  differing issue identities. This is not a claim that all raw native
  animation fixtures are clean.
- Sampled-audio traces retain 32 known-miss markers per link. All 480 paired
  waveform sequences and normalized miss identities match; these markers are
  not relabeled as clean playback or newly attributed to the egg lists.
- The separate historical diagnostic host group has the same six failures,
  16 errors and 103 skips on both links. These archived assumptions are not
  the current 87-case host acceptance group, which passes without skips.
- Registration proves 9,066 unique committed B/End exits. The larger replay
  count includes duplicate/pending attempts. Pending-at-leave cancellation is
  actually observed for Info B, not for every tab/button combination; work
  can finish before dispatch or during footer travel. The raw summary retains
  these limitations rather than claiming every pending path was observed.
- Agent contact-sheet inspection is complete. User visual/listening approval,
  physical hardware validation and a natural complete breeding session are
  not claimed by this qualification. Battle Tower was deliberately not run.

The local orchestrator is `run.py`; `egg_checks.py`, `bank_checks.py`,
`additional.py` and `media.py` supply the focused native/boundary, caller-state,
Legacy/phase and recording work.
`inputs.json` and the campaign manifest protect the root ROM/symbol/map and
player saves; all protected hashes match at completion. `source-diff.json`
compares 8,165 source/art paths and identifies only the egg-data and link-layout
changes. No production integration is requested or performed for this test.

Once approved, the placeholder lists can be discarded without removing the
reusable controls. Future legitimate content still needs its source validation,
page-limit check and a focused content regression. The bank-placement finding
and separate gameplay TM-inheritance issue must not be forgotten when the
artificial lists are removed.

Conclusion: the existing Dex renderer handles these two/three-page Breeding
lists without new graphics, RAM or renderer code. This completes the private
long-list technical qualification, not final species-data approval. Keep
`DEX-DATA-03` open for the legitimate content pass. Dummy lists need not be
retained in production to preserve this coverage.
