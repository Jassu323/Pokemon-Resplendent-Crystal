# Preserved Thunderbolt Reference

The user requested retention of the three-way Thunderbolt investigation on
2026-10-04 for future animation development. The maintained findings are in
[Thunderbolt three-way comparison](../thunderbolt_three_way_comparison.md).

The local evidence package is outside disposable build outputs:

`research_artifacts/thunderbolt-comparison-20261004/`

Do not remove this directory during build cleanup. It is intentionally ignored
by Git because it includes recordings, raw captures, emulator states and copied
cartridges. The documentation and preservation/replay tools remain in Git.
This is a local retained archive, not an off-machine backup or a GitHub upload.

## Contents

- `videos/`: all six individual recordings with sound, all four compiled
  comparisons, posters and the representative review screenshots.
- `captures-and-replay-inputs.tar.gz`: every Emerald and Crystal instrumentation
  capture, raw frame/audio output, state/hold CSV, result record, combined
  measurements, private start states and observer configuration/builds.
- The same compressed archive includes the exact three ROMs, matching
  Crystal symbols and Emerald ELF/map, host-tool source snapshots and a report
  snapshot. It does not need the temporary full Emerald source/build tree.
- `manifest.json`: sizes and SHA256 hashes for every archive member and media
  file, plus their original locations. Archive contents and copied videos are
  verified against the originals before preservation is reported complete.

The double-speed arm is the accepted unpaced whole-game prototype, not the
rejected shared phase-pacing experiment. ROM identities are in the report and
are independently preserved by the manifest.

## Verification and Recovery

From the project root:

```sh
python3 -m tools.gba_timing.preserve
```

On an existing package this command verifies it without overwriting it.
To inspect or recover files into a new working directory:

```sh
mkdir -p build/thunderbolt-reference-restored
tar -xzf research_artifacts/thunderbolt-comparison-20261004/captures-and-replay-inputs.tar.gz -C build/thunderbolt-reference-restored
```

Members are grouped under `captures/`, `roms/` and `host-source/` rather than
using absolute extraction paths. The videos are immediately usable without
unpacking the raw captures. Original generated outputs remain unchanged under
`build/`, but future cleanup may remove those because this verified archive is
the retained copy.
