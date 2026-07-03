# Palette Color Correction Notes

These notes capture known-good source colors for sprites viewed through the
RetroArch `gbc-color.slangp` color-correction shader. Use them as calibration
points when tuning future palettes.

## Bright Greens

Salamence's shiny green was tuned to better match later-generation shiny
Salamence while avoiding the yellow/olive shift caused by GBC correction.

- Palette source value: `RGB 04, 28, 06`
- Raw screenshot sample: `#21e731`
- GBC-corrected screenshot sample: `#6fc270`
- Previous source value `RGB 11, 28, 00` corrected to about `#9ec36b`, which
  was too yellow/olive.

For saturated shiny greens, bias the source color cooler than the desired final
color by lowering red significantly and adding a small amount of blue.

## Purples

Ambipom's normal purple was tuned against the shared party-menu icon purple.
Uneven red/blue values tended to shift too blue or too dusty after GBC
correction.

- Palette source value: `RGB 18, 04, 18`
- Raw screenshot sample: `#902090`

For clear sprite purples, keep red and blue equal or nearly equal, and keep
green low. Good starting points are `RGB 16, 03, 16`, `RGB 18, 04, 18`, and
`RGB 20, 04, 20`.
