# Pokedex Info Return Relocation Preflight

2026-10-03. Private prototype for `DEX-INFO-01`, not a production fix.
Relocating the actually visible Info glyphs preserves the outgoing panel and
keeps the Listing's complete-cache ownership rule. The prototype passes the
focused returns, cancellation checks and playback regressions, but adds
approximately 50ms to unaliased Info returns and 151ms to aliased returns.
That latency is a real tradeoff, not hidden or eliminated by correct pixels.

The user rejected that latency. The [committed-record successor](pokedex_info_return_records_preflight.md)
reuses bank-3 Tower storage and removes VRAM readback, reducing common
aliased-return overhead to about 50ms and unaliased-return overhead to nearly
zero, with a separately measured Info-preparation cost. That successor is now
integrated into production. This report remains the historical readback
benchmark, not the current implementation.

Production assembly, `pokecrystal.gbc`, its symbols/map and the user's battery
save were not modified. Evolution data and shared pagination are outside this
preflight. The hybrid BG/OBJ Listing grid is unchanged.

## Build Identity

```text
Production ROM: 2928c51263a162d573f4ee96204aca768f83ffb9aff1fe418a7af3de0ee76346
Production SYM: 3c1ee132610963d7f37debd1548b979d1c0a02401bb6930084de195f4136af92
Production MAP: 00a269639d0fd6d1b0383478ad2eb8bf5783dd162e6da4e8e134dfc8ddd991ee
Prototype ROM: 7d45017926717f2169318f5fb2df9ed50707c0a481b104666c703c92bdb6a374
```

The separate cartridge and matching symbols/map are under
`build/dex-info-return-relocation-20261003/`, named
`pokecrystal-info-return-relocation.*`. This entire output is ignored.
`info_return_preflight.py` snapshots the current working tree, rebuilds an
isolated baseline and requires it to match production before applying exact,
guarded source transformations to a second private source copy. A second
fresh recipe run reproduced the prototype ROM byte-for-byte.

## Transaction

1. Cancel Description/Info jobs and mark Selected LEAVING. Stop its cry and
   portrait producer before borrowing any upload scratch.
2. If Info never dirtied the Listing cache, skip preservation. Otherwise hold
   hardware OAM, automatic BG-map work and palette updates. Snapshot the
   **actual** lower VRAM tilemap and attributes, rows 9-15, into the existing
   owner buffers. Unfinished jobs may have modified their previous contents,
   so those contents are not assumed to describe the visible screen.
3. Scan for bank-1 tile IDs `$00-$27`, the borrowed Listing frame-0/Info-B
   atlas. If none are visible, proceed to ordinary restoration.
4. Read all 40 Info-B glyphs, 640 bytes, into the existing bank-3 Info GFX
   workspace. Upload them to the scattered, unaliased Info-A cells using the
   existing bounded uploader. The original glyphs remain visible throughout.
5. Remap the copied tile IDs to their Info-A equivalents. All destination
   cells are in the same VRAM bank, so attributes/palettes do not change.
6. Queue a private owner transition. An admitted early VBlank publishes only
   the seven lower tilemap rows, then acknowledges completion. No OAM,
   palette or attribute transaction is necessary for this remap.
7. Restore the ordinary Listing cache, maps, palettes, OAM and viewport using
   the existing full-cache path. Its frame-0 uploads can no longer overwrite
   visible Info text. No partial-cache validity rules are introduced.

Per-byte VRAM reads exclude interrupts between the access check and the read;
interrupts remain possible between bytes. The caller has IME enabled. OAM
remains held until the ordinary Listing reveal. Thus evolution minis and the
HP endpoint keep their last displayed pixels rather than reading overwritten
shadow OAM during the return.

## Measurements

Normal-speed SameBoy T cycles, 70,224 cycles per display interval. Measurements
are emulated time, not host execution time. Three identical repeated returns
were measured for each of 32 focused paths.

The following starts at the B input supplied by the host and ends at the
Listing reveal acknowledgement. It includes the owner's input-polling delay.
Physical-button polling phase can vary during manual play. All numbers are
rounded milliseconds; the raw reports retain cycles and display-frame data.

| Path | Production | Prototype | Added |
| --- | ---: | ---: | ---: |
| Chikorita Description | 171.208 | 171.213 | 0.005 |
| Chikorita Info Stats, atlas B | 238.095 | 388.758 | 150.663 |
| Chikorita Info Evolutions, atlas A | 238.078 | 288.311 | 50.233 |
| Tyrogue Info P.3, atlas B | 254.818 | 405.518 | 150.700 |
| Eevee Info P.4, atlas A | 254.835 | 305.065 | 50.230 |
| Chansey Info Stats, atlas B | 254.885 | 405.554 | 150.669 |
| Blissey Info Stats, atlas B | 254.801 | 405.506 | 150.705 |
| Dusknoir Info Stats, active-entry case | 246.220 | 396.884 | 150.664 |
| Kyogre Info Stats, active-entry case | 246.149 | 396.765 | 150.616 |
| Info retained, Chikorita -> Bayleef | 238.105 | 288.334 | 50.229 |
| Info retained, Chikorita -> Bayleef -> Meganium | 238.103 | 388.801 | 150.698 |

The corresponding Leave-routine-to-reveal timings exclude the first input
poll: Chikorita Stats 220.614 -> 371.277ms; Dusknoir Stats
238.115 -> 388.801ms. Across the Description-only controls the difference is
approximately -0.110 to +0.117ms, including active-cry cancellation cases.
Ordinary settled Description returns add just 20 T cycles.

The expensive part is the deliberately conservative VRAM snapshot and reuse
of the safe uploader. One Chikorita Stats trace reaches the borrowed-atlas
scan result at 2.813 intervals, finishes glyph upload/remapping preparation
around 8.158, and acknowledges remap publication at 8.836. The normal Listing
repair/reveal follows. Even an unaliased page spends roughly three extra
intervals taking and scanning its actual map/attributes.

There is no full-screen black/white flash, no lower-panel mask and no visual
change when the remap publishes. The unchanged page simply remains visible
longer. This is a correctness-first preflight, not an optimized return path.

## Validation

| Suite | Result |
| --- | --- |
| Paired production/prototype returns, 32 paths x 3 | 96/96 prototype passes |
| B during another Info page or Info -> Description preparation | 150/150 paired prototype passes |
| All-species Info content, exact playback, internal paging, Description restoration and B-return | 373/373 passes, 746 full playback audits |
| All-species rapid inputs, five families x four phases | 7,459/7,460 passes; the sole failure also reproduces in production, below |
| Seen but uncaught controls, eight species x two phases | 16/16 passes |
| Sparse-seen Listing returns plus scrolling/wrapping/re-entry | 4/4 passes |
| Host observer disabled/enabled controls | 5/5 identical cycles, state, palettes, maps and final pixels |
| Unit/linked checks and negative relocation-oracle controls | 47 checks |
| Fresh private build recipe rerun | Byte-identical prototype |

The focused matrix includes cold Description returns, active sampled-cry
cancellation, internally paged and viewport-boundary returns, Description
P.2, Stats, Evolutions, Tyrogue stat conditions, Eevee branches, Skitty's
approved link, Chansey/Blissey's endpoint, retained Info during species paging
and the partial final Listing row. Every returned cache is checked, followed
by scrolling, wrapping and selected-page re-entry.

Twenty-one of the 96 production comparisons corrupt the outgoing panel;
none of the 96 prototype comparisons do. For each relocating case, the host
also verifies that the destination tile bytes match the original visible
source glyphs, attributes and hardware palettes/OAM remain identical, and no
visible reference to atlas B survives before Listing uploads begin. The
150 cancellation pairs use 15 cancellation ages on five representative
species for both next-Info-page and Info-to-Description preparation.

The broad stress phases are 0, 8, 32 and settled after entry. Input families
are mashed A, held A, return to Description, B-return and internal species
paging. No new animation miss or premature sampled-cry exhaustion was
detected. Intentional owner cancellation is not treated as exhaustion.

### Existing badge failure

Rhyperior, phase 0, immediate Info -> Description fails both production and
the prototype. Phases 8, 32 and settled pass. This is not a B-return failure,
and the relocation helper has not executed when it occurs.

The failed Description map differs from its expected map at exactly one
cell: row 9, column 1 is `$32` (blank), not `$77` (the lower `P.` badge).
Description text, number, owner state and playback are otherwise complete.
The broad test's message, "Requested Description text did not publish,"
includes badge equality and therefore overstates the symptom.

Source-level cause: `PokedexInfo_ClearRow` clears this owner-buffer cell,
and `PokedexInfo_DrawBadge` reinstates it only after all eight rows are
cleared. An early cancellation can occur between those operations. The
caught return path in `PokedexInfo_ReturnDescription` assumes the existing
badge is complete, while `PokedexSelectedMon_InitializeDescriptionText`
rewrites the digit but not the `P.` cell. Recommend explicitly staging the
complete Description badge when restoring Description, with a cancellation
phase sweep. No fix was included in this preflight; see `DEX-INFO-04`.

### Resolved prototype startup failure

The first experimental build put an additional helper check before the
existing VBlank owner admission guard. Its extra entry cost pushed the
handoff into LY145, while that guard requires LY144, causing an infinite
entry wait. The final private build branches to the new owner **after** the
existing admission guard. Ordinary pre-admission timing is unchanged. The
full runtime/return suites and a fresh reproducible rebuild use this corrected
version. Failed first-version evidence remains under `runtime/`; accepted
checkpoints are under `runtime-v2/`.

## Linked Resource Costs

| Resource | Added |
| --- | ---: |
| ROMX bank `$a6`, Info relocation helper | 204 bytes |
| ROMX bank `$77`, publisher plus admitted routing | 70 bytes |
| ROMX bank `$a0`, Leave call/reordering | 6 bytes |
| Total ROMX | **280 bytes** |
| ROM0, static WRAM0, WRAMX, HRAM, SRAM, VRAM | **0 bytes** |

No additional bank is allocated. Remaining space in the affected banks is
6,131 / 1,926 / 1,410 bytes respectively. Existing Info GFX, owner map and
attribute buffers, upload payload and stack are reused after their previous
owners are canceled. Memory-symbol locations are identical between builds.
ROM0 remains 568 bytes free, WRAM0 13 and HRAM 0.

## Assessment

This proves that relocation is a workable alternative to blanking the panel
or adding partial-cache ownership. Its resource cost and correctness risk are
small, but the extra approximately nine display intervals on atlas-B returns
are potentially noticeable. Do not fold it into production solely because
the tests pass. First judge the held-page pause in the separate ROM; if it is
too long, investigate reducing the snapshot/upload cost without dropping the
actual-visible-state and acknowledgement guarantees.

The current implementation intentionally favors reliable cancellation over
assuming that requested-page metadata or a partly built owner buffer describes
the display. Skipping the snapshot based on such assumptions would need
additional proof or a deliberately maintained committed-page record.

## Reproduction Tools

```sh
PYTHONPATH=tools python3 -B -m dex_timing.info_return_preflight \
  --output build/dex-info-return-relocation-fresh --jobs 8 \
  --source build/dex-info-return-relocation-20261003/baseline

PYTHONPATH=tools python3 -B -m dex_timing.info_ui \
  --rom build/dex-info-return-relocation-fresh/pokecrystal-info-return-relocation.gbc \
  --sym build/dex-info-return-relocation-fresh/pokecrystal-info-return-relocation.sym \
  --battery build/dex-info-placement/fixture.sav \
  --output build/dex-info-return-relocation-fresh/runtime --phases settled --jobs 8

PYTHONPATH=tools python3 -B -m dex_timing.info_return_regression \
  --build build/dex-info-return-relocation-fresh \
  --checkpoints build/dex-info-return-relocation-fresh/runtime \
  --output build/dex-info-return-relocation-fresh/paired --repeat 3 --jobs 8
```

The paired tool requires matching frozen baseline checkpoints under
`build/dex-info-placement` and reads that baseline ROM from the build manifest,
not from today's promoted production cartridge. Add `--cancel-sweep --repeat 1` in a separate
paired output directory for the cancellation sweep. Run `info_ui --stress`
with phases `0 8 32 settled` for broad input stress. Its known badge failure
remains a genuine failing result, not suppressed acceptance.

Raw evidence is retained under `paired-full/`, `cancel-sweep/`, `runtime-v2/`,
`stress-runtime/`, `uncaught-runtime/`, `sparse-returns/`, `observer-controls/`
and `production-rhyperior-control/`. The build recipe and private ASM probes
are retained in `tools/dex_timing/`; no production INCLUDE references them.
