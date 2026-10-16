# Interactive New Dex Registration Prototype

Original prototype date: 2026-10-15. Accepted production integration: 2026-10-16.

## Status And Inputs

**2026-10-16 production integration:** the user accepted the corrected build
and explicitly retained its 20 reviewed temporary evolution requirements.
Root ROM/symbols/map match the fully qualified review build exactly; fresh root
checks pass. The main save is unchanged. See
[integration and current costs](pokedex_interactive_registration_integration.md).
The earlier unchanged-production/private-only statements below describe their
original review phases, not the current status.

**2026-10-16 qualified update:** the synchronized LCD-on handoff and Pay Day
context fix are now folded into the current prototype. The full regression and
all-species registration qualification pass with the documented baseline
exceptions and five timing-only Info alerts. The new review ROM, private saves,
recordings, timings and complete results are in
[the capture-fixes review](pokedex_registration_capture_fixes_review.md).
Production and the player's main save remain unchanged. The remainder of this
document preserves the original 2026-10-15 build and its subsequent correction;
its 64-byte context and four-alert figures are historical, not the latest build.

**2026-10-16 correction:** manual capture review found a new false Pay Day payout
and an unacceptable visible Gotcha speed-handoff flash. The earlier capture
suite did not compare the wallet and therefore missed real money corruption.
The reviewed ROM below is preserved, not approved for promotion. Independent
fixes, options, costs, recordings and focused qualification are documented in
[the capture investigation](pokedex_registration_capture_handoff_investigation.md).

The 2026-10-15 automated qualification had reported no new functional
regression against the frozen production baseline. Existing baseline
exceptions remain explicitly recorded. Human visual/listening approval and
the four responsiveness alerts remain for manual review. This is not a
production integration or a claim that every historical test is clean.

- Production commit: `3ed28c430b67e8a7c695459a568fc71568cfb7df`.
- Protected production ROM SHA-256:
  `52ba945b4b5e94107495988265401c586ea359212637b666e47df58abe25c7a5`.
- Frozen candidate: `build/interactive-registration-dev07-20261015/candidate/`.
- Candidate ROM SHA-256:
  `1abe990d9d96ef34a910e444c6990aa9e745c8827d48946834aa179a29cc8634`.
- Candidate symbols SHA-256:
  `16ad83afc8b86c30d542c0c1804fa88452e7f97e9dd0205e13b81fa07b5f3bb6`.
- Matching full-suite source copies, rollback ROM and source archive:
  `build/interactive-registration-full-20261015/`.
- Review ROM, symbols, map, private save and media:
  `build/interactive-registration-review-20261015/`.

The root production ROM, production runtime/data sources and player's main
save are not changed. Test tools and documentation are normal repository
changes. Temporary evolution requirements must not be mistaken for a final
game-design decision when this prototype is considered for integration.

## Behavior

Registration opens the newly caught or awarded species on Desc P.1.
Left/right moves the shared blinking footer arrow over Desc, Info, Mov and End;
A activates the highlighted choice. A on Desc toggles its two description
pages. Returning from Info or Mov starts Desc P.1. A on Info or Mov cycles
their existing internal pages and wraps with the regular Selected conventions.

Info contains Stats, configured forward Evolutions, and Evolves From. Mov
contains the species' Level Up, TM/HM, Tutor and Breeding pages, not just the
captured individual's moves. Viewing pages does not mark moves seen. There is
no Area tab, species navigation, fabricated Listing, sort change or bookmark
update. B from any tab or A on End cancels work and returns once to the
original capture/prize continuation.

The portrait uses the Selected screen's authored streaming sequence and cry.
Tab changes neither cancel nor restart either. Natural completion remains
completed; this is not an indefinitely looping idle animation. Explicitly
leaving registration cancels remaining playback and pending publication.

The previously qualified Gotcha music-reset handoff switches a successful
capture tail to double speed before registration. EXP, learning, naming,
post-battle evolution and map return retain that speed policy. This does not
change the normal-speed battle animation owner or add interrupt work.

## Runtime Architecture

`tools/dex_timing/probes/interactive_registration.asm` replaces only the private
copy of `engine/pokedex/new_pokedex_entry.asm`. It initializes a fixed species,
permanent identity, live ID lock, page state, display dispatch and palettes.
It reuses existing Selected preparation, foreground services, bounded
lower-panel jobs and VBlank publication. It does not call Selected's Listing
entry/update/leave controller, which would introduce Listing dependencies and
species paging.

Retained resident registration helpers are not removed in this prototype.
Their old helper matrix is still tested, but it is not counted as streaming
owner coverage, and no speculative retirement credit is subtracted from cost.

The owner loop services description animation first and the active lower
panel afterwards, using existing admission and pacing. The prepared-animation
entry label is placed before the existing WAITING-state guard, after only the
Listing-specific guards. Calling it for an already running/completed portrait
must not replay the cry or reset animation. A host negative control checks
this placement.

The controller saves a 64-byte context in already allocated, inactive
`wTempTilemap` storage in WRAMX bank 2: 32 bytes of battle graphics-prefix
state, 28 scalar bytes, the two-byte previous Dex identity and the two-byte
old Selected lock's permanent identity. No new WRAM allocation is made.
The old lock is restored by permanent identity, not by a transient ID that
garbage collection may have recycled. Order/bookmark/discovery state is not
borrowed as scratch space.

On exit it cancels description/Info/Mov work, streaming prefetch and cry,
clears dirty/pending ownership, restores context, and runs the original
post-registration DV/font/palette continuation. The old battle prefix is
restored semantically but CLEAN and inactive producer claims are cleared:
registration replaced the old VRAM/payload, so claiming those assets remain
clean would be wrong. Both Game Corner prize return paths now rebuild map
blocks with `ReturnToMapFromSubmenu` before `ExitAllMenus`.

### Banked Numeric Pointer Dependency

Completing the evolution graph added enough generated Info metadata to exceed
its former combined bank by 1,763 bytes. The existing 2,048-byte
`PokedexInfoNumbers` pointer table was relocated, not duplicated, into spare
space in the existing Info glyph bank. Semantic evolution/ancestor metadata
remains local to the Info code. This is not the previously rejected runtime
glyph architecture.

Stats planning copies one eight-byte numeric-pointer row through
`FarCopyBytes` into the first eight inactive `wPokedexInfoMiniGFX` staging
bytes. Stats has no mini producer; the prior committed evolution minis are
already in VRAM. Do not add a concurrent mini producer or reuse this staging
prefix during Stats planning without revisiting this alias.

The fixed cost is 672 CPU T-cycles per row: 0.080109 ms / 0.004785 display
frames at double speed, or
0.480652 ms / 0.028708 display frames across all six numeric rows, CPU-only.
The worst modeled row is 14,224 CPU T-cycles and fits the existing 18,498-cycle
conservative budget after the guard and finish reserve. No admission threshold
was widened to accommodate this change. This calculation does not replace
native end-to-end page timing.

Linked-CPU numeric-pointer qualification executes 256 values x six rows x two
ROMs: 3,072 linked planner cases in the host CPU interpreter, checking source
pointers, bank restoration and the eight-byte staging boundary. These are not
native SameBoy gameplay runs. Host checks separately compare all 1,024
numeric glyphs with production, measure 30 row-cost cases and enforce the
original budget.

## Cartridge And RAM Cost

All values below are decimal linked bytes against protected production.

| Component | ROMX bytes |
| --- | ---: |
| Qualified Gotcha speed/fade boundary | 219 |
| Interactive owner replacement and prize return changes, net | 567 |
| Banked numeric-pointer transport code | 14 |
| Added gameplay evolution rows | 268 |
| Added generated Info semantic/pointer data | 3,510 |
| Added deduplicated Info glyph tiles | 880 |
| Total | 5,458 |

Allocated growth is zero for ROM0, WRAM0, WRAMX, HRAM and SRAM. The 64-byte
context and eight-byte numeric staging row are aliases in existing inactive
storage, not new capacity. No save version/migration is introduced.

The candidate uses 2,365,146 of 4,194,304 cartridge bytes; 1,829,158 bytes
remain free (43.61%). Info's bank has 271 bytes remaining and its glyph bank
has 3,263 bytes remaining, so future data growth may require another ownership
or bank-layout decision despite substantial total cartridge capacity.

The linked section audit independently sums the same 5,458 bytes: evolution
sections +24/+36/+208, Info code/data +1,476, Info glyphs +2,928, bank3 +9,
bank3E +564 and bankB +213. Moving the 2,048-byte number-pointer table accounts
for opposite changes within the two Info sections; it is not additional data.
The Selected Moves section has zero byte growth.

Zero added ROM0 allocation does not mean every ROM0 byte is identical: the
global checksum and existing far-call target operands change when ROMX labels
move. Actual shared VBlank/LCD/delay paths and the Selected publication bank
are checked byte-for-byte unchanged; no new shared ISR work is introduced.

## Evolution Test Data

The prototype adds all 67 missing links: 47 original requirements supported
by existing methods and 20 explicitly approved temporary requirements. There
are now 190 direct links across all 373 species. All 123 existing evolution
rows and every learnset are preserved. Delcatty's first-stage metadata is
corrected from Delcatty to Skitty in the private candidate.

The independent pinned reference is the
[Platinum game-data reconstruction](https://github.com/pret/pokeplatinum/tree/1dc13dcea40c04ab53f1f607de46023dc409ef20/res/pokemon).
The source/linked audit checks all 373 direct, forward, ancestor and first-stage
records, plus ordered-method reachability witnesses for all 190 direct links.
It has 12 audit/negative/branch tests. These are structural/linked-data checks,
not a claim that every evolution was played through as a normal battle.
Electivire and Magmortar are outside the current roster; their two links are
listed separately by the audit and are not silently introduced as new species.

Completing the graph also connects existing family breeding-move streams in
the Selected Mov index. Ambipom, Mismagius, Honchkrow, Weavile, Lickilicky,
Rhyperior, Tangrowth, Togekiss, Yanmega, Leafeon, Glaceon, Gliscor and Mamoswine
gain the corresponding family entries: 13 species, 16 additional visible pages.
The base-species page total changes from 2,576 to 2,592. This reuses existing
arrays/pointers and adds no Moves-section ROMX bytes; it does not invent new
move lists or change the preserved raw learnsets. Tests that explicitly assumed
those evolution links remained deferred must use the actual source graph.

### Temporary Requirements

| Link | Prototype requirement | Original unsupported condition replaced |
| --- | --- | --- |
| Magneton -> Magnezone | Level 40 | Magnetic-field location |
| Lickitung -> Lickilicky | Level 33 | Knowing Rollout |
| Rhydon -> Rhyperior | Trade holding Metal Coat | Protector |
| Tangela -> Tangrowth | Level 40 | Knowing AncientPower |
| Eevee -> Leafeon | Leaf Stone | Moss Rock; Leaf Stone is also a later canonical alternative |
| Eevee -> Glaceon | Moon Stone | Ice Rock; avoids collision with Vaporeon's Water Stone |
| Togetic -> Togekiss | Sun Stone | Shiny Stone |
| Aipom -> Ambipom | Level 32 | Knowing Double Hit |
| Yanma -> Yanmega | Level 33 | Knowing AncientPower |
| Murkrow -> Honchkrow | Moon Stone | Dusk Stone |
| Misdreavus -> Mismagius | Moon Stone | Dusk Stone |
| Gligar -> Gliscor | Level 40 | Razor Fang at night |
| Sneasel -> Weavile | Level 40 | Razor Claw at night |
| Piloswine -> Mamoswine | Level 40 | Knowing AncientPower |
| Porygon2 -> Porygon-Z | Trade holding Up-Grade | Dubious Disc |
| Kirlia -> Gallade | Sun Stone, no gender check | Male plus Dawn Stone |
| Roselia -> Roserade | Sun Stone | Shiny Stone |
| Feebas -> Milotic | Water Stone | Beauty threshold |
| Dusclops -> Dusknoir | Trade holding Spell Tag | Reaper Cloth |
| Snorunt -> Froslass | Moon Stone, no gender check | Female plus Dawn Stone |

The complete 67-link table and 373-species family table are in
`build/evolution-audit-20261015/qualification-dev07/report.md` and `.json`.
The patch is `tools/dex_timing/probes/interactive_evolutions.diff`, SHA-256
`9507d176ad24e37b2ec2baea5c9d8628ce91fd176f710f83a0769a8757ffe94a`.
Existing Info uses the generic friendship label rather than spelling out
day/night; the underlying Riolu daytime condition is preserved in gameplay
data. That preexisting presentation convention is not a new evolution method.

## Qualification Evidence

The all-species streaming campaign and all 34 surrounding-game actions are
complete: 16 standard actions including report, 13 supplementary, three
capture and two independent Tower actions. The support audit has no missing
action and records no new failures. It deliberately leaves its own
`full_qualification` false because the parent separately adjudicates the
all-species matrix, data audit and manual review. These evidence sets all
refer to the same frozen ROM; manual approval is still not implied.

- Context/architecture contracts: 9 tests, no failures, errors or skips.
- Evolution audit: 373 species / 190 links, no mismatches; 12 audit tests pass.
- Special returns: 10 cases pass, covering B/End for contest/Celebi fixtures,
  actual Transform catch, Goldenrod Abra and Celadon Pikachu prize scripts.
- Forced-GC/cancellation case: passes; old identity 373 is restored after its
  transient ID was recycled. Pending description work is cleared on return.
- Private review save: normal Continue reaches the overworld without edits
  to the seed or main battery.

### Broad Regression And Retained Exceptions

All 15 standard non-report phases are complete. This includes the 4,479-case
Dex matrix, standalone Moves/search/persistence/discovery, 1,600 standard
battle-move scenarios, gameplay/menus/audio/transition checks, both 373-species
Modern and Legacy cold/paging/warm matrices (2,238 scenarios), readiness,
gift/Struggle, chart, shared arrows and linked host checks. The linked host
group passes 87/87 on both baseline and candidate, with no skips. The older
historical host group retains the exact same 6 failures, 16 errors and 103
skips among 187 checks on both; those are not silently described as clean.

The all-animation campaign completes 7,312 renderer calls, 3,656 paired
comparisons including all 333 moves from both sides, and 1,332 normal-input
cases (666 pairs). Renderer visual/logical sequences, restoration and timings
match production exactly: minimum/median/maximum duration delta **0 ms /
0 display frames**. Native coverage is complete; 632 pairs are clean and
34 retain identical preexisting issue identities, with zero differing-issue
pairs. The 34 include condition-specific fixture limitations, older menu/end
expectations and the two Sand Tomb hangs. This does not fix that separate bug.
Evidence: `build/interactive-registration-full-20261015/all-animations/report.json`.

Two harness corrections were necessary and their original failures are kept
under `orchestration/dex-source-root-repair/` and `host-contract-repair/`.
Mode-transition expectations were accidentally compiled from the root's old
graph rather than the candidate. Host snapshots likewise assumed deferred
breeding inheritance, a four-page maximum and the old numeric row cost. The
repaired checks use matching raw source, independently parse family breeding
lists, retain original expectations on the old graph, and require the banked
Stats rows to be exactly 672 CPU T-cycles more than each production row while
remaining below the unchanged actual gate. They do not just raise a timeout
or accept a new unexplained failure. Both ROMs are replayed after correction;
runtime code remains frozen.

The catch-tail campaign exposed a third harness defect, preserved under
`orchestration/no-dex-fixture-repair/`. The old "no-dex" fixture cleared bit 1
(Unown Dex), not bit 0 (Pokedex). Its old-production cases still entered
registration, and the driver's held A automatically dismissed the old two
pages, creating a false-positive bypass result. The interactive screen does
not exit on repeated A, which made the mistake visible. The repaired fixture
derives `STATUSFLAGS_POKEDEX_F` from source, checks the native Dex query returns
A=0/Z set, advances without silently dismissing registration, and requires zero
registration entries. Eight fresh baseline/candidate phase replays pass and
restore the 104-case gate. Prior Gotcha no-Dex claims from that fixture are
superseded; there was no game-code defect or production-ROM change.

The following-catch driver also assumed the next wild species was already
registered and waited for `skip_pokedex` with held A. A genuinely unseen
second catch correctly opens New Entry. The driver now checks pre-catch Dex
ownership/caught identity, handles the expected resident/streaming owner and
exits via B, checks exactly the expected entry count, and verifies delivery
and return. Four fresh following-catch replays plus the four passing fight
cases complete the eight-case supplement. Original traces and its two failed
candidate attempts remain under `orchestration/following-capture-repair/`.

The 104-case catch-tail matrix and eight following-battle cases have no new
failure or changed miss identity. The main matrix retains 16 known sampled
cry misses per ROM, and the supplement retains four per ROM: the Dusknoir
battle-introduction sample stops with 45 blocks remaining, before Gotcha or
registration. These are not new registration underruns and are not fixed
by this work. New Entry's all-species playback tests remain clean.

Supplementary results include 1,492 active all-species Description returns,
1,536 return cases across six CGB models, 336 lifecycle cases, 36 secondary
routes, 88 hardware exit cases, and 12 button-audio register/timing comparisons.
No new failures, premature reveal frames or unexplained cue differences are
present. Standard persistence includes 2,380 helper, four snapshot, 1,490 cold
boot, 152 interrupted-write, 150 interrupted-repair and five lifecycle cases.
The wider sampled-audio campaign has 960 cases; Selected entry timing has
1,024. These overlap other checks and must not be summed as a grand scenario
count.

Ordinary Dex lifecycle medians remain production-like: entry 444.695 ms /
26.5605 frames, exit 711.637 ms / 42.5043 frames. Paired median changes are
+0.000477 ms / +0.000028 frames on entry and -0.000477 ms / -0.000028 frames
on exit, effectively instruction-boundary measurement differences rather than
a perceptible transition change.

### Independent Tower Result

The independent Tower addendum completes 6,728 checks, including 140 native
battles per ROM: 70 regular-move and 70 Struggle cases. Coverage is complete,
all native battle-owner returns complete, and there are no new failure
identities. The Tower is not clean: ten prize-routing cases and one related
UI case fail on each ROM, matching the already deferred reward-pocket issue.
Evidence: `build/interactive-registration-full-20261015/battle-tower/report.json`.

Two first-budget overruns complete within the existing bounded continuation,
also with the original cadence; their actual turn/HP progress and initial
attempts are retained. Two other Struggle timeouts were a host-driver bug.
Both battles were already won (`wBattleEnded=1`), with a stale party-action
flag 2 and two fainted slots. The driver kept sending party-navigation input
at victory text instead of A. Gating party steering on battle-not-ended
allows the original matching checkpoints to return after 130 frames /
2,176.552 ms and 144 frames / 2,410.950 ms, without forcing any game state.
Four fresh matched replays pass with the normal battle/restoration contract.
Six additional focused host input tests preserve the victory guard, alongside
the four existing Tower oracle/gate controls; all ten pass.
No game-code fix or enlarged budget was used. The initial failures, second
budget attempts, screen/CPU context and fresh replays are retained under
`orchestration/tower-victory-input-repair/`, `tower-context/` and
`tower-original-cadence/`. The separate Tower runbook now documents the guard.

Final support evidence is `orchestration/audit.json`; it checks protected
production/main-save hashes and lists every action, original failure and
repair receipt. Final observer/harness sources are frozen in
`orchestration/harness-final/manifest.json`. The review package's combined
qualification record separately checks the all-species and evolution evidence.

### All-Species Streaming Matrix

`build/interactive-registration-tabs-20261015/summary.json` identifies the
final ROM/symbol hashes and requires the full declared coverage plan:

This streaming matrix uses the native SameBoy CGB-E core. The surrounding
suite's six-model Selected/Type/Unown checks are separate coverage; they do
not turn this into an all-373 registration test on every hardware model.

| Dimension | Completed |
| --- | ---: |
| Regular Selected species controls | 373 |
| Registration species/forms, including all 26 Unown letters | 398 |
| Registration page/tab requests | 7,369 |
| Unique Description pages | 796 |
| Unique Info pages | 772 |
| Unique Mov pages | 2,617 |
| Directed tab pairs | 2,388 |
| Unique committed-page B/End exits | 8,370 |
| Total exit attempts including queued-page checkpoints | 24,102 |
| Supplemental pending-exit probes | 9,364 |
| Total exit replays | 33,466 |
| Four-phase input stress cases | 12,736 |
| Negative controls | 15 |
| Correctness/playback failures | 0 |

Stress families are rapid tab switching, rapid Info paging, held A,
directional input without species navigation, tab changes around animation
finish, tabs after natural finish, early B and early End. Checks include
actual published/displayed portrait pixels, authored timing, no replay/restart,
sampled wave blocks/frequency, synthesized playback signature, semantic lower
content, read-only discovery/bookmark state and cleanup/continuation ownership.

The initial matrix samples queued state before the host signals the button:
4,682 B cases are pending at that point, and zero End cases remain pending
after normal footer travel. That alone does not prove pending state at the
actual exit dispatch. Supplemental physical-input probes use one-frame taps
and Right+A together from Mov to choose End and activate it in one poll.
They observe the actual leave boundary before cancellation: 2,830 pending Mov
End cases, 2,830 pending Mov B cases and 160 pending Info B cases all pass.
Pending Description B/End and Info End were not observed at dispatch; those
jobs can finish before the button is handled. Do not claim that coverage.
All committed B/End exits are complete. The Egg is not a registerable species
and is intentionally outside the 373-species roster. Full proof is retained
in `pending-exits.json`, alongside the original pre-input measurements.

The 15 negative controls detect missing/wrong/late animation publication,
render-only portrait corruption, sampled cache starvation, cry restart,
missing wave blocks, wrong complete lower pixels, altered ROM/fixture
manifests, invalid species/form/boundary fixtures and a stale identical wrap
frame. Host timing/coverage tests add 12 unit tests, including explicit
publication-versus-display and stale-frame controls.

Contest/Celebi tests declare special battle types on a Route 30 encounter;
they do not play through contest scoring or the Ilex event script. Prize
tests initialize saved-map objects and then use actual controller-driven
vendor scripts, delivery and coin deduction. Forced GC directly calls the
collector after playback settles; it is helper coverage, not normal-game
timing. Reports are in `build/interactive-registration-returns-20261015/`
and `build/interactive-registration-returns-gc-20261015/`.

### Timing Definitions

Physical display time uses 4,194,304 T-cycles/second and 70,224 T-cycles/frame:
one display frame is 16.742706 ms. CPU double speed does not halve a display
frame. Request-to-publication measures the accepted controller request until
its fresh lower-panel publication. Request-to-displayed additionally waits
for the first subsequent complete visible frame. Input-to-displayed starts
at the host key press and therefore includes polling/input phase.

A page whose pixels equal an earlier page still requires fresh publication;
an already visible identical frame cannot satisfy a new request. The initial
measurement accidentally allowed that case for wrap operations. Revision 2
recomputes from retained unchanged-ROM traces, with a stale-frame negative
control; no runtime change or relaxed timing threshold is involved.

Twenty matched species use both regular Selected and registration in the
same candidate, so the comparison isolates controller behavior with identical
evolution data and numeric transport. These are not old-production versus
new-registration comparisons. Production has no corresponding interactive
registration tabs, and lacks the added graph links.

### Twenty-Species Tab Timing

The continuous campaign has 345 paired operations. Median paired
request-to-displayed delta is +0.161648 ms / +0.009655 frames; maximum is
+33.565998 ms / +2.004813 frames. Including host input polling, median paired
input-to-displayed delta is +1.928329 ms / +0.115174 frames; maximum is
+35.409927 ms / +2.114946 frames. These are sample medians across matched
operations, not repeated-trial statistical confidence bounds.

All cells below are **milliseconds / display frames**, measured from accepted
request to first complete displayed frame after fresh publication. A tab
selection opens the first page of that tab. Internal paging is listed
separately because its cost depends on the species' page content.

| Operation | Pairs | Selected median | Registration median | Selected max | Registration max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Select Desc | 40 | 48.81 / 2.92 | 48.99 / 2.93 | 48.81 / 2.92 | 48.99 / 2.93 |
| Select Info | 60 | 65.51 / 3.91 | 65.67 / 3.92 | 116.39 / 6.95 | 116.20 / 6.94 |
| Select Mov | 60 | 97.96 / 5.85 | 82.60 / 4.93 | 133.27 / 7.96 | 115.68 / 6.91 |
| Desc internal page | 40 | 49.46 / 2.95 | 49.44 / 2.95 | 66.21 / 3.95 | 66.19 / 3.95 |
| Info internal page | 44 | 82.03 / 4.90 | 82.20 / 4.91 | 116.17 / 6.94 | 116.33 / 6.95 |
| Mov internal page | 101 | 98.77 / 5.90 | 98.94 / 5.91 | 183.14 / 10.94 | 115.78 / 6.92 |

The largest paired slowdown is not necessarily the largest absolute maximum:
different active-playback/display phases can favor either owner. Do not infer
a universal speedup from Selected's isolated 183 ms Mov-page sample or the
difference between separate Mov-selection medians. Initial tab activations
are included as selections, not accidentally grouped with internal paging.
The detailed directed-transition tables are in `timing-tables.md`, `.json`
and `.csv` alongside all per-species pairs.

| Species | Pairs | Selected median | Registration median | Median paired delta | Largest paired slowdown |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bastiodon | 14 | 66.15 / 3.95 | 74.08 / 4.42 | -0.08 / -0.00 | 16.90 / 1.01 |
| Caterpie | 13 | 65.51 / 3.91 | 65.67 / 3.92 | 0.16 / 0.01 | 1.02 / 0.06 |
| Dusknoir | 14 | 82.42 / 4.92 | 82.28 / 4.91 | -0.13 / -0.01 | 0.38 / 0.02 |
| Eevee | 23 | 98.12 / 5.86 | 98.26 / 5.87 | 0.16 / 0.01 | 1.25 / 0.07 |
| Exeggcute | 20 | 98.38 / 5.88 | 98.50 / 5.88 | 0.16 / 0.01 | 0.71 / 0.04 |
| Gloom | 20 | 98.33 / 5.87 | 98.11 / 5.86 | 0.16 / 0.01 | 1.40 / 0.08 |
| Groudon | 13 | 82.11 / 4.90 | 82.28 / 4.91 | -0.02 / -0.00 | 16.91 / 1.01 |
| Luxray | 14 | 82.25 / 4.91 | 82.41 / 4.92 | 0.07 / 0.00 | 17.38 / 1.04 |
| Magnemite | 19 | 97.80 / 5.84 | 98.26 / 5.87 | 0.16 / 0.01 | 1.36 / 0.08 |
| Metagross | 14 | 82.03 / 4.90 | 82.36 / 4.92 | 0.07 / 0.00 | 16.90 / 1.01 |
| Mewtwo | 23 | 98.45 / 5.88 | 98.37 / 5.88 | 0.16 / 0.01 | 0.71 / 0.04 |
| Mudkip | 14 | 82.02 / 4.90 | 82.07 / 4.90 | 0.16 / 0.01 | 0.19 / 0.01 |
| Poliwhirl | 23 | 98.45 / 5.88 | 98.61 / 5.89 | 0.16 / 0.01 | 0.95 / 0.06 |
| Slowpoke | 23 | 98.77 / 5.90 | 98.94 / 5.91 | 0.16 / 0.01 | 1.36 / 0.08 |
| Spheal | 14 | 73.17 / 4.37 | 73.77 / 4.41 | 0.16 / 0.01 | 1.25 / 0.07 |
| Swinub | 21 | 98.45 / 5.88 | 98.61 / 5.89 | 0.16 / 0.01 | 16.91 / 1.01 |
| Torchic | 14 | 73.99 / 4.42 | 74.03 / 4.42 | 0.15 / 0.01 | 0.18 / 0.01 |
| Treecko | 14 | 65.84 / 3.93 | 82.19 / 4.91 | 0.16 / 0.01 | 16.91 / 1.01 |
| Tyrogue | 20 | 81.49 / 4.87 | 82.30 / 4.92 | 0.16 / 0.01 | 33.57 / 2.00 |
| Weavile | 15 | 82.03 / 4.90 | 81.65 / 4.88 | 0.16 / 0.01 | 0.19 / 0.01 |

The median of paired differences need not equal the difference of the two
separate medians. Negative near-zero values mean a sub-frame improvement,
not a negative elapsed duration. Full per-operation publication, displayed and
host-input values are in `timing-comparison.json` under the tabs campaign.

### Four Responsiveness Alerts

Across the full species matrix, four matched operations exceed the two-frame
comparison warning. They are retained as responsiveness-review items, not
hidden by a widened tolerance:

| Species / operation | Selected | Registration | Added time |
| --- | ---: | ---: | ---: |
| Primeape, Info wrap to Stats | 64.83 / 3.87 | 98.39 / 5.88 | 33.57 / 2.00 |
| Tyrogue, Info page 3 | 64.94 / 3.88 | 98.50 / 5.88 | 33.57 / 2.00 |
| Beldum, Desc -> Info | 65.37 / 3.90 | 99.02 / 5.91 | 33.65 / 2.01 |
| Toxicroak, Desc -> Info | 65.07 / 3.89 | 99.15 / 5.92 | 34.08 / 2.04 |

Eighty diagnostic probes cover continuous/settled playback, four input phases
and both owners, with no correctness or playback failure. The work/slice counts
do not show duplicated content preparation. In the first three cases READY is
tested at LY86-87, after the existing LY84 staging cutoff, so the panel waits
one loop. The following lower transaction reaches LY148, after its LY147
publication cutoff, and waits again. Toxicroak has a later producer/READY phase
followed by the same publication wait. Settled-playback comparisons remove the
large discrepancy. This is phase-dependent admission contention with portrait
playback, not a reason to widen shared interrupt/admission windows.

`latency-alert-analysis.json` retains every probe and relevant gate timestamp.
No runtime change was made after freezing dev07. The slight controller timing
difference and different entry history place lower-panel work at a different
physical phase; there is no claim that every selection is within 0.16 ms.

One Dusknoir diagnostic also measures initial routine boundaries: registration
first complete display at 305.35 ms / 18.24 frames, with input dispatch at
300.07 ms / 17.92 frames. Regular Selected is 99.23 ms / 5.93 frames and
95.65 ms / 5.71 frames respectively. These entry paths start from different
owners (battle preparation versus an already prepared Listing), so this is not
a like-for-like tab latency or production-entry comparison. Neither has an
already-visible, input-dead interval in that diagnostic.

The separate main exit matrix measures the final B/End signal to public
registration return, excluding earlier footer travel: both medians are
920.706 ms / 54.991 frames, maximum 923.286 ms / 55.146 frames. This includes
the retained fade/font/DV/palette continuation back to the caller and is not
lower-panel tab latency or a promise of an instantaneous End action. Those
12,051 B and 12,051 End samples are separate from continuous-session tab
timings and the supplemental cancellation probes.

## Manual Review

The review ROM has a same-stem private save: Route 30, four party members,
99 Master Balls and cleared caught flags. Bulbasaur and Exp Share Caterpie
are one EXP below level 7, for learning/evolution follow-up checks. It is not
the player's main save. Catch a previously unregistered wild Pokemon, then
exercise both descriptions, every Info/Mov page, tab changes during the cry,
and B/End. Reload the private save to repeat.

`regular-dex-comparison/` contains a second copy of the same ROM with the
native control save: all 373 species seen/caught and all Unown letters. Use
that copy to browse regular Selected without first catching each species.
It is separate because an all-caught save would suppress New Entry registration.

The packaged `qualification.json` requires matching candidate hashes for all
independent reports, the complete support/all-species/evolution/context/return
gates, unchanged protected inputs and linked costs. It also reruns 22 focused
host controls (ten Tower and 12 registration-harness tests). Its automated
pass is separate from the explicit pending human approval fields.

Four silent side-by-side videos cover Dusknoir, Eevee, Exeggcute and Metagross.
Left is regular Selected, right is registration, both in the candidate.
Both begin on their first complete Description; later input sequences advance
independently when each page is ready. Thus different pages at a later instant
can mean one side has advanced further, not that the initial reveal lagged.

Separate `*-audio-selected-then-registration.wav` files play 3.2-second clips
starting 80 ms before each owner's cry with 0.7 seconds of silence between them. Native pitch,
rate and timing are unchanged. Automated deadline/wave checks are not a claim
of human listening approval.

## Reproduction

All commands are run from the repository root. Build into a fresh private path:

```sh
PYTHONPATH=tools:. python3 -B tools/build_interactive_registration_prototype.py \
  --output build/interactive-registration-FRESH \
  --evolution-patch tools/dex_timing/probes/interactive_evolutions.diff
```

The builder preserves the qualified Gotcha source boundary and production
inputs, copies the new controller/data patch, regenerates Info assets and
links a private ROM. It rejects a reused output path. Existing dev07 source
is the frozen authority for this run, not a future rebuild against a changed
root checkout. Full qualification commands and exact evidence are recorded
by `tools/dex_timing/interactive_full_regression.py` in its orchestration
ledger. The all-species and special-return runners are separate modules;
their results must also be present before acceptance.

Rejected development links remain named dev01-dev06 in `build/`. They are not
qualified artifacts: early bank-call/LCD sequencing failures and the temporary
Info bank overflow were fixed before dev07 was frozen. Do not reuse their
CPU checkpoints with dev07 or present their partial tests as final coverage.
