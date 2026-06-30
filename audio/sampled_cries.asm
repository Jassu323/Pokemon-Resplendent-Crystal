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
	const SAMPLED_CRY_SWAMPERT
	const SAMPLED_CRY_POOCHYENA
	const SAMPLED_CRY_MIGHTYENA
	const SAMPLED_CRY_WINGULL
	const SAMPLED_CRY_PELIPPER
	const SAMPLED_CRY_RALTS
	const SAMPLED_CRY_KIRLIA
	const SAMPLED_CRY_GARDEVOIR
	const SAMPLED_CRY_GALLADE
	const SAMPLED_CRY_SHROOMISH
	const SAMPLED_CRY_BRELOOM
	const SAMPLED_CRY_MAKUHITA
	const SAMPLED_CRY_HARIYAMA
	const SAMPLED_CRY_MAWILE
	const SAMPLED_CRY_ARON
	const SAMPLED_CRY_LAIRON
	const SAMPLED_CRY_AGGRON
	const SAMPLED_CRY_MEDITITE
	const SAMPLED_CRY_MEDICHAM
	const SAMPLED_CRY_CARVANHA
	const SAMPLED_CRY_SHARPEDO
	const SAMPLED_CRY_NUMEL
	const SAMPLED_CRY_CAMERUPT
	const SAMPLED_CRY_TORKOAL
	const SAMPLED_CRY_TRAPINCH
	const SAMPLED_CRY_VIBRAVA
	const SAMPLED_CRY_FLYGON
	const SAMPLED_CRY_SWABLU
	const SAMPLED_CRY_ALTARIA
	const SAMPLED_CRY_ZANGOOSE
	const SAMPLED_CRY_SEVIPER
	const SAMPLED_CRY_LUNATONE
	const SAMPLED_CRY_SOLROCK
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
	elif sampled_cry_mon == SWAMPERT
		db SAMPLED_CRY_SWAMPERT
	elif sampled_cry_mon == POOCHYENA
		db SAMPLED_CRY_POOCHYENA
	elif sampled_cry_mon == MIGHTYENA
		db SAMPLED_CRY_MIGHTYENA
	elif sampled_cry_mon == WINGULL
		db SAMPLED_CRY_WINGULL
	elif sampled_cry_mon == PELIPPER
		db SAMPLED_CRY_PELIPPER
	elif sampled_cry_mon == RALTS
		db SAMPLED_CRY_RALTS
	elif sampled_cry_mon == KIRLIA
		db SAMPLED_CRY_KIRLIA
	elif sampled_cry_mon == GARDEVOIR
		db SAMPLED_CRY_GARDEVOIR
	elif sampled_cry_mon == GALLADE
		db SAMPLED_CRY_GALLADE
	elif sampled_cry_mon == SHROOMISH
		db SAMPLED_CRY_SHROOMISH
	elif sampled_cry_mon == BRELOOM
		db SAMPLED_CRY_BRELOOM
	elif sampled_cry_mon == MAKUHITA
		db SAMPLED_CRY_MAKUHITA
	elif sampled_cry_mon == HARIYAMA
		db SAMPLED_CRY_HARIYAMA
	elif sampled_cry_mon == MAWILE
		db SAMPLED_CRY_MAWILE
	elif sampled_cry_mon == ARON
		db SAMPLED_CRY_ARON
	elif sampled_cry_mon == LAIRON
		db SAMPLED_CRY_LAIRON
	elif sampled_cry_mon == AGGRON
		db SAMPLED_CRY_AGGRON
	elif sampled_cry_mon == MEDITITE
		db SAMPLED_CRY_MEDITITE
	elif sampled_cry_mon == MEDICHAM
		db SAMPLED_CRY_MEDICHAM
	elif sampled_cry_mon == CARVANHA
		db SAMPLED_CRY_CARVANHA
	elif sampled_cry_mon == SHARPEDO
		db SAMPLED_CRY_SHARPEDO
	elif sampled_cry_mon == NUMEL
		db SAMPLED_CRY_NUMEL
	elif sampled_cry_mon == CAMERUPT
		db SAMPLED_CRY_CAMERUPT
	elif sampled_cry_mon == TORKOAL
		db SAMPLED_CRY_TORKOAL
	elif sampled_cry_mon == TRAPINCH
		db SAMPLED_CRY_TRAPINCH
	elif sampled_cry_mon == VIBRAVA
		db SAMPLED_CRY_VIBRAVA
	elif sampled_cry_mon == FLYGON
		db SAMPLED_CRY_FLYGON
	elif sampled_cry_mon == SWABLU
		db SAMPLED_CRY_SWABLU
	elif sampled_cry_mon == ALTARIA
		db SAMPLED_CRY_ALTARIA
	elif sampled_cry_mon == ZANGOOSE
		db SAMPLED_CRY_ZANGOOSE
	elif sampled_cry_mon == SEVIPER
		db SAMPLED_CRY_SEVIPER
	elif sampled_cry_mon == LUNATONE
		db SAMPLED_CRY_LUNATONE
	elif sampled_cry_mon == SOLROCK
		db SAMPLED_CRY_SOLROCK
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
	dba SwampertSampledCry
	dba PoochyenaSampledCry
	dba MightyenaSampledCry
	dba WingullSampledCry
	dba PelipperSampledCry
	dba RaltsSampledCry
	dba KirliaSampledCry
	dba GardevoirSampledCry
	dba GalladeSampledCry
	dba ShroomishSampledCry
	dba BreloomSampledCry
	dba MakuhitaSampledCry
	dba HariyamaSampledCry
	dba MawileSampledCry
	dba AronSampledCry
	dba LaironSampledCry
	dba AggronSampledCry
	dba MedititeSampledCry
	dba MedichamSampledCry
	dba CarvanhaSampledCry
	dba SharpedoSampledCry
	dba NumelSampledCry
	dba CameruptSampledCry
	dba TorkoalSampledCry
	dba TrapinchSampledCry
	dba VibravaSampledCry
	dba FlygonSampledCry
	dba SwabluSampledCry
	dba AltariaSampledCry
	dba ZangooseSampledCry
	dba SeviperSampledCry
	dba LunatoneSampledCry
	dba SolrockSampledCry
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

SwampertSampledCry::
	dw (SwampertSampledCryEnd - SwampertSampledCryData) / 9
SwampertSampledCryData:
	INCBIN "audio/sampled_cries/swampert.mm2"
SwampertSampledCryEnd:
	assert (SwampertSampledCryEnd - SwampertSampledCryData) % 9 == 0

PoochyenaSampledCry::
	dw (PoochyenaSampledCryEnd - PoochyenaSampledCryData) / 9
PoochyenaSampledCryData:
	INCBIN "audio/sampled_cries/poochyena.mm2"
PoochyenaSampledCryEnd:
	assert (PoochyenaSampledCryEnd - PoochyenaSampledCryData) % 9 == 0

MightyenaSampledCry::
	dw (MightyenaSampledCryEnd - MightyenaSampledCryData) / 9
MightyenaSampledCryData:
	INCBIN "audio/sampled_cries/mightyena.mm2"
MightyenaSampledCryEnd:
	assert (MightyenaSampledCryEnd - MightyenaSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 3", ROMX

WingullSampledCry::
	dw (WingullSampledCryEnd - WingullSampledCryData) / 9
WingullSampledCryData:
	INCBIN "audio/sampled_cries/wingull.mm2"
WingullSampledCryEnd:
	assert (WingullSampledCryEnd - WingullSampledCryData) % 9 == 0

PelipperSampledCry::
	dw (PelipperSampledCryEnd - PelipperSampledCryData) / 9
PelipperSampledCryData:
	INCBIN "audio/sampled_cries/pelipper.mm2"
PelipperSampledCryEnd:
	assert (PelipperSampledCryEnd - PelipperSampledCryData) % 9 == 0

RaltsSampledCry::
	dw (RaltsSampledCryEnd - RaltsSampledCryData) / 9
RaltsSampledCryData:
	INCBIN "audio/sampled_cries/ralts.mm2"
RaltsSampledCryEnd:
	assert (RaltsSampledCryEnd - RaltsSampledCryData) % 9 == 0

KirliaSampledCry::
	dw (KirliaSampledCryEnd - KirliaSampledCryData) / 9
KirliaSampledCryData:
	INCBIN "audio/sampled_cries/kirlia.mm2"
KirliaSampledCryEnd:
	assert (KirliaSampledCryEnd - KirliaSampledCryData) % 9 == 0

GardevoirSampledCry::
	dw (GardevoirSampledCryEnd - GardevoirSampledCryData) / 9
GardevoirSampledCryData:
	INCBIN "audio/sampled_cries/gardevoir.mm2"
GardevoirSampledCryEnd:
	assert (GardevoirSampledCryEnd - GardevoirSampledCryData) % 9 == 0

GalladeSampledCry::
	dw (GalladeSampledCryEnd - GalladeSampledCryData) / 9
GalladeSampledCryData:
	INCBIN "audio/sampled_cries/gallade.mm2"
GalladeSampledCryEnd:
	assert (GalladeSampledCryEnd - GalladeSampledCryData) % 9 == 0

ShroomishSampledCry::
	dw (ShroomishSampledCryEnd - ShroomishSampledCryData) / 9
ShroomishSampledCryData:
	INCBIN "audio/sampled_cries/shroomish.mm2"
ShroomishSampledCryEnd:
	assert (ShroomishSampledCryEnd - ShroomishSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 4", ROMX

BreloomSampledCry::
	dw (BreloomSampledCryEnd - BreloomSampledCryData) / 9
BreloomSampledCryData:
	INCBIN "audio/sampled_cries/breloom.mm2"
BreloomSampledCryEnd:
	assert (BreloomSampledCryEnd - BreloomSampledCryData) % 9 == 0

MakuhitaSampledCry::
	dw (MakuhitaSampledCryEnd - MakuhitaSampledCryData) / 9
MakuhitaSampledCryData:
	INCBIN "audio/sampled_cries/makuhita.mm2"
MakuhitaSampledCryEnd:
	assert (MakuhitaSampledCryEnd - MakuhitaSampledCryData) % 9 == 0

HariyamaSampledCry::
	dw (HariyamaSampledCryEnd - HariyamaSampledCryData) / 9
HariyamaSampledCryData:
	INCBIN "audio/sampled_cries/hariyama.mm2"
HariyamaSampledCryEnd:
	assert (HariyamaSampledCryEnd - HariyamaSampledCryData) % 9 == 0

MawileSampledCry::
	dw (MawileSampledCryEnd - MawileSampledCryData) / 9
MawileSampledCryData:
	INCBIN "audio/sampled_cries/mawile.mm2"
MawileSampledCryEnd:
	assert (MawileSampledCryEnd - MawileSampledCryData) % 9 == 0

AronSampledCry::
	dw (AronSampledCryEnd - AronSampledCryData) / 9
AronSampledCryData:
	INCBIN "audio/sampled_cries/aron.mm2"
AronSampledCryEnd:
	assert (AronSampledCryEnd - AronSampledCryData) % 9 == 0

LaironSampledCry::
	dw (LaironSampledCryEnd - LaironSampledCryData) / 9
LaironSampledCryData:
	INCBIN "audio/sampled_cries/lairon.mm2"
LaironSampledCryEnd:
	assert (LaironSampledCryEnd - LaironSampledCryData) % 9 == 0

AggronSampledCry::
	dw (AggronSampledCryEnd - AggronSampledCryData) / 9
AggronSampledCryData:
	INCBIN "audio/sampled_cries/aggron.mm2"
AggronSampledCryEnd:
	assert (AggronSampledCryEnd - AggronSampledCryData) % 9 == 0

MedititeSampledCry::
	dw (MedititeSampledCryEnd - MedititeSampledCryData) / 9
MedititeSampledCryData:
	INCBIN "audio/sampled_cries/meditite.mm2"
MedititeSampledCryEnd:
	assert (MedititeSampledCryEnd - MedititeSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 5", ROMX

MedichamSampledCry::
	dw (MedichamSampledCryEnd - MedichamSampledCryData) / 9
MedichamSampledCryData:
	INCBIN "audio/sampled_cries/medicham.mm2"
MedichamSampledCryEnd:
	assert (MedichamSampledCryEnd - MedichamSampledCryData) % 9 == 0

CarvanhaSampledCry::
	dw (CarvanhaSampledCryEnd - CarvanhaSampledCryData) / 9
CarvanhaSampledCryData:
	INCBIN "audio/sampled_cries/carvanha.mm2"
CarvanhaSampledCryEnd:
	assert (CarvanhaSampledCryEnd - CarvanhaSampledCryData) % 9 == 0

SharpedoSampledCry::
	dw (SharpedoSampledCryEnd - SharpedoSampledCryData) / 9
SharpedoSampledCryData:
	INCBIN "audio/sampled_cries/sharpedo.mm2"
SharpedoSampledCryEnd:
	assert (SharpedoSampledCryEnd - SharpedoSampledCryData) % 9 == 0

NumelSampledCry::
	dw (NumelSampledCryEnd - NumelSampledCryData) / 9
NumelSampledCryData:
	INCBIN "audio/sampled_cries/numel.mm2"
NumelSampledCryEnd:
	assert (NumelSampledCryEnd - NumelSampledCryData) % 9 == 0

CameruptSampledCry::
	dw (CameruptSampledCryEnd - CameruptSampledCryData) / 9
CameruptSampledCryData:
	INCBIN "audio/sampled_cries/camerupt.mm2"
CameruptSampledCryEnd:
	assert (CameruptSampledCryEnd - CameruptSampledCryData) % 9 == 0

TorkoalSampledCry::
	dw (TorkoalSampledCryEnd - TorkoalSampledCryData) / 9
TorkoalSampledCryData:
	INCBIN "audio/sampled_cries/torkoal.mm2"
TorkoalSampledCryEnd:
	assert (TorkoalSampledCryEnd - TorkoalSampledCryData) % 9 == 0

TrapinchSampledCry::
	dw (TrapinchSampledCryEnd - TrapinchSampledCryData) / 9
TrapinchSampledCryData:
	INCBIN "audio/sampled_cries/trapinch.mm2"
TrapinchSampledCryEnd:
	assert (TrapinchSampledCryEnd - TrapinchSampledCryData) % 9 == 0

VibravaSampledCry::
	dw (VibravaSampledCryEnd - VibravaSampledCryData) / 9
VibravaSampledCryData:
	INCBIN "audio/sampled_cries/vibrava.mm2"
VibravaSampledCryEnd:
	assert (VibravaSampledCryEnd - VibravaSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 6", ROMX

FlygonSampledCry::
	dw (FlygonSampledCryEnd - FlygonSampledCryData) / 9
FlygonSampledCryData:
	INCBIN "audio/sampled_cries/flygon.mm2"
FlygonSampledCryEnd:
	assert (FlygonSampledCryEnd - FlygonSampledCryData) % 9 == 0

SwabluSampledCry::
	dw (SwabluSampledCryEnd - SwabluSampledCryData) / 9
SwabluSampledCryData:
	INCBIN "audio/sampled_cries/swablu.mm2"
SwabluSampledCryEnd:
	assert (SwabluSampledCryEnd - SwabluSampledCryData) % 9 == 0

AltariaSampledCry::
	dw (AltariaSampledCryEnd - AltariaSampledCryData) / 9
AltariaSampledCryData:
	INCBIN "audio/sampled_cries/altaria.mm2"
AltariaSampledCryEnd:
	assert (AltariaSampledCryEnd - AltariaSampledCryData) % 9 == 0

ZangooseSampledCry::
	dw (ZangooseSampledCryEnd - ZangooseSampledCryData) / 9
ZangooseSampledCryData:
	INCBIN "audio/sampled_cries/zangoose.mm2"
ZangooseSampledCryEnd:
	assert (ZangooseSampledCryEnd - ZangooseSampledCryData) % 9 == 0

SeviperSampledCry::
	dw (SeviperSampledCryEnd - SeviperSampledCryData) / 9
SeviperSampledCryData:
	INCBIN "audio/sampled_cries/seviper.mm2"
SeviperSampledCryEnd:
	assert (SeviperSampledCryEnd - SeviperSampledCryData) % 9 == 0

LunatoneSampledCry::
	dw (LunatoneSampledCryEnd - LunatoneSampledCryData) / 9
LunatoneSampledCryData:
	INCBIN "audio/sampled_cries/lunatone.mm2"
LunatoneSampledCryEnd:
	assert (LunatoneSampledCryEnd - LunatoneSampledCryData) % 9 == 0

SolrockSampledCry::
	dw (SolrockSampledCryEnd - SolrockSampledCryData) / 9
SolrockSampledCryData:
	INCBIN "audio/sampled_cries/solrock.mm2"
SolrockSampledCryEnd:
	assert (SolrockSampledCryEnd - SolrockSampledCryData) % 9 == 0
