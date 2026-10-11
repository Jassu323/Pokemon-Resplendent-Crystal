# Moves Dex Mode Visual Prototype

Started 2026-10-06; qualification and popup alignment updated 2026-10-07. Private visual
prototype based on the accepted Search and Sort
candidate at `build/dex-search-results-20261006d`, following the
[Moves Mode assessment](pokedex_moves_mode_scope.md). This is the move
encyclopedia, not the Selected Pokemon learnset tab. Production is unchanged.

The eight-row listing, compact colored type badge, Physical/Special/Status
icon, Pow/Acc/Eff panel and six-line description area are implemented using
existing artwork and the native font. Two generated orders cover all 333
moves. Discovery hooks, persistent seen flags, save migration and SRAM changes
remain deferred until visual acceptance.

The user accepted the `20261007b` popup alignment for retention on October 7.
It remains a private prototype. The subsequent
[discovery/save assessment](pokedex_move_discovery_scope.md) scopes persistent
seen flags without modifying that accepted visual baseline.

Before the persistence-only trial, the accepted `20261007b` ROM, save, symbols,
map, qualification metadata and complete candidate checkout were frozen at
`build/dex-moves-safe-rollback-20261007`. Its `rollback.json` records SHA-256
checks for every retained artifact. See the
[persistence prototype](pokedex_move_persistence_prototype.md) for the next
private owner; this visual baseline remains unchanged and recoverable.

## Manual Review

Main ROM and matching save:

- `build/dex-moves-mode-20261007b/pokecrystal-dex-moves-mode.gbc`
- `build/dex-moves-mode-20261007b/pokecrystal-dex-moves-mode.sav`

Unknown-entry visual fixture:

- `build/dex-moves-mode-unknown-20261007b/pokecrystal-dex-moves-mode-unknown.gbc`
- `build/dex-moves-mode-unknown-20261007b/pokecrystal-dex-moves-mode-unknown.sav`

Use SELECT from either species Listing, choose Moves Dex Mode, then press A.
Up/Down browse the list and wrap at both ends. Left/Right shift the visible
list by eight entries, retaining the cursor row and clamping to the first/last
complete viewport, like Legacy paging. Details update with selection;
no second A press is required. START opens a Type/Alphabet sort popup, A
confirms and B/START cancels. A changed order resets to its first entry;
confirming the current order preserves the selection. B/SELECT returns to
Modes with Moves Dex Mode highlighted. The previous species presentation,
sort and selection are retained. Moves Mode begins in Type order on each
entry; its own preferences are not saved yet.

The main ROM treats every move as seen. The second ROM uses a static,
read-only ROM fixture with 67 unknown moves and 266 known moves, retaining
the same 333 slots in both orders. Unknown names are `-----`, with type,
category, stats and description all blank. These are deliberate review
fixtures, not acquired or battle-based discovery. The supplied save is a
byte-identical copy of the accepted Search review save; installed saves and
the production cartridge are not modified.

Native screenshots are under `moves-mode-qualification/` in each build.
`double-edge-0.png` demonstrates the sidebar and existing short description;
`interface-0-0/sort-popup.png` shows the sort popup. The mixed build's
`interface-0-0/selected-second-entry.png` shows a selected unknown entry.

### October 7 Visual Follow-Up

The sort popup previously used the main screen's border tiles, whose outside
pixels include the orange background. It now uses the existing user-authored
`pokedex_popover_sheet.png` tiles in the same inactive Info atlas cells as the
species Listing popup. No replacement artwork or new font is generated.
Those eight tiles are prepared on Moves entry, before reveal; opening the
popup only changes the staged map and its edge attributes.

The follow-up adds 180 ROMX bytes over the initial visual prototype. It
temporarily stages 128 border bytes at offset 48 in the existing Info graphics
workspace and reuses another 128 VRAM bytes in the inactive Info atlas.
The 34-byte active Moves state, six OAM entries, SRAM and physical RAM layouts
are unchanged. Page jumps use the same atomic publication as single-row
navigation, updating the full panel together with the list.

## Data And Presentation

Type order is Bug, Dark, Dragon, Electric, Fairy, Fighting, Fire, Flying,
Ghost, Grass, Ground, Ice, Normal, Poison, Psychic, Rock, Steel, Water, with
alphabetical move names within each type. Alphabet order uses the displayed
name across all types. Both ignore spaces/punctuation and case for comparison,
with the permanent move index as a tie-break. Sorting never filters unknown
moves or mutates the species ordering array.

Move names reuse `PokedexMovesNamePointers`; stats and descriptions use the
permanent-index indirect tables. Pow below two, always-hit Acc and zero Eff
use `---`, consistent with the scoped battle-panel conventions. Eff is the
secondary-effect chance. Category is type-based under the existing TM/HM
rules, with the current low-power Status convention; this does not introduce
a physical/special split. Several custom moves still have placeholder stats
or descriptions in their actual data, which are displayed as-is.

Description line breaks advance one tile row, not the general printer's
two-row spacing. The writer is bounded to six rows of nineteen cells. Existing
descriptions fit without truncation; longer future descriptions remain a
separate data task because the current strings also serve smaller menus.

The generator verifies complete permanent-index coverage and legal types.
Names, type changes and appended moves regenerate both orders automatically.
The shared learnset/name-pointer generator's former final-`LEEK_SLAP` check
was replaced with complete move-index coverage, removing that manual growth
dependency. No generated image, replacement font or new artwork is added.

## Publication And Resources (20261007a)

Scrolling prepares the next badge in an inactive tile buffer, retains the
old displayed OAM, stages the complete tile/attribute maps, then publishes
the maps, OAM and palettes together in the protected VBlank interval. The
LCD stays on. Existing owner transitions mask entry/exit and reveal only the
complete destination.

The initial frame audit caught icons being revealed one display interval
before the background on entry. Publishing the BG palette in the same
transaction as the OBJ palettes corrected that prototype defect; the
correction is included in both review ROMs.

| Resource | Increment over accepted Search candidate |
| --- | ---: |
| ROMX, all-seen visual prototype | 3,023 bytes |
| Two generated orders including terminators | 1,336 bytes, included above |
| Renderer and owner integration beyond orders | 1,687 bytes, included above |
| Mixed fixture increment over all-seen ROM | 70 bytes, including a 42-byte ROM bitmap |
| New ROM0 / WRAM0 / WRAMX / HRAM / SRAM allocation | 0 bytes |
| Reused Info graphics scratch | 34 active bytes, plus 128 temporary border bytes at offset 48, in WRAMX bank 3 |
| Local shared VRAM ownership | 352 bytes: type/category tiles plus eight inactive Info atlas cells for the popup |
| OAM | Six entries, maximum four on one scanline; cursor is BG |

Full owner map buffers and WRAM0 staging scratch are reused. The Moves owner
has exclusive use of the Info scratch while active; this is not a persistent
seen bitmap. Physical RAM and SRAM layouts are byte-identical to the source
candidate, with 523 ROM0 bytes, 13 WRAM0 bytes, 4,728 WRAMX bytes and no HRAM
bytes free, unchanged. The all-seen link has 715,500 ROMX bytes free in the
same 186 banks. Persistent discovery costs from the scope are not spent yet.

The root cartridge captured before this task uses 2,317,924 ROMX bytes. The
review ROM's cumulative difference from that cartridge is 14,000 bytes:
10,977 bytes belong to earlier private Listing Options/Search work, and
3,023 bytes are this Moves Mode feature. Comparing only the new owner with
the previous accepted review candidate avoids attributing earlier work to it.

## Full Qualification (20261007a)

Native observers use normal button inputs, exact-link private checkpoints
and separate save fixtures. Testing is capped at six native workers and
eight compilation jobs. Each follow-up cartridge has newly prepared,
exact-link checkpoints and its own private save fixtures.

The new owner passes 672 sweep/navigation cases and 1,348 page-jump cases per
ROM: every move in both orders, wraparound, changed-sort reset, special
stat/description handling, all eight cursor rows, held Left/Right, final-page
clamping and crossings beyond ordinal 255. The host CPU fixture independently
checks both page directions at every possible scroll offset.
Each ROM also passes sixteen interface cases across both species Listings,
locked/unlocked Unown menus and eight subframe input phases, with 544 content
and control checks and 176 frame-captured transitions. These include entry
after Info/Moves/Area, same-sort confirmation away from the top, rapid/held
scrolling, full-page jumps, Search after Moves Mode, and Selected tabs after
returning, including Info to Moves Mode to Info with independent glyph/type
graphics oracles. The popup audits verify its exact existing border graphics, tile
identities, VRAM-bank attributes, labels and cursor at opening/reopening.
All captured scrolling/modal frames are wholly old or wholly new; owner
transitions may also use the existing black mask. No mixed frame, white flash,
LCD-off interval or reverted reveal remains in those captures.

Both Modern and Legacy pass the 6,555-case Selected/listing regression:
373 cold selections, 373 warm selections, 373 internal-paging cases, 1,492
Info cases, 746 learnset Moves cases, 2,238 Area cases, 400 Info stress cases
and 560 learnset Moves stress cases per presentation. The existing animation
and sampled-cry assertions require the accepted double-speed behavior.

The host suite passes 40 tests, including linked word orders above index 255,
automatic move/type/name changes, six full description rows, clipping bounds,
existing artwork and unchanged save/memory layouts. An outdated existing
learnset-workspace test was corrected to distinguish its 45-byte payload from
the two already-present Info scheduling bytes; no RAM change was made.

The final total is **24,028 native cases and 40 host tests, all passing**.
Native case counts include the interface scenarios once, rather than counting
their individual assertions or captured frames as separate cases.

| Native qualification | Cases | Failures |
| --- | ---: | ---: |
| New Moves owner, both fixtures including interface cases and page jumps | 4,072 | 0 |
| Modern and Legacy Selected/listing suites | 13,110 | 0 |
| Existing Modes menu | 54 | 0 |
| Species sorting, all entries/orders | 2,238 | 0 |
| Sparse/empty Listing edge cases | 26 | 0 |
| Shared integration, popup controls and visual publication | 402 | 0 |
| Cross-order cache tests, warm/cold and eight phases | 3,456 | 0 |
| Search content, defaults, return, Results, badges and stress | 654 | 0 |
| Existing Modes/Unown frame transitions | 16 | 0 |

The new owner and existing Modes/Unown frame suites capture 448 transitions
without mixed frames, white flashes, LCD-off intervals or reverted reveals.
The Results suite covers every species, and its three variants audit 4,074
scroll selections and 47,252 visible scanouts; Search control stress adds
14,856 icon scanouts. No new animation/cry miss was identified.

Full native evidence is retained in each build's qualification directories
and the main build's `regression-modern/` and `regression-legacy/`.
`final-qualification.json` consolidates the final counts and host result.
Production ROM/symbol/map hashes were checked unchanged after qualification;
neither installed SameBoy games nor saves were modified.

| Review file | SHA-256 |
| --- | --- |
| Main ROM | `46eabee8402e2cb8e96c7b4a0dd38784d41790d5efbaf527a6d6b0513d8a3112` |
| Mixed ROM | `7b5fda8f40b3bf6e49997b93a52c797eaf897d844a8e0572738e1ca02cd44673` |
| Both supplied saves | `7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce` |

## Visual Latency Baseline (20261007a)

The all-seen fixture's sixteen captured cases include Modern/Legacy and eight
input phases. These are initial renderer measurements, not a performance
optimization comparison. One physical display interval is about 16.743 ms.
"Scanout" counts the first post-input display as number one; elapsed intervals
are fractional because input can start between display boundaries.

| Action | First visual response, elapsed intervals / ms | Complete destination, elapsed intervals / ms | First / complete scanout |
| --- | --- | --- | --- |
| Modes to Moves | 2.01-2.85 / 33.7-47.7 | 6.01-6.85 / 100.7-114.7 | 3 / 7 |
| Down one move | 3.05-3.93 / 51.1-65.7 | Same | 4 / 4 |
| Left/Right one page | 3.05-3.93 / 51.1-65.7 | Same | 4 / 4 |
| Open sort popup | 2.05-2.98 / 34.4-49.9 | Same | 3 / 3 |
| Change sort | 3.05-3.93 / 51.1-65.7 | Same | 4 / 4 |
| Moves to Modes | 2.05-2.92 / 34.3-49.0 | 12.18-13.80 / 203.9-231.1 | 3 / 13-14 |

Entry/exit first response is the existing black owner mask; completion is the
intact destination. Scrolling and sorting retain the old contents until the
complete new contents appear, so first response and completion coincide.
These timings do not establish discovery/save-hook costs. Modes return still
uses the existing menu renderer rather than a new optimized handoff.
The October 7 border/paging follow-up retains the initial build's first and
complete scanout counts for the shared actions; small fractional differences
reflect changed execution phases, not an extra visible delay.

## Three-Pixel Popup Alignment (20261007b)

The entire Moves sort popup, including its native-font labels and cursor, is
shifted exactly three pixels left. Its opaque bounds change from
`[51,24,155,64)` to `[48,24,152,64)`, retaining the 104-by-40-pixel size.
SCX stays at five; the main page does not move. The implementation horizontally
mirrors pieces from the existing user-authored modern popup sheet and shifts
the native glyphs at runtime. No graphical asset or replacement font is added.

The rightmost partial tile preserves the three newly exposed pixels of the
underlying move name, rather than painting that strip gray. Native checks
cover opening and cancelling at all 333 positions in both orders, including
long names, extended move IDs and unknown-entry names. Opening, changing the
highlight, confirming and cancelling still use atomic map publication.

This follow-up costs **553 additional ROMX bytes**, making the new Moves
owner's increment over the accepted Search candidate 3,576 bytes. The all-seen
link uses 2,332,477 ROMX bytes, leaving 714,947 free in the same 186 banks.
The mixed fixture remains another 70 bytes. Physical RAM, SRAM and ROM0
allocations are unchanged. Active state now uses 48 bytes of existing Info
scratch; temporary preparation uses up to 336 bytes at offset 48. A 1,024-byte
native-font copy occupies the existing, mutually exclusive listing-popup /
Battle Tower workspace at bank 3 `$dc00-$dfff`. Shared VRAM ownership is
720 bytes: the unchanged 224 type/category bytes plus 31 inactive Info atlas
cells for the popup. OAM usage remains six entries.

Both updated cartridges pass 1,338 navigation/modal sweep cases, 1,348
page-jump cases and sixteen interface cases each: **5,404 native cases** for
the new owner. The interface cases include 1,088 content/control checks and
352 captured transitions across both species presentations and eight input
phases. Full-screen pixel comparisons against the previous cartridges pass
all 32 captures: the previous popup translated left three pixels is exactly
the new screen, with zero changes elsewhere. The host suite passes 42 tests,
including all native font glyphs and exhaustive partial-edge composition.

The previous section's 24,028-case full regression is retained as the
`20261007a` baseline, not claimed as newly rerun for this visual adjustment.
The new revision also reruns the relevant shared Modes, listing-popup,
Search integration and Modes/Unown transition checks: 54, 144, 66 and sixteen
cases respectively. The updated revision's total is **5,684 native cases and
42 host tests, all passing**, plus the 32 exact full-screen pixel comparisons.
Its 448 captured transitions contain no mixed frames, white flashes, LCD-off
intervals or reverted reveals. Production ROM/symbol/map hashes and both
supplied save hashes remain unchanged. Evidence is in each
new build's `moves-mode-qualification/`, with exact pixel results in
`alignment.json` and consolidated results in the main build's
`alignment-qualification.json`.

Popup opening/highlighting stays at scanout 3; changing/cancelling sort,
single-row navigation and page jumps stay at scanout 4. Return to Modes is
unchanged at first scanout 3 and completion 13-14. Preparing the shifted
font on entry adds one display interval: the initial black owner mask still
appears at scanout 3, while the complete Moves page now appears at scanout 8
instead of 7. Completion is 7.01-7.85 elapsed intervals, or 117.4-131.5 ms,
across the tested input phases. This is an approximately 16.7 ms one-time
entry cost, not extra latency on each popup opening.

| Updated review file | SHA-256 |
| --- | --- |
| Main ROM | `56b5b5947ba012a6981b5e1b6ae58aabe7e2ceab524da31c7da50e92f104bd2c` |
| Mixed ROM | `bf25dc66460dcbd0810d7ae34e77648333f4e701b3ccd7526abbf0096f5375c2` |
| Both supplied saves | `7ed4610e4812ed5eb6659a603e053914850d05e8dd5738c63610c4a69150a9ce` |

## Reproduction

Build a fresh private candidate from the retained Search prototype:

```sh
PYTHONPATH=tools python3 -B tools/build_dex_moves_mode_prototype.py \
  --source build/dex-search-results-20261006d \
  --output build/NEW-MOVES-MODE --jobs 8 --prepare
PYTHONPATH=tools python3 -B -m dex_timing.moves_mode \
  --output build/NEW-MOVES-MODE --jobs 6
PYTHONPATH=tools python3 -B -m dex_timing.dex_modes \
  --output build/NEW-MOVES-MODE --jobs 6
```

Use another fresh output and `--unknown` for the static unknown-entry fixture.
`--relink --prepare` regenerates linked checkpoints after renderer changes.
The builder verifies that root production ROM/symbol/map hashes do not change.
Tracked prototype sources are `tools/dex_timing/probes/pokedex_moves_mode.asm`,
`tools/pokedex_moves_mode_assets.py` and
`tools/build_dex_moves_mode_prototype.py`. Runtime integration is private to
the candidate; `main.asm`, the root Dex engine and the SRAM layout are not
changed.
