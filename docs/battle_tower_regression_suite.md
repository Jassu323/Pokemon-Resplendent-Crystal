# Battle Tower Regression Suite

Maintained: 2026-10-14. This is an independently runnable addendum to
[Full Regression Suite](full_regression_suite.md), not a replacement for it.
It describes implemented tests, fixture limitations, required manual coverage,
and failure handling. A future thread must not interpret the coverage matrix
as a claim that every possible Tower battle or save interruption was tested.

## 1. Purpose And Current Result

Test the supported offline Battle Tower after relinking, shared-engine changes,
save changes, or removal of mobile/printer code. Cover the catalog, permanent
and transient IDs, rules, menus, opponent generation, challenge state, battles,
rewards, and return to gameplay. Unsupported Mobile System GB screens must
remain safely retired rather than accidentally becoming playable.

Implementation: `tools/dex_timing/battle_tower.py`. The October 14 campaign is
`build/dex-cleanup-20261014/battle-tower-final/`. Its baseline is pre-cleanup
production, not vanilla Crystal. Native observers use SameBoy CGB E; other
CGB revisions and actual hardware remain additional coverage, not implied
Tower passes from the Dex's six-model tests.

The suite deliberately detects an existing prize-pocket defect on **both**
production and cleanup. Thus `report` must not claim an entirely clean Tower.
See [Battle Tower Findings](battle_tower_testing_findings.md) and the deferred
`BT-REWARD-01` in the [Battle Tower bug backlog](battle_tower_bug_backlog.md).
Do not delete, skip, or reverse those expectations to make the summary green.

Final October 14 result: implemented case coverage complete; protected inputs
unchanged; **no new candidate failures**. Both ROMs pass the 242 data, 2,136
rules, 610 legacy-action, 210 team-generation and 140 direct-battle cases.
Both reproduce ten vitamin-routing assertions and the one normal-button
failed-prize assertion. Normal-button seven-opponent completion and loss return
pass. One production Tyranitar battle completed after its bounded continuation
at 90,063 total display frames; its initial timeout remains preserved.
`report.json` therefore records `coverage_complete: true`, `no_new_failures:
true`, and `clean: false`. Coverage means the implemented matrix, not all
additional/manual scenarios in section 7.

## 2. Baselines And Safety

October 14 inputs:

| Input | SHA-256 |
| --- | --- |
| Pre-cleanup production ROM | `e5f14a4e77082323dce6756f59c8b8951a00f243ff25a87ebbd30d2293b4dc4e` |
| Cleanup ROM | `dbef024fdaa1cdceb5a7458e323ac5d0f7e012ddfabb35585e3d806219f3ca7a` |
| Pre-cleanup commit | `81ff02a25` |

Use separate frozen source trees containing matching `pokecrystal.gbc`, `.sym`,
and `.map`. The candidate can be the shared checkout only if no build/edit will
occur while the campaign runs. Each tree needs its own converted graphics and
generated tables. Symbols from a different link are never acceptable.

Preparation copies the donor battery, records protected input hashes, compiles
fresh native cores, and writes `config.json`. It never saves over the donor.
The output must be a new directory under this repository's `build/`; an
existing output is rejected. All injected data and native checkpoints are
private fixtures. The runner executes the actual linked game code; it does not
patch the ROM, replace interrupts, advance animation counters artificially,
or force completion flags.

CPU checkpoints are specific to their exact ROM/core. Never transplant a
baseline `.s0` into the candidate. Construct equivalent semantic fixtures in
each ROM through its own ID-conversion APIs instead.

## 3. Environment

Use Python 3, the repository modules, Clang/C11, the normal RGBDS toolchain,
SameBoy source at `~/Documents/GitHub/SameBoy`, and the CGB boot ROM at
`/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin`.
Record dependency versions and SameBoy revision with the run.

October 14: Python 3.13.12, RGBDS 1.0.1, Apple Clang 17.0.0,
SameBoy `c4cf7abab79a4e22dc17e0704995976cb2751b2d` with a clean worktree.
The main cleanup campaign retains `dependency-versions.json`.

```sh
export PYTHONPATH=tools:.
python3 --version
rgbasm --version
clang --version
git -C ~/Documents/GitHub/SameBoy rev-parse HEAD
```

The current default donor is
`build/dex-moves-search-final-review-20261011/legacy-input.sav`.
It is a retained local dependency, not available on every clean clone. Supply
`--battery` with another valid battery when necessary. Its checksums, save
layout, party records and permanent-ID extensions must match this game.
Never use a foreign ROM's battery simply because its length is correct.

## 4. Running Independently

Example using the retained October 14 frozen trees and a fresh output:

```sh
python3 -m tools.dex_timing.battle_tower prepare --output build/battle-tower-new-review --baseline-source build/dex-cleanup-20261014/runtime-regression/baseline/candidate --candidate-source build/dex-cleanup-20261014/candidate --battery build/dex-moves-search-final-review-20261011/legacy-input.sav
python3 -m tools.dex_timing.battle_tower all --output build/battle-tower-new-review
```

For a future change, replace both source arguments with that review's frozen
production/candidate trees. Do not reuse these October 14 builds as evidence
for a new candidate. `all` runs every phase and preserves non-clean results;
its exit status is nonzero if any correctness failure remains, including a
matched baseline defect. Inspect `no_new_failures` separately from `clean`.

Phases can be run or retried independently:

```sh
python3 -m tools.dex_timing.battle_tower data --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower rules --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower actions --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower teams --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower reward-routing --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower ui --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower battles-moves --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower battles --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower timeout-audit --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower recover-timeouts --output build/battle-tower-new-review
python3 -m tools.dex_timing.battle_tower report --output build/battle-tower-new-review
```

`recompile` rebuilds observers after a host-only harness change. A game relink
instead requires fresh preparation and fresh checkpoints. Retrying a phase
preserves the preceding phase directory as `*-attempt-N`; inspect its old
summary before using extra timeout files left in the canonical directory.

When collating independently run battle phases, `import-battles --source-output
<other-output>` verifies the same protected inputs and ROM hashes, archives
the previous phase directories, and records `battle-phase-provenance.json`.
This was used to retain the final fresh-checkpoint battles from
`battle-tower-isolated-2/` alongside the earlier menu/rules phases. It is not
permission to import results from another ROM or replace missing cases with
old passes.

## 5. Implemented Coverage

Counts are per ROM, not combined baseline/candidate totals. They overlap and
must not be advertised as independent end-to-end playthroughs.

| Phase | Cases | What it proves |
| --- | ---: | --- |
| Data | 242 | All 210 catalog records across ten level groups and all 32 action pointers |
| Rules | 2,136 | Party size, species/items/eggs, level limits, legendary exceptions, bank restoration |
| Actions | 610 | Dispatch/state/flags, level persistence, streak reset, legacy capacity contract, cold reload |
| Teams | 210 | Ten groups x three seeds x seven positions; 630 generated opponents per ROM |
| Reward routing | 15 | Vitamin capacity follows Medicine, including the 94/95 quantity boundary |
| UI | 11 | Normal-button cancel/explanation/save/level paths, real challenge entry, streak/prize, loss, capacity failures |
| Battles with moves | 70 | Native battle owner at every group/position with Aerial Ace and declared combat fixtures |
| No-PP battles | 70 | Native Struggle/AI path at every group/position with declared combat fixtures |

`report` checks exact case counts, unique case identities, paired coverage,
fatal errors, and unchanged protected inputs. Partial runs, missing reports,
blocked cases and timeouts cannot become clean passes. The comparison matches
case identity and issue text; RNG-dependent timeout differences require
investigation, not blanket acceptance because both versions timed out somewhere.

### Catalog And ID Widths

The oracle independently parses `data/battle_tower/parties.asm` and constants.
It checks linked species, held item, four permanent move indices, level, and
record stride. Zero is legal for an empty move slot. The October catalog has
210 records, 373 species and 333 moves; intentional catalog changes require
updating the fixed coverage contract explicitly.

Generated opponents must correspond to a record in the selected 21-entry
pool. Check distinct species and held items within the team, avoidance of the
previous two teams, shifted 12-byte history, seven distinct trainers, level,
progress, and in-progress state. Resolve transient IDs back to permanent
indices with that ROM's APIs. Enemy generation alone must not discover moves.

### Rules

Test party counts 0 through 6 at the count helper. Test each duplicate-species
pair and all 256 item bytes against all three duplicate-item pairs; zero means
no held item and may repeat. Test eggs in every occupied slot. For every level
group, test below/equal/above the limit in all three slots and incoming WRAM
banks 1 through 7. Verify the current special treatment of Mewtwo, Mew, Lugia,
Ho-Oh and Celebi below L70, with ordinary/extended-species controls.

These low-level count fixtures do not imply that calling the full rules owner
with corrupt party data is safe. Normal UI invalid-party feedback belongs in
the manual matrix below as well.

### State And Persistence

Exercise all 256 challenge-state getter values; supported setters from states
0 through 4; all 256 explanation-flag values without changing unrelated bits;
all ten level-group save/reload values; reset of trainer/progress records; all
32 action entries; and cold reload of supported states.

State meanings: 0 idle/canceled, 1 saved mid-challenge, 2 in progress, 3 won with
prize pending, 4 prize received but not finalized by a normal save. Cold load
deliberately rolls 4 back to 3 because the received inventory may not have been
saved. A normal `SaveGameData` finalizes 4 to 0. Do not "fix" either transition
or change its test to expect the opposite without auditing transaction safety.

Multiple stacks of an item are supported. The 94/95 Medicine boundary fixtures
fill all 40 slots, leaving only that vitamin stack's remaining capacity. A
single 95 stack with free slots can legitimately accept overflow in a new
stack and must not be treated as a failed grant.

The 610-case action phase records the original capacity helper's behavior as
a legacy contract. It does not certify that choosing the Items pocket is
correct. The separate reward-routing phase intentionally tests the correct
Medicine policy and currently fails against both ROMs.

### Native Menus And Battles

Menu cases boot copied batteries and use buttons through the receptionist,
save prompt, level menu, elevator/hallway, and actual battle-room script.
The full-streak case covers all seven opponents, healing, continuation prompts,
five-item prize delivery to Medicine, lobby return, and save finalization.
The controlled loss case covers choosing surviving party members and the
native loss return. Prize-capacity cases use normal receptionist dialogue.

The map fixture must run `LoadMapObjects` and `RefreshMapSprites` before it is
saved. Editing only map IDs/coordinates leaves Continue's saved object table
inconsistent and can make the receptionist unresponsive. That is a setup
error, not evidence that a ROM broke NPC interaction.

Direct battle phases use three distinct species, selected-group levels, no
held items, HP 999, and five stats of 500. These are declared synthetic combat
stats, not naturally legal Pokemon. They exercise native damage, AI, moves,
animations, result delivery and restoration; the normal-button UI streak
supplies complete script integration. Do not present direct helper batches as
ten complete ordinary-player tournament playthroughs.

Each direct case starts from its own freshly restored overworld checkpoint,
then runs the native opponent loader repeatedly to generate the requested
streak position/history. It does not reuse a preceding battle's VRAM/clock
state without the real map-reload protocol. A timeout does not block testing
later positions from their own checkpoints. Earlier chained-owner attempts
remain in the campaign history; only the UI streak claims continuous play.

No-PP fixtures use native Struggle. Move fixtures use Aerial Ace to avoid
Tackle's Ghost immunity and evasion-dependent completion. OHKO moves, Destiny
Bond and other real AI outcomes can still cause losses. Both win and loss are
valid battle-owner returns; a failed owner or corrupt result is not.

The input driver alternates press/release and chooses a living party slot
after fainting. It must not repeatedly press A on a fainted first slot or keep
sending navigation during a text prompt. Observe menu state before diagnosing
such a run as a game hang. The direct owner remains at normal clock speed on
return; map setup, not this owner, restores overworld double speed.

## 6. PR 16 And Retired Mobile Boundaries

Audited [PR 16](https://github.com/Jassu323/Pokemon-Resplendent-Crystal/pull/16)
through local merge `8d19d3bb6b79efbd7e5ee9f174ee8279d45f28c9` and first parent
`1dc9e308d`. Preparation preserves the complete diff as `pr16.diff`.

That removal intentionally retained code intertwined with Battle Tower.
`home/mobile.asm` now supplies failure/return stubs; removed mobile API,
trade, printer and menu modules do not provide real backend functionality.
`BattleTowerAction_10.Action4` was changed to clear `s5_a800` and return false.
Do not interpret all surviving mobile login branches as supported features.

The October cleanup removes two Slowpoke blobs and three obsolete loads, and
turns `Function11c1ab`, `Function11765d`, and `Function1719c8` into safe returns.
It keeps their public labels and special IDs. Battle Tower, its trainer text,
ordinary level/cancel menus, `GiveOddEgg`, and shared callbacks stay linked.
Do not remove whole `mobile/*` includes based solely on their filenames.

Check exact RET opcodes, stable special pointers, and supported UI paths after
future removal passes. A forced unsupported login returning early is not a
normal Tower regression. A normal level/cancel path entering that login branch
would be a regression and must fail the suite.

## 7. Required Additional/Manual Matrix

The following are required before claiming exhaustive Tower acceptance, but
are not all automated in this runner. Record each performed case explicitly:

| Area | Additional coverage |
| --- | --- |
| Map access | Exterior/gate/lobby/elevator/hallway/battle-room travel, exits and NPC/rules-sign dialogue |
| Restrictions | Full normal-button feedback for wrong party count, eggs, duplicate species/items, levels and banned species |
| Levels | Normal-button selection and full tournament at each of the ten groups; both cancel-confirmation answers |
| Resume | Save/quit after opponents 1 through 6, reboot, resume without reset of level/team history/progress/options |
| Cancellation | Decline next opponent, decline save, cancel challenge Yes/No, abort without saving and restart |
| Transactions | New Game, different save identity, pending prize, save cancellation, primary/backup corruption, interrupted normal save |
| Rewards | Every vitamin, empty pocket, existing 94/95/99 stack, full actual Medicine, unrelated Items fullness, repeated claim, reset before/after save |
| Battle rules | Player items forbidden, Set behavior, no experience/EV payout, no catching/escaping, all faint/switch outcomes, simultaneous KO and OHKO |
| Data repair | Corrupt downloaded trainer names/moves only where still supported; ID GC/locked IDs across repeated streaks |
| Restoration | Options, party/PP/status/healing, map/music/SFX, LCD/STAT/VBlank/scroll/palette ownership, ROM/WRAM banks, input and overworld speed |
| Interactions | Dex and Pack before/after Tower; PC/daycare before/after; normal saving; sampled and synthesized cries |
| Displays | Multiple CGB revisions, frame-by-frame menus/maps/battle returns and audio playback; hardware if available |

Existing full regression provides broad shared-engine, save/discovery, custom
menu, PC/daycare and all-move coverage. It is supporting evidence, not proof
that each Tower-specific transaction above ran. Mobile networking/printer
hardware is retired and intentionally excluded.

## 8. Triage, Negative Controls And Retention

First distinguish a setup failure, a budget/input-policy failure, an existing
production defect, and a new candidate regression. Save CPU state, screen,
registers, relevant party/Tower fields, and matching ROM hashes. `timeout-audit`
replays only current no-PP timeouts in their own ROM, samples HP/state, and
counts move-info, animation, turn and return entries. HP/turn progress refutes
a claim of a frozen LY wait, but does not by itself qualify the original case.

Increase a documented budget only when evidence shows legitimate progress;
rerun the original assertion and all blocked cases. Do not replace a timeout
with a pass, force a return flag, or count unrun positions as tested. Preserve
the original attempt even if the later run completes.

`recover-timeouts` allows one additional 60,000 display-interval budget for a
recorded active native call, with a seven-frame input cadence rather than the
original sixteen-frame cadence. It reloads only that ROM's checkpoint, waits
for the genuine caller PC/bank/SP, and rechecks the same battle/restoration
contract. Initial failures remain in `summary-before-recovery.json`; recovered
rows retain initial, continuation and total frame counts. It refuses a second
recovery attempt. Synthetic HP 999 plus defensive/Leftovers AI can make a
battle much longer than a normal player fixture. A still-active call remains
a timeout, never a forced success.

Host negative controls should verify that a corrupted linked catalog field
fails its independent source oracle; a malformed action pointer fails; missing
case coverage prevents a clean report; and candidate-only issue identity fails
comparison. Keep those controls separate from acceptance ROMs.

Four such controls are implemented and pass in `tools/test_battle_tower_suite.py`:

```sh
python3 -m unittest tools.test_battle_tower_suite
```

They corrupt only an in-memory oracle copy or private report fixtures, never
the acceptance cartridge or player's battery.

Retain `config.json`, protected hashes, dependency versions, source trees or
restorable source archives, ROM/symbol/map, donor/private batteries, per-phase
summaries/comparisons, final report, PR diff, and relevant failure screenshots
and checkpoints. Checkpoints require matching SameBoy/core and are not durable
cross-version fixtures. Large routine traces may be regenerated after retaining
their findings and input hashes. Future threads should start with this file,
the findings document, and that campaign's final report, then build fresh
evidence for their own candidate.
