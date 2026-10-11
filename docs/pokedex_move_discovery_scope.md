# Moves Dex Discovery And Save Assessment

2026-10-07. Architecture assessment. The user accepted the three-pixel popup
alignment in the private visual prototype at `build/dex-moves-mode-20261007b`.
Retain that cartridge as the next visual baseline; this assessment does not
promote it, add discovery hooks, or modify player saves. The visual owner's
all-seen/static-unknown fixtures are not persistent discovery implementations.

The user subsequently approved WRAMX bank 2 and discovery at egg hatch.
The [persistence-only prototype](pokedex_move_persistence_prototype.md) tests
the storage layer separately, with the accepted visual build pinned as a
rollback point. Gameplay hooks and legacy owned-move bootstrap were deferred
at that stage. Subsequent private stages implement
[acquisition/learning and owned-move bootstrap](pokedex_move_acquisition_prototype.md)
and [battle-use discovery](pokedex_move_battle_use_prototype.md). This assessment
retains its original visual baseline and proposal; production is not promoted
by those prototypes.

Baseline ROM SHA-256:
`56b5b5947ba012a6981b5e1b6ae58aabe7e2ceab524da31c7da50e92f104bd2c`.

## Recommendation

Use a permanent-move-index bitmap in dedicated, non-unioned WRAMX. Update it
at actual move presentation and successful player acquisition/learning points.
Persist it through the existing primary/backup save machinery, using the
already-reserved padding rather than expanding the main save payload.

This is a moderate implementation with a high-consequence save integration
boundary. The bitmap and renderer changes are small; event coverage, legacy
save bootstrap, interrupted saves and backup repair are the substantial work.
Implement in stages in a new private candidate and qualify persistence before
wiring every discovery source. Do not change animation timing, cry scheduling,
graphics ownership or the accepted popup to implement this feature.

## Flag Identity And Lifetime

There are 333 permanent moves. One bit per move requires 42 bytes today;
recommend allocating 64 bytes, supporting 512 moves and leaving 179 additional
move identities available without resizing the bitmap. There is no second
"owned" bitmap: acquisition is another way to set the same seen bit.

For permanent index `n`, use byte `(n - 1) >> 3` and mask
`1 << ((n - 1) & 7)`. Move 256 is byte 31, bit 7; move 257 is byte 32, bit 0;
move 333 is byte 41, bit 4. Null, negative/reserved IDs and indices beyond the
compiled move count must be rejected. Legitimate permanent indices 255 and
above must not be mistaken for transient byte-ID sentinels. Struggle is a
real encyclopedia move and should be discoverable when actually used.

Party, daycare and active-box move fields contain transient byte IDs, resolved
through `GetMoveIndexFromID`. Stored inactive PC boxes contain permanent
14-bit indices: the low byte is in the move field and the upper six bits are
packed into the corresponding PP byte. They must be decoded directly without
allocating transient IDs or treating those PP bytes as ordinary PP counts.
See `home/16bit.asm`, `engine/16/macros.asm` and
`engine/pokemon/bills_pc.asm:2579`.

Three small operations should own the flag contract: check a permanent index,
mark a permanent index, and resolve/mark a live byte ID. Owned-moves walkers
must distinguish live and packed formats. Helpers restore the caller's ROM
and WRAM banks and documented registers; flag results can use the existing
far-call-compatible carry convention. They must not invoke the allocating
index-to-ID conversion just to record or display a permanent index.

Flags are monotonic within a playthrough. Forgetting, deleting, trading away
or releasing a Pokemon does not clear them. Losing a battle does not clear
them. Unsaved discovery is lost on a normal reset, just like unsaved game
progress. Track from the beginning of the game, even before the player receives
the Pokedex, so starter moves and early encounters are not omitted.

The Moves screen replaces its fixture check with the persistent bitmap. Its two
orders and all move slots remain unchanged; unseen names stay `-----` and the
selected unseen panel remains blank. No eligibility array or new sorting
records are required. Discovery does not affect the Selected Pokemon learnset
tab's existing behavior.

## Memory And Storage

The accepted link leaves bank 2 `$d500-$dfff` free: 2,816 contiguous bytes after
the conversion tables. Place the persistent bitmap there in a dedicated
section, not in the Dex/Battle Tower scratch union. Budget 64 bitmap bytes,
with up to four additional lifecycle/context bytes if needed by the final
implementation. No new WRAM0 or HRAM allocation is recommended.

The proposed bitmap itself occupies bank 2 `$d500-$d53f`. Reserve it through
a named non-union WRAM section and the linker layout, rather than an unchecked
address alias. The current bank-2 owners end at `$d1c1` (pic animations),
`$d1f1` (contest Pokemon) and `$d4ff` (conversion tables). No existing owner
needs to move or share the bitmap. Boot's `ClearWRAM` clears all seven
switchable banks; New Game's `_ResetWRAM` instead clears explicit ranges,
including only the two conversion tables in bank 2. Add the bitmap's own
bounded clear before New Game restores bank 1, and initialize live discovery
before loading a save. Do not broaden either clear to wipe unrelated owners.

Bank 1 has only six free bytes, and WRAM0 has thirteen, so neither can hold
the bitmap without relocating existing data. Inserting it into `wGameData`
would also change the existing bulk save layout. Bank 5 has a free tail after
the listing buffer and is a possible dedicated alternative, but New Game does
not automatically clear that either. It provides no reset or persistence
advantage over bank 2. Banks 3, 4, 6 and 7 are already fully assigned to shared
Tower/Dex workspaces, sampled audio, scratch or window-stack storage. Explicit
allocation, initialization and bank restoration determine safety here, not
whether a free address happened to fall inside an older reset range.

New Game requires an explicit clear. `_ResetWRAM` currently clears the bank-2
conversion tables, but does not clear this free region after them. Assuming
the new bitmap is covered by that reset would leak discoveries between games.
New Game must clear live state without erasing the previous on-disk game until
the player actually approves overwriting it. Save deletion already clears the
SRAM banks; approved replacement should also invalidate old extension records.

The two padding spans are independently available:

| Copy | Reserved span, inclusive | Proposed 72-byte record | Remaining padding |
| --- | --- | --- | ---: |
| Primary | SRAM bank 1 `$ac88-$ad0f` | `$ac88-$accf` | 64 bytes |
| Backup | SRAM bank 0 `$be88-$bf0f` | `$be88-$becf` | 64 bytes |

This uses **72 bytes per copy, 144 bytes total**, from the existing 272
reserved bytes. It does not require fitting 144 bytes into one 136-byte span.
The SRAM section sizes, existing field addresses and save-file length can
remain unchanged. The retained review battery is 32,816 bytes: 32,768 battery
bytes plus its 48-byte RTC trailer. Preserve that trailer byte-for-byte when
constructing offline test fixtures.

Keep `sSaveDataEnd`, `sBackupSaveDataEnd` and both existing checksum addresses
unchanged. The old main checksum intentionally stops before this padding.
Replacing part of its `ds $88` with named extension fields and a smaller
reserved tail must not extend the old checksummed range.

The retained legacy battery has valid primary/backup main and conversion-table
checksums, but **both padding spans contain nonzero, unrelated bytes**. They
cannot be adopted as move flags merely because the storage is reserved.

### Proposed Eight-Byte Header

| Field | Bytes | Purpose |
| --- | ---: | --- |
| Signature | 2 | Distinguish the extension from legacy padding |
| Format version | 1 | Explicit layout/migration contract |
| Bitmap byte count | 1 | 64 now; permit an explicitly supported future capacity |
| Parent main-save checksum | 2 | Reject an extension belonging to a different save transaction |
| Extension CRC16 | 2 | Detect damaged metadata, bitmap or partial writes |

Follow with 64 bitmap bytes. The extension CRC should cover the identifying
metadata and bitmap, and bind to the corresponding player/secret ID from the
main save. Parent checksum plus playthrough identity prevents recovery from
an unrelated save just because the extension itself is well formed. Neither
the existing additive main checksum nor a CRC is a cryptographic guarantee.

Use a compact bitwise CRC rather than a ROM lookup table unless native timing
demonstrates a reason to spend that table space. An independent extension CRC
is recommended over a bare additive byte sum, which misses compensating byte
changes and permutations.

During each copy's normal checksum finalization, invalidate the extension
signature, write the complete body/check metadata, commit the signature last,
and finalize that copy's main checksum after the extension is complete. Keep
the other save copy available during this sequence. Test the exact native
write order, including the two-byte marker and main-checksum boundaries.
This integrates the extension; it is not a redesign of the game's entire
existing power-loss behavior.

## Save Loading And Recovery

`TryLoadSaveFile` first validates/loads a main save and its conversion tables,
loads the active box, then immediately repairs the other save copy. Discovery
loading/bootstrap must happen **before that repair**, or the repair can write
stale/uninitialized flags over a recoverable extension.

1. Clear live discovery state and choose the main save using the existing
   primary/backup validation rules. Do not change which player/Pokemon data
   the game considers valid just because the move extension is damaged.
2. Validate and load that copy's extension if its format, capacity, identity,
   parent checksum and CRC are supported and valid.
3. If it is missing/damaged, use the other extension only when its own main
   save is valid and it belongs to the same playthrough. Do not blindly OR
   arbitrary primary/backup records or recover from unvalidated core data.
4. For a legacy save or extension recovery, add currently owned moves from
   party, active box, the thirteen other boxes and occupied daycare slots.
5. Let ordinary save/copy-repair operations write validated live state. No
   additional save or full-box scan occurs merely from opening Moves Mode.

Primary and backup checksums can legitimately differ after conversion-table
garbage collection, even for the same game. Validate each extension against
its own parent; same-playthrough fallback should not require byte-identical
conversion tables or identical parent checksum values.

A valid modern extension should avoid a routine full-PC scan on every load.
The legacy/recovery scan is read-only. Do not repeatedly call `LoadBox` while
scanning: that converts moves, changes active-box state, restores PP and can
trigger garbage collection. Scan the active `sBox` in live-ID format and skip
its stored copy; read the other boxes directly in packed-index format. Honor
box counts and daycare occupancy, skip unhatched eggs under the confirmed
egg policy, bound corrupt counts, and restore the initial bank/open-SRAM state.
Do not use `CheckOwnMonAnywhere` as a direct implementation: it filters by OT
and player ID and omits daycare, whereas acquired NPC-trade Pokemon count here.

At maximum capacity this examines 288 owned Pokemon and 1,152 move slots:
six party, 280 PC and two daycare. Duplicate/empty slots are harmless. Historic
enemy moves, released Pokemon and forgotten moves cannot be reconstructed from
an old save without a prior discovery record. Do not falsely unlock the whole
Dex to conceal that limitation.

Unsupported newer formats need an explicit policy, not the same branch as
uninitialized legacy padding. Do not silently overwrite an unknown valid
extension with zero flags. Guaranteed preservation across a downgrade to an
older ROM is outside this proposal; appending supported moves to the current
format is not a downgrade.

## Discovery Hook Coverage

User-confirmed case policies (2026-10-07): first visible charge/preparation
counts even if the attacking turn never executes; Focus Punch's tighten-focus
presentation likewise counts even if disrupted. Called moves count as actual
uses, as does the caller. Gift and contest ownership hooks should register
the final received moveset at a successful, stable integration point, including
post-gift custom rewrites. Sketch is discovered on its actual use; the move
that replaces it does not need a separate permanent-learning hook. Daycare
retrieval registers only the final received moveset, not intermediate learned
and overwritten moves. Eggs register their final moveset at hatch, not at
creation or receipt; unhatched eggs are skipped during legacy bootstrap.

| Source | Candidate integration | Important qualifications |
| --- | --- | --- |
| Actual ordinary move use, either side | `BattleCommand_UsedMoveText` / `DisplayUsedMoveText` | Record the announced current move, including misses, immunity and subsequent effect failure; not AI/team generation or menu selection |
| Initial two-turn charge | Successful awake branch of `BattleCommand_Charge` | Record the visible charge on turn one; a canceled/sleep-blocked charge must not invent discovery |
| Focus Punch preparation | `Battle_FocusPunchMessagePlayer/Enemy` | Its visible tighten-focus preparation bypasses ordinary used-move text; record that presentation, even if focus is subsequently broken |
| Called moves | Existing Metronome/Sleep Talk/Mirror Move reset-turn path | Calling and actually invoked moves both count; random candidates and rejected moves do not |
| Catch into party or directly into PC | Successful acquisition branches in the ball handler | Register the restored, actually acquired moveset, not temporary transformed battle moves; failed catches/tutorial acquisitions do not count |
| Starters and ordinary gifts | Successful `GivePoke` player path | Party and box destinations; reject failed/full acquisition and opponent generation |
| NPC trades | Final received Pokemon in `DoNPCTrade` | NPC trades remain in scope despite multiplayer being disabled |
| Special gift moves | `GiveDratini` and any analogous post-gift rewrite | Extremespeed is assigned directly and does not pass through `LearnMove` |
| Contest Pokemon retained by player | Both `CheckPartyFullAfterContest` destinations | These copy/insert paths bypass normal party acquisition; successful retained Pokemon only |
| Successful normal learning | `LearnMove.learned` | Empty slot and confirmed replacement; level/evolution/TM/HM and tutors using this API; canceled/declined attempts do not count |
| Daycare retrieval | Successful `RetrieveBreedmon` completion after `FillMoves` | Register the final received moveset only; intermediate learned/overwritten moves do not count and need no `FillMoves` discovery context |
| Sketch use | Ordinary actual-use presentation | Discover Sketch when used; no additional hook for the replacement move, which can be discovered through later actual use |
| Egg moves | Actual `HatchEggs` completion | Confirmed policy is discovery at hatch, not unhatched egg creation/receipt |

`TryAddMonToParty` creates opponent parties too, and `GiveEgg` temporarily calls
it before converting the slot to an egg. `FillMoves` also creates enemy and
egg movesets. Blanket hooks in either would falsely discover unseen moves.
Use player-success/context-aware integration, not a hook in every move ID
conversion or generic data loader. Borrowed Transform/Mimic sets do not
automatically expose every copied move; an actual use still discovers it.

No additional egg policy is outstanding. Hatch discovery will be implemented
with the gameplay hooks, not in the persistence-only stage.

Multiplayer, infrared and mobile paths remain out of scope. Do include normal
wild/trainer/Tower/scripted/tutorial move presentations where actually visible.
No SRAM writes or bitmap work should be placed inside animation steps, OAM
updates, VBlank, sampled-cry refill or audio interrupts.

## Cost And Runtime Assessment

These are planning allowances, not linked results for a built discovery ROM.
The accepted visual owner already exists and its cost is not charged again.

| Addition | Allowance / effect |
| --- | --- |
| Flag helpers, UI lookup and reset integration | Approximately 0.4-0.8 KiB ROMX |
| Event hooks and context wrappers | Approximately 0.4-1.0 KiB ROMX |
| Extension validate/load/write/repair and CRC | Approximately 1-2 KiB ROMX |
| Legacy owned-moves bootstrap | Approximately 0.8-2 KiB ROMX |
| Total incremental ROMX | Budget approximately **3-6 KiB** |
| Persistent WRAMX | **64 bytes**, with a planning ceiling of **68 bytes** including small lifecycle/context state |
| Reserved SRAM consumed | **144 bytes across two copies**, no section/file-size increase |
| Additional ROM0 / WRAM0 / HRAM | Target **zero** |
| Additional VRAM / OAM / artwork / ordering tables | **Zero** |

The current prototype has 714,947 free ROMX bytes and 4,728 free WRAMX bytes
overall. A 64-byte bitmap leaves 4,664 WRAMX bytes free; the 68-byte ceiling
leaves 4,660. ROMX placement and exact costs must be reported after linking.

Discovery is constant-time per actually used/learned move. Ownership handles
four moves at acquisition, not an all-species lookup. The current linked
`GetMoveIndexFromID` measured 256-412 SM83 T-cycles across all 256 byte inputs
in the isolated CPU fixture: approximately 0.061-0.098 ms at normal speed,
or 0.031-0.049 ms at double speed. This is only the existing conversion call;
it excludes the new setter, interrupts and any display/cry contention. It
establishes that resolving a byte ID is not a search through 333 records.

Expect well below one display interval for an ordinary flag update and the
eight visible checks plus selected-entry check. Do not promise unchanged
scanout counts until native phase testing confirms them. No animation speed
change is intended. Saving adds two small copy/CRC operations; measure the
actual added duration rather than assuming it is zero. Legacy/recovery load
time scales with occupied move slots, not species count. Avoid that scan on
routine new-format loads and keep interrupts enabled during longer work.

Appending moves through index 512 needs no manually maintained seen index.
Name/type/description changes do not alter saved identity. Reordering or
reusing permanent indices requires an explicit migration. A later 128-byte
bitmap plus the same eight-byte header fits the full 136-byte span per copy,
supporting 1,024 moves, but needs a format/capacity migration and larger live
WRAM; it is not automatically implemented by this first version.

## Alternatives And Risks

| Option | Tradeoff | Recommendation |
| --- | --- | --- |
| Dedicated 64-byte WRAM bitmap plus padded save extension | Small fixed RAM cost; explicit, isolated save integration; no existing offsets move | Recommended |
| Minimal 42-byte bitmap | Saves only 22 WRAM bytes and 44 reserved SRAM bytes; capacity is only 336 moves before resizing | Not worth the early migration pressure |
| Direct SRAM-only flags | Saves 64 WRAM bytes but adds SRAM access to gameplay and complicates unsaved progress, New Game and copy consistency | Reject for this feature |
| Insert flags into the existing main player payload | Existing bulk copy/checksum could save it automatically, but moves subsequent SRAM fields and forces a much wider migration | Reject while compatible padding is available |

Highest risks are backup repair ordering, stale flags after New Game, false
discovery from generic generation, missing special acquisition paths, incorrect
decoding of boxed extended move IDs, and bank/register damage in live battle.
Ordinary bit lookup and the accepted renderer are low risk. Save integration
has the largest blast radius; a small byte count does not make it low risk.

## Implementation And Qualification Gates

1. Core bitmap and save extension: isolated flag tests, format/CRC checks,
   cold-load/save/reload and primary/backup fault recovery before gameplay hooks.
2. Acquisition and learning: add explicit source coverage, migration walkers,
   New Game/overwrite behavior and negative acquisition tests.
3. Battle discovery and live UI: actual-use, charge/preparation/called-move
   hooks, then all-seen/all-unseen/mixed screen oracles and timing comparisons.
4. Fresh full regression and manual review: publish a separate ROM with a
   genuinely partially discovered save, plus pre/post-migration review files.
   Preserve the accepted visual-only cartridge as the A/B reference.

### Exhaustive Helper And Storage Tests

- Every current permanent index independently, all byte/word boundaries,
  duplicate sets, arbitrary initial bitmap patterns and invalid/sentinel IDs.
  Verify that only the intended bit changes and reads/sets restore banks and
  registers. Include legitimate indices 255, 256, 257, 333 and capacity edges.
- Reassign/reuse transient IDs and force conversion-table collection while
  holding the permanent bitmap constant; discovery meaning must not change.
- Freeze all pre-existing SRAM labels, WRAM tables and checksum boundaries.
  New serialization may touch only the allowed padding and existing normal
  save-write ranges. Compare player/Pokemon/box/mail/RTC data independently.
- Legacy padding filled with zero, `$ff`, random bytes and header-like garbage;
  known/unknown versions and capacity values; every extension bit/header-byte
  corruption; invalid selected extension must not invalidate a valid main game.
- Valid primary only, valid backup only, both valid but different, each damaged
  extension, both damaged, foreign-playthrough copies and parent mismatch.
  Reproduce the immediate load-time mirror repair, not just manual saving.
- Interrupted saves at every extension write/commit boundary for both copies,
  and representative surrounding main-data/checksum/repair boundaries. Capture
  native write ordering, construct private interrupted batteries, then reboot
  the real runner. Never accept a partially written record as discoveries.
- New Game after Continue, save refusal, approved overwrite, deletion,
  soft reset and save/reload. Old on-disk games must survive canceled overwrite;
  old discoveries must never leak into the new live playthrough.

### Gameplay Discovery Tests

- Successful/failed moves, immunity, misses, multi-hit/rampage, charge turn,
  charge cancellation, Focus Punch prep/lost focus, Bide, Struggle and both
  combatants. Sleep/freeze/flinch/paralysis/obedience cancellation must not mark
  a move merely selected, unless its visible preparation already qualified.
- Metronome, Sleep Talk and Mirror Move: exact caller/callee bits and no
  rejected candidate leakage. Transform/Mimic/Sketch, including captured
  transformed Pokemon and temporary moves. Sketch use must mark Sketch;
  its replacement alone must not newly mark the replacement move.
- Starter, ordinary/special gifts, NPC trade, successful catch into party and
  full-party box destination, failed/full acquisition, retained/rejected
  contest captures, hatch variants and daycare move catch-up. Opponent team
  generation, tutorial temporary parties and unhatched egg creation must not
  count as ownership under the recommended policy.
- Successful empty-slot/replacement level, evolution, TM/HM and tutor learning;
  decline/cancel/already-known behavior; deleting/forgetting/releasing moves
  must not clear history. Verify PP, move slot, item/money and party data too.
- Daycare retrieval with multiple catch-up levels: only final received moves
  are newly marked. Intermediate auto-overwritten moves remain unchanged;
  failed retrieval into a full party must not register ownership.
- Bootstrap empty/full/sparse boxes, all fourteen active-box selections,
  daycare occupancy, NPC-trade ownership, eggs, duplicates and packed extended
  indices. Verify box selection, PP-Up fields, checksums and Pokemon bytes are
  unchanged by the scanner itself.

### Surrounding Regression And Timing

Rerun the complete current Dex suite on the final linked cartridge, including
both species presentations, all Selected tabs, Area, Search, Modes/Unown and
the accepted Moves popup/paging/partial-edge coverage. Exercise zero, one,
sparse and all seen moves in both orders; no panel or icon may expose an
unseen entry. Persistent flags must survive all owner-scratch reuse.

Run the existing 100-move/both-side battle suite, custom battle menu, switching,
Stats return and capture/New Entry cases. Recheck sampled cries and synth audio
across battle, Stats, new registration and Dex, with normal battle/double world
clock assertions. Also qualify Pack, TM/HM Case, Apricorn Box, PC/daycare,
shopping/item teaching, evolution, normal overworld/trainer/wild play, automatic
Hall of Fame saving and box/PC save entry points. Multiplayer stays excluded.

Compare input-to-first-change and completion for browsing/paging/sorting,
baseline versus discovery ROM, at multiple input phases and discovery levels.
Measure new-format load/save separately from legacy bootstrap and damaged-copy
recovery, using empty, realistic and full PC fixtures. Read-only observers can
inspect flags, banks and write ranges; actual gameplay events should use normal
inputs. Offline fault fixtures must be private copies, not live saves.

Use at most six native workers and eight compilation jobs under the current
80% headroom constraint. This assessment does not claim that the new discovery
suite has passed: the persistence implementation has not been built yet.
