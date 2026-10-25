# Selected Backlog Investigation History

> Historical excerpts preserved before consolidation on 2026-09-21. Statuses
> and proposed explanations below belong to their respective investigation
> stages. The [live backlog](../../pokedex_selected_bug_backlog.md) is the
> authority on current status; none of these excerpts closes a deferred bug.

These entries retain the original measurement progression without making the
live backlog a second scheduler investigation log. The Description-page claim
about a missing lower VBlank bound is superseded: the current handler checks
that bound. Its old explanation is preserved as history, not a current finding.

### DEX-ANIM-01: Work scheduling falls behind authored publication deadlines

Status: Reported cold-entry/internal-paging stress suite passed; release cleanup pending

The 2026-09-20 implementation replaces the per-call micro-schedule with useful
work selected on the hardware display clock, independent completion tracking,
bounded finishing, cheaper gather/queue copies, quiet publication ownership and
owner-local pacing/audio sequencing. All ten linked full-sequence cases match
SameBoy instruction-for-instruction and meet every authored deadline; 60 further
timer-phase controls pass. No extra RAM/VRAM allocation is used.
The user subsequently tested cold Listing entry and internal paging across the
Weavile-to-Exeggcute set, covering the replay species plus Mewtwo, without hitting
the animation-miss breakpoint. Warm Listing entry was deliberately not tested;
the remaining ownership/exit cases are not all signed off. Rapid paging exposed
the separate outgoing-cry cancellation issue `DEX-CRY-04`, not an animation miss.
See [implementation](../../pokedex_animation_scheduler.md) and
[results/test procedure](../../dex_scheduler_validation.md).

The expanded 2026-09-20 suite found two Groudon misses, at events 13/14. The
actual current-link replay matches the core and both captures exactly. The
three-event high-water horizon prevents early decoding during repeated poses;
the later new poses arrive before their source tiles are decoded. A host-only
control raises later targets without increasing startup and clears both misses
while preserving all 211 authored intervals and natural cry completion. The
diagnosis, fix direction and validation gates are
recorded in [Groudon decode-lookahead results](dex_groudon_target_results.md).
The follow-up [15-species regression](dex_target_regression_results.md) passes
all 105 earlier-decoding candidates (nominal plus six timer phases), including
Milotic, Drapion, Rhyperior and Yanmega. Both nominal policies match the
independent core exactly. No sampled-cry, map, timeline or transfer regression
was found. This established the proposed generator change before implementation.

The subsequent Spheal/Sealeo/Snorlax unused-tail regression passes all 21 new
candidate cases (42 baseline/candidate runs), bringing the candidate matrix to
126 runs across 18 species. Spheal's eight additional decode calls do not shift
any publication or cry-completion timestamp; the two fully preloaded controls
also preserve timing. All nominal replays match the independent core. See the
follow-up section in the same results document.

The approved target rule is now implemented and rebuilt: event 1 is unchanged,
and later events target the complete dictionary. The compiled ROM passes all
126 replay cases, with 18 exact independent-core comparisons and no added
runtime instructions or storage. Startup lead, work quotas, VRAM ownership,
audio prefill and publication deadlines are unchanged. The user has now tested
cold entry and internal paging across all previously tested sampled species and
thirteen named synthesized controls, with neither miss breakpoint firing.
Warm entry remains deliberately untested and Listing warming is still present.
This validates the reported settled-playback cases; cleaned-build regression,
remaining ownership/exit cases are not automatically signed off. See the
validation guide's latest acceptance record.

The user subsequently completed the entire New Dex through internal paging,
with no uninterrupted-playback miss hits. The normal-input headless SameBoy
cold suite now also passes animation/audio playback for all 373 species,
checking every published frontpic, exact hardware-interval timing and natural
sampled-cry completion. Its additional static-reveal check exposes Drapion's
text overflow below (`DEX-UI-02`); 372 species pass that check as well.
See [cold Listing results](../../dex_cold_listing_results.md). This does
not close the deferred description/input/transition bugs or eliminate the need
to rerun after instrumentation removal.

2026-09-21 presentation follow-up: the user reports no visible animation issues
for synthesized-cry Chikorita, Bayleef and Meganium, or sampled-cry Dusknoir,
Rampardos and Luxray. B-return palette errors still occur (`DEX-GRID-01`), and
the user confirms Drapion's static-portrait text overflow (`DEX-UI-02`). The
new directional-input issue is recorded separately as `DEX-NAV-02` below.

The following paragraphs preserve the historical investigation stages and their
then-current limitations; statements about no installed fix refer to those stages.

The 2026-09-19 host replay matches the Weavile and Luxray five-stop captures'
core state and timer readings within their measurement uncertainty. Their
producer-call-index schedule loses ground when owner work crosses VBlank before
the next wait is armed; Luxray also reaches an HDMA launch window too late.
Both first-miss cases have fully decoded dictionaries but unfinished uploads.
This is not evidence that the hardware cannot meet the authored animation timing.

The proposed direction is display-clock-based work release with independently
tracked completion, early preparation when slot ownership permits it, bounded
upload/wait scheduling, and unchanged deadline-controlled atomic publication.
It must not skip unfinished work or stretch animation holds to hide failure.

Detailed evidence, build/fixture identities, remaining model uncertainty, code
touchpoints, next validation cases, and final-review gates are preserved in
[Selected Dex Scheduler Investigation](dex_scheduler_investigation.md).
The 2026-09-20 [publication-budget follow-up](dex_publication_budget_results.md)
records successful host-only phase/cost controls, the redundant empty-OAM
transfer, a ready-frame deferral that causes a later upload miss, and the
remaining publication safety bound. These experiments do not close this bug
or constitute a game fix.
The subsequent [steady-display recovery tests](dex_steady_publication_results.md)
bound that quiet publication path and pass the three actual-state phase/cost
suites. Broader partial-state controls retain Garchomp's event-5/frame-4 failure
at 20/30 uploaded tiles despite a fully decoded dictionary, in all 17 runs.
Next is a complete-chain work budget in place of the fixed eight-tile suffix
heuristic. No runtime fix or generalized signoff has been made.
The [Garchomp finishing follow-up](dex_garchomp_finishing_results.md) adds six
new actual starting states, all independently core-calibrated, and a complete-chain
admission candidate. All nine actual sampled-species nominal runs now pass without
larger preload; Garchomp still fails one phase control and two overhead settings.
The missing margin, actual post-cry timer cost, and queue/gather optimization
direction are recorded there. This is host-only progress, not closure of the bug.
The subsequent [queue-copy optimization](dex_queue_construction_results.md)
removes 3,216 T of counted copy-loop overhead without changing map ownership.
On top of the host scheduler candidate, 316 phase/cost/combined continuations
now pass, including all known Garchomp counterexamples. No game fix is installed;
the remaining concrete guard-cost, synthesized-cry and input-handoff validation
gates still apply. The bug remains open.
The [headroom/synth investigation](dex_headroom_synth_results.md) then adds a
fixed tile-copy optimization and an 8,192-T finishing reserve. Its 328 final
phase/cost continuations pass, with a minimum accepted finishing margin of
8,232 T (Garchomp: 12,120 T rather than 556 T). Exeggcute's actual active-synth
baseline is independently core-calibrated; candidate runs preserve its sound
updates, hardware-write sequence and completion frames. This removes the known
tiny finishing margin and adds one genuine synth control, not generalized
runtime or all-synth signoff. Implementation costs and input/owner paths remain
gates. No game fix is installed; this bug remains open.
The separate Description-page transaction bug remains `DEX-DESC-01` below.

### DEX-CRY-01: Dusknoir's sampled cry underruns on the Selected page

Status: Uninterrupted live cold-entry/internal-paging checks passed

2026-09-20: The integrated Dex scheduler completes the sampled cries without an
underrun in all nine sampled-species baseline replays and their phase controls,
with the 32-block prefill retained. The user's subsequent live cold-entry and
internal-paging tests did not hit the cache-empty breakpoint during uninterrupted
playback. Hits while rapidly changing species were isolated to `DEX-CRY-04`.
Warm entry and the remaining ownership/exit cases are not all signed off.
This does not close the independent Party Stats/battle issues or the
synthesized-cry cancellation issue below. Earlier measurements follow as history.

The final target-correction build also passes the user's expanded sampled-cry
suite on cold entry and internal paging without either miss breakpoint firing.
The compiled host matrix has 112 natural sampled completions across sixteen
species and seven timer phases each. A cleaned-build smoke test is still needed
after instrumentation removal; warm entry was intentionally not tested.

The all-species cold Listing suite subsequently completed all 122 sampled cries
naturally with no cache-empty hits while checking the full animation sequences.
The user's complete internal-paging pass likewise had no uninterrupted-playback
misses. Rapid-paging exhaustion remains separately deferred as `DEX-CRY-04`.

Cry playback has been restored. Baseline instrumentation confirmed that
Dusknoir can exhaust its decoded cache while compressed blocks remain during
concurrent frontpic production. The exact-resident animation-stage fast path is
working as intended but is insufficient by itself:

- Cold Listing-to-Selected and internal Mewtwo-to-Dusknoir runs reduced stage
  builds from 33 to 14 and increased audio production from 216 to 240 blocks,
  but both still underrran with 126 of 366 blocks left compressed.
- A warm Listing-to-Selected run reduced stage builds from 32 to 13 and
  increased audio production from 312 to 344 blocks, but still underrran with
  22 of 366 blocks left compressed.
- Reveal and playback timing did not regress, and none of these runs recorded
  an animation underrun.

Metagross is a useful pre-fast-path baseline control: a cold
Listing-to-Selected run completed with no audio or animation underrun, zero
compressed blocks remaining, and a minimum decoded-cache depth of five blocks.
A post-fast-path repeat remained clean, reduced stage builds from 21 to 15,
and increased its minimum decoded-cache depth from five to ten blocks.

### DEX-DESC-01: Toggling description pages can corrupt the upper screen

Status: Open

Pressing A to switch between an entry's two Description pages can corrupt the
frontpic, header, and other portions of the upper seven tile rows. The failure
is distinct from an animation underrun and occurs during the complete backing
tilemap/attrmap copy used by the page toggle.

This is a tilemap transaction race, not an animation underrun. The A path
redraws the complete backing map through [`CopyTilemapAtOnce` (line 57)](../../../home/tilemap.asm#L57),
while the animation controller can still have a seven-row portrait publish pending.

[`Pokedex_VBlankAnimationFrontpicMap` (line 1306)](../../../engine/pokedex/pokedex_3.asm#L1306)
rejects scanlines 146 and later, but never verifies that rLY >= 144.
If the full-map copy delays the VBlank interrupt, the pending handler can
consequently run during visible scanlines 127–143 and treat them as VBlank.
That explains Meganium’s corrupted header, portrait, and horizontal screen
sections immediately after toggling descriptions.
