# Deferred Dex Cleanup Archive

Archived 2026-10-13 before scoping the New Dex Entry layout redesign. Cleanup
is deferred until that screen is finalized. No archived cleanup has been
promoted to production or accepted through the full runtime regression suite.

## Contents

- `findings.md`: component boundaries, decimal savings, complexity/risk and
  dependencies on the New Dex Entry redesign.
- `baseline-source.tar.xz`: committed production source with matching converted
  graphics and generated tables, without objects or player batteries.
- `baseline-cartridge.tar.xz`: the exact assessed production ROM, symbols/map.
- `recommended.patch` and `recommended-cartridge.tar.xz`: the 1,661-ROMX-byte
  code-cleanup candidate, including the wrap no-op and overwritten footer.
- `with-asset.patch` and `with-asset-cartridge.tar.xz`: the 1,702-ROMX-byte
  candidate, also trimming the Dex-only Slowpoke graphics prefix.
- `with-asset-additions/`: the prefix blob required by that second patch.
- `manifest.json`: source baseline identity and SHA-256 checksums.
- `inventory.json`, `results.json`, `extras.json`, build logs and `recipes/`:
  the audit and reproducibility evidence. The two patches are alternatives,
  both based on the archived baseline; do not apply one on top of the other.

These are **link-only pruning probes**, not play-qualified prototypes. The old
nest scanner's retained namespace must be cleaned up before promotion; any
observer/interface updates and the complete regression remain required.
The existing player save is deliberately not included or modified.

## Restore

From the repository root, use a new private output directory:

```sh
PYTHONPATH=tools:. python3 tools/archive_dex_unused_scope.py verify
PYTHONPATH=tools:. python3 tools/archive_dex_unused_scope.py restore \
  --variant recommended --destination build/dex-cleanup-restored
```

Use `--variant with-asset` or `--variant baseline` for the other packages.
The restore helper checks archive hashes, extracts the source, applies one
baseline-relative patch and supplies its matching ROM/symbol/map files.
Building the restored source must reproduce the manifest's ROM hash:

```sh
make -C build/dex-cleanup-restored -j6 pokecrystal.gbc
shasum -a 256 build/dex-cleanup-restored/pokecrystal.gbc
```

The archived recipes are provenance, not instructions to overwrite a later
production checkout. For a future implementation, compare its source with
this baseline, reevaluate which registration dependencies have become unused,
adapt the patches narrowly and rerun the full documented regression. Preserve
the accepted precomputed Selected renderer; this archive does not replace it.
