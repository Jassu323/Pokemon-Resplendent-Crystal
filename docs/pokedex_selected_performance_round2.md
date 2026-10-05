# Selected Pokedex Performance: Round Two

Historical investigation. The accepted options are now integrated under
[the production clock policy](production_clock_policy.md), with normal-speed
battles. Unchanged-production statements below refer to this earlier trial.

2026-10-04. Private investigation for `DEX-PERF-02`, based on production
`2cec80517`. **Production gameplay source, ROM, symbols and map are unchanged.**
Round one's visual benchmark is preserved separately. This report supersedes
its untested follow-up estimates, not its recorded measurements.

## Assessment

Whole-Dex double speed is the strongest tested improvement. Combined with
bounded Info preparation and committed-Info retention across Area, it reduces
active Stats loading from about 18-19 intervals to 5-6, settled Stats to 4.54,
and Area loading to about 9.5. Removing eager Listing lookahead saves another
interval on many returns without slowing the tested held-scroll cadence.

This is not an unconditional responsiveness win:

- Complete Listing return is faster, and median Info-return initial response
  recovers from round one's regression. Some First measurements have long tails.
  Fresh active Moves -> Listing has a **later median first change**, despite a
  much faster completed Listing. Manual review must assess this tradeoff.
- Whole-Dex closing is about three intervals / 49ms slower. Opening is faster.
  Entry/exit remain the separately deferred lifecycle optimization story.
- SameBoy's APU warning is a **hardware-model qualification**, not a detected
  sampled cry underrun. Software/audio regressions passed, but this emulator
  cannot validate behavior it explicitly describes as untested.
- Normal-speed active-Info admission caused Garchomp misses and was rejected.
  Only the tested double-speed combination is proposed for review.

Recommendation: compare the private ROM manually, especially active Info,
B-return histories and audio after leaving the Dex. Do not promote production
automatically. Retain the APU qualification until independent emulator or
physical-CGB evidence is available.

## Builds And Measurements

Artifacts: ignored `build/dex-performance-20261004/`. Round one remains under
`build/dex-performance-20261003/final/`. No live battery save was modified.

| Build | ROM SHA-256 |
| --- | --- |
| Unchanged production | `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666` |
| Round-one benchmark | `249c86d40307e63f4b6dee0b633e5b5839b97f87ddd12a53dab92bb6c64b1d08` |
| Final `combined-no-lookahead/pokecrystal-dex-round2-combined-no-lookahead.gbc` | `f43ec91074b0103011212040bcebf55018421001cb388fd302aa29908076188c` |

Final symbols: `b8be268617dbe360b775e36f7997ed492559433e76efc28f3128d799ab428af5`.
SameBoy: `213a12ce93d66b105a113debd9396306066a7cfc`.
Vanilla source: `5beda23ffa505f62e1dad7e3d7c214d1737b3358`.

One physical display interval is 70,224 normal-speed T-cycles at 4,194,304Hz,
**16.742706ms**. Double speed does not halve it. Core timestamps are converted
to physical time, not doubled CPU cycles. The
[round-one measurement contract](pokedex_selected_performance.md#measurement-contract)
is retained: button press -> first rendered change and -> correct complete
visible result are separate. Quiet lower-panel crops exclude animation/footer;
full-screen First can include natural outgoing portrait/footer changes. Maps,
tiles, palettes, OAM, owners and exact publication timing independently determine
correctness. Parent routine spans include interrupts/waits and must not be
added to their nested children. Observer timestamps have callback-boundary
granularity, not independently calibrated eight-cycle instruction boundaries.

Final matrix: **3,280 cases**, 27 species, active/settled playback, all relevant
Info pages, fourteen actions and four quarter-interval input offsets. Existing
baseline numbers were reused. Description/Moves return baselines were added.
Separate normal-input sequences are not identical frozen CPU/PPU states.

## Performance Comparison

Medians: **physical intervals / ms**. Each cell is **First; Complete**.
Active refers to playback at the original request; Area cancels it before return.

| Scenario | Production | Round-one benchmark | Round-two final |
| --- | --- | --- | --- |
| Description -> Stats, active | 19.79 / 331.4; same | 19.15 / 320.6; same | **5.97 / 99.9; same** |
| Moves -> Stats, active | 18.37 / 307.5; same | 17.67 / 295.8; same | **5.43 / 91.0; same** |
| Description/Moves -> Stats, settled | 12.43 / 208.1; same | 7.43 / 124.4; same | **4.54 / 76.1; same** |
| Info cycle, active | 17.75 / 297.1; same | 17.37 / 290.8; same | **5.65 / 94.6; same** |
| Info cycle, settled | 12.86 / 215.3; same | 7.61 / 127.4; same | **4.68 / 78.4; same** |
| Description -> Area, active | 2.10 / 35.1; 36.49 / 611.0 | 2.10 / 35.1; 15.34 / 256.9 | **2.22 / 37.1; 9.47 / 158.5** |
| Description/Moves -> Area, settled | about 2.43 / 40.7; 36.43-36.59 / 610-613 | about 2.43 / 40.7; 15.36 / 257.2 | **2.54 / 42.6; 9.54 / 159.8** |
| Info -> Area, settled | 2.36 / 39.5; 36.43 / 610.0 | 2.43 / 40.7; 15.36 / 257.2 | **2.43 / 40.8; 9.54 / 159.8** |
| Area -> Info, formerly active | 2.41 / 40.4; 15.59 / 261.1 | 2.44 / 40.8; 15.34 / 256.9 | **2.51 / 42.0; 8.42 / 141.0** |
| Area -> Info, formerly settled | 2.42 / 40.6; 15.59 / 261.1 | 2.43 / 40.7; 15.34 / 256.9 | **2.51 / 42.0; 8.42 / 141.0** |
| Info -> Listing, active | 1.75 / 29.3; 18.74 / 313.8 | 12.50 / 209.2; 15.00 / 251.1 | **1.97 / 32.9; 10.65 / 178.3** |
| Info -> Listing, settled | 1.61 / 26.9; 18.61 / 311.6 | 14.43 / 241.6; 14.86 / 248.8 | **1.68 / 28.2; 10.68 / 178.9** |
| Internal species page from Info, active | 1.85 / 30.9; 15.75 / 263.6 | 5.16 / 86.4; 15.20 / 254.4 | **2.56 / 42.9; 7.90 / 132.3** |
| Internal species page from Info, settled | 1.54 / 25.7; 15.36 / 257.2 | 5.86 / 98.1; 15.36 / 257.2 | **1.54 / 25.9; 7.68 / 128.7** |

Final active Info/Mov -> Area: First approximately 2.22 / 37.1; Complete
9.47 / 158.5, like Description. No cry/animation replay on Area return; exact
tab/page restored. Unchanged one-page contents have no visible-change metric,
not a fabricated zero-latency publication.

Rapid test: fifteen A presses, two intervals held/two released, ending around
interval 59. Complete starts at the first press; its one-second value mostly
describes continued player input, not a stall.

| Rapid Info cycling | Production First; Complete | Benchmark First; Complete | Final First; Complete |
| --- | --- | --- | --- |
| Active | 70.37 / 1178; same | 21.37 / 357.8; 68.87 / 1153.1 | **5.78 / 96.7; 60.03 / 1005.0** |
| Settled | 67.61 / 1132; same | 8.49 / 142.1; 59.86 / 1002.2 | **5.18 / 86.8; 59.68 / 999.3** |

Final last-release -> correct page: active median 1.38 intervals, range
0.86-2.88; settled median 0.92, range 0.91-1.92. Pages appear during input;
requests no longer perpetually abandon unfinished preparation.

### Listing Return History

Additional production/benchmark matrices: 864 attempted cases each. Production
rejected four setups: one Garchomp active Info -> Description miss repeated
before four later offsets. Benchmark passed all 864. Rejected cases are not
included as latency successes. Final matrix passed all 3,280.

| Return | Production First; Complete | Benchmark First; Complete | Final First; Complete |
| --- | --- | --- | --- |
| Fresh Description, active | 1.59 / 26.7; 11.16 / 186.8 | same | 1.65 / 27.7; **6.72 / 112.5** |
| Fresh Description, settled | 10.36 / 173.4; 10.86 / 181.8 | same | 6.43 / 107.7; **6.68 / 111.9** |
| Fresh Moves, active | 1.87 / 31.3; 11.09 / 185.7 | same | **6.15 / 103.0**; 6.97 / 116.7 |
| Fresh Moves, settled | 1.61 / 27.0; 10.86 / 181.8 | same | 1.68 / 28.2; **6.93 / 116.1** |
| Description after Info, active | 1.55 / 26.0; 15.81 / 264.6 | 1.56 / 26.0; 12.81 / 214.4 | 1.54 / 25.8; **8.90 / 149.0** |
| Description after Info, settled | 1.74 / 29.1; 15.86 / 265.6 | 12.11 / 202.7; 12.86 / 215.3 | 1.93 / 32.4; **8.68 / 145.4** |
| Moves after Info, active | 15.25 / 255.3; 15.87 / 265.7 | 12.09 / 202.4; 12.76 / 213.7 | 8.40 / 140.7; **8.97 / 150.1** |
| Moves after Info, settled | 1.61 / 27.0; 15.86 / 265.6 | 1.61 / 27.0; 12.86 / 215.3 | 1.68 / 28.2; **8.93 / 149.6** |

Round one's regression affects the Info glyph/cache *history*, not just the
currently selected tab. Fresh Description/Moves returns were unchanged. Round
two removes that rejected frame-0 component-repair change and uses ordinary
cache repair with less residency work and faster CPU preparation.

Do not treat the favorable Info First median as a worst-case guarantee. Active
Info First P90 is about 10.4 intervals, maximum 10.96; settled maximum 9.18.
Footer blinking and natural portrait changes make this metric bimodal. Fresh
active Moves First is explicitly about **+4.28 intervals / 71.7ms worse** than
production, while its correct Listing appears about 4.12 intervals / 69ms
sooner. The player's judgment of this retained-page presentation still matters.

Chikorita's rendered Info-return gallery retains the correct panel through
frame 10 and reveals the correct Listing at frame 11, with no intermediate
blank, palette failure or glyph corruption. This is specific-case visual
evidence, not a claim that every species shares that exact duration.

### Species Variation

- Active Description -> Stats: 4.15-7.97 intervals / 69.5-133.4ms overall.
  Species medians include Unown 4.53 and Drapion 7.59. Active Moves -> Stats
  reaches a Dusknoir median around 7.58. Concurrent work still matters.
- Settled Stats: 4.15-4.94 intervals / 69.5-82.6ms; little species variation.
- Info-return Complete species medians range about Garchomp 9.59 to Luxray
  14.59, overall maximum 14.97 / 250.6ms. Mini-sprite repair is still
  species/viewport-dependent, not a uniform ten-interval promise.
- Area static lookup/transfer is mostly uniform. Roamers, regions, empty nests
  and marker presentation have separate checks.

## Experiments, Costs And Decisions

| Option | Measured effect | Cost / complexity / risk | Decision |
| --- | --- | --- | --- |
| Retain Info across Area, normal speed | Return 15.34 -> 12.42-12.52 intervals, about 49ms saved | +154 ROMX bytes over round-two base, one overlay flag; moderate lifetime/ownership risk | Included with reconstruction fallback |
| Whole-Dex double speed alone | Area about 9.5; species 7.7-8; fresh Listing 6.7-6.9 intervals | Lifecycle/timer policy; fixed DMA/LCD waits do not double; APU hardware qualification | Included; insufficient alone for active Info |
| More admitted Info work, normal speed | Intended active benefit | +79 ROMX bytes, no extra state; ten Garchomp failures in 408 runs | Rejected standalone |
| Double speed plus admitted Info | Active Stats 5-6; settled 4.54 intervals | Moderate scheduling risk, empirical gates; exact playback regressions required | Included only as tested combination |
| No eager Listing lookahead | Info return 10.68 vs combined-with-lookahead 11.44; after-Info returns about one interval faster | -93 ROMX bytes versus round-two base; five physical slots retained, three resident rows required; moderate wrap risk | Included; tested held-scroll cadence unchanged |
| Permanent Stats BG / smaller physical ring | Not implemented or benchmarked | Remapped tile/mini-sprite ownership and wrap staging; higher structural risk | Deferred; not needed for this gain |

### Retained Committed Info

Only an idle committed page with no pending request/owner transition is retained.
The immutable record supplies 224 tilemap bytes, 80 glyph-source bytes and tile
count. Its 224 attributes reuse the now-dead 640-byte Info graphics scratch.
Area's bank-0 graphics do not overwrite the bank-1 Info atlas/mini sprites.
Return restores maps, metadata, badge, palettes and OAM without uploading the
same glyphs. A one-use flag resets; incomplete/canceled jobs use normal fallback.

### Bounded Info Admission

Up to twelve slices replace the old three active/six quiet slices. Each active
slice rechecks the display tick, animation upload and sampled-cache runway;
nine state LY limits are 0/65/81/104/87/84/113/94/108. Empirical normal-speed
isolated costs include a 2,048-cycle guard and 8,182-cycle finishing reserve.
Quiet work stops at LY 96 too.

Isolated slice costs do not prove a whole owner loop. Normal-speed admission
caused Garchomp misses more than 100,000 physical T after the last Info slice:
cumulative deadline pressure, not proof of a single upload as complete cause.
The double-speed combination passed full exact-timeline/audio checks. Future
UI workloads still need validation, not assumed universal admission bounds.

### Lookahead Versus Physical VRAM

The prototype stops eager above/below-viewport uploads and requires three
visible rows. An incoming row is prepared before draw/reveal. **Five physical
slots remain** for wrap/offscreen staging. Residency policy frees no VRAM.

Held-scroll median is about eight intervals in production/round one and five
in both double-speed variants. No-lookahead does not change the latter tested
cadence; it avoids unseen return work. Initial repeat delay remains about
fifteen intervals, a separate input policy.

Physical five -> three rows would free 32 BG tiles gross, but sixteen frame-0
tiles are already borrowed by Info. Sixteen net frame-1 tiles could hold the
fifteen common Stats tiles, not those plus twenty-four numeric tiles. Five ->
four yields eight net plus two currently free bank-0 tiles, insufficient for
fifteen. A physical reduction needs different safe wrap staging. No OAM
conversion or permanent Stats pool was implemented in this iteration.

## Double Speed And Audio

### Lifecycle And Timer

The Dex switches once on entry and restores the caller's speed on exit. Both
switches run with LCDC bit 7 clear; none occurs on tabs, species or Area. Caller
KEY1 costs two stack bytes. Existing `SwitchSpeed` clears IE, so private wrappers
preserve/restore it before normal ownership resumes. No extra HRAM/WRAM0.

SameBoy measures about 15.67ms entry switching / 31.28ms exit switching; its
STOP code has timing TODOs, so these are **core measurements, not calibrated
hardware guarantees**. Existing white lifecycle transitions hide the switch;
no new mid-page blackout. Cold Dex opening improves about 64.5-65.27 intervals /
1,080-1,093ms -> 50.56-51.31 / 846-859ms. Reopening: 61.83 / 1,035 -> 48.01 /
804. Whole closing worsens 62.90 / 1,053 -> 65.84 / 1,102. `DEX-PERF-01` remains.

APU wave frequency does not double, but CPU divider/timer does. Startup-only
timer compensation is therefore required; the IRQ does not gain a farcall.

| Sample / speed | TAC | TMA | Physical block period |
| --- | ---: | ---: | ---: |
| Standard, normal | 6 | 56 | 200 * 64 = 12,800 T |
| Standard, double | 7 | 156 | 100 * 256 / 2 = 12,800 T |
| Existing faint, normal | 6 | 43 | 213 * 64 = 13,632 T |

The startup helper is moved to ROMX behind the existing ROM0 entry; normal
settings stay unchanged. Animation admission accepts the expected double-speed
profile and conservatively retains old normal-speed finishing bounds.
For an odd period such as 213 *in double speed*, upward rounding to 107 gives
13,696 physical T, approximately 0.47% slower. The Dex does not faint Pokemon;
native battle fainting remains normal and was verified at 13,632 T. Revisit
rounding before another owner uses arbitrary modified-pitch samples in double
speed. CPU/timer versus LCD/HDMA/APU behavior is documented by
[Pan Docs' KEY1 reference](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md#ff4d--key1spd-cgb-mode-only-prepare-speed-switch).

### SameBoy Warning

`SameBoy/Core/sm83_cpu.c`, `stop()`, logs
`ROM triggered an APU odd mode, which is currently not tested.` whenever the
APU is globally enabled on double -> normal switching. It does **not** check
for an observed audio miss, invalid decoded block or bad pitch. The separate
LCD-on PPU warning does not occur in this LCD-off prototype.

No NR52 reset or emulator-state repair silences it. Post-Dex tests retain real
APU/divider state, including four consecutive roundtrips. These tests show no
software regression *within SameBoy*, not proof of its untested hardware mode.
Music/SFX may have a subtle switch-phase discontinuity that sample-block
identity cannot exclude. Manual listening and independent core/physical-CGB
validation are still appropriate before broad hardware qualification.

### Expanded Cross-Owner Audio Suite

**1,920 runs, 2,048 sampled segments, 1,440 paired comparisons, zero differences
and zero rejected final setups.** Four arms, each at four quarter offsets:
production after a normal-speed Dex visit; candidate before any visit; candidate
after one normal -> double -> normal Dex roundtrip; candidate after four.

Twenty species: Luxray, Caterpie, Metagross, Dusknoir, Garchomp, Exeggcute,
Vibrava, Mewtwo, Groudon, Weavile, Bastiodon, Unown, Seviper, Rampardos, Kyogre,
Rayquaza, Spheal, Milotic, Yanmega and Rhyperior. Synthesized controls: Caterpie,
Exeggcute, Mewtwo and Unown. Every species/arm/offset exercises:

- Native party Stats entry and automatic cry.
- Native wild appearance -> actual capture -> New Dex Entry cry.
- Native wild appearance -> real move choice -> enemy faint cry.
- Native player send-out against a Caterpie control foe.
- Real blocking `PlayMonCry` and `PlayStereoCry` wrappers.

Matching checkpoints are reached by normal controls after real speed roundtrips.
The game's species-ID allocator creates explicitly generated contexts before
the native initializer. Party fixtures retain the copied lead's stats/moves:
**audio/species contexts, not valid species-specific combat-stat tests**. Player
send-out has native UI/animation. Blocking wrappers use a native menu donor:
**shared-routine coverage, not full PC/daycare/hatching/evolution/trade screens**.

Read-only observers capture each committed CH3 table (32 nibbles), reload/rate,
wave frequency, speed, block count and remaining count. Every candidate sample
sequence/hash, setting and exhaustion point matches its paired production run.
IRQ timestamps have a few cycles of jitter; they are not timer reloads. PCM
recordings are listening evidence, not claimed identical across music phases.

| Dusknoir path | Production and all candidate arms |
| --- | --- |
| Stats automatic cry | 488 / 557 blocks; existing miss with **69 remaining** |
| Wild appearance | 512 / 557; existing miss with **45 remaining** |
| Player send-out | 557 / 557, natural completion |
| New Dex Entry | 557 / 557, natural completion |
| Enemy faint | 557 / 557, altered frequency 1835 / period 213, natural completion |
| Blocking mono/stereo | 557 / 557, natural completion |

Existing Stats misses also match for Vibrava (41 remaining), Groudon (254),
Kyogre (250) and Yanmega (405). Wild misses match for Groudon (198), Kyogre
(226) and Yanmega (405). In catch/faint runs these belong to the **earlier
appearance**, not the later faint/New Entry cry. They extend the adjacent audio
backlog and are neither new speed regressions nor fixes of old failures.

New Dex Entry: **8,890 cases, zero failures**. This includes 320 natural-completion
replays across all arms/offsets, plus 8,570 one-interval-shifted A/B/startup/hold/
mash/rapid-cross-button cases after a roundtrip. Over 1.25 million displays
checked authored timelines, maps/pixels, owners and sample accounting. Entry
donors come from actual catch flow. Only Unown's letter is normalized in a
generated form-A context for its independent pixel reference.

Initial rejected harness evidence is preserved. Fifty-two cases needed setup
correction: Unown incorrectly expected sampled audio, its unlocked-letter flag
absent, and four Rampardos inputs preceding move-cursor readiness. An earlier
smoke recorder initialized late and caused a SameBoy host assertion; recording
is now configured before boot. None is counted as a game regression or hidden
as a pass.

### Existing Speed Usage: Fork Versus Vanilla

Audit covers assembly helper calls/jumps, the STOP instruction and KEY1/SPD
accesses, excluding generated builds/host instrumentation.

| Existing path | Fork | Vanilla | Meaning |
| --- | --- | --- | --- |
| Boot | `home/init.asm:154` NormalSpeed | line 152 | Ensure normal speed |
| Mobile enable/disable | `mobile/mobile_40.asm:77/100` | same | EnableMobile switches up; DisableMobile switches down |
| Battle Tower room menu init/cleanup | `mobile/mobile_46.asm:447/504` | same | Room/mobile menu, **not ordinary Tower battle playback** |
| Actual STOP helper | `home/double_speed.asm:26` | same | Sole game STOP instruction |

`home/double_speed.asm` is source-identical. Battle animations read SPD in both;
vanilla's mobile library also reads it. Reads are not extra speed owners. The
fork's animation-policy KEY1 read rejects unsupported timing, not switches it.

Ordinary Stats, wild/trainer battle, New Dex Entry, PC, evolution/hatching,
daycare and scripted cries have **no dedicated switch**. Mobile contexts can
inherit their enclosing owner's double speed; static audit does not imply
every dynamic call path was tested. The private prototype adds the whole-Dex
owner and speed-aware sample-start helper, not another production speed owner.

Vanilla mobile behavior is useful precedent but **not sampled-audio proof**:
vanilla has no fork codec/player. No ordinary fragile audio owner was skipped.
Direct `PlayCry` callers in trade/PC and scripted cries share the tested lower
cry/wait machinery; their entire screens were not replayed. `PlaySlowCry`
currently returns on sampled `LoadCry`; it is not a double-speed sampled success.

### Polished Crystal Follow-Up

Read-only source audit of the local Polished Crystal checkout at
`f7745f128030c2ba8b0bd7ec8c3f161b58791d07` (2026-10-01), compared with vanilla
pokecrystal at `5beda23ffa505f62e1dad7e3d7c214d1737b3358`. This is a source
audit, not an additional emulator or physical-hardware test campaign.

**Polished uses double speed throughout normal CGB gameplay, not just in
individual menus.** `engine/init.asm:19-40` waits for LY 145, disables the LCD,
checks `hCGB`, and switches to double speed with KEY1/SPD and STOP. The bit-7
guard avoids toggling back when initialization is reached already at double
speed (for example, through soft reset). Non-CGB initialization skips this
switch. LCD enable is later at line 136 and `InitSound` at line 173.

| Path | Vanilla | Polished Crystal |
| --- | --- | --- |
| Initialization | Explicit `NormalSpeed`, `home/init.asm:152` | Explicit double-speed setup while LCD is off, `engine/init.asm:27` |
| Ordinary CGB overworld, Dex, Stats, battles and New Entry | No dedicated speed switch; normal boot speed | Inherit double speed from initialization |
| Mobile enable/disable and Battle Tower room menu | Paired double/normal switches | No equivalent helper/call sites in this checkout |
| Return from ordinary screens | Remain at enclosing speed | Remain in double speed; no switch back to normal |
| Battle-animation speed detection | SPD read selects VBlank handler 1 or 3 | Same selection, `engine/battle_anims/anim_commands.asm:25-29` |

A full assembly/include search for speed helpers, KEY1/SPD accesses and STOP
finds only Polished's initialization switch and the battle-animation SPD read
outside hardware definitions. There is no normal-speed restoration path or
menu-local switch. The ordinary-screen inheritance above follows from this
boot setup and call-site audit; it is not a separate runtime observation for
each screen.

Its timing-sensitive graphics code also budgets for double speed:
`home/vblank.asm:143` describes approximately 2,280 M-cycles per VBlank, with
LY-gated heavy map copying; `engine/pokedex/lcd.asm:637-642` explicitly states
double-speed assumptions for its cycle-critical HBlank functions. Other text
matches are not CPU switches: the intro's faster Unown fade and Quick Powder's
Ditto Speed multiplier are unrelated.

Audio qualification: Polished's `PlayCry` uses its command-based audio engine.
For example, `audio/siren-cries/weavile.asm:1-9` identifies a WAV-derived
approximation using two square channels and noise, not streamed PCM. Although
`tools/dedenc.c` exists, the linked cry includes do not use DED payloads;
`TODO.md:51` explicitly lists DED cries among features not planned. This is
therefore useful precedent for sustained double-speed gameplay and synthesized
audio, **not proof for our sampled-cry timer/cache driver**.

Because normal gameplay stays at double speed, Polished also avoids our
prototype's recurring double-to-normal return transition. It does not resolve
SameBoy's APU odd-mode qualification or replace the fork-specific cross-owner
audio tests. Nothing in this audit requires expanding our proposed whole-Dex
speed owner into a whole-game speed change. Production ROM/source, comparison
checkouts and saves were not changed by this follow-up.

## Resource Budget

Exact final delta: **+3,821 ROMX bytes**, one added mapped 16KiB bank `$b9`,
**-14 ROM0 bytes**, two reused bank-3 overlay bytes and two temporary stack
bytes. Versus round one: +104 ROMX bytes.

| Component versus production | Linked delta |
| --- | ---: |
| Dex bank `$10`, including lifecycle wrappers | +41 ROMX bytes |
| Area bank `$24` call sites | +19 |
| Listing bank `$77`, no lookahead/no round-one repair | -87 |
| Animation policy | +37 |
| Info queue/preparation/retention/admission | +372 |
| Glyph/Town Map copy/palette helpers | +577 |
| Performance Index: 2,760 data + 62 lookup + 40 timer helper | +2,862 |
| ROM0 startup relocation | -14 ROM0 bytes |

Pending Info page at `$db65`, retained flag `$db66`; workspace ends `$db67`,
**153 bytes before `$dc00`**. Existing overlay slack, not new permanent WRAM.
No VRAM, OAM, SRAM, WRAM0 or HRAM growth. About 63 unused legacy glyph-helper
bytes could be reclaimed on promotion; they were not needed for this test.

| Region | Production used / free | Final used / free |
| --- | ---: | ---: |
| ROM0 | 15,830 / 554 | **15,816 / 568** |
| Mapped ROMX | 2,314,022 / 700,634, 184 banks | **2,317,843 / 713,197, 185 banks** |
| SRAM | 49,994 / 15,542 | unchanged |
| WRAM0 | 4,083 / 13 | unchanged |
| WRAMX | 23,944 / 4,728 in seven banks | unchanged aggregate |
| HRAM | 127 / 0 | unchanged |

Mapped free space increases because a largely empty bank is added. About 1.77MiB
of the 4MiB cartridge is outside linked ROM0/ROMX payload. Aggregate WRAMX slack
is bank/section-specific, not one interchangeable pool.

## Regression Results

| Final suite | Cases | Failures |
| --- | ---: | ---: |
| Physical timing matrix | 3,280 | 0 |
| All 373 species: cold/internal, Info, Moves, Area, stress | 6,182 | 0 |
| Actual Listing cache/frames/palettes/wrap/cancellation | 613 | 0 |
| Area return across selected Info pages | 504 | 0 |
| Uncaught/Kanto-locked Area | 72 | 0 |
| Live roamers, unlocked/locked | 48 | 0 |
| Female-player Kanto Area | 36 | 0 |
| Held-scroll final candidate | 6 | 0 |
| Cross-owner audio | 1,920 | 0 setup/speed/comparison regressions; baseline misses retained |
| Post-switch New Entry animation/input | 8,890 | 0 |
| Current host/unit contracts | 320 | 0; two explicit skips |

Negative units reject speed leaks, changed samples, altered timer configuration
and changed exhaustion. Historical `test_dex_timing.LinkedTests` require their
captured old link/trace labels and are excluded, not silently reported passing.

Limits: no physical-CGB APU qualification, full native trainer/PC/hatching/
trade/evolution UI campaign, arbitrary Cartesian product of all inputs, other
Dex modes or universal future-workload admission proof. Native wild enemy,
player, faint and full post-catch Entry plus shared wrappers have direct checks.

## Reproduction And Manual Review

Preserve round one. Build a separate copy:

```sh
python3 tools/build_dex_performance_round2.py \
  --variant combined-no-lookahead \
  --output build/dex-performance-round2-rebuilt --jobs 24
```

Regenerate matching Listing checkpoints with `dex_timing.performance`; never
use another ROM's states. Reusable additions: `performance_audio` for native
post-switch contexts; `performance_entry` for registration/input replays; the
read-only SameBoy observer. No second hardware model is introduced.

```sh
python3 -m tools.dex_timing.performance_audio \
  --baseline build/dex-performance-20261003/current/config.json \
  --candidate build/dex-performance-20261004/combined-no-lookahead/measurements/config.json \
  --output build/dex-performance-20261004/cross-audio --jobs 24
python3 -m tools.dex_timing.performance_audio \
  --baseline build/dex-performance-20261003/current/config.json \
  --candidate build/dex-performance-20261004/combined-no-lookahead/measurements/config.json \
  --shared-from build/dex-performance-20261004/cross-audio \
  --output build/dex-performance-20261004/cross-audio-shared --jobs 24
python3 -m tools.dex_timing.performance_entry \
  --audio build/dex-performance-20261004/cross-audio \
  --output build/dex-performance-20261004/cross-entry --jobs 24
```

Use fresh output paths for a new link. Generated ROMs, saves, states, runners,
PCM/WAVs and traces remain ignored. Compressed evidence restores losslessly;
representative WAVs stay openable for listening.

Manual priorities:

1. Active/settled Info on Dusknoir, Garchomp, Luxray, Weavile, Rampardos and a
   synthesized control. A cycling, every Info page and internal paging.
2. B-return fresh from Description/Moves, directly from Info, and from
   Description/Moves **after visiting Info**. Judge immediate perceived response.
3. Area from all tabs, exact-page return, repeat visits, empty/roamer cases,
   held Listing scrolling near both ends.
4. Enter/leave several times; listen to music/SFX at each switch, then Stats,
   wild/player cries and New Entry. Do not mistake the documented old adjacent
   misses for new prototype failures.
5. Independent core or physical-CGB switch/audio comparison before removing
   SameBoy's hardware qualification.

For this exact private link, Selected animation miss is `Pokedex_AnimationMiss`
at `$a0:$6671`. Sample-cache exhaustion is the verified empty-cache branch at
`$00:$3cc1`, six bytes before `SampledCry_AsyncTimerTick.has_decoded_block`.
It is not the normal end-of-cry branch.

```text
breakpoint $a0:$6671
breakpoint $0:$3cc1
```

On an unexpected hit, record species, screen/action, before/after Dex visits,
registers, backtrace, `ticks keep`, `lcd`, and these reads:

```text
x/8 $4:$dff4
x/6 $0:$ffee
print/x [$ff4d]
print/x [$ff06]
print/x [$ff07]
```

For a Selected animation miss also capture `x/27 $0:$c72e`; outside Selected
that scratch is not valid Dex instrumentation. Categorize adjacent-owner hits
by stack/remaining state: the documented Stats/wild failures are still present.
