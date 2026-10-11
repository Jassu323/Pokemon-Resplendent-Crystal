# Moves Dex Acquisition And Learning Prototype

2026-10-08. Private stage-two prototype based on the accepted scrollbar/popup
owner at `build/dex-moves-scrollbar-20261007e`. No production integration,
commit, installed-emulator replacement or modification of a player save.

## Review Files

- ROM: `build/dex-moves-acquisition-20261008/pokecrystal-dex-moves-acquisition.gbc`
- Matching save: `build/dex-moves-acquisition-20261008/pokecrystal-dex-moves-acquisition.sav`
- Evidence/qualification: `build/dex-moves-acquisition-20261008/final-qualification.json`
- Native known/unseen screenshots: `build/dex-moves-acquisition-20261008/manual-review/`

ROM SHA-256:
`19d039e49728a59767ea474d25308c13f1150abe1e45e3c44823ab75eede6db4`.
Review save SHA-256:
`bf3b8887a932a17fd15eb2e4b8c7bc7abaa7eb777e552d075be6688d31c68307`.

The review save has **seven naturally bootstrapped discoveries**, not the old
25-bit seeded fixture: Tackle, Body Slam, Disable, Razor Leaf, PoisonPowder,
Confusion and Reflect. It includes all 57 TMs/HMs, the TM/HM Case, Apricorn Box,
10 of each Apricorn, 76 Rare Candies and unlocked Unown Mode for convenient
review. These inventory/progression edits are declared private fixtures;
discovery itself comes from the ROM's legacy ownership scan, followed by its
real Save routine and a successful cold reload.

Teach an eligible party member an unseen TM/HM move, reopen Moves Dex Mode,
and check that the name/details appear. Declining the learn prompt must leave
an unseen move hidden. Save normally, restart and Continue to check persistence.
Receiving a Pokemon records its current moves; receiving an egg does not.
Egg moves are recorded when it hatches. Daycare records only the final moves
returned to the player, not intermediate moves subsequently overwritten.

**Battle-use discovery is not implemented in this stage.** Merely using or
seeing an unseen move, including Metronome/Sketch/charge/Focus Punch cases,
does not mark it yet. Those first-use policies belong to stage three. Learning
after a battle is included here because it is a committed learning event.
Owning a TM, browsing its description and opponent generation do not count.

The original visual safe rollback remains frozen at
`build/dex-moves-safe-rollback-20261007`. The immediately preceding accepted
scrollbar ROM/save/symbols/map are also protected by this build's manifest;
its ROM hash is
`299b74dc8e226c4c67ed7f816b1ee983a8af181c44a847d2cbd9cf83183d5b1d`.
Production ROM/symbol/map and protected previous artifacts are hash-checked
again by final qualification.

## Hook Design

The existing permanent-index bitmap and SRAM format are unchanged. Discovery
hooks update WRAM only; normal Save persists the existing primary/backup
records. A preserving call macro saves AF/HL, and the called wrappers preserve
BC/DE and the caller's WRAM bank. Ownership walkers also restore open SRAM
bank ownership or leave SRAM closed if it was closed. The unused hardware
bank selector while SRAM is disabled is not promised to remain identical.

| Source | Commit point |
| --- | --- |
| Ordinary gifts/starters | Successful `GivePoke` party/PC destination |
| Wild captures | Successful party/PC insertion branches in `PokeBallEffect`, after restoration of the actually acquired moveset |
| NPC trades | Received mon's completed stat/move construction |
| Dragon's Den Dratini | Each special/normal direct move assignment, in addition to ordinary gift discovery |
| Bug Catching Contest | Actual retained party/PC insertion; a pending contest catch is not owned yet |
| Eggs | Hatch replaces the party's egg marker with its actual species |
| Daycare | `RetrieveBreedmon` has finished producing the returned moveset/experience |
| Learning | `LearnMove.learned`, after successful empty-slot or replacement commit |

Level-up, TM/HM, tutor and evolution learning share that successful-learning
hook. Known/incompatible/declined attempts never reach it. Generic stat or
party generation is deliberately not hooked: that would discover opponent or
temporary tutorial moves and would blur acquisition boundaries.

The Dratini policy can retain both the ordinary gift's initial moves and the
subsequently assigned special moves. It uses the explicitly approved direct
assignment policy, with monotonic seen flags, rather than deleting an earlier
discovery when a move is replaced.

## Migration And Recovery

Legacy or recoverable/damaged extension loads scan six party slots, occupied
daycare slots, the live active PC box and the other thirteen packed boxes.
Unhatched eggs, empty/invalid species and out-of-range moves are excluded.
Stored box move high bits are decoded from the low six PP-byte bits; PP-Up
bits are ignored. This does not allocate transient move IDs or force GC.

The active box is scanned only in its freshly loaded live representation;
its stale stored copy is skipped. Counts are bounded. The maximum fixture
contains 288 Pokemon and 1,152 move slots, covering all 333 permanent moves.

The loader now delays extension repair until **after** index-table and active
box loading, ownership bootstrap and validation. Otherwise an interrupted
load could commit a valid but incomplete pre-bootstrap bitmap and skip the
scan on the next Continue. The selected record is repaired before the existing
main-save mirror operation can replace the donor. All 150 tested full-capacity
migration commit prefixes recover the complete expected set.

Valid modern records remain authoritative and skip the scan. Unsupported,
CRC-valid future formats retain the existing write-block policy. A legacy
save cannot reconstruct moves on Pokemon already released, forgotten historic
moves or eggs that have not hatched. The old persistence-only trial's valid,
deliberately seeded records also do not force a retroactive ownership scan;
use the supplied new review save or a genuine legacy save for migration tests.

This remains an extension of the existing save transaction, not a universal
power-loss guarantee for unrelated game fields or arbitrary battery damage.

## Resource Cost

Relative to the accepted scrollbar prototype:

| Resource | Delta |
| --- | ---: |
| Acquisition/owned-scan ROMX section | +552 bytes |
| Integration call sites | +127 bytes |
| Deferred-repair storage adjustment | -4 bytes |
| **Total ROMX** | **+675 bytes** |
| New ROM0, WRAM0/WRAMX, HRAM, SRAM allocation | **0 bytes** |
| New VRAM/OAM/graphics assets | **0** |

The existing 66-byte dedicated bank-2 allocation, 64-byte menu-lifetime
snapshot and two 72-byte records in reserved save padding are unchanged.
Linked ROMX use is 2,333,843 bytes / 713,581 free in the same 186 banks.
WRAMX remains 24,010 used / 4,662 free. ROM0 has 523 bytes free, WRAM0 13 and
HRAM zero; this stage does not consume any more of those tight regions.

## Qualification

Native SameBoy tests execute this exact linked ROM, with newly prepared
matching checkpoints. Every storage recovery uses a fresh emulator and battery
file, not a save state. Controlled source tests call actual ROM routines and
drive their dialogs; separate normal-input gameplay tests cover ordinary
captures, hatching, post-battle learning and saving. At most six native workers
run concurrently, usually two per stream, preserving the requested CPU headroom.

| Suite | Passed coverage |
| --- | ---: |
| Permanent bitmap mark/check, seven caller banks | 2,380 cases |
| Bounded menu snapshots | 4 cases |
| Transient reuse, GC, packed indices/PP-Up bits, register/bank/SRAM ownership | 12,276 cases |
| Cold storage loads, corruption/recovery/migration/lifecycle | 1,490 cold loads; 5 lifecycle cases |
| Interrupted normal writes / recovery repair | 152 / 150 prefixes, included in cold loads |
| Owned-move migration, all fourteen active-box positions and live edge cases | 29 cases |
| Interrupted full-capacity owned-move migration | 150 additional fresh cold loads |
| Discovery source positives/negatives | 59 cases |
| Modern species Dex, all 373 species and stress families | 6,555 cases |
| Legacy species Dex, all 373 species and stress families | 6,555 cases |
| Moves browsing/pages/interfaces, both orders | 2,702 cases; 544 interface checks; 176 transitions |
| Zero / one / 25-known Moves fixtures | 8,058 browse/page cases |
| Scrollbar visual captures / exact accepted popup placement | 16 / 16 cases |
| Modes/Search integration / listing popovers | 66 / 144 cases |
| Ranked Search all type pairs / sparse flags / active stress | 2,052 / 144 / 192 cases |
| Search Results all-species scrolling / badge fixtures | 108 / 114 cases |
| Search listing returns / default-empty cases | 36 / 24 cases |
| Modes/Unown stage-and-reveal | 32 cases, 192 captured transitions |
| Battle regression, 100 moves, both sides, four display phases, two builds | 1,600 cases |
| Sampled cry regression, 20 species, six contexts, four phases, two builds | 960 cases, with unchanged known exceptions below |
| Custom Pack/TMHM/Apricorn selections | 464 paired-build cases |
| General menu input/register contracts | 1,792 input cases across ten location/build jobs |
| Surrounding gameplay | 22 paired-build scenarios |
| Repeated battle entry, post-battle learning, whiteouts | 24 paired-build jobs |
| Popup construction/input-readiness follow-up | 148 paired-build cases |
| Independent host tests | 69 tests, 3 intentional obsolete-path skips |

Storage includes bit boundaries 255/256/257/333, invalid values, duplicates,
every single-bit record corruption in both copies, foreign identity, damaged
core/table donors, unsupported future records, New Game, canceled overwrite,
approved overwrite and deletion. Helpers do not write SRAM. The index-reuse
tests reuse the same transient byte for every permanent move and retain the
complete set through conversion-table GC.

Source coverage includes gifts to party/PC/full, pre-Dex receipt, extended move
indices, retained/pending/failed contest cases, successful/declined/wrong NPC
trades, both Dratini sets, successful/declined/known/incompatible learning,
unhatched/hatched/not-ready eggs, both daycare owners and failed retrieval.
Public daycare dialogs additionally cover growth/overwriting, payment, declined
withdrawal, insufficient funds and full party. Only the final returned moves
are discovered. Negative ball tests cover failed capture, trainer rejection,
full storage and temporary tutorial capture.

Surrounding gameplay covers building/map transitions, purchase and Pack
contents, wild/trainer battles, party/PC captures, leveling/evolution, hatch,
fishing, phone, healing, normal Save/reload and Ruins of Alph's puzzle. Menus
also cover PC deposit/withdraw/box selection/naming, party Stats, Pokegear,
radio, mail, trainer card, options, mart and game corner. Repeated battle
tests preserve the double-speed world/normal-speed battle policy, including
nested battle menus and eight actual Leech Seed learn prompts with return.
The campaign includes 64 repeated battle entries, eight learning battles and
eight defeats. It is broad regression coverage, not every possible map/event
permutation or a physical-cartridge power-loss certification.

### Fixture Limits And Known Issues

- All shipped evolution-only move entries are `NO_MOVE`. Its two learning
  cases use one declared data-only table entry in that emulator instance.
- Garchomp currently has a placeholder Tackle-only learnset. Two high-index
  gift cases replace one learnset word with Caustic inside the emulator only.
  These are forward-compatibility checks, not claims of natural availability.
- Three transformed/current/other-battle-mon learning cases stop at the
  committed hook boundary before the message. Full ordinary post-battle
  learning, its dialog and return are independently tested through gameplay.
- Synthetic calls to `GiveEgg` with a full party and the contest box-full
  routine deliberately violate public-entry preconditions. They verify no
  discovery hook is reached, but their unchanged lower-level routines are not
  generally side-effect-free under invalid calls. Public egg NPCs and contest
  admission already check capacity. No new reachable gameplay bug is established
  by these synthetic tests; they are not proof of defensive safety there.
- The tutorial negative selects a ball through the real Pack, then applies the
  tutorial battle-type fixture at item-effect entry. It verifies the temporary
  catch's no-acquisition branch, not a complete replay of the Dude's auto-input
  tutorial or its separate pre-existing invalid-ball crash.
- `BATTLE-CRY-01` remains: wild appearance misses for Dusknoir (45 blocks),
  Groudon (198), Kyogre (226) and Yanmega (405). The catch/faint-context campaign
  sees 32 known warnings in each build, with identical species/context/phase
  signatures. These precede the catch/faint event, are not new tracker failures,
  and must not be mislabeled as intentional cry cancellation.
- No battle animation, audio or HOME source is changed. All 100 moves complete
  in both directions without new playback diagnostics. Nevertheless, paired
  first-invocation durations range from -5 to about +2.968 display intervals.
  Native RNG/input-phase differences can alter critical/multihit sequences;
  some later invocation counts differ. This suite does not establish pixel-
  identical videos or deterministic identical timing for every invocation.
  No retiming or animation-speed adjustment was made.

Two test-harness issues were corrected before final qualification: outdated
Search/Unown navigation and a pending-contest case dispatched to the retained
contest caller. The latter now explicitly checks its entry label and zero hook
hits. Ball negative tests must enter from the actual battle Pack owner, not
inject a text/item routine into an unrelated battle-animation checkpoint.

## Native Timing

One display interval is 70,224 base-clock cycles, **16.7427 ms**. These are
emulated hardware time, not wall-clock test throughput. Save/load rows measure
the real native routines, excluding boot, text/confirmation and Continue's
later visible world handoff. They are **completion costs**, not first-visible-
response measurements. Values are medians of four runs against the accepted
scrollbar/persistence baseline.

| Path | Accepted baseline ms / intervals | Stage two ms / intervals | Added ms / intervals |
| --- | ---: | ---: | ---: |
| Normal valid Continue load | 190.480 / 11.3769 | 190.567 / 11.3821 | +0.087 / +0.0052 |
| Normal Save | 150.487 / 8.9882 | 150.394 / 8.9826 | -0.093 / -0.0056 |
| Review-size legacy migration | 177.111 / 10.5784 | 188.694 / 11.2702 | +11.584 / +0.6919 |
| Full-capacity legacy migration | 307.684 / 18.3772 | 510.158 / 30.4704 | +202.473 / +12.0932 |
| Damaged selected record / valid donor | 196.805 / 11.7547 | 202.020 / 12.0661 | +5.214 / +0.3114 |

The migration scan/repair is one-time for valid migrated saves, not a cost on
every Continue. The worst-case fixture fills all party/daycare/PC capacity;
its later normal load skips bootstrap. Ordinary save/load differences below
0.1 ms are phase/instruction noise, not a meaningful save optimization.

Isolated double-speed hook calls cost approximately 0.259-0.272 ms
(0.0155-0.0162 intervals) for one learned move and 0.903-0.916 ms
(0.0539-0.0547 intervals) for a four-move receipt. These include the native
call wrapper and are not normal-speed battle costs or whole dialogue timings.
The small legacy read-only ownership scan alone measures 3.819 ms / 0.2281
interval; full migration above also includes loader/CRC/repair work.

### Visible Responsiveness

In the sixteen paired Moves interface captures, median **first visible response**
and **fully revealed destination** differences are zero display intervals for
entry, up/down, page jumps, popup, sort, cancel and return. All individual
first-response and revealed-destination differences are also zero in the
retained final paired capture set.
Popup bounds remain exactly `(43,16)-(147,56)`, including the accepted five-
pixel-left and one-tile-up placement. Known/unseen panels and scrollbar pixels
pass independent native memory/pixel assertions.

The custom inventory campaign retains identical final pixel/palette sets and
TM/HM disc OAM sets. First visible response has median zero delta and no added
interval (range -2 to 0). Its older **late steady-image-set** metric sometimes
reports one interval later completion, especially on opening item submenus,
despite identical destination images. That metric depends on animation phase;
it is not an input-readiness boundary. A separate 148-case native check reaches
`StaticMenuJoypad` after popup construction/publication with median +0.0067 ms
and maximum +0.0196 ms, only +0.00117 interval. There is no additional whole
display interval of popup construction/input delay. Both observations are
retained rather than presenting the pixel-hash number as a loading regression.

## Retention And Reproduction

Reusable implementation/test tools and this report are repository files.
The private candidate, ROM/save, fresh runners/checkpoints, JSON summaries,
screenshots and native traces remain under the ignored build directory.
Completed runtime text traces were losslessly gzip-compressed; no previous
accepted evidence or rollback was deleted. This iteration retains about
5.2 GB instead of its roughly 13 GB uncompressed trace footprint.

Build a fresh output (do not overwrite a directory while its tests run):

```sh
env PYTHONPATH=tools python3 tools/build_move_acquisition_prototype.py \
  --source build/dex-moves-scrollbar-20261007e \
  --output build/dex-moves-acquisition-NEW --jobs 6 --prepare
```

Use `tools.dex_timing.move_persistence` for cold storage faults and lifecycle;
`tools.dex_timing.move_acquisition` for helpers, `--sources`, `--migration` and
`--interruptions`; `tools.dex_timing.acquisition_regression` for menus, custom,
gameplay, moves, audio and transitions; and
`tools.dex_timing.acquisition_performance` for native save/load timings.
The established Dex/Search/Moves/scrollbar suites run against fresh output
configs. `tools.dex_timing.acquisition_report` provides `readiness`, `review`
and `final` actions. Final verifies report hashes, the qualified ROM, protected
inputs, independent host assertions, scrollbar pixels and paired cry exceptions.

Next step is manual acceptance of this acquisition/learning prototype. Battle-
use discovery remains the next separate engineering/qualification stage.
