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

Chikorita is a useful vanilla comparison point: with color correction disabled,
its greens are much brighter and more saturated; with correction enabled, they
become more muted and olive. This reinforces the same rule of thumb for custom
greens: the source color may need to look too bright or cool in raw screenshots
to land correctly after correction.

## Blues

Croagunk's normal blue was tuned against its official-art direction. Earlier
source values looked closer in raw screenshots, but corrected too bright and
electric-blue in-game.

- Palette source value: `RGB 10, 06, 22`
- RGB5-expanded source color: `#5231b5`
- Raw screenshot appearance: too purple/indigo without correction
- GBC-corrected screenshot appearance: muted medium blue, closer to target

The RetroArch `gbc-color.slangp` shader's sRGB path explains this behavior. It
linearizes the source color, applies a matrix, then converts back to gamma space:

```text
linear = pow(source, 2.2) * 0.91

red   = 0.9050r + 0.1950g - 0.1000b
green = 0.1000r + 0.6500g + 0.2500b
blue  = 0.1575r + 0.1425g + 0.7000b

display = pow(result, 1 / 2.2)
```

For blue sprites, high source blue both raises the displayed green component and
reduces the displayed red component. That can push a raw blue toward bright
cyan/electric blue after correction. If a corrected blue looks too electric,
try lowering blue and slightly raising red, even if the raw source starts
looking more purple than desired.

## Reds

Toxicroak's normal red accents were tuned against its official-art coral red.
The original sprite source color had too much blue, causing the corrected color
to read pink/magenta instead of warm red.

- Palette source value: `RGB 27, 09, 00`
- RGB5-expanded source color: `#de4a00`
- GBC-corrected screenshot sample: about `#d87068`
- Previous source value `RGB 26, 04, 08` corrected too pink.

In the same `gbc-color.slangp` matrix used above, source blue subtracts from the
displayed red channel and strongly survives into the displayed blue channel.
For warm reds and corals, keep source blue very low or at zero, then use green
to control warmth and brightness. The raw source may need to look orange with
color correction disabled to land as a natural red after correction.

## Purples

Ambipom's normal purple was tuned against the shared party-menu icon purple.
Uneven red/blue values tended to shift too blue or too dusty after GBC
correction.

- Palette source value: `RGB 18, 04, 18`
- Raw screenshot sample: `#902090`

For clear sprite purples, keep red and blue equal or nearly equal, and keep
green low. Good starting points are `RGB 16, 03, 16`, `RGB 18, 04, 18`, and
`RGB 20, 04, 20`.
