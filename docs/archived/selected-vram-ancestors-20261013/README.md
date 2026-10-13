# Selected Pokemon VRAM Renderer Fallback

Archived 2026-10-13. This is the complete rejected space-saving Selected
Pokemon renderer, including its ancestor pages. Production retains precomputed
display graphics for speed. Revisit this fallback when ROM space is more
valuable than the additional Info-page latency. Do not install it by replacing
a future checkout wholesale.

## Preserved Versions

- `production-before-ancestors.tar.xz`: original production source at commit
  `f4182c81fc19a637feffa7b17e8fa01a7d4e77df`, plus required generated graphics
  and display assets. Its cartridge archive contains the matching ROM/map/symbols.
- `vram-ancestors-source.tar.xz`: exact reviewed runtime-display/semantic-ROM/
  VRAM-recovery source, without the temporary evolution fixture.
- `vram-sampled-evolutions-source.tar.xz`: that architecture with the nine Hoenn
  starters and completed Magnemite/Swinub lines used for cry timing. The new
  Level 40 links are test-only and must not become future balance decisions.
- The two corresponding `*-cartridge.tar.xz` files contain immutable review
  ROMs, symbols, maps and saved batteries.
- `production-before-to-vram.diff`: the text-code conversion from the frozen
  old production source. Generated files are rebuilt, not embedded in the diff.
- `sampled-evolution-fixture.diff`: isolates the temporary evolution data.
- `recipes/`: frozen generators, build recipes, assembly modules and patches.
  Full source snapshots are the authoritative restoration route; old recipe
  paths assume the October 12 baseline and must not be run blindly on new HEAD.
- Frozen resource/timing comparisons, the earlier reports and regression
  runbook are retained beside this guide. They describe their original binaries,
  not acceptance of a new integration.

`manifest.json` records checksums of the preserved files. Source archives
include native animation dictionaries/plans/timelines/schedules, converted
graphics and all required generated Selected assets. They exclude disposable
CPU checkpoints, raw frame/audio captures, observer binaries and object files.
No old `build/` directory is required to restore the game source itself.

## Restore And Rebuild

From the repository root, use a fresh private destination:

```sh
PYTHONPATH=tools:. python3 tools/archive_selected_vram_ancestors.py verify
PYTHONPATH=tools:. python3 tools/archive_selected_vram_ancestors.py restore --destination build/restored-selected-vram --variant vram-ancestors
make -C build/restored-selected-vram -s -j6 pokecrystal.gbc
shasum -a 256 build/restored-selected-vram/pokecrystal.gbc
```

The reviewed cartridge hash is:

```text
07bec143ad5138fed762476fdc8df9bd8f57011e121b6d4b1cbf1d5b4efb23d2
```

The archive was restored into a new directory and rebuilt from fresh object
files on October 13. The resulting ROM matched this hash exactly. This checks
the restoration recipe, not merely the integrity of the copied cartridge.

Use `--variant production-before-ancestors` to restore the original code and
cartridge, or `--variant vram-sampled-evolutions` for the cry fixture. The
restorer refuses existing destinations and destinations outside `build/`.
Standard RGBDS/Make/Python tools are still required. On a different host,
rebuild native utilities rather than relying on bundled host executables.
Native testing additionally needs the SameBoy source and legally supplied CGB
boot ROM identified in the regression runbook.

The final integration adds a version-specific
`production-ancestors-to-vram.diff` and `production-ancestors-comparison.json`
with exact production-with-ancestors costs and matched native timing evidence.
That patch is an implementation reference, not a promise of applying cleanly
after unrelated future changes. The immutable source archives remain the
authoritative originals.

## Architecture

### Retain Meaning, Generate Pixels

Info retains a six-byte header per species: forward count/pointer and ancestor
count/pointer. Semantic lists contain permanent target indexes and native
evolution method/parameter fields, five bytes per entry. Complete semantic
lists are deduplicated. This is not a stored shifted-name or requirement image.

Selected Moves retains its existing stream pointers/counts, egg-family mapping,
TM/HM/tutor compatibility lists and page counts, plus the already shared move
name pointer index. The Area page, move descriptions, actual evolution rules,
type icons, minis, palettes, borders and portrait plans remain unchanged.

Removed display-only ROM consists of the Info glyph pool, precomposed evolution
text lines and source pointers, shifted headings, and numeric/bar lookup
graphics. Rendering instead uses the original font/item/move names, native
level marker, and seven original bar-art tiles.

### Local Bounded Composition

`pokedex_runtime_graphics.asm` composes shifted/compact text, decimal digits,
partial bar tiles and headings. `pokedex_runtime_data.asm` formats native
requirements and selects retained semantic records. `pokedex_runtime_font.asm`
copies glyph rows from the font's own ROM bank, avoiding per-row far reads.

Work remains in ordinary Selected preparation and the existing admitted Info
service slices. A 40-tile local atlas deduplicates composed pixels for the
requested page. It is published through the existing double-buffered
tilemap/attribute/OAM ownership path. Completed visible pages remain stable
while another request is prepared or canceled. No composition is added to
shared VBlank, LCD, timer or audio handlers.

The CPU is already double speed, but the display cadence is not. Bounded work
can consume additional display frames. More ROM savings do not imply that the
game can perform that work invisibly between two arbitrary inputs.

### VRAM Recovery Instead Of A RAM Copy

The broad runtime prototype used a persistent 640-byte copy of the committed
atlas-B pixels. This version removes that allocation and the ordinary page
jobs maintaining it. It uses the visible, committed atlas-B image already in
bank-1 VRAM as the recovery source.

On the affected Modern-listing return, producers are canceled, committed
atlas-B pixels are captured into existing `wPokedexInfoGFX`, and the existing
upload path reconstructs scattered atlas A before the listing's cache repair
overwrites atlas B. The visible lower panel is preserved. Legacy does not need
the same repair. Capture is limited to actually used tiles, up to 640 bytes.

VRAM reads use interrupt-guarded pairs: disable interrupts, wait for STAT
mode 0/1, read two bytes, and re-enable interrupts. The pair fits the following
80-dot mode-2 margin even at normal CPU speed. VBK and caller bank state are
restored. The capture must precede every operation which repurposes atlas B;
never recover a queued or partially built page in place of the committed one.

### Memory Ownership

The linked WRAM allocation does not grow relative to original production.
There is still 217 bytes of additional temporary use inside the already
allocated bank-3 Battle Tower overlay, ending at `$dc40`: 128-byte composed
line, 32-byte encoded text, eight glyph rows, 16-byte tile and 33 state/format
bytes. Another 24 bytes reuse dead mini staging and three bytes are aliases.
Search begins immediately after this workspace. Do not describe it as unused
global RAM or extend it without auditing every overlapping owner.

Unlike the broad runtime trial, there is no 746-byte parent index, 180-byte
evolution cache, 77-byte Moves cache or 640-byte restoration allocation.
Bank 5 ends at `$d950`, leaving 1,712 bytes before `$e000` in the frozen map.
No SRAM format, save migration or discovery storage changes are introduced.

### Ancestor Pages And Heading

Page order is Stats, every forward-evolution page, then every ancestor page.
Empty groups are skipped and groups never share a partly empty page. Ancestors
are ordered earliest first and use each actual edge's native requirement.
Siblings are excluded; missing game-graph links are not invented. Bayleef's
ancestor is Chikorita/Level 16; Meganium shows Chikorita/16 and Bayleef/32.

The 13-tile heading temporarily uses bank-1 Unown font cells `$b5-$c1`, physical
`$8b50-$8c1f`. The runtime version regenerates it eagerly during Selected
species preparation. Unown entry restores exactly those original inverted
glyphs. Returning to Selected regenerates the heading. This ownership is
paired and must not be separated when porting the implementation.

Do not move the heading into the animated sidebar or either scattered Info
atlas. Those collisions occurred in rejected intermediate trials. Also retain
the plain call to the ROM0 graphics wrapper when HL contains the upload
source: replacing it with a farcall clobbers that pointer. Intraspecies paging
and an actual all-letter Unown-font readback are necessary tests.

## Costs And Benefits

The original frozen production has no ancestors. Relative to that binary, the
reviewed VRAM version with ancestors reclaims 10,256 allocated ROMX bytes and
adds no allocated ROM0/WRAM0/WRAMX/SRAM/HRAM bytes. Adding ancestors inside this
architecture costs 2,108 ROMX bytes. The comparable production-architecture
ancestor cost is 5,332 ROMX bytes, with no additional allocated RAM. Therefore
the fallback recovers **15,588 ROMX bytes relative to production with ancestors**
(15.22 KiB, about 95% of a 16 KiB bank). It does not recover 15,588 bytes from
the original binary or necessarily free one contiguous bank. The exact linked
totals are 2,340,802 ROMX bytes for production with ancestors and 2,325,214 for
the fallback. This excludes disposable test assets and source archive size.

The frozen generic comparison observes approximately +33-50 ms for Stats,
+84-117 ms for forward pages, +8 ms Dex reopen and +one frame initial Selected
entry. These are content-dependent differences versus the original production,
not universal fixed costs. Selected Moves transitions and typical native
listing-return readiness are effectively unchanged. Raw blinking-image hash
timings can differ by multiple frames without a matching native reveal delay.

The final matched comparison uses the integrated precomputed ancestor ROM
`357d1699b916c87a850ea4b4fff8f4d382de1d3251d8941380c65283667faed0`
and the exact archived fallback. Both have the same native evolution graph,
page sequence and displayed requirements. Each has 1,072 general timing cases
and 1,056 feature cases. Positive values below mean the fallback is slower.

| Transition | Settled median | Early-request median | Observed maximum |
| --- | ---: | ---: | ---: |
| Description to Stats, Modern | +33.49 ms | +50.25 ms | +83.71 ms |
| Description to Stats, Legacy | +33.48 ms | +50.23 ms | +66.99 ms |
| Stats to first forward page, Modern | +84.33 ms | +117.20 ms | +133.95 ms |
| Stats to first forward page, Legacy | +83.73 ms | +117.17 ms | +133.98 ms |
| Description to Selected Moves | effectively zero | effectively zero | under 1 ms |
| Listing return, native owner-ready | effectively zero | effectively zero | +17.25 ms |

The feature matrix includes ancestor pages and wraps: its median cycle penalty
is about 33.5 ms settled and 50.2 ms early, with a content-dependent maximum
of 150.73 ms. The generic first-forward sample above is intentionally separate.
The fallback's first Selected portrait reveal is typically one display frame
later; Modern Dex reopen is +8.03 ms. The Legacy reopen sample is 7.05 ms
faster, a changed frame/input alignment rather than evidence that runtime font
composition speeds up opening. See the JSON for all extrema and sample counts.

Production's existing settled Stats and forward-page medians remain effectively
unchanged versus the pre-feature production control. A few early or species/
Area-return requests cross one display boundary. This comparison does not claim
every instruction or every input phase is identical after adding a feature.

The configured cry fixture narrows the comparison: two-entry forward pages
add about 67 ms settled and 84-100 ms active in Modern; one-entry pages add
about 33 ms settled and 33-51 ms active. The largest observed Legacy increase
is 119 ms. All early forward/Stats/line-handoff requests have the corresponding
cry actually active. No sampled buffer starvation is observed. Sampled versus
synthesized cries do not show a distinct extra display penalty, although this
is not a same-species audio-backend ablation.

The trade is less stored display graphics and less restoration RAM for local
rendering complexity and visible Info latency. Guarded readback also relies on
VRAM ownership/cancellation order. Retaining precomputed production graphics
avoids that composition cost. Partial numeric/bar acceleration or conditional
heading preparation are possible unbuilt middle grounds; they must be measured
rather than assumed to recover the entire performance difference.

### When This Fallback Is Useful

Revisit it if generated display data grows beyond available ROM banks, an
Info glyph pool approaches its one-bank capacity, or future species/move/name
changes make static display assets disproportionately expensive. It avoids
storing shifted name/requirement images and number/bar display lookups; normal
font/item/move strings remain the source. It also avoids the additional
640-byte preservation buffer used by the RAM-based runtime trial. Current
production reconstructs pixels from its committed ROM source-pointer records;
it does not have that extra buffer. Both production and this fallback retain
the existing 640-byte Info upload workspace. The fallback introduces 217 bytes
of additional temporary overlay use, not a net allocated-RAM saving.

It is not a remedy for battle animation timing, cry starvation, Type Matchups
interrupt ownership, missing evolution rules or corrupt discovery saves. Those
systems are deliberately unchanged. Font-composition bugs, an overwritten VRAM
recovery source, unsafe overlay reuse or a broken cancellation sequence are
new risks introduced by the fallback, not problems it solves. In those cases,
precomputed production is the lower-complexity choice until the renderer is
repaired. Space pressure is the principal reason to accept this trade.

## Instructions For A Future Codex Thread

Use this guide, `manifest.json`, both complete source archives, and the
production-to-VRAM diff as the implementation brief. Verify and rebuild the
archived source privately first. Read the current repository instructions,
changes, allocation map, Selected owner code and interrupt timing contract.
Do not apply the archive's whole checkout over current production.

Port the local rendering/data/font modules and the required owner, header,
workspace and return changes onto the current architecture. Preserve current
evolution/learnset/item/type/save/cry data rather than restoring the frozen
catalog. Regenerate semantic metadata for the current species and moves.
Keep page selection, tile deduplication, committed recovery and paired
Selected/Unown heading ownership together.

The frozen compiler limits are 19 Info pages and 40 unique tiles per page.
Future species/name/requirement changes must remain within these limits or
explicitly redesign them. Audit the bank-3 overlay and atlas addresses again;
they are not contracts for an arbitrary later checkout. More species grows the
semantic headers/lists; longer names/methods grow composition time instead of
a stored shifted font pool.

Recreate all fixtures after linking. Compare same-content transitions, never
old wrap-to-Stats against a new ancestor page. Capture active cry state at the
accepted request. Use native readiness alongside pixel hashes. Run every Info
page for all species, canceled/held/rapid inputs, all Unown letters after Info,
all return paths, Selected Moves, Type Matchups and complete Dex regression.
Then run the full persistence/discovery/gameplay/audio/all-battle-animation
campaign from the retained runbook. Known production exceptions must retain
their identities. Native/emulator evidence is not physical-hardware testing.

Report exact linked ROMX/WRAMX changes and matched performance against the
then-current production with ancestors. Keep integration separate from the
archive, preserve a rollback point, and do not add any overhead to shared
interrupt handlers. See the archived interrupt timing contract for why.
