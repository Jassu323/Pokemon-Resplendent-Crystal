# Interactive Registration: Capture Fixes Review

Date: 2026-10-16. Qualified prototype, subsequently accepted and integrated.

## Status

**Production follow-up:** the user accepted this exact build and requested
integration, explicitly retaining the 20 reviewed temporary evolution
requirements. Root ROM/symbols/map match byte-for-byte; fresh root checks pass.
The player's main save is unchanged. See
[production integration](pokedex_interactive_registration_integration.md).
The qualification record below describes the frozen pre-integration review;
protected production inputs and approval-pending notes refer to that phase.

The current prototype includes the synchronized LCD-on capture handoff and
three-byte Pay Day preservation. Automated qualification is complete and passes:
all 35 support actions plus all-species registration, evolution, special-return,
garbage-collection, legitimate Pay Day, delivery and visual-handoff supplements.
There are no new functional failure differences against frozen production.
Known baseline exceptions and five Info timing warnings remain documented below.
Human listening/visual/responsiveness approval and physical-hardware testing
remain separate from these automated results.

- Candidate SHA-256:
  `d1ce69a431dc138fdbbecb834c050097e5ebf807856d2d16323d32f644d95ff0`.
- Frozen source: `build/interactive-registration-fixed-full-20261016/candidate/`.
- Support evidence: `build/interactive-registration-fixed-full-20261016/`.
- Registration evidence: `build/interactive-registration-fixed-tabs-20261016/`.
- Qualified review package: `build/interactive-registration-review-20261016/`.
- Safe rollback remains the previous reviewed prototype in
  `build/interactive-registration-review-20261015/`, source
  `build/interactive-registration-dev07-20261015/candidate/`, SHA-256
  `1abe990d9d96ef34a910e444c6990aa9e745c8827d48946834aa179a29cc8634`.

The frozen source was rebuilt and exactly reproduced the independently tested
combined candidate. Production ROM and the player's main save are protected
inputs. Neither is an integration target for this request.

The review ROM is
[`pokecrystal-interactive-registration.gbc`](../build/interactive-registration-review-20261016/pokecrystal-interactive-registration.gbc).
Its adjacent private save starts on Route 30 with four Pokemon, 99 Master Balls,
and cleared caught flags. Bulbasaur and Exp Share Caterpie are one EXP below
level 7. Continue was checked through normal controls. A separate
`regular-dex-comparison/` copy has all 373 species seen/caught and all Unown forms
for ordinary Selected-screen comparison. Neither save is the player's main save.

## Changes And Dependencies

Only two gameplay source files differ from the prior reviewed prototype:
`engine/battle/capture_speed.asm` and
`engine/pokedex/new_pokedex_entry.asm`. The reusable prototype probes and
builder are updated, together with the relevant host tests and diagnostics.

The capture helper waits for the mode-2-to-mode-3 LCD edge, then switches from
normal to double speed without disabling the display or fading its palettes.
It remains after the caught cue and `MUSIC_NONE`, before capture music starts.
It is not a generic speed-switch replacement: preserve its silent,
successful-capture-tail, normal-to-double, no-concurrent-producer contract.
The shared speed helper, VBlank/STAT/timer handlers and per-frame work are not
expanded. Existing registration animation, tabs and capture-tail speed policy
are retained. Normal battle animations still run at normal speed.

Registration saves/restores all three big-endian `wPayDayMoney` bytes because
they overlap live portrait scratch. It must preserve legitimate earnings, not
clear them. The saved context is now 67 rather than 64 bytes in the already
borrowed WRAMX bank-2 `wTempTilemap` region. The next live animation structure
begins at offset 360. Keep the context-size assertion and independent field
table, transient-ID/lock, bank/stack and legitimate-amount tests.

| Linked Resource | Versus Production | Versus Previous Prototype |
| --- | ---: | ---: |
| ROMX, decimal bytes | +5332 | -126 |
| ROM0 / allocated WRAM0 / allocated WRAMX / HRAM / SRAM | 0 each | 0 each |
| Borrowed registration context | 67 bytes | +3 bytes |

The synchronized helper saves 132 ROMX bytes versus the fade helper; three
additional field pointers spend six of those. No new graphical assets are
required. The Pay Day save/restore CPU-only round-trip cost is 0.120163 ms /
0.007177 display frames at double speed.

## Completed Registration Qualification

- All 373 species and all 26 Unown forms: 398 registration contexts, with 373
  ordinary Selected controls using the same data and executable.
- 7,369 registration page/tab requests, 14,438 continuous operations across
  both owners, and 2,388 directed registration tab transitions.
- 796 Description pages, 772 Info pages and 2,617 Moves pages.
- 33,718 total exit replays, including 8,370 unique committed B/End exits.
- 12,736 rapid-input, held-input, finish-boundary and early-exit stress cases.
- All 15 content/playback/harness negative controls reject their injected faults.
- No missing acceptance/publication/display completion, wrong event order,
  negative timing interval, pixel-parity failure or registration playback error.
- 160 detailed phase probes, covering this build's actual five timing alerts,
  the four previous alert controls, and sampled Dusknoir entry. No probe failures.
- The pending-exit limitations remain explicit: Info End and Description work
  often finish before the physical exit dispatch; do not claim unobserved pending
  cancellation merely because the player began moving toward End earlier.

Independent special-return runs pass ten cases: contest/Celebi declared battle
types, an actual transformed encounter, and both Game Corner prize scripts via
B and End. A separate forced-ID-garbage-collection case also passes. The saved
67-byte context is checked for integrity. Declared battle-type fixtures and a
direct collector call are not described as full event-script gameplay.

The evolution audit passes all 373 species and 190 in-roster links, including
the previously approved 20 temporary requirements. No learnset was altered by
these capture fixes. The linked registration context contracts pass ten tests;
the combined harness/clock/Tower/delivery control group passes 36 host tests.

## Legitimate Pay Day Supplement

Eight fresh native cases compare production and candidate, with/without Amulet
Coin and with/without reaching the 999,999 wallet cap. The player actually uses
Pay Day through battle controls before catching the opponent. The real move-ID
allocator is used in the declared pre-enemy data fixture, not a guessed live ID.

All eight pass: a level-6 use earns 12, the amount remains 12 across registration,
the ordinary wallet gains 12 or 24 with Amulet Coin, and capped totals stop at
999,999. Candidate coin cases additionally visit Info or Mov before returning.
The seven seeded helper amounts independently cover all three accumulator bytes.

Evidence: `build/interactive-registration-fixed-payday-v2-20261016/report.json`.
The initial fixture retained the level-32 seed party, which knocked out the
level-10 opponent before a capture could occur. Its eight failed driver attempts
are preserved in `build/interactive-registration-fixed-payday-20261016/`.
Using the intended level-6 party corrected the fixture, not the ROM.

## Capture Handoff And Delivery

The fresh 104-case capture matrix and eight following-battle supplements pass,
including unchanged wallets in all no-attack cases, repeat/no-Dex exclusions,
EXP Share, learning/replacement/decline, naming, successful/canceled evolution,
map resume, and subsequent running, fighting or catching. The handoff's median
duration is 18.846 ms / 1.126 display frames, with a measured range of
18.830-18.921 ms / 1.125-1.130 frames. This is elapsed helper time, not a display
blackout: the LCD stays enabled and the battlefield remains visible.

Two fresh recorded captures pass the first-200-ms native scanout check: no full
white/black or LCD-off scanout, and STOP occurs in mode 3 with sound and
interrupts inactive. The original independent six-revision CGB checks used the
same exact candidate hash. They are not independent cores or physical hardware.

The legacy paired-data helper initially reported DV differences on all 52
production/candidate pairs, and derived stat differences in four high-level
fixtures. These values are already different before Gotcha or either fix.
A new 104-case native replay proves that each delivered Pokemon preserves its
own pre-handoff wild DVs/stats through delivery and map return. The normalized
52-pair comparison has zero remaining differences; only these proved initial
values of the newly caught individual are excluded. Existing party members,
moves, EXP, PP, nicknames and all other compared fields remain strict.
`comparison-raw-exact.json` preserves the original mismatches, while
`delivery-proof.json` contains the matching-link pre-handoff evidence. Two
new unit controls reject actual delivery corruption and over-broad comparison
exclusions. No cartridge code was changed to address this harness issue.

## Full Support Regression

The final parent record is
[`qualification.json`](../build/interactive-registration-review-20261016/qualification.json):
`automated_qualification_pass: true`, with all twelve gates true. The support
audit has 16 standard actions, 14 supplementary actions, three capture actions
and two Tower actions complete, with no missing actions and no new failures.
The checks below overlap; they must not be summed into end-to-end scenarios.

| Coverage | Completed Checks |
| --- | ---: |
| Standard Dex | 4,479 |
| Current host group | 87 candidate and 87 explicit production controls |
| Selected playback / entry timings | 2,238 / 1,024 |
| Sampled audio / battle-move regression | 960 / 1,600 |
| All 333 move animations, both sides, both ROMs | 1,332 native cases / 666 pairs |
| Move-animation renderer calls | 7,312 |
| Linked numeric planners | 3,072 |
| Active Description returns / six-model returns | 1,492 / 1,536 |
| Lifecycle / routes / exit matrix | 336 / 36 / 88 |
| Capture / following-battle supplement | 104 / 8 |
| Independent Battle Tower suite | 6,728 |

Persistence additionally passes 2,380 helper cases, four snapshot cases, 1,490
cold boots, 152 interrupted writes, 150 interrupted repairs and five lifecycle
cases. The broad Type audio sweeps cover 122 tracks both stationary and during
navigation; the display supplements cover six CGB revisions and Unown paging.

Four Tower calls exceeded the initial 60,001-interval driver budget: production
Struggle cases 9-1 and 9-5, production Aerial Ace 8-2, and candidate Aerial Ace
10-0. All four complete and pass the battle-return contracts under the existing
bounded seven-interval continuation. Their initial failures, CPU checkpoints,
watch audits, pre-recovery summaries and final recovery results remain under
`build/interactive-registration-fixed-full-20261016/battle-tower/`.
This is not a claim of zero initial timeouts or identical battle timing. No
game state or cartridge code was patched to continue those calls.

The first packaging audit used a nonexistent separate baseline host-report
path. The standard host module actually reruns only failing candidate cases
against production. The corrected campaign adds an explicit full production
host group, rather than inferring its count; all 87 pass. The interrupted,
unqualified package is preserved as
`build/interactive-registration-review-20261016-pre-audit-attempt/`.
The final qualified package was regenerated after the corrected audit.

### Existing Exceptions

- Battle Tower retains the known vitamin reward-routing/lost-prize bug on both
  ROMs. Coverage is complete and `no_new_failures` is true, but `clean` is false.
  See the separate [Tower backlog](battle_tower_bug_backlog.md).
- Native animation comparisons retain 34 baseline issue pairs: 632 of 666 pairs
  are clean, with zero differing issue pairs. They are not newly fixed by this
  capture change.
- The historical host group retains matching identities for six failures,
  16 errors and 103 skips out of 187 tests per ROM. The current 87-case host
  group is clean on both ROMs.
- Dusknoir's initial wild appearance still stops at 512/557 sampled blocks,
  with 45 remaining, before Gotcha on both ROMs. Its registration cry completes
  all 557 blocks. There are no new capture audio-miss identities.

## Timing Warnings For Review

Five continuous-scan Info operations are about two display frames slower in
registration than in ordinary Selected on the same candidate:

| Species | Operation | Additional Milliseconds | Additional Display Frames |
| --- | --- | ---: | ---: |
| Diglett | Info wrap to Stats | 33.635 | 2.009 |
| Farfetch'd | Info Stats | 33.660 | 2.010 |
| Hoothoot | Info Stats | 33.578 | 2.006 |
| Koffing | Info Stats | 33.631 | 2.009 |
| Nidoran male | First evolution page | 33.756 | 2.016 |

These are latency warnings, not content/portrait/audio errors. Four diagnostics
observe both late READY admission and late lower-panel VBlank publication; the
Nidoran case observes late publication without a late READY event in that
diagnostic sample.
The same conservative gates remain in place; no admission budget was widened.
The previous scan flagged four other operations, with a maximum 34.084 ms /
2.036 frames. That count and identity are phase-dependent, not a promise that
only four specific species can encounter the scheduling condition.

Typical 20-representative request-to-complete-display medians are unchanged:
Desc-to-Info is 81.433 ms / 4.864 frames, with a paired median delta of
0.146 ms / 0.009 frames versus Selected; Desc-to-Mov is 82.412 ms / 4.922 frames,
with a paired median delta of 0.162 ms / 0.010 frames. The complete tables retain
input-to-acceptance, publication and complete displayed-frame measurements
separately. One physical display frame is 16.742706 ms, not 16.666667 ms.

The first diagnostic pass still selected the four prior warning species. That
controls-only report is preserved under the registration evidence directory.
The harness now derives targets from the actual current timing alerts, also
retains historical controls, matches each operation explicitly, and decodes
the linked admission cutoffs. A negative-control unit test guards against
silently reporting only old species in future runs.

## Manual Review

The qualified package contains two real-time production-versus-prototype capture
videos, a native capture-jingle A/B WAV, four Selected-versus-registration videos
and native cry A/B WAVs, paired panel screenshots, the first twelve Gotcha frames,
and the full timing tables. Capture audio plays production first, then 0.7 seconds
of silence, then the prototype; it is not retimed or mixed. The side-by-side
videos are silent. Start with
[`party-name-production-vs-prototype.mp4`](../build/interactive-registration-review-20261016/party-name-production-vs-prototype.mp4)
and [`capture-audio-production-then-prototype.wav`](../build/interactive-registration-review-20261016/capture-audio-production-then-prototype.wav).

Manual listening/visual approval and physical-hardware qualification are not
supplied by automated SameBoy checks. Known baseline exceptions remain identified
rather than described as a completely clean game. See the
[investigation](pokedex_registration_capture_handoff_investigation.md)
for the hardware dependency, original payout reproduction and alternative
implementations. The prototype run itself did not authorize promotion;
the user's subsequent approval and integration are recorded above.
