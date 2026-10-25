# Selected Pokedex Moves Pages

Integrated 2026-10-03 after private-prototype regression and the user's visual,
audio, data and miss-breakpoint checks. This extends the Start-menu Selected
Mon lower panel, not the Party Stats Screen, battle or New Dex Entry renderer.
The production ROM and symbols are byte-identical to the accepted prototype.

## Behavior

Select `Mov` and press A to open page 1. Further A presses advance and wrap.
Each page contains at most five moves. Nonempty categories appear in this order:

| Header | Row prefix | Authoritative source |
| --- | --- | --- |
| Level Up | Dedicated level symbol and number | Evolution/level-up records |
| TM/HM | TM01-TM50 or HM01-HM07 | Base-stat compatibility and machine definitions |
| Move Tutor | Tut | Existing three tutor compatibility bits |
| Breeding | Egg | Configured evolution family's existing egg list |

Each category starts a fresh page; empty categories are skipped. The hard limit
is 19 pages, enforced at build time, not silent truncation. Present content has
2,576 caught-species pages across 373 species; Mew's 15 pages are the maximum.
Seen-but-uncaught species get a blank page 1. Internal species paging retains
Mov but resets the incoming page to 1. B cancels pending work and returns to
Listing. Selecting Info or Description cancels the previous lower-panel job.
The Area placeholder and deferred evolution/learnset content are unchanged.

Text uses resident BG font tiles. Prefixes begin at tile column 2 and names at
column 7, on rows 11-15; the title is on row 9. Existing SCX and the shell are
retained. There is no shifted move-name atlas, OAM text or scanline split.
The level symbol comes from the existing battle font, not a capital L.

## Build-Time Index

`tools/pokedex_moves_assets.py` creates disposable outputs under
`build/dex-moves-assets/`. Make tracks the compiler, species/move/item constants,
move names, evolution/level-up files, egg files, compatibility files and the
battle-font glyph. Generated exports make original source lists linkable.

Each species has a 17-byte descriptor: one page-count byte, then four records
of count, bank and 16-bit pointer. Level-up and egg records point at their
original game data. TM/HM and tutor eligibility use compact generated lists;
move names use generated 16-bit pointers into the original name table.
No second handwritten learnset or duplicated level-up/egg payload is needed.

The compiler groups actual evolution links into families, including branches
and babies. Every member references the family's existing nonempty egg list.
Identical lists share a source; conflicting nonempty lists stop the build.
Cycles, unknown targets, inconsistent pointer ordering and resource overflows
also fail. This changes Dex display only, not breeding gameplay records.
112 species gained inherited egg pages without increasing the descriptor size
or adding a runtime graph walk.

Edit the ordinary game data and rebuild to update page counts and pointers.
Fully registered new species are indexed automatically; no manual Dex index
entry is required. Normal source ordering, filename/partition conventions and
bank capacity still apply. Adding a new source partition, nonstandard filename,
machine schema or future tutor system needs a compiler adapter/guard review.
Missing evolution links and empty family egg lists remain `DEX-DATA-02/03`,
not inferred content. Tests exercise source edits and adding a new family member.

## Runtime And Publication

The existing portrait producer and deadline publication run first. Moves then
services at most three bounded work slices. During active portrait playback,
it admits work only while the portrait loop tick matches the display counter
and LY is below 64. Preparation for an incoming species happens before that
species' animation/cry starts; it does not add work inside cry startup.

| State | Work |
| --- | --- |
| 0 | Idle |
| 1 | Resolve indexed category, source and local page offset |
| 2 | Clear one padded lower row; after seven rows prepare badge and heading |
| 3 | Draw one move row from its original source and name pointer |
| 4 | Ready: stage lower OAM clear and request the existing lower publisher |

The old completed page remains visible until publication. Preparing Moves does
not discard the committed Info-visible record used by retained-page B-return.
At publication, Moves clears Info's visible/minis ownership and its own job.
Upper type sprites are preserved. No pending job survives tab/species/Listing
ownership changes. Moves reuses existing tilemap/attrmap staging and publisher;
it does not use Info's glyph atlases or alter portrait slots/timeline budgets.

## Shared Page Indicators

Description, Info and Moves all use `PokedexBadge_Prepare`. It fills the inactive
two-tile digit buffer, then stages map references; the publisher commits the
selector with the completed lower panel. Single-digit and double-digit source
sheets remain editable PNGs in `gfx/pokedex/`, converted in column order.

| Bank-0 signed tile IDs | Use |
| --- | --- |
| $73/$78 | Digit buffer A, upper/lower |
| $79/$7a | Digit buffer B, upper/lower |
| $77 | Existing P. prefix |
| $7b/$7c | Permanent double-digit right-closing pair |
| $7d | Dedicated level glyph |
| $7e/$7f | Unused BG cells |

Pages 10-19 reference the wider closing pair; returning to single digits removes
that reference. All pages 1-19 and both buffer parities have linked pixel tests.
Mainline badge byte writes protect each STAT-check/write pair from intervening
interrupts, rather than holding interrupts off over the whole upload. Description
badge preparation is a separate bounded slice, not hidden inside text setup.
Lower publication updates both top-edge columns used by a wide indicator.

## Physical-Clock Correction

Natural sampled-cry completion formerly re-cleared IF_TIMER inside its ISR.
The IRQ had already acknowledged that request. A new VBlank between the IF read
and stale write could be erased, leaving the software display counter one
physical interval behind. This caused the Info-owned Dusclops-to-Dusknoir
sequence to take 175 intervals while reporting the authored 174, without an
animation miss or sampled-cache-empty breakpoint.

Both timer shutdown branches now use `StopSampledCryAsync_FromTimer`, disabling
playback/timer/CH3 and joining the existing saved-state restoration without
touching IF. Manual cancellation keeps its original pending-timer clear.
No scheduler, duration, decode, 32-block prefill or validator was relaxed.

The exact-phase replay removes precisely 70,224 T-cycles, one physical display
interval (about 16.743 ms), from publication 29 onward. All 35 publications and
557 sampled blocks remain correct. Initial readiness/reveal is identical.
The path costs 14 ROM0 bytes and runs 56 T-cycles faster than the manual path.
Host observers recognize both shutdown entries. Linked contracts test all 32
pending-bit combinations, saved timer/audio restoration and both branch targets.
This is not a fix for unrelated IF updates or the deferred battle cry underrun.

## Resource Cost

| Resource | Change from pre-Moves production |
| --- | ---: |
| ROMX | +15,877 bytes |
| Bank $b7, Moves code and badge assets | 1,727 bytes used |
| Bank $b8, index and lookup data | 14,070 bytes used |
| Existing ROMX integration, net | 80 bytes |
| ROM0, timer correction | +14 bytes; 554 bytes free overall |
| WRAM0 / HRAM | No additions; 13 / 0 bytes free |
| WRAMX | 45 bytes of existing overlay padding, no section-size growth |
| SRAM / portrait VRAM / type OAM | No additions or layout changes |

The 45-byte workspace occupies bank 3 $db38-$db64: ten Moves job bytes, three
badge selector/page bytes and a 32-byte glyph buffer. The overlay ends at $db65,
leaving 155 bytes before its $dc00 assertion. It is mutually exclusive with
Battle Tower storage, not a separate live allocation. Move/Area work must still
respect the other lower-panel lifetimes. Total linked cart usage is 2,329,771
of 4,194,304 bytes (55.55%), leaving 1,864,533 bytes, about 1.78 MiB.

## Validation

The user manually accepted every prototype review entry without visual/audio/data
errors or either miss breakpoint. A clean production build is byte-identical to
that accepted ROM and symbol file. The following production checks completed
2026-10-03, with independent suites running concurrently and worker pools within
the species/input sweeps:

| Production check | Result |
| --- | --- |
| Moves, caught | 373 species; all 2,576 pages, wrapping and internal paging pass |
| Moves, uncaught | 373/373 blank-page cases pass |
| Moves input/cancellation stress | 1,323/1,323 cases pass |
| Info | 746/746 cases pass |
| Description | 1,492/1,492 cases pass |
| Cry ownership | 1,492 species handoffs, 40 targeted cases and 14 navigation controls pass |
| Cold Listing | 373 entries and 373 returns pass |
| New Dex Entry | 8,594 generated-context cases across 20 species pass |
| Focused linked tests | 93/93 pass |
| Sampled decoder | All 122 assets, 37,655 blocks, decode byte-exactly |

No animation or sampled-cache misses were found. Reports are under ignored
`build/dex-moves-production-regression/`. The main regression run completed in
about 5.3 minutes; this is measured wall time, not a claimed speedup over an
unmeasured sequential run. Matched Moves A/B replays retain identical first-page
readiness for all 373 species. The production matched Info replay also confirms
Dusknoir's 35 publications and all 557 cry blocks over the authored 174 physical
intervals (the instruction-boundary measurement is 173.999829 intervals).

Production ROM SHA-256:
`72173fbfb6d14537384238d538cbabbb3dff7de8d7778fb0c50f6f93c442945e`.
Production symbol SHA-256:
`bc062e0b26c82bf71938d6aadaef230fa2067eb9606d7c0abba8f192817bc5ac`.

Listing restoration passes 96/96. The separate strict follow-up legality audit
retains three pre-existing Dusknoir palette-write warnings (`DEX-GRID-04`), with
correct sampled visible content. Full legacy test discovery retains the same
six failures and sixteen errors as the untouched baseline; these historical
scheduler-model assertions are not weakened or reported as passing.

Ordinary suite entry points, with unique output folders for concurrent runs:

```sh
PYTHONPATH=tools python3 -B -m dex_timing.moves_ui --output build/moves-caught --jobs 8
PYTHONPATH=tools python3 -B -m dex_timing.moves_ui --uncaught --output build/moves-uncaught --jobs 8
PYTHONPATH=tools python3 -B -m dex_timing.info_ui --battery /path/to/private.sav --output build/info --phases 0 settled --jobs 8
PYTHONPATH=tools python3 -B -m unittest test_pokedex_moves test_sampled_cry_shutdown
```

The normal-input suites copy/prepare private batteries, never edit the user's
live save. The New Dex Entry factory uses an explicitly recorded native-catch
donor and generated species contexts, not claims of twenty authentic catches.
Optional instruction-level IF/clock tracing is host-only (`DEX_CLOCK_TRACE`).

Current production miss breakpoints:

```text
breakpoint $a0:$6677
breakpoint $0:$3cc1
```

The second is cache exhaustion, not natural completion or intentional cancel.
If one fires, capture registers, backtrace, `ticks keep`, `lcd`, and:

```text
x/27 $0:$c72e
x/45 $3:$db38
x/8 $4:$dff4
x/6 $0:$ffee
```

Record species, tab/page and input, and whether the path was cold entry,
internal paging or B-return. Re-resolve these addresses after future linking.
Prototype history and its exact-phase controls remain under ignored
`build/dex-moves-prototype/`, with its rebuild script and README preserved.
