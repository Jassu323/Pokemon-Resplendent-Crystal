# Moves Dex Sort Remembrance Prototype

2026-10-08. Private follow-up over the accepted battle-use/Struggle prototype.
Production and all previous review builds remain untouched. Position remembrance
is separate deferred work: `DEX-PREF-01` for Modern/Legacy Pokemon listings and
`DEX-PREF-02` for Moves Mode, in the live bug backlog.

## Behavior

- Confirming Type or Alphabet remembers that order immediately for this session.
  Leaving Moves, visiting the Pokemon listing, or closing/reopening the Dex does
  not lose it. The Pokemon listing's presentation and sort remain independent.
- Normal Save persists the preference in both primary and backup saves. Cold
  Continue restores it. Merely selecting a sort does not write SRAM.
- Canceling the popup with B or Start does not change the preference or position.
- Selecting a different order still starts at the beginning. Confirming the
  current order retains the current cursor and scroll.
- Reentering Moves still resets the cursor/scroll. This prototype remembers
  the sort, not the position. The two backlog stories cover that later work.
- New Game and unrecognized/legacy preference values default to Type.

## Implementation And Cost

`wLastMovesDexSort` occupies WRAMX bank 1 at `$d9e3`, the first byte of the
13-byte saved-player padding immediately after `wFarfetchdPosition`. Twelve
padding bytes remain there. Existing fields, save sizes and checksums retain
their addresses. This field is inside `wPlayerData` and `wGameData`, so ordinary
player saving/loading and New Game clearing already cover it.

Stored values are `$a0` for Type and `$a1` for Alphabet. Only `$a1` restores
Alphabet; zero, raw one and all other values safely select Type. The tag avoids
interpreting ordinary old zero/one padding as an explicit Alphabet choice.
No discovery record version or legacy-migration algorithm changes.

The initializer restores the preference after clearing its shared workspace.
The sort-confirmation handler remembers the accepted choice before its existing
same-sort comparison. Both helpers preserve AF/BC/DE/HL and incoming WRAM bank,
including bank zero's alias. Neither allocates transient move IDs, modifies
discovery flags or writes SRAM.

| Resource | Increment over accepted Struggle build |
| --- | ---: |
| ROMX | 65 bytes |
| ROM0 | 0 |
| WRAM/SRAM allocated size | 0 |
| Existing saved-player padding used | 1 byte, covered by both save copies |
| VRAM/OAM/assets | 0 |

Linked totals: ROM0 15,861 bytes used / 523 free; ROMX 2,333,997 used /
713,427 free; WRAM0 4,083 used / 13 free; WRAMX 24,010 used / 4,662 free;
SRAM 49,994 used / 15,542 free; HRAM 127 used / 0 free.

Only `ram/wram.asm` and the private `engine/pokedex/pokedex_moves_mode.asm`
differ from the previous prototype. Battle, audio, clock policy, discovery,
save algorithms, descriptions and artwork are unchanged. Low complexity and
small runtime cost; the main risks were shared-memory clearing, bank restoration,
accidental preference writes on cancellation, and old-save interpretation.

## Qualification

Fresh SameBoy runners use this ROM's symbols and cold batteries. No older
emulator checkpoints were reused. Native testing passed:

- 4,096 helper contracts: both operations, all 256 input/stored values and all
  eight WRAM bank selections. Registers/banks, neighboring saved bytes, unrelated
  scratch and discoveries remain intact. Helpers generate zero SRAM writes.
- 16 normal-input UI contexts spanning Modern/Legacy, both Moves sorts, all
  three Pokemon orders, locked/unlocked Unown and four entry phases. Includes
  cancel, same-sort/change-sort behavior, modes/listing roundtrips, complete
  Dex close/reopen, and content/graphics audits after restoration.
- 11 save/reload scenarios: both choices with natural and first-use battle
  fixtures, primary-versus-backup precedence, primary corruption, backup
  corruption, legacy zero/one, invalid 255 and declined Save. Four normal-input
  Save/cold-Continue roundtrips verify both preference and discovery records.
- Six New Game/overwrite/deletion checks, including a live Alphabet value
  present before the real New Game reset. Starting New Game without replacing
  the old battery preserves that old saved preference.
- Full existing Moves navigation sweep: 1,338 single-row cases, 1,348 page cases,
  16 interface cases / 544 checks and 176 measured transitions. Popup alignment,
  scrollbar, known/unseen rendering and stage-and-reveal audits pass.
- 37 host tests pass; three obsolete popup-implementation tests intentionally
  skip. All 32 protected production/rollback inputs retain their hashes.

The full 100-move, sampled-cry and unrelated gameplay campaigns were not rerun
for this preference-only revision. Their owners are byte-for-byte unchanged
from the previously qualified source. There is no animation retiming.

### Responsiveness

All 176 interface comparisons retain the same physical display intervals as
the earlier fully qualified stage-three UI capture. At most 0.000114 of an
interval (0.002 ms) differs in breakpoint-relative timing; no added visible
display interval. The immediate previous Struggle revision has no separate
full UI capture, so its earlier stage-three capture is explicitly used here.

Instrumented routine medians, four repetitions using the same valid review
battery in the immediate previous Struggle build and the new build:

| Routine | Previous | New | Difference |
| --- | ---: | ---: | ---: |
| `TryLoadSaveFile` | 190.370 ms | 190.513 ms | +0.143 ms |
| `SaveGameData` | 150.445 ms | 150.433 ms | -0.012 ms |

These measure the named routine bodies, not the full text/menu/save-sound
sequence. The tiny differences are not a meaningful responsiveness change.
No remaining game defect was identified. During qualification the new driver
needed a longer released-button interval after Start-menu redraws; its original
short synthetic B presses were consumed before the input poll. That was fixed
in the host driver, not in the game.

## Review Files

- ROM: `build/dex-moves-sort-memory-20261008/pokecrystal-dex-moves-sort-memory.gbc`
- Matching natural save: `build/dex-moves-sort-memory-20261008/pokecrystal-dex-moves-sort-memory.sav`
- First-use battle pair: same ROM/save basename under that build's `battle-review/`.
- Qualification: `build/dex-moves-sort-memory-20261008/sort-memory-qualification.json`.
- Raw helper/UI/save/timing captures: that build's `sort-memory/`.
- Full navigation/visual evidence: that build's `moves-mode-qualification/`.

ROM SHA-256:
`f64ab16071231f4d0830b09d92b89c5b5de405519e8bccbd2c181eb9e8c958e8`.
Natural save SHA-256:
`435a9071c8868c2e0b7913412ae526334f3a6f739ed7d263df04f3773df5e056`.
Battle save SHA-256:
`6376dc3c8d965832706d72c4d3ea1f810680c9dc7f284f34df479fe1882f703f`.

Both review saves start with Alphabet selected, committed through the normal
Save menu. The natural save retains its eight discoveries; the battle fixture
still has only Struggle discovered and retains the earlier supplied party/PC
moves. This preference change does not reveal additional moves. Choose Type,
exit/reenter, Save, restart and Continue to review the other preference.

## Reproduction

The builder requires a fresh private output directory and protects earlier
artifacts. Tests use at most four build workers and two navigation workers.

```sh
PYTHONPATH=tools:. python3 tools/build_moves_sort_memory_prototype.py \
  --source build/dex-moves-struggle-grant-20261008 \
  --output build/dex-moves-sort-memory-20261008 --jobs 4
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_sort_memory prepare \
  --output build/dex-moves-sort-memory-20261008
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_sort_memory helpers \
  --output build/dex-moves-sort-memory-20261008
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_sort_memory ui \
  --output build/dex-moves-sort-memory-20261008
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_sort_memory saves \
  --output build/dex-moves-sort-memory-20261008
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_sort_memory timing \
  --output build/dex-moves-sort-memory-20261008
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_mode \
  --output build/dex-moves-sort-memory-20261008 --jobs 2 \
  --baseline build/dex-moves-battle-use-20261008
PYTHONPATH=tools:. python3 -m tools.dex_timing.moves_sort_memory qualify \
  --output build/dex-moves-sort-memory-20261008
PYTHONPATH=tools:. \
  MOVE_DISCOVERY_BUILD=build/dex-moves-sort-memory-20261008 \
  DEX_MOVES_MODE_BUILD=build/dex-moves-sort-memory-20261008 \
  python3 -m unittest tools.test_moves_sort_memory tools.test_move_discovery \
  tools.test_pokedex_moves_mode
```
