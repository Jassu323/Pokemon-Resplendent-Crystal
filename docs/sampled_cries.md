# Direct Sampled Cry Implementation Guide

This document is a handoff guide for future development of direct sampled
Pokemon cries in this pokecrystal16-based repo. It explains the asset pipeline,
species lookup, compression format, runtime playback path, and memory layout.

The current implementation is the async minmax2 cache player. The older
Prism-style VBlank mode 7 experiment is intentionally not part of this worktree.
It was archived separately on the `Pokeprism-VBlank-Mode-7-Test-Implementation`
branch.

## Current State

The sampled cry system is part of the normal `make crystal` build. There is no
separate MVP/test ROM target anymore.

Current output:

```sh
make crystal
```

Expected ROM:

```text
pokecrystal.gbc
```

No vanilla Pokemon are currently mapped to sampled cries. The generated Hoenn
starter and Shinx `.mm2` assets remain in `audio/sampled_cries/` for future
content work, but they are not `INCBIN`ed into the ROM until a real species
mapping is added.

## Important Files

Runtime code:

```text
audio/sampled_cry_player.asm
audio/sampled_cries.asm
audio.asm
home/audio.asm
home/pokemon.asm
home/mobile.asm
home/header.asm
home/delay.asm
engine/battle_anims/anim_commands.asm
audio/engine.asm
ram/hram.asm
ram/wram.asm
layout.link
constants/audio_constants.asm
```

Asset pipeline:

```text
tools/wav2pcm4.py
audio/sampled_cries/mastering_profiles.json
audio/sampled_cries/*.mm2
```

The ROM build consumes checked-in `.mm2` files. It does not run the converter
automatically.

## Asset Pipeline Overview

The source cry starts as a WAV file, usually from a Game Boy Advance direct
sample cry source such as pokeemerald.

The intended pipeline is:

```text
source WAV
  -> mastering profile
  -> mono float processing
  -> resample to ~10485.76 Hz
  -> 4-bit CH3 PCM nibbles
  -> minmax2 compression
  -> .mm2 file included by the ROM
```

The ROM never sees WAV files. It only sees minmax2-compressed block payloads.

## Mastering Profiles

Mastering settings live in:

```text
audio/sampled_cries/mastering_profiles.json
```

Keep this file in the repo. It is not a build input, but it is the reproducible
recipe for generating future `.mm2` assets.

The current default profile name is:

```text
17_v4_clarity_auto
```

The current alternate profile name is:

```text
14_v3_softlimit_4p0
```

The profile JSON can contain:

- source WAV paths
- target sample rate
- Prism-style volume multiplier settings
- auto gain settings
- DC removal
- high-pass filtering
- body boost
- preemphasis
- compressor settings
- limiter settings
- dither/noise shaping
- trim settings

The current mastering philosophy is:

- preserve intelligibility under CH3's 4-bit ceiling
- avoid extreme hard clipping when possible
- use per-cry profile tuning when needed
- prefer listening review over numeric metrics

The volume setting is not a magic loudness escape hatch. Testing showed CH3 hits
a practical playback ceiling, so mastering mostly affects clarity, distortion,
and perceived body rather than unlimited loudness.

## Converter CLI

The converter is:

```text
tools/wav2pcm4.py
```

It supports raw PCM4 and minmax2 output:

```sh
python3 -B tools/wav2pcm4.py INPUT.wav OUTPUT.mm2 \
  --profile-json audio/sampled_cries/mastering_profiles.json \
  --profile mudkip_17_v4_clarity_auto \
  --compression minmax2 \
  --preview-wav /private/tmp/mudkip_preview.wav \
  --report-json /private/tmp/mudkip_report.json
```

Useful options:

```text
--compression pcm4|minmax2
--profile-json PATH
--profile NAME
--preview-wav PATH
--report-json PATH
--mode linear|prism
--mastering baseline|softclip|compressor|compressor-preemphasis
```

Use `--compression minmax2` for ROM assets.

Use `--preview-wav` when you want to listen to the decoded 4-bit result before
building it into the ROM.

Use `--report-json` to capture diagnostics such as block count, duration, rail
rate, saturation rate, RMS, and quantization metrics.

## PCM4 Format

The Game Boy wave channel uses 4-bit samples. Raw PCM4 is stored as:

```text
2 samples per byte
32 samples per CH3 wave block
16 bytes per raw wave block
```

Silence is centered at nibble `8`.

The converter pads to full 32-sample wave blocks.

The current CH3 playback period is:

```asm
DEF SAMPLED_CRY_BLOCK_PERIOD_NORMAL EQU 200
DEF SAMPLED_CRY_CH3_PERIOD EQU 2048 - SAMPLED_CRY_BLOCK_PERIOD_NORMAL
```

This gives Prism-style playback around `10485.76 Hz`. Fainted sampled cries use
a Prism-style slower period, which changes pitch and duration together because
direct CH3 sample playback cannot independently time-stretch and pitch-shift at
runtime.

## Minmax2 Compression

The production codec is minmax2.

Each compressed block expands to one raw CH3 wave block:

```text
1 compressed block = 9 bytes compressed
1 decoded block    = 16 bytes raw PCM4
1 decoded block    = 32 4-bit samples
```

Block layout:

```text
byte 0: min/max nibble pair
bytes 1-8: 32 two-bit selectors, 4 selectors per byte
```

The first byte indexes a 16x16 min/max table:

```asm
MinMax2BitLevels:
for minlevel, 0, 16
    for maxlevel, 0, 16
        ...
```

For each block, the decoder derives four possible nibble levels:

```text
level 0 = min
level 1 = lower interpolation
level 2 = upper interpolation
level 3 = max
```

Each 2-bit selector chooses one of those four levels. The result is packed back
into raw PCM4 bytes and streamed into CH3 wave RAM.

Space cost:

```text
raw PCM4 block:     16 bytes
minmax2 block:       9 bytes
compression ratio:  56.25% of raw PCM4
```

The sampled cry header stores a 16-bit compressed block count:

```asm
MudkipSampledCry::
    dw (MudkipSampledCryEnd - MudkipSampledCryData) / 9
MudkipSampledCryData:
    INCBIN "audio/sampled_cries/mudkip.mm2"
MudkipSampledCryEnd:
    assert (MudkipSampledCryEnd - MudkipSampledCryData) % 9 == 0
```

The runtime treats this count as both the compressed block count remaining and
the decoded wave-block count to play.

## Pokecrystal16 Species Index Rules

This repo is based on pokecrystal16 concepts. Do not assume the runtime 8-bit
species ID is stable enough for direct table lookup.

Pokecrystal16 uses two species identifiers:

- a temporary 8-bit ID, allocated by the conversion table while the game runs
- a permanent 16-bit Pokemon index, used for stable table lookups

The sampled cry lookup must be keyed by the permanent species index, not the
temporary 8-bit ID.

The relevant conversion path is:

```asm
GetCryIndex::
    and a
    jr z, .no
    cp MON_TABLE_ENTRIES + 1
    jr nc, .no

    push hl
    call GetPokemonIndexFromID
    dec hl
    ld b, h
    ld c, l
    pop hl
    and a
    ret
```

`GetPokemonIndexFromID` converts the current 8-bit ID in `a` to a permanent
16-bit Pokemon index in `hl`.

`dec hl` converts that one-based permanent index to a zero-based table index.

`bc` then holds the zero-based permanent species index for cry lookup.

Future sampled cry code should preserve this rule:

```text
sampled cry table index = permanent Pokemon index - 1
```

Do not index sampled cries directly by the temporary 8-bit ID.

## Direct Species Lookup Table

The sampled cry metadata lives in:

```text
audio/sampled_cries.asm
```

The constants:

```asm
DEF NUM_SAMPLED_CRY_SLOTS EQU 60
DEF NO_SAMPLED_CRY EQU $ff
```

The direct index table:

```asm
SampledCryIndexByPokemon:
    table_width 1
DEF sampled_cry_mon = 1
rept NUM_POKEMON
    ...
endr
    assert_table_length NUM_POKEMON
```

This table has exactly one byte per permanent Pokemon index.

Each byte is either:

```text
$ff = no sampled cry, fall back to synthesized cry
0-59 = slot into SampledCryPointers
```

The pointer table:

```asm
SampledCryPointers:
    table_width 3
rept NUM_SAMPLED_CRY_SLOTS
    dba NullSampledCry
endr
    assert_table_length NUM_SAMPLED_CRY_SLOTS
```

Each pointer is a `dba` far pointer:

```text
bank, address low, address high
```

`TryLoadSampledCryBySpeciesIndex`:

- input: `bc = zero-based permanent species index`
- output carry set if a sampled cry exists
- output carry clear if caller should use the synth cry path
- stores selected sample metadata in HRAM:
  - `hSampledCryBank`
  - `hSampledCryAddress`

The helper rejects:

- indexes outside `NUM_POKEMON`
- table entries equal to `$ff`
- slots `>= NUM_SAMPLED_CRY_SLOTS`
- null sample pointers

## Adding A New Sampled Cry

High-level steps:

1. Add or update a profile in `audio/sampled_cries/mastering_profiles.json`.
2. Convert the source WAV to minmax2:

   ```sh
   python3 -B tools/wav2pcm4.py SOURCE.wav audio/sampled_cries/species.mm2 \
     --profile-json audio/sampled_cries/mastering_profiles.json \
     --profile species_17_v4_clarity_auto \
     --compression minmax2 \
     --preview-wav /private/tmp/species_preview.wav \
     --report-json /private/tmp/species_report.json
   ```

3. Add a sampled cry label and `INCBIN` in `audio/sampled_cries.asm`.
4. Add that label to `SampledCryPointers`.
5. Map the target species in `SampledCryIndexByPokemon`.
6. Build:

   ```sh
   make crystal
   ```

7. Test at least:

   - Pokemon stats page
   - send-out cry in battle
   - Growl or Roar if the species can use cry-based moves
   - Pokedex cry playback
   - a non-sampled Pokemon to confirm synth fallback still works

## Runtime Playback Overview

The sampled cry runtime is async from the caller's perspective.

The caller starts sampled playback and returns. A timer interrupt streams decoded
CH3 wave blocks. Mainline code periodically refills the rolling cache.

The major runtime stages are:

1. A cry request enters `PlayCry` or `LoadCry`.
2. The Pokemon species ID is converted to a zero-based permanent index.
3. `TryLoadSampledCryBySpeciesIndex` checks whether that species has sampled
   cry data.
4. If there is no sampled cry, the normal synthesized cry path runs.
5. If there is sampled data, `PlayLoadedSampledCry` calls
   `StartSampledCryAsync`.
6. Startup saves audio/timer state and decodes an initial cache window into
   WRAMX bank 4.
7. Startup copies the first decoded block to CH3 wave RAM and starts CH3.
8. The timer interrupt streams one decoded block per tick.
9. Mainline calls to `ServiceSampledCryAsync` refill more minmax2 blocks into
   the rolling cache.
10. When all blocks are played, the stop routine restores saved timer/audio
    state.

## Cry Entry Points

`home/audio.asm`:

- `PlayCry` checks sampled cry lookup before `PokemonCries`.
- `PlayLoadedSampledCry` switches to the sampled player bank and starts async
  playback.
- `UpdateSound` returns early while sampled playback is active so the normal
  audio engine does not stomp CH3 registers.
- `WaitSFX` waits for sampled playback as well as normal SFX.
- `ServiceSampledCryAsync` refills the decoded rolling cache.

`home/pokemon.asm`:

- `LoadCry` calls `GetCryIndex`.
- It then checks the sampled table before loading synthesized cry parameters.
- If a sampled cry exists, it returns carry set and `a = 1`.
- If not, it loads normal cry base/pitch/length from `PokemonCries`.

`engine/battle_anims/anim_commands.asm`:

- battle animation cry command checks whether `LoadCry` found sampled data
- if sampled, it calls `PlayLoadedSampledCry`
- `ServiceSampledCryAsync` is called during animation delay/OAM update points so
  the rolling cache keeps ahead of playback

`home/delay.asm`:

- `DelayFrame` services sampled cry async playback when it is not waiting in
  `halt`.

`home/header.asm` and `home/mobile.asm`:

- the timer interrupt vector jumps to `SampledCryTimer`
- if no sampled cry is active, `SampledCryTimer` falls through to `MobileTimer`
- if sampled playback is active, it services one CH3 block and returns with
  `reti`

## Timer And CH3 Playback

Timer vector:

```asm
SECTION "timer", ROM0[$0050]
    jp SampledCryTimer
```

`SampledCryTimer`:

- checks `hSampledCryTimer`
- if zero, jumps to `MobileTimer`
- if nonzero, banks to `SampledCry_AsyncTimerTick`
- streams the next decoded block
- returns via `reti`

Timer configuration:

```asm
DEF SAMPLED_CRY_BLOCK_PERIOD_NORMAL EQU 200
DEF SAMPLED_CRY_TIMER_RELOAD EQU 256 - SAMPLED_CRY_BLOCK_PERIOD_NORMAL
```

The timer uses 65,536 Hz mode:

```text
256 - 56 = 200 timer ticks per block
200 / 65536 seconds = ~3.0518 ms per block
```

Each CH3 block is 32 samples, so this matches approximately:

```text
32 samples / 10485.76 Hz = ~3.052 ms
```

CH3 setup:

```asm
SampledCry_RestartCH3:
    rAUD3ENA   = on
    rAUD3LEN   = 0
    rAUD3LEVEL = 100%
    rAUD3LOW/HIGH = 2048 - wSampledCryBlockPeriod with restart
```

`SampledCry_StartBlockTimer` uses `256 - wSampledCryBlockPeriod` for `rTMA`
and `rTIMA`. The timer period and CH3 period must always use the same
`wSampledCryBlockPeriod`; otherwise the player will swap wave RAM blocks out
of step with the hardware playback rate.

Output routing:

```asm
SampledCry_EnableOutput:
    rAUDVOL  = SAMPLED_CRY_MAX_VOLUME
    rAUDTERM = CH3 left/right routing from wCryTracks when stereo is enabled
```

If `wCryTracks` is zero or stereo is disabled, sampled cries route to both
speakers.

## Volume Policy

Current constants:

```asm
DEF MAX_VOLUME EQU AUDVOL_LEFT | AUDVOL_RIGHT
DEF NORMAL_MAX_VOLUME EQU $22
DEF NORMAL_LOW_VOLUME EQU $22
DEF SAMPLED_CRY_MAX_VOLUME EQU MAX_VOLUME
```

Normal game audio is intentionally lower so sampled cries can play at `$77` and
feel closer in relative loudness.

`Music_Volume` calls:

```asm
ClampNormalVolumeForSampledCry
```

That clamp preserves panning while capping each side at `2`:

```text
$77 -> $22
$70 -> $20
$07 -> $02
$11 -> $11
```

Sampled cry playback forces `rAUDVOL` to `$77` while the sample plays and
restores the previous hardware volume afterward.

## HRAM Layout

The sampled player uses the original 19-byte padding at the end of HRAM.

Current symbols from `pokecrystal.sym`:

```text
$ffee hSampledCryBank
$ffef hSampledCryAddress      ; 2 bytes: $ffef-$fff0
$fff1 hSampledCryTimer
$fff2 hSampledCryBlocks       ; 2 bytes: $fff2-$fff3
$fff4 hSampledCrySavedAUDVOL
$fff5 hSampledCrySavedAUDTERM
$fff6 hSampledCrySavedAUD3ENA
$fff7 hSampledCrySavedAUD3LEN
$fff8 hSampledCrySavedAUD3LEVEL
$fff9 hSampledCrySavedAUD3LOW
$fffa hSampledCrySavedAUD3HIGH
$fffb hSampledCrySavedIE
$fffc hSampledCrySavedTAC
$fffd hSampledCrySavedTMA
$fffe hSampledCrySavedTIMA
```

There are two bytes of padding before `hSampledCryBank`.

Meanings:

- `hSampledCryBank`: ROM bank containing the current sample data or player code
- `hSampledCryAddress`: dual-use pointer
  - before startup cache fill: compressed data pointer in ROM
  - during playback: decoded cache read pointer in WRAMX bank 4
- `hSampledCryTimer`: active flag; nonzero means sampled playback is running
- `hSampledCryBlocks`: decoded blocks still to play
- saved `AUD*`, `IE`, `TAC`, `TMA`, `TIMA`: restored when playback stops

Be careful adding HRAM. This implementation consumes nearly all of the old end
padding.

## WRAMX Bank 4 Layout

WRAMX bank 4 is reserved for sampled cry RAM:

```text
layout.link:
WRAMX 4
    "Sampled Cry RAM"
```

Current symbols from `pokecrystal.sym`:

```text
04:d000 wSampledCryDecodedBuffer
04:dff0 wSampledCryDecodedBufferEnd
```

Layout:

```asm
w4_d000::
wSampledCryDecodedBuffer::
wSampledCryWaveBuffer:: ds AUD3WAVE_SIZE
    ds SAMPLED_CRY_DECODED_BUFFER_SIZE - AUD3WAVE_SIZE
wSampledCryDecodedBufferEnd::
wSampledCryLevel0:: db
wSampledCryLevel1:: db
wSampledCryLevel2:: db
wSampledCryLevel3:: db
wSampledCryCacheCount:: db
wSampledCryCompressedBlocks:: dw
wSampledCryCompressedAddress:: dw
wSampledCryCacheWriteAddress:: dw
wSampledCryBlockPeriod:: db
    ds $1000 - (@ - w4_d000)
```

Important constants:

```asm
DEF SAMPLED_CRY_DECODED_BUFFER_SIZE EQU $0ff0
DEF SAMPLED_CRY_MAX_DECODED_BLOCKS EQU SAMPLED_CRY_DECODED_BUFFER_SIZE / AUD3WAVE_SIZE
DEF SAMPLED_CRY_CACHE_REFILL_BLOCKS EQU 8
```

The decoded buffer is:

```text
$0ff0 bytes
4080 bytes
255 raw CH3 blocks
8160 4-bit samples
about 0.778 seconds at 10485.76 Hz
```

The remaining 16 bytes at `$dff0-$dfff` hold decoder/cache state.

`w4_d000` remains as a compatibility alias for the old bank-4 base.

## Rolling Cache Behavior

Startup:

1. `StartSampledCryAsync` saves audio/timer state.
2. It switches `rSVBK` to bank 4.
3. `SampledCry_InitRollingCache` copies compressed block count/address into
   WRAMX state.
4. `SampledCry_FillRollingCache` decodes up to 255 blocks.
5. The first decoded block is copied to CH3 wave RAM.
6. CH3 and timer playback begin.

Timer tick:

1. `SampledCry_AsyncTimerTick` switches to WRAMX bank 4.
2. If no remaining blocks or no decoded cache blocks remain, playback stops.
3. Otherwise it copies one 16-byte decoded block to CH3 wave RAM.
4. It restarts CH3 and decrements cache/remaining block counts.

Mainline refill:

1. `ServiceSampledCryAsync` checks `hSampledCryTimer`.
2. If active, it switches to WRAMX bank 4.
3. It decodes up to `SAMPLED_CRY_CACHE_REFILL_BLOCKS` more compressed blocks.
4. Current refill cap is `8` blocks per service call.

The cache is circular:

- read pointer is `hSampledCryAddress`
- write pointer is `wSampledCryCacheWriteAddress`
- both wrap back to `wSampledCryDecodedBuffer` at `wSampledCryDecodedBufferEnd`
- `wSampledCryCacheCount` tracks decoded blocks available

## Large Cries

Cries longer than 255 decoded blocks can still play because the buffer is a
rolling cache, not a full predecode requirement.

The system must refill fast enough to stay ahead of the timer. Refills happen in
foreground/service points, not inside VBlank mode 7.

Known practical result:

- Wailord worked as a stress case with the rolling cache approach.
- Long cries may need careful testing for battle pacing and cry-based moves.

If a future cry underruns:

1. Confirm `ServiceSampledCryAsync` is being called in the active code path.
2. Increase `SAMPLED_CRY_CACHE_REFILL_BLOCKS` cautiously.
3. Add a service call to the specific long-running foreground loop.
4. Avoid heavy decode work inside the timer interrupt.

## Battle Behavior

Sampled cries are currently async. Battle logic can continue while a cry plays.

Send-out, Growl/Roar, and fainted paths should be tested for every new sampled
species.

Important details:

- battle cry command uses `LoadCry`
- normal sampled cries are played through `PlayLoadedSampledCry`
- fainted sampled cries are played through `PlayLoadedSampledCryWithPeriod`
- panning is controlled through `wCryTracks`
- `SampledCry_GetAUDTERM` routes CH3 according to `wCryTracks` when stereo is
  enabled
- `WaitSFX` waits for sampled playback, but not every battle animation command
  is inherently blocked by the sampled player

Fainted cry behavior follows Prism's split between synth and sampled cries:

```asm
DEF SAMPLED_CRY_BLOCK_PERIOD_NORMAL EQU 200
DEF SAMPLED_CRY_BLOCK_PERIOD_FAINTED EQU 213
```

Synth fainted cries multiply pitch by roughly `90%` and add roughly `11%` of
their length back onto the length value. Sampled fainted cries use the slower
fainted block period instead. The current sampled period is tuned closer to
Emerald's fainted cry pitch ratio than Prism's `10/9` slowdown. Growl/Roar
sampled cries use the normal period.

For very long cries, battle scripting may advance before the cry ends unless the
caller explicitly waits. This is acceptable for some paths and undesirable for
others; test by move/use case.

## Audio Engine Ownership During Playback

While sampled playback is active:

- `UpdateSound` returns early
- the timer interrupt owns CH3 wave streaming
- CH3 registers are controlled by sampled playback
- sampled playback owns `rAUDVOL` and `rAUDTERM`

On start, the player saves:

- `rAUDVOL`
- `rAUDTERM`
- CH3 registers
- timer registers
- interrupt enable register

On stop, it restores them.

This is why normal audio should resume after playback. If future changes cause
BGM/SFX disruption, inspect the save/restore boundary first.

## ROM Placement

`audio.asm` includes:

```asm
SECTION "Sampled Cries", ROMX

INCLUDE "audio/sampled_cry_player.asm"
INCLUDE "audio/sampled_cries.asm"
```

The section is movable. The current no-active-mappings build places the compact
runtime/metadata section in ROMX bank `$01` / decimal `1`:

```text
01:74c0 StartSampledCryAsync
01:7c99 TryLoadSampledCryBySpeciesIndex
01:7ce5 SampledCryIndexByPokemon
01:7de0 SampledCryPointers
```

Do not rely on that bank being permanent unless the section is pinned later. The
code uses `BANK(...)` and `dba` pointers, so bank movement is okay as long as all
far calls/pointers remain correct. Adding real `INCBIN`ed sample payloads can
move this section again.

## Cleanup Before Production Content

Before this becomes final content:

1. Add only real species mappings to `SampledCryIndexByPokemon`.
2. Add only real sampled cry labels to `SampledCryPointers`.
3. Keep `tools/wav2pcm4.py`.
4. Keep `audio/sampled_cries/mastering_profiles.json`.
5. Build with `make crystal`.
6. Check `pokecrystal.map` for ROM0, ROMX, HRAM, and WRAMX usage.

If a sampled cry label remains `INCBIN`ed, it still costs ROM space even if no
species points to it.

## Recommended Regression Matrix

After any sampled cry runtime change:

```sh
make crystal
```

Then test in SameBoy or SameBoy core:

- stats page opens for each mapped sampled species
- frontpic appears promptly
- cry plays fully
- no tile/palette/OAM corruption
- battle send-out cry plays
- Growl/Roar cry path plays
- Tackle or another scanline/BG-effect move still renders correctly
- non-sampled species still use synthesized cries
- BGM/SFX resume after sampled cry playback
- stereo panning behaves correctly in battle
- long stress cry, if relevant, does not underrun

When debugging with SameBoy:

- use `pokecrystal.sym`
- watch HRAM active flag `hSampledCryTimer`
- inspect WRAMX bank 4 cache state if underruns are suspected

Useful symbols:

```text
hSampledCryTimer
hSampledCryBlocks
wSampledCryCacheCount
wSampledCryCompressedBlocks
wSampledCryCompressedAddress
wSampledCryCacheWriteAddress
```

## Common Failure Modes

Sample is silent:

- species table points to `$ff` or `NullSampledCry`
- `.mm2` was not `INCBIN`ed
- block count is zero
- CH3 routing in `wCryTracks` masks output unexpectedly

Sample is garbled:

- wrong compression selected during conversion
- `.mm2` is not a multiple of 9 bytes
- decoder and encoder formats do not match
- wrong bank/address loaded into `hSampledCryBank/address`

Sample cuts off:

- `hSampledCryBlocks` reaches zero too early
- compressed block count header is wrong
- cache underrun stops playback
- a caller explicitly stops or replaces the current sampled cry

Graphics hiccup or corruption:

- too much decode work is happening in a timing-sensitive loop
- add/refine service points carefully
- avoid decoding inside timer interrupt beyond one raw block stream

Normal audio too loud relative to sampled cries:

- check `NORMAL_MAX_VOLUME`
- check `ClampNormalVolumeForSampledCry`
- search for direct writes to `wVolume` or `rAUDVOL`

Sampled cry too quiet:

- check mastering profile and `prism_vol`
- remember CH3 has a practical volume ceiling
- raising input gain past the ceiling may only add crunch, not perceived volume

## Future Work

Potential future improvements:

- replace temporary 60-slot table entries with real species mappings
- add a small generator for `audio/sampled_cries.asm`
- group sampled cry data across multiple ROMX banks when the set grows
- add build-time validation that every `.mm2` file length is a multiple of 9
- add per-cry reports from `wav2pcm4.py` to review ROM space and quality
- decide per move/path whether long sampled cries should block battle logic
- tune mastering per final species instead of applying one universal profile
