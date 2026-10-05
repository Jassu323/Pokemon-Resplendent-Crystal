# Archived Documentation

These records are intentionally kept separate from maintained instructions.
See the [documentation index](../index.md) for current systems and testing.

- [Dex scheduler investigation](dex-scheduler/README.md): dated measurements, prototypes and superseded procedures retained as engineering evidence.
- [Legacy Virtual Console notes](legacy/vc_patch.md): upstream historical reference; not a supported or validated target for this fork.
- [Preserved Thunderbolt reference](thunderbolt-reference.md): user-retained three-way videos, raw instrumentation, exact ROMs/states and verification manifest outside disposable build outputs.

Keep curated documentation in Git. Raw captures, copied ROMs/saves, generated
reports and binaries belong in ignored root `build/`. The local
`sampled_cry_prism_vblank_mode7_archive.patch` is already excluded by the
repository's patch ignore rule; it is not a required documentation dependency.

Exception for explicitly requested long-term evidence: the ignored
`research_artifacts/` directory contains retained packages that must not be
removed as ordinary build cleanup. Each package has a tracked catalog entry
above with its provenance and recovery procedure.

## Speed-Trial Build Cleanup

The 2026-10-05 cleanup uses `tools/cleanup_speed_builds.py` to archive explicitly
listed performance, clock and animation-trial build families. It verifies every
archived member before deleting any loose copy. The local archive and member
manifests are under `build/retained-history-20261005/`; its `README.md` describes
recovery into a fresh scratch directory. Current accepted source snapshots,
review ROM/saves, aggregate reports and videos remain directly available.
Historical document paths may now refer to archive members rather than loose
files. Reproduction scripts remain in `tools/`. This local archive is ignored,
not an off-machine backup, and does not replace the separately protected
Thunderbolt research package.

This pass verified 1,710,964 historical members and archived approximately
109.91 GiB of loose file data into 28.66 GiB of lossless archives, reclaiming
about 81.25 GiB before filesystem allocation effects. One changed Finder
metadata file was preserved when the safety check paused removal; `--finish`
resumed using the verified archive hashes. Production and current review ROMs
are unchanged. Exact member/retention records are in the local cleanup manifest.

## Approved Follow-Up Compaction

Later on 2026-10-05, the user approved retiring redundant historical per-test
traces, extracted frames/audio and rebuildable objects. This supersedes the
first pass's lossless retention policy for eight speed-trial families.
`tools/compact_build_evidence.py` keeps source/build recipes, all derived
result/reference/configuration JSON and CSV, ROMs/symbols/maps, battery saves,
starting CPU states, authored assets and review media. Replacement archives
and every retained member are verified before the original archives are removed.

The current production qualification is compressed **losslessly**, not pruned.
Its aggregate reports, configurations and starting inputs remain directly
usable; bulky traces, raw frames/audio and individual result files are in the
verified archive. Neither the production ROM nor accepted review pairs change.
The protected Thunderbolt research package and its older build archive are
excluded from this compaction.

Current evidence and recovery instructions:
`build/retained-history-20261005/compact/README.md`. The original full member
catalogs survive in `compact/original-manifests/*.json.gz`; they document what
was retired but do not restore discarded content. Recover retained members
into a scratch directory or regenerate old bulk from the preserved inputs.
Do not run the first-pass tool's `--finish` after compaction. Use
`python3 -B tools/compact_build_evidence.py --verify --jobs 3` for read-only
member/archive verification. These remain local ignored archives, not backups
stored with the repository.

Measured follow-up result: approximately **39.86 GB / 37.12 GiB reclaimed**;
the build folder is now about **7.96 GB / 7.41 GiB** rather than roughly 48 GB.
The eight historical archives shrink from 28.56 GiB to 1.61 GiB, retaining
647,923 source/result/input/media members and retiring 1,031,376 redundant bulk
members. Current qualification's 49,123 removed loose files compress losslessly
from 11.66 GiB to 1.69 GiB. Catalogs add some overhead to those archive sizes.

All nine replacement archives pass post-cleanup verification of 697,046
retained members. Five helper tests pass. The 2,325 protected file hashes are
unchanged, the production ROM still has SHA-256
`94ca7887537a378e036f9b5bfd5e771ef8989ec0c20854e32da13bf100d53aec`, and
the separate Thunderbolt package independently re-verifies all 4,549 members.
Exact byte counts and family identities are in `compact/cleanup.json`.
