DEF NO_SAMPLED_CRY EQU $ff

	const_def
	const SAMPLED_CRY_TREECKO
	const SAMPLED_CRY_GROVYLE
	const SAMPLED_CRY_SCEPTILE
	const SAMPLED_CRY_TORCHIC
	const SAMPLED_CRY_COMBUSKEN
	const SAMPLED_CRY_BLAZIKEN
	const SAMPLED_CRY_MUDKIP
	const SAMPLED_CRY_MARSHTOMP
DEF NUM_SAMPLED_CRY_SLOTS EQU const_value

TryLoadSampledCryBySpeciesIndex::
; Load sampled cry metadata for a zero-based permanent Pokemon index.
; in: bc = zero-based species index
; out: carry set if hSampledCryBank/address contain a sampled cry
;      carry clear if the caller should use the synth cry path
	push bc
	push de

	ld a, b
	cp HIGH(NUM_POKEMON)
	jr c, .lookup
	jr nz, .no_sampled_cry
	ld a, c
	cp LOW(NUM_POKEMON)
	jr nc, .no_sampled_cry

.lookup
	ld hl, SampledCryIndexByPokemon
	add hl, bc
	ld a, [hl]
	cp NO_SAMPLED_CRY
	jr z, .no_sampled_cry
	cp NUM_SAMPLED_CRY_SLOTS
	jr nc, .no_sampled_cry

	ld c, a
	ld b, 0
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
	ld bc, SampledCryPointers
	add hl, bc

	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hl]
	ld d, a

	ld a, b
	cp BANK(NullSampledCry)
	jr nz, .found
	ld a, e
	cp LOW(NullSampledCry)
	jr nz, .found
	ld a, d
	cp HIGH(NullSampledCry)
	jr z, .no_sampled_cry

.found
	ld a, b
	ldh [hSampledCryBank], a
	ld a, e
	ldh [hSampledCryAddress], a
	ld a, d
	ldh [hSampledCryAddress + 1], a
	pop de
	pop bc
	scf
	ret

.no_sampled_cry
	pop de
	pop bc
	and a
	ret

SampledCryIndexByPokemon:
	table_width 1
DEF sampled_cry_mon = 1
rept NUM_POKEMON
	if sampled_cry_mon == TREECKO
		db SAMPLED_CRY_TREECKO
	elif sampled_cry_mon == GROVYLE
		db SAMPLED_CRY_GROVYLE
	elif sampled_cry_mon == SCEPTILE
		db SAMPLED_CRY_SCEPTILE
	elif sampled_cry_mon == TORCHIC
		db SAMPLED_CRY_TORCHIC
	elif sampled_cry_mon == COMBUSKEN
		db SAMPLED_CRY_COMBUSKEN
	elif sampled_cry_mon == BLAZIKEN
		db SAMPLED_CRY_BLAZIKEN
	elif sampled_cry_mon == MUDKIP
		db SAMPLED_CRY_MUDKIP
	elif sampled_cry_mon == MARSHTOMP
		db SAMPLED_CRY_MARSHTOMP
	else
		db NO_SAMPLED_CRY
	endc
DEF sampled_cry_mon += 1
endr
	assert_table_length NUM_POKEMON

SampledCryPointers:
	table_width 3
	dba TreeckoSampledCry
	dba GrovyleSampledCry
	dba SceptileSampledCry
	dba TorchicSampledCry
	dba CombuskenSampledCry
	dba BlazikenSampledCry
	dba MudkipSampledCry
	dba MarshtompSampledCry
	assert_table_length NUM_SAMPLED_CRY_SLOTS

NullSampledCry::
	dw 0


SECTION "Sampled Cry Payloads 1", ROMX

TreeckoSampledCry::
	dw (TreeckoSampledCryEnd - TreeckoSampledCryData) / 9
TreeckoSampledCryData:
	INCBIN "audio/sampled_cries/treecko.mm2"
TreeckoSampledCryEnd:
	assert (TreeckoSampledCryEnd - TreeckoSampledCryData) % 9 == 0

GrovyleSampledCry::
	dw (GrovyleSampledCryEnd - GrovyleSampledCryData) / 9
GrovyleSampledCryData:
	INCBIN "audio/sampled_cries/grovyle.mm2"
GrovyleSampledCryEnd:
	assert (GrovyleSampledCryEnd - GrovyleSampledCryData) % 9 == 0

SceptileSampledCry::
	dw (SceptileSampledCryEnd - SceptileSampledCryData) / 9
SceptileSampledCryData:
	INCBIN "audio/sampled_cries/sceptile.mm2"
SceptileSampledCryEnd:
	assert (SceptileSampledCryEnd - SceptileSampledCryData) % 9 == 0

TorchicSampledCry::
	dw (TorchicSampledCryEnd - TorchicSampledCryData) / 9
TorchicSampledCryData:
	INCBIN "audio/sampled_cries/torchic.mm2"
TorchicSampledCryEnd:
	assert (TorchicSampledCryEnd - TorchicSampledCryData) % 9 == 0

CombuskenSampledCry::
	dw (CombuskenSampledCryEnd - CombuskenSampledCryData) / 9
CombuskenSampledCryData:
	INCBIN "audio/sampled_cries/combusken.mm2"
CombuskenSampledCryEnd:
	assert (CombuskenSampledCryEnd - CombuskenSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 2", ROMX

BlazikenSampledCry::
	dw (BlazikenSampledCryEnd - BlazikenSampledCryData) / 9
BlazikenSampledCryData:
	INCBIN "audio/sampled_cries/blaziken.mm2"
BlazikenSampledCryEnd:
	assert (BlazikenSampledCryEnd - BlazikenSampledCryData) % 9 == 0

MudkipSampledCry::
	dw (MudkipSampledCryEnd - MudkipSampledCryData) / 9
MudkipSampledCryData:
	INCBIN "audio/sampled_cries/mudkip.mm2"
MudkipSampledCryEnd:
	assert (MudkipSampledCryEnd - MudkipSampledCryData) % 9 == 0

MarshtompSampledCry::
	dw (MarshtompSampledCryEnd - MarshtompSampledCryData) / 9
MarshtompSampledCryData:
	INCBIN "audio/sampled_cries/marshtomp.mm2"
MarshtompSampledCryEnd:
	assert (MarshtompSampledCryEnd - MarshtompSampledCryData) % 9 == 0
