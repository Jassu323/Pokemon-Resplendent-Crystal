# Pokedex Cry Ownership Investigation

Investigated 2026-10-01 against committed category-fix checkpoint
`a712c1ef0e904157adc43cf9819125a96d9f33cd`. This covers `DEX-CRY-02` and
`DEX-CRY-04`, plus the related incoming-header race recorded as `DEX-CRY-05`.
All three are ownership failures, not evidence that settled animation or audio
production needs another throughput change.

Implemented 2026-10-01: cancel the outgoing sampled and synthesized cry at
accepted Selected-Mon owner boundaries, before synchronous preparation or
incoming cry metadata lookup. The production helper passes all-species cold
entry, internal paging and active-handoff regressions. It adds 127 ROMX bytes,
no dedicated memory, and no measured transition delay. The three cry ownership
items are solved for this owner; Stats/battle and Area rendering remain separate.

## Inputs And Isolation

| Input | Identity |
| --- | --- |
| Accepted ROM | `c94a70ad545580a580b55ba24133e222f032f3afb4c8c6f3102101796a763470` |
| Matching symbols | `bb1222d0ad898826b9a1fa5b033aed98422c31dbfcf6d1aa8bcab867b061590e` |
| SameBoy revision | `213a12ce93d66b105a113debd9396306066a7cfc` |
| Private cancellation ROM | `bca07be23fe007325aa777cbf04c0f6490964b4bcce3689fc87937eba19f1da3` |
| Integrated production ROM | `21c582198de90bb64caf61cbe8e18cb8a653a0cb355d308a8f172ccc140ee5d5` |
| Integrated symbols | `d2630646be2ea60230251da264bdcfa42d6618daf4ddeba12b919a5b8bdc1caf` |

The accepted ROM is preserved at
`build/dex-category-rendering-fixed/cold/input-copy.gbc`. The root
`pokecrystal.gbc` was absent during the initial read-only investigation. Before
integration, its matching symbols/map were preserved under
`build/dex-cry-ownership-integrated/baseline/`. The root ROM is now rebuilt with
the Dex-local helper. Only `engine/pokedex/pokedex_detail.asm` changes production
behavior. No live save was edited or ROM copied into the user's emulator folder.

The headless runner uses normal controller input. To reproduce the original
paging neighbors, a private battery fixture exposes Chikorita, Bayleef,
Caterpie, Exeggcute, Mewtwo, Dusknoir, Metagross, Luxray, Bastiodon, Garchomp,
Weavile and Regigigas as seen. Only seen/caught bitsets and both save checksums
change in that copy; caught flags are intersected with seen flags, and unrelated
data and the RTC tail are checked unchanged. This is not an in-game memory
injection. The live battery is never substituted.

With every species seen, Mewtwo and Dusknoir are not adjacent. Supplementary
controls therefore use real all-seen neighbors, including Celebi to Treecko,
Garchomp to Riolu and Metagross to Regirock. Do not confuse the sparse fixture's
neighbors with the full New Dex order.

The optional `DEX_CRY_OWNER_TRACE` C observer is compiled into a separate
headless executable, not the cartridge. It records owner boundaries, cry
metadata writes, timer copies, sampled start/stop, synth note parsing, mixer
state and channel scripts. Observer-on/off controls agree in four cases on
checkpoint cycles, publication/miss events, UI buffers, rendered pixels and
saved emulated state. Only host-synchronized RTC wall-clock bytes are excluded
from state comparison; the RTC cycle accumulator remains compared. Raw state
hashes can differ because sequential runs happen at different real times.

## Synthesized Cry Resumption

### Reproduction

1. In the sparse fixture, select Mewtwo from the Listing.
2. Press Down while its synthesized cry is still playing, accepting Dusknoir.
3. Leave Dusknoir selected until its sampled cry finishes naturally.
4. Observe sound-engine parsing resume the remaining Mewtwo notes while the
   selected entry is still Dusknoir.

Offsets are counted as Selected input-loop turns after the first Selected
update, not promised one-for-one hardware display intervals. The 0/4/16/40
offsets reproduce 18/16/12/5 resumed synth note parses respectively; the settled
Mewtwo control does not. These counts are note parser executions, not durations
or subjective loudness measurements.

An all-seen reproduction is Celebi to Treecko: open Celebi and quickly page
Down once while its cry is active. Offsets 0 and 4 both leave four outgoing
synth note parses after Treecko's natural sampled completion. Offset 16 and
settled controls do not reproduce it. Early B-return from Mewtwo also permits
the outgoing synth cry to continue on the Listing.

### Cause

In the baseline, `PokedexSelectedMon_ChangeSpecies` and
`PokedexSelectedMon_Leave` in
[pokedex_detail.asm](../engine/pokedex/pokedex_detail.asm) canceled animation
production, but not cry ownership. Starting sampled playback did not cancel
the outgoing synthesized channel scripts.

Both `UpdateSound` in [home/audio.asm](../home/audio.asm) and `_UpdateSound` in
[audio/engine.asm](../audio/engine.asm) return while `hSampledCryTimer` is active.
That deliberately pauses the normal sound engine, including the leftover cry.
Mewtwo's channels 5, 6 and 8 retain flags `$21`: active channel plus synthesized
cry. Their script cursors and note durations freeze during sampled playback.
Once the sample stops, ordinary sound updates resume those same scripts.

In the offset-0 trace, Dusknoir stops naturally at T-cycle 9,457,940 with zero
remaining playback blocks. Mewtwo's channel cursors are still
`$7b75/$7b9c/$0000/$7bbe`, with the cry channels in bank `$3c`. The first
resumed note is at T-cycle 9,620,360, still on Dusknoir's Selected index 315.

The historical account tied resumption to a Dusknoir underrun. Current
reproduction proves **underrun is not necessary**: natural completion exposes
the uncanceled synth scripts too. Globally pausing the sound engine is not
itself the bug; failing to relinquish the outgoing cry before that pause is.

## Outgoing Sample Exhaustion

### Reproduction

1. Open Garchomp in the sparse fixture.
2. Press Up while its sample is active, accepting Bastiodon.
3. During the hidden preparation, observe the empty-cache branch with nonzero
   remaining playback. The incoming Bastiodon cry has not started yet.

Garchomp to Bastiodon and Dusknoir to Mewtwo reproduce at offsets 0/4/16;
offset 40 and settled controls do not. Metagross to Luxray reproduces outgoing
exhaustion at offsets 0/4. Dusknoir and Weavile also reproduce on immediate
B-return to the Listing. Ten of the 40 primary baseline cases exhaust the
outgoing sample cache.

The Garchomp offset-0 handoff is particularly clear:

| Observation | Accepted handoff | Cache-empty branch |
| --- | ---: | ---: |
| T-cycle | 1,409,076 | 1,967,468 |
| Sample bank | `$9f`, Garchomp | `$9f`, Garchomp |
| Decoded blocks ready | 34 | 0 |
| Playback blocks remaining | 300 | 258 |
| Compressed blocks remaining | 266 | 258 |
| Selected owner | Beginning handoff | Switching species, incoming Bastiodon |

The gap is about 7.95 hardware display intervals. The empty-cache stop is real,
but belongs to Garchomp. Bastiodon's subsequent sample starts and completes
naturally. A shared stop-routine breakpoint alone cannot distinguish this from
natural completion or deliberate cancellation.

### Cause

The accepted handoff leaves the old sample timer running through synchronous
dictionary, graphics and UI preparation. That timer continues consuming the
outgoing decoded cache even though the old visible owner is already leaving.
Those preparation paths are not guaranteed to refill the outgoing sample.

Increasing prefill or adding refill calls could postpone this symptom, but
would preserve an audio owner that should already have ended. The correct
boundary is before preparation, not when the next cry is finally started.
B-return has the same ownership problem while restoring the Listing.

This diagnosis does not reopen the settled Selected playback acceptance or
the separate Stats/battle refill issues.

## Incoming Header Race

Metagross to Luxray at offset 16 reveals a more serious related failure: the
incoming cry reads the wrong header and remains active beyond the bounded
test. It is recorded separately as `DEX-CRY-05`.

`TryLoadSampledCryBySpeciesIndex.found` in
[sampled_cries.asm](../audio/sampled_cries.asm) writes the incoming bank/address
to shared HRAM while interrupts and the old sample timer are still active.
`SampledCry_CopyNextCachedBlock` in
[sampled_cry_player.asm](../home/sampled_cry_player.asm) uses and advances that
same address as its live decoded-cache cursor. The two meanings overlap.

| T-cycle | Phase | Relevant state |
| ---: | --- | --- |
| 3,245,928 | Incoming metadata found | IME on; Metagross timer active; new Luxray header is `$8f:$53a0` |
| 3,246,472 | Old timer copies a block | Bank/address already replaced with `$8f:$53a0`; old remaining count is 441 |
| 3,248,008 | Loaded sampled cry dispatch | Shared incoming address is now `$53b0`; old remaining count is 440 |
| 3,248,140 | Async startup | `DE=$53b0`, not `$53a0` |
| 3,248,288 | Existing old-sample stop | Too late: startup already captured the corrupted pointer |
| 3,317,452 | Incoming playback armed | Block count is `$d19e`, or 53,662, instead of Luxray's 508 |

`PlayLoadedSampledCryWithPeriod` reads the shared header before entering
`StartSampledCryAsync`. Startup then disables interrupts and
`SampledCry_PrepareCacheFromHeader` stops an active old sample, but `DE`/`HL`
already contain the wrong header. The stop does not repair that value.

At offsets 0/4 the outgoing sample happens to exhaust earlier, avoiding this
specific race accidentally. That is why the symptoms can vary by timing.
Stopping the outgoing timer **before metadata lookup** prevents the race in
this owner. The shared loader deserves an explicit no-active-sample contract
or a future general transaction audit; failures in other owners were not
demonstrated in this investigation.

## Implemented Scoped Fix

`PokedexSelectedMon_CancelCry` lives in the existing Dex ROMX bank. Its three
ordinary `CALL` sites execute immediately after setting the accepted boundary
state in these mainline routines:

- `PokedexSelectedMon_ChangeSpecies`, before hiding or staging the next entry.
- `PokedexSelectedMon_Leave`, before Listing or linear-return restoration.
- `PokedexSelectedMon_Area`, before entering the separate Area owner.

Do not attach it to generic `Pokedex_CancelAnimationPrefetch`: warming and
other animation housekeeping also use that routine without ending audio
ownership. Do not cancel or restart the same cry for an A-button Description
text toggle. Area returns already rebuild/restart their Selected presentation.

The integrated helper performs the transaction previously tested in a private
prototype:

1. Preserve AF/BC/DE/HL and disable interrupts under a documented
   mainline, interrupts-enabled call contract.
2. If `hSampledCryTimer` is active, call the existing
   `StopSampledCryAsync_NoInterruptControl`. This restores the saved timer,
   CH3 and mixer state and ends the old sample before incoming lookup.
3. Clear only active synthesized-cry channels: require both
   `SOUND_CHANNEL_ON` and `SOUND_CRY`. Silence their corresponding hardware
   channels, including pulse sweep cleanup for channel 5.
4. If any active synth cry was canceled, restore a nonzero `wLastVolume` to
   `wVolume`, clear cry volume/priority bookkeeping and clear the channel
   6/8 pitch offsets. Leave music scripts and non-cry SFX channels intact.
5. Restore registers and enable interrupts on return. Continue the existing
   screen transition and start only the incoming owner's cry.

The order and guards are important:

- Stop sampled playback first. Its saved CH3/mixer restoration must not undo
  synth cleanup performed afterward.
- Do not call sampled stop unconditionally when inactive; its saved register
  values could be stale.
- Natural synth completion clears the active bit but can retain `SOUND_CRY`.
  Testing the cry bit alone would act on an already-finished channel.
- `SFXChannelsOff` clears software flags but does not immediately silence
  hardware or restore cry volume/priority. It also affects unrelated SFX.
- `RestoreVolume` is channel-5-specific and checks `wCurChannel`; calling it
  blindly at an owner boundary can return without performing cleanup.
- Do not use the helper's unconditional final `EI` from interrupt handlers
  or callers that require interrupts to remain disabled.

This deliberately truncates the outgoing cry when selection changes. It does
not wait for that cry, restart music, change the codec, increase prefill,
change refill cadence or touch the animation schedule.

## Cost And Performance

The assembled helper is 118 ROMX bytes. Three ordinary call sites add nine
bytes, for **127 additional ROMX bytes** in the integrated implementation.
Using only species-change and B-return would be 124 bytes, but Area should
follow the same ownership rule. The diagnostic overlay is 145 bytes because
it also has three prefix-preserving test stubs; those stubs are not needed in
production source.

| Resource | Added allocation |
| --- | ---: |
| ROM0 | 0 bytes, reuse the existing sampled stop |
| ROMX | 127 bytes, existing Dex bank `$a0` |
| WRAM0 and WRAMX | 0 dedicated bytes |
| HRAM | 0 bytes |
| VRAM or tables | 0 bytes |

The Dex bank had 2,458 free bytes and now has exactly 2,331 bytes
(`$76e5-$7fff`), without another bank or repacking. Register
preservation temporarily uses eight stack bytes; nested return addresses bring
the sampled cleanup's extra mainline stack footprint to 14 bytes, excluding
an interrupt before `DI`. This uses the existing stack, not new storage.

Measured helper costs, including an ordinary `CALL`/`RET`, are 392 T-cycles
with no active cry, 616-860 for the observed synth channel mixes/phases, and
820-928 for sampled playback. The inactive path reaches 500 when a short
interrupt lands before `DI`. The observed maximum is about 0.221 milliseconds
at normal speed, not a proven universal worst-case bound for every channel mix.
The existing transition waits absorb this work; see the timing comparison below.

## Alternatives And Tradeoffs

| Direction | Cost and complexity | Tradeoff |
| --- | --- | --- |
| Dex-local helper | Measured 118-byte body plus nine call-site bytes; no dedicated RAM/ROM0 | Narrowest change; mainline IME and channel-cleanup rules must be explicit. Recommended. |
| Shared ROMX `StopCry` API | About 136 bytes with three existing `farcall` sites, or 148 with call-site AF/HL preservation; estimate, not assembled | Reusable for later owners, but bank-switch overhead and a broader API/caller audit. Existing audio bank `$58` has 265 free bytes. No new ROM0 is inherently required. |
| Global cry-start/metadata transaction change | Byte cost requires auditing every entry point; no new data storage is inherently necessary | Can enforce safety across owners, but affects battle/fainted/Stats and other callers outside this task. Merely moving `DI` into async startup is too late. |
| Sample-only boundary stop | Smaller helper, but incomplete | Prevents outgoing timer exhaustion/race in the Dex while leaving the synth-resumption bug. |
| Refill through the transition | Extra runtime decoding and possible waits | Masks cache depletion but does not cancel frozen synth scripts or prevent the shared-header race. |
| Wait for the old cry or reset all sound | Small call-site changes | Waiting adds cry-length navigation delay; full reset disrupts music and unrelated SFX. Neither matches owner-change semantics. |

A shared API is reasonable when the Stats Screen or battle owners are
explicitly in scope. For this fix, the Dex-local helper reuses the existing
player safely without redesigning shared audio startup or allocating premium
resources. Its eligibility for reuse later is not acceptance of those other
owners today.

## Historical Prototype Validation

The unmodified primary baseline has 40 cases: five paging pairs and three
B-return species at offsets 0/4/16/40 and settled completion. It reproduces
four Mewtwo synth-resumption cases, ten outgoing cache-empty cases, and the
Metagross-to-Luxray header race. That race exceeds the 2,400-input-loop bounded
completion test. Four additional all-seen Celebi-to-Treecko controls confirm
two synth-resumption cases without a sparse seen fixture.

The private prototype expands offsets to 0/4/8/12/16/20/40 plus settled:

- 40 paging cases: Mewtwo to Dusknoir, Garchomp to Bastiodon, Dusknoir to
  Mewtwo, Metagross to Luxray and Chikorita to Bayleef.
- 24 B-return cases: Mewtwo, Dusknoir and Weavile.
- 10 normal all-seen neighbor/B-return controls.
- Two Description A-toggle controls with an active Mewtwo or Dusknoir cry.
- Two Area-entry controls with those active cries.

All **78 cases pass**. There are no outgoing or incoming cache-empty hits,
resumed outgoing synth notes, incoming header/block-count failures or
animation misses. Paging also passes Description shell/type graphics/palette
audits and exact authored publication, tilemap and pixel checks. Representative
full timelines retain Dusknoir's 174, Bastiodon's 205, Mewtwo's 111, Luxray's 92
and Bayleef's 81 display intervals; these include the complete generated
sequence, not an older partial timing target.

Description toggles retained the same cry without cancellation/restart. Area
entry stopped the outgoing timer/cry before showing that owner. These were
entry-only checks, not acceptance of Area round-trip navigation.

The original missing-root-ROM test run passed 178 host checks and skipped 116
linked/historical checks. The complete integrated run below supersedes that
limited result; no test expectations were relaxed to make it pass.

## Integrated Validation

All reports, isolated battery fixtures, matching ROM/symbol copies and raw
traces are under ignored `build/dex-cry-ownership-integrated/`.

| Suite | Result | Checks |
| --- | --- | --- |
| Cold Listing | 373/373 entries and B-returns pass | Full authored timelines, VBlank publication, tilemap/pixel data, natural completion for all 122 sampled species |
| Settled internal paging | 373/373 entries and B-returns pass | Same full animation/audio audits, including end-of-list wrapping |
| Focused ownership | 64/64 pass | Five paging pairs and three B-return species at offsets 0/1/2/4/8/16/40 and settled completion |
| Navigation controls | 14/14 pass | All-seen neighbors, early B-return, two active A-description toggles and two Area-entry checks |
| All-species active handoffs | 1,492/1,492 pass | Each of 373 species at offsets 0 and 16, both paging to its next all-seen neighbor and B-return |
| Observer equivalence | 4/4 pass | Checkpoint cycles, events, UI, rendered pixels and emulated state agree with observer disabled |
| Listing restoration | 21/21 plus follow-ups pass | Direct/paged/active/page-2 return, cache repair, scrolling, wrapping and re-entry |
| Host unit/linked contracts | 301/301 pass | Includes 21 cry ownership checks; frozen scheduler reference explicitly selected |

The integrated handoffs have no outgoing or incoming empty-cache hits, resumed
outgoing synth notes, bad incoming headers/block counts or animation misses.
At helper entry/return, AF/BC/DE/HL and SP agree, IME is restored enabled, and
the outgoing sampled timer and active synth cry channels are cleared. Linked
helper contracts cover all 15 active-channel combinations, inactive audio,
stale cry flags, zero saved volume and preservation of music/non-cry SFX.

Listing restoration retains correct visible palettes, zero white flashes and
the expected icon/cache contents. No input/graphics regression was found in
the covered Selected/Listing paths. This is headless cycle/state/pixel evidence,
not a waveform/listening assessment or certification of other display owners.
Warm entry and every possible rapid-input sequence are not exhaustively covered.

### Transition Timing

The committed category-fix ROM and integrated ROM were both booted through
normal controller input with matching isolated fixtures. Each comparison uses
time from accepted owner handoff, not time spent waiting to accept the button.
One normal-speed hardware display interval is 70,224 T-cycles.

- All 373 settled paging cases have exactly unchanged static-reveal and first
  animation-publication times. Their later settled B-return-to-input-loop times
  are also exactly unchanged.
- Across the 64 focused cases, accepted paging to the next Selected input loop
  changes by -140,092 to 0 T-cycles (up to 1.995 display intervals faster).
  B-return to the Listing input loop changes by -92,404 to 0 T-cycles
  (up to 1.316 intervals faster).
- In 20 matching Listing-restoration cases, accepted B-return to actual Listing
  reveal changes by -94,020 to 0 T-cycles (up to 1.339 intervals faster).
  Settled and page-2 returns remain unchanged; the gains are active-cry cases.

No measured transition increased. Removing outgoing timer/refill work can make
active-cry transitions faster despite the small added helper. These are separate
visible-reveal and input-loop metrics, not interchangeable endpoints or a
guarantee that every untested interrupt phase has zero timing difference.
`comparison.json` preserves the matched per-case results and both ROM identities.

### Deferred Area Stall

Additional normal-input Area round-trip checks exposed an existing Area setup
stall in both the unchanged category-fix baseline and integrated build. Open
Dusknoir, move the footer cursor Right three times, and press A. The Selected
state becomes `AREA_ACTIVE`, but `Pokedex_GetArea` never reaches its input loop,
so B cannot return.

The first nest-icon `Request2bpp` remains pending with size 1 and destination
`$87f0`. A six-display trace in each build reaches `Serve2bppRequest` at LY 146
on every call, with no `_Serve2bppRequest` execution. That routine accepts only
LY 144-145, so the normal fallback rejects the upload repeatedly. The added
Dex VBlank dispatch is already present in the baseline. This is not introduced
by cry cancellation; outgoing audio is correctly relinquished in the new build.

This finding is recorded under deferred `DEX-AREA-01`. A separate Area-owner
change could select an appropriate ordinary VBlank handler before its first
request, or provide measured Area-local upload service. Either needs the Area
entry/return graphics contract audited; neither is included in this fix.
The optional `--area-roundtrips` diagnostic intentionally reports the stall,
rather than treating an entry-only audio check as a successful round trip.

## Reproducing The Investigation

The retained tool is [cry_ownership.py](../tools/dex_timing/cry_ownership.py).
It requires matching ROM/symbols, accepted cold checkpoints, RGBDS and the
local SameBoy source. Use a separate output subdirectory of ignored `build/`.
Generated cartridges, fixtures, states, reports and raw traces are not tracked.

```sh
python3 -B -m tools.dex_timing.cold_listing \
  --battery build/dex-category-rendering-fixed/cold/input-copy.sav \
  --output build/dex-cry-ownership-integrated/cold --jobs 8

python3 -B -m tools.dex_timing.cold_listing \
  --battery build/dex-category-rendering-fixed/cold/input-copy.sav \
  --output build/dex-cry-ownership-integrated/paging --jobs 8 \
  --paging

python3 -B -m tools.dex_timing.cry_ownership \
  --checkpoints build/dex-cry-ownership-integrated/cold \
  --output build/dex-cry-ownership-integrated/focused --jobs 8 \
  --offsets 0 1 2 4 8 16 40 --navigation-controls \
  --all-species-handoffs --observer-control

python3 -B -m tools.dex_timing.listing_restoration \
  --checkpoints build/dex-cry-ownership-integrated/cold \
  --output build/dex-cry-ownership-integrated/listing-restore \
  --expect-fixed --follow-up --no-images

DEX_TIMING_REFERENCE_ROOT=build/dex-scheduler-reference-20260920 \
  python3 -B -m unittest discover -s tools -p 'test_*.py'
```

The first ownership run generates normal-input sparse Listing checkpoints.
Later runs can add `--reuse-states`; provenance must still match. Use separate
cold/paging output folders to avoid replacing one suite's reports with another.
For a frozen baseline, explicitly provide its `--rom` and `--sym`, and matching
cold checkpoints. The baseline ownership run returns a failure for the
Metagross-to-Luxray header race; this is expected evidence, not a runner crash.

The historical `--prototype` mode assembles
[cry_ownership_cancel.asm](../tools/dex_timing/probes/cry_ownership_cancel.asm)
and overlays verified unused ROMX bytes plus the three accepted boundary
prefixes in a private cartridge only. It refuses changed prefixes or a
nonmatching free-space layout. It requires the old baseline map/layout, is not
applicable to the integrated production link, and is no longer needed for
routine regression. It is historical evidence, not a distributable patched ROM.

The full unittest command must select the frozen timing reference for historical
linked model tests. Those tests intentionally encode its instrumented addresses
and instruction costs; running them against a newer production link is not a
valid timing comparison. Current linked cry-helper tests still use the root ROM.
