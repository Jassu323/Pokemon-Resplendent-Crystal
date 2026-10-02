# Pokedex Description Paging Investigation

Investigated 2026-10-02 for `DEX-DESC-01` against committed checkpoint
`c289b1b365ad47d9882148f026c53493217fb15a` (Menu Navigation Fix).
The recommended bounded text transaction is now implemented in production.
Automated acceptance passes; manual acceptance remains pending. The original
diagnosis below refers to that checkpoint, not the corrected game. See
[Implemented Transaction](#implemented-transaction) for current behavior,
resource costs and complete regression results.

A-button text paging was a synchronous, full-screen redraw that left the
Selected animation owner in its slower ordinary mode. It can both expose a
partly replaced portrait and starve subsequent animation preparation. The
full-screen copy also delays sampled-cry timer service. The appropriate fix is
a bounded, text-only transaction within the existing Selected owner, not a
replacement animation decoder or another timeline/scheduler architecture.

## Inputs And Isolation

| Input | Identity |
| --- | --- |
| Production ROM | `d3004b30abc41fcf3ce0933736fd697a85de15944da0e680c03ad80e6d1ad6ea` |
| Matching symbols | `4fa9f046cb9ce4c20dd2955acdfcc5bf36b063c0bb73bbde65be463f32af57a1` |
| Matching map | `fab2c5d95a3e64dba08b067c1760b8f46ce2e6fcf4b1560a5133e9bf44fb8a70` |
| Copied source battery | `a2bdef4a621ba92cfc2b549d28cdda980234cd94d648313e3dbe5c447fa57ea7` |
| Private caught fixture | `dddb0d5c5e63b031b6a79083e7f9ce9396ca2de1f54f829fb9305949e6647fd2` |
| SameBoy revision | `213a12ce93d66b105a113debd9396306066a7cfc` |

The source battery already has all species seen. Only the two copies of the
caught flags and their checksums are changed in a private fixture, allowing
full description text on every test species. Seen data, Unown initialization,
party data and RTC bytes are preserved. The live battery is not edited.

The private unmodified diagnostic cartridge is byte-identical to production.
The optional `DEX_DESCRIPTION_PAGING_TRACE` instrumentation is compiled into
the headless executable, not the ROM. It observes instructions, physical
display boundaries, timer service, map writes, backing maps, palettes and
rendered portrait/header pixels without writing emulated memory or cycles.

Four tracing-on/off replays agree on elapsed cycles, complete emulated state,
publication/miss events, UI maps/palettes and final rendered pixels. State
comparison excludes only existing RTC wall-clock fields, not its cycle
accumulator. The host contract suite passes 145 tests.

Generated states, traces, copied ROMs and pictures are isolated under the
ignored `build/dex-description-paging/` directory. No production game source,
root cartridge, installed SameBoy cartridge or live save was changed during
the diagnostic stage. The later approved implementation changes production
source and rebuilds the root cartridge, but never edits the installed
SameBoy cartridge or live save.

## Reproduction

1. Open a caught Pokemon's Selected Description from the Listing.
2. While its portrait is animating, press A with Desc selected to change text
   page 1 to page 2.
3. Watch the portrait immediately around the text change and during later
   animation events. Depending on input phase and species, there can be a
   one-frame mixed portrait, a later scrambled/stale portrait, or both.

Meganium reproduces the familiar early-species issue: from the saved initial
Selected update, wait four physical display intervals and press A. Its first
animation miss is followed by six noncanonical rendered portrait frames.
In the frame capture, the text has already changed before the later scrambled
portrait appears. Weavile and Garchomp have wider failing input windows;
waiting until playback finishes avoids the animation failure in this suite.

The offsets are relative to the first normal-input Selected update checkpoint,
after initial portrait publication. They are not offsets from the physical
Listing A press or a requirement that a person time a press to one exact
millisecond. The runner provides the repeatable phase control.

The main sweep uses eight active offsets, `0/1/2/4/8/16/32/64`, plus a separate
post-completion toggle. A is applied through controller pins, not by invoking
the handler or editing input mirrors. Each case runs for another 180 display
intervals to catch delayed consequences.

## Results

| Species | Cases with an animation miss | Tested cases |
| --- | ---: | ---: |
| Chikorita | 0 | 9 |
| Bayleef | 0 | 9 |
| Meganium | 1 | 9 |
| Dusknoir | 6 | 9 |
| Metagross | 0 | 9 |
| Luxray | 0 | 9 |
| Rampardos | 3 | 9 |
| Garchomp | 8 | 9 |
| Weavile | 6 | 9 |
| **Total** | **24** | **81** |

All nine post-completion cases have no animation misses. Eighteen matched
uninterrupted controls, an active and completed checkpoint for every species,
have no animation misses, noncanonical portraits or sampled cache-empty stops.
This separates the A transaction from ordinary playback.

Sixteen detailed pixel/map replays use Meganium, Dusknoir, Garchomp and Weavile
at offsets `0/4/16/completed`. Ten have animation misses and visibly invalid
portrait frames. They also identify transient portrait tearing during the
full-screen copy, independently of the later miss fallback. In particular,
retaining quiet ownership leaves one-frame noncanonical portraits on Dusknoir
despite no animation-miss hits. A clean miss counter does not establish that
this copy is visually atomic.

The current-link name/header/type/footprint region remains pixel-identical
through the completed post-load frames in these detailed tests. The historical
report of other upper-row corruption is not independently reproduced here.
Confirmed current symptoms are portrait tearing and animation corruption.

SameBoy save states do not restore the host's pixel output buffer. The first
callback after loading can retain pixels above the saved scanline from the
preceding replay. Rendered-pixel checks therefore start at the next complete
frame. Raw VRAM/map checks do not need this exclusion. The earlier 81-case
probe has raw-map observations but no rendered-pixel hashes; its transient
VRAM samples must not be described as 81 visually inspected recordings.

## Transaction Timing

All values below are elapsed normal-speed T-cycles, including interrupts and
waits, not isolated instruction-only CPU costs. A display interval is 70,224
T-cycles.

- The full A handler takes **188,656-357,376 T-cycles**, about **2.69-5.09
  display intervals**, or **45-85 ms**, across the 81-case sweep.
- In the detailed baseline, redraw/setup before the map copy takes
  **81,956-189,680 T-cycles**. No main-thread animation producer runs while
  that synchronous work is in progress. Interrupts can still publish a
  previously prepared portrait until the copy disables them.
- `CopyTilemapAtOnce` itself takes **97,712-148,924 T-cycles**, including its
  admission wait, separate attribute/tile transfers and the second wait.
  This is not just the cost of copying a few text tiles.
- The existing right-edge repair adds work after the full copy despite the
  exposed border column not changing when the text page changes.

For a representative Meganium offset-4 case, relative to A-handler entry:

| Phase | T-cycles | LY | Detail |
| --- | ---: | ---: | --- |
| Toggle entry | 0 | 31 | Quiet owner enabled |
| Release quiet owner | 24 | 31 | Later loop remains ordinary |
| Shared entry printer | 3,012 | 38 | Reprints unchanged header data |
| Page 1 string begins | 39,404 | 117 | Printed even though page 2 is requested |
| Pending portrait published | 51,972 | 145 | An already-ready map can publish in an IRQ |
| Page 2 string begins | 135,628 | 20 | Page 1 has been cleared again |
| Full-screen copy begins | 183,108 | 125 | Waits to admit the stack copier |
| Attribute half begins | 184,108 | 127 | Interrupts disabled |
| Tile-ID half begins | 201,800 | 12 | Raster has wrapped; attributes already replaced |
| Map copying finishes | 223,804 | 60 | Still inside interrupt-disabled transaction |
| Copy helper returns | 281,284 | 32 | Includes second wait and delayed IRQ processing |
| A handler returns | 299,020 | 71 | Text action consumed over four intervals |

The handler/return scanlines are phase-dependent; the cause does not depend
on one particular line number.

## Confirmed Causes

### Quiet Owner Is Released Permanently

`PokedexSelectedMon_ToggleDescriptionPage` calls
`Pokedex_ReleaseQuietAnimationOwner` first. This strips the quiet VBlank bit,
re-enables normal OAM work and resets the scheduler-control byte. The toggle
does not call `Pokedex_AcquireQuietAnimationOwner` afterward. Acquisition occurs
at animation startup, so later owner iterations stay on the ordinary loop and
lose optional finishing/admission opportunities until the page is left.

The Selected update also returns through its A action before its usual
prepare/produce/commit calls. The timeline is not canceled or restarted, but
its producer is unavailable while the synchronous redraw runs.

### Redraw Repeats Unchanged And Unwanted Data

`Pokedex_DisplayDescriptionEntry` calls the shared `DisplayDexEntry` printer.
That reprints name, category, Dex number, height and weight. It clears the
description, prints page 1, then clears and prints page 2 when page 2 was
requested. None of the unchanged upper data or the unused page is needed for
an A toggle. Generic string/number rendering and banked lookups add substantial
elapsed work with no cooperative producer yield.

### Full Copy Bypasses Portrait Publication Ownership

`Pokedex_CopyBackingToBG` invokes `CopyTilemapAtOnce` for the whole map and
attributes. The backing portrait can already contain the next prepared frame,
not only the currently visible frame. Publishing that backing through a
general copier bypasses the animation owner's deadline and slot-publication
bookkeeping.

The copier separately replaces attributes and tile IDs across a physical
raster wrap. A completed display can consequently contain tiles interpreted
with the other map's bank attributes, or a partially replaced portrait. This
is demonstrated in rendered hashes even when retaining quiet mode prevents
later animation misses. The subsequent animation-miss handler supplies its
underflow map, explaining the longer scrambled/stale sequences after the
short copy-time tearing.

This is **not** a missing `LY >= 144` check in the portrait publisher. The
current `Pokedex_VBlankAnimationFrontpicMap` has that check; the general A-page
copier is a separate publication path.

## Audio Side Effect

Eight active A tests on Dusknoir, Metagross, Luxray and Garchomp measure
**74,752-85,256 T-cycles** between executed sampled-cry timer block services,
about **18-20 ms**. The corresponding uninterrupted controls have maximum
gaps of **16,600-16,940 T-cycles**, with the normal block period at 12,800.

The interrupt-disabled copy coalesces timer requests instead of servicing each
block on time. The wave hardware continues running, but the software block
advancement pauses. In the offset-0 controls, natural sample completion is
delayed by 51,200 cycles for Dusknoir, 64,000 for Metagross and Luxray, and
51,232 for Garchomp. All still finish with zero blocks remaining.

No sampled cache-empty breakpoint fires in the A sweep. That does **not** mean
audio timing is unaffected: stalled consumption prevents this particular
failure counter from detecting the playback interruption. These are timer
observations, not a claim that every gap was audibly perceived in a recording.
Removing the long interrupt mask belongs to the same local text fix; no
sampled-cry decoder or refill-policy change is proposed.

## Cause Isolation

These are private byte-patched counterfactuals from the exact same 16 starting
states, not production candidates. Calls and replacement bytes are verified
against linked symbols; only those bytes and the cartridge global checksum
change.

| Private variant | Animation-miss cases | Invalid rendered-portrait cases |
| --- | ---: | ---: |
| Unmodified A handler | 10/16 | 10/16 |
| Keep quiet ownership; retain redraw/full copy | 4/16 | 8/16 |
| Keep quiet ownership; omit full copy; retain redraw | 2/16 | 2/16 |

The last variant deliberately does not display the new text page. It is useful
only to isolate the cost of redraw. Weavile and Garchomp still miss at offset 4,
with handler times of 95,804 and 84,144 T-cycles respectively. Thus retaining
quiet ownership or merely removing the full-screen copy is not a complete
fix. The redraw itself needs less work and/or cooperative bounds.

## Fix Options

### Stop Or Defer Animation

Cancel animation on A and restore the base portrait before switching text, or
defer A until playback finishes. The former is a small owner-state change but
removes the current continue-animation behavior and still needs a safe text
publication to avoid interrupt masking. The latter can delay a requested page
by seconds and may also outlast the portrait if a sampled cry is still active.
Neither is recommended for the intended responsive Description UI.

### Retain Ownership And Use A Synchronous Text Only Printer

Avoid upper-data reprinting and page-1 work on a page-2 request, preserve quiet
mode and publish only the changed lower rows. This removes much wasted work
with lower implementation complexity, but an unbounded string render can
still begin close to a tight animation deadline. It would need admission and
worst-case testing; the isolated full redraw shows why retaining ownership
alone is not an adequate timing argument.

### Bounded Text Only Transaction

**Recommended direction:** keep the current animation owner and timeline
running while a small local job prepares the requested text page. The job
retains independent desired/ready state, services a bounded number of text
operations between existing animation/audio work, and publishes only the
description/badge/divider rows in a short admitted VBlank transaction.

The portrait, header, type graphics, footprint and palettes remain untouched.
The fixed lower text attributes may not need rewriting at all; establish that
contract before choosing a tile-only transfer. Reuse the existing padded
bank-3 owner buffers for lower rows, which do not overlap the portrait's
rows 1-7. Do not call the full blocking `Pokedex_QueueOwnerTransition` unchanged:
it clears quiet ownership and is intended for a complete owner handoff.

The VBlank dispatch must preserve portrait priority without starving text
publication. Finishing/cycle admission must account for both operations when
both are due. Text should publish with its page badge, not leave a badge/text
mismatch. Repeated A may coalesce the desired page; B, Area and species
changes must cancel the pending text job before their buffers change owners.
Existing Selected generation/state checks can help guard those boundaries.

Planning costs, **not assembled implementation measurements**:

| Resource | Expected direction |
| --- | --- |
| ROMX | Several hundred bytes, provisionally about 0.5-1 KiB for local bounded rendering/publication; refine during preflight |
| ROM0 / HRAM | No new allocation intended; use existing far-read/transfer helpers |
| WRAM0 | Aim for no new bytes by extending the existing owner-request byte's dispatch contract, not borrowing padding |
| WRAMX | Approximately 6-12 job-state bytes in the existing Dex/Battle Tower overlay; its already allocated 4 KiB footprint need not grow |
| VRAM / animation assets | No new tiles, slots, dictionary metadata or timeline tables |

The current Dex bank `$a0` has 2,175 free bytes. The plan does not require a new
ROMX bank, but the precise layout, job state and byte costs should be verified
before implementation. Lower-row transfer size is much smaller than the
full screen; final VBlank and text-job budgets must be measured on the link,
not inferred solely from that size.

Main risks are stale pending-page publication after a species/owner change,
text-control handling in a bounded renderer, and priority interactions when
portrait/audio work is due. These are local transaction contracts. They do not
require changing the accepted two-slot animation representation, normal-speed
clock, codec, prefill or dictionary assets. Page-switch latency may span several
owner turns; its actual input-to-visible timing must be measured before
acceptance rather than promised from these diagnosis runs.

## Implemented Transaction

Implemented and tested 2026-10-02. No animation timeline, dictionary, decoder,
finishing table, audio codec or prefill/refill parameter changes are included.
New Dex Entry retains its separate resident scheduler and text publisher.

### Mainline Preparation

`PokedexSelectedMon_ToggleDescriptionPage` changes the desired page and queues
a local text job rather than releasing quiet ownership or calling the generic
entry printer. The Selected update then runs its ordinary animation
prepare/produce/commit work before servicing text. A no longer returns early
and skips the producer. B retains priority over A; A retains priority over
directional navigation in the same input update.

`PokedexSelectedMon_ServiceDescriptionText` allows at most three slices per
owner iteration. Each chunk reads at most 24 source bytes using the existing
banked-copy helper. Every slice rechecks admission: active-animation work is
admitted only before LY 96 or at/after LY 144. After animation completion,
late mainline text work is also allowed so an idle owner's late arrival cannot
starve the job. This admission is for mainline WRAM preparation, not a claim
that VRAM can be written during visible scanning.

Initialization finds the selected entry, snapshots the requested page, clears
the 90 lower description cells in both backing maps and stages the matching
page badge. Subsequent slices skip the category terminator and four numeric
bytes, skip page 1 only when page 2 is requested, and render only the desired
text. The bounded renderer supports the current data's literal glyphs,
`<NEXT>`, `#` expansion through `PlacePOKeText`, and `@`. A linked-data/unit
audit covers both pages of all 373 entries, including line/column bounds.
Future text controls need matching renderer support and renewed validation.

The longest current isolated slice is 5,464 normal-speed T-cycles (a Sneasel
page-1 chunk), below the tested 6,144-T bound. This is an instruction/linked
operation measurement, not the total elapsed cost of three slices plus
interrupts. Actual playback timing is checked separately in SameBoy.

### Atomic Lower-Row Publication

Completion queues `POKEDEX_OWNER_TRANSITION_DESCRIPTION_TEXT` in the existing
owner-request byte and arms the existing Dex VBlank dispatch. Arming is needed
even when animation has already finished. The staged source becomes immutable
until the VBlank acknowledgement; no further chunk runs against a ready job.

VBlank priority is full-owner handoff, then a due portrait, then ready text,
then Listing icon work. Text accepts only `144 <= LY < 148`, rejects competing
BG-map/DMA work, selects bank 3/VBK 0 and performs one 224-byte GDMA transfer
for padded rows 8-14. These rows include the badge/divider and all three text
lines. The badge and text therefore change together, without an intermediate
blank or partially rendered page. The previous complete page stays visible
until this publication is admitted.

No portrait rows, upper data, type/footprint graphics, attributes or palettes
are rewritten. The publisher does not acknowledge animation events or alter
their deadlines. It restores both hardware banks and retains quiet ownership.
If an animation map remains pending, its handler stays armed. Otherwise the
low handler bits are cleared while preserving the quiet tag.

A combined due portrait/text unit profile completes its VBlank VRAM work in
4,160 T-cycles including interrupt entry, within 4,560. This is a measured
profile, not an unconditional allowance for arbitrary late or additional
work: each publisher retains its own admission gate. Physical-frame tests
check for visible partial text and portrait corruption separately.

### Cancellation And Ownership

Another A cancels the old job and coalesces to the newly desired page. Species
changes, B-return, Area entry and full Description staging cancel text before
the shared buffers change owners. Cancellation clears the owner request only
when it belongs to text, not when another publication is queued.

Uncaught entries keep their empty physical description and badge while
retaining the existing logical page toggle behavior. CGB uses the new job;
the prior synchronous DMG fallback remains. Current hardware regressions are
normal-speed CGB tests, not a fresh DMG emulator acceptance suite.

### State And Resource Cost

All job state lives after the existing padded maps in the otherwise inactive
bank-3 Battle Tower/Dex union:

| Address | Field | Bytes |
| --- | --- | ---: |
| `$d480` | state | 1 |
| `$d481` | source ROM bank | 1 |
| `$d482` | source pointer | 2 |
| `$d484` | main backing cursor | 2 |
| `$d486` | padded owner cursor | 2 |
| `$d488` | text row | 1 |
| `$d489` | job page | 1 |
| `$d48a` | source chunk | 24 |

The actual 34 bytes exceed the initial 6-12-byte state estimate because the
bounded implementation adds a 24-byte chunk. This avoids a banked lookup for
every glyph and makes each operation's maximum input count explicit. The
union's already allocated 4 KiB maximum does not grow.

| Resource | Net change versus diagnostic baseline |
| --- | ---: |
| ROMX bank `$a0` | +763 bytes; 1,412 free remain |
| ROMX bank `$77` | +100 bytes; 2,495 free remain |
| Total ROMX | **+863 bytes**, no new bank or asset dataset |
| ROM0 | Unchanged; 568 free bytes remain |
| WRAM0 | Unchanged; 13 free bytes remain |
| WRAMX allocation | Unchanged; 34 additional owned bytes inside an existing union |
| HRAM / VRAM | Unchanged |

### Final Automated Results

All tests below use the production ROM, controller-pin input and isolated
save fixtures. The observer runs only in the headless executable; there is
no new game instrumentation or artificial scheduling write.

| Suite | Result |
| --- | --- |
| Linked/unit and transaction contracts | 153 tests pass |
| Nine species, eight active A phases plus completion | 81/81 pass |
| Matched uninterrupted controls | 81/81 publication signatures exactly match A runs |
| All-species cold Listing playback | 373/373 pass |
| All-species internal paging playback | 373/373 pass |
| All-species active/completed page-2 requests | 746/746 pass |
| All-species page 1/page 2/page 1 and next-species UI | 1,492/1,492 checks pass |
| Repeated A, held A, A+B, pending B and species handoff | 90/90 cases pass |

The 81 matched controls agree on each portrait's hardware tick, frame identity,
map and rendered content. Natural sampled completion differs by only -12 to
0 T-cycles, not a display interval. There are no animation or active-sampled
cache-empty misses, noncanonical portrait frames, partial rendered text,
badge/content mismatches or changed upper/header pixels in these suites.
Maximum sampled block-service gap is 17,080 T in the all-species A suite,
instead of the baseline copy's 74,752-85,256-T interruptions. Linked tests also
verify unchanged lower attributes and exact bank restoration.

The owner-input suite additionally tries 15 pending-text Area entries:
three roundtrips pass and twelve stall during existing Area setup. All twelve
reach the Area owner rather than publishing stale text. A separate no-A pass
against the unchanged baseline stalls in 13 of 15 Area entries. This confirms
the previously logged `DEX-AREA-01` setup problem is not introduced by this
fix. Area remains deferred and is not included in the clean Description
acceptance claim.

The focused 81-phase sweep's input-handler cost is 1,456-3,144 T-cycles,
about 0.35-0.75 ms. Input-to-visible text latency is a distinct measurement:
median 2.586 display intervals, 95th percentile 4.294, maximum 7.872 intervals
(Weavile, active offset 2), about 132 ms. The all-species offset-0/completed
suite has median 2.521 and maximum 5.280 intervals. Animation/cry work has
priority during those waits; the old page remains complete and visible.
Manual acceptance should specifically assess whether the rare text-only wait
is acceptable, not mistake unchanged playback for instantaneous text reveal.

During implementation, tests caught and corrected an owner-transition
classification added before the startup LY gate, a missing text-only dispatch
arm after animation completion, and late-iteration job starvation. The final
production tests above are fresh runs after those corrections, not results
from the earlier intermediate builds.

### Identity And Reproduction

| File | SHA-256 |
| --- | --- |
| `pokecrystal.gbc` | `7bd5442840f4f190b426d3dbd54bf3e0aa840c087c78f93263c41a8a59862a2a` |
| `pokecrystal.sym` | `a472b6709640e240a2d84f2a52d4df83d01afde56232bd31524f43160430656a` |
| `pokecrystal.map` | `418b299843fde9dd8d39a89586b96517bc877de3e79b35cedb7eda2c3dc0e452` |

Reports/checkpoints are in ignored `build/dex-description-paging/`:
`production-final`, `production-no-a`, `production-comparison`,
`production-cold-all`, `production-paging-all`, `production-all-text-final`,
`production-ui-all`, `production-inputs-final2`, and `area-baseline-final`.
Use a freshly rebuilt matching ROM/symbol link, not a previous-link save state.

```sh
make -j8
PYTHONPATH=tools:. python3 -B -m unittest test_description_paging test_listing_restoration test_direction_changes test_dex_cold_listing test_dex_target_regression test_new_dex_entry test_shared_input test_dex_description_ui test_dex_scheduler test_cry_ownership test_internal_transitions
PYTHONPATH=tools:. python3 -B -m dex_timing.description_paging --output build/dex-description-paging/retest --species chikorita bayleef meganium dusknoir metagross luxray rampardos garchomp weavile --offsets 0 1 2 4 8 16 32 64
PYTHONPATH=tools:. python3 -B -m dex_timing.description_paging --output build/dex-description-paging/retest-no-a --reuse-starts build/dex-description-paging/retest --no-a
PYTHONPATH=tools:. python3 -B -m dex_timing.description_text_regression --starts build/dex-description-paging/retest --output build/dex-description-paging/retest-inputs
```

For broader coverage, use `--all-species --offsets 0` with the paging probe,
the existing `cold_listing` runner with/without `--paging`, and the
`description_ui` audit with `--all-species`. Run
`description_text_regression --compare-controls` to compare matched signatures.
Test batteries must have valid initialized Unown data; the harness makes only
private caught-flag/checksum edits.

## Implementation Acceptance

No more manual debugger captures are needed to establish the current cause.
After approving a fix, extend the private runner to test both text-page
directions and repeated A, rather than only the first flip. Include:

- The existing nine-species phase sweep and uninterrupted controls, followed
  by all-species page-content and playback checks.
- Exact physical animation intervals, canonical portrait pixels and sampled
  completion, not only the two miss counters.
- A toggles during tight frame changes, before/after initial publication and
  after animation completion while a longer sampled cry can still be active.
- Repeated A, held A, A+B, B-return, footer/Area changes and internal species
  changes while a text job is pending.
- Badge/content agreement, unchanged header/type/footprint/palettes, correct
  final text and both caught/uncaught entries.
- Input-to-visible text latency and maximum timer-service gaps compared with
  uninterrupted playback.

## Reproducing The Diagnostic

Build the current root ROM and use an isolated battery copy with valid checksums,
all species seen and initialized Unown data. The runner creates the caught
fixture itself; never point its output directory at the root build or input save.

```sh
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.description_paging \
  --battery /absolute/path/to/isolated-save-copy.sav \
  --output build/dex-description-paging/sweep \
  --species chikorita bayleef meganium dusknoir metagross luxray rampardos garchomp weavile

PYTHONPATH=tools:. python3 -B -m tools.dex_timing.description_paging \
  --output build/dex-description-paging/sweep --analyze-only
```

Use `--reuse-starts build/dex-description-paging/sweep` for matched controls.
`--no-a` runs uninterrupted playback; `--observer-controls` compares tracing
enabled/disabled. Checkpoint reuse verifies the original ROM and symbols.
`--variant keep-owner` and `--variant keep-owner-skip-copy` generate only the
cause-isolation copies described above. Do not promote them to production:
they are intentionally incomplete.

Relevant production sources are [Selected actions](../engine/pokedex/pokedex_detail.asm),
[shared entry printer](../engine/pokedex/pokedex_2.asm),
[Description border/text adapter](../engine/pokedex/pokedex_description.asm),
[owner policy](../engine/pokedex/pokedex_animation_policy.asm),
[general map copier](../home/tilemap.asm) and
[VBlank dispatch and portrait publication](../engine/pokedex/pokedex_3.asm).
