# Battle Tower Testing Findings

Review: 2026-10-14. The independently runnable suite and coverage limitations
are documented in [Battle Tower Regression Suite](battle_tower_regression_suite.md).
Evidence is in `build/dex-cleanup-20261014/battle-tower-final/`.

## Confirmed Existing Prize Defect

`BattleTower_GiveReward` in `engine/events/battle_tower/battle_tower.asm` still
checks `wNumItems`, `wItems`, and `MAX_ITEMS`. Every vitamin in its current
five-item reward pool is assigned to **Medicine**, not Items, in
`data/items/attributes.asm`.

This creates two incorrect decisions:

1. A full unrelated Items pocket can reject a prize even when Medicine has room.
2. An Items pocket with room can approve a prize that Medicine cannot accept.

The second problem is aggravated by `Script_GivePlayerHisPrize` in
`maps/BattleTower1F.asm`: `giveitem ITEM_FROM_MEM, 5` sets `wScriptVar` false
when receipt fails, but the script does not test that result. It continues to
the congratulatory text and `BATTLETOWERACTION_1D`, marking the prize received.
The pending prize can therefore be lost without delivering the five items.

### Reproduction

Use a copied save with a completed challenge and an unclaimed HP Up prize.
Keep room in Items. Fill all **40 Medicine slots**, with 39 full non-reward
stacks and one **95-HP-Up** stack. Speak to the receptionist.
Five more would exceed that stack's limit with no free slot. Expected: refuse delivery and
retain the pending prize. Actual: Medicine remains at 95, but challenge state
becomes 4, indicating receipt. The suite's `prize-medicine-full` case creates
this declared, valid full-pocket/stack-boundary fixture and drives the normal dialogue.
Multiple stacks of one item are supported by `PutItemInPocket`; a lone stack
of 95 with a free slot is **not** a failure case, since receipt can put the
overflow into another stack. The earlier lone-stack probe was a test error
and is preserved in the attempt history, not accepted as evidence of loss.

For the opposite error, fill Items while leaving Medicine able to accept five
vitamins. The old guard returns the Potion sentinel and refuses the prize.
The low-level `reward-routing` phase isolates both wrong decisions for all
five vitamins, with quantity 94 as the successful boundary control.

### Production And PR 16 Comparison

Both pre-cleanup production and the cleanup ROM reproduce the issue. The
15-case routing phase has ten intended-policy failures on each ROM, with
matching case identities. The normal-button prize failure also matches.
These are not new failures caused by deleting the mobile Slowpoke assets or
retiring their three screen entries.

The pocket mismatch dates to the Medicine feature, commit `30520c379`
(2026-05-10). The capacity guard and unconditional prize script predate it.
[PR 16](https://github.com/Jassu323/Pokemon-Resplendent-Crystal/pull/16), merged
as `8d19d3bb6b79efbd7e5ee9f174ee8279d45f28c9` on June 25, did not introduce
this mismatch. This attribution uses the local merge diff and file history;
it is not a claim that every other surviving mobile branch is correct.

### Fix Choices, Not Applied In This Cleanup

| Approach | Complexity | Cost | Risk |
| --- | --- | --- | --- |
| Change the vitamin capacity query to Medicine; also branch on failed `giveitem` before marking receipt | Low/moderate | Likely same-size pointer/limit substitutions plus a small ROMX script branch; no new persistent/RAM fields expected. Not linked/measured yet. | Reward pool becomes coupled to one pocket; future non-vitamin rewards require revisiting the guard. Must preserve state 3/4 save transaction rules. |
| Remove duplicated capacity policy and let actual item receipt determine success; mark receipt only on success | Moderate | A small script/control-flow change; obsolete query logic may return ROMX space. Exact net cost needs a prototype. No new RAM expected. | Less pocket-specific fragility, but the prize sentinel/text/script-variable contract must be audited carefully. Test successful, failed, canceled and interrupted claims. |

Prefer the second direction for a later scoped fix, because normal item receipt
already owns pocket selection, stack limits and insertion. Do not simply swap
the pocket pointer while leaving the unconditional received-state transition.
Test all five rewards, 94/95/99 stacks, both pockets' capacity, normal saving,
canceled saving, reset before/after save, repeated receptionist interaction,
and cold state-4 rollback to state 3. No shared interrupt changes are needed.

## Budget And Fixture Findings

Initial native battle probes timed out with no moves/PP, oversized stats, or
Tackle against Ghosts. Those attempts remain preserved. Replaying the captured
states showed HP changes and animation/turn progress, so the evidence did
**not** establish a frozen `BattleMoveInfo_UpdateTilemapAndAttrmap.wait` loop.
A PC sampled in that loop is not sufficient to diagnose a permanent stall.

The current completion fixture uses Aerial Ace, selected-group levels, HP 999
and stats 500. The no-PP fixture remains a separate Struggle stress test.
Both are synthetic helper-level battle batches, distinct from the normal-button
seven-opponent streak and controlled loss. Budgets, blocked positions, actual
outcomes and retries must remain visible in the final campaign report.

The final direct matrix completes **140 battles per ROM with zero battle
failures**. Each case uses a fresh checkpoint and native prior-position
`CopyBTTrainer` transitions. Earlier chained-owner/setup probes are not the
acceptance matrix. One production Aerial Ace case against a defensive
Tyranitar exceeded 60,000 frames while continuing to change HP/PP; it returned
natively at 90,063 total frames after the single bounded continuation, with
all restoration/result assertions passing. This extreme synthetic-HP battle
is not an ordinary-player performance benchmark or an interrupt deadlock.
The original timeout is retained. No candidate battle needed that extension.

Other corrected harness assumptions: Continue needs initialized map objects;
Tower teardown reloads the saved party, so the declared party must be saved;
party switching needs navigation to a living slot rather than repeated A;
the direct battle owner returns at normal speed until map setup; vitamins must
be checked in Medicine rather than Items. None of these test corrections
modified game battle/interrupt code.

## Residual Coverage

Save/quit and resume at every streak position, every normal-button level group,
all simultaneous-KO outcomes, corrupted downloaded-data repair, CGB revision
coverage, and exhaustive transaction interruption remain additional work.
Do not label the entire Tower clean solely because helper phases pass or
because the main Dex/full-animation suite is green. The independent report
distinguishes clean correctness, matched baseline defects, and incomplete
attempts. Final implemented coverage is complete with no new candidate failures;
the matched prize defect keeps `clean` false. It is logged as `BT-REWARD-01` in
the [Battle Tower bug backlog](battle_tower_bug_backlog.md) and deferred for a
later Tower-focused fix.
