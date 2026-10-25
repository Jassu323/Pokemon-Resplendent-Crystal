# Moves Dex Mode Scope

2026-10-06. Assessment against `ccb0299d6` (Dex Search and Sort) and the user's
160x144 Moves Mode mockup. This is a separate move encyclopedia, not the
Selected Pokemon Moves tab that lists learnsets. Runtime and save changes are
not implemented by this scope.

The later [visual prototype](pokedex_moves_mode_prototype.md) implements the
screen and sort controls privately. Discovery and SRAM work below remain
unimplemented; its exact visual-only costs are recorded separately.

The later [discovery/save assessment](pokedex_move_discovery_scope.md) refines
the storage header, event hooks, packed-box migration and primary/backup
qualification against the accepted `20261007b` visual baseline.

The layout is feasible with existing artwork. Its renderer is simpler than
the species Listings because it has no portrait, minisprites, cry or animation
producer. Discovery tracking and backward-compatible save handling are the
larger engineering tasks. Recommended direction: a dedicated screen owner,
two generated ROM orders, permanent-index discovery flags, and a separately
validated save extension that leaves existing save offsets unchanged.

## Layout And Artwork

The mockup divides the top into a narrow information sidebar and a move list,
with one full-width description panel below them. The footer retains the
existing SELECT MODE and START OPTION artwork.

| Component | Mockup geometry | Proposed implementation |
| --- | --- | --- |
| Information sidebar | Outer white edges near x1 and x36, y5-75 | Existing Dex border cells, compact type badge, category icon, stacked Pow/Acc/Eff labels and three-digit values |
| Move list | Outer edges near x38 and x159, y5-75; names begin near x59 | Eight 8px-spaced rows, starting at y8; existing small arrow cursor |
| Description | Full-width panel below y77 | Six consecutive 8px-spaced text rows, about 19 character cells per row |
| Footer | Existing bottom hint band | Existing assets; START can expose the two move sorts |

Seven entries are drawn in the sample, including the unknown placeholder. The
panel has room for an eighth row at y64. All 333 current displayed move names
are at most 12 characters, so they fit the right-hand list without truncation.

An all-BG layout avoids the Window/BG split needed by the species portrait.
With the existing Dex SCX=5, placing the existing narrow divider at BG column
5 produces the two white edges near x36/x38, and names at column 8 begin near
x59. Recompose existing border tiles rather than stretching the old frontpic
layout. Confirm the description inset and right edge in a native capture;
they should not justify a new shifted alphabet or a baked text sheet.

Reuse the compact type graphics and palettes, the Physical/Special/Status
icons already used by the TM/HM Case, the normal font, and the smaller arrow.
No new user artwork is currently identified as necessary. If native rendering
exposes a missing junction tile, request that tile rather than generating it.

OAM is a suitable owner for the type/category icons: four 8x8 entries for the
type badge and two for the category. A one-entry cursor brings the total to
seven; a BG cursor avoids that seventh entry. This is well below the forty
entry total, and the sidebar arrangement does not threaten the ten-entry
scanline limit. Six category tiles can be resident, with four type tiles
replaced on selection: ten 2bpp tiles, 160 bytes of local VRAM. Their ROM
graphics already exist and do not need duplicating.

For unseen rows, show `-----`. Recommended behavior is to blank the selected
row's type/category/stats/description too, rather than reveal the move through
its information panel. Retain every move slot in both orders; discovery
changes the displayed entry, not the ordering table.

## Ordering And Data Access

The current game has 333 real moves, with permanent indices 1 through 333.
Generate two word-index tables from the authoritative constants, names and
move records:

1. Alphabetical type order: Bug, Dark, Dragon, Electric, Fairy, Fighting,
   Fire, Flying, Ghost, Grass, Ground, Ice, Normal, Poison, Psychic, Rock,
   Steel, Water; then alphabetical move names within each type.
2. Alphabetical move names across all types.

Use case-insensitive displayed names with a documented punctuation convention
and permanent index as a final tie-break. Validate complete coverage,
uniqueness, name width, legal types and monotonic ordering during the build.

Two orders with one word terminator each cost exactly **1,336 ROMX bytes** at
333 moves. Optional boundaries for eighteen type groups cost another 38 bytes
(nineteen word offsets); they are unnecessary unless type-group jumping or
headers are added. Switching sorts selects a different ROM pointer, with no
runtime comparison sort or eligibility-record table. Reset to the first row
on a changed sort, consistent with the accepted species sorting behavior.

Read these orders directly from ROM. The Moves owner does not compact or
filter them, so it does not need to overwrite `wPokedexOrder` or allocate
another move-sized WRAM array. This also preserves the species list while
using Moves Mode and avoids a buffer-capacity issue as moves are added.

The Selected Pokemon Moves tab already generates `PokedexMovesNamePointers`.
Reuse that permanent-index name lookup. Resolve `Moves` and `MoveDescriptions`
through the existing indirect-table primitives using the permanent word
index. Do not allocate transient move IDs merely to browse the encyclopedia,
and do not invoke the TM/HM menu's selected-machine loader as a generic move
renderer.

Changes to names, types or newly appended moves automatically regenerate the
orders. No manually maintained sorting index is required. One existing
generator check names `LEEK_SLAP` as the final move; generalize that cardinality
check to the declared move count as part of this work, so adding moves cannot
silently leave the shared name-pointer output behind. Gameplay learnsets do
not affect either sort.

## Stat Semantics

Use the static move record, with the formatting already established in battle
and the TM/HM Case:

- Pow is base power; the existing small/variable-power convention shows `---`
  when the stored value is below two.
- Acc is the stored accuracy converted with the existing percentage formatter.
  Use the battle panel's `---` convention for always-hit effects. The current
  TM/HM Case does not apply that explicit always-hit override, so avoid
  inheriting that discrepancy into the new screen.
- Eff is the secondary-effect chance, not type effectiveness or recoil.
  A zero chance displays `---`.
- Category follows the current TM/HM rules: status for the existing low-power
  convention, otherwise Physical/Special according to type. This feature does
  not introduce a per-move physical/special split.

The example Double-Edge has power 120, accuracy 100 and secondary-effect chance
zero in the current data. Its Eff value would therefore be `---`, not the
mockup's 30. Dynamic battle calculations, enemy matchups and Hidden Power
variations should not alter this static encyclopedia panel.

## Six Line Descriptions

Current descriptions use the general text printer's `line` convention, which
advances two tile rows. The new panel needs a bounded compact renderer that
advances one tile row and handles the supported text tokens without crossing
the 19-cell/six-row rectangle. Clear the entire panel on selection, including
when moving from a long description to a short or unseen entry. Validate text
width and row count at build time instead of silently truncating future text.

Current short descriptions can be rendered compactly without copying them
into another ROM text set. For later extended descriptions, recommend a
Dex-specific override table with fallback to the current short strings.
Those strings are shared by party/TM/HM interfaces: expanding them to six
lines directly would overflow existing smaller windows unless all their
consumers were also redesigned. A fallback keeps that unrelated work out of
this feature.

A full bank/address override table would cost about **999 bytes** for 333
moves. Add it when extended descriptions are introduced, or generate only
the supported overrides with a validated lookup. If every move eventually
uses all 114 visible character cells, plus five line separators and a
terminator, plain one-byte text is about **39 KiB** before pointer metadata.
That future text is separate from the initial renderer estimate.

## Move Discovery

Use one permanent-index bit per move. The current minimum is **42 bytes**;
recommend **64 bytes** initially, providing capacity for 512 moves. This is
not a permanent game limit: a larger bitmap can be introduced with a versioned
extension when needed.

Party and battle structures store transient byte IDs. Convert through
`GetMoveIndexFromID` before setting a bit. Keying the bitmap by those byte IDs
would corrupt discovery meaning after conversion-table reuse, and would not
represent all moves above index 255. Reject null/sentinel/synthetic animation
values without excluding legitimate permanent move indices.

Discovery should be monotonic during one playthrough and should have these
sources:

- An actual move announced/performed by either combatant, including misses,
  immunity or a subsequent effect failure. Merely selecting a move, loading
  AI data, or being unable to act does not discover it.
- Called moves from Metronome/Sleep Talk/Mirror Move and similar effects,
  alongside the calling move when it is actually used.
- A charging move on its initial visible charge, not only its second turn.
- All known moves when a Pokemon is successfully acquired: starters, gifts,
  catches into party or directly into a box, NPC trades and contest rewards.
- A successfully learned level/TM/HM/tutor move, including an empty-slot learn
  and a confirmed replacement. Declining a move does not discover it.
- Egg moves on hatching, confirmed by the user on October 7. Unhatched egg
  creation/receipt does not discover moves.

Candidate battle hooks include `BattleCommand_UsedMoveText` and the accepted
initial-charge path in `BattleCommand_Charge`. No single generic data-loading
hook is sufficient. `TryAddMonToParty` is also used to create opponent parties,
so ownership checks and successful final acquisition points are essential.
Do not discover every move in an opponent's generated moveset before it is
used. Do not clear bits when a Pokemon is released or forgets a move.

Set bits in WRAM during play; write them with the normal save transaction.
There is no reason to add SRAM writes, animation-frame work or sampled-cry
interrupt work to move playback. Multiplayer hooks remain out of scope.

## Save Compatibility And RAM

Both primary and backup saves contain **136 bytes of reserved padding** after
their current checksummed payload and before their existing checksum fields.
The source save routines reference the payload ends and do not treat these
padded spans as part of the old checksum. This provides a promising extension
location without moving existing save fields, Pokemon data or conversion
tables.

Recommended allocation per copy: 64 bitmap bytes plus an eight-byte header
for a signature, version/capacity and extension checksum. That is **72 bytes
per copy, 144 bytes total**, carved from the existing 272 padded bytes. It
does not enlarge the cartridge SRAM allocation or save file. It still consumes
reserved space and must be included in the resource accounting.

Treat the extension independently from the old checksum. Old saves without a
valid marker remain valid; initialize their move flags and seed currently
owned party, PC and daycare moves using the loaded conversion tables. Past
enemy moves that are no longer represented by an owned Pokemon cannot be
reconstructed. Preserve active-box semantics during that scan, and write the
new extension on the next ordinary save.

Primary/backup selection and repair need explicit integration. `TryLoadSaveFile`
currently repairs the other save copy immediately after a successful load;
validate/select the matching move extension before that mirror is refreshed.
New Game, erased saves, absent extensions and corrupted extensions must not
inherit flags from a previous playthrough. A bad extension alone should not
make otherwise valid Pokemon/player data unusable.

Reserve a non-unioned **64-byte WRAMX block** for live flags. The current map
has 2,816 free contiguous bytes at bank 2 `$d500-$dfff`, beyond the conversion
tables. This is a suitable candidate; do not borrow the Dex/Battle Tower owner
scratch for data that must survive battles and every menu. Bank restoration
and initialization remain part of qualification. UI cursor, scroll, sort and
staging fields can reuse the Dex owner scratch; budget approximately 16-32
bytes there, not an additional persistent screen-sized allocation.

WRAM0 has only 13 free bytes, and HRAM is full. Target no new permanent
allocation in either. ROM0 has 523 free bytes; the renderer, save helpers and
discovery helper should live in ROMX, using existing home primitives.

Stable move indices are a save-format contract. Appending a move is safe;
reordering existing permanent constants changes the meaning of already saved
bits and needs an explicit migration, regardless of whether the generated
orders are correct. The reserved spans can later accommodate a 128-byte
bitmap plus the same eight-byte header, supporting 1,024 moves without moving
existing save fields; live WRAM and the versioned checksum policy would grow
accordingly.

## Cost Complexity And Performance

| Area | Initial cost or allowance | Complexity and risk |
| --- | --- | --- |
| Two generated orders | 1,336 ROMX bytes; no full WRAM order buffer | Low; build validation and regeneration are important |
| Screen owner, bounded text/stat renderer, navigation and sort UI | Planning allowance roughly 4-7 KiB ROMX, including shell maps/control glue | Medium; coherent map/palette/OAM publication and returning to the correct mode |
| Discovery, save extension and old-save bootstrap | Planning allowance roughly 2-5 KiB ROMX | Medium-high; coverage of acquisition/called moves and primary/backup recovery |
| Initial overall ROMX allowance | Roughly 8-14 KiB including orders, excluding future expanded text | Estimate only; exact linked bytes require a prototype |
| Persistent WRAMX | 64 bytes, plus any separately approved persistent preferences | Small, but must not be unioned with scratch |
| UI scratch | Approximately 16-32 bytes reused from the inactive Dex owner | No new screen-sized allocation expected |
| SRAM | 144 reserved bytes consumed across both copies | No physical SRAM/save-size increase; migration and corruption testing required |
| New artwork | None currently required | Reuse user-supplied assets; request any proven missing tile |

The accepted Search/Results link (`build/dex-search-results-20261006d/`) reports
718,523 free ROMX bytes in allocated banks and 4,728 free WRAMX bytes overall.
The initial allowance is modest relative to ROMX
headroom; bank placement and exact linked totals are prototype results, not
claims that all spare bytes are interchangeable.

Sorting should be dominated by repainting eight rows and the selected move
panel, not by move count or Dex completion. Scrolling reads only the visible
rows and one selected record/description. Target a coherent update on the
next available display interval, with no portrait decompression, animation
warming or cry wait. Measure input-to-first-change and input-to-completion
separately in the prototype; those targets are not benchmark measurements.

Discovery is a bounded index conversion and bit set outside the animation
loop. It should not produce a perceptible animation/audio difference, but
instrumented regression is still required. Old-save seeding scans owned
Pokemon once and may have a measurable Continue-time cost; it is not work to
repeat on every Moves Mode entry.

## Implementation Sequence And Qualification

1. Generate and validate the two orders; implement the new Modes action as a
   dedicated owner. Do not set the existing Modern/Legacy boolean presentation
   to a third value: its nonzero paths mean Legacy throughout the current code.
2. Prototype the screen with controlled seen flags, existing short descriptions,
   wrapping navigation and the two sorts. Use the accepted hide/stage/reveal
   handoff and publish each selection's name, icons, stats and text coherently.
   Preserve the species Listing/order while Moves Mode owns the screen.
3. Add permanent discovery storage, normal save/load integration, old-save
   seeding and all successful acquisition/learning/battle hooks.
4. Qualify the exact private build before considering production promotion.

Explicit cases should include all 333 moves in both orders; every name and
description bound; zero/sparse/full discovery; first/last wrapping; rapid
scroll/sort/cancel; known-to-unknown and long-to-short panel clears; always-hit,
status, variable-power and secondary-effect values; and indices above 255.

Save tests should cover existing saves, new games, save/reload, soft reset,
conversion-table garbage collection, no-save reset, primary failure with backup
recovery, independent extension corruption and poisoned old padding. Include
all boxes and daycare in bootstrap fixtures, while checking that owned Pokemon,
box contents, items, options and conversion tables are unchanged.

Discovery tests should distinguish player/enemy execution from AI selection,
blocked actions and failed effects; cover initial charge, called moves,
successful/declined learning, direct-to-box catches, starters/gifts, NPC trades,
contest rewards and eggs under the chosen policy. Check that generating an
opponent or merely viewing its data does not reveal its unused moves.

Finally run the standard Dex/Selected/audio suites plus focused battle, party,
TM/HM, PC and acquisition regressions, with the standing reduced parallelism
limit. Preserve the double-speed world/normal-speed battle policy and animation
scripts. Native frame captures should confirm atomic selection updates and
clean mode-entry/return publication.

Follow-up decisions: unseen selections blank their entire panel in the
accepted visual prototype, and eggs discover their final moveset at hatch.
Moves Mode currently resets its own sort to Type on entry; additional
persisted preferences remain deferred and would require explicit memory
accounting. See the [persistence trial](pokedex_move_persistence_prototype.md)
for the separate approved storage stage.
