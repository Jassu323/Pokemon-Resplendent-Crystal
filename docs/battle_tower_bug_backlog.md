# Battle Tower Bug Backlog

Track Battle Tower issues independently of the Pokédex backlog. These issues
are deferred unless a separate fix is explicitly approved.

## BT-REWARD-01: Update Prize Capacity And Failure Handling

Status: Backlog; deferred by user, 2026-10-14. Reproduced on pre-cleanup
production and the cleanup ROM; not introduced by this cleanup or PR 16.

The vitamin prize guard still checks Items, but vitamins are Medicine items.
Unrelated Items fullness can reject a valid prize. Conversely, full Medicine
can reject actual receipt while the map script still marks it received,
potentially losing the pending prize without granting the five vitamins.
See [Tower findings and fix choices](battle_tower_testing_findings.md) and the
[independent regression addendum](battle_tower_regression_suite.md).

### Reproduction

1. Use a copied save with a completed challenge and an unclaimed HP Up prize.
2. Leave room in Items. Fill all 40 Medicine slots with 39 full non-reward
   stacks and one 95-HP-Up stack.
3. Speak to the receptionist. Actual: Medicine stays at 95, but challenge
   state becomes 4, marking receipt. Expected: refuse delivery and retain
   the pending prize.
4. For the opposite error, fill Items while leaving Medicine able to accept
   five vitamins. The guard incorrectly refuses the prize.

A lone 95 stack with a free slot is valid overflow into another stack, not a
failed grant. Multiple stacks are supported by normal item receipt.

### Relevant Code

- `BattleTower_GiveReward` in `engine/events/battle_tower/battle_tower.asm`.
- `Script_GivePlayerHisPrize` in `maps/BattleTower1F.asm`.
- `PutItemInPocket` in `engine/items/items.asm`.
- Medicine item attributes in `data/items/attributes.asm`.

### Fix Direction And Acceptance

Use actual receipt success to gate the received-state transition. Preserve
pending state on failure and the existing state-4 cold-load/save transaction.
Do not change shared interrupts or treat all mobile modules as unused.

Test all five rewards, legal multi-stack capacity, 94/95/99 with a full pocket,
free extra slots, wrong-pocket fullness, repeat claims, saving/cancellation and
reset before/after saving. The independent suite currently reproduces ten
vitamin-routing assertions and one normal-button failed-prize assertion on
both ROMs. Do not suppress those failures to make the Tower report clean.

No fix is included in DEX-CLEAN-01 or the production cleanup promotion.
