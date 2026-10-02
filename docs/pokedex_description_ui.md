# Selected Description UI

Updated 2026-10-01. This layout belongs only to the Start-menu Dex's Selected
Description view. New Dex Entry keeps its existing shell and shared text printer;
the animation scheduler, dictionary plans and audio decoder are unchanged.

## Layout

The native display is 160x144 with `SCX=5`. The Description-specific background
uses a fixed 20x18 backing tilemap plus one separately owned right-edge column.
That column matters: five pixels of BG column 20 remain visible after the
horizontal offset. Both hidden transition buffers and direct publication retain
its border tiles and palette-0 attributes. Animation publications copy those
same buffers, so they cannot replace the edge with the generic padding tile.

The frontpic outline occupies x=1..60, y=5..66; the data outline occupies
x=62..158, y=5..66. The Description outline occupies x=1..158, y=69..130.
The footer retains its existing labels and cursor, with its right cap inside
the visible display. Name, category, height, weight, description text and
frontpic placement are unchanged.

The page badge is embedded in the divider, with its glyph two pixels higher
than the former badge. `Pokedex_DisplayDescriptionEntry` delegates content to
`DisplayDexEntry`, then restores the Description-specific divider and P.1/P.2
tiles. The registration page continues calling the shared printer directly.

The upper-right species footprint retains its white mark but now uses a
dark-gray background instead of the former black square. This is a footprint,
not the Listing's caught-ball marker; its graphics are unchanged.

## Type Badges And Palettes

First type: `(9,7)` in backing tiles, screen x=67..98, y=56..63.
Second type: `(14,7)`, screen x=107..138, y=56..63. Each badge is 32x8 and
occupies four BG tiles. Matching base-stat types display only the first badge;
the background template clears the second slot on every species transition.

`GetBaseData` resolves the selected species through the existing extended-ID
tables. The shared compact type graphics are copied into the first 128 bytes
of `wPokedexWRAM0Scratch`, after the base/footprint have been committed but
before animation priming. Only this temporary copy has its four corners changed
to background color, leaving the icons used in other screens unchanged.
One exact four- or eight-block HDMA transfer uploads the badges to bank 1.

Internal paging alternates two footprint/type sets: footprint A at `$8b10`
and types A at `$9640`, footprint B at `$96c0` and types B at `$9700`, all in
bank 1. The outgoing footprint and badges remain visible until the incoming
owner's atomic reveal. Only the shared portrait becomes white during VRAM
replacement. New entry resets to set A; B-return restores its normal resident
footprint before Listing resumes. This avoids an extra reentry repair frame
and prevents a stale resident-footprint tag after repeated internal paging.

BG palette 6 belongs to the first badge, palette 7 to the optional second.
Their shared type colors are retained, but color 1 is replaced with the Dex
background `RGB 5,5,5`. BG palette 2 belongs to the footprint: white color 0,
black colors 1/2, dark-gray color 3. All three palette slots participate in
the existing staged owner's dirty mask; Listing reconstructs its own palettes
when ownership returns. Palette writes explicitly select/restore WRAM bank 5.

## Resources

| Resource | Added use |
| --- | ---: |
| Bank 0 `vTiles2 $71-$7a` | 10 border/badge tiles, 160 bytes |
| Bank 1 `vTiles5 $64-$6b` | 8 type tiles maximum, 128 bytes |
| Bank 1 `vTiles5 $6c-$77` | 12 alternate footprint/type tiles, 192 bytes |
| ROMX | Original UI addition 1,133 bytes; buffered-icon follow-up adds 228 bytes |
| ROM0, WRAM0, WRAMX, HRAM | No new allocations |

The buffer selector reuses the last existing Dex scratch-union byte at `$cd13`.
The follow-up uses 127 additional ROMX bytes in `$77` and 101 in `$a0`; no new
bank, metadata dataset, font graphics or animation slot is required.

Both 49-tile animation slots, all Listing minisprite allocations, the inverted
font and all existing generated animation metadata remain intact. The border
is loaded while the LCD is off when opening the Dex. Species entry performs
the small badge upload before starting playback, not during timed production.

## Verification

Use a freshly rebuilt ROM, never a previous-link save state. The normal-input
headless tests use isolated save copies and observe hardware memory without
changing game RAM or cartridge flags.

```sh
make -j8
make verify-dex-animations verify-sampled-cries
PYTHONPATH=tools python3 -B -m unittest test_dex_scheduler test_dex_cold_listing test_dex_target_regression test_new_dex_entry test_dex_description_ui
python3 -B -m tools.dex_timing.cold_listing --battery build/dex-cold-listing/input-copy.sav --output build/dex-description-ui/cold-final --jobs 8
python3 -B -m tools.dex_timing.description_ui --checkpoints build/dex-description-ui/cold-final --output build/dex-description-ui/screens --all-species
```

The UI audit checks both badge graphics and palettes, monotype clearing,
footprint attributes, both page badges, right-edge preservation and internal
paging. It saves native-resolution images with color correction disabled for
comparison. Color values should be compared as 5-bit GBC colors; emulator
RGB expansion and RetroArch correction can otherwise produce misleading
differences. A settled animation is used before A-button text paging; the
separately logged active-animation A-button issue is not fixed by this change.

Drapion's former category overflow and Mew's embedded terminator have since
been corrected. The audits still report shell/static defects rather than
suppressing them. Outputs remain under ignored `build/` and can be regenerated
from a matching fresh all-seen battery and ROM.

### Current Results

The following bullets describe the original 2026-09-30 UI checkpoint. The
2026-10-01 production link has no Mew/Drapion failures: all 373 cold entries,
373 internal targets and 373 fully rendered buffered transitions pass.
Continuous paging through all 373 species, 36 back-and-forth swaps, 13
Listing returns/reentries and 36 footer checks (24 text-page toggles and
12 Area roundtrips, including both icon sets) also pass. The exact final-link
identity and transition acceptance are in the
[transition reference](pokedex_internal_transition_investigation.md#buffered-icons-in-production).
Historical builds/notes are cataloged in [build history](archived/build-history.md).

- 65 current-link unit/contract tests pass. The finishing tables remain
  conservative in all 216,000 host inequalities; no table changes were needed.
- All 373 cold entries and 373 internal-page targets retain their authored
  animation intervals, correct animated tile pixels and complete sampled cries.
  Each suite reports only Drapion's pre-existing static reveal failure. All
  373 B-return destinations pass in each suite; this is not a palette-flicker
  certification for the separately logged return issue.
- The 1,492 UI observations cover initial page, P.2, P.1 again and internal
  paging for every species. All type identities match base stats, both slots'
  graphics/attributes/palettes match their sources, and monotypes clear the
  second slot. Only Drapion's category overflow reports a shell failure.
- Eight authentic catch flows and 24 New Dex Entry playback/input variants
  pass, including exact uninterrupted animation timing and complete cries.
- Chikorita's UI pixels match the supplied mockup after 5-bit color comparison
  and excluding its intentionally hypothetical second badge. Eight sprite
  outline pixels on the mockup's bottom row are dark gray rather than the
  source frontpic's black; Pokemon artwork is intentionally left unchanged.

`make test-dex-timing` is an older investigation suite, not the current-link
suite above. It still reports six failures and sixteen errors on this cleaned
link because it expects former instrumentation fields, captured breakpoint
addresses and earlier measured costs. Those historical harness assumptions
were not changed as part of this UI work. Use the maintained current-link
checks and normal-input SameBoy audits for the implementation's acceptance.
