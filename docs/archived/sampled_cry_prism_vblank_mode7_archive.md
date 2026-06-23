# Prism VBlank Mode 7 Sampled Cry Archive

This archive preserves the experimental Prism-style sampled cry scheduling
implementation. It is intentionally not part of the cleaned production path.

The current production direction uses the async minmax2 cache player with WRAMX
bank 4 as a rolling decoded PCM4 cache. The Prism path was archived because it
is more invasive and fragile, even though it is useful as a reference and stress
test for very large sampled cries.

## Branch

Archive branch:

```text
Pokeprism-VBlank-Mode-7-Test-Implementation
```

This branch is intended to hold the archived Prism scheduling test so a future
Codex thread can recover the work without polluting the active sampled cry
implementation.

## Files In This Archive

```text
docs/archived/sampled_cry_prism_vblank_mode7_archive.md
docs/archived/sampled_cry_prism_vblank_mode7_archive.patch
docs/archived/sampled_cry_prism_vblank_helpers.asm
```

`sampled_cry_prism_vblank_mode7_archive.patch` is the captured worktree diff for
the Prism-style scheduler as it existed before cleanup.

`sampled_cry_prism_vblank_helpers.asm` is a helper source file that the patch
expects to be included from `main.asm`, but the helper itself is stored beside
the patch so it does not live in the production source tree.

This Markdown file is the handoff guide.

## Goal Of The Test

The goal was to compare two runtime scheduling systems for direct CH3 sampled
cries:

1. Our async WRAMX bank 4 cache player.
2. A Prism-style blocking player that uses VBlank mode 7 to service only narrow
   animation work while sampled audio is playing.

The comparison mattered because some cries, such as Wailord, can exceed the
single-bank decoded cache size. Prism's scheduler streams/decompresses during
blocking playback instead of requiring the entire decoded sample to fit in WRAM.

The Prism test was not meant to replace our codec, mastering, or data pipeline.
It only tested Prism's scheduling model.

## Intentional Differences From Prism

This archive keeps our own:

- mastered cry assets
- minmax2 compression format
- sampled cry metadata tables
- CH3 playback path
- `$22` normal volume / `$77` sampled cry volume policy

It tried to mirror Prism's scheduling behavior:

- sampled cry is queued first
- the caller sets an animation service mode
- playback blocks the main thread
- playback sets `hVBlank = 7`
- VBlank mode 7 services only the paired animation work
- audio/timer/VBlank state is restored afterward

This means the archive is "Prism scheduling parity", not a full Prism sampled
cry port.

## Prism Scheduling Model

Prism's sampled cry path treats `hVBlank == 7` as a special mode, not as just
another normal VBlank handler table entry.

The important sequence is:

1. A sampled cry request is queued instead of played immediately.
2. The caller sets a small mode flag describing which animation is allowed to
   run while playback blocks.
3. The sampled cry playback routine saves audio/timer/VBlank state.
4. Playback sets `hVBlank` to mode 7.
5. The main thread blocks while the timer-driven sample player advances.
6. Each VBlank enters the special mode 7 path before normal handler dispatch.
7. Mode 7 runs only the specific animation service needed for that context.
8. Playback restores audio/timer/VBlank state and returns.

The mode flag was mirrored as `hSampledCryRunPicAnim`:

```text
0 = no paired animation / animate tileset only
1 = stats page frontpic animation
2 = Growl/Roar battle animation service
```

The queue flag was mirrored as `hSampledCryQueued`.

## Why VBlank Mode 7 Exists

The blocking sampled cry player would normally freeze all foreground logic until
the cry finishes. Prism uses VBlank mode 7 so a small amount of visual work can
continue during that block.

For the stats page, this lets the frontpic animation continue while the sampled
cry plays.

For Growl/Roar, this lets the battle animation service enough OAM/palette work
to keep the animation alive during the blocking cry.

This is not a generic async system. It is a carefully limited exception for the
few animation paths Prism chose to support during sampled playback.

## Patch Contents

The archive patch touches these areas:

```text
Makefile
constants/ram_constants.asm
engine/battle_anims/anim_commands.asm
engine/gfx/dma_transfer.asm
engine/gfx/pic_animation.asm
engine/pokemon/stats_screen.asm
home/audio.asm
home/vblank.asm
main.asm
ram/hram.asm
ram/wram.asm
```

The patch adds test ROM targets, including:

```text
sampled_cry_mvp_prism_vblank_minmax2
pokecrystal_sampled_cry_prism_vblank_minmax2_mvp.gbc
```

The Prism test target used these defines:

```text
SAMPLED_CRY_MVP
SAMPLED_CRY_MVP_MINMAX2
SAMPLED_CRY_MVP_PRISM_VBLANK
SAMPLED_CRY_MVP_VOLUME_POLICY_22
```

The old patch may also include other experimental sampled cry targets because it
was captured before the cleanup pass. If restoring this work, port only the
Prism VBlank scheduling pieces unless those older targets are explicitly needed.

## Helper File

The patch adds this include to `main.asm`:

```asm
INCLUDE "engine/battle_anims/sampled_cry_prism_vblank_helpers.asm"
```

Before building a restored Prism test, copy:

```text
docs/archived/sampled_cry_prism_vblank_helpers.asm
```

to:

```text
engine/battle_anims/sampled_cry_prism_vblank_helpers.asm
```

That helper contains:

- `CopyGrowlOrRoarPals`
- `BattleAnim_TransferAnimatingPicDuringHBlank`

Those routines were kept outside the live source tree because they are only for
the archived Prism scheduling path.

## HRAM/WRAM Concepts

The Prism path used additional HRAM fields to mirror Prism's scheduling state:

```text
hSampledCryQueued
hSampledCryRunPicAnim
hRequestedVTileDest
hRequestedVTileSource
hLYOverrideStackCopyAmount
```

It also used WRAM fields for Prism-style stats pic transfer state and temporary
debugging:

```text
wPokeAnimDestination
wSampledCryVBlankDebugStatus
wSampledCryVBlankDebugEntrySP
wSampledCryVBlankDebugExitSP
wSampledCryVBlankDebugVBlank
wSampledCryVBlankDebugRunMode
wSampledCryVBlankDebugROMBank
wSampledCryVBlankDebugWBK
```

Some of the debug fields may not be desirable if this is revived. They were
useful for diagnosing hard crashes while matching Prism's VBlank mode 7 flow.

## LY Override Ordering

One important bug was caused by not matching Prism's assumed ordering for LY
override request state. Tackle's BG scanline effect became corrupted until the
ordering was copied to match Prism.

If the Prism path is revived, preserve the Prism ordering for the requested tile
source/destination and LY override copy amount unless the whole path is audited
and rewritten. This ordering is not cosmetic; some code assumes it.

## Known Test Results

During testing, the Prism VBlank build eventually reached this state:

- stats page sampled cries no longer hard crashed
- stats page frontpic animation worked during playback
- battle send-out sampled cries worked
- Growl with sampled cries worked after bank/layout fixes
- Tackle scanline BG corruption was fixed by matching Prism's LY override order
- Wailord worked as a large-cry stress test in the Prism build

However:

- the Prism build blocks menu/battle foreground logic until sampled playback
  returns
- long cries such as Wailord prevent changing stats tabs or moving to another
  Pokemon while the cry is still playing
- Growl/Roar visual scheduling is more fragile than the async cache path
- restoring this patch on top of newer code may require manual conflict work

The async WRAMX cache path was preferred because it lets foreground behavior
continue more naturally while sampled cries play.

## Restoration Procedure

Use a clean branch or worktree. Do not apply this directly on top of production
work unless you intend to revive the Prism experiment.

From the repo root:

```sh
git apply --check docs/archived/sampled_cry_prism_vblank_mode7_archive.patch
```

If that passes:

```sh
git apply docs/archived/sampled_cry_prism_vblank_mode7_archive.patch
```

If it does not pass because production code has moved on, try:

```sh
git apply --3way docs/archived/sampled_cry_prism_vblank_mode7_archive.patch
```

Then copy the helper file:

```sh
cp docs/archived/sampled_cry_prism_vblank_helpers.asm \
   engine/battle_anims/sampled_cry_prism_vblank_helpers.asm
```

Build the Prism test target:

```sh
make sampled_cry_mvp_prism_vblank_minmax2
```

Expected output:

```text
pokecrystal_sampled_cry_prism_vblank_minmax2_mvp.gbc
```

## Suggested Retest Matrix

If this is revived, test at least:

- pink stats page for a sampled cry Pokemon
- battle send-out for a sampled cry Pokemon
- Growl using a sampled cry Pokemon
- Roar using a sampled cry Pokemon
- Tackle or another animation using LY/scanline BG effects
- one long stress cry such as Wailord
- one non-sampled Pokemon to confirm synth cries still work

For each, check:

- no hard crash
- no illegal opcode
- no palette/OAM/BG corruption
- no stale tile corruption after playback
- correct left/right panning in battle
- audio/timer state restores after playback
- BGM/SFX resume correctly

## Why This Is Archived

The Prism-style implementation proved useful for understanding how Prism keeps
limited animation work alive during blocking sampled cry playback. It also
showed that very large cries can be handled without a full decoded WRAM cache.

The production path moved away from it because our async minmax2 cache player:

- is less invasive
- does not require special VBlank mode 7 scheduling
- keeps foreground behavior responsive during normal-size cries
- avoids Prism's fragile Growl/Roar visual coupling
- still supports minmax2 compression and the current mastering pipeline

Keep this archive as a fallback if future large cries exceed the practical
limits of the rolling WRAMX cache strategy.
