roms := \
	pokecrystal.gbc
patches := pokecrystal.patch

rom_obj := \
	audio.o \
	home.o \
	main.o \
	ram.o \
	data/text/common.o \
	data/maps/map_data.o \
	data/pokemon/dex_entries.o \
	data/pokemon/egg_moves.o \
	data/pokemon/evos_attacks.o \
	engine/movie/credits.o \
	engine/overworld/events.o \
	gfx/misc.o \
	gfx/pics.o \
	gfx/sprites.o \
	gfx/tilesets.o \
	lib/mobile/main.o \
	lib/mobile/mail.o

pokecrystal_obj    := $(rom_obj:.o=.o)
pokecrystal_vc_obj := $(rom_obj:.o=_vc.o)


### Build tools

ifeq (,$(shell command -v sha1sum 2>/dev/null))
SHA1 := shasum
else
SHA1 := sha1sum
endif

RGBDS ?=
RGBASM  ?= $(RGBDS)rgbasm
RGBFIX  ?= $(RGBDS)rgbfix
RGBGFX  ?= $(RGBDS)rgbgfx
RGBLINK ?= $(RGBDS)rgblink

RGBASMFLAGS  ?= -Weverything -Wtruncation=1
RGBLINKFLAGS ?= -Weverything -Wtruncation=1
RGBFIXFLAGS  ?= -Weverything
RGBGFXFLAGS  ?= -Weverything


### Build targets

.SUFFIXES:
.SECONDEXPANSION:
.PRECIOUS:
.SECONDARY:
.PHONY: \
	all \
	crystal \
	clean \
	tidy \
	tools

all: crystal
crystal:    pokecrystal.gbc
crystal_vc: pokecrystal.patch

clean: tidy
	find gfx \
	     \( -name "*.[12]bpp" \
	        -o -name "*.lz" \
	        -o -name "*.gbcpal" \
	        -o -name "*.sgb.tilemap" \) \
	     -delete
	find gfx/pokemon -mindepth 1 \
	     ! -path "gfx/pokemon/unown/*" \
	     \( -name "bitmask.asm" \
	        -o -name "frames.asm" \
	        -o -name "front.animated.tilemap" \
	        -o -name "front.dimensions" \) \
	     -delete

tidy:
	$(RM) $(roms) \
	      $(roms:.gbc=.sym) \
	      $(roms:.gbc=.map) \
	      $(patches) \
	      $(patches:.patch=_vc.gbc) \
	      $(patches:.patch=_vc.sym) \
	      $(patches:.patch=_vc.map) \
	      $(patches:%.patch=vc/%.constants.sym) \
	      $(pokecrystal_obj) \
	      $(pokecrystal_vc_obj) \
	      rgbdscheck.o
	$(MAKE) clean -C tools/

tools:
	$(MAKE) -C tools/


RGBASMFLAGS += -Q8 -P includes.asm
# Create a sym/map for debug purposes if `make` run with `DEBUG=1`
ifeq ($(DEBUG),1)
RGBASMFLAGS += -E
endif

$(pokecrystal_obj):         RGBASMFLAGS +=
$(pokecrystal_vc_obj):      RGBASMFLAGS += -D _CRYSTAL_VC

%.patch: %_vc.gbc %.gbc vc/%.patch.template
# Ignore the checksums added by tools/stadium at the end of the ROM
	tools/make_patch --ignore 0x1ffde0:0x220 $*_vc.sym $^ $@

rgbdscheck.o: rgbdscheck.asm
	$(RGBASM) -o $@ $<

# Build tools when building the rom.
# This has to happen before the rules are processed, since that's when scan_includes is run.
ifeq (,$(filter clean tidy tools,$(MAKECMDGOALS)))

$(info $(shell $(MAKE) -C tools))

# The dep rules have to be explicit or else missing files won't be reported.
# As a side effect, they're evaluated immediately instead of when the rule is invoked.
# It doesn't look like $(shell) can be deferred so there might not be a better way.
preinclude_deps := includes.asm $(shell tools/scan_includes includes.asm)
define DEP
$1: $2 $$(shell tools/scan_includes $2) $(preinclude_deps) | rgbdscheck.o
	$$(RGBASM) $$(RGBASMFLAGS) -o $$@ $$<
endef

# Dependencies for shared objects objects
$(foreach obj, $(pokecrystal_obj), $(eval $(call DEP,$(obj),$(obj:.o=.asm))))
$(foreach obj, $(pokecrystal_vc_obj), $(eval $(call DEP,$(obj),$(obj:_vc.o=.asm))))

endif


RGBFIXFLAGS += -Cjv -t PM_CRYSTAL -k 01 -l 0x33 -m MBC3+TIMER+RAM+BATTERY -r 3 -p 0
pokecrystal.gbc:      RGBFIXFLAGS += -i BYTE -n 0
pokecrystal11_vc.gbc: RGBFIXFLAGS += -i BYTE -n 1

%.gbc: $$(%_obj) layout.link
	$(RGBLINK) $(RGBLINKFLAGS) -l layout.link -n $*.sym -m $*.map -o $@ $(filter %.o,$^)
	$(RGBFIX) $(RGBFIXFLAGS) $@
	tools/stadium $@


### LZ compression rules

%.lz: %
	tools/lzcomp -- $< $@


### Pokemon pic animation rules

gfx/pokemon/%/front.animated.2bpp: gfx/pokemon/%/front.2bpp gfx/pokemon/%/front.dimensions
	tools/pokemon_animation_graphics -o $@ $^
gfx/pokemon/%/front.animated.tilemap: gfx/pokemon/%/front.2bpp gfx/pokemon/%/front.dimensions
	tools/pokemon_animation_graphics -t $@ $^
gfx/pokemon/%/bitmask.asm: gfx/pokemon/%/front.animated.tilemap gfx/pokemon/%/front.dimensions
	tools/pokemon_animation -b $^ > $@
gfx/pokemon/%/frames.asm: gfx/pokemon/%/front.animated.tilemap gfx/pokemon/%/front.dimensions
	tools/pokemon_animation -f $^ > $@


### Pokemon and trainer sprite rules

gfx/pokemon/%/back.2bpp: RGBGFXFLAGS += --columns
gfx/pokemon/%/back.2bpp: gfx/pokemon/%/back.png gfx/pokemon/%/normal.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:$(word 2,$^) -o $@ $<
gfx/pokemon/%/front.2bpp: gfx/pokemon/%/front.png gfx/pokemon/%/normal.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:$(word 2,$^) -o $@ $<
gfx/pokemon/%/normal.gbcpal: gfx/pokemon/%/front.gbcpal gfx/pokemon/%/back.gbcpal
	tools/gbcpal $(tools/gbcpal) $@ $^

gfx/trainers/%.2bpp: RGBGFXFLAGS += --columns
gfx/trainers/%.2bpp: gfx/trainers/%.png gfx/trainers/%.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:$(word 2,$^) -o $@ $<

# Egg does not have a back sprite, so it only uses front.gbcpal
gfx/pokemon/egg/front.2bpp: gfx/pokemon/egg/front.png gfx/pokemon/egg/front.gbcpal
gfx/pokemon/egg/front.2bpp: RGBGFXFLAGS += --colors gbc:$(word 2,$^)

# Unown letters share one normal.gbcpal
unown_pngs := $(wildcard gfx/pokemon/unown_*/front.png) $(wildcard gfx/pokemon/unown_*/back.png)
$(foreach png, $(unown_pngs),\
	$(eval $(png:.png=.2bpp): $(png) gfx/pokemon/unown/normal.gbcpal))
gfx/pokemon/unown_%/back.2bpp: RGBGFXFLAGS += --colors gbc:$(word 2,$^)
gfx/pokemon/unown_%/front.2bpp: RGBGFXFLAGS += --colors gbc:$(word 2,$^)
gfx/pokemon/unown/normal.gbcpal: $(subst .png,.gbcpal,$(unown_pngs))
	tools/gbcpal $(tools/gbcpal) $@ $^


### Misc file-specific graphics rules

gfx/pokemon/egg/unused_front.2bpp: RGBGFXFLAGS += --columns

gfx/pokemon/spearow/normal.gbcpal: tools/gbcpal += --reverse
gfx/pokemon/fearow/normal.gbcpal: tools/gbcpal += --reverse
gfx/pokemon/farfetch_d/normal.gbcpal: tools/gbcpal += --reverse
gfx/pokemon/hitmonlee/normal.gbcpal: tools/gbcpal += --reverse
gfx/pokemon/scyther/normal.gbcpal: tools/gbcpal += --reverse
gfx/pokemon/jynx/normal.gbcpal: tools/gbcpal += --reverse
gfx/pokemon/porygon/normal.gbcpal: tools/gbcpal += --reverse
gfx/pokemon/porygon2/normal.gbcpal: tools/gbcpal += --reverse

gfx/trainers/swimmer_m.gbcpal: tools/gbcpal += --reverse

gfx/new_game/shrink1.2bpp: RGBGFXFLAGS += --columns
gfx/new_game/shrink2.2bpp: RGBGFXFLAGS += --columns

gfx/mail/dragonite.1bpp: tools/gfx += --remove-whitespace
gfx/mail/large_note.1bpp: tools/gfx += --remove-whitespace
gfx/mail/surf_mail_border.1bpp: tools/gfx += --remove-whitespace
gfx/mail/flower_mail_border.1bpp: tools/gfx += --remove-whitespace
gfx/mail/litebluemail_border.1bpp: tools/gfx += --remove-whitespace

gfx/pokedex/pokedex.2bpp: tools/gfx += --trim-whitespace
gfx/pokedex/pokedex_sgb.2bpp: tools/gfx += --trim-whitespace
gfx/pokedex/question_mark.2bpp: RGBGFXFLAGS += --columns
gfx/pokedex/slowpoke.2bpp: tools/gfx += --trim-whitespace

gfx/pokegear/pokegear.2bpp: RGBGFXFLAGS += --trim-end 2
gfx/pokegear/pokegear_sprites.2bpp: tools/gfx += --trim-whitespace

gfx/mystery_gift/mystery_gift.2bpp: tools/gfx += --trim-whitespace

gfx/title/crystal.2bpp: tools/gfx += --interleave --png=$<
gfx/title/old_fg.2bpp: tools/gfx += --interleave --png=$<
gfx/title/logo.2bpp: RGBGFXFLAGS += --trim-end 4

gfx/trade/ball.2bpp: tools/gfx += --remove-whitespace
gfx/trade/game_boy.2bpp: tools/gfx += --remove-duplicates --preserve=0x23,0x27
gfx/trade/game_boy_cable.2bpp: gfx/trade/game_boy.2bpp gfx/trade/link_cable.2bpp ; cat $^ > $@

gfx/slots/slots_1.2bpp: tools/gfx += --trim-whitespace
gfx/slots/slots_2.2bpp: tools/gfx += --interleave --png=$<
gfx/slots/slots_3.2bpp: tools/gfx += --interleave --png=$< --remove-duplicates --keep-whitespace --remove-xflip

gfx/card_flip/card_flip_1.2bpp: tools/gfx += --trim-whitespace
gfx/card_flip/card_flip_2.2bpp: tools/gfx += --remove-whitespace

battle_anim_dir := gfx/battle_anims
battle_anim_2bpp = $(addprefix $(battle_anim_dir)/,$(addsuffix .2bpp,$(1)))
battle_anim_png = $(addprefix $(battle_anim_dir)/,$(addsuffix .png,$(1)))
battle_anim_chunk_pngs = $(foreach chunk,$(2),$(battle_anim_dir)/$(1)_$(chunk).png)
battle_anim_chunk_tmps = $(foreach chunk,$(1),$@.$(chunk))

$(call battle_anim_2bpp,angels bubble charge): tools/gfx += --trim-whitespace
$(call battle_anim_2bpp,egg explosion hit horn lightning noise reflect rocks skyattack status vine_whip): tools/gfx += --remove-whitespace

gfx/battle_anims/beam.2bpp: tools/gfx += --remove-xflip --remove-yflip --remove-whitespace
gfx/battle_anims/misc.2bpp: tools/gfx += --remove-duplicates --remove-xflip
gfx/battle_anims/objects.2bpp: tools/gfx += --remove-whitespace --remove-xflip
gfx/battle_anims/pokeball.2bpp: tools/gfx += --remove-xflip --keep-whitespace

transparent_gray_battle_anim_colors := '\#none,\#606060,\#909090,\#c8c8c8'
mud_ball_battle_anim_colors := '\#ffffff,\#f0f0f0,\#884828,\#683018'
thunder_battle_anim_colors := '\#none,\#c8c8c8,\#686868,\#ffffff'
ember_transparent_battle_anim_colors := '\#none,\#a0a0a0,\#606060,\#282828'
ember_opaque_battle_anim_colors := '\#ffffff,\#a0a0a0,\#606060,\#282828'
water_column_battle_anim_colors := '\#none,\#0838f8,\#08a0f8,\#60e8f8'
claw_battle_anim_colors := '\#ffffff,\#606060,\#a0a0a0,\#282828'
poison_bubble_battle_anim_colors := '\#ffffff,\#f0f0f0,\#e050e0,\#c800c8'
poison_powder_battle_anim_colors := '\#ffffff,\#8860c0,\#e050e0,\#c800c8'
shadow_ball_battle_anim_colors := '\#ffffff,\#2030c8,\#182088,\#181050'
sludge_bomb_battle_anim_colors := '\#ffffff,\#f0f0f0,\#e050e0,\#c800c8'
sharp_teeth_battle_anim_colors := '\#ffffff,\#f0f0f0,\#606060,\#000000'
hyper_fang_battle_anim_colors := '\#ffffff,\#f8f828,\#f87010,\#c81800'
bullet_seed_battle_anim_colors := '\#ffffff,\#c8b870,\#807038,\#483800'
silver_wind_battle_anim_colors := '\#ffffff,\#d0d8c8,\#b8c0a0,\#a0a878'
ice_chunk_battle_anim_colors := '\#ffffff,\#08f8f8,\#08a0f8,\#0820f8'
block_battle_anim_colors := '\#ffffff,\#000000,\#f81800,\#c00800'
force_palm_battle_anim_colors := '\#ffffff,\#c8c8c8,\#606060,\#000000'
ingrain_battle_anim_colors := '\#ffffff,\#909090,\#404040,\#000000'
taunt_bubble_battle_anim_colors := '\#ffffff,\#e8e8e8,\#a090b8,\#9078a8'
taunt_finger_battle_anim_colors := '\#ffffff,\#f8e0e0,\#f8a898,\#000000'
taunt_anger_battle_anim_colors := '\#ffffff,\#f86010,\#f83008,\#000000'
ghost_flame_battle_anim_colors := '\#ffffff,\#e030f8,\#b030f8,\#6830f8'
pink_petal_battle_anim_colors := '\#ffffff,\#f888a0,\#f87090,\#d06078'
aurora_beam_battle_anim_colors := '\#ffffff,\#20e820,\#20e8e8,\#e820e8'
signal_beam_battle_anim_colors := '\#ffffff,\#2020e8,\#e82020,\#e820e8'

define battle_anim_rgbgfx_rule
$(call battle_anim_2bpp,$(1)): $(call battle_anim_png,$(1))
	$$(RGBGFX) $$(RGBGFXFLAGS) --colors $$($(2)) -o $$@ $$<
endef

# like battle_anim_rgbgfx_rule, but strips blank tiles afterward; the consuming
# OAM data must be authored against the whitespace-removed tile layout
define battle_anim_rgbgfx_rw_rule
$(call battle_anim_2bpp,$(1)): $(call battle_anim_png,$(1))
	$$(RGBGFX) $$(RGBGFXFLAGS) --colors $$($(2)) -o $$@ $$<
	tools/gfx --remove-whitespace -o $$@ $$@
endef

$(call battle_anim_2bpp,electricity_effect thundershock thundershock_horizontal thunderbolt thunderbolt_aftereffect): %.2bpp: %.png
	$(RGBGFX) $(RGBGFXFLAGS) --colors $(transparent_gray_battle_anim_colors) -o $@ $<

$(eval $(call battle_anim_rgbgfx_rule,mud_ball_medium,mud_ball_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rw_rule,thunder,thunder_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,poison_bubble,poison_bubble_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,toxic_bubble,poison_bubble_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,shadow_ball,shadow_ball_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,sludge_bomb,sludge_bomb_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,sharp_teeth,sharp_teeth_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rw_rule,hyper_fang,hyper_fang_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,bullet_seed,bullet_seed_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,silver_wind,silver_wind_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,ice_chunk,ice_chunk_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,block,block_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,force_palm,force_palm_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,ingrain,ingrain_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,thought_bubble_1,taunt_bubble_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,thought_bubble_2,taunt_bubble_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,thought_bubble_3,taunt_bubble_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,thought_bubble_4,taunt_bubble_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,taunt_finger,taunt_finger_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,anger,taunt_anger_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,ghost_flame,ghost_flame_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,pink_petal,pink_petal_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,aurora_beam,aurora_beam_battle_anim_colors))
$(eval $(call battle_anim_rgbgfx_rule,signal_beam,signal_beam_battle_anim_colors))

$(call battle_anim_2bpp,ember): $(call battle_anim_chunk_pngs,ember,1 2 3 4 5)
	for chunk in 1 2; do \
		$(RGBGFX) $(RGBGFXFLAGS) --colors $(ember_transparent_battle_anim_colors) -o $@.$$chunk $(battle_anim_dir)/ember_$$chunk.png; \
	done
	for chunk in 3 4 5; do \
		$(RGBGFX) $(RGBGFXFLAGS) --colors $(ember_opaque_battle_anim_colors) -o $@.$$chunk $(battle_anim_dir)/ember_$$chunk.png; \
	done
	cat $(call battle_anim_chunk_tmps,1 2 3 4 5) > $@
	$(RM) $(call battle_anim_chunk_tmps,1 2 3 4 5)

$(call battle_anim_2bpp,water_column): $(call battle_anim_chunk_pngs,water_column,1 2 3 4)
	for chunk in 1 2 3 4; do \
		$(RGBGFX) $(RGBGFXFLAGS) --colors $(water_column_battle_anim_colors) -o $@.$$chunk $(battle_anim_dir)/water_column_$$chunk.png; \
	done
	cat $(call battle_anim_chunk_tmps,1 2 3 4) > $@
	$(RM) $(call battle_anim_chunk_tmps,1 2 3 4)

$(call battle_anim_2bpp,poison_powder): $(call battle_anim_chunk_pngs,poison_powder,1 2 3 4 5 6 7 8)
	for chunk in 1 2 3 4 5 6 7 8; do \
		$(RGBGFX) $(RGBGFXFLAGS) --colors $(poison_powder_battle_anim_colors) -o $@.$$chunk $(battle_anim_dir)/poison_powder_$$chunk.png; \
	done
	cat $(call battle_anim_chunk_tmps,1 2 3 4 5 6 7 8) > $@
	$(RM) $(call battle_anim_chunk_tmps,1 2 3 4 5 6 7 8)

$(call battle_anim_2bpp,claw): $(call battle_anim_chunk_pngs,claw,1 2 3 4 5)
	for chunk in 1 2 3 4 5; do \
		$(RGBGFX) $(RGBGFXFLAGS) --colors $(claw_battle_anim_colors) -o $@.$$chunk $(battle_anim_dir)/claw_$$chunk.png; \
		tools/gfx --remove-whitespace -o $@.$$chunk $@.$$chunk; \
	done
	cat $(call battle_anim_chunk_tmps,1 2 3 4 5) > $@
	$(RM) $(call battle_anim_chunk_tmps,1 2 3 4 5)

gfx/player/chris.2bpp: RGBGFXFLAGS += --columns
gfx/player/chris_back.2bpp: RGBGFXFLAGS += --columns
gfx/player/kris.2bpp: RGBGFXFLAGS += --columns
gfx/player/kris_back.2bpp: RGBGFXFLAGS += --columns

gfx/trainer_card/chris_card.2bpp: RGBGFXFLAGS += --columns
gfx/trainer_card/kris_card.2bpp: RGBGFXFLAGS += --columns
gfx/trainer_card/leaders.2bpp: tools/gfx += --trim-whitespace

gfx/overworld/chris_fish.2bpp: tools/gfx += --trim-whitespace
gfx/overworld/kris_fish.2bpp: tools/gfx += --trim-whitespace

gfx/sprites/big_onix.2bpp: tools/gfx += --remove-whitespace --remove-xflip

gfx/battle/dude.2bpp: RGBGFXFLAGS += --columns

gfx/font/unused_bold_font.1bpp: tools/gfx += --trim-whitespace

gfx/sgb/sgb_border.2bpp: tools/gfx += --trim-whitespace
gfx/sgb/sgb_border.sgb.tilemap: gfx/sgb/sgb_border.bin ; tr < $< -d '\000' > $@

gfx/mobile/ascii_font.2bpp: tools/gfx += --trim-whitespace
gfx/mobile/dialpad.2bpp: tools/gfx += --trim-whitespace
gfx/mobile/dialpad_cursor.2bpp: tools/gfx += --trim-whitespace
gfx/mobile/electro_ball.2bpp: tools/gfx += --remove-duplicates --remove-xflip --preserve=0x39
gfx/mobile/mobile_splash.2bpp: tools/gfx += --remove-duplicates --remove-xflip
gfx/mobile/card.2bpp: tools/gfx += --trim-whitespace
gfx/mobile/card_2.2bpp: tools/gfx += --trim-whitespace
gfx/mobile/card_folder.2bpp: tools/gfx += --trim-whitespace
gfx/mobile/phone_tiles.2bpp: tools/gfx += --remove-whitespace
gfx/mobile/pichu_animated.2bpp: tools/gfx += --trim-whitespace
gfx/mobile/stadium2_n64.2bpp: tools/gfx += --trim-whitespace

### Pack item icon graphics

pack_item_icon_pals := $(wildcard gfx/items/*.pal gfx/items/*/*.pal)
pack_item_icon_pngs := $(pack_item_icon_pals:.pal=.png)
pack_item_icon_gbcpals := $(pack_item_icon_pngs:.png=.gbcpal)
pack_item_icon_2bpp := $(pack_item_icon_pngs:.png=.2bpp)

gfx/items/%.gbcpal: gfx/items/%.pal
	printf 'SECTION "Pack Item Icon Palette", ROM0\nINCLUDE "%s"\n' "$<" > $@.asm
	$(RGBASM) $(RGBASMFLAGS) -o $@.o $@.asm
	$(RGBLINK) -x -o $@ $@.o
	$(RM) $@.o $@.asm

$(pack_item_icon_2bpp): %.2bpp: %.png %.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:$*.gbcpal -o $@ $<

tmhm_case_frame_2bpp := \
	gfx/items/tmhm/tmhm_frame_1.2bpp \
	gfx/items/tmhm/tmhm_frame_2.2bpp \
	gfx/items/tmhm/tmhm_frame_3.2bpp \
	gfx/items/tmhm/tmhm_frame_4.2bpp

$(tmhm_case_frame_2bpp): %.2bpp: %.png gfx/items/tmhm/tmhm_static.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:gfx/items/tmhm/tmhm_static.gbcpal -o $@ $<

### Type icon graphics

type_icon_pngs := $(wildcard gfx/types/*.png)
type_icon_pals := $(type_icon_pngs:.png=.pal)
type_icon_gbcpals := $(type_icon_pngs:.png=.gbcpal)
type_icon_2bpp := $(type_icon_pngs:.png=.2bpp)

gfx/types/%.gbcpal: gfx/types/%.pal
	printf 'SECTION "Type Icon Palette", ROM0\nINCLUDE "%s"\n' "$<" > $*.pal.asm
	$(RGBASM) $(RGBASMFLAGS) -o $*.pal.o $*.pal.asm
	$(RGBLINK) -x -o $@ $*.pal.o
	$(RM) $*.pal.o $*.pal.asm

$(type_icon_2bpp): %.2bpp: %.png %.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:$*.gbcpal -o $@ $<

gfx/types/compact/%_compact.2bpp: gfx/types/compact/%_compact.png gfx/types/%.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:gfx/types/$*.gbcpal -o $@ $<

### Move category icon graphics

move_category_icon_pngs := $(wildcard gfx/move_categories/*.png)
move_category_icon_pals := $(move_category_icon_pngs:.png=.pal)
move_category_icon_gbcpals := $(move_category_icon_pngs:.png=.gbcpal)
move_category_icon_2bpp := $(move_category_icon_pngs:.png=.2bpp)

gfx/move_categories/%.gbcpal: gfx/move_categories/%.pal
	printf 'SECTION "Move Category Icon Palette", ROM0\nINCLUDE "%s"\n' "$<" > $*.pal.asm
	$(RGBASM) $(RGBASMFLAGS) -o $*.pal.o $*.pal.asm
	$(RGBLINK) -x -o $@ $*.pal.o
	$(RM) $*.pal.o $*.pal.asm

$(move_category_icon_2bpp): %.2bpp: %.png %.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:$*.gbcpal -o $@ $<

gfx/move_categories/compact/%_compact.2bpp: gfx/move_categories/compact/%_compact.png gfx/move_categories/%.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:gfx/move_categories/$*.gbcpal -o $@ $<

### Status condition icon graphics

status_icon_names := burn fainted freeze paralysis poisoned sleep toxic
status_icon_battle_slot1_names := paralysis sleep
status_icon_battle_slot2_names := burn freeze poisoned toxic
status_icon_pngs := $(addprefix gfx/status_con/,$(addsuffix .png,$(status_icon_names)))
stats_status_icon_pngs := $(addprefix gfx/status_con/,$(addsuffix _stats_menu.png,$(status_icon_names)))
status_icon_gbcpals := $(status_icon_pngs:.png=.gbcpal)
status_icon_2bpp := $(status_icon_pngs:.png=.2bpp)
stats_status_icon_gbcpals := $(stats_status_icon_pngs:.png=.gbcpal)
stats_status_icon_2bpp := $(stats_status_icon_pngs:.png=.2bpp)
status_icon_battle_slot1_2bpp := $(addprefix gfx/status_con/,$(addsuffix _battle_slot1.2bpp,$(status_icon_battle_slot1_names)))
status_icon_battle_slot2_2bpp := $(addprefix gfx/status_con/,$(addsuffix _battle_slot2.2bpp,$(status_icon_battle_slot2_names)))

gfx/status_con/%.gbcpal: gfx/status_con/%.pal
	printf 'SECTION "Status Condition Icon Palette", ROM0\nINCLUDE "%s"\n' "$<" > $*.pal.asm
	$(RGBASM) $(RGBASMFLAGS) -o $*.pal.o $*.pal.asm
	$(RGBLINK) -x -o $@ $*.pal.o
	$(RM) $*.pal.o $*.pal.asm

$(status_icon_2bpp): %.2bpp: %.png %.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:$*.gbcpal -o $@ $<

$(stats_status_icon_2bpp): %.2bpp: %.png %.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:$*.gbcpal -o $@ $<

$(status_icon_battle_slot1_2bpp): gfx/status_con/%_battle_slot1.2bpp: gfx/status_con/%.png gfx/status_con/%_battle_slot1.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:gfx/status_con/$*_battle_slot1.gbcpal -o $@ $<

$(status_icon_battle_slot2_2bpp): gfx/status_con/%_battle_slot2.2bpp: gfx/status_con/%.png gfx/status_con/%_battle_slot2.gbcpal
	$(RGBGFX) $(RGBGFXFLAGS) --colors gbc:gfx/status_con/$*_battle_slot2.gbcpal -o $@ $<

### Catch-all graphics rules

%.2bpp: %.png
	$(RGBGFX) --colors dmg $(RGBGFXFLAGS) -o $@ $<
	$(if $(tools/gfx),\
		tools/gfx $(tools/gfx) -o $@ $@ || $$($(RM) $@ && false))

%.1bpp: %.png
	$(RGBGFX) --colors dmg $(RGBGFXFLAGS) --depth 1 -o $@ $<
	$(if $(tools/gfx),\
		tools/gfx $(tools/gfx) --depth 1 -o $@ $@ || $$($(RM) $@ && false))

%.gbcpal: %.png
	$(RGBGFX) -p $@ $<
	tools/gbcpal $(tools/gbcpal) $@ $@ || $$($(RM) $@ && false)

%.dimensions: %.png
	tools/png_dimensions $< $@


### File extensions that are never generated and should be manually created

%.inc: ;
%.pal: ;
%.bin: ;
%.blk: ;
%.rle: ;
