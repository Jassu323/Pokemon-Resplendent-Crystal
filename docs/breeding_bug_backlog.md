# Breeding Bug Backlog

Updated 2026-10-17. Gameplay breeding issues are separate from Dex presentation
and final egg-move content. A passing Dex family/page test does not close these
underlying gameplay reports.

## BREED MOVE 01 TM Inheritance Stops At The First Table Entry

Status: Confirmed in current production and the private egg-page prototype;
not fixed by the Dex qualification.

### Reproduction

The focused native helper fixture uses Treecko as the offspring, an empty
mother move list, and Rest in the father's move list. Treecko's authoritative
TM compatibility includes Rest, and its explicit egg-move list does not.

1. Set the ordinary breeding helper fields to that context using allocated
   transient species/move IDs, not raw National/move indices in live fields.
2. Call the real `GetEggMove` with DE pointing at the father's Rest slot.
3. It returns carry clear instead of accepting inherited Rest.
4. Call the real `InitEggMoves` with an empty offspring move array. It leaves
   that array empty instead of inserting Rest.

The source-driven native reproduction is
`build/dex-egg-placeholder-20261017/egg_checks.py tm-fallback`.
Its four raw failed checks, matching per-link checkpoints and logs are retained
under `build/dex-egg-placeholder-20261017/tm-fallback/`. This is an explicit
helper-input test on cold-booted native cores, not a claimed naturally generated
egg/hatch reproduction.

### Cause

`GetEggMove.tmhm_loop` in `engine/pokemon/breeding.asm` reads a 16-bit move, then
checks for the zero terminator with:

```asm
ld a, h
and l
jr z, .done
```

That is not a 16-bit zero test. Every valid index below 256 has a zero high
byte, so AND produces zero and exits. Current `TMHMMoves` starts with
DynamicPunch, index 223 (`$00df`). Both ROMs return HL 223 and never write the
putative Rest move to `wPutativeTMHMMove`. The intended TM compatibility query
is never reached in this fixture.

The earlier explicit egg-list loop uses a different `$ffff` terminator; its
AND/combined-byte test must not be changed as part of this proposed correction.
The shared-parent level-up path is separate too.

### Production Comparison

- Production: `302099f5836115c776de6606379820fbc661c82824aee438364afd4e7f7834e9`.
- Private prototype: `d76657ba00cb3b24b4126dbf552890e3b6b2c73d4a11a67e3d0fd43286ebef5b`.
- Both have the same offending instruction and the same two raw failures.
- The private prototype has no new failure identity. Its explicit egg-list
  path accepts the placeholder moves, including indices above 255; that does
  not repair the separate TM fallback.

An initial broad native probe incorrectly assumed that the production TM
fallback would supply Rest for Barboach. Its failed log is retained as
`egg-checks.log`. The corrected egg-path qualification records that overlap as
an existing exception and is accompanied by this separate strict reproduction;
it does not relabel the TM inheritance behavior as correct.

### Candidate Fix And Required Follow Up

The local candidate is to replace only the TM loop's `and l` with `or l`.
This is a one-opcode substitution with zero ROM allocation or RAM growth.
The two instructions have the same isolated instruction cost; the corrected
routine would naturally execute more of the previously skipped lookup.
No completed-routine timing gain or cost has been measured.

Implementation complexity is low. Validation should be broader than that one
opcode: positive/negative TM and HM inheritance, move indices above 255,
terminator handling, explicit egg moves, shared-parent level-up moves, Ditto,
parent roles, PP/four-slot behavior, and a natural daycare-generated egg/hatch
control. Newly reachable TM compatibility behavior may expose another old
assumption, so do not claim the complete breeding path fixed from Rest alone.

No fix or production change is approved or implemented in this report.
