# Durable Regression Inputs

`dex/inputs.tar.xz` contains only fixtures that cannot be replaced by fresh
run output: seed batteries, known-bad Unown/Moves visual controls and their
symbols, the pre-relocation numeric-cost reference, independent species
description expectations and original footprint masks. Its manifest lists
each input, purpose, size and checksum. It contains no recordings, old pass
reports, copied game source trees, checkpoints or compiled observers.

```sh
PYTHONPATH=tools:. python3 -m tools.dex_timing.regression_fixtures verify
PYTHONPATH=tools:. python3 -m tools.dex_timing.regression_fixtures restore --compile-controls
```

Restoration writes only declared inputs under `build/`, remaps checkout paths
in JSON, refuses differing existing files/symlink destinations and compiles
native observers from current `tools/` plus the separately installed SameBoy
source. These few old cartridges are deliberately faulty controls, not review
ROMs or production baselines. Never use their CPU states with a new link.
The current full campaign still freezes a fresh production baseline and candidate.

See [the cleanup and component map](../../docs/pokedex_build_retirement.md) and
[the regression runbook](../../docs/full_regression_suite.md). Old private
prototype builders may require re-creating their stated historical baseline;
retaining every experiment is not required to run current regression coverage.
