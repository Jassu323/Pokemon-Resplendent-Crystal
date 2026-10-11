# Unown Mode Vanilla Comparison

2026-10-11. Investigation only; no game code, ROM or graphics changed.
The user reported white blocks around Unown in the no-warming prototype.

Follow-up: the [private correctness repair](pokedex_unown_fix_prototype.md)
fixes both findings on that prototype's base and adds independent native content
and pixel assertions. This report retains the original investigation evidence.

## Captures

Evidence is under `build/dex-no-warming-20261011/unown-investigation/`.
`comparison.json` records the ROM hashes, caught-form data, displayed count,
current form index, resident-font comparison and screenshot hashes.

- `vanilla/1-forms-0.png`: freshly linked upstream vanilla, one caught A form.
- `production/1-forms-0.png`: committed production, same caught-form fixture.
- `prototype/1-forms-0.png`: no-warming prototype, same fixture.
- Corresponding `26-forms-0.png` images: all forms caught in A-Z order.

The vanilla reference is the retained upstream build in
`build/dex-sort-scope-20261005/vanilla/`, SHA-256
`d6702e353dcbe2d2c69183046c878ef13a0dae4006e8cdff521cca83dd1582fe`.
It is not byte-identical to the installed `pokecrystal-original.gbc`; each
capture uses its own matching symbols and a private copy of the installed
vanilla battery. Production/prototype identities are the same as the
[no-warming report](pokedex_no_warming_prototype.md).

The only fixture changes unlock Unown Mode, select the initial Listing mode
and set the declared caught forms in both checksummed save records. No live
game memory or instructions are patched. Navigation uses normal inputs.

## Findings

1. **Unused glyph/cursor positions select the wrong blank tile bank.**
   `_CGB_PokedexUnownMode` in `engine/gfx/cgb_layouts.asm` marks entire overlay
   strips as `BG_BANK1`, including untouched `$7f` spaces. Bank 0's `$7f` is
   the valid dark-gray space (`00ff` repeated); bank 1's `$7f` is zero-filled
   and therefore displays white with palette 0. This produces white bands
   and blocks around the portrait. The correct resident blank background
   exists separately at bank-1 tile `$32`; assets are not missing.
2. **The caught-form drawing loop overwrites its remaining-count register.**
   `Pokedex_DrawUnownModeBG` in `engine/pokedex/pokedex.asm` initializes C to
   `NUM_UNOWN`, then its CGB/DMG tile-conversion branch assigns the current
   form number to C. A has value 1; the subsequent decrement terminates the
   loop immediately. With all 26 IDs present, production and prototype set
   `wDexUnownCount` to 1, show only A and reject Right. Vanilla reports 26,
   draws all forms and advances to B. Other catch orders can hide the early
   exit; the overwritten register also loses the full-capacity loop bound.

The production/prototype settled screenshots match byte-for-byte. Both faults
predate no-warming removal. The 27 resident Unown font/cursor tiles match the
ROM's inverted source data exactly in both builds, so no new graphics are
required. The selected A frontpic and its five-letter Unown word are correct;
the project's orange/dark-gray palette versus vanilla's black panel is not
itself a missing-asset defect.

Prior Modes regressions checked complete/atomic screen transitions, menu-row
restoration and subsequent Selected playback. They did not independently
validate every settled Unown glyph, caught-form count or blank-overlay pixel.
Those content assertions must accompany a fix, including sparse caught orders,
A in different positions, all 26 forms, both Listing origins and return paths.
Keep correctness repairs separate from deferred Unown latency work.

## Reproduction

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.unown_comparison \
  --source build/dex-no-warming-20261011 \
  --output build/dex-no-warming-20261011/unown-investigation \
  --vanilla-source build/dex-sort-scope-20261005/vanilla
```

The tool creates isolated one-form/all-form batteries and native emulator
screenshots, not replacement artwork or a repair ROM.
