# Selected Info Ancestors: Production Integration

Date: 2026-10-13. Status: complete, integrated, qualified and manually accepted.
The final report is merge-ready with no new
issues relative to production, including explicitly retained baseline exceptions.
No commit or push was made. Production retains its precomputed renderer.

## Build Identity

- Baseline commit: `f4182c81fc19a637feffa7b17e8fa01a7d4e77df`.
- Baseline ROM: `6ee2b0026f6b68fed2e28a5e15613c194310d6e7c5da9d5d0079268f41b48eac`.
- Integrated ROM: `357d1699b916c87a850ea4b4fff8f4d382de1d3251d8941380c65283667faed0`.
- Production cartridge: `pokecrystal.gbc`, with matching `.sym` and `.map`.
- Frozen candidate and evidence: `build/dex-selected-ancestors-integration-20261013/`.

The temporary Hoenn/Magnezone/Mamoswine evolution timing fixture is not in
production. Both forward and ancestor pages derive only from the actual native
evolution records. Missing evolution links remain a separate data task.

## Behavior And Implementation

Info cycles through Stats, forward Evolutions, then Evolves from. Empty groups
are omitted; an odd forward group never shares a page with ancestors. Both
groups use the existing two-entry layout, minis, requirement wording and
publication/cancellation machinery. Ancestors are earliest first, contain only
the selected species' lineage and show each actual edge's requirement.

- Bayleef: Stats; Meganium / Level 32; Chikorita / Level 16.
- Meganium: Stats; Chikorita / Level 16 and Bayleef / Level 32.
- Chikorita: no ancestor section. Branched lines do not include siblings.
- Existing caught/uncaught visibility rules remain in force.

`tools/pokedex_info_assets.py --ancestors` generates six-byte species headers:
forward count/pointer and ancestor count/pointer. Both lists point to pooled
eight-byte precomputed display records. Names, requirements, heading pixels,
numbers, bars and the existing restoration mechanism remain precomputed.
The generator rejects ambiguous parents, cycles and over-capacity pages.

`engine/pokedex/pokedex_ancestors.asm` handles group/page selection and the
static heading. It lives in the existing Info ROM bank. The 13 new heading
tiles temporarily occupy bank-1 Unown font cells `$b5-$c1` (`$8b50-$8c1f`).
They use existing dead mini staging, not a new buffer or the primed animated
portrait payload. CGB Unown entry restores exactly those original inverted
glyphs. Selected preparation uploads the heading only for caught species with
ancestors. No composition is added to any shared interrupt handler.

Other game edits are limited to `Makefile`, `main.asm`,
`engine/pokedex/pokedex_info.asm` and the paired Unown-entry restoration call
in `engine/pokedex/pokedex.asm`. Area, save/discovery storage, gameplay
evolution rules, battle logic and shared ISR code are unchanged.

## Resources And Performance

| Allocated region | Change from original production |
| --- | ---: |
| ROMX | +5,332 bytes |
| ROM0 / WRAM0 / WRAMX / SRAM / HRAM | 0 bytes |

The linked ROMX total is 2,340,802 bytes. Original live RAM addresses also match
the baseline. The feature does not require another persistence format.

Fresh comparisons have 1,072 general timing cases, 1,056 feature timing cases,
512 Selected-entry cases and eight Dex-reopen cases. Existing settled Stats
and first-forward-page medians remain effectively unchanged versus original
production. Some early requests, species changes and Area returns cross one
display boundary; this is not an instruction-identical feature addition.
The full paired entry check has 256 cases/style: native reveal delta is exactly
zero throughout Legacy and -0.48 to +0.46 ms in Modern, median zero. Valid,
legacy, full legacy and recovery loading medians match production exactly;
normal saving differs by -0.117 ms. All battle renderer durations are exact.

The archived VRAM renderer with the same ancestor pages recovers 15,588 ROMX
bytes relative to this build, without reducing the linked RAM allocation.
Its median Stats cost is roughly +33.5 ms settled / +50.2 ms early, and its
first-forward-page cost roughly +84 ms settled / +117 ms early. The matched
feature matrix reaches +150.73 ms for its slowest page transition. Those costs
are absent from the chosen precomputed architecture. Detailed paired evidence
is preserved in the archive's `production-ancestors-comparison.json`.

## Qualification

Completed focused checks:

- Eight ancestor asset/linked-code tests, including every native header/list,
  ancestry ordering, page capacity, atlas/sidebar preservation and bank restoration.
- 746 all-species Info and 746 Selected Moves native cases, no failures.
- 400 rapid/held/canceled Info cases and 115 visible-panel return checks, no failures.
- 16 ancestor-font-reuse scenarios / 96 transitions, no failures.
- 1,072 general timings, 1,056 feature timings, 512 entries and eight reopens,
  no functional failures.
- 4,479 main Dex cases, plus Pokemon Search, all sort/mode transitions and
  the full Unown content/border/font regression, no failures.
- Six-model Type Matchups and six-model Unown selection qualification;
  112 Unown selections/model plus 156 direct decoder cases, no failures.
- Shared blinking cursor checks at 52 locations / 3,328 idle frames, no failures.
- Moves Search filtering, visuals, naming/cursor, navigation and preference
  persistence, all passed after restoring historical negative-control fixtures.
- Discovery persistence, acquisition/learning, corruption/migration/interrupted
  writes and lifecycle checks passed.
- 960 paired cry/audio cases and 22 surrounding gameplay scenarios passed.
- Both 122-song private Type-owner audio/SFX stresses passed, including held
  navigation and actual palette/pixel/bank checks.
- Exhaustive battle rendering: 7,312 calls / 3,656 production-candidate pairs,
  exact duration, logical sequence, pixels and restoration.
- Normal all-move battle inputs: 1,332 cases / 666 pairs. 632 clean pairs;
  all 34 known exception identities match production exactly.
- Historical 100-move/four-phase battle campaign: 1,600 cases / 800 pairs,
  no failures or over-one-frame timing differences.
- Battle discovery: 4,724 contract and 400 semantic cases, plus Bide and actual
  battle/save/cold-reload/Dex roundtrip, no failures.
- Full playback: 2,238 cold/paging/warm cases across Modern and Legacy, no failures.
- Normal/custom menus, 24 speed/learning/loss transitions, cache-warming-disabled
  idle checks, gift idempotence, chart and final readiness all passed.
- Current host group: 86 tests, no new failures. The LY=64 synthetic Info
  handoff assertion fails identically on baseline and candidate (`5 != 0`).
- Historical host group: 187 cases each, identical results and messages:
  six failures, 16 errors and 103 skips on both. This is retained historical
  model/fixture coverage, not a claim that all historical host cases passed.

All 15 campaign phases, including the final report, completed successfully.
`precomputed-regression/full-regression.json` records `merge_ready: true`,
`issues: []`; it checks fresh all-move, audio and six-model evidence against
the exact candidate hash. The final root rebuild still matches that hash.

Initial Moves failures were missing compressed historical fixtures, not ROM
assertion failures. Restoring and rebuilding the negative-control observer and
donor battery produced a successful retry. Original phase logs and retry
results are retained. Host snapshots keep their own matching generated tables;
new six-byte ancestor tables must not overwrite the old baseline's tables.

The all-move exceptions are retained coverage limitations: condition-specific
moves not activated by the generic fixture, battle-ending/menu-return paths,
and the separately backlogged production Sand Tomb hang. Direct rendering
covers their animation scripts; this does not claim to fix their gameplay.
No physical Game Boy hardware has been tested.

## Archived Fallback

The permanent handoff is
[Selected VRAM Renderer Fallback](archived/selected-vram-ancestors-20261013/README.md).
It includes complete source/assets, exact cartridges and saved batteries,
baseline and temporary-cry-fixture variants, porting diffs, recipes, checksums,
memory/VRAM ownership, costs, risks and instructions for another Codex thread.

The canonical source archive was restored into a fresh build directory and
rebuilt from new objects. It reproduced the reviewed fallback ROM exactly:
`07bec143ad5138fed762476fdc8df9bd8f57011e121b6d4b1cbf1d5b4efb23d2`.
All archive checksums and compressed streams were verified. Individual archive
files stay below 12 MB; the complete handoff is about 46 MB.

## Manual Review

Open the root production ROM. In either Pokemon listing style, select caught
Bayleef and enter Info. Cycle Stats, Meganium/32, Chikorita/16, then Stats.
Repeat with Meganium, which shows Chikorita/16 then Bayleef/32 on one ancestor
page. Check a branched family, switch tabs/species during a cry, cancel a page
update and return to the listing. Enter Unown afterward and check all letters,
then return to Selected Info. The feature uses existing borders and needs no
new editable graphic asset.
