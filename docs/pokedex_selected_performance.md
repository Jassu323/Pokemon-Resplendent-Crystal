# Selected Pokedex Performance Investigation

Historical investigation. Later accepted components are now integrated under
[the production clock policy](production_clock_policy.md); the component-repair
Listing return in this first trial was rejected. Statements below about
unchanged production refer to the original A/B run.

2026-10-04. Private A/B investigation for `DEX-PERF-02`, based on production
commit `2cec80517` (Dex - Area Tab). **No production ROM or gameplay source was
changed.** The candidate below is ready for manual comparison, not accepted
for production. Entry/exit optimization and other Dex modes remain deferred.

## Summary

The best tested package substantially improves Area entry, settled Info
preparation and rapid Info page cycling. Component-level Listing repair also
reduces complete B-return time. Area -> Info is almost unchanged: reconstructing
the Selected presentation, rather than finding nests, dominates that direction.

- Settled Description/Moves -> Stats: **12.43 -> 7.43 intervals**, about
  **208 -> 124ms**. The page remains atomic; first content change is completion.
- Any lower tab -> Area: approximately **36.5 -> 15.35 intervals**, about
  **611 -> 257ms**, with essentially unchanged initial transition response.
- Area -> Info: **15.59 -> 15.34 intervals**, about **261 -> 257ms**.
- Info -> Listing completion: **18.61 -> 14.86 intervals** when settled,
  about **312 -> 249ms**. There is a first-response caveat below.
- Rapid A no longer continually abandons preparation. Pages publish while
  pressing A, and all accepted presses contribute to the final page target.
- Active portrait/cry playback still limits Info. The median improvement is
  less than one interval, not the five-interval settled improvement. Some
  active cases still take approximately 0.54-0.58 seconds.

**Important first-response tradeoff:** the current ROM often erases a small
footer arrow within two intervals on B-return or species paging. The candidate
usually retains that outgoing footer longer. Consequently literal first-pixel
response is later even though the substantive Listing appears sooner. This is
not a uniformly better responsiveness result and needs visual approval.

## ROMs And Provenance

Local artifacts are under the ignored `build/dex-performance-20261003/` tree.
They are not repository dependencies and may be removed after acceptance.

| ROM | SHA-256 |
| --- | --- |
| Unchanged production `pokecrystal.gbc` | `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666` |
| Final private `final/pokecrystal-dex-performance-repair.gbc` | `249c86d40307e63f4b6dee0b633e5b5839b97f87ddd12a53dab92bb6c64b1d08` |
| Fresh vanilla `vanilla/fresh-source/pokecrystal.gbc` | `d6702e353dcbe2d2c69183046c878ef13a0dae4006e8cdff521cca83dd1582fe` |

Production symbols SHA-256:
`5b63e314adb0606d09f130e1ee18c3ffd3fc7d3feb58e33b04bfb471bd3867ee`.
Production map SHA-256:
`e6bff3efc764c58cc91d34029c9b757076c689ecefcaad02ef3c65b4d699a1aa`.
The live SameBoy save is unchanged, SHA-256
`6f7cc42ecc7842d407b5152a9d5c554b99153acc11bf5731946ab5ebcb960b16`.

The user's downloaded original ROM/save were first copied into the private
`vanilla/` directory. The ROM had no matching symbols and did not match the
local historical vanilla revision. Following the user's clarification, the
latest local `~/Documents/GitHub/pokecrystal` checkout was copied and built
privately instead. Upstream commit:
`5beda23ffa505f62e1dad7e3d7c214d1737b3358`.
The original downloaded files and upstream checkout were not edited.
Original save SHA-256:
`5824b3f5645aad0c9529a2907cf18586e93f78082c4ad200d0371b618aee27f4`.

Headless SameBoy source commit:
`213a12ce93d66b105a113debd9396306066a7cfc`.
Tests use the existing CGB boot ROM, normal CPU speed, private battery copies,
matching Listing checkpoints and ordinary controller input. No runtime RAM,
producer, interrupt or instruction patching is used for the measurements.

## Measurement Contract

One physical display interval is **70,224 T-cycles at 4,194,304 Hz**, or
**16.742706ms**. These are hardware interval equivalents, not 60Hz assumptions,
producer-call counts or the game's byte-sized animation counter. Fractional
intervals reflect input timing relative to a rendered frame.

For each action, record separately:

1. Button press to first changed rendered pixels after the request is accepted.
2. Button press to the correct final visible result.
3. Accepted-input delay, routine spans and final ownership/content checks.

The profiler observes emulator render callbacks and linked routine entry/return
without editing emulated state. Its cycle timestamp is callback-boundary
granularity; this report does not claim an independently calibrated eight-cycle
instruction-boundary match. The frame/ms differences are much larger than that
granularity. Routine spans include interrupts and boundary waits. Nested parent
and child costs must not be added together.

Tab-content changes use a lower-panel pixel crop, x=32..154, y=72..127,
excluding moving portrait/minisprites and the footer cursor. Listing and
species transitions use the full image for first response, and a stable crop
for completion. Moving minisprites/portraits are excluded from completion,
not mistaken for newly loaded content. Area's legitimate marker blink is
allowed. Correct final maps, glyphs, palettes, OAM and owner state are checked
independently of the pixel hash.

Actions that reload an identical one-page panel can have **no changed pixels**;
their visible metrics are absent, not zero milliseconds. There are 176 such
normal-cycle cases in both matrices. Rapid A has 184 unchanged cases in the
current matrix and 176 in the final matrix: a three-page cycle can end at its
starting page, but the candidate still displays intermediate pages.

The performance matrix contains **2,416 cases per ROM**: 27 representative
species, ten actions, active/settled playback, every current Info page where
applicable, and four quarter-interval input offsets (0/17,556/35,112/52,668 T).
Active Description/Moves -> Info cases are confirmed to have playback running
at the measured input. Settled cases wait for both animation and audio.
Area -> Info's active/settled label describes the state before entering Area;
playback has been canceled by the time the user returns from Area.

These are matched normal-input sequences and settings. Different ROMs take
different amounts of time during setup, so a quarter-offset pair is not a claim
of identical absolute PPU phase or CPU register state in both ROMs. Distributions
and additional phase sweeps are used instead of a single favorable sample.

Representative species: Chikorita, Meganium, Dusknoir, Weavile, Luxray,
Garchomp, Bastiodon, Rampardos, Groudon, Kyogre, Rayquaza, Metagross, Milotic,
Drapion, Rhyperior, Yanmega, Spheal, Sealeo, Snorlax, Exeggcute, Mewtwo, Unown,
Seviper, Eevee, Tyrogue, Chansey and Mew.

## Current Versus Final Timings

Medians, written as **intervals / ms**. "First" is a rendered response, not
merely input acceptance. All measurements begin at the button press.

| Scenario | Current First | Current Complete | Candidate First | Candidate Complete |
| --- | ---: | ---: | ---: | ---: |
| Description -> Info, active | 19.79 / 331.4 | 19.79 / 331.4 | 19.15 / 320.6 | 19.15 / 320.6 |
| Description -> Info, settled | 12.43 / 208.1 | 12.43 / 208.1 | 7.43 / 124.4 | 7.43 / 124.4 |
| Moves -> Info, active | 18.37 / 307.5 | 18.37 / 307.5 | 17.67 / 295.8 | 17.67 / 295.8 |
| Moves -> Info, settled | 12.43 / 208.1 | 12.43 / 208.1 | 7.43 / 124.4 | 7.43 / 124.4 |
| Description -> Area, active | 2.10 / 35.1 | 36.49 / 611.0 | 2.10 / 35.1 | 15.34 / 256.9 |
| Description -> Area, settled | 2.43 / 40.7 | 36.43 / 610.0 | 2.43 / 40.7 | 15.36 / 257.2 |
| Info -> Area, active | 2.10 / 35.1 | 36.49 / 611.0 | 2.25 / 37.6 | 15.34 / 256.9 |
| Info -> Area, settled | 2.36 / 39.5 | 36.43 / 610.0 | 2.43 / 40.7 | 15.36 / 257.2 |
| Moves -> Area, active | 2.34 / 39.2 | 36.48 / 610.8 | 2.34 / 39.2 | 15.34 / 256.9 |
| Moves -> Area, settled | 2.43 / 40.7 | 36.59 / 612.6 | 2.43 / 40.7 | 15.36 / 257.2 |
| Area -> Info, formerly active | 2.41 / 40.4 | 15.59 / 261.1 | 2.44 / 40.8 | 15.34 / 256.9 |
| Area -> Info, formerly settled | 2.42 / 40.6 | 15.59 / 261.1 | 2.43 / 40.7 | 15.34 / 256.9 |
| Info -> Listing, active | 1.75 / 29.3 | 18.74 / 313.8 | 12.50 / 209.2 | 15.00 / 251.1 |
| Info -> Listing, settled | 1.61 / 26.9 | 18.61 / 311.6 | 14.43 / 241.6 | 14.86 / 248.8 |
| Info page cycle, active | 17.75 / 297.1 | 17.75 / 297.1 | 17.37 / 290.8 | 17.37 / 290.8 |
| Info page cycle, settled | 12.86 / 215.3 | 12.86 / 215.3 | 7.61 / 127.4 | 7.61 / 127.4 |
| Rapid A sequence, active | 70.37 / 1178.2 | 70.37 / 1178.2 | 21.37 / 357.8 | 68.87 / 1153.1 |
| Rapid A sequence, settled | 67.61 / 1132.0 | 67.61 / 1132.0 | 8.49 / 142.1 | 59.86 / 1002.2 |
| Info -> next species, active | 1.85 / 30.9 | 15.75 / 263.6 | 5.16 / 86.4 | 15.20 / 254.4 |
| Info -> next species, settled | 1.54 / 25.7 | 15.36 / 257.2 | 5.86 / 98.1 | 15.36 / 257.2 |

Candidate complete-result ranges:

| Scenario | Interval Range | Approximate ms Range |
| --- | ---: | ---: |
| Description -> Info, active | 14.09-34.34 | 236-575 |
| Description/Moves -> Info, settled | 7.00-7.86 | 117-132 |
| Moves -> Info, active | 13.03-32.34 | 218-541 |
| Any tab -> Area, active | 13.97-16.85 | 234-282 |
| Any tab -> Area, settled | 14.07-15.86 | 236-266 |
| Area -> Info | 14.02-16.84 | 235-282 |
| Info -> Listing, active | 11.00-19.99 | 184-335 |
| Info -> Listing, settled | 12.11-19.86 | 203-332 |
| Info page cycle, active | 15.00-25.25 | 251-423 |
| Info page cycle, settled | 7.11-9.86 | 119-165 |
| Info -> next species, active | 12.99-17.85 | 217-299 |
| Info -> next species, settled | 13.11-17.86 | 219-299 |

### Rapid Input Interpretation

This test sends **15 distinct presses**, two intervals on/two off. The sequence
itself lasts approximately 59 intervals, or 988ms. Its one-second completion
number is **not the latency of a single A press**.

Current production publishes no new Info page during the presses: each press
restarts the unfinished job. The final candidate publishes 2-5 times during
active-playback sequences and 8-9 times when settled. Every final rapid case
records 15 accepted activations, and the final page matches
`(starting_page + 15) % page_count`.

For visually changing cases, after the final release:

| State | Current Median | Candidate Median | Candidate Range |
| --- | ---: | ---: | ---: |
| Active | 11.73 intervals / 196.3ms | 10.29 / 172.3ms | 0.55-21.70 / 9-363ms |
| Settled | 8.82 / 147.6ms | 0.82 / 13.6ms | 0.79-7.81 / 13-131ms |

The visual-changing subsets differ when an entire page cycle ends back at the
initial image. The full accepted-request/final-page correctness checks cover
all 216 rapid cases, including identical one-page panels.

### First Response Versus Substantive Response

Frame-by-frame Chikorita Stats -> Listing comparison:

- Current: frame 2 changes only **23 footer-arrow pixels**, bounds
  x=44..49, y=136..143. The substantive Listing appears at frame 18.
- Candidate: retains the outgoing presentation longer; the substantive
  Listing appears at frame 15.

For Stats -> next species, current similarly erases the arrow at frame 2 and
begins masking the portrait at frame 6. The candidate begins the portrait mask
at frame 7; the complete incoming page appears at frame 15 in both examples.

Therefore Listing completion really is faster, but it would be incorrect to
say that every button receives earlier visible feedback. A deliberate small
pressed-state/footer response could be considered separately. It has not been
prototyped or costed as an accepted fix; do not claim it is included here.

## Vanilla Area Comparison

Fresh upstream build, eight species and four input phases, **64 cases**, all
passing. Species: Chikorita, Eevee, Mewtwo, Exeggcute, Snorlax, Chansey, Rattata,
Magikarp.

| Vanilla Action | First Median | Complete Median | Complete Range |
| --- | ---: | ---: | ---: |
| Description -> Area | 2.08 / 34.9ms | 31.58 / 528.8ms | 31.08-39.83 / 520-667ms |
| Area -> Description | 2.50 / 41.9ms | 25.94 / 434.3ms | 24.01-28.93 / 402-484ms |

On the six shared species (24 entry cases per ROM), settled entry medians are:

- Vanilla: 2.21 intervals / 36.9ms first, **31.46 / 526.7ms complete**.
- Current fork: 2.48 / 41.6ms first, **36.48 / 610.8ms complete**.
- Candidate: 2.48 / 41.6ms first, **15.48 / 259.2ms complete**.

Thus the user's observation is supported: current Area entry is about
**5.03 intervals / 84ms slower than vanilla** in the shared-species comparison.
The candidate removes much more than that overhead.

Vanilla return is not the same operation as this fork's return. Vanilla
restores Description and replays the portrait animation; the fork restores
the exact prior tab/page with a static base portrait and no cry replay.
Do not attribute their entire return-time difference to one optimized routine.

## Causes And Implemented Private Changes

### Area Entry

`Pokedex_GetArea` calls general-purpose Town Map loaders. Small generic
graphics/map transfers spend many intervals waiting for their next slice.
The palette mapper also extracts packed palette nibbles for every cell, and
`FindNest` scans all grass/water encounter records to collect landmarks.

The candidate keeps the accepted masked transition and complete ownership
handoff, but replaces only Dex Area's call sites:

- Decompress 48 Town Map tiles into existing owner scratch and transfer them
  with the established safe `Pokedex_HDMATransferCacheGFX` path.
- Pad maps/attributes to native 32-byte rows in the existing owner buffers;
  upload each 18-row plane as 36 aligned blocks through that same helper.
- Replace per-cell packed-nibble extraction with a 256-byte ROMX palette table.
- Generate two counted static landmark lists per species, indexed directly by
  species/region. Append the existing native live Raikou/Entei logic afterward.

The other Pokegear/Town Map callers are unchanged. This does not turn graphics
into unchecked direct VRAM writes or allocate another map-sized RAM buffer.
The linked static index must be regenerated when species or encounter data
changes. Production promotion should put that dependency in the asset build;
the historical private builder regenerates it from its pinned linked baseline.

### Info Preparation And Rapid A

Info already uses an inactive atlas and atomic lower-panel publication. The
main costs are repeated glyph-bank calls, bounded service cadence, and the
cancel/restart behavior on A while a job is unfinished.

The candidate:

- Copies up to eight glyphs per copy slice with one bank switch and an unrolled
  16-byte tile loop; no shifted-font data or larger atlas is added.
- Runs six instead of three service slices **only when portrait playback,
  sampled-cry timer and all synthesized SFX channels are quiet**. Existing
  admission/cutoff checks remain. Active playback keeps the original budget.
- Finishes and publishes the current requested page, while coalescing newer A
  presses into one pending target. It starts that target after publication.
- Clears the pending request on real cancellation, tab exit or species reset.
  This is local Info state, not a global input-repeat change.

### Listing Component Repair

Info's second atlas borrows the Listing side minisprites' frame-0 tiles.
There are five physical rows: center sprites, side frame 0 and side frame 1.
Only **40 side frame-0 tiles** are borrowed, but current return invalidates
complete row tags and therefore rebuilds unaffected components too.

After moving the visible outgoing Info page into atlas A, the candidate
reconstructs those 40 borrowed tiles before trusting any retained full-row tag.
It then runs the ordinary viewport cache ensure: genuine logical-row mismatches
after internal paging still rebuild normally. No validity tag is weakened while
its frame-0 contents are incorrect. Existing row scratch is safe because this
hidden restoration is synchronous, with no Listing input/icon animation running.

### Inclusive Routine Costs

Representative current settled Dusknoir case; these spans include interrupts
and waits and are **not additive** with their parents:

| Work | Current T-cycles | ms | Interpretation |
| --- | ---: | ---: | --- |
| Info clear, eight calls | 37,172 | 8.86 | Panel/map preparation |
| Stats plan, six calls | 54,700 | 13.04 | Labels, numbers, bars |
| Glyph copy, five calls | 63,924 | 15.24 | Candidate: 29,424 T / 7.02ms |
| Info upload, six calls | 57,240 | 13.65 | Existing safe DMA admission |
| Info page-record work, six calls | 19,320 | 4.61 | Retained outgoing-page correctness |
| Info service, fourteen calls | 252,384 | 60.17 | Parent span, includes work above |
| Town graphics loader | 630,632 | 150.35 | About nine intervals in generic pipeline |
| Town palette mapper, two calls | 198,580 | 47.34 | Packed per-cell palette lookup |
| Town map upload, two calls | 967,956 | 230.78 | About fourteen generic upload intervals |
| FindNest | 248,580 | 59.27 | Full encounter-table scan |
| Area return Selected staging | 787,896 | 187.85 | Parent reconstruction/waits |
| Return portrait preparation | 156,796 | 37.38 | Nested in preceding row |
| Info preserve-return panel | 205,340 | 48.96 | Existing visible-page retention |
| Complete Listing-cache repair | 355,236 | 84.69 | Candidate frame-0 repair: 121,728 T / 29.02ms |

Info's approximately 208ms visible latency is not 208ms of raw planning/copy
CPU work: service cadence and safe boundary waits account for the difference.
Area return does not perform the expensive nest search again. Faster entry
alone therefore cannot materially fix return.

## Alternatives And Tradeoffs

Measured options refer to whole private variants, not isolated additive gains.
Unimplemented estimates below are explicitly not benchmark promises.

| Option | Gain Or Result | Cost | Complexity / Risk | Assessment |
| --- | --- | --- | --- | --- |
| Dex-local bulk Town Map transfer + palette lookup | Area complete approximately 36.9 -> 18.9 intervals before nest indexing | Small ROMX routines/table, existing scratch | Moderate; DMA owner/bank/visibility contracts | Strong candidate; accepted helper, not new DMA architecture |
| Add generated static nest index | Roughly another 3.5 entry intervals; final approximately 15.35 | 2,760 data bytes + 62 code bytes, one reusable ROMX bank | Low/moderate; regeneration and live-roamer append | Worthwhile, near-uniform species cost |
| Faster glyph copy + quiet-only batching | Settled Stats approximately five intervals / 84ms faster; little active gain | Small ROMX code, no atlas/RAM growth | Moderate; quiet gate must include synthesized cries | Recommend together with regression coverage |
| Finish/coalesce Info A requests | New pages appear during rapid presses; settled release-to-final typically <1 interval | One reused-overlay byte, small local ROMX code | Moderate; queued/committing/idle states | Fixes confirmed restart starvation |
| Repair only borrowed Listing frame 0 | Complete settled return approximately 3.75 intervals / 63ms faster | 149 linked ROMX bytes including call site, existing row scratch | Moderate; must repair before trusting full-row tags | Recommend subject to first-feedback visual review |
| Dense precomputed per-species Stats rows | CPU planning improves, but tested settled publication about one interval slower | 102,948 payload + 1,119 index bytes; full variant +107,848 ROMX bytes/eight banks | Data maintenance, unchanged cadence remains bottleneck | Reject this representation |
| Quiet direct GDMA upload | Four corrected-gate visual cases all failed | Small code, but wait/owner/bank behavior not safe | High until fully isolated | Reject; not included in final build |
| Narrow copy-only early-clock guard | 48 tests passed, but did not recover early feedback and worsened return completion | Small code | Additional timing gate with no measured benefit | Reject |

Further opportunities, **not implemented or validated**:

- **Retain committed Info assets across Area.** Town Map graphics use bank 0;
  Info atlas/minisprite assets are largely bank 1. Existing page records are
  still present, but they do not contain a complete attrmap, cancellation may
  clear active minis, and pending jobs must be accounted for. A same-species,
  committed-generation check could avoid rebuilding surviving assets. Estimate
  300-800 ROMX bytes and a few overlay state bytes; medium ownership risk.
  Several intervals (perhaps 4-6) are a plausible target, not measured savings.
  This is the most relevant follow-up for the nearly unchanged Area -> Info.
- **Background Stats warming after animation and cry completion.** Reuse
  inactive atlas/records and cancel on generation change. Estimate 0.5-1KiB
  ROMX and 4-8 overlay bytes, not a new permanent page cache. A warm hit might
  publish in 1-2 intervals. Medium/high cancellation/ownership complexity;
  does not help a player selecting Info immediately during heavy playback.
- **Additional cost-admitted active Info work.** Keep exact portrait deadlines
  and audio reserve, add only work proven to fit the remaining display budget.
  Estimate 0.5-1KiB ROMX plus a few overlay bytes. Possible 2-4 interval target
  is unproven. Higher risk than quiet batching; raising the active slice count
  without fresh cost/phase regressions is not recommended.
- **OBJ digits.** Twenty-four digit sprites plus eight type sprites, HP endpoint
  and footer would use about 34/40 OAM entries. Full labels plus digits exceed
  forty sprites. Double-buffered digits need about 48 OBJ tiles and ~64 bytes
  of shadow staging, plus palette/layout work. Existing bank-0 OBJ slack may
  fit digits, but scanline limits and transition ownership still need testing.
  Moderate/high complexity for an unmeasured partial benefit; not necessary
  for the successful package.
- **Permanent BG Stats tiles / fewer Listing rows.** Current BG space is tight
  (two bank-0 BG tiles and no bank-1 BG tiles unallocated in the existing model).
  Reserving fifteen shared Stats tiles means reclaiming another owner's space.
  Reducing five cached Listing rows to three gives up scroll lookahead. The
  tested component repair is less disruptive; do not take portrait-streaming
  VRAM to solve a lower-panel performance issue.
- **More precomputed Town Map attrs.** Roughly 2-3KiB per region could save
  remaining per-cell preparation. Expected benefit is smaller after bulk DMA;
  no separate prototype was justified yet.
- **One-page Info A no-op.** Approximately 20-40 ROMX bytes/no RAM could avoid
  rebuilding identical Stats-only pages. It prevents wasted work but cannot
  produce a visible page change. Not implemented.

## Species Dependence

Settled Stats always constructs its fixed-size atlas, so its improvement is
essentially uniform. Evolution pages vary with number/length of conditions and
minisprites. Active cases depend strongly on animation/cry cost and the point
at which the quiet gate becomes true. Larger dictionary/tight timeline cases
retain the conservative active service path.

Area's generated lookup removes almost all species-dependent encounter scanning.
Listing return still depends on the current viewport and which rows genuinely
need rebuilding. Internal paging still pays for the incoming portrait and
sampled-cry startup, so speeding glyph copies cannot remove that cost.

Example candidate Stats-page medians, complete hardware intervals:

| Species | Description -> Info Active / Settled | Listing Active / Settled | Next Species Active / Settled |
| --- | ---: | ---: | ---: |
| Chikorita | 15.87 / 7.49 | 14.37 / 14.49 | 14.37 / 14.49 |
| Dusknoir | 33.97 / 7.49 | 14.47 / 14.49 | 13.47 / 14.49 |
| Weavile | 33.97 / 7.49 | 15.47 / 14.49 | 15.97 / 17.49 |
| Luxray | 16.97 / 7.49 | 14.97 / 14.49 | 15.97 / 16.49 |
| Eevee | 19.37 / 7.49 | 16.37 / 16.49 | 14.37 / 14.49 |
| Tyrogue | 18.87 / 7.49 | 15.37 / 17.48 | 14.87 / 14.48 |
| Chansey | 17.87 / 7.49 | 19.62 / 15.49 | 16.37 / 16.49 |
| Groudon | 23.97 / 7.49 | 16.97 / 14.49 | 17.47 / 17.49 |
| Kyogre | 19.97 / 7.49 | 15.96 / 14.49 | 17.46 / 17.49 |

Multiply by 16.742706 for ms. The next-species measurement belongs to that
outgoing species' normal Down input; its cost is also affected by the successor.

## Resource Costs

Exact linked final candidate delta: **+3,717 ROMX bytes**, one additional mapped
16KiB bank `$b9`. Most of that new bank remains free for later work.

| Linked Section / Use | Delta |
| --- | ---: |
| Dex Performance Index: 2,760 generated data + 62 code | +2,822 ROMX bytes |
| Info preparation/queue/copy call changes | +150 ROMX bytes |
| Info glyph-bank fast-copy/Town Map routines/palette lookup | +577 ROMX bytes |
| Area call-site changes in bank `$24` | +19 ROMX bytes |
| Listing frame-0 repair and call site in bank `$77` | +149 ROMX bytes |
| Pending page field | One existing bank-3 overlay byte, `$db65` |
| ROM0 / WRAM0 / HRAM / SRAM / VRAM / OAM growth | **0** |

The overlay ends at `$db66`, leaving **154 bytes before `$dc00`**. No additional
physical WRAMX union allocation occurs. Linker aggregate WRAMX usage remains
23,944 bytes used / 4,728 free; this is bank/section-specific slack, not a pool
of freely interchangeable scratch RAM. WRAM0 is still 4,083 used / 13 free;
HRAM 127 used / 0 free. ROM0 remains 15,830 used / 554 free.

The legacy glyph-copy body is deliberately retained in this private A/B build.
Approximately **63 ROMX bytes** could be reclaimed when promoting/removing that
unreachable comparison implementation; this saving is not included above.

Mapped ROMX: baseline 2,314,022 used / 700,634 free in 184 banks; final
2,317,739 used / 713,301 free in 185 banks. The increase in mapped free space
comes from adding a largely empty bank, not from magically reclaiming storage.
Across the 4MiB cartridge, approximately **1,860,735 bytes / 1.77MiB** remain
outside linked ROM0/ROMX payload. Mapped bank slack and the unmapped tail have
different placement constraints.

## Bugs And Corrections

### Confirmed Current Rapid-Info Starvation

`DEX-INFO-06`: on a species with multiple Info pages, settle Stats, leave the
cursor on Info and repeatedly press/release A at two-interval spacing. Current
production restarts the job after every accepted activation; the lower panel
does not publish until input stops. Same behavior is tested during active
animation/cry playback. The finish/coalesce candidate fixes this while retaining
the final page implied by the accepted activation count.

### Corrected Prototype Publication-Gap Race

An earlier candidate passed rendering/playback regressions but could discard
a queued target when A arrived immediately after publication: state and owner
were idle while the pending target was still nonzero. The idle activation path
canceled it. The final queue explicitly treats a nonzero pending target as busy.
All 216 final rapid cases pass accepted-count/final-target checks. Do not use
the older `repair/` ROM for manual comparison; use `final/`.

### Corrected Observer Transaction Mix-Up

The expanded Area-follow-up tests initially reported palette/VBlank failures
despite correct pixels/maps/palettes. The trace included an earlier species
publication before the later B-return. The Listing summarizer selected the
earlier owner boundary and mixed two transactions. It now filters phases and
frames beginning at `leave`; all 412 and 72 affected cases pass on the **same
unchanged candidate ROM**. This was a test-observer bug, not a palette fix in
the game. A unit test covers it.

The old `DEX-INFO-03` report specifically concerns **Info -> Description after
internal paging**. This matrix measures Description/Moves -> Info and proves
that those directions are accepted but budget-limited; it does not close the
opposite-direction report merely by analogy. Standard cancellation regressions
pass, but that older report needs its own focused responsiveness measurement.

## Regression Results

Final candidate, parallel private headless runs (up to 24 workers):

| Suite | Cases | Failures |
| --- | ---: | ---: |
| Performance matrix | 2,416 | 0 |
| Info rendering/playback at four phases, all 373 species | 1,492 | 0 |
| Moves rendering/playback at active/settled phases, all species | 746 | 0 |
| Cold Listing playback, all species | 373 | 0 |
| Internal paging playback, all species | 373 | 0 |
| Area from three tabs/two phases, all species | 2,238 | 0 |
| Info cancellation/input stress | 400 | 0 |
| Moves cancellation/input stress | 560 | 0 |
| Actual Listing cache content/scroll/re-entry | 613 | 0 |
| Expanded all-page Area context/repeat/A-B/follow-up | 412 | 0 |
| Seen-but-uncaught / locked-Kanto Area | 72 | 0 |
| Live Raikou/Entei locations, locked/unlocked Kanto | 48 | 0 |

The **6,182 standard regression cases** are the seven Info/Moves/cold/internal/
Area/Info-stress/Moves-stress rows above, not an additional duplicate count.
Those tests check exact authored animation publications/physical timing and
sampled-cry completion, not just absence of miss callbacks. Known troublemakers
are included. Area tests check nest/player locations, region locking, left/right
paging, marker blinking, female player palettes, A/B returns, exact prior page,
no portrait/cry replay, subsequent species playback and Listing restoration.

The 613 cache tests compare retained physical rows against fresh native rows
at the corresponding absolute logical offsets, including both side animation
frames, center sprites, presence/flags and palettes. They cover every species'
Stats/evolution pages, multi-row internal paging, early cancellation,
up/down/left/right navigation and re-entry. Restoring only frame 0 does not
leave stale frame-1/center data hidden behind a valid row tag in those checks.

Current baseline performance: 2,416/2,416 pass. Vanilla comparison: 64/64 pass.
Additional earlier candidate runs are retained as historical evidence, not
counted as final acceptance.

Current nonhistorical host suite: **315 tests, 0 failures/errors, 2 skipped**.
Full unfiltered discovery also runs archived `test_dex_timing.LinkedTests`
against the current instrumentation-free production ROM: 404 tests total,
6 failures, 16 errors, 103 skips. All failures/errors are confined to that
historical class's removed trace labels/old linked cost expectations. They are
not green, and are not hidden as candidate successes. Modern rendering,
physical-clock, content and measurement tests pass. Modernizing/removing those
historical linked tests is separate tooling cleanup, not a runtime change.

## Reproduction And Artifact Policy

Build the final private candidate from the pinned baseline checkout/ROM:

```sh
python3 tools/build_dex_performance_prototype.py \
  --output build/dex-performance-reproduction --variant repair --jobs 16
```

The builder archives the baseline, applies the private probe sources, generates
data, links in the private checkout and copies its matching ROM/sym/map. It
rejects a changed HEAD/baseline ROM instead of mixing later data with this
historical source. Variants `lean`, `indexed`, `idle`, `batch`, `repair` retain
the experimental sequence; `repair` uses the final corrected queue source.

Measure baseline/candidate separately:

```sh
python3 -m tools.dex_timing.performance --help
python3 -m tools.dex_timing.performance_regression \
  --config build/dex-performance-20261003/final/measurements/config.json \
  --output build/dex-performance-repeat --jobs 24
python3 -m tools.dex_timing.performance_cache_regression --help
python3 -m tools.dex_timing.area_ui --help
python3 -m tools.dex_timing.performance_roamers --help
python3 -m tools.dex_timing.vanilla_performance --help
```

Detailed data: `current/performance.json`, `final/measurements/performance.json`,
`vanilla/measurements/performance.json`, `final/full-regression/summary.json`,
`final/cache-regression/summary.json`, Area context/roamer `report.json` files,
matching configs/provenance and frame-review images. Large full-VRAM JSONL
traces were losslessly gzip-compressed, retaining their contents while
reclaiming most of the generated disk usage. Production/user files were not
removed. All generated artifacts remain ignored by Git.

Maintained host changes include measurement observers, pending-request-aware
Info readiness and the Listing transaction-summary correction. The private
ASM lives only in `tools/dex_timing/probes/performance_*.asm`; production
`engine/`, `ram/`, `main.asm` and linked files remain unchanged.

## Recommendation And Manual Review

The final package is a strong private candidate for Area entry, settled Stats
and rapid Info behavior. It does not solve active heavy-playback latency or
Area -> Info reconstruction, and its delayed incidental footer feedback should
not be promoted without the user's visual judgment.

Compare the unchanged production ROM with
`final/pokecrystal-dex-performance-repair.gbc`. An unchanged copy of the live
save is supplied beside it as `pokecrystal-dex-performance-repair.sav`, with
the corresponding basename. The live save/ROM remain untouched. Manually review:

- Description/Moves -> Stats during and after Chikorita, Dusknoir, Weavile,
  Luxray, Groudon and Kyogre playback; listen through the complete cry.
- Normal and rapid A on Chikorita, Eevee and Tyrogue, including switching tabs,
  B-return or species paging before the queued request is finished.
- All three tabs -> Area, region switch/player marker, and A/B return to exact
  prior Stats/evolution/Moves/Description pages without frontpic/cry replay.
- Stats and longer evolution pages -> Listing, immediate scroll and re-entry,
  especially after internal paging changes the Listing viewport.
- The first-feedback tradeoff on B-return/internal paging, not just the faster
  completed Listing. No additional SameBoy captures are needed unless manual
  review reveals a new visual/audio/input problem.

Optional miss breakpoints for **this final private ROM only**, verified against
its matching symbols/linked cache-empty branch:

```text
breakpoint $a0:$6677
breakpoint $0:$3cc1
```

The first is the Selected animation miss; the second is sampled-cache exhaustion.
If one fires, record species, selected tab/page, preceding input sequence,
registers and backtrace. Do not reuse an older ROM's hardcoded addresses.

If accepted, promotion should integrate the generated-nest build dependency,
remove unreachable legacy comparison code, update current-system docs and
re-run the final linked production regressions. This report alone does not
authorize production integration or close the wider `DEX-PERF-02` story.
