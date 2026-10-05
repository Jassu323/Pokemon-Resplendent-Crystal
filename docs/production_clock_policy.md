# Production CPU clock and Dex performance

Integrated 2026-10-05 from the manually accepted normal-battle prototype.
The clean production ROM is byte-identical to that accepted cartridge:
`94ca7887537a378e036f9b5bfd5e771ef8989ec0c20854e32da13bf100d53aec`.
The former production reference is `2cec8051763e01b45fc2da51186ef795477fe7d4`,
ROM `7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666`.
Live battery saves were not modified, and no commit was created automatically.

## Clock ownership

- CGB initialization requests double speed only after the stack and hardware
  flags are valid, before ordinary audio setup with LCD/interrupts disabled.
  Soft reset uses the existing current-speed guard, not an unconditional STOP.
- Ordinary overworld, menus, Dex and standalone Stats inherit double speed.
  The LCD/APU retain their physical clocks: one display interval is still
  70,224 normal T-cycles, about 16.742706ms.
- `StartBattle` completes the existing battle wipe, then calls
  `BattleSpeed_EnterNormal` on its black screen before loading the battlefield.
  The wrapper waits for SFX, disables LCD/interrupts, saves IE, stops any owned
  sample, disables NR52, requests normal speed and reinitializes sound. It
  restores IE/LCD and deliberately restarts battle music at that hidden handoff.
- Entire battle ownership remains normal: opponent/player animation, battle
  menu, nested Party/Stats/Pack, catch, registration, XP/level-up and post-battle
  evolution. Do not independently toggle those nested screens.
- Map setup's existing LCD-disable command calls `BattleSpeed_MapDisableLCD`.
  While `wBattleMode` is nonzero it does not switch. After battle cleanup it
  calls `BattleSpeed_LeaveNormal`: disable interrupts/APU and sampled ownership,
  request double speed, reinitialize sound, restore IE. LCD stays off for the
  native map graphics reload and music restoration. Native whiteout uses the
  same guarded map return. There is no visible battlefield speed switch.
- Disabled multiplayer paths remain disabled. Legacy mobile cleanup requests
  the ordinary double-speed policy; this does not qualify or enable multiplayer.

No move script, frameset, object-motion function, BG effect, vibration amplitude
or sound schedule was retimed. Rejected shared pacing, phase/motion payloads
and the double-speed wild-slide workaround were not promoted. They remain
historical research, not production dependencies. Battle animation performance
optimization is deferred to `BATTLE-PERF-01`.

## Audio contract

The existing ROM0 timer-start entry dispatches to ROMX. Normal/even playback
keeps its original active IRQ budget; only double-speed odd-period playback
uses alternating reload work. The existing HRAM byte is 0 inactive, 1 normal
or even period, 2 double-speed odd period. The alternating step reuses bank-4
padding, not a new memory allocation. See [sampled cries](sampled_cries.md).

At New Dex Entry's final owner exit, after cancellation of the animation, a
guarded DI/stop/EI cancels any remaining nonblocking sample. The internal
page-1/page-2 transaction does not cancel it. This prevents playback leaking
into naming/post-catch waits that do not service that owner. Intentional
cancellation is audited separately from natural completion; it is not counted
as successful complete sample playback.

## Retained Dex optimizations

All are the accepted double-speed options with useful measured paths, not a
claim that every request saves an interval. Historical timings and independent
ablations are in [global qualification](global_double_speed.md).

| Component | Production behavior |
| --- | --- |
| Active Info admission | Recheck physical-frame/scanline, DMA ownership and sample runway for each bounded slice; keep finishing reserve |
| Quiet Info preparation | Bounded batch work while settled; no speculative work that steals animation publication deadlines |
| Info queue | Finish/publish the current job, coalesce newer requests into one target, clear pending state on real exit/reset |
| Area transfers | Decompress into owned scratch, transfer padded tile/attribute maps and graphics in batches, expanded palette lookup |
| Static nests | Build-time species/region index, preserving encounter-order deduplication; merge live roamers at runtime |
| Info across Area | Retain only a committed idle page using its record and dead scratch; reconstruct if validity conditions fail |
| Listing cache | Three resident visible rows, no eager offscreen lookahead; retain the five physical slots for scroll staging |
| Glyph transfer | Copy a bounded glyph batch with one source-bank handoff |

`tools/pokedex_area_assets.py` now produces `build/dex-area-assets/tables.asm`
and `town-pals.bin` directly from species/map/landmark constants, native grass
and water encounters, map headers and the Town Map palette source. Make tracks
all those inputs. Species and encounter edits regenerate the index; there is
no manual species index and no prototype ROM dependency. The unused private
Stats table was not included. Validation rejects unsupported/incomplete
encounter records or mismatched map ordering instead of silently omitting data.

The table and palette payloads reproduce the accepted prototype exactly.
All 746 species/region nest entries are also checked against the original
native encounter walker by `tools/test_pokedex_area_assets.py`.

## Linked resource cost

Compared with the former production link: **+31 ROM0 bytes, +3,902 ROMX bytes,
one additional mapped ROMX bank, no aggregate RAM/VRAM/OAM growth**. The ROM
remains padded to 4 MiB. Info pending/retained fields and timer alternation use
existing scratch/padding; ownership lifetime, not free space, governs reuse.

| Resource | Used | Free in mapped sections/banks |
| --- | ---: | ---: |
| ROM0 | 15,861 | 523 |
| ROMX | 2,317,924 | 713,116 across 185 banks |
| WRAM0 | 4,083 | 13 |
| WRAMX | 23,944 | 4,728 across 7 banks |
| HRAM | 127 | 0 |
| SRAM | 49,994 | 15,542 across 8 banks |

ROMX free space is not the entire unused portion of the padded cartridge.
ROM0/WRAM0/HRAM remain constrained; future work must not infer spare premium
memory from the much larger cartridge budget. The retained native battle
envelope itself costs +24 ROM0/+98 ROMX against the preceding all-double trial.

## Fresh production qualification

Fresh results are retained under the ignored directory
`build/production-speed-integration-20261005/`; no old CPU checkpoint is
transferred between ROM links. The old ROM/symbols/map are backed up there.
The original battery test seed was restored from its verified historical
archive; live saves and the separate animation-review save remain untouched.

`python3 -B -m tools.dex_timing.production_speed <suite>` provides isolated
matching-link setup for menus, custom inventories, 100 moves/both sides,
cross-owner audio, odd timers, authentic registration, all-species Dex,
20-species New Entry input sweeps, native gameplay and continuous speed switches.
Run `menus` before `custom`/`moves`/`gameplay`/`transitions`, and `audio` then
`registration` before `new-entry`. Pools run sequentially with at most 12
workers (normally 16-24); initial integration used 19 build jobs and the final
clean rebuild used 12. Menu/setup pools use eight or fewer workers.
Coverage is not reduced for the requested CPU headroom.

### Completed results

| Fresh suite | Coverage | Result |
| --- | --- | --- |
| Selected Dex | 6,182 cases across all 373 species: 1,492 Info, 746 Moves, 373 cold entries, 373 internal paging, 2,238 Area, 400 Info stress, 560 Moves stress | Zero content, input, animation, audio or ownership failures |
| New Dex Entry | 20 baseline plus 8,572 input/phase cases; 1,211,179 display intervals audited | All 8,592 pass exact authored timing, publication and natural-versus-canceled cry accounting |
| Native menu input | Both links: 1,792 axis/register and 1,344 hold/button/chord controls; standard, battle, Mart, puzzle, Game Corner | Zero wrong masks/registers, return or walking/bicycle failures |
| Custom inventories | 232 actions per link; five Pack pockets, 57 TM/HM selections, seven Apricorn colors | All 464 pass selection, scrolling, palette/OAM and clock checks |
| Battle moves | 100 moves, both sides, four starting offsets, both links: 1,600 executions / 800 comparisons | Zero execution failures; identical logical, object, BG and sound-command sequences |
| Cross-owner audio | 20 species, six contexts, four offsets, both links: 960 runs | No new misses; existing battle failures and Stats improvements separated below |
| Odd-period timer | 128 executions / 64 comparisons against the accepted all-double parent | No timer, waveform, CH3 frequency or content differences; zero misses |
| Native gameplay | Ten scenarios: maps/buildings, shopping, sliding puzzle, fishing, Joey, phone, level-up/evolution, egg, full-party PC catch, healing/save/reboot/reset | All pass |
| Continuous battle ownership | Four streams of 16 native battles without CPU-state reload; four whiteouts; four win/level-up/evolution routes | All 140 observed battle/map speed switches have LCD/APU off and no active sample |
| Battle soft reset | Four input offsets from a normal-speed battle | Native reset/Continue returns to double-speed overworld; no illegal operation, miss or odd-mode warning |
| Sliding intros | 64 wild and eight trainer cases, both links | No irregular pixel translations or playback/clock failures |
| Area generator | Native parity for all 746 species/region entries and expanded palettes, malformed-record rejection, source order | Three unit tests pass |
| Host helpers | Performance, motion, pacing tests | 13 + 11 + 10 unit tests pass |

The final `make clean` rebuild also starts without the generated Area directory.
Make regenerates it from source, and the ROM still matches the accepted SHA-256
above. Raw glyph inputs needed by the independent content auditor are explicit
prerequisites of its qualification command, not ROM dependencies introduced by
a debug build. No timing observer, fixture encounter or animation retiming was
linked into production.

Evidence relative to `build/production-speed-integration-20261005/`:
`dex-retry/summary.json`, `new-entry/report.json`, `menus/qualification.json`,
`custom-menus/report.json`, `moves/report.json`, `comparison.json`,
`audio/report.json`, `odd-timer/report.json`, `gameplay/report.json`,
`transitions/report.json`, `battle-reset/report.json`,
`intros/{wild,trainer}-report.json` and `fresh-build.log`. Failed *host setup*
attempts remain separately labeled in `menus-*-revision.log` and `dex.log`.
They were corrected by selecting the matching ROM explicitly, restoring the
original fixture party, normalizing the cursor through actual input, and
building the auditor's missing raw stat-bar prerequisite. None required a
production runtime correction beyond the accepted prototype.

The subsequent approved build cleanup retains this qualification losslessly:
bulky per-case traces, frame/audio extractions and individual results are now
in `build/retained-history-20261005/compact/production-speed-integration-20261005.tar.gz`.
Reports/configurations, starting saves/states and the former production ROM
remain loose. Recover the original paths into a scratch directory before using
an archived per-case file. See [the retention and recovery policy](archived/README.md#approved-follow-up-compaction).

### Differences and limits

The 960 cross-owner executions contain 84 known miss-containing runs across
both links. Sixty-four are the same initial battle-appearance failures for
Dusknoir (45 blocks remaining), Groudon (198), Kyogre (226) and Yanmega (405):
each appears in both catch/faint fixtures, before the later action. Their
player send-out, actual faint and New Entry segments complete. Twenty are
former production's standalone Stats failures for Dusknoir, Vibrava, Groudon,
Kyogre and Yanmega. Those five now finish naturally at double speed in all four
offsets. This is evidence for those owner cases, not a general shared-refill fix;
normal-speed nested battle owners and `BATTLE-CRY-01` remain deferred.

Identical animation *state sequences* do not mean identical displayed holds.
The largest fresh primary-effect duration delta is foe Flame Wheel, one phase:
235.080 -> 243.083 intervals (+8.003, about 134ms). Its 201 logical updates,
object/BG states and SFX sequence are identical; boundary holds differ. This is
within the already accepted private trial's observed phase-dependent range,
not an added retiming implementation. The earlier comparison videos and the
unconfirmed Superpower shake report remain available for future work.

These are native headless SameBoy tests plus the user's prior visual acceptance,
not physical-hardware or every-map/full-story coverage. Battle Tower/tutorial
ownership paths are source-audited, not fully played here. Disabled multiplayer
is deliberately unqualified. Premium memory is tight even though all listed
checks pass; future owners must honor the clock, scratch and publication
contracts rather than assuming additional CPU capacity eliminates deadlines.
Prior prototype acceptance is recorded independently in the
[normal-battle report](battle_normal_speed_prototype.md).
