# Buffered Dex Icons Test ROM

This is a private test build. The production ROM and production source files
have not been changed for this prototype. This entire build folder is ignored.

## Files

- `pokecrystal-dex-buffered-icons.gbc`: executable test ROM.
- `pokecrystal-dex-buffered-icons.sym`: matching production and prototype symbols.
- Implementation: `../dex-icon-buffer-return-repair/icon-buffer.asm`.
- Rebuild and focused checks: `../dex-icon-buffer-return-repair/run.py`.
- Return and footer checks: `../dex-icon-buffer-return-repair/return-controls.py`.

ROM SHA-256:
`853fa67532e7bc603a6fe2857e6896c119db6b592b87d9ca950bf654711a21a7`

## Expected Behavior

During internal Description paging, the outgoing footprint and type badges
remain unchanged, including their colors, until the incoming page is revealed.
The portrait still uses its temporary white mask. New icon graphics upload into
the inactive buffer and become visible with the new page's atomic reveal.

B-return restores the original footprint cache before Listing re-entry. This
also prevents an immediate reopening from displaying another species' footprint.
Animation scheduling and sampled cry settings are unchanged.

## Manual Review

1. Page in both directions through single-type and dual-type species.
2. Try several consecutive pages, including while animations and cries play.
3. B-return and immediately reopen the selected species; check its footprint.
4. Toggle the description text with A and make an Area-page round trip.

Check for icon flicker, changing colors before the reveal, incorrect footprints,
missing or stale type badges, and animation or cry regressions. Existing save
files use the same format; no user save file was modified.

## Resource Use

- 262 ROMX bytes total, 202 more than the background-mask prototype.
- 12 additional BG VRAM tiles (192 bytes).
- One byte reused from the existing Dex scratch union.
- No new ROM0, WRAM0, WRAMX, or HRAM allocation.

The broader preflight passed 647 paired transition cases and a continuous
all-species paging chain. Fresh focused transition and return checks are run
again when packaging this ROM.
