# Moves Dex Scrollbar Prototype

Private visual follow-up to the persistence-only Moves encyclopedia, October 7,
2026. Production and `build/dex-move-persistence-20261007` remain unchanged.
Gameplay discovery hooks and legacy owned-move bootstrap are still deferred.
The accepted visual rollback archive remains intact.

## Manual Review

Current review candidate: `build/dex-moves-scrollbar-20261007e`.
The original scrollbar qualification below records the unchanged `20261007b`
baseline; the subsequent popup placement revisions are documented at the end.

- ROM: `pokecrystal-dex-moves-scrollbar.gbc`
- Matching save: `pokecrystal-dex-moves-scrollbar.sav`
- Optional sparse fixture: `sparse-review.sav`, containing the prior 25 discoveries.
- Native screenshots: `scrollbar-visual/` and `scrollbar-mixed/review/`.

The matching manual-review save seeds all 333 moves to make both full lists
available for inspection. These are private fixtures, not real discovery hooks.
Enter the Dex, press SELECT, choose Moves Dex Mode, and press A. Up/Down browse
and wrap; Left/Right jump eight entries. START opens Sort; a changed sort resets
the list and thumb to the top. Confirming the same sort retains both positions.

## Layout And Ownership

The user's opaque 16-by-24 sheet at
`gfx/pokedex/pokedex_moves_scroll_bar_and_borders.png` is consumed unchanged.
All six tiles match the agreed pixel contract and exact source colors:
white `#ffffff`, orange role `#aaaaaa`, dark role `#555555`.

Move names and the BG cursor shift one tile left, to visible x51 and x43.
Twelve-character names occupy x51 through x146, leaving three dark pixels before
the listing border at x150. The eight rows and six-line description area do not
move. The track's white sides occupy x153 and x157, from y5 to y74.
The bottom tile pair includes the description panel's top/right junction.

The six supplied tiles occupy inactive Info graphics cells `$ba` through `$bf`
in VRAM bank 1 while this owner is active. The existing bank-0 listing rail,
font and sprite graphics are not overwritten. Both visible rightmost BG
columns are staged together, including column 20 exposed by SCX=5.

The existing thumb graphic and listing thumb palette are reused. OAM slot 6
holds the thumb independently of the four type and two category sprites. It
remains present on unseen rows while all move detail icons/stats are cleared.
The normal pixel contract never exceeds five active sprites on one scanline.

Thumb position is rounded from the 16-bit viewport offset over 65 pixels of
travel. With 333 moves, the maximum viewport offset is 325. Top visible thumb
pixels range from y5 to y70; the five-pixel thumb stays inside the track.
Its position represents the viewport, not the selected cursor row.

The original scrollbar link keeps the Sort popup at its accepted placement.
Its partially covered right
edge retains both bitplanes of the underlying scrollbar art rather than
interpreting the rail tile as a font character. The thumb and uncovered track
remain visible while the popup is open. Maps, attributes, palettes and OAM
publish in the existing protected transaction.

## Resources

Increment for the original `20261007b` over the prior persistence prototype:

| Resource | Increment |
| --- | ---: |
| ROMX | 244 bytes |
| Supplied graphics, included above | 96 bytes |
| Net renderer change, included above | 148 bytes |
| New ROM0 / WRAM0 / WRAMX / HRAM / SRAM | 0 bytes |
| Reused VRAM bank 1 | 96 bytes |
| Additional OAM entries | 1, maximum 7 total |

The initial private `20261007` trial used Get2bpp to load the six tiles, adding
one display interval to entry completion. The retained `20261007b` uses the
existing masked staging/HDMA path instead. It temporarily borrows 96 bytes at
the beginning of the existing border scratch; later popup preparation reuses
that same scratch. The discovery snapshot at offset 576 is unaffected.

The isolated thumb calculation costs 256 to 1,816 SM83 T-cycles across every
legal offset, about 0.031 to 0.216 ms at double speed. This is a host instruction
measurement, not a whole-screen latency measurement.

## Qualification

The original qualified `20261007b` ROM SHA-256 is
`018b517302a2c18e550b99e55a7dc26411bc01de8217a4548d347214d8056395`.
All final-link checks passed:

| Check | Coverage |
| --- | ---: |
| All-seen move sweeps and popup cancellation | 1,338 cases |
| Full-page jumps, all cursor rows and endpoints | 1,348 cases |
| Owner/interface matrix | 16 cases, 544 checks, 176 captured transitions |
| Zero/one/25-seen sweeps and page jumps | 8,058 cases |
| Targeted first/middle/end/wrap/sort visual captures | 16 images |
| Independent rendered rail/thumb/border comparison | 16,640 pixels, zero mismatches |
| Adjacent Selected/listing/stress matrix | 2,520 cases across 20 species and both presentations |
| Host contracts, storage layout, assets and arithmetic | 55 tests |

All 843 bytes of the isolated persistence library are byte-identical to the
prior persistence prototype. Its cartridge, save and accepted rollback hashes
are unchanged, as are the root production cartridge/symbols/map.

The initial scrollbar link additionally passed all 6,555 Modern all-species
Selected/listing checks. The retained final-link qualification above was
repeated after changing the entry upload path; initial-link results are not
counted as final-link coverage.

Paired final-link captures against the prior persistence prototype show exactly
zero entry first-response/completion change in all 16 interface cases. Median
first-response and completion differences for navigation, page jumps and Sort
are zero display intervals. The small instruction-phase differences do not add
a whole display interval. Modes return has a near-zero median difference, with
one capture completing an interval earlier due to phase alignment; no speedup
is claimed from that isolated observation.

Final-link results are recorded in the build's `final-qualification.json`.
The visual suite covers both sort orders, first/middle/final viewports, wrapping,
page jumps, popup preservation and cancellation, sorting reset, every permanent
move identity, all eight cursor rows, offsets above 255, and zero/one/sparse
discovery fixtures. Frame captures require wholly old or wholly new menu
publication, with only the existing hidden owner-transition mask permitted.

Surrounding-screen checks cover Modern and Legacy listing restoration, Selected
Description/Info/learnset Moves/Area, animation and sampled-cry deadlines, rapid
inputs, Modes and Search after leaving Moves Mode. The final scoped neighboring
suite targets the 20 established stress species in both listing presentations.
An additional all-species Modern run is retained for the initial scrollbar link.
Those initial-link results are supplemental, not attributed to the final link.

No full save-fault campaign is repeated for this renderer-only follow-up.
Host checks verify the unchanged storage layout, storage routines, seeded
records, protected production artifacts and rollback checksums. The prior
persistence qualification remains the evidence for interrupted-save recovery.

## Reconstruction

Build privately, then prepare exact-link observers/checkpoints:

```sh
env PYTHONPATH=tools python3 -B tools/build_dex_moves_scrollbar_prototype.py \
  --source build/dex-move-persistence-20261007 \
  --output build/dex-moves-scrollbar-20261007b --jobs 8 --prepare
```

Use a fresh output directory, or `--relink` when intentionally rebuilding that
private candidate. Stop its active observers before relinking and prepare fresh
checkpoints. Run the Moves suite, scrollbar visual/mixed/adjacent suites and the
host tests with no more than six native workers concurrently.

## Four-Pixel Popup Follow-Up

The entire Moves Sort popup moves four pixels left, from bounds
`[48, 24, 152, 64]` to `[44, 24, 148, 64]` (exclusive right/bottom edges).
Its 104-by-40 size, text spacing, cursor, vertical placement and surrounding
screen remain unchanged. SCX remains 5; neither the listing nor its track moves.

No source graphics are added or modified. The existing eight-tile border is
repacked at entry for a one-pixel sub-tile phase, and the existing glyph staging
changes from a net three-pixel to a net seven-pixel left shift. The two-pixel
right border now crosses BG columns 18/19. Its partial tile retains seven pixels
of the supplied scrollbar tile, in both bitplanes. The uncovered left pixel is
dark for both listing blanks and the small cursor; the font contract is tested.

All frame tiles can now be staged once on entry. The former per-popup mirrored
edge construction is removed. The final link uses 122 fewer ROMX bytes than
`20261007b`, with no change to ROM0, WRAM, SRAM, HRAM or OAM allocation. The
popup occupies nine reusable bank-1 graphics cells instead of ten.

Review ROM SHA-256:
`4cb28162cd55d3283b8a1f5848b59806f1af0fc2f6b3b1aa20bbc6b1addf9d30`.
The matching all-333-moves save is byte-identical to the prior review save.

The native Moves suite passes 1,338 browsing/popup cases, 1,348 page cases and
16 interface cases with 544 checks and 176 captured transitions. Every one of
the 16 full-screen pixel comparisons matches the old popup translated exactly
four pixels left over the original page. The zero/one/25-discovery matrix passes
8,058 additional browsing/paging cases. Entry and popup first-response/completion
measurements differ by exactly zero display intervals in all paired interface
captures against `20261007b`.

The final-link adjacent regression also passes all 2,520 cases across the 20
established stress species in Modern and Legacy presentations. The 16 scrollbar
captures pass 16,640 independent rail/thumb pixel checks. All 55 applicable host
tests pass; the retained earlier right-edge path test is skipped because that
path was removed. All 843 persistence-library bytes are unchanged. Results are
recorded in `build/dex-moves-scrollbar-20261007c/final-qualification.json`.

Build with the same recipe above, substituting `20261007c` for the output. Run
the Moves suite with `--baseline build/dex-moves-scrollbar-20261007b` to retain
the exact translation comparisons. Native screenshots and detailed results are
in the current review candidate's `moves-mode-qualification/` and
`scrollbar-visual/` directories. Production, persistence and the prior review
cartridge remain untouched. Discovery event hooks are still deferred.

## Corrected Centered Popup

The corrected request moves the popup five pixels left from the original
`20261007b` placement and one tile upward. Relative to `20261007c`, this is one
additional pixel left and eight pixels upward. The final bounds are
`[43, 16, 147, 56]`, retaining the 104-by-40 size and leaving exactly three dark
pixels between each side of the popup and the listing frame. Labels and cursor
move with the frame; the scrollbar and all other layout stay in place.

This placement aligns with the existing BG tile grid at SCX=5. The renderer
uploads the user's original eight border tiles unchanged and uses the regular
font and cursor directly. Sub-tile glyph packing, the copied font workspace,
and the partial scrollbar-edge tile are no longer required. No artwork is
added or modified. The final cartridge uses 379 fewer ROMX bytes than
`20261007c` and 501 fewer than `20261007b`, with unchanged ROM0, WRAM, SRAM,
HRAM and OAM allocation.

An initial placement-only trial (`20261007d`) exposed a phase-sensitive missed
two-display-interval paging press. Its page logic and rendered layout were
correct, but a press could occur entirely inside a redraw before the ordinary
input mirror sampled it. The faster entry altered the starting phase and made
this reproducible. Moves Mode now consumes the existing physical press latch
in both browsing and Sort, atomically, using the same approach as other Dex
popups. It synchronizes the held-input mirror to avoid accepting an edge twice,
keeps the normal held-key repeat delay, gives new directions priority over older
held directions, and leaves scripted auto-input untouched. No new input buffer
or saved state is allocated.

Final review ROM SHA-256:
`299b74dc8e226c4c67ed7f816b1ee983a8af181c44a847d2cbd9cf83183d5b1d`.
The matching review save still seeds all 333 moves. Production, persistence,
the accepted rollback and the earlier review builds remain unchanged.

The final native Moves suite passes 1,338 browsing/popup cases, all 1,348 page
cases and 16 interface cases with 544 checks and 176 captured transitions.
Every full-screen alignment comparison matches `20261007c` translated exactly
one pixel left and eight pixels upward over the original listing. The formerly
missed paging case passes with the new latch handling. Host tests cover short
released presses, held-key mirroring, repeat suppression and auto-input bypass.
The final seen/unseen matrix passes all 8,058 cases; the neighboring Dex suite
passes 2,520 cases across the established 20 stress species in both listing
presentations. The 16 scrollbar captures pass 16,640 independent pixel checks.
All 55 applicable host tests pass, with three earlier packing-path tests skipped
because those paths were removed. All 843 persistence-library bytes are
unchanged. Final results are recorded in the review build's
`final-qualification.json`.

Against `20261007c`, entry's first response is unchanged and completion is one
display interval sooner in all 16 paired captures (about 16.74 ms). Popup open,
highlight, sorting and cancellation have near-zero median differences and no
new full display interval of delay. Detailed final-link results and screenshots
are retained in `build/dex-moves-scrollbar-20261007e`.

Build with the recipe above using output `20261007e`; run the Moves suite with
`--baseline build/dex-moves-scrollbar-20261007c` for the latest translation
comparison. Gameplay discovery hooks remain deferred.
