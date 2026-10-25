# Description Multipage Renderer Scope

Date: 2026-10-16. Scope only. No renderer prototype, species import, game build,
ROM integration or save edit has been performed.

**This is feasible as a small extension of the existing Selected Description
owner.** Keep the current panel, font, portrait scheduler, text workspace and
atomic lower-panel publisher. Both regular Selected and interactive New Dex
Entry can use the same extension. No shared interrupt changes are necessary.

My recommendation is a small **direct-page-offset table** for the added
species. It costs 366 ROMX bytes of metadata instead of a 122-byte count table,
but avoids making pages three and four slower simply because earlier text has
to be scanned. The scanner-only variant remains a valid smaller alternative.

See the [content assessment](pokedex_species_information_scope.md) for the
122 entries, word wrapping, measurement discrepancies and 12,767-byte text
growth. This document scopes the renderer separately from that content cost.

## Current Paths

| Path | Current Handling | Required Change |
| --- | --- | --- |
| A on Desc | `PokedexSelectedMon_ToggleDescriptionPage` uses `xor 1` | Increment the requested page and wrap at its species' actual count |
| Visible text change | A bounded job renders into existing backing maps and queues publication | Select the requested page while retaining the same job and publication mechanism |
| Cold entry or species change | `PokedexSelectedMon_StageDescription` uses the shared synchronous printer before incoming playback starts | Print exactly the requested page, not page one followed by page two |
| Area return | The same staging path rebuilds Description using its retained page value | Support retained page three/four, including the correct badge |
| Info/Mov to Desc | `PokedexInfo_ReturnDescription` resets Description to page one, then queues the text job | Preserve this behavior and the existing attribute/OAM restoration contract |
| New Dex Entry | Registration calls the same footer action and text service | Inherit multipage handling; preserve B/End and post-catch continuation |

The key owners are `engine/pokedex/pokedex_detail.asm`,
`pokedex_description_text.asm`, `pokedex_2.asm` and `pokedex_description.asm`.
No new per-screen implementation is needed in registration.

## Page Selection and Metadata

Keep the existing zero-based `wPokedexDescriptionPage` as the requested page,
with `wPokedexStatus` synchronized where current staging code expects it.
Pressing A on Desc advances 0, 1, 2, 3, then wraps to zero for a four-page entry.
Two-page entries retain their current visible behavior and input convention.
Do not change D-pad species selection or add a new page-selection UI.

Use `GetPokemonIndexFromID` to resolve the stable 16-bit species index before
accessing metadata. `wPokedexSelectedSpecies` is an 8-bit transient ID, not a
direct index into the 373-species data; comparing it with Treecko's index or
indexing metadata with it would fail for later species and recycled IDs.

Original species 1 through 251 keep their existing two-page count. Added
species occupy a contiguous 122-index range even though Gen 3/Gen 4 families
are interleaved within it. Validate the index range and wrap/clamp the requested
page before any skip or direct seek. Seen-but-uncaught entries must keep their
current blank-description behavior without exposing text or numeric badges.

### Recommended Direct Offsets

Store three bytes per added species: the offsets of pages two, three and four
relative to the first description page. Page one is implicitly offset zero;
zero in a later-page slot means that page does not exist. The highest populated
slot supplies the page count, so **a separate 122-byte count table is not
needed**. Total metadata is **122 x 3 = 366 ROMX bytes**.

All current entries have at least two pages. The highest actual later-page
offset is 157 bytes; the largest complete proposed record is 179 bytes.
With this layout, even three maximum-length preceding pages occupy only
171 encoded bytes, so an 8-bit relative offset suffices for the four-page
scope. These are semantic source offsets, not generated font glyphs, rasterized
pages or another cache.

Have assembly labels or an equivalently checked generator derive offsets from
the actual encoded page boundaries. Assert the maximum page count, offset
range, nonempty pages and absent-slot convention at build time. Future text
that exceeds this format must fail the build rather than truncate or wrap an
offset. Extending beyond four pages would then be an explicit format change.

After the reader skips the category and four measurement bytes, it adds the
requested page offset to the existing banked source pointer and renders.
Original species can retain their existing single-page skip for page two;
they need no additional offset table or content rewrite. Share the offset
lookup between normal paging and the static return printer.

### Smaller Scanner Alternative

Use the 122-byte count table from the content assessment. After preparing the
badge, reuse `wPokedexDescriptionTextPage` as a remaining-pages-to-skip counter.
At each `@` terminator, decrement the counter and enter render state only when
it reaches zero. Keep `wPokedexDescriptionPage` unchanged; it is the requested
page, not scratch state. The badge is already staged from the request before
this counter is consumed.

This is the smallest change to the existing streamed reader and requires no
additional RAM. Its drawback is repeated scanning through earlier text on
every later-page request. It is still safe if scanning remains bounded; do not
replace it with an unbounded active-playback loop to recover the time.

## Bounded Rendering and Publication

Retain the existing 24-byte source chunk, maximum three work slices per owner
iteration, active-animation LY admission and animation-first service order.
The new work belongs to foreground preparation, not VBlank, STAT, timer or
sample-refill handlers. Do not enlarge the time slice just because prose is
longer.

Keep the complete old page visible until the requested page and its numeric
badge are ready. The current text publisher already transfers the fixed lower
panel; the number of description pages does not enlarge that transfer. It
does not need a loop over pages or any new interrupt work.

`PokedexBadge_Prepare` already accepts 1 through 19. Feed it the actual requested
page plus one; P.3/P.4 require no new artwork or upload architecture. Preserve
its inactive-buffer selection, which is independent of the page ordinal.

Retain cancellation before a new request, tab change, species change or exit.
If A replaces a pending request, the new job must use a fresh request snapshot
and prepare the matching badge. Do not let the consumed scanner counter become
the visible page number or let a canceled job publish afterward.

All imported content must be validated as at most three lines of 18 expanded
glyph cells per page, including compact contractions and existing `#`
expansion where used. This is trusted ROM data: build-time checks can prevent
clipping without adding a new per-character runtime width counter or RAM field.

## Static Printer and Return Paths

`DisplayDexEntry` currently prints page one and, for any nonzero status, clears
it and prints page two. Generalize it to seek first and print only the desired
page. Preserve names, category, Dex number, measurements and caught gating.
Do not route ordinary A paging through this full-entry printer.

Its current uses are initial/staged screens, before the incoming authored
animation starts, and Area return, after the outgoing owner cancels playback.
Keeping the full-entry work synchronous there does not create a new blocking
loop during active Description paging.

`Pokedex_DisplayDescriptionEntry` also patches every nonzero page to the old
page-two badge tiles. Remove that fixed page-two assumption from CGB staging;
restore the canonical shell border and let the existing staged badge preparer
choose the real digit. `Pokedex_PublishOrStageDescriptionBacking` already
prepares that badge using `wPokedexDescriptionPage + 1` before reveal. There
is no reason to put another badge upload into the early shared printer, where
initial registration can still have the LCD off.

Preserve resets on cold selection, species changes and Info/Mov-to-Desc.
Preserve the selected Description page on Area round trips. Preserve the
current [pending-map-aware Info return dependency](pokedex_info_description_latency_investigation.md#atomic-portrait-contract);
the portrait publication flag must retain its existing atomic meaning.

## Costs and Complexity

All figures are decimal bytes. Exact net code size requires an approved
prototype link; these are conservative **planning budgets**, not measured
candidate allocation deltas.

| Resource | Scanner Extension | Direct Offsets, Recommended |
| --- | --- | --- |
| ROMX metadata | 122 | 366, replacing the count table |
| Renderer code plus metadata budget | Up to 512 total | Up to 768 total |
| ROM0 | No addition required | No addition required |
| WRAM0 and WRAMX | No new allocation required | No new allocation required |
| HRAM, SRAM and VRAM | No new allocation required | No new allocation required |
| Graphics | Existing font, border and numeric badges | Same |
| Complexity | Low/moderate | Low/moderate, with a small shared seek helper |

The direct table adds **244 metadata bytes** over scanner-only, not 366 plus
122. Code can stay in the current ROMX owners. The current map has 1,435 free
bytes in the bank containing the Selected Description/animation owner and
3,053 in the shared entry printer's bank; a new renderer bank is not indicated.
Link placement must still be checked after the content section is split.

The separate prose/data growth remains **12,767 ROMX bytes**. It is not included
in the renderer budgets. With the recommended 768-byte allowance, a conservative
combined planning allowance is 13,535 ROMX bytes. Replacing the duplicate
static page-one/page-two code may make the actual net renderer increase smaller.

## Responsiveness

The direct-offset version removes the need to scan preceding added-species
pages. It does not promise every page will appear on the next frame: rendering,
badge preparation, scanline admission and publication still use the existing
bounded pipeline.

The scanner-only alternative can read up to 157 description bytes before page
four. Compared with requesting page two of the same entry, pages three/four
can add up to six extra skip chunks. With all three slices admitted each time,
that is up to two additional owner iterations, approximately **33.49 ms /
2 physical display frames**. This is a structural scheduling comparison, not
a measured candidate delay or an upper latency bound; playback-related
deferrals can change the elapsed difference. Direct offsets avoid those
length-dependent skip iterations.

A fresh read-only run of the current linked renderer's six host tests passes,
including all **746 existing species/page cases**, publication ownership,
cancellation and hardware-bank restoration. Its largest isolated work slice
is **5,464 CPU T-cycles**, below the current 6,144-cycle test limit. At double
speed this is **0.651 ms / 0.0389 display-frame equivalents**; at normal speed
it is **1.303 ms / 0.0778 frames**. These are instruction-path equivalents,
excluding real interrupts and HBlank waits, not visible page-change timings.

No new candidate timing or audio/video comparison exists yet because renderer
prototyping has not been approved. Capture visible page latency and playback
evidence during the eventual prototype, in milliseconds and display frames.

## Risks and Qualification

The main risks are localized to incorrect page indexing, mismatched badge/text,
and incomplete cancellation or restoration handling. There is no need to
change battle execution, the speed-switch boundary, save layouts or shared
display interrupts. Preserve the
[battle interrupt timing contract](battle_animation_interrupt_timing_contract.md).

Update tests before claiming extended-page coverage. The current independent
`description_pages` oracle explicitly enumerates `(0, 1)` and several trace
checks also assume two pages; leaving those unchanged could produce a passing
suite that never looks at page three or four. Test badge buffers independently
of ordinal page values, rather than initializing their active flag as
`1 - page`, which only works for page zero/one.

Required prototype checks:

- Independently derive text pages and offsets from encoded entry data; compare
  them with generated metadata. Reject bad line widths, excess lines, unknown
  controls, missing terminators, out-of-range offsets and invalid page counts.
- Exhaustively test all 373 species, every valid page and wraparound. There
  will be **868 unique caught Description pages per presentation**, or 1,736
  across Modern and Legacy, before transition/repetition cases. Test all
  registration species as well.
- Exercise recycled transient IDs, entries around index 255/256, mixed
  two/three/four-page neighbors, stale/out-of-range page values and uncaught
  entries. Preserve the original 251 species' content and behavior.
- Compare the streamed and static printers' results, including Area return
  from P.3/P.4, Info/Mov returns, search-result selection and Listing return.
- Test rapid repeated A, held A, canceled in-progress requests, B/End and tab
  or species changes during both scanning/rendering and queued publication.
- Check every slice against the existing cycle/admission budget and audit
  correct ROM/WRAM/VRAM bank restoration and job immutability.
- During active synthesized and sampled cries, verify exact authored portrait
  events, natural cry completion, sample-refill deadlines and unchanged upper
  pixels. Include screenshots and matched recordings for manual review.
- Check both post-catch registration and script/prize registration returns,
  then run the standard full regression before any production integration.

Read-only audit output and the current-link test log are retained under
`build/dex-species-information-scope-20261016/renderer-scope/`. Its `audit.json`
records the source/layout calculations, bank headroom and protected-input
checks. Reproduce with:

```sh
python3 -B build/dex-species-information-scope-20261016/renderer-scope/audit.py
```
