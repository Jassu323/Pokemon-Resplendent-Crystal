# First SameBoy Cost-Model Calibration Captures

Status: diagnosis and partial calibration only. No runtime or host-model implementation changes made during this review.

## Provenance

- Inputs: `Luxray - Test 1.txt` through `Luxray - Test 3.txt`, and `Weavile - Test 1.txt` through `Weavile - Test 3.txt`, from `/Users/jakeadams/Downloads`.
- Both the repository ROM and `/Applications/SameBoy/Games/pokecrystal.gbc` match SHA-256 `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`, as checked before this testing round and again during review. This checks disk images, not the emulator's in-memory image.
- All captures are the expected version-6, 139-byte trace format at `$c758`, with the expected `$a0:$67fc` underflow breakpoint and matching call paths.
- All KEY1 readings are `$7e`: normal CPU speed, no speed switch requested. All captured VRAM/WRAM selections are `$fe`/`$f9`, selecting bank 0/bank 1 respectively at this breakpoint.
- Parsed outputs are `weavile-1.json` through `weavile-3.json`, and `luxray-1.json` through `luxray-3.json`, beside this report.
- There are 32 supplied snapshots. Weavile test 2 BP3/BP4 and BP7/BP8 are duplicate states, including the pre-increment underflow counter. They are not evidence of additional misses. There are 30 distinct underflow snapshots.

## Why the Stop Precedes Visible Corruption

`Pokedex_CommitDescriptionAnimation` tests the upcoming display deadline, records the failure, and calls `Pokedex_CountAnimationUnderflow`. The breakpoint is at that counter routine's entry. It has not yet called `Pokedex_BuildAnimationUnderflowMap` or queued that map for publication. Stopping before the visible error is expected and does not invalidate these captures. No video is required to classify these failures.

## Repeatable First Failures

Deadlines below are display intervals after the first animation-map publication, not from the player's input. Event numbers are one-based timeline entries; frame IDs refer to the distinct source poses.

| Pokemon | Attempts | First missed event | Frame ID | Deadline | Uploaded / needed | Decoded dictionary |
|---|---:|---:|---:|---:|---:|---:|
| Weavile | 3/3 | 2 | 2 | +3 | 0 / 18 | 128 / 128 |
| Luxray | 3/3 | 7 | 2 | +29 | 0 / 21 | 134 / 134 |

Both dictionaries are already completely decoded. More startup dictionary lead cannot fix these particular failures.

### Weavile

All three traces show the frame-2 preparation taking 62 scanlines, beginning at LY 74 and ending at LY 136. A producer call follows around LY 140, but it consumes an idle action. The next retained producer call is two VBlank-counter increments later, around LY 67-68. There is no producer call in the intervening display interval.

At failure, the compact-schedule cursor is `$5538`, the run count is zero, and the next byte is `$c1`: one upload call. The first two scheduled idle calls have occurred, but the upload scheduled for the third opportunity has not. Publication time has advanced farther than completed schedule work.

### Luxray

All three first-miss traces show four successive producer calls with no decode or upload, while frame 2 still needs 21 tiles. The dictionary is complete and the stage is valid but not ready. At failure the schedule cursor is `$4c58`, run count zero, with `$c2` next: two upload calls. The runtime has just finished its long idle run and has not yet reached those uploads.

There is no missing producer interval within the last four retained calls. The drift was accumulated earlier; the five-record ring does not retain the original divergence. The unchanged first event/frame and cursor across all attempts make the mismatch repeatable, not an intermittent dictionary-content problem.

## Later Failures

Weavile's six distinct failures recur at events 2, 3, 4, 6, 8 and 9: deadlines +3, +6, +8, +16, +24 and +30. Uploaded counts are respectively 0/18, 20/27, 20/24, 0/18, 0/24 and 20/25.

Luxray's four failures recur at events 7, 8, 10 and 12: deadlines +29, +34, +44 and +77. Uploaded counts are 0/21, 20/49, 20/49 and 0/17.

These later misses are useful for observing operation costs, but are not independent clean-run root-cause tests: the earlier underflow maps change residency and subsequent execution.

Luxray exposes a real upload launch boundary. Its 20-tile requests arrive at the wrapper near LY 107-108. The helper requires LY < 108 when it actually performs the eligibility check, after wrapper/setup work. Requests that miss that check wait through the rest of the interval, then finish near LY 20 in the next interval. The trace records roughly 66-67 scanlines for those HDMA phases, versus about 21 scanlines for one otherwise similar request that launches in time. The elapsed HDMA phase includes waiting and interrupts; it is not all DMA CPU halt time.

## Host-Model Calibration Gap

The current model does not reproduce the complete first-miss history. Depending on initial phase, it can reproduce Weavile's frame-2 failure or predict a later failure. It does not reproduce Luxray's first failure at event 7: current cold/native scenarios either miss earlier or predict no miss. Matching a species' general failure is not calibration.

A specific omitted hardware cost is now confirmed: LCD STAT interrupts.

- Captured STAT values have bit 3 set, enabling HBlank interrupt requests.
- Initialization configures mode-0 STAT requests and `IE_DEFAULT` includes the STAT interrupt.
- Follow-up at the first Luxray breakpoint: IE (`$ffff`) is `$0f`, and `hLCDCPointer` (`$ffc6`) is `$00`. STAT interrupt delivery is enabled and the handler takes its short return path. This follow-up confirms the cause of missing budget; the precise per-operation interruption history remains unrecorded.
- With `hLCDCPointer == 0`, the LCD handler still executes a 72-T return path. Hardware entry adds 20 T and the interrupt-vector jump adds 16 T: 108 T per delivered interrupt.
- At one delivery per visible scanline, that is nominally 15,552 T per display interval, about 22.1% of its normal-speed CPU budget. Actual delivery can differ while other interrupts mask/coalesce requests. This is not a guaranteed amount of recoverable time.

The correspondence with elapsed measurements is strong, without fitting arbitrary per-species constants:

| Operation | Linked instruction-only cost between relevant trace points | Observed elapsed | Rough estimate including short LCD handler and sampled-audio IRQ load |
|---|---:|---:|---:|
| Weavile frame-2 preparation | 4.30 ms | 6.74 ms, all three | 6.64 ms |
| Luxray frame-3 preparation | 8.19 ms | 12.39-12.83 ms | 12.64 ms |
| 20-tile gather, inner loop only | 4.57 ms | 6.96-7.50 ms including wrappers | 7.05 ms before wrappers |

The rough estimate divides CPU work by the average visible-period availability after 108 T/scanline LCD overhead and the sampled-audio ISR load. It is explanatory, not a cycle-accurate replay. Recorded elapsed ranges have scanline uncertainty and can include VBlank/other work. The model's sampled-timer cost also omits the 16-T interrupt-vector jump, a much smaller accounting correction.

## Next Step

The requested follow-up has been supplied at Luxray's first breakpoint:

```text
print/x [$ffff]
= $0f
x/1 $0:$ffc6
00:ffc6: 00
```

IE bit 1 confirms STAT interrupt delivery is enabled. `$ffc6` is `hLCDCPointer`; zero selects the short handler above. No additional full suite or video is needed at this stage.

The next proposed change is to correct the host model's interrupt accounting and compare the recorded component spans and first-miss history again. Keep uncertainty explicit for owner-loop work, VBlank work and initial timer phase. Do not compensate for missing interrupt work with a species-specific timing multiplier.

The runtime direction remains shared display-time deadlines, independently tracked completed work, and early preparation when storage is safe. The captures do not prove sufficient CPU headroom for every species or justify simply increasing quotas. Whether to suppress unused LCD interrupts within the Selected screen is a separate potential optimization requiring an ownership/restore audit; no such runtime change was made here.
