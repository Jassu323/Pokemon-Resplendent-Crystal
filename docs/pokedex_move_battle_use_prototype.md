# Moves Dex Battle-Use Discovery Prototype

## Pokedex Award Addendum

2026-10-08 follow-up: Struggle is now recorded when Oak first gives the player
the Pokedex. Its existing battle-use discovery remains intact. This is a new
private revision; the accepted stage-three build and the full qualification
below remain unchanged historical evidence.

- Updated ROM: `build/dex-moves-struggle-grant-20261008/battle-review/pokecrystal-dex-moves-battle-use.gbc`
- Matching battle-review save: `build/dex-moves-struggle-grant-20261008/battle-review/pokecrystal-dex-moves-battle-use.sav`
- Natural eight-discovery save: `build/dex-moves-struggle-grant-20261008/pokecrystal-dex-moves-battle-use.sav`
- New-link evidence: `build/dex-moves-struggle-grant-20261008/pokedex-gift-qualification.json`
- Visual check: `build/dex-moves-struggle-grant-20261008/pokedex-gift/struggle-seen.png`

The new ROM SHA-256 is
`55cf07248de994ebad2a718ff1db7ced21d0542a18d08a30de39a312265b5dbf`.
The new battle-review save SHA-256 is
`7cfb380f0396ba4f51c04f39e7e476aee9ebfb1c0ae61e7d63df4be9e3a1a192`.

Immediately after `setflag ENGINE_POKEDEX` in Oak's real award script,
`callasm MoveDiscovery_PokedexGift` marks permanent index `STRUGGLE` (165).
The preserving helper does not allocate a live move ID or write SRAM. The
normal save path persists the bit. Cost is **22 ROMX bytes**: four script bytes
and an 18-byte helper. No ROM0, RAM, SRAM, VRAM or OAM increase. Only `main.asm`,
`maps/MrPokemonsHouse.asm` and the new helper differ from the accepted build;
battle, animation, audio, graphics and storage owners are unchanged.

Focused native testing passed 16 actual award-command cases across four
display phases and four prior-discovery patterns, 16 repeated awards, 16
register/bank contracts including WRAM bank zero's alias, two normal-input
Save/cold-Continue roundtrips, five New Game/overwrite/deletion lifecycle
checks and a normal-input Moves Dex display audit. A pre-Dex cold boot does
not reveal Struggle. Receiving the Dex adds only Struggle, preserves existing
discoveries and performs no immediate SRAM write. Seven focused host tests
also pass; 25 protected artifacts remain unchanged. The large stage-three
battle regression was not rerun for this grant-only revision.

The updated review files preserve their parties and other discovery bits.
The battle-review save now starts with **only Struggle seen**, leaving its 93
supplied moves available for first-use testing. The natural save retains its
seven prior discoveries plus Struggle. Both were updated by running the real
award's commands through the ROM script dispatcher, followed by normal Save
menu inputs; the rest of Oak's story sequence was not replayed. Existing valid
saves are not silently backfilled merely by Continue. Production remains
untouched.

Reproduction:

```sh
python3 tools/build_move_battle_use_prototype.py \
  --source build/dex-moves-acquisition-20261008 \
  --output build/dex-moves-struggle-grant-20261008 \
  --jobs 4 --grant-struggle
PYTHONPATH=tools:. python3 -m tools.dex_timing.pokedex_gift \
  --output build/dex-moves-struggle-grant-20261008 \
  --baseline build/dex-moves-battle-use-20261008
PYTHONPATH=tools:. python3 -m unittest tools.test_pokedex_gift -v
```

## Original Stage-Three Qualification

2026-10-08. Private stage-three prototype over the manually accepted
[acquisition/learning prototype](pokedex_move_acquisition_prototype.md).
Production is not integrated or rebuilt. The accepted stage-two ROM, save,
symbols and map remain protected rollback inputs. No animation retiming,
generated graphics, installed-emulator replacement or player-save modification.

## Review Files

- ROM: `build/dex-moves-battle-use-20261008/battle-review/pokecrystal-dex-moves-battle-use.gbc`
- Matching battle-review save: `build/dex-moves-battle-use-20261008/battle-review/pokecrystal-dex-moves-battle-use.sav`
- Natural seven-discovery save: `build/dex-moves-battle-use-20261008/pokecrystal-dex-moves-battle-use.sav`
- Qualification: `build/dex-moves-battle-use-20261008/final-qualification.json`
- Focused native witnesses: `build/dex-moves-battle-use-20261008/battle-use/`
- Normal-input battle/Save/Continue/Dex proof: `build/dex-moves-battle-use-20261008/battle-use/roundtrip/`
- Manual fixture manifest: `build/dex-moves-battle-use-20261008/battle-review/review.json`

ROM SHA-256:
`f80862d319fe9a14a5a81cdbe60694ec5cd21505c9d0a777e5bb7db3a0b3b1ad`.
Accepted stage-two ROM SHA-256:
`19d039e49728a59767ea474d25308c13f1150abe1e45e3c44823ab75eede6db4`.

The separate battle-review save deliberately has **valid, empty discovery
records** despite its configured party/PC. This is an artificial first-use
fixture, not natural acquisition behavior. There are 24 level-30 Pokemon with
93 distinct moves: 24 party moves and 69 moves on 18 Pokemon in Box 14.
The final native cold reload verifies every supplied move. Its party includes:

| Pokemon / nickname | Moves |
| --- | --- |
| Smeargle / CALL | Sketch, Metronome, Mirror Move, Transform |
| Snorlax / FOCUS | Focus Punch, Sleep Talk, Rest, Body Slam |
| Charizard / CHARGE | Fly, SolarBeam, Skull Bash, Razor Wind |
| Diglett / FIRSTUSE | Dig, Sky Attack, Pound, Surf |
| Luxray / REGULAR | Thunderbolt, Caustic, Dragon Dance, Water Pulse |
| Meganium / COPY | Mimic, PoisonPowder, Tackle, Reflect |

Use a move, leave battle and inspect Moves Dex Mode. Both the player's and
opponent's presented moves should become visible. Save normally and restart to
check persistence. Browsing/canceling a move must not discover it. Sleep Talk
requires sleep; Rest is supplied on the same Pokemon. Smeargle supplies the
called/copied-move checks. The PC contains additional review moves.

The main-directory save instead retains the stage-two natural ownership
bootstrap: Tackle, Body Slam, Disable, Razor Leaf, PoisonPowder, Confusion and
Reflect. Inventory/progression convenience edits remain declared fixtures.
Normal modern saves do not retroactively discover all owned moves on every
Continue; a valid record remains authoritative. Legacy migration still scans
currently owned moves once. Historic opponent uses before this prototype
cannot be reconstructed from a legacy save.

Battle-review save SHA-256:
`7004b2f7891a26972a24642f7e81e9a5ce0445a88ea71cd0c8e385240dc476f7`.
Natural seven-discovery save SHA-256:
`15e8f4e3abdd6f1774ba561e69884df8bca1bdcc15418d3ce088491dea031240`.

## Implemented Behavior

| Event | Discovery behavior |
| --- | --- |
| Player or opponent presents a move | Record the actual move's permanent index |
| Miss, immunity or effect failure | Record it; the move was still presented |
| Canceled selection, switching, sleeping/frozen/flinching/recharging, disabled move or full paralysis | Do not record an unexecuted selected move |
| Confusion/disobedience | Follow the action that actually occurs, not the original selection |
| Fly, Dig, SolarBeam, Skull Bash, Sky Attack, Razor Wind | Record first accepted charge, before the attacking turn |
| SolarBeam in sun | Record the ordinary immediate-use presentation |
| Focus Punch | Record visible tightening focus, even if later disrupted |
| Metronome, Sleep Talk, Mirror Move | Record caller and actually invoked move; not rejected candidates |
| Sketch | Record Sketch on use; copying the replacement alone does not reveal it |
| Mimic / Transform | Record the presented move, not every copied move; later actual use counts |
| Struggle | Discoverable like any other real permanent move |
| Before obtaining the Pokedex | Discovery still operates |
| Battle Scene disabled | Text/use presentation still records moves |

Flags are monotonic until New Game/deletion and survive forgetting or replacing
moves. Unsaved discoveries are lost on reset, matching ordinary game progress.
There is no extra SRAM write, full-party scan or conversion-table allocation
per battle use. Multiplayer remains outside project scope.

## Three Hook Boundaries

1. `DisplayUsedMoveText`, after `BattleTextbox` and before its final `WaitBGMap`.
   This observes the accepted move, including called/disobedient substitutions,
   instead of hooking the menu selection or generated move lists.
2. `BattleCommand_Charge.awake`, after the charged flag is committed. Charge
   preparation skips ordinary used-move text on its first turn, so it needs
   this separate boundary. Merely selecting a charge move does not count.
3. `Battle_PlayFocusPunchTightenAnim`, after the shared player/enemy focus text
   caller. This catches preparation even when the attack later loses focus.

All three call one preserving wrapper, `MoveDiscovery_BattleUse`. It rejects
non-battle contexts, obtains the acting side's live move from
`BATTLE_VARS_MOVE_ANIM`, resolves it through the existing read-only
`GetMoveIndexFromID` path and marks the permanent-index bitmap. It restores
AF/BC/DE/HL and the WRAM bank. Null/invalid transient IDs and out-of-range
permanent indices are rejected by the existing bitmap owner.

Ordinary text/charge call sites retain the stage-two preserving macro. Focus
uses a plain `farcall`: AF/HL are overwritten immediately by the existing
helper, so preserving them at the outer call site is unnecessary. BC/DE are
preserved. Native tests check the wrapper's stronger full-register contract.

The static effect audit covers all **114** distinct scripts ending in `endmove`;
each contains `movebegin`, `usedmovetext` or `focuspunch`. This is a coverage
guard against future bypasses, not proof that every future branch is correct.
Bide receives an additional native first-turn check on both sides.

## Resource Cost

Relative to the accepted stage-two link:

| Resource | Delta |
| --- | ---: |
| New shared ROMX wrapper | +41 bytes |
| Used-move text call site | +10 bytes |
| Accepted-charge call site | +10 bytes |
| Focus Punch preparation call site | +6 bytes |
| **Total ROMX** | **+67 bytes** |
| ROM0 / WRAM0 / WRAMX / HRAM / SRAM | **0 additional bytes** |
| VRAM / OAM / graphics assets | **0** |

Linked ROMX is 2,333,910 used / 713,514 free in the same 186 banks. ROM0 has
523 bytes free, WRAM0 13 and HRAM zero. The Battle Core section has only
**3 bytes free** after its six-byte hook; future additions there need deliberate
bank planning. The shared wrapper is in a separate ROMX section. This stage
does not relocate any existing RAM symbol.

Storage remains the existing 64-byte bitmap plus two lifecycle/status bytes in
dedicated WRAMX bank 2, the existing 64-byte Moves menu snapshot and two
72-byte primary/backup records in reserved SRAM padding. No format/version
change or second migration is required for stage-two saves. Physical cartridge
SRAM remains four banks / 32 KiB; linker declarations for inactive mobile
owners must not be mistaken for added physical save capacity.

## Qualification Method

All native checks execute this exact linked ROM in SameBoy. Existing
Modern/Legacy checkpoints were freshly prepared for the new link. Parallel
streams are capped at six native workers total, generally two per stream,
preserving the requested CPU headroom. Production/rollback hashes are checked
again at final qualification.

The focused battle tests enter actual battle input/turn/effect owners. Three
read-only witnesses observe **original presentation boundaries**, independently
of the new discovery hook. The final bitmap must exactly equal the witnessed
set for both actors; legitimate moves from the other side are not ignored.
This avoids using the implementation's own hook hits as its correctness oracle.

Controlled RNG-return fixtures force Metronome to reject an exception and an
already-owned move before accepting Surf. Only Metronome and Surf are recorded.
A disobedience fixture forces a different actual move and rejects discovery of
the selected move. These alter data/register results inside the emulator, not
the ROM's battle code, animation scripts or clock.

The wrapper tests exercise all 333 permanent moves, invalid values, both sides,
all seven caller WRAM banks, transient-byte reuse and garbage collection.
They check registers, WRAM/SRAM bank ownership and speed restoration. SRAM
write tracing must remain empty throughout discovery helper calls.

The normal-input roundtrip is separate: choose Fight/a move, execute it, flee,
return to double-speed overworld, use the normal Save menu, cold-start Continue
and open Moves Dex. The discovered name/details are audited against the bitmap.
It is not only an injected-helper persistence test.

### Results

Final qualification passed with **no new runtime regression**. The existing
sampled-cry exceptions below are unchanged, not silently counted as clean
playback. Production and all 19 protected production/rollback inputs retain
their expected hashes. The accepted stage-two owner remains unchanged.

| Suite | Qualified coverage |
| --- | ---: |
| Battle wrapper: all permanent IDs, invalid IDs, actors, seven WRAM banks, reuse/GC and ownership | 4,724 cases |
| Native battle policy: 50 scenarios, both actors, four display phases | 400 cases |
| Supplemental first-turn Bide, both actors, four phases | 8 cases |
| Static effect-script presentation audit | 114 scripts |
| Normal-input battle, flee, Save, cold Continue and visible known Moves entry | 1 complete roundtrip |
| Permanent bitmap helpers / bounded menu snapshots | 2,380 / 4 cases |
| Acquisition helpers, packed indices, PP-Up bits, reuse/GC and ownership | 12,276 cases |
| Storage corruption/recovery/migration/lifecycle | 1,490 cold loads; 5 lifecycle cases |
| Interrupted normal writes / recovery repair, included in cold loads | 152 / 150 prefixes |
| Owned-move migration / interrupted full-capacity migration | 29 cases / 150 additional cold loads |
| Acquisition/learning source positives and negatives | 59 cases |
| Modern / Legacy species Dex, all 373 species and stress families | 6,555 / 6,555 cases |
| Moves browsing/pages/interfaces, both orders | 2,702 cases; 544 interface checks; 176 transitions |
| Zero / one / 25-known Moves fixtures | 8,058 browse/page cases |
| Scrollbar visuals / accepted popup placement | 16 / 16 cases |
| Final scrollbar pixel audit | 16 images; 16,640 checks; zero mismatches |
| Modes/Search integration / Listing popovers | 66 / 144 cases |
| Ranked Search all type pairs / sparse flags / active stress | 2,052 / 144 / 192 cases |
| Search Results all-species scrolling / badge fixtures | 108 cases with 3,324 scroll checks / 114 cases |
| Search listing returns / default-empty cases | 36 / 24 cases |
| Modes/Unown stage-and-reveal | 32 cases; 192 captured transitions |
| Battle regression: 100 moves, two sides, four phases, two builds | 1,600 cases |
| Sampled cries: 20 species, six contexts, four phases, two builds | 960 cases; unchanged 32 known warnings per build |
| Custom Pack/TMHM/Apricorn selections | 464 paired-build cases |
| General menu input/register contracts | 1,792 inputs across ten location/build jobs |
| Surrounding gameplay | 22 paired-build scenarios |
| Repeated battle entry, post-battle learning and whiteout | 24 paired-build jobs |
| Popup input readiness | 148 paired-build cases |
| Final independent host qualification, including current-link scheduler/New Entry contracts | 140 tests; 3 intentional obsolete-path skips |
| Manual first-use fixture cold reload | All 24 Pokemon / 93 supplied moves verified |

Rows describe coverage, not independent additive totals; the storage prefixes
are included in cold-load counts, and the 60 maintained current-link checks are
included in the final 140 host tests. Modern's 6,555 cases combine the 6,182-case
main pass with its separate 373-species warm pass.

Blocked and permitted actions are both exercised. For example, the naturally
varied paralysis fixtures produce three blocked/five used outcomes, and the
confusion fixtures seven blocked/one used outcome across actors/phases. The
independent witnesses verify each actual result; explicit RNG fixtures cover
Metronome rejection and disobedient substitution deterministically.

The surrounding gameplay/menu campaigns retain building/map transitions,
purchases and Pack contents, wild/trainer battles, party/PC catches, leveling,
evolution, hatch, fishing, phone, healing, Save/reload, the Ruins sliding puzzle,
PC and daycare dialogs, nested battle Stats/Pack, Pokegear/radio/mail, trainer
card, options, mart and game corner. Repeated-transition jobs include 64 battle
entries, eight actual post-battle learning prompts and eight defeats, retaining
double-speed world/normal-speed battle ownership. This is broad regression
coverage, not every possible story/map permutation or physical-cartridge
power-loss certification.

## Native Timing

One physical display interval is 70,224 base-clock cycles, **16.7427 ms**.
These are emulated hardware costs, not host test throughput. The focused
runner's tick unit is half a base-clock cycle, so its divisor is 140,448;
the performance runner uses 70,224. Neither CPU double speed nor runner
tick units change the LCD's physical display rate.

The **normal-speed battle wrapper body** measures:

| Statistic | ms | Display intervals |
| --- | ---: | ---: |
| Minimum | 0.613 | 0.03663 |
| Median | 0.710 | 0.04244 |
| Maximum | 4.867 | 0.29067 |

The maximum includes an interrupt/display-phase overlap. These boundaries
cover entry to return of the wrapper body, including its internal index/bitmap
calls, but exclude the outer preserving macro/farcall shell. They are **not**
whole-button latency or battle-turn duration measurements. The flag is set
after accepted presentation/preparation; no save, full ownership scan or
animation retiming is added to a turn. Duplicate uses simply OR the same bit.

### Save And Continue Completion

Medians of four fresh native runs per path against accepted stage two. Load
rows exclude boot/title/Continue dialog and the later world handoff; Save
excludes its confirmation/text. These are completion costs, not visible first
response measurements.

| Path | Stage two ms / intervals | Stage three ms / intervals | Delta ms / intervals |
| --- | ---: | ---: | ---: |
| Valid modern Continue | 190.567 / 11.38212 | 190.567 / 11.38212 | 0 / 0 |
| Normal Save | 150.468 / 8.98710 | 150.437 / 8.98523 | -0.031 / -0.00187 |
| Review-size legacy migration | 188.694 / 11.27025 | 188.694 / 11.27025 | 0 / 0 |
| Full-capacity legacy migration | 510.062 / 30.46474 | 510.062 / 30.46474 | 0 / 0 |
| Damaged selected record / valid donor | 202.020 / 12.06613 | 202.020 / 12.06613 | 0 / 0 |

The tiny Save difference is phase variation, not a save optimization. Stage
three adds no storage work. Legacy bootstrap remains a one-time cost for valid
migrated saves, not a scan on every Continue or Moves Dex entry.

### Visible Responsiveness

Moves interface medians pool 16 presentation/phase fixtures. First means first
visible pixel change after input; Complete means final expected visible output,
not completion of invisible background work. The accepted stage-two and new
stage-three medians below are the same at the shown precision.

| Path | First ms / intervals | Complete ms / intervals |
| --- | ---: | ---: |
| Enter Moves | 42.677 / 2.5490 | 109.648 / 6.5490 |
| Move down | 58.402 / 3.4882 | 58.402 / 3.4882 |
| Page right | 58.406 / 3.4884 | 58.406 / 3.4884 |
| Open Sort | 41.226 / 2.4623 | 41.226 / 2.4623 |
| Change sort | 58.412 / 3.4888 | 58.412 / 3.4888 |
| Return to Modes | 41.522 / 2.4800 | 217.447 / 12.9876 |

Across all eleven measured Moves transitions, median first/completion deltas
are zero. The largest individual increase is 0.00011392 interval / 0.001907 ms.
All 464 paired Pack/TMHM/Apricorn pixel first/completion metrics match exactly.
The separate 148 popup input-readiness cases also match exactly, avoiding the
mistake of interpreting a late idle pixel change as delayed input ownership.

The 100-move suite's first requested-animation duration deltas range from
-0.05047 interval / -0.845 ms to zero, with median zero across 800 paired
move/side/phase comparisons. This is sub-display phase variation, not a
retiming claim. No animation/audio/HOME source changes were made.

### Limits And Existing Issues

- Trainer/Tower/tutorial/scripted focused cases apply declared context data at
  a valid battle-turn entry. They check discovery in those contexts, not a
  complete natural Tower challenge or the entire Dude auto-input tutorial.
  Separate gameplay regressions cover ordinary wild/trainer battles.
- Charge cases prove first-turn discovery and retained flags after explicitly
  canceling the pending charge state. They do not replay every Roar/faint/
  interruption permutation. The Focus disruption fixture sets the lost-focus
  flag after real tightening presentation and checks the actual turn owner;
  it is not a natural replay of every possible damaging interruption.
- Paralyzed/confused/disobedient outcomes use independent presentation witnesses;
  controlled additional cases force specific substitution/rejection branches.
- Stage-two acquisition fixture qualifications remain applicable, including
  data-only evolution/high-index gift tables, committed-hook-only battle
  learning cases and invalid low-level egg/contest calls. See its report for
  exact limits; this stage does not redefine those as complete natural events.
- `BATTLE-CRY-01` remains the pre-existing wild-appearance issue for Dusknoir
  (45 missed blocks), Groudon (198), Kyogre (226) and Yanmega (405). These
  precede later catch/faint events and are not intentional cancellation.
- The previously documented battle-menu glyph/switch flash, Glacial Slam OAM
  slicing and Superpower shake-intensity investigation are not addressed here.
- No battle-animation, audio or HOME source differs from stage two. Passing
  completion/audio checks does not establish pixel-identical comparison videos.
  No timing adjustments or replacement artwork were made.

### Host Harness Maintenance

The maintained current-link host checks initially had one outdated assertion
treating `rKEY1` double speed as unsupported. Production and stage two already
support double-speed Dex playback. The test now checks the accepted double
timer profile, wrong-speed/reload combinations, insufficient audio runway and
bank restoration. All **60** current-link checks pass on both accepted stage
two and stage three. This changes tests only, not the game policy.

The separately attempted legacy `make test-dex-timing` diagnostic reports
187 tests with six assertion failures, sixteen errors and 103 skips against
the untouched production ROM. It expects historical instruction costs and
removed trace symbols such as `wPokedexAnimTraceStageEntryLY`, as documented in
[the timing-tool guide](dex_timing_model.md#historical-reproduction). Its raw
output is retained as `standard-timing-model.log`. It is not counted as a
passing current-link gate and was not made green by weakening frozen historical
assertions. Current native playback and current-link contracts are the relevant
acceptance checks.

## Reproduction

Build a fresh private candidate from the accepted stage-two owner:

```sh
env PYTHONPATH=tools python3 tools/build_move_battle_use_prototype.py \
  --source build/dex-moves-acquisition-20261008 \
  --output build/dex-moves-battle-use-YYYYMMDD --jobs 6 --prepare
```

Run `move_persistence`, the existing paired menu/100-move campaigns and
`move_battle_use --only contract` before the discovery lane. The discovery lane
then runs its 400 semantic cases, audio-dependent gameplay/custom/transition
regressions, timing checks and both review saves. The `dex` and `ui` lanes
provide all-species and interface qualification. Do not exceed six native
workers when running lanes together. Supplement Bide with
`move_battle_use --only semantic --kinds bide --jobs 2`. Finish with
`acquisition_report final` only after every required report exists.

Evidence is retained under the private build directory. Large raw traces may
be losslessly gzip-compressed after their writers have exited; summary JSON,
native screenshots, source/symbols/map and manual-review files remain directly
available. This round's completed raw menu traces were gzip-compressed and
integrity-checked, reducing the round's build folder from about 13 GB to 5.6 GB
without deleting evidence or modifying earlier builds. Neither this report nor
the build tool promotes production.
