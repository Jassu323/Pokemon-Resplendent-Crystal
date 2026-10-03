# Pokedex Info Return Committed Record Preflight

2026-10-03. Accepted successor to the [VRAM readback preflight](pokedex_info_return_preflight.md)
for `DEX-INFO-01`, now integrated into production at the user's request. Two atlas-specific page
records eliminate VRAM readback while preserving the actually displayed Info
page during Listing cache repair. Most affected B-returns add approximately
three display intervals (50ms), instead of nine (151ms). Unaliased pages no
longer incur the previous three-interval snapshot penalty.

There is another measured cost: bounded record preparation adds approximately
two display intervals (33.49ms) when activating Info's Stats page. This is an
accepted tradeoff, not a claim of a free or latency-neutral preservation fix.
The hybrid Listing grid, full-cache validity rules, animation scheduler,
sampled-cry decoder, evolution data and pagination are not redesigned here.

## Build Identity

```text
Pre-fix ROM: 2928c51263a162d573f4ee96204aca768f83ffb9aff1fe418a7af3de0ee76346
Pre-fix SYM: 3c1ee132610963d7f37debd1548b979d1c0a02401bb6930084de195f4136af92
Pre-fix MAP: 00a269639d0fd6d1b0383478ad2eb8bf5783dd162e6da4e8e134dfc8ddd991ee
Readback prototype: 7d45017926717f2169318f5fb2df9ed50707c0a481b104666c703c92bdb6a374
Committed record prototype: 404909c990c9df0e34a9a05ab0ec6cfcb9ceda3c808133693501d8334bc13009
```

The original preflight cartridge, matching symbols/map, private source copies, checkpoints,
screenshots and raw reports are under ignored
`build/dex-info-return-records-20261003/`. The cartridge is
`pokecrystal-info-return-records.gbc`. A fresh second recipe run reproduces
its hash. During that preflight, the production ROM/SYM/MAP hashes and all
3,004 production assembly/build sources remained unchanged. Production now
uses the committed-record cartridge identity above; ROM/SYM/MAP each match
the accepted prototype byte-for-byte. The user's battery and SameBoy states
were not edited in either pass.

## Records And Ownership

Each record contains 224 bytes for lower tilemap rows 9-15, eighty bytes for
the forty possible immutable ROM glyph pointers, and a one-byte glyph count.
There is one record per atlas. The existing active-atlas selector identifies
the committed Info record; a new visible-Info flag distinguishes an actually
published Info page from a requested or partially prepared tab.

The record is prepared after the inactive atlas's glyph uploads, before READY,
in six slices of at most 64 bytes. The existing mainline admission and three
slices per service call apply. The row cursor is reused; no extra copying
cursor or large interrupt-time copy is added. Across the 373-species settled
pass, the new slice costs at most 4,356 T cycles, including the measured
interrupt work. Blank uncaught pages also obtain a consistent record.

Info publication selects the already prepared record alongside the active
atlas, while interrupts are disabled. Initial species reveal uses the same
selection. Actual Description or Listing publication clears visible-Info
ownership. Cancellation alone does not change that flag or the active selector:
canceling the next job cannot discard the old page's still-visible record.

The two records are not copies of the continually mutable workspaces. Info's
owner map, glyph pointers and graphics can be overwritten for an incoming
page while the other record remains valid. This is what makes early B during
preparation safe without taking a hardware VRAM snapshot.

## B Return Transaction

1. Cancel text/Info jobs, mark Selected LEAVING, and cancel its cry/portrait
   producers before reusing their temporary upload payload.
2. Skip preservation if the Listing cache is clean, if Info is not actually
   visible, or if the visible atlas is already unaliased A.
3. For visible atlas B, hold hardware OAM and automatic map/palette work.
   Copy its committed tilemap and ROM pointers into the existing Info/owner
   workspaces. Reconstruct only the recorded glyph count from ROM, using the
   existing copy and bounded upload routines. Upload to unaliased atlas A.
4. Remap the captured B tile IDs to A, preserving attributes, palettes,
   minisprite/endpoint OAM and all permanent shell/title/page cells.
5. The existing private early-VBlank owner publishes the seven tilemap rows
   and acknowledges completion. No new attribute, palette or OAM transfer is
   needed. The old glyphs remain visible until their replacements are ready.
6. Run the unchanged complete-cache Listing repair and reveal. Its frame-0
   uploads no longer target any displayed Info glyphs.

Within these Info rows, only atlas-B glyphs use IDs below forty; all permanent
bank-0 cells are above that range. This is a local renderer invariant, not a
general tilemap remapper. The host oracle verifies both translated glyph
bytes and unchanged permanent cells. A future renderer that introduces lower
bank-0 IDs must revise the remapping rule or capture their ownership explicitly.

## Return Measurements

Normal-speed SameBoy emulated time, 70,224 T cycles per display interval,
approximately 16.74ms. Each entry starts when the host supplies B and ends at
the Listing reveal acknowledgement. The table shows **ms / display-interval
equivalent**; fractions reflect the scanline at which input is supplied and
reveal completes, not fractional rendered images. Three identical repetitions
were recorded for every focused case. Raw cycles, crossed display boundaries
and Leave-to-reveal timing are retained in `comparison.json`.
The table's Production column is the frozen pre-fix baseline; Committed
records is the implementation now integrated into production.

| Path | Production | Readback prototype | Committed records |
| --- | ---: | ---: | ---: |
| Chikorita Description | 171.21 / 10.23 | 171.21 / 10.23 | 171.04 / 10.22 |
| Chikorita Stats, B | 238.10 / 14.22 | 388.76 / 23.22 | 288.19 / 17.21 |
| Chikorita Evolutions, A | 238.08 / 14.22 | 288.31 / 17.22 | 237.99 / 14.21 |
| Tyrogue P.3, B | 254.82 / 15.22 | 405.52 / 24.22 | 288.29 / 17.22 |
| Eevee P.4, A | 254.84 / 15.22 | 305.07 / 18.22 | 254.72 / 15.21 |
| Chansey Stats, B | 254.88 / 15.22 | 405.55 / 24.22 | 304.99 / 18.22 |
| Blissey Stats, B | 254.80 / 15.22 | 405.51 / 24.22 | 306.12 / 18.28 |
| Dusknoir Stats, active-entry case | 246.22 / 14.71 | 396.88 / 23.70 | 296.35 / 17.70 |
| Kyogre Stats, active-entry case | 246.15 / 14.70 | 396.76 / 23.70 | 296.30 / 17.70 |
| Info retained, Chikorita -> Bayleef, A | 238.10 / 14.22 | 288.33 / 17.22 | 237.93 / 14.21 |
| Info retained, Chikorita -> Bayleef -> Meganium, B | 238.10 / 14.22 | 388.80 / 23.22 | 288.24 / 17.22 |

Most atlas-B paths add about 50ms/three intervals versus production; Tyrogue
adds about 33.47ms/two intervals because its smaller committed glyph set
finishes sooner. Atlas-A returns are effectively unchanged. The prior
readback prototype was approximately 100ms slower on common B cases and
50ms slower on A cases. Sub-millisecond differences on unchanged paths are
instruction/polling/interrupt phase effects, not a meaningful speedup claim.

The callback counts agree: Chikorita Stats crosses 14 / 23 / 17 display
boundaries in production/readback/records; Dusknoir crosses 15 / 24 / 18.
Its fractional elapsed-time values differ because B arrives later in its
current display interval.

The two additional record-preparation intervals are **before** B is supplied
and are not folded into these return measurements. Across all 373 settled
Stats activations, their measured increase is 1.99937-2.00080 intervals,
median 2.00006. Chikorita and Dusknoir each change from approximately eleven
to thirteen intervals in the same normal-input preparation test. Internal
species reveal is not consistently two intervals slower: the extra CPU work
interacts with existing transition waits. Its median phase-shifted change
is near zero, with individual paired replays up to 1.94 intervals slower.
These measurements do not justify promising phase-independent paging latency.

## Regression Results

| Suite | Result |
| --- | --- |
| Focused production/prototype returns, 32 paths x 3 | 96/96 candidate passes |
| Original pending-Info/Description cancellation matrix | 150/150 candidate passes |
| Additional cancellation ages through interval 24 | 100/100 candidate passes |
| Full Info content, exact playback, internal paging, Description restoration and B-return | 373/373 species, 746 complete playback audits |
| Full rapid-input matrix, five families x four phases | 7,459/7,460; same existing production badge defect |
| Seen but uncaught controls, eight species x two phases | 16/16 passes |
| Sparse-seen returns, navigation, wrap and re-entry | 4/4 passes |
| Host observer disabled/enabled | 5/5 identical cycles, state, palettes, maps and final pixels |
| Unit/linked/oracle checks | 48/48 passes |
| Second fresh private recipe | Byte-identical cartridge |

Twenty-one of 96 production comparisons corrupt their outgoing panel. None
of the candidate comparisons do. Glyph-byte translation, permanent cells,
attributes, palettes and actual OAM match across relocation; no visible B
reference survives before cache uploads. No new animation deadline miss or
premature sampled-cry exhaustion is detected. Intentional cry cancellation
is excluded from premature-exhaustion acceptance.

The cancellation sweeps cover every integer age 0-24 on five species for both
next-Info and Info-to-Description preparation. Ten saved B-entry checkpoints
are explicitly verified to be inside the new record-copy state, rather than
merely before or after it. Final Listing cache bytes/tags/presence, palettes,
scrolling/wrapping and re-entry pass after each return.

The sparse fixture contains only ten caught species and derives seen flags
from those, retaining the final order entry. It genuinely contains unseen
holes. The earlier prototype's nominal sparse fixture came from an all-caught
source and had no holes; that limitation is corrected in this pass. All save
edits here are private generated fixtures, not the user's battery.

`DEX-INFO-04` remains: Rhyperior, phase 0, immediate Info -> Description
loses the lower `P.` badge. The sole stress failure matches the old prototype
and previously verified production replay exactly. The return helper has not
run when it occurs. No unrelated fix or suppressed badge check is included.
See the [existing cause and fix direction](pokedex_info_return_preflight.md#existing-badge-failure).

## Linked Resource Costs

| Resource | Added versus pre-fix production |
| --- | ---: |
| Info bank `$a6` | 273 ROMX bytes |
| Publisher/routing bank `$77` | 85 ROMX bytes |
| Leave integration bank `$a0` | 6 ROMX bytes |
| Total ROMX | **364 bytes**, 84 more than the readback prototype |
| Bank-3 Dex-owned workspace | **611 bytes** reused within the Tower union |
| Physical WRAMX allocation | **0 bytes** |
| ROM0, WRAM0, HRAM, SRAM, VRAM | **0 bytes** |

Records A/B occupy `$d8d5-$da05` / `$da06-$db36`; visible-Info is `$db37`.
The workspace ends at `$db38`, leaving 200 bytes before the conservative
`$dc00` boundary. The physical union remains `$d000-$dfff`; all pre-existing
RAM symbols retain their locations. No animation dictionary, sampled-cry,
window-stack or persistent game-data buffer is borrowed. The larger Reset
clears these new owner-local fields within the already reserved overlay.

The records may be shared with future mutually exclusive lower tabs; they
are not spare independent capacity to allocate again for each tab. Overall
cart cost is only the 364 linked ROMX bytes, without another ROMX bank.

## Reproduction

```sh
PYTHONPATH=tools python3 -B -m dex_timing.info_return_preflight \
  --mode records --output build/dex-info-return-records-fresh --jobs 8 \
  --source build/dex-info-return-records-20261003/baseline

PYTHONPATH=tools python3 -B -m dex_timing.info_ui \
  --rom build/dex-info-return-records-fresh/pokecrystal-info-return-records.gbc \
  --sym build/dex-info-return-records-fresh/pokecrystal-info-return-records.sym \
  --battery build/dex-info-placement/fixture.sav \
  --output build/dex-info-return-records-fresh/runtime --phases settled --jobs 8

PYTHONPATH=tools python3 -B -m dex_timing.info_return_regression \
  --build build/dex-info-return-records-fresh \
  --checkpoints build/dex-info-return-records-fresh/runtime \
  --output build/dex-info-return-records-fresh/paired-full --repeat 3 --jobs 8
```

Run the original `--cancel-sweep --repeat 1` separately, then another output
with `--cancel-ages 13 14 15 17 18 19 20 21 22 23`. Run the unchanged full
`info_ui --stress --phases 0 8 32 settled` matrix, uncaught controls and
observer/sparse Listing checks as in the prior preflight. The comparison
tool `dex_timing.info_return_summary --build ... --previous ...` audits saved
reports and emits all 32 timing comparisons plus per-species preparation costs.
Generated output remains ignored.

## Assessment

This is a materially faster, resource-contained retained-screen fix.
It preserves cancellation correctness without a new grid/cache paradigm or
VRAM readback. The user accepted its remaining 2-3 return intervals and two
Info-preparation intervals and requested production integration. Further
performance work is deferred to `DEX-PERF-02` after the other Dex components
are situated. The alternative lower-panel mask has not been implemented
or benchmarked and remains a different presentation/cost tradeoff.

## Production Integration

The user accepted this retained-page transaction on 2026-10-03 and explicitly
deferred performance refinement until the other Dex components are situated.
The helpers now live in `engine/pokedex/pokedex_info_return.asm` and the
existing `pokedex_info_publish.asm`; no production INCLUDE references the
private probes. The linked production ROM, symbols and map reproduce the
accepted prototype exactly:

```text
ROM: 404909c990c9df0e34a9a05ab0ec6cfcb9ceda3c808133693501d8334bc13009
SYM: 583417e4b47ab9362bc46301385a1a3457f9e8f3416958ecee939260262f65b8
MAP: a466c4b667563c99ff05363eecac6f73aa7701301b137b6b4b2602eb5a418b47
```

Production regressions use fresh normal-input checkpoints and copied private
batteries under ignored `build/dex-info-return-production-20261003/`:

| Suite | Result |
| --- | --- |
| Info content, internal paging and exact playback, all species | 373/373; 746 complete playback audits |
| Focused B-returns against frozen pre-fix baseline | 96/96, no outgoing panel corruption |
| Info/Description cancellation ages 0-24 | 250/250, retained pixels and repaired Listing cache/navigation |
| Rapid input, all species at four phases and five families | 7,459/7,460; only the unchanged Rhyperior badge defect |
| Uncaught controls | 16/16 |
| Genuine sparse Listing, wrap/navigation/re-entry | 4/4 |
| Host observer controls | 5/5 identical cycle/state/palette/map/pixel results |
| Maintained unit/linked/oracle checks | 197/197 |
| Authored timeline and sampled decoder asset checks | 399 structures; 65,536 lookup combinations; 122 cries |
| Historical build recipe from frozen source | Byte-identical accepted cartridge |

No new animation deadline miss, premature sampled-cry exhaustion or return
ownership regression is detected. `DEX-INFO-01` is closed; `DEX-INFO-04`
remains independently open. The main Info system/VRAM documents carry the
current record lifetime, allocation and return sequence, and `DEX-PERF-02`
retains both return and preparation costs as optimization baselines.

The paired tool uses the build manifest's frozen baseline ROM instead of
assuming today's production is still the pre-fix version. Supply
`--candidate-rom pokecrystal.gbc` to test production explicitly. Historical
prototype generation uses `--source` with the saved pre-integration baseline;
the current integrated tree is intentionally rejected as a preflight source.
The comparison tool likewise reads historical costs from the frozen map and
recognizes byte-identical production promotion rather than flagging it as an
unexpected production mutation.

A full clean production rebuild and subsequent asset verification retain the
same ROM/SYM/MAP identities. One linked-test invocation overlapped the asset
target's relink and read a temporarily incomplete ROM; rerunning only after
the build finished passes all 197 checks. This was a host invocation ordering
error, not a cartridge failure. Build and linked-ROM acceptance must run
sequentially even when independent replay workers run concurrently.
