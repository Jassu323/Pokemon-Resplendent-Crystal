# Interactive Registration Production Integration

Accepted and integrated 2026-10-16. The user approved the corrected prototype
and explicitly chose to retain its 20 temporary evolution requirements in
production. No commit or push was made; the working tree is ready for review.

## Build And Scope

The root `pokecrystal.gbc`, symbols and map exactly match the fully qualified,
manually accepted review build. Production ROM SHA-256:
`d1ce69a431dc138fdbbecb834c050097e5ebf807856d2d16323d32f644d95ff0`.
The previous production ROM was
`52ba945b4b5e94107495988265401c586ea359212637b666e47df58abe25c7a5`.

Fourteen source/build files were promoted without changing unrelated work.
The exact list and before-source hashes are in
`build/interactive-registration-production-20261016/inputs.json`; the complete
source diff is `promotion.patch` in that directory. `rollback/` retains the
old source, ROM, symbols and map. The player's main save and repository saves
were hash-checked and left unchanged. No emulator-library ROM was replaced.

Registration now provides fixed-species `Desc/Info/Mov/End`; B or End returns
to the original capture or prize continuation. Selected-style authored
portrait animation and cry playback continue across tab changes. Browsing
does not discover moves or change Listing bookmarks.

The successful-capture tail switches to double speed at the silent Gotcha
music-reset boundary, synchronized to early LCD mode 3 with the LCD still on.
This exception belongs only to that helper, not the generic speed-switch API.
Shared interrupt handlers have no new per-frame overhead; normal battle
animations remain normal speed. Registration preserves all three Pay Day
bytes rather than clearing legitimate earnings. Keep its 67-byte borrowed
context, alias-lifetime assertions and bank/identity restoration contracts.

The evolution graph now contains 190 in-roster links. The 67 additions comprise
47 canonical and 20 explicitly approved temporary requirements; Delcatty's
first-stage metadata is also corrected to Skitty. This completes the reviewed
graph, not the deferred final species-data/design pass. The numeric pointer
table is relocated rather than duplicated; its eight-byte banked row copy
uses verified inactive Stats staging. See the
[architecture and dependencies](pokedex_interactive_registration_prototype.md).

| Resource | Change From Previous Production, Decimal Bytes |
| --- | ---: |
| ROMX | +5332 |
| ROM0 / allocated WRAM0 / allocated WRAMX / HRAM / SRAM | 0 each |
| Borrowed registration context | +3, now 67; no allocation growth |

## Verification

The complete pre-promotion qualification applies by exact executable identity,
not by assuming a new build behaves similarly. It includes all 373 species,
26 Unown forms, ordinary Selected controls, uninterrupted playback, tab/exit
stress, all-move battle comparisons, persistence, surrounding gameplay and
the independent Battle Tower suite. The final gates are in
`build/interactive-registration-review-20261016/qualification.json`; detailed
coverage, baseline exceptions, timings and manual-review media remain in the
[capture-fixes review](pokedex_registration_capture_fixes_review.md).

Fresh checks against the actual root production build also pass:

- 87 current host cases, ten context contracts and 36 harness controls.
- All 373 species / 190 evolution links, including linked-data consistency.
- Six native capture cases with wallet, speed-switch and return checks.
- Eight legitimate Pay Day cases, including Amulet Coin and wallet caps.
- Exact reviewed source/ROM/symbol/map identity and protected-save hashes.

Results: `build/interactive-registration-production-20261016/root-checks.json`
and `verification.json`. An initial root-check attempt correctly failed its
positive numeric-copy cost assertion because the test used newly promoted
production as its own baseline. The test now takes an explicit frozen
`--baseline`; no timing assertion was relaxed or cartridge code changed.
The first attempt is preserved under `root-checks-prepromotion-baseline/`.

The five phase-sensitive Info warnings remain accepted: approximately
33.578-33.756 ms / 2.006-2.016 additional physical display frames versus the
ordinary Selected owner in that scan. Typical Desc-to-Info and Desc-to-Mov
complete-display medians are 81.433 ms / 4.864 frames and 82.412 ms / 4.922
frames. The LCD-on handoff median is 18.846 ms / 1.126 frames, not a blackout.
One physical frame is 16.742706 ms. No new functional regression is identified.

The user supplied manual visual/responsiveness acceptance separately from
automated qualification. Physical-hardware approval is not claimed. Existing
Tower reward, native-animation and pre-Gotcha wild-cry exceptions remain
documented, not silently closed. See the
[reconciled remaining backlog](pokedex_backlog_reconciliation.md#still-outstanding).

To recheck identity and protected saves without rerunning the full campaign:

```sh
PYTHONPATH=tools:. python3 -B -m tools.dex_timing.registration_integration verify
```
