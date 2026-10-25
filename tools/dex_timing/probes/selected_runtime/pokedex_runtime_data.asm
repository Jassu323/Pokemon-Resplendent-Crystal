PokedexRuntime_EvolutionPointer:
; Stable 16-bit species index in HL, native source bank in A on return.
	ld b, h
	ld c, l
	ld hl, EvosAttacksPointers
	ld a, BANK(EvosAttacksPointers)
	jp LoadDoubleIndirectPointer

PokedexRuntime_PrepareData:
; Initial species preparation precedes portrait/cry playback.
IF DEF(DEX_RUNTIME_SEMANTIC)
	xor a
	ld [wPokedexRuntimeReturnRepair], a
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
IF DEF(DEX_RUNTIME_ANCESTORS)
	add hl, hl
ENDC
	ld de, PokedexInfoSemanticSpecies
	add hl, de
	ld a, [hl]
	ld [wPokedexRuntimeEvoCount], a
	ret
ELSE
	xor a
	ld [wPokedexRuntimeEvoCount], a
	ld [wPokedexRuntimeReturnRepair], a
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	push hl
	call PokedexRuntime_EvolutionPointer
	ld b, a
.skip
	ld a, b
	call GetFarByte
	inc hl
	and a
	jr z, .level
	cp EVOLVE_STAT
	ld de, 3
	jr nz, .advance
	inc de
.advance
	add hl, de
	jr .skip
.level
	ld a, b
	ld [wPokedexRuntimeLevelBank], a
	ld a, l
	ld [wPokedexRuntimeLevelSource], a
	ld a, h
	ld [wPokedexRuntimeLevelSource + 1], a
	pop hl
	call PokedexRuntime_WalkEvolutions
	jp PokedexRuntime_PrepareMoves

PokedexRuntime_WalkEvolutions:
	call PokedexRuntime_EvolutionPointer
	ld b, a
.edge
	ld a, b
	call GetFarByte
	inc hl
	and a
	ret z
	ld c, a
	ld a, b
	call GetFarByte
	inc hl
	ld d, a
	ld e, 0
	ld a, c
	cp EVOLVE_STAT
	jr nz, .target
	ld a, b
	call GetFarByte
	inc hl
	ld e, a
.target
	push hl
	push bc
	ld a, b
	call GetFarWord
	call .append
	call PokedexRuntime_WalkEvolutions
	pop bc
	pop hl
	inc hl
	inc hl
	jr .edge
.append
	ld a, l
	ld [wPokedexRuntimeTarget], a
	ld a, h
	ld [wPokedexRuntimeTarget + 1], a
	push bc
	push de
	push hl
	ld a, [wPokedexRuntimeEvoCount]
	cp 36
	jr nc, .overflow
	ld e, a
	ld d, 0
	ld h, d
	ld l, e
	add hl, hl
	add hl, hl
	add hl, de
	ld de, wPokedexRuntimeEvoRecords
	add hl, de
	ld a, BANK(wPokedexRuntimeEvoRecords)
	ldh [rSVBK], a
	pop de
	ld [hl], e
	inc hl
	ld [hl], d
	inc hl
	pop de
	pop bc
	ld [hl], c
	inc hl
	ld [hl], d
	inc hl
	ld [hl], e
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld hl, wPokedexRuntimeEvoCount
	inc [hl]
	ld a, [wPokedexRuntimeTarget]
	ld l, a
	ld a, [wPokedexRuntimeTarget + 1]
	ld h, a
	ret
.overflow
	; Invalid/cyclic source data is rejected by the host graph validator.
	pop hl
	pop de
	pop bc
	ret
ENDC

PokedexRuntime_NameText:
	ld a, [wPokedexRuntimeTarget]
	ld l, a
	ld a, [wPokedexRuntimeTarget + 1]
	ld h, a
	dec hl
	ld d, h
	ld e, l
	add hl, hl
	add hl, hl
	add hl, de
	add hl, hl
	ld de, PokemonNames
	add hl, de
	ld de, wPokedexRuntimeTextBuffer
	ld bc, MON_NAME_LENGTH - 1
	ld a, BANK(PokemonNames)
	call FarCopyBytes
	ld a, "@"
	ld [de], a
	jp PokedexRuntime_StartText

PokedexRuntime_RequirementText:
	ld a, [wPokedexInfoEvolutionRecord]
	ld l, a
	ld a, [wPokedexInfoEvolutionRecord + 1]
	ld h, a
IF DEF(DEX_RUNTIME_SEMANTIC)
	ld a, BANK(PokedexInfoSemanticSpecies)
	call GetFarByte
ELSE
	ld a, BANK(wPokedexRuntimeEvoRecords)
	call GetFarWRAMByte
ENDC
	inc hl
	ld b, a
IF DEF(DEX_RUNTIME_SEMANTIC)
	ld a, BANK(PokedexInfoSemanticSpecies)
	call GetFarByte
ELSE
	ld a, BANK(wPokedexRuntimeEvoRecords)
	call GetFarWRAMByte
ENDC
	inc hl
	ld c, a
IF DEF(DEX_RUNTIME_SEMANTIC)
	ld a, BANK(PokedexInfoSemanticSpecies)
	call GetFarByte
ELSE
	ld a, BANK(wPokedexRuntimeEvoRecords)
	call GetFarWRAMByte
ENDC
	ld [wPokedexRuntimeStatCompare], a
	ld de, wPokedexRuntimeTextBuffer
	ld a, b
	cp EVOLVE_LEVEL
	jr z, .level
	cp EVOLVE_HAPPINESS
	jr z, .friendship
	cp EVOLVE_STAT
	jr z, .stat
	cp EVOLVE_TRADE
	jr nz, .item
	push bc
	ld hl, .Trade
	call .append_string
	pop bc
	ld a, c
	cp $ff
	jr z, .done
	ld a, " "
	ld [de], a
	inc de
.item
	ld a, c
	dec a
	ld [wPokedexRuntimeItemRemaining], a
	ld a, LOW(ItemNames)
	ld [wPokedexRuntimeItemSource], a
	ld a, HIGH(ItemNames)
	ld [wPokedexRuntimeItemSource + 1], a
	ld a, e
	ld [wPokedexRuntimeTextAppend], a
	ld a, d
	ld [wPokedexRuntimeTextAppend + 1], a
	ld a, 1
	ld [wPokedexRuntimeTextState], a
	ret
.friendship
	ld hl, .Friendship
	call .append_string
	jr .done
.level
	push bc
	ld hl, .Level
	call .append_string
	pop bc
	ld a, c
	call PokedexRuntime_AppendDecimal
	jr .done
.stat
	ld a, '<LV>'
	ld [de], a
	inc de
	ld a, c
	call PokedexRuntime_AppendDecimal
	ld hl, .Atk
	call .append_string
	ld a, [wPokedexRuntimeStatCompare]
	add $1b
	ld [de], a
	inc de
	ld hl, .Def
	call .append_string
.done
	ld a, "@"
	ld [de], a
	jp PokedexRuntime_StartText
.append_string
	ld a, [hli]
	cp "@"
	ret z
	ld [de], a
	inc de
	jr .append_string
.Level db "Level @"
.Trade db "Trade@"
.Friendship db "friendship@"
.Atk db " Atk @"
.Def db " Def@"

PokedexRuntime_AppendDecimal:
	push af
	xor a
	ld [wPokedexRuntimePhase], a
	pop af
	ld b, "0" - 1
.hundreds
	inc b
	sub 100
	jr nc, .hundreds
	add 100
	ld c, a
	ld a, b
	cp "0"
	jr z, .tens
	ld [de], a
	inc de
	ld a, 1
	ld [wPokedexRuntimePhase], a
.tens
	ld a, c
	ld b, "0" - 1
.divide
	inc b
	sub 10
	jr nc, .divide
	add 10
	add "0"
	ld c, a
	ld a, b
	cp "0"
	jr nz, .tens_digit
	ld a, [wPokedexRuntimePhase]
	and a
	jr z, .ones
	ld a, b
.tens_digit
	ld [de], a
	inc de
.ones
	ld a, c
	ld [de], a
	inc de
	ret

PokedexRuntime_ItemTextStep:
; One ROM switch for a bounded native-string chunk, not one per byte.
	farcall PokedexRuntime_ItemTextChunk
	ld a, [wPokedexRuntimeTextState]
	cp 4
	ret nz
	jp PokedexRuntime_StartText

IF !DEF(DEX_RUNTIME_SEMANTIC)
PokedexRuntime_BuildParents:
; Session-time native graph index, not a ROM display/family table.
	ld a, BANK(wPokedexRuntimeParents)
	ldh [rSVBK], a
	ld hl, wPokedexRuntimeParents
	ld bc, NUM_POKEMON * 2
	xor a
	call ByteFill
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld a, 1
	ld [wPokedexRuntimeTarget], a
	xor a
	ld [wPokedexRuntimeTarget + 1], a
.species
	ld a, [wPokedexRuntimeTarget]
	ld l, a
	ld a, [wPokedexRuntimeTarget + 1]
	ld h, a
	call PokedexRuntime_EvolutionPointer
	ld b, a
.edge
	ld a, b
	call GetFarByte
	inc hl
	and a
	jr z, .next_species
	ld de, 1
	cp EVOLVE_STAT
	jr nz, .target
	inc de
.target
	add hl, de
	push hl
	push bc
	ld a, b
	call GetFarWord
	dec hl
	add hl, hl
	ld de, wPokedexRuntimeParents
	add hl, de
	ld a, [wPokedexRuntimeTarget]
	ld e, a
	ld a, [wPokedexRuntimeTarget + 1]
	ld d, a
	ld a, BANK(wPokedexRuntimeParents)
	ldh [rSVBK], a
	ld [hl], e
	inc hl
	ld [hl], d
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	pop bc
	pop hl
	inc hl
	inc hl
	jr .edge
.next_species
	ld a, [wPokedexRuntimeTarget]
	ld l, a
	ld a, [wPokedexRuntimeTarget + 1]
	ld h, a
	inc hl
	ld a, l
	ld [wPokedexRuntimeTarget], a
	ld a, h
	ld [wPokedexRuntimeTarget + 1], a
	cp HIGH(NUM_POKEMON + 1)
	jr c, .species
	ret nz
	ld a, l
	cp LOW(NUM_POKEMON + 1)
	jr c, .species
	ret
PokedexRuntime_FamilyRoot:
.parent
	push hl
	dec hl
	add hl, hl
	ld de, wPokedexRuntimeParents
	add hl, de
	ld a, BANK(wPokedexRuntimeParents)
	call GetFarWRAMByte
	ld e, a
	inc hl
	ld a, BANK(wPokedexRuntimeParents)
	call GetFarWRAMByte
	ld d, a
	or e
	pop hl
	ret z
	ld h, d
	ld l, e
	jr .parent

PokedexRuntime_PrepareMoves:
; Cache native stream counts/pointers before the incoming portrait starts.
	ld hl, wPokedexRuntimeTextBuffer
	ld bc, 16
	xor a
	call ByteFill
	ld a, [wPokedexRuntimeLevelBank]
	ld [wPokedexRuntimeTextBuffer + 1], a
	ld b, a
	ld a, [wPokedexRuntimeLevelSource]
	ld [wPokedexRuntimeTextBuffer + 2], a
	ld l, a
	ld a, [wPokedexRuntimeLevelSource + 1]
	ld [wPokedexRuntimeTextBuffer + 3], a
	ld h, a
	ld e, 0
.level
	ld a, b
	call GetFarByte
	and a
	jr z, .level_count
	inc e
	ld a, l
	add 3
	ld l, a
	jr nc, .level
	inc h
	jr .level
.level_count
	ld a, e
	ld [wPokedexRuntimeTextBuffer], a
	ld a, BANK(wPokedexRuntimeTMs)
	ld [wPokedexRuntimeTextBuffer + 5], a
	ld [wPokedexRuntimeTextBuffer + 9], a
	ld a, LOW(wPokedexRuntimeTMs)
	ld [wPokedexRuntimeTextBuffer + 6], a
	ld a, HIGH(wPokedexRuntimeTMs)
	ld [wPokedexRuntimeTextBuffer + 7], a
	ld a, LOW(wPokedexRuntimeTutors)
	ld [wPokedexRuntimeTextBuffer + 10], a
	ld a, HIGH(wPokedexRuntimeTutors)
	ld [wPokedexRuntimeTextBuffer + 11], a
	ld hl, wBaseTMHM
	ld de, wPokedexRuntimeTextBuffer + 16
	ld b, 8
.flags
	ld a, BANK(wBaseTMHM)
	call GetFarWRAMByte
	inc hl
	ld [de], a
	inc de
	dec b
	jr nz, .flags
	xor a
	ld [wPokedexRuntimeNumberTile], a
.machine
	ld a, [wPokedexRuntimeNumberTile]
	ld b, a
	and 7
	ld c, a
	ld a, 1
	jr z, .mask_ready
.mask
	add a
	dec c
	jr nz, .mask
.mask_ready
	ld c, a
	ld a, b
	srl a
	srl a
	srl a
	ld l, a
	ld h, 0
	ld de, wPokedexRuntimeTextBuffer + 16
	add hl, de
	ld a, c
	and [hl]
	jr z, .next_machine
	ld a, b
	cp NUM_TMS + NUM_HMS
	jr nc, .tutor
	inc a
	ld hl, wPokedexRuntimeTextBuffer + 4
	ld de, wPokedexRuntimeTMs
	jr .append_machine
.tutor
	sub NUM_TMS + NUM_HMS - 1
	ld hl, wPokedexRuntimeTextBuffer + 8
	ld de, wPokedexRuntimeTutors
.append_machine
	ld c, a
	ld a, [hl]
	inc [hl]
	ld l, a
	ld h, 0
	add hl, de
	ld a, BANK(wPokedexRuntimeTMs)
	ldh [rSVBK], a
	ld [hl], c
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
.next_machine
	ld hl, wPokedexRuntimeNumberTile
	inc [hl]
	ld a, [hl]
	cp NUM_TM_HM_TUTOR
	jr c, .machine
	ld a, [wPrevDexEntry]
	ld l, a
	ld a, [wPrevDexEntry + 1]
	ld h, a
	call PokedexRuntime_FamilyRoot
	ld b, h
	ld c, l
	ld hl, EggMovePointers
	ld a, BANK(EggMovePointers)
	call LoadDoubleIndirectPointer
	ld [wPokedexRuntimeTextBuffer + 13], a
	ld b, a
	ld a, l
	ld [wPokedexRuntimeTextBuffer + 14], a
	ld a, h
	ld [wPokedexRuntimeTextBuffer + 15], a
	ld e, 0
.egg
	push hl
	ld a, b
	call GetFarWord
	ld a, h
	and l
	inc a
	pop hl
	jr z, .egg_count
	inc e
	inc hl
	inc hl
	jr .egg
.egg_count
	ld a, e
	ld [wPokedexRuntimeTextBuffer + 12], a
	ld hl, wPokedexRuntimeTextBuffer
	ld b, 4
	ld c, 0
.pages
	ld a, [hl]
	and a
	jr z, .next_category
.five
	inc c
	sub 5
	jr z, .next_category
	jr nc, .five
.next_category
	ld de, 4
	add hl, de
	dec b
	jr nz, .pages
	ld a, c
	and a
	jr nz, .page_count
	inc a
.page_count
	ld c, a
	ld a, BANK(wPokedexRuntimeMovesStreams)
	ldh [rSVBK], a
	ld a, c
	ld [wPokedexRuntimeMovesPages], a
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ld hl, wPokedexRuntimeTextBuffer
	ld de, POKEDEX_ANIM_PAYLOAD
	ld bc, 16
	call CopyBytes
	ld a, BANK(wPokedexRuntimeMovesStreams)
	ldh [rSVBK], a
	ld hl, POKEDEX_ANIM_PAYLOAD
	ld de, wPokedexRuntimeMovesStreams
	ld bc, 16
	call CopyBytes
	ld a, BANK(wPokedexInfoState)
	ldh [rSVBK], a
	ret
ENDC
