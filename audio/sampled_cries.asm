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
	const SAMPLED_CRY_BARBOACH
	const SAMPLED_CRY_WHISCASH
	const SAMPLED_CRY_CORPHISH
	const SAMPLED_CRY_CRAWDAUNT
	const SAMPLED_CRY_LILEEP
	const SAMPLED_CRY_CRADILY
	const SAMPLED_CRY_ANORITH
	const SAMPLED_CRY_ARMALDO
	const SAMPLED_CRY_FEEBAS
	const SAMPLED_CRY_MILOTIC
	const SAMPLED_CRY_SHUPPET
	const SAMPLED_CRY_BANETTE
	const SAMPLED_CRY_DUSKULL
	const SAMPLED_CRY_DUSCLOPS
	const SAMPLED_CRY_DUSKNOIR
	const SAMPLED_CRY_ABSOL
	const SAMPLED_CRY_SNORUNT
	const SAMPLED_CRY_GLALIE
	const SAMPLED_CRY_FROSLASS
	const SAMPLED_CRY_SPHEAL
	const SAMPLED_CRY_SEALEO
	const SAMPLED_CRY_WALREIN
	const SAMPLED_CRY_BAGON
	const SAMPLED_CRY_SHELGON
	const SAMPLED_CRY_SALAMENCE
	const SAMPLED_CRY_BELDUM
	const SAMPLED_CRY_METANG
	const SAMPLED_CRY_METAGROSS
	const SAMPLED_CRY_REGIROCK
	const SAMPLED_CRY_REGICE
	const SAMPLED_CRY_REGISTEEL
	const SAMPLED_CRY_KYOGRE
	const SAMPLED_CRY_GROUDON
	const SAMPLED_CRY_RAYQUAZA
	const SAMPLED_CRY_SHINX
	const SAMPLED_CRY_LUXIO
	const SAMPLED_CRY_LUXRAY
	const SAMPLED_CRY_CRANIDOS
	const SAMPLED_CRY_RAMPARDOS
	const SAMPLED_CRY_SHIELDON
	const SAMPLED_CRY_BASTIODON
	const SAMPLED_CRY_AMBIPOM
	const SAMPLED_CRY_MISMAGIUS
	const SAMPLED_CRY_HONCHKROW
	const SAMPLED_CRY_BRONZOR
	const SAMPLED_CRY_BRONZONG
	const SAMPLED_CRY_RIOLU
	const SAMPLED_CRY_LUCARIO
	const SAMPLED_CRY_CROAGUNK
	const SAMPLED_CRY_TOXICROAK
	const SAMPLED_CRY_SNOVER
	const SAMPLED_CRY_ABOMASNOW
	const SAMPLED_CRY_WEAVILE
	const SAMPLED_CRY_MAGNEZONE
	const SAMPLED_CRY_LICKILICKY
	const SAMPLED_CRY_RHYPERIOR
	const SAMPLED_CRY_TANGROWTH
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
	elif sampled_cry_mon == BARBOACH
		db SAMPLED_CRY_BARBOACH
	elif sampled_cry_mon == WHISCASH
		db SAMPLED_CRY_WHISCASH
	elif sampled_cry_mon == CORPHISH
		db SAMPLED_CRY_CORPHISH
	elif sampled_cry_mon == CRAWDAUNT
		db SAMPLED_CRY_CRAWDAUNT
	elif sampled_cry_mon == LILEEP
		db SAMPLED_CRY_LILEEP
	elif sampled_cry_mon == CRADILY
		db SAMPLED_CRY_CRADILY
	elif sampled_cry_mon == ANORITH
		db SAMPLED_CRY_ANORITH
	elif sampled_cry_mon == ARMALDO
		db SAMPLED_CRY_ARMALDO
	elif sampled_cry_mon == FEEBAS
		db SAMPLED_CRY_FEEBAS
	elif sampled_cry_mon == MILOTIC
		db SAMPLED_CRY_MILOTIC
	elif sampled_cry_mon == SHUPPET
		db SAMPLED_CRY_SHUPPET
	elif sampled_cry_mon == BANETTE
		db SAMPLED_CRY_BANETTE
	elif sampled_cry_mon == DUSKULL
		db SAMPLED_CRY_DUSKULL
	elif sampled_cry_mon == DUSCLOPS
		db SAMPLED_CRY_DUSCLOPS
	elif sampled_cry_mon == DUSKNOIR
		db SAMPLED_CRY_DUSKNOIR
	elif sampled_cry_mon == ABSOL
		db SAMPLED_CRY_ABSOL
	elif sampled_cry_mon == SNORUNT
		db SAMPLED_CRY_SNORUNT
	elif sampled_cry_mon == GLALIE
		db SAMPLED_CRY_GLALIE
	elif sampled_cry_mon == FROSLASS
		db SAMPLED_CRY_FROSLASS
	elif sampled_cry_mon == SPHEAL
		db SAMPLED_CRY_SPHEAL
	elif sampled_cry_mon == SEALEO
		db SAMPLED_CRY_SEALEO
	elif sampled_cry_mon == WALREIN
		db SAMPLED_CRY_WALREIN
	elif sampled_cry_mon == BAGON
		db SAMPLED_CRY_BAGON
	elif sampled_cry_mon == SHELGON
		db SAMPLED_CRY_SHELGON
	elif sampled_cry_mon == SALAMENCE
		db SAMPLED_CRY_SALAMENCE
	elif sampled_cry_mon == BELDUM
		db SAMPLED_CRY_BELDUM
	elif sampled_cry_mon == METANG
		db SAMPLED_CRY_METANG
	elif sampled_cry_mon == METAGROSS
		db SAMPLED_CRY_METAGROSS
	elif sampled_cry_mon == REGIROCK
		db SAMPLED_CRY_REGIROCK
	elif sampled_cry_mon == REGICE
		db SAMPLED_CRY_REGICE
	elif sampled_cry_mon == REGISTEEL
		db SAMPLED_CRY_REGISTEEL
	elif sampled_cry_mon == KYOGRE
		db SAMPLED_CRY_KYOGRE
	elif sampled_cry_mon == GROUDON
		db SAMPLED_CRY_GROUDON
	elif sampled_cry_mon == RAYQUAZA
		db SAMPLED_CRY_RAYQUAZA
	elif sampled_cry_mon == SHINX
		db SAMPLED_CRY_SHINX
	elif sampled_cry_mon == LUXIO
		db SAMPLED_CRY_LUXIO
	elif sampled_cry_mon == LUXRAY
		db SAMPLED_CRY_LUXRAY
	elif sampled_cry_mon == CRANIDOS
		db SAMPLED_CRY_CRANIDOS
	elif sampled_cry_mon == RAMPARDOS
		db SAMPLED_CRY_RAMPARDOS
	elif sampled_cry_mon == SHIELDON
		db SAMPLED_CRY_SHIELDON
	elif sampled_cry_mon == BASTIODON
		db SAMPLED_CRY_BASTIODON
	elif sampled_cry_mon == AMBIPOM
		db SAMPLED_CRY_AMBIPOM
	elif sampled_cry_mon == MISMAGIUS
		db SAMPLED_CRY_MISMAGIUS
	elif sampled_cry_mon == HONCHKROW
		db SAMPLED_CRY_HONCHKROW
	elif sampled_cry_mon == BRONZOR
		db SAMPLED_CRY_BRONZOR
	elif sampled_cry_mon == BRONZONG
		db SAMPLED_CRY_BRONZONG
	elif sampled_cry_mon == RIOLU
		db SAMPLED_CRY_RIOLU
	elif sampled_cry_mon == LUCARIO
		db SAMPLED_CRY_LUCARIO
	elif sampled_cry_mon == CROAGUNK
		db SAMPLED_CRY_CROAGUNK
	elif sampled_cry_mon == TOXICROAK
		db SAMPLED_CRY_TOXICROAK
	elif sampled_cry_mon == SNOVER
		db SAMPLED_CRY_SNOVER
	elif sampled_cry_mon == ABOMASNOW
		db SAMPLED_CRY_ABOMASNOW
	elif sampled_cry_mon == WEAVILE
		db SAMPLED_CRY_WEAVILE
	elif sampled_cry_mon == MAGNEZONE
		db SAMPLED_CRY_MAGNEZONE
	elif sampled_cry_mon == LICKILICKY
		db SAMPLED_CRY_LICKILICKY
	elif sampled_cry_mon == RHYPERIOR
		db SAMPLED_CRY_RHYPERIOR
	elif sampled_cry_mon == TANGROWTH
		db SAMPLED_CRY_TANGROWTH
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
	dba BarboachSampledCry
	dba WhiscashSampledCry
	dba CorphishSampledCry
	dba CrawdauntSampledCry
	dba LileepSampledCry
	dba CradilySampledCry
	dba AnorithSampledCry
	dba ArmaldoSampledCry
	dba FeebasSampledCry
	dba MiloticSampledCry
	dba ShuppetSampledCry
	dba BanetteSampledCry
	dba DuskullSampledCry
	dba DusclopsSampledCry
	dba DusknoirSampledCry
	dba AbsolSampledCry
	dba SnoruntSampledCry
	dba GlalieSampledCry
	dba FroslassSampledCry
	dba SphealSampledCry
	dba SealeoSampledCry
	dba WalreinSampledCry
	dba BagonSampledCry
	dba ShelgonSampledCry
	dba SalamenceSampledCry
	dba BeldumSampledCry
	dba MetangSampledCry
	dba MetagrossSampledCry
	dba RegirockSampledCry
	dba RegiceSampledCry
	dba RegisteelSampledCry
	dba KyogreSampledCry
	dba GroudonSampledCry
	dba RayquazaSampledCry
	dba ShinxSampledCry
	dba LuxioSampledCry
	dba LuxraySampledCry
	dba CranidosSampledCry
	dba RampardosSampledCry
	dba ShieldonSampledCry
	dba BastiodonSampledCry
	dba AmbipomSampledCry
	dba MismagiusSampledCry
	dba HonchkrowSampledCry
	dba BronzorSampledCry
	dba BronzongSampledCry
	dba RioluSampledCry
	dba LucarioSampledCry
	dba CroagunkSampledCry
	dba ToxicroakSampledCry
	dba SnoverSampledCry
	dba AbomasnowSampledCry
	dba WeavileSampledCry
	dba MagnezoneSampledCry
	dba LickilickySampledCry
	dba RhyperiorSampledCry
	dba TangrowthSampledCry
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

BarboachSampledCry::
	dw (BarboachSampledCryEnd - BarboachSampledCryData) / 9
BarboachSampledCryData:
	INCBIN "audio/sampled_cries/barboach.mm2"
BarboachSampledCryEnd:
	assert (BarboachSampledCryEnd - BarboachSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 7", ROMX

WhiscashSampledCry::
	dw (WhiscashSampledCryEnd - WhiscashSampledCryData) / 9
WhiscashSampledCryData:
	INCBIN "audio/sampled_cries/whiscash.mm2"
WhiscashSampledCryEnd:
	assert (WhiscashSampledCryEnd - WhiscashSampledCryData) % 9 == 0

CorphishSampledCry::
	dw (CorphishSampledCryEnd - CorphishSampledCryData) / 9
CorphishSampledCryData:
	INCBIN "audio/sampled_cries/corphish.mm2"
CorphishSampledCryEnd:
	assert (CorphishSampledCryEnd - CorphishSampledCryData) % 9 == 0

CrawdauntSampledCry::
	dw (CrawdauntSampledCryEnd - CrawdauntSampledCryData) / 9
CrawdauntSampledCryData:
	INCBIN "audio/sampled_cries/crawdaunt.mm2"
CrawdauntSampledCryEnd:
	assert (CrawdauntSampledCryEnd - CrawdauntSampledCryData) % 9 == 0

LileepSampledCry::
	dw (LileepSampledCryEnd - LileepSampledCryData) / 9
LileepSampledCryData:
	INCBIN "audio/sampled_cries/lileep.mm2"
LileepSampledCryEnd:
	assert (LileepSampledCryEnd - LileepSampledCryData) % 9 == 0

CradilySampledCry::
	dw (CradilySampledCryEnd - CradilySampledCryData) / 9
CradilySampledCryData:
	INCBIN "audio/sampled_cries/cradily.mm2"
CradilySampledCryEnd:
	assert (CradilySampledCryEnd - CradilySampledCryData) % 9 == 0

AnorithSampledCry::
	dw (AnorithSampledCryEnd - AnorithSampledCryData) / 9
AnorithSampledCryData:
	INCBIN "audio/sampled_cries/anorith.mm2"
AnorithSampledCryEnd:
	assert (AnorithSampledCryEnd - AnorithSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 8", ROMX

ArmaldoSampledCry::
	dw (ArmaldoSampledCryEnd - ArmaldoSampledCryData) / 9
ArmaldoSampledCryData:
	INCBIN "audio/sampled_cries/armaldo.mm2"
ArmaldoSampledCryEnd:
	assert (ArmaldoSampledCryEnd - ArmaldoSampledCryData) % 9 == 0

FeebasSampledCry::
	dw (FeebasSampledCryEnd - FeebasSampledCryData) / 9
FeebasSampledCryData:
	INCBIN "audio/sampled_cries/feebas.mm2"
FeebasSampledCryEnd:
	assert (FeebasSampledCryEnd - FeebasSampledCryData) % 9 == 0

MiloticSampledCry::
	dw (MiloticSampledCryEnd - MiloticSampledCryData) / 9
MiloticSampledCryData:
	INCBIN "audio/sampled_cries/milotic.mm2"
MiloticSampledCryEnd:
	assert (MiloticSampledCryEnd - MiloticSampledCryData) % 9 == 0

ShuppetSampledCry::
	dw (ShuppetSampledCryEnd - ShuppetSampledCryData) / 9
ShuppetSampledCryData:
	INCBIN "audio/sampled_cries/shuppet.mm2"
ShuppetSampledCryEnd:
	assert (ShuppetSampledCryEnd - ShuppetSampledCryData) % 9 == 0

BanetteSampledCry::
	dw (BanetteSampledCryEnd - BanetteSampledCryData) / 9
BanetteSampledCryData:
	INCBIN "audio/sampled_cries/banette.mm2"
BanetteSampledCryEnd:
	assert (BanetteSampledCryEnd - BanetteSampledCryData) % 9 == 0

DuskullSampledCry::
	dw (DuskullSampledCryEnd - DuskullSampledCryData) / 9
DuskullSampledCryData:
	INCBIN "audio/sampled_cries/duskull.mm2"
DuskullSampledCryEnd:
	assert (DuskullSampledCryEnd - DuskullSampledCryData) % 9 == 0

DusclopsSampledCry::
	dw (DusclopsSampledCryEnd - DusclopsSampledCryData) / 9
DusclopsSampledCryData:
	INCBIN "audio/sampled_cries/dusclops.mm2"
DusclopsSampledCryEnd:
	assert (DusclopsSampledCryEnd - DusclopsSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 9", ROMX

DusknoirSampledCry::
	dw (DusknoirSampledCryEnd - DusknoirSampledCryData) / 9
DusknoirSampledCryData:
	INCBIN "audio/sampled_cries/dusknoir.mm2"
DusknoirSampledCryEnd:
	assert (DusknoirSampledCryEnd - DusknoirSampledCryData) % 9 == 0

AbsolSampledCry::
	dw (AbsolSampledCryEnd - AbsolSampledCryData) / 9
AbsolSampledCryData:
	INCBIN "audio/sampled_cries/absol.mm2"
AbsolSampledCryEnd:
	assert (AbsolSampledCryEnd - AbsolSampledCryData) % 9 == 0

SnoruntSampledCry::
	dw (SnoruntSampledCryEnd - SnoruntSampledCryData) / 9
SnoruntSampledCryData:
	INCBIN "audio/sampled_cries/snorunt.mm2"
SnoruntSampledCryEnd:
	assert (SnoruntSampledCryEnd - SnoruntSampledCryData) % 9 == 0

GlalieSampledCry::
	dw (GlalieSampledCryEnd - GlalieSampledCryData) / 9
GlalieSampledCryData:
	INCBIN "audio/sampled_cries/glalie.mm2"
GlalieSampledCryEnd:
	assert (GlalieSampledCryEnd - GlalieSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 10", ROMX

FroslassSampledCry::
	dw (FroslassSampledCryEnd - FroslassSampledCryData) / 9
FroslassSampledCryData:
	INCBIN "audio/sampled_cries/froslass.mm2"
FroslassSampledCryEnd:
	assert (FroslassSampledCryEnd - FroslassSampledCryData) % 9 == 0

SphealSampledCry::
	dw (SphealSampledCryEnd - SphealSampledCryData) / 9
SphealSampledCryData:
	INCBIN "audio/sampled_cries/spheal.mm2"
SphealSampledCryEnd:
	assert (SphealSampledCryEnd - SphealSampledCryData) % 9 == 0

SealeoSampledCry::
	dw (SealeoSampledCryEnd - SealeoSampledCryData) / 9
SealeoSampledCryData:
	INCBIN "audio/sampled_cries/sealeo.mm2"
SealeoSampledCryEnd:
	assert (SealeoSampledCryEnd - SealeoSampledCryData) % 9 == 0

WalreinSampledCry::
	dw (WalreinSampledCryEnd - WalreinSampledCryData) / 9
WalreinSampledCryData:
	INCBIN "audio/sampled_cries/walrein.mm2"
WalreinSampledCryEnd:
	assert (WalreinSampledCryEnd - WalreinSampledCryData) % 9 == 0

BagonSampledCry::
	dw (BagonSampledCryEnd - BagonSampledCryData) / 9
BagonSampledCryData:
	INCBIN "audio/sampled_cries/bagon.mm2"
BagonSampledCryEnd:
	assert (BagonSampledCryEnd - BagonSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 11", ROMX

ShelgonSampledCry::
	dw (ShelgonSampledCryEnd - ShelgonSampledCryData) / 9
ShelgonSampledCryData:
	INCBIN "audio/sampled_cries/shelgon.mm2"
ShelgonSampledCryEnd:
	assert (ShelgonSampledCryEnd - ShelgonSampledCryData) % 9 == 0

SalamenceSampledCry::
	dw (SalamenceSampledCryEnd - SalamenceSampledCryData) / 9
SalamenceSampledCryData:
	INCBIN "audio/sampled_cries/salamence.mm2"
SalamenceSampledCryEnd:
	assert (SalamenceSampledCryEnd - SalamenceSampledCryData) % 9 == 0

BeldumSampledCry::
	dw (BeldumSampledCryEnd - BeldumSampledCryData) / 9
BeldumSampledCryData:
	INCBIN "audio/sampled_cries/beldum.mm2"
BeldumSampledCryEnd:
	assert (BeldumSampledCryEnd - BeldumSampledCryData) % 9 == 0

MetangSampledCry::
	dw (MetangSampledCryEnd - MetangSampledCryData) / 9
MetangSampledCryData:
	INCBIN "audio/sampled_cries/metang.mm2"
MetangSampledCryEnd:
	assert (MetangSampledCryEnd - MetangSampledCryData) % 9 == 0

MetagrossSampledCry::
	dw (MetagrossSampledCryEnd - MetagrossSampledCryData) / 9
MetagrossSampledCryData:
	INCBIN "audio/sampled_cries/metagross.mm2"
MetagrossSampledCryEnd:
	assert (MetagrossSampledCryEnd - MetagrossSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 12", ROMX

RegirockSampledCry::
	dw (RegirockSampledCryEnd - RegirockSampledCryData) / 9
RegirockSampledCryData:
	INCBIN "audio/sampled_cries/regirock.mm2"
RegirockSampledCryEnd:
	assert (RegirockSampledCryEnd - RegirockSampledCryData) % 9 == 0

RegiceSampledCry::
	dw (RegiceSampledCryEnd - RegiceSampledCryData) / 9
RegiceSampledCryData:
	INCBIN "audio/sampled_cries/regice.mm2"
RegiceSampledCryEnd:
	assert (RegiceSampledCryEnd - RegiceSampledCryData) % 9 == 0

RegisteelSampledCry::
	dw (RegisteelSampledCryEnd - RegisteelSampledCryData) / 9
RegisteelSampledCryData:
	INCBIN "audio/sampled_cries/registeel.mm2"
RegisteelSampledCryEnd:
	assert (RegisteelSampledCryEnd - RegisteelSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 13", ROMX

KyogreSampledCry::
	dw (KyogreSampledCryEnd - KyogreSampledCryData) / 9
KyogreSampledCryData:
	INCBIN "audio/sampled_cries/kyogre.mm2"
KyogreSampledCryEnd:
	assert (KyogreSampledCryEnd - KyogreSampledCryData) % 9 == 0

GroudonSampledCry::
	dw (GroudonSampledCryEnd - GroudonSampledCryData) / 9
GroudonSampledCryData:
	INCBIN "audio/sampled_cries/groudon.mm2"
GroudonSampledCryEnd:
	assert (GroudonSampledCryEnd - GroudonSampledCryData) % 9 == 0

RayquazaSampledCry::
	dw (RayquazaSampledCryEnd - RayquazaSampledCryData) / 9
RayquazaSampledCryData:
	INCBIN "audio/sampled_cries/rayquaza.mm2"
RayquazaSampledCryEnd:
	assert (RayquazaSampledCryEnd - RayquazaSampledCryData) % 9 == 0

ShinxSampledCry::
	dw (ShinxSampledCryEnd - ShinxSampledCryData) / 9
ShinxSampledCryData:
	INCBIN "audio/sampled_cries/shinx.mm2"
ShinxSampledCryEnd:
	assert (ShinxSampledCryEnd - ShinxSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 14", ROMX

LuxioSampledCry::
	dw (LuxioSampledCryEnd - LuxioSampledCryData) / 9
LuxioSampledCryData:
	INCBIN "audio/sampled_cries/luxio.mm2"
LuxioSampledCryEnd:
	assert (LuxioSampledCryEnd - LuxioSampledCryData) % 9 == 0

LuxraySampledCry::
	dw (LuxraySampledCryEnd - LuxraySampledCryData) / 9
LuxraySampledCryData:
	INCBIN "audio/sampled_cries/luxray.mm2"
LuxraySampledCryEnd:
	assert (LuxraySampledCryEnd - LuxraySampledCryData) % 9 == 0

CranidosSampledCry::
	dw (CranidosSampledCryEnd - CranidosSampledCryData) / 9
CranidosSampledCryData:
	INCBIN "audio/sampled_cries/cranidos.mm2"
CranidosSampledCryEnd:
	assert (CranidosSampledCryEnd - CranidosSampledCryData) % 9 == 0

RampardosSampledCry::
	dw (RampardosSampledCryEnd - RampardosSampledCryData) / 9
RampardosSampledCryData:
	INCBIN "audio/sampled_cries/rampardos.mm2"
RampardosSampledCryEnd:
	assert (RampardosSampledCryEnd - RampardosSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 15", ROMX

ShieldonSampledCry::
	dw (ShieldonSampledCryEnd - ShieldonSampledCryData) / 9
ShieldonSampledCryData:
	INCBIN "audio/sampled_cries/shieldon.mm2"
ShieldonSampledCryEnd:
	assert (ShieldonSampledCryEnd - ShieldonSampledCryData) % 9 == 0

BastiodonSampledCry::
	dw (BastiodonSampledCryEnd - BastiodonSampledCryData) / 9
BastiodonSampledCryData:
	INCBIN "audio/sampled_cries/bastiodon.mm2"
BastiodonSampledCryEnd:
	assert (BastiodonSampledCryEnd - BastiodonSampledCryData) % 9 == 0

AmbipomSampledCry::
	dw (AmbipomSampledCryEnd - AmbipomSampledCryData) / 9
AmbipomSampledCryData:
	INCBIN "audio/sampled_cries/ambipom.mm2"
AmbipomSampledCryEnd:
	assert (AmbipomSampledCryEnd - AmbipomSampledCryData) % 9 == 0

MismagiusSampledCry::
	dw (MismagiusSampledCryEnd - MismagiusSampledCryData) / 9
MismagiusSampledCryData:
	INCBIN "audio/sampled_cries/mismagius.mm2"
MismagiusSampledCryEnd:
	assert (MismagiusSampledCryEnd - MismagiusSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 16", ROMX

HonchkrowSampledCry::
	dw (HonchkrowSampledCryEnd - HonchkrowSampledCryData) / 9
HonchkrowSampledCryData:
	INCBIN "audio/sampled_cries/honchkrow.mm2"
HonchkrowSampledCryEnd:
	assert (HonchkrowSampledCryEnd - HonchkrowSampledCryData) % 9 == 0

BronzorSampledCry::
	dw (BronzorSampledCryEnd - BronzorSampledCryData) / 9
BronzorSampledCryData:
	INCBIN "audio/sampled_cries/bronzor.mm2"
BronzorSampledCryEnd:
	assert (BronzorSampledCryEnd - BronzorSampledCryData) % 9 == 0

BronzongSampledCry::
	dw (BronzongSampledCryEnd - BronzongSampledCryData) / 9
BronzongSampledCryData:
	INCBIN "audio/sampled_cries/bronzong.mm2"
BronzongSampledCryEnd:
	assert (BronzongSampledCryEnd - BronzongSampledCryData) % 9 == 0

RioluSampledCry::
	dw (RioluSampledCryEnd - RioluSampledCryData) / 9
RioluSampledCryData:
	INCBIN "audio/sampled_cries/riolu.mm2"
RioluSampledCryEnd:
	assert (RioluSampledCryEnd - RioluSampledCryData) % 9 == 0

LucarioSampledCry::
	dw (LucarioSampledCryEnd - LucarioSampledCryData) / 9
LucarioSampledCryData:
	INCBIN "audio/sampled_cries/lucario.mm2"
LucarioSampledCryEnd:
	assert (LucarioSampledCryEnd - LucarioSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 17", ROMX

CroagunkSampledCry::
	dw (CroagunkSampledCryEnd - CroagunkSampledCryData) / 9
CroagunkSampledCryData:
	INCBIN "audio/sampled_cries/croagunk.mm2"
CroagunkSampledCryEnd:
	assert (CroagunkSampledCryEnd - CroagunkSampledCryData) % 9 == 0

ToxicroakSampledCry::
	dw (ToxicroakSampledCryEnd - ToxicroakSampledCryData) / 9
ToxicroakSampledCryData:
	INCBIN "audio/sampled_cries/toxicroak.mm2"
ToxicroakSampledCryEnd:
	assert (ToxicroakSampledCryEnd - ToxicroakSampledCryData) % 9 == 0

SnoverSampledCry::
	dw (SnoverSampledCryEnd - SnoverSampledCryData) / 9
SnoverSampledCryData:
	INCBIN "audio/sampled_cries/snover.mm2"
SnoverSampledCryEnd:
	assert (SnoverSampledCryEnd - SnoverSampledCryData) % 9 == 0

AbomasnowSampledCry::
	dw (AbomasnowSampledCryEnd - AbomasnowSampledCryData) / 9
AbomasnowSampledCryData:
	INCBIN "audio/sampled_cries/abomasnow.mm2"
AbomasnowSampledCryEnd:
	assert (AbomasnowSampledCryEnd - AbomasnowSampledCryData) % 9 == 0

WeavileSampledCry::
	dw (WeavileSampledCryEnd - WeavileSampledCryData) / 9
WeavileSampledCryData:
	INCBIN "audio/sampled_cries/weavile.mm2"
WeavileSampledCryEnd:
	assert (WeavileSampledCryEnd - WeavileSampledCryData) % 9 == 0


SECTION "Sampled Cry Payloads 18", ROMX

MagnezoneSampledCry::
	dw (MagnezoneSampledCryEnd - MagnezoneSampledCryData) / 9
MagnezoneSampledCryData:
	INCBIN "audio/sampled_cries/magnezone.mm2"
MagnezoneSampledCryEnd:
	assert (MagnezoneSampledCryEnd - MagnezoneSampledCryData) % 9 == 0

LickilickySampledCry::
	dw (LickilickySampledCryEnd - LickilickySampledCryData) / 9
LickilickySampledCryData:
	INCBIN "audio/sampled_cries/lickilicky.mm2"
LickilickySampledCryEnd:
	assert (LickilickySampledCryEnd - LickilickySampledCryData) % 9 == 0

RhyperiorSampledCry::
	dw (RhyperiorSampledCryEnd - RhyperiorSampledCryData) / 9
RhyperiorSampledCryData:
	INCBIN "audio/sampled_cries/rhyperior.mm2"
RhyperiorSampledCryEnd:
	assert (RhyperiorSampledCryEnd - RhyperiorSampledCryData) % 9 == 0

TangrowthSampledCry::
	dw (TangrowthSampledCryEnd - TangrowthSampledCryData) / 9
TangrowthSampledCryData:
	INCBIN "audio/sampled_cries/tangrowth.mm2"
TangrowthSampledCryEnd:
	assert (TangrowthSampledCryEnd - TangrowthSampledCryData) % 9 == 0
