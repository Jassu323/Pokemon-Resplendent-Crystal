# Retired Pokedex Graphics

Preserved during the 2026-10-14 CGB-only Dex cleanup. No original pixels were
edited. The exact converted/compressed files are retained alongside the source
PNGs so future reuse does not depend on a particular graphics-tool version.

- `pokedex_sgb.*`: the retired SGB-specific Dex sheet. No cartridge code loads it.
- `slowpoke.*`: the original complete Search sheet, including seven obsolete
  large-cursor tiles. The active build derives `slowpoke_dex.2bpp` from its first
  48 tiles only. This preserves all five animation frames and the live scrollbar
  tile without compiling the trailing cursor tiles. Neither mobile copy remains.
- `unused_info_page_numbers.2bpp`: the exact four tiles formerly loaded by the
  unused Info page-number graphics label, offset 96 and length 64 in the original
  column-major sheet. `info_page_numbers_source.png` preserves the whole source
  for context. The active shared page sheet stays in `gfx/pokedex`, since other
  Description/Info owners still use it.

The Slowpoke binary is a source dependency for the retained prefix. Do not delete
or globally truncate this archived original. The Makefile's conversion option
preserves its original whitespace-trimming convention if regeneration is needed.
These archival binaries are explicitly exempted from compiled-graphics ignores.
