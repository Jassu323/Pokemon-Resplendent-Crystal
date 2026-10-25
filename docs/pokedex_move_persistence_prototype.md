# Moves Dex Persistence Prototype

2026-10-07. Private stage-one trial based on the accepted Moves visual owner
at `build/dex-moves-mode-20261007b`. Production, installed emulator cartridges
and player saves are unchanged. Gameplay discovery hooks and legacy owned-move
bootstrap are deliberately not part of this trial. The confirmed egg policy
is discovery at hatch; it will be wired with those gameplay hooks.

## Review And Rollback

Review cartridge and matching seeded save:

- `build/dex-move-persistence-20261007/pokecrystal-dex-moves-persistence.gbc`
- `build/dex-move-persistence-20261007/pokecrystal-dex-moves-persistence.sav`

ROM SHA-256:
`7d41a03ef5c86ca203f421701fe1445fd311a7a053315d18f6a85a2b65885be0`.

The review save has 25 deliberately seeded discoveries, including Surf,
Thunderbolt, Water Pulse, Dragon Dance, Caustic and Sketch, the first five Type
entries, and the first three alphabetical entries. Other moves show `-----` and
a blank details panel. Enter Moves Dex Mode from SELECT in either species
Listing. Existing navigation, eight-row page jumps and Type/Alphabet sorting
are unchanged. Exit the Dex, save normally, restart the emulator and Continue
to check that the known/unseen presentation survives a real reload.

Using or acquiring moves does **not** mark them yet. This save tests persistence
of controlled flags, not discovery coverage. An old save without an extension
starts with no discoveries in this stage; do not use the trial as a migration
tool for a real playthrough. The later bootstrap must still be tested against
original legacy saves, not saves already rewritten by this storage-only ROM.

Safe rollback is frozen at `build/dex-moves-safe-rollback-20261007`:
accepted ROM/save/symbols/map, qualification metadata, a complete candidate
archive, and `rollback.json` containing checksums for every retained artifact.
The accepted ROM remains
`56b5b5947ba012a6981b5e1b6ae58aabe7e2ceab524da31c7da50e92f104bd2c`.
No production promotion, commit or Git tag was performed.

## Storage Contract

Dedicated WRAMX bank 2 contains the canonical 64-byte bitmap at
`$d500-$d53f`, one load-status byte at `$d540`, and one unsupported-write guard
at `$d541`. It does not share the pic workspace, contest mon or conversion
tables. Each move uses its permanent index, not a transient party/box byte ID.
The check/mark APIs reject zero and indices beyond the compiled 333 moves,
restore the caller's WRAM bank, preserve BC/DE, and never write SRAM. The
bitmap supports growth to 512 moves without changing this format.

Boot clears all WRAM banks. New Game now explicitly clears this bounded
66-byte allocation in its normal reset path. Starting New Game does not erase
the previous battery save; approved overwrite invalidates the old extension
markers, and save deletion clears the battery through the existing routine.

Each primary/backup copy uses 72 bytes from its existing 136-byte padding:

| Copy | Location | Record | Remaining padding |
| --- | --- | ---: | ---: |
| Primary | SRAM bank 1 `$ac88-$accf` | 72 bytes | 64 bytes |
| Backup | SRAM bank 0 `$be88-$becf` | 72 bytes | 64 bytes |

The eight-byte header stores ASCII `MD`, version 1, bitmap length 64, the
corresponding main-save checksum, and CRC16/CCITT-FALSE. CRC coverage includes
header metadata, player ID, secret ID and the bitmap. The old main checksummed
ranges and both checksum addresses stay unchanged. Total reserved use is
144 bytes; no SRAM section or battery-file expansion occurs. Private fixture
construction preserves the 48-byte RTC trailer.

Normal saving invalidates each extension marker, writes metadata/body/CRC,
commits the two marker bytes last, then writes the existing main checksum.
Loading validates the ordinary game first; a bad extension does not discard
otherwise valid Pokemon/player data. It prefers the selected copy's valid
record and can recover from a valid, same-playthrough donor. Donor main data
and conversion tables must pass their own checksums. Different parent sums
are allowed when each record is correctly bound to its own copy.

Recovery repairs the selected extension **before** the normal loader mirrors
over its donor. That ordering preserves a durable record during interrupted
repair. This is an extension to the existing save transaction, not a redesign
or universal power-loss guarantee for all legacy save fields.

CRC-valid unknown versions/capacities are treated as opaque. Their records
are not rewritten during that session, including manual Save. Guaranteed
semantic preservation after downgrading and changing the parent game data is
not promised; this policy prevents silent destruction on first encounter.

## Renderer And Costs

Moves Mode snapshots the canonical bitmap once on each entry, into the last
64 bytes of its existing 640-byte Info graphics scratch in bank 3. Its sort
glyph/border staging ends before that slice, enforced by assembly assertions.
Gameplay is paused while this menu is active, so discoveries cannot change
behind it. Every re-entry refreshes the snapshot. Canonical flags remain in
the dedicated bank-2 region; the shared bank-3 copy is menu-lifetime only.

This avoids nine cross-bank helper calls on every redraw. The initial live
lookup version missed one short two-frame paging stimulus; the snapshot
version passes the original stimulus without lengthening test presses or
changing navigation cadence. No VRAM, OAM, font or graphical assets are added.

| Resource | Increment over accepted visual prototype |
| --- | ---: |
| ROMX total | 948 bytes |
| Storage/helper library | 843 bytes, included above |
| Renderer snapshot/query changes | 56 bytes, included above |
| Existing save/reset integration | 49 bytes, included above |
| Dedicated WRAMX | 66 bytes |
| Existing scratch borrowed while Moves is active | 64 bytes, no new allocation |
| Reserved SRAM used | 144 bytes, no new allocation |
| New ROM0 / WRAM0 / HRAM / VRAM / OAM | 0 bytes |

Linked totals are 2,333,425 ROMX bytes used / 713,999 free, in the same 186
banks, and 24,010 WRAMX bytes used / 4,662 free. ROM0, WRAM0, HRAM, SRAM section
sizes and all pre-existing named RAM addresses are unchanged.

## Qualification

All storage recovery tests use fresh native SameBoy instances and battery
files, not save states. Controlled calls enter actual ROM helpers/save
routines; separate tests use the real Save menus. Ordinary Dex regression
checkpoints are freshly prepared for this exact ROM. Concurrent native
workers are capped at six total, with eight compilation jobs.

The storage layer passes 2,380 mark/check cases across all seven caller WRAM
banks, four bounded snapshot-copy cases, five save patterns, 1,490 fresh
reloads and five lifecycle checks. It tests word boundaries 255/256/257/333,
invalid indices, duplicate marks, conversion-table GC, no SRAM writes before
Save, all 576 single-bit record faults in each copy, legacy/random padding,
player/secret-ID mismatch, invalid core/table donors, and opaque future
records. The reload total includes 152 interrupted-save prefixes and 150
interrupted-repair prefixes reconstructed from actual native SRAM write
traces. No partially written bitmap is accepted.

The remaining qualification also passes:

| Suite | Passed cases |
| --- | ---: |
| All-seen Moves UI: both orders, every move/page, interfaces | 2,702 |
| Zero / one / 25-known Moves fixtures: complete move/page sweeps | 8,058 |
| Modern Selected/listing, all 373 species and stress families | 6,555 |
| Legacy Selected/listing, all 373 species and stress families | 6,555 |
| Modes / Search / reopening integration | 66 |
| Existing species-list popup phases and controls | 144 |
| Search UI / listing returns / default-empty scenarios | 204 |
| Modes / Unown transitions | 8, with 48 captured transitions |
| Exact accepted-popup and selected-entry pixel comparisons | 18 |
| Independent host tests | 53 |

Each presentation's Selected suite includes cold/warm selection, internal
paging, all Info pages, learnset Moves, Area entry/return, and active/settled
rapid/held-input stress. Existing animation and sampled-cry assertions pass.
The Moves interface cases include 544 content/control checks and 176 captured
transitions. The canonical flags and menu snapshot are checked throughout
all move/page sweeps, including popup open/cancel/re-sort.

The normal Save menus are separately tested for confirmation and cancellation,
each followed by a cold reload. Two opaque-format manual saves preserve their
records. Independent native traces show the same 9,344 existing save-write
addresses in the same order as the accepted baseline, after excluding only
the two new records. All pre-existing named RAM addresses remain unchanged.

New Game testing follows the actual main-menu reset path and the overwrite/
deletion storage boundaries; it does not claim a full fresh playthrough or
starter/hatch/acquisition coverage. Those are next-stage gameplay tests.

Final artifact hashes, protected-input checks, report checksums and the fresh
host result are in `build/dex-move-persistence-20261007/final-qualification.json`.
Review save SHA-256:
`5491094544ef590602c8958cb4752b94797784b7b094ae70362c2d43e63e8488`.

### Native Timing

These measure `SaveGameData` / `TryLoadSaveFile` routine execution at the
double-speed world clock, excluding boot, confirmation dialogs, text and
save sound effects. Display intervals are physical elapsed cycles divided by
70,224 base-clock cycles, not emulator wall time. One interval is 16.7427 ms.

| Operation | Accepted visual baseline | Persistence trial | Added time |
| --- | --- | --- | --- |
| Save, five bitmap patterns | 137.21 ms / 8.195 intervals | 150.79-150.96 ms / 9.006-9.017 intervals | 13.58-13.76 ms / 0.811-0.822 intervals |
| Continue, valid records | 137.13 ms / 8.191 intervals | 190.48 ms / 11.377 intervals | 53.35 ms / 3.186 intervals |
| Continue, legacy padding | Same baseline | 177.11 ms / 10.578 intervals | 39.98 ms / 2.388 intervals |
| Continue, damaged selected record / valid donor | Same baseline | 196.81 ms / 11.755 intervals | 59.67 ms / 3.564 intervals |

The observed VBlank-callback counts were eight versus nine during Save and
eight versus eleven during valid Continue. Loading includes validation of
the donor and the existing mirror repair, now with CRC-protected records;
there is no legacy owned-move scan yet. This cost is paid at save/load, not
on every listing scroll or selected-tab update.

Median first-response and completion deltas in the paired Moves transition
captures round to zero display intervals for navigation and sorting. Entry/
return have occasional subframe-phase shifts approaching one interval;
there is no consistent new whole-frame navigation delay. No mixed publication,
white flash or LCD-off frame is observed in the accepted final captures.

### Trial Corrections

The live-query paging miss and donor-overwrite window were corrected before
the final qualification. The storage assembly owns its section through
`PUSHS`/`POPS`, preventing subsequent implicit includes from being captured
by the new section. The initial direct-reset diagnostic used an invalid
mid-overworld precondition; lifecycle tests now use the actual New Game
caller rather than treating that harness failure as a game bug.

One ancillary test briefly read a partially republished symbol file during
an identical-ROM relink. It was a build/test artifact race, not a visual or
save fault; the completed-link suite was rerun successfully. The trial
builder now atomically publishes ROM/symbol/map copies. Future actual code
relinks still require new checkpoints and must not share live qualification
inputs. No unresolved runtime defect was identified in this stage's coverage.

## Reproduction

Rebuild the retained private candidate, preserving the rollback pin:

```sh
env PYTHONPATH=tools python3 -B tools/build_move_discovery_prototype.py \
  --source build/dex-moves-mode-20261007b \
  --output build/dex-move-persistence-20261007 \
  --rollback build/dex-moves-safe-rollback-20261007 \
  --jobs 8 --relink --prepare

env PYTHONPATH=tools python3 -B -m dex_timing.move_persistence \
  --output build/dex-move-persistence-20261007 \
  --baseline build/dex-moves-mode-20261007b --jobs 6

env PYTHONPATH=tools python3 -B -m dex_timing.moves_mode \
  --output build/dex-move-persistence-20261007 --jobs 6

env PYTHONPATH=tools python3 -B -m dex_timing.move_persistence_integration \
  --output build/dex-move-persistence-20261007 \
  --baseline build/dex-moves-mode-20261007b --jobs 6
```

Run these serially if each uses six workers. The ordinary Modern/Legacy
Selected suites use `dex_timing.performance_regression`, the eight suites
`cold warm paging info moves area info-stress moves-stress`, and
`--expected-double-speed`. Host tests are `tools.test_move_discovery`,
`tools.test_pokedex_moves_mode`, `tools.test_pokedex_moves`,
`tools.test_pokedex_sort`, and `tools.test_pokedex_search_results`, with their
build environment variables pointed at this trial.

After all surrounding suites have been rerun, assemble/verify their evidence:

```sh
env PYTHONPATH=tools python3 -B -m dex_timing.move_persistence_report \
  --output build/dex-move-persistence-20261007
```

## Next Stage

Gameplay discovery, live-ID/packed-index walkers, legacy owned-move bootstrap,
and their acquisition/battle/learning/hatch coverage remain separate work.
They require their own broad gameplay/save qualification. This stage establishes
and tests the storage boundary without conflating it with event coverage.
Append-only permanent move IDs within the 512-bit capacity need no format
change; renumbering/reusing existing permanent IDs would require an explicit
discovery migration rather than merely regenerating display sort orders.
