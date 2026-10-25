# Type Matchups: Isolated Mode 7 Comparison

Final comparison date: 2026-10-12. This records the pre-integration comparison.
The user subsequently selected runtime for production and retained precomputed
as a [documented fallback](pokedex_type_precomputed_fallback.md). Integration and
cleanup results are recorded separately; the comparison measurements below are
the original frozen review evidence.

## Recommendation

Both private prototypes work and complete the full native regression campaign.
Prefer the **precomputed lower panel**: it displays a changed selection about
one frame sooner for 4,889 additional linked ROMX bytes, with identical artwork
and no additional SRAM, WRAM, or HRAM allocation. Runtime construction remains
a viable smaller alternative. Both share the same display-owner implementation;
runtime does not avoid its raster/audio complexity.

Production parity is strong, but not literally universal. Phase-matched battle
animations are exact. The requested battle-chart changes cause a few different
animation start phases in whole-battle tests. One Legacy Selected-entry case
also takes one extra frame. These are quantified rather than hidden behind an
unqualified "all green" statement.

## Review Artifacts

Paths below are relative to the repository root. The base directory is
`build/dex-types-mode7-audio-20261012/`:

| Artifact | Path Within Base |
| --- | --- |
| Runtime ROM | `runtime/pokecrystal-dex-types.gbc` |
| Precomputed ROM | `precomputed/pokecrystal-dex-types.gbc` |
| Source trees and review batteries | Each variant's `candidate/` and matching `.sav` |
| Safe rollback | `rollback/` |
| Comparison acceptance | `comparison.json` |
| Independent full campaigns | `runtime-regression/full-regression.json`, `precomputed-regression/full-regression.json` |
| Exhaustive animation evidence | `all-animations/report.json` |
| Chart/start-phase investigations | `chart-phase-check/summary.json`, `chart-phase-check-100/summary.json` |

Frozen SHA-256 values:

```text
Production:
591d2075b0c986846b94bc92288d1fa4f9d2918fccc680a83928fd8fdcf59bee
Retained Type/cursor prototype and rollback:
69705d016d2cd9022bdd2fc3ae28d5884b78548012c430ec70cc8f784000803c
Runtime:
469f7db4ed492e3d44fc29cd6bd0dbc51d1f5e5671732861c98a81623a747cac
Precomputed:
a5c469fc9cd06a89c10ee14fa3c9fb08dac4326a92cce91abb8abd6755f684c4
```

The older `build/dex-types-mode7-20261012/` versions are superseded. They failed
expanded music/SFX stress and are not the final review ROMs. Replay builds in
`build/dex-types-mode7-final-replay-20261012/` reproduce both final hashes.

## Display Ownership

Mode 7 was not unused: existing Dex listing/preparation uses it. The extension
tags the Type-only use with bit 4 of `hVBlank`, producing `$17`. The common
wrapper still masks to the existing eight-handler table. No ninth slot or
extra common-wrapper check was added.

The ordinary LCD routine, VBlank wrapper, `VBlank_Normal`, and ordinary audio
engine retain production instruction paths. Old Type checks in shared
LCD/normal VBlank were removed. Only mode 7 pays the new selector: 28 CPU
T-cycles on its non-Type path, about 3.34 microseconds at double speed. Ordinary
battle interrupt handling does not pay this check.

The Type owner disables STAT interrupts while active and services the raster
cooperatively. Four BG palette accent slots are reused across rows. Ten events
occur at visible lines 21, 35, 49, 63, 77, 95, 103, 111, 119, and 127; the first
row is prepared in VBlank. Palette 0 remains the Dex frame/background. Existing
badge artwork is retained; no new assets are required.

Lower tile/attribute maps and accents are double buffered. Selection changes
are built off-screen, then five rows, palette page, and cursor commit together.
Directions update the bottom section automatically; A/Start are ignored.
B/Select leave through the normal Dex menu. Banks, registers, interrupt
settings, OAM locks, and palette ownership are restored. Nine bytes of existing
exclusive Dex scratch are used, without new global allocations or save changes.

## Runtime And Precomputed Panels

Runtime caches the canonical battle chart once on entry and constructs W/R/I
lists with cooperative yields. Precomputed records are generated from the same
chart, constants, character map, alphabetical order, and existing badge/palette
definitions. Each of 18 records is 262 bytes: 22 metadata, 100 tile IDs,
100 attributes, and 40 accent bytes. Records plus the pointer index take
4,752 bytes; loader code accounts for the remaining 137-byte difference.
Build dependencies regenerate records after relevant changes. There is no
second hand-maintained chart. Some unused runtime drawing code remains linked
in the precomputed prototype; later cleanup could remove it.

Both show separate immunity rows for Dark, Electric, Fairy, Flying, Ghost,
Ground, and Normal. Steel keeps ten combined resistance/immunity badges.
Resistance placement moves down when weaknesses require a second row.

## Audio Stress Failure And Correction

The first versions passed normal Type tests but failed Route 12 music plus
menu SFX. A long command burst in `_UpdateSound` ran past a palette deadline;
one captured frame contained five mode-3 palette writes. Bank/register checks
still passed, so those checks alone were insufficient.

Final versions use a **Type-only cooperative audio copy**, yielding at each
channel and music-command loop while reusing existing finite decoder helpers
and hardware writes. Subroutine returns go through the private loop too.
Ordinary `_UpdateSound` is unchanged. The copy adds 239 ROMX bytes and a
14-byte ROM0 bank-preserving yield bridge.

Both passed all 122 music entries, including silence, with 1,800 idle frames
per entry and three menu SFX. A second campaign used 360 idle frames and
immediate SFX/held-direction navigation with atomic frame checks. No illegal
palette windows, bad indexes, mixed selection frames, duplicate frame work,
or bank/register failures were found. The longest private VBlank call was
about 6.89 ms; cooperative raster service continues inside that call. This is
Type-only work, not a larger budget for ordinary VBlank.

## Responsiveness

Eight entry phases and 576 navigation cases were measured per variant:
18 types, four directions, eight physical starting phases. These are emulated
wall-clock input-to-display times, not host CPU benchmark time.

| Metric | Runtime Min / Median / Max | Precomputed Min / Median / Max |
| --- | --- | --- |
| Complete Type entry | 168.00 / 175.32 / 182.65 ms | 168.00 / 175.32 / 182.65 ms |
| Direction accepted | 2.81 / 10.50 / 18.18 ms | 2.82 / 10.50 / 18.19 ms |
| Lower panel published | 51.38 / 58.72 / 66.05 ms | 34.65 / 41.98 / 49.31 ms |
| First complete changed display | 68.06 / 75.39 / 82.73 ms | 51.32 / 58.66 / 65.98 ms |

Precomputation saves about 16.74 ms, one frame. Shared setup dominates entry.
Both keep the CPU polling while this page is active; actual hardware power
consumption has not been measured.

## Outside Type Matchups

- All 3,656 renderer cases per build exactly match production physical cycles,
  logical updates, and full rendered-frame hashes: 10,968 calls across three
  builds, all 333 moves and 28 auxiliary entries, with no coverage/restoration
  errors. No animation scripts were changed.
- The normal-input sweep has 666 cases per build and the same 632 clean cases
  and 34 exceptions. Nineteen need condition-specific fixtures; thirteen return
  somewhere other than the generic turn menu; two reproduce production's
  Sand Tomb hang, separately queued as `BATTLE-MOVE-02`.
- The 100-move campaign has 800 paired comparisons per candidate: 781 exact
  durations, nineteen start-phase-dependent differences, seven slightly over
  one frame. The largest increase is 33.60 ms for foe Swift.
- Replacing only the new chart with production's chart in a diagnostic runtime
  build restores exact duration in every differing targeted case: eleven
  checks from the all-move sweep and twenty-one from the 100-move campaign,
  including controls. Both final variants have identical measured deltas.
  This separates chart-scan/start alignment from display overhead.
- Modern Selected-owner reveal: 256 pairs, median -0.024 ms, maximum slowdown
  0.782 ms. Legacy: 256 pairs, median 0 ms, maximum 16.744 ms for long-hover
  Dusknoir. Traces show actual publication one frame later in that narrow case.
  The exact responsible instruction was not isolated. Do not describe all
  non-Type latency as bit-identical.
- Custom-menu first/complete pixel timing and popup readiness match exactly.
  Valid load, legacy load/migration, full legacy migration, and recovery match
  exactly. Normal save is approximately 0.021 ms faster in the fixture.
- Sampled-cry segments match production, including the same 32 known sampled
  timing misses, without new identities.

The requested chart effectiveness changes and already-approved shared blinking
cursors are intentional feature differences from production.

## Regression And Limitations

Each final ROM independently completed Pokemon Dex, Moves/search/keyboard,
sort memory, persistence, acquisition, battle discovery, Struggle award,
Unown, PC/daycare, custom menus, sampled cries, surrounding gameplay, speed
transitions, Selected playback, and timing campaigns. See the
[Full Regression Suite](full_regression_suite.md) for exact counts and commands.

Focused Type tests covered all six CGB revisions, all selections, 13,164 legal
display frames per variant, 790,016 badge pixels per revision, and return paths.
All eighteen rendered selections also match between variants outside the
expected cursor blink phase, covering 413,568 compared pixels.

The 86-case linked host suite retains one production Info LY64 assertion
failure. The historical 187-case suite has the same six failure, sixteen error,
and 103 skip identities as production. These are not represented as passing
checks; historical message differences remain recorded.

Initial host comparison lacked conventional ROM/symbol/map files inside the
baseline source folder. Preparation was corrected and both host suites and
reports rerun. `phase-results.json` preserves failed attempts and successful
retries. Neither game ROM changed during that correction.

Acceptance requires current hashes, exhaustive animation timing/pixels and
coverage, both audio stress campaigns, and six-model Type evidence. Both final
reports have no new acceptance issues. Physical hardware, subjective visual/
audio review, and the narrow Legacy timing difference remain review caveats.
This report does not authorize production integration.

## Space, Complexity, And Risks

| Allocation | Runtime | Precomputed |
| --- | --- | --- |
| ROM0 used / free | 15,905 / 479 bytes | 15,905 / 479 bytes |
| ROMX used / free in allocated banks | 2,340,223 / 707,201 bytes | 2,345,112 / 702,312 bytes |
| Delta from retained Type/cursor prototype | -26 ROM0, +713 ROMX bytes | -26 ROM0, +5,602 ROMX bytes |
| Additional SRAM/WRAM/HRAM | 0 | 0 |

The audio/song bank `$3a` has only **26 free bytes** after the private copy.
Eighty new moves do not necessarily mean eighty new sounds, but new SFX
pointer/data growth needs a bank-layout review. Aggregate free ROM does not
guarantee that individual bank-local assets fit.

Shared owner complexity is moderate/high: cooperative raster deadlines, audio
yields, atomic publication, and exits are maintenance contracts. Runtime adds
on-page chart-building/yield work. Precomputed adds a small deterministic
generator/dependency obligation but reduces runtime work. Its approximately
4.8 KiB cost is modest against current space, subject to bank-local constraints.

Future audio commands and Type loops must remain bounded or yield often enough.
Do not restore checks to ordinary IRQs as a shortcut. The
[interrupt timing contract](battle_animation_interrupt_timing_contract.md)
still requires physical timing and pixel comparison, not merely a return check.

## Reproduction

Captured patches are `tools/dex_timing/probes/type_mode7_runtime.patch` and
`type_mode7_precomputed.patch`. The builder plus panel/audio generators
reproduce both hashes from the retained rollback source. Replay builds verified
this rather than relying on incremental object timestamps.

```sh
python3 tools/build_dex_types_mode7.py prepare --source build/dex-types-cursors-20261011 --output build/type-mode7-new-review
python3 tools/build_dex_types_mode7.py build --output build/type-mode7-new-review --variant runtime
python3 tools/build_dex_types_mode7.py build --output build/type-mode7-new-review --variant precomputed
```

Detailed setup, fixture dependencies, test ordering, acceptance rules, and reuse
on other branches are in [Full Regression Suite](full_regression_suite.md).
