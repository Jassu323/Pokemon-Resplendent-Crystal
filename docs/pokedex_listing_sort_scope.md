# Listing Options And Sort Scope

2026-10-05. Initial feasibility and resource estimates for the Modern Listing
START popup. No popup, sorting-path change or ordering-data correction is
implemented by this investigation. The Modes page and its clean transitions
are accepted; Unown transition optimization is deferred as `DEX-PERF-04`.

The subsequent [private prototype](pokedex_listing_options_prototype.md) now
implements this direction and records exact linked costs, timing, qualification
and review files. The estimates below are historical scope, not final costs.

## Layout And Controls

START opens a small `Sort` / `Search` popup over the current Modern grid.
The portrait, name, Seen/Own totals, footer and uncovered grid remain visible.
Choosing Sort replaces that popup with `Evolves`, `Nat'l Dex`, `Alphabet`.
Choosing Search opens the existing full-screen Slowpoke/type Search screen.
The popup is a Listing-only owner; Selected Description/Info/Moves still do
not expose START or mode switching.

Recommended controls are Up/Down to select, A to confirm, B from Sort to return
to Options, and B/START from Options to close. Sort opens on the current saved
ordering choice. Applying the same choice simply closes it. Preserve the
selected permanent species index when changing order, not its old ordinal or
transient species ID. If Alphabet excludes an unseen highlighted species,
select its first valid result; an empty Dex remains safely empty.

These are proposed defaults, not yet implemented controls. The shared ordering
choice can also serve Legacy, but the supplied popup placement is Modern-only;
Legacy's popup placement should be reviewed separately before including it.

## Artwork And Tile Constraints

All four images were checked directly. The isolated popup images match the
mockups exactly when composited at the following canvas origins:

| Artwork | Canvas | Opaque rectangle | Mockup canvas origin |
| --- | --- | --- | --- |
| Dex Options | 72x40 | 60x29, local x6/y5 | x72/y56 |
| Dex Sort | 96x56 | 84x45, local x6/y5 | x64/y48 |

The canvases already have dimensions divisible by eight. Their opaque borders
do not: the Options rectangle is screen x78-137/y61-89, and Sort is
x70-153/y53-97. Both have two-pixel white borders, dark-gray fill and text rows
at 16px spacing. Alpha is binary transparent/opaque, not antialiasing.

A BG/Window tile does not provide PNG-style transparency. An exact partial
edge tile may need to retain the underlying colored icon pixels while adding
white/gray popup pixels; that mixture can exceed the four colors available to
one CGB BG tile. OAM is not a good whole-window substitute: the current Modern
grid already uses 26 entries, and a wide sprite border also faces the
ten-sprites-per-scanline limit.

Recommended first prototype: modestly adjust the boxes to opaque tile-aligned
rectangles, approximately 72x40 Options and 88x56 Sort, preserving 16px row
spacing and the surrounding live Listing. Final placement needs visual review;
these are not promises of pixel identity with the original transparent edges.
The existing font can render every label and the standard white triangle.
The longest Sort label occupies eight character cells; including the cursor
and two border columns requires eleven cells, or 88px.

Graphical assets:

- One reusable eight-tile border set: four corners and four straight edges,
  two-pixel white outline, opaque dark-gray remainder. This is 128 bytes at
  2bpp; opposing edges may optionally share flipped artwork.
- Reuse the existing dark-gray fill, font and triangle cursor. No baked text
  sheet, new minisprites, portrait graphics or whole-window bitmap is needed.
- A standalone `gfx/pokedex/dex_popup_border.png` is preferable to extending
  the core `pokedex.png` load and changing its established tile destinations.
  The sheet could be 32x16 or 64x8. Use opaque grayscale authoring colors:
  white `#ffffff` and the existing dark-gray slot `#555555`. BG palette 0 maps
  them to the existing UI white and RGB(5,5,5) dark gray, rendered as `#282828`.
- If exact off-tile borders become mandatory, prototype masked/composed edge
  tiles as a separate higher-complexity alternative. Do not flatten transparent
  margins to a color and assume the original grid will remain visible there.

## Publication And Ownership

Use the existing Window and BG palette 0, not a third screen-sized hardware
layer. Freeze Listing icon animation and navigation while the modal owns its
rectangle. Preserve the original rectangle's tile IDs/attributes and shadow
OAM, stage the new rectangle offscreen, mask intersecting grid/caught/cursor
sprite entries, then publish map and OAM changes together in the protected
Listing handoff. BG priority alone is insufficient to guarantee coverage of
all OBJ pixels, including color-zero UI pixels.

Cancel restores the saved rectangle/OAM without reloading the frontpic or
rebuilding/decompressing the grid. Resume the normal icon phase coherently.
Options-to-Sort replaces the modal rectangle while retaining the original
Listing backup. Idle animation warming must be stopped/cancelled before menu
scratch is borrowed, and restarted safely afterward; removing it globally is
the separate `DEX-PERF-03` story.

On a changed sort, keep the outgoing Listing/popup intact during preparation.
Build the incoming active order, relocate selection by permanent species index,
invalidate position-keyed grid tags and eligibility flags, and stage the new
grid/marks/cursor/scrollbar/name. Retain the portrait and its palette where the
same known species remains selected. Reveal a coherent new Listing, not a white
clear or incremental icon/palette repair. Search uses the accepted full-screen
hide/stage/reveal policy; its existing palette report still needs revalidation.

No portrait scheduler or sampled-cry retiming is needed. Post-popup entry must
nevertheless qualify cold/warm playback, because menu preparation can cancel
idle warming and borrow otherwise inactive owner scratch.

## Ordering Data And Future Species

The game already has two 373-word ROM tables: `NewPokedexOrder` and
`AlphabeticalPokedexOrder`. Each is 746 bytes. The old numerical path generates
1..N internal indices rather than consulting a third table. The current New
and Alphabet tables each include every species exactly once, but coverage does
not guarantee correct family/alphabetical placement.

The old numerical path is not a genuine National order for all additions.
Gallade (475) appears before Shroomish (285), Roserade (407) before Carvanha
(318), Dusknoir (477) before Absol (359), and Froslass (478) before Spheal (363).
Its direct-copy eligibility-mask assumption also relies on ordinal equaling
species index, so it cannot be retained unchanged with a National table.
The authored alphabetical list has clear inversions too, such as Absol before
Abra and Buneary before Banette. Do not simply expose those tables unchanged
and call their order correct.

Recommended data pipeline:

- Evolves: retain the current authored New-order backbone, independently
  editable without changing gameplay evolution requirements. Family corrections
  can be deferred; later rearranging that source and rebuilding updates the
  table without any sorting-engine change. Correcting gameplay evolution
  records alone does not reorder this authored list.
- Alphabet: generate the order from displayed species names at build time,
  with explicit punctuation/gender tie-break conventions and stable identities.
  Newly added or renamed species then participate automatically.
- National: generate a third 16-bit order table from explicit National-number
  metadata. Current constants document all 373 numbers, including the first
  251 implied sequentially; migrate this into validated metadata rather than
  relying indefinitely on free-form comments. New species need a National
  number, not a hand-inserted position in the output array.
- Validate range, uniqueness and complete species coverage for all three
  outputs, as well as alphabetical/numerical monotonicity. Missing family
  placement or National metadata must fail clearly instead of silently dropping
  a new species. Build dependencies must regenerate outputs after species,
  names, family-order or number-metadata changes.

Use a ROM selector plus the existing `wPokedexOrder` buffer. There is no runtime
comparison sort: copy/rebuild the active view in one bounded O(N) pass. The
buffer is also modified in place by Search to compact matching species, and
Alphabet compacts seen species only. Converting every consumer to read directly
from ROM would add ownership/refactoring risk for little copy-time savings.
Keep Evolves/National's unknown holes through the last seen entry and Alphabet's
seen-only behavior unless a separate visibility change is requested.

Family placement is semantic data, not something reliable code can infer from
missing evolution links. Fully automatic future family grouping would need a
complete evolution graph and/or explicit family overrides/order anchors.
That is optional later work, not a prerequisite for these popups. For this first
implementation, a new species requires a source family placement; generated
Alpha/National positions do not require manual output-index maintenance.

The three arrays occupy 2,238 ROMX bytes total at 373 species, only 746 bytes
more than the two existing arrays. Each future species adds six ROM bytes to
the three outputs and two bytes to the existing active WRAMX order buffer.
Existing species/save/UI/scratch limits still apply. In particular, the current
order eligibility mask has 67 bytes before its neighboring scratch allocation,
enough for 536 species; a larger expansion requires revisiting that allocation,
not merely increasing `NUM_POKEMON`.

## Native Timing Check

Private probe and raw traces: `build/dex-sort-scope-20261005/`. A fresh vanilla
checkout copy was built there; the source checkout, production ROM outputs and
installed saves were not changed. SameBoy observes real execution without
runtime memory patches. Private saves mark all species caught/seen.

Vanilla ROM SHA-256:
`d6702e353dcbe2d2c69183046c878ef13a0dae4006e8cdff521cca83dd1582fe`.
Accepted Modes baseline ROM SHA-256:
`d53736afb6a6098f6c5b0ed228c9e5ba5efbd9d1cb4e28f169c9fed60a55a34b`.

| Routine/route | ms | Physical display intervals |
| --- | ---: | ---: |
| Vanilla New order, boot preparation | 5.63 | 0.34 |
| Vanilla numerical order, selecting Old | 4.64 | 0.28 |
| Vanilla Alphabet order, selecting ABC | 135.00 | 8.06 |
| Vanilla Changing Modes message after numerical order | 2,152.64 | 128.57 |
| Vanilla Changing Modes message after Alphabet order | 2,141.55 | 127.91 |
| Vanilla Listing initialization after numerical order | 652.45 | 38.97 |
| Vanilla Listing initialization after Alphabet order | 652.52 | 38.97 |
| Vanilla button to Listing update-loop readiness, numerical | 2,879.24 | 171.97 |
| Vanilla button to Listing update-loop readiness, Alphabet | 2,996.53 | 178.98 |
| Current 373-species Evolves order, double speed | 39.32 | 2.35 |
| Current internal-index numerical order, double speed | 4.82 | 0.29 |
| Current 373-species Alphabet order, double speed | 24.89 | 1.49 |

These are narrow single-path measurements, not the future popup's latency
distribution. Current ordering costs were captured at Dex opening; full vanilla
route readiness is a code checkpoint, not a claimed first-intact-pixel metric.
Physical intervals use 70,224 reference cycles and 59.7275Hz, not CPU-frame counts.

Vanilla orders first, then calls `Pokedex_DisplayChangingModesMessage`, which
deliberately waits 64 frames, plays a sound, and waits another 64. Its several
seconds of latency are mostly that explicit delay and Listing reconstruction,
not an inherently slow sorting algorithm. The Pack sorts smaller pockets with
an early-exit comparison loop and a precomputed item-rank lookup, without this
two-second message. Precomputed Dex ordering is simpler still.

Do not retain the message, its blocking waits, or wholesale cold initialization
on popup cancellation. Tighten the current position-mask/seen-filter loops too:
avoid repeated general flag helpers, stack work and WRAM-bank changes where
direct local bit operations and a compact seen snapshot suffice. Optional
build-time `(seen-byte offset, bit mask)` records cost 746 bytes per order,
2,238 bytes for all three, if a measured prototype justifies them.

Target less than one display interval for order construction and one-to-two
intervals for popup publication/cancellation; these are engineering targets,
not measured guarantees. Changed-sort completion also includes a bounded grid
rebuild and must be measured separately from the first visible input response.

## Initial Cost And Risk

Estimates below require a linked prototype before acceptance:

| Resource/work | Initial estimate |
| --- | --- |
| New ROMX | Approximately 2.5-4.5 KiB for controller, transactions, tighter order loops, strings, 128-byte border and 746-byte National output; optional eligibility records add up to 2.19 KiB |
| ROM0 / WRAM0 / HRAM growth | Target zero; flag any unavoidable addition before implementation |
| Temporary WRAMX | About 0.5 KiB reused within inactive Info work storage: original/staged modal maps and up to 160 OAM bytes plus small state; no new aggregate allocation intended |
| VRAM | Eight borrowed Info-atlas BG tiles, 128 bytes while Listing popup owns them; existing atlas capacity, no permanent expansion |
| Palettes / OAM | Reuse BG0, font cursor; no new palette or sprite entries |
| SRAM | Reuse saved order enum; no save-size or checksum-layout change |
| Implementation complexity | Low for precomputed order selection, moderate for modal map/OAM transactions and redraw latency |
| Main risks | VBlank grid animation overwriting popup cells, leaked/hastily restored OAM, stale order-keyed cache/seen masks, warming scratch reuse, Search cancellation, future missing metadata |

The accepted Modes bank has 14,608 free bytes; this scoped work does not require
another entire ROMX bank. Exact opaque-border matching at arbitrary sub-tile
coordinates would increase graphics/compositing complexity and should not be
bundled into the lower-risk aligned first prototype.

## Prototype Qualification

- Measure START-to-popup, cursor response, Options-to-Sort, cancel and changed
  sort separately, including same-sort no-op, held/rapid input and physical
  input phases. Report first changed pixels and first complete destination,
  not only routine return times.
- Audit every transition frame with the cursor in all nine grid cells and
  every row-animation phase; uncovered pixels remain intact, with no icon,
  caught ball or green corner drawn over modal text/borders.
- Verify all three full permutations, saved sort preference, 255/256 boundary,
  top/bottom wraps, sparse seen flags, unseen selection, empty/one-entry lists,
  Search/no-match cancellation and presentation switches.
- Re-run all-species cold/warm/internal Selected animation/sample-cry checks,
  tab/Area/Listing returns and rapid input regressions after menu use. Preserve
  the existing warmed/cold-entry policy until its separate removal story.
- Obtain manual popup/alignment/timing approval before production integration.
