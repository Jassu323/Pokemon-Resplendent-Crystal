# New Dex Entry Description Layout Scope

Scoped 2026-10-13 against production commit `81ff02a25`. Both requested options
are feasible. The user subsequently selected visual-only option A; its private
implementation and measured results are in [the prototype report](pokedex_new_entry_visual_prototype.md).
Option B remains scoped only. Production ROM and the player battery remain unchanged.

The cleanup findings and exact builds were archived first in
[Deferred Dex Cleanup Archive](archived/dex-unused-scope-20261013/README.md).
Both archived source/patch packages were restored and rebuilt; each produced
its original ROM byte-for-byte. Cleanup remains deferred until registration
is finalized.

## Options

| Dimension | A Visual Only | B Desc Info Mov End |
| --- | --- | --- |
| Description content | Same panels, borders, page badge, text, colored frontpic, footprint and type badges as Selected Description | Same, with the interactive footer |
| Controls | Current two-page A/B flow retained | Left/right footer selection; A activates; B or A on End leaves |
| Info and Moves | Not available | Reuse existing species Info and Moves pages |
| Species selection | Captured species only | Captured species only; no up/down species paging |
| Portrait architecture | Keep current resident New Entry owner | Must choose a static handoff or Selected streaming owner |
| New graphics or semantic tables | None expected | None expected; End uses the existing font |
| Complexity | Low/moderate | Moderate with static portrait handoff; moderate/high for uninterrupted portrait animation |
| Principal risk | Text/badge publication and post-catch restoration | The same risks plus RAM/VRAM ownership and normal-speed lower-panel servicing |

### Planning Costs

These are the original **engineering planning envelopes, not linked measurements**.
Option A's subsequent measured cost is 227 ROMX bytes, with no added RAM; see
the prototype report above. B has not been implemented. Estimates exclude
unrelated cleanup and do not duplicate the existing
Info/Moves/ancestor tables or glyph atlases.

| Resource | A Visual Only | B Static Handoff | B Continuous Animation |
| --- | --- | --- | --- |
| Additional ROMX budget, net of replacing the old registration shell | Approximately 300-800 bytes | Approximately 1,000-2,500 bytes | Approximately 2,000-5,000 bytes |
| Added allocated WRAMX target | 0 bytes | 0-64 bytes for context/owner bookkeeping | 0-64 bytes for context/owner bookkeeping |
| Added allocated WRAM0 target | 0 bytes | 0 bytes | 0 bytes |
| Added ROM0 / HRAM target | 0 / 0 bytes | 0 / 0 bytes | 0 / 0 bytes |
| Persistent SRAM or save migration | None | None | None |
| Implementation effort before full qualification | Small | Several times A | Larger owner integration and timing audit |

The WRAMX allowance is a conservative contingency, not a request to allocate
it immediately. Prefer existing verified-dead owner scratch, stack-held small
context and existing temporary SRAM staging. Do not allocate a full battle
scratch backup or another page buffer merely because it simplifies integration.
The actual source/alias audit must decide which state can safely be reused.

The source banks containing the existing registration, Description and Info
code have available space, but final placement must be checked after linking.
No new ROM bank is inherently required for either option.

## Shared Visual Work

The reference is the actual current Selected Description owner, not a new
approximation of its mockup. Reuse `PokedexDescriptionTilemap`,
`PokedexDescriptionGFX` and `PokedexDescriptionRightEdge` in
`engine/pokedex/pokedex_description.asm`.

At native 160 by 144 pixels and the existing five-pixel horizontal offset,
the portrait outline is x=1..60, y=5..66; the data outline is x=62..158,
y=5..66; the lower outline is x=1..158, y=69..130. The extra right-edge column
is necessary because the horizontal offset exposes five pixels beyond the
ordinary 20-column backing map. It must have the Description join/divider
tiles and palette-0 attributes through every reveal and text-page change.

Name, number, category, height, weight and text positions already largely
match. The substantive differences are the shell/divider/page badge, footprint
background, compact type badges and footer handling. Keep the existing
species data and authored descriptions; this does not change National IDs,
evolutions, learnsets or wording.

`Pokedex_LoadGFX` already calls `Pokedex_LoadPermanentCGBGFX`, which loads the
Description border/page graphics and permanent badge/Info assets. A must not
add another copy of their ROM data or eagerly reload them just to change the
registration tilemap. The shared shell data comprises a 360-byte backing map,
18-byte edge column and 160-byte border/badge graphics, all already linked.

Use a registration-specific palette/setup adapter. Do not call Selected's
full entry procedure or fake its species-list context simply to satisfy a
layout check. Its entry/exit/controller assumes a Listing, saved viewport,
species navigation, Area and Start-menu return ownership that registration
does not have.

## A Visual Only

Keep `NewPokedexEntry` in `engine/pokedex/new_pokedex_entry.asm` as the lifecycle
and `new_dex_entry_animation.asm` as the resident animation owner. Preserve:

- A or B advances page 1 to page 2; A or B then returns from registration.
- The initial authored main/hold/idle animation and cry begin once.
- Description paging does not restart or interrupt portrait/cry playback.
- Final exit cancels the page-owned sampled cry and restores the original
  catch/naming context and normal-speed clock policy.

Replace `_NewPokedexEntry`'s old background/edge setup with the common
Description shell and explicit registration attributes/palettes. Reuse the
entry printer through the Description divider/page-badge repair instead of
leaving its old divider on screen. Initialize the description-page state
explicitly, rather than relying on a previous Dex session's value.

### Type Badges And Footprint

The compact type OBJ destinations are already safe with the resident loader.
Use the same tile graphics, palette colors and screen positions as Selected:
one 32 by 8 badge at x=67, y=56 and an optional second at x=107, y=56. Monotypes
must clear the second four-sprite slot. Eight sprites on the badge scanline
remain below the ten-sprite limit.

However, `PokedexInfo_LoadTypeSprites` is not safe to call unchanged from
battle registration: its staging buffer is `wPokedexWRAM0Scratch`, which
aliases battle graphics state. Reuse its compact-type copy/remap primitive,
but stage registration's small upload in its existing temporary upload
workspace rather than overwriting live battle state. Select and restore the
SRAM/WRAM/VRAM banks explicitly, and publish the initial OAM before the
resident animation owner locks ordinary OAM updates.

Keep registration's existing four footprint tiles in VRAM bank 0. Apply the
same white/dark-gray footprint palette as Selected while leaving their bank
attribute at zero. This is pixel-equivalent without moving the footprint to
Selected's conflicting bank-1 address. It also keeps the current animation
dictionary capacity available for future species.

### Description Page Two

Keep the existing disjoint, immutable text transaction. The current New Entry
publisher copies 90 text cells plus one old page-number cell. The modern page
badge has two changing cells, at backing coordinates (2,8) and (2,9), so page 2
must commit **92 cells**, not merely replace the old lower digit.

That additional cell requires remeasuring the New Entry-only publication
routine's live-LY admission margin. The present 91-cell normal-speed contract
has 296 T-cycles of store margin; adding a literal load/store pair would consume
32 T-cycles, but the complete linked path must confirm its actual cost. Do not
relax the cutoff or add any check to ordinary VBlank/STAT dispatch.
The frame-map ACK barrier, text READY discipline and final-owner retention
must remain intact.

### Footer

For A, retain the registration continuation indicator in the same footer
geometry. The content panels should match Selected exactly; showing inactive
Info/Mov/Area commands would imply navigation that A does not implement.
This footer content is the intentional visual difference, not a new layout.

### Runtime Expectation

No new per-frame graphics composition, extra dictionary loading or cry startup
is needed. The shell is already resident. Badge staging adds a small one-time
copy/upload to entry, and the page-2 publisher adds one cell. These are expected
to be small costs, but no millisecond or display-frame delta is claimed without
a prototype. Measure setup-to-first-complete-reveal and input-to-complete-page
separately; keeping the same animation timeline does not prove unchanged entry
latency.

## B Desc Info Mov End

Give registration its own fixed-species controller and return path. Reuse
lower-panel renderers, not `PokedexSelectedMon_Update` or
`PokedexSelectedMon_Leave` wholesale.

Proposed behavior:

- Open on Description P.1 with Desc selected.
- Left/right moves the shared blinking footer arrow between Desc, Info, Mov,
  End. Up/down does not change species.
- A on Desc from another tab returns to Description P.1; subsequent A presses
  on Desc toggle P.1/P.2. Description does not automatically exit on A.
- A on Info opens Stats, then cycles the existing Evolutions and Evolves From
  pages in their current order and wraps. A on Mov opens/cycles the existing
  species learnset pages.
- A on End, or B from any tab, cancels pending work and returns to the original
  capture sequence. Area is not available.

Mov means the Selected screen's species learnsets, not the newly captured
Pokemon's four current moves and not the standalone searchable Moves Dex.
Viewing those records must not mark the entire learnset as seen.

The capture code in `engine/items/item_effects.asm` sets Seen/Caught before
opening registration, but party/box insertion and nickname handling happen
after it returns. The interactive screen must remain read-only and preserve
the enemy/captured-mon records required by those later operations. Do not
treat viewing Info as completion of acquisition or move-discovery hooks.

### Why The Resident Owner Cannot Simply Keep Running

The read-only audit covered all **399 linked species/form animation assets**.
Maximum dictionary size is 247 tiles, with a maximum 198-tile tail. Existing
bank-1 overlap counts are:

| Region | Assets with a resident-dictionary overlap |
| --- | ---: |
| Description type OBJ sets | 0 |
| Info mini and HP endpoint OBJ regions | 0 |
| Selected normal footprint | 4 |
| Selected alternate footprint | 22 |
| Info glyph atlas A | 399 |
| Info glyph atlas B | 399 |

The four normal-footprint conflicts are Bastiodon, Dusknoir, Groudon and
Spheal. The atlas conflicts are structural, not an exceptional big species:
one atlas includes base-frame cells and the other is entirely inside the
resident base. Preparing an invisible Info page can already corrupt the
animation. Ancestor-title preparation also writes bank-1 glyph cells, so it
must not be eagerly run against an active resident dictionary.

These are physical VRAM collisions; extra ROM tables, CPU speed or an extra
VBlank wait cannot fix them.

### B Static Handoff

Keep A's resident animation on the initial Description page. Before entering
Info/Mov, acknowledge/cancel or finish that animation, atomically restore its
bank-0 static base, then relinquish the resident dictionary and give the normal
lower renderer its bank-1 workspace. Delay graphics-writing Info preparation
until that handoff is complete.

The portrait would remain static after the first tab handoff, including when
returning to Desc; it would not replay its cry. Audio still needs foreground
service until completion or final exit. Waiting for an authored animation to
finish would delay the requested tab; canceling immediately changes that
animation's behavior. Either policy needs explicit acceptance before building
this variant.

Reuse current lower-panel formatting, page data, bounded upload and atomic
publication helpers under a registration-local adapter. Ensure a New Entry
owner cannot be silently converted into a different owner by existing Info
request/cleanup code. Normal-speed work must keep audio runway and service
limits intact. Avoid copying the whole Selected service controller merely to
obtain lower-panel updates.

This is the smaller interactive implementation, but it is not full animation
parity with Selected. It avoids new frame streaming while making the lifecycle
handoff and static-base restoration explicit.

### B Continuous Animation

Use the existing Selected streaming frontpic producer for this registration
profile instead of keeping the full New Entry dictionary resident. Its two
frame slots, footprint/type buffers and lower glyph atlases are already designed
to coexist. Reuse the accepted precomputed renderer and metadata; do not add
new per-species tables or redo glyph architecture.

This is the better fit if opening Info/Mov must leave the frontpic and cry
running like Selected. It requires adapting the entry/reveal lifecycle to the
captured species, seeding stable species metadata, initializing the correct
owner fields, and validating the Selected producer plus lower-panel work at
the post-catch **normal CPU speed**. Do not switch the whole catch/naming path
to double speed just to make this integration easier.

The fixed-species controller must not require a fabricated list order or
viewport. Existing getters/footer handlers with those assumptions need narrow
shared primitives or registration-specific wrappers. B/End must not restore a
Listing, update its last position, enter Area or execute Start-menu fades.

Keep ordinary VBlank/STAT instruction budgets unchanged. Reuse existing
owner dispatch/publication interfaces rather than adding a new generic-owner
test. Any necessary changes to owner-local publication still require physical
timing verification from both battle sides and all existing Dex paths.

This path has greater integration/testing cost, but preserves the strongest
behavioral parity with Selected and avoids a new special-purpose lower renderer.
Potential retirement of the old registration animation code is a later audit,
not an assumed ROM0/ROMX refund in these planning estimates.

## RAM And Return Ownership

`wPokedexWRAM0Scratch` is a 1,300-byte overlay of overworld map blocks and the
battle menu/frontpic staging region. Its first 32 bytes include battle graphics
flags, saved palettes and producer metadata; the next 784 bytes are the staged
frontpic. Registration occurs inside battle, so the Start-menu assumption that
these bytes are disposable does not apply automatically.

A should avoid that overlap. B must preserve the still-live prefix/context and
prove whether the producer payload is already dead or must be reconstructed.
Do not restore an active flag referring to overwritten payload. Prefer keeping
small verified context in existing temporary owner storage and reconstructing
only genuinely disposable graphics over adding a 1,300-byte RAM backup.

The lower renderer's WRAMX bank-3 workspace overlays Battle Tower state.
Ordinary successful wild captures do not run inside an active Battle Tower
session, but that lifetime assumption must remain an explicit contract. New
Entry's bank-2 animation workspace and conversion/contest/discovery regions
also have separate owners; do not treat the whole bank as free scratch.

Preserve the captured stable species index and transient ID lock, current
party species/level, enemy moves/PP/DVs and the caller's menu/viewport/bank
state. Save/restore rather than persistently change the ordinary Dex's view,
selection or remembrance settings. Cancel queued lower jobs before return,
release any sprite locks, clear the type/mini OAM and restore fonts/palettes,
volume, clock and the original catch continuation exactly once.

Neither option requires save-format changes, additional seen flags or a
migration. The battle scratch issue is a runtime lifetime contract, not a
persistent storage requirement.

## Files And Cleanup Dependencies

| File | Expected responsibility |
| --- | --- |
| `engine/pokedex/new_pokedex_entry.asm` | Registration input/lifecycle and catch return; B adds its own fixed-species footer loop |
| `engine/pokedex/pokedex.asm` | Replace `_NewPokedexEntry` setup and retire its old shell only when the new path is complete |
| `engine/pokedex/pokedex_description.asm` | Reuse common shell/edge; narrow footer or explicit palette adapter if needed |
| `engine/pokedex/new_dex_entry_animation.asm` | A's two-cell modern page badge and bounded publication; B's chosen owner handoff |
| `engine/gfx/new_dex_entry_pics.asm` | Preserve resident loader for A/static B; continuous B uses the Selected preparation path |
| `engine/pokedex/pokedex_info.asm`, `pokedex_moves.asm`, `pokedex_ancestors.asm` | B lower-panel services and their existing metadata, without list/Area assumptions |
| `engine/pokedex/pokedex_detail.asm`, animation/policy/publication modules | B shares narrow primitives; no wholesale Selected entry/leave reuse |
| `engine/gfx/cgb_layouts.asm` | Explicit registration palette/attribute setup where reuse needs an adapter |
| `ram/wram.asm`, `ram/sram.asm` | Ownership/alias guards and only necessary context storage |
| Current New Entry/Dex tests and `docs/full_regression_suite.md` | Independent pixel, input, audio, timing and restoration expectations |

The old 126-byte `Pokedex_DrawDexEntryScreenBG` becomes unneeded once
registration uses the shared shell. Current production has not received the
archived cleanup, so 126 is the gross old shell span here. The archived
1,661-byte cleanup already includes three bytes of its unused Number string
and its 30-byte overwritten footer; do not count those 33 bytes twice when
rebasing cleanup after this feature.

`DisplayDexEntry` remains shared by Selected Description and can also remain
the common header/content producer for A/B. Its 224 bytes are not automatically
freed. A deliberately keeps the existing bank-0 footprint loader, so the old
19-byte footprint entry points are not newly dead simply because the screen
looks modern. The old right-edge routine also retains non-CGB callers unless
those compatibility paths are explicitly adapted.

Update the cleanup inventory after implementing the selected option. Do not
apply either archived pruning patch blindly to the resulting production.

## Qualification Before Promotion

No New Entry layout candidate exists yet. This scope ran the read-only linked
asset/VRAM audit and the current baseline's 20 New Entry contract tests, all
passing. Those checks do not qualify a future A/B implementation.

For either option, compare complete native displayed pixels with Selected
Description, including right-edge exposure, monotype clearing, both type
palettes, footprint background, category/name dimensions, P.1/P.2 and every
border join. Use independently captured reference expectations, not an oracle
generated by the proposed registration builder itself.

Re-run all-species/form resident or streaming frame mapping, all-species New
Entry normal-input/phase sweeps, authored animation timing and sampled/synth
cry checks. Include the existing short-hold Mewtwo and ACK-race Dusknoir controls,
and Bastiodon/Groudon/Spheal footprint collisions. Test before/after the final
animation event and while text or a lower page is queued.

B additionally needs every Info/evolution/ancestor and Moves category/page for
the fixed captured species, rapid repeated requests, all tab return pairs,
both portrait policies as applicable, and B/End from each pending/committed
state. Verify that no keypress navigates to another species and no lower
renderer marks moves seen or changes saved Dex preferences.

Use authentic captures with party space and full-party PC delivery, nickname
yes/no, already-caught/no-Dex bypass, contest and special supported catches.
Check captured species, level, moves/PP/DVs, caught data and acquisition hooks
after delivery. Continue through battle exit and normal overworld input/audio.

Run the complete [Full Regression Suite](full_regression_suite.md), including
all other Dex modes, all move animations from both sides, cries, persistence,
custom menus, PC/daycare and normal saving/loading. Recreate matching native
checkpoints after each link. Report timings in both milliseconds and display
frames for first complete registration reveal, description paging, B tab
changes and End/B return to naming/catch continuation. No generic ISR overhead
or outside-registration timing changes should be accepted without investigation.

## Recommendation

A is the lowest-cost foundation and keeps the already qualified resident
animation flow. If the interactive footer is preferred, choose its portrait
policy explicitly: static handoff is smaller but changes animation behavior;
continuous animation should use the existing streaming Selected architecture
and receive the broader normal-speed ownership qualification. Neither needs
new artwork or duplicate Info/Moves/ancestor metadata.
