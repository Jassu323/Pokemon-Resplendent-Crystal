PUSHS
SECTION "Move Acquisition", ROMX

; C is a live move ID. BC/DE and the WRAM bank survive; carry means valid.
MoveDiscovery_MarkLiveID::
    push bc
    push de
    ld a, c
    call GetMoveIndexFromID
    ld d, h
    ld e, l
    farcall MoveDiscovery_MarkIndex
    pop de
    pop bc
    ret

; DE points to four live move IDs. Preserve all registers and bank ownership.
MoveDiscovery_MarkMoveList::
    push af
    push bc
    push de
    push hl
    ld h, d
    ld l, e
    call MoveDiscovery_LiveMoves
    pop hl
    pop de
    pop bc
    pop af
    ret

MoveDiscovery_Learned::
    push af
    push bc
    push de
    push hl
    ldh a, [rSVBK]
    push af
    ld a, 1
    ldh [rSVBK], a
    ld a, [wPutativeTMHMMove]
    ld c, a
    call MoveDiscovery_MarkLiveID
    jp MoveDiscovery_RestoreContext

MoveDiscovery_LastParty::
    push af
    push bc
    push de
    push hl
    ldh a, [rSVBK]
    push af
    ld a, 1
    ldh [rSVBK], a
    ld a, [wPartyCount]
    dec a
    call MoveDiscovery_PartySlot
    jp MoveDiscovery_RestoreContext

MoveDiscovery_CurrentParty::
    push af
    push bc
    push de
    push hl
    ldh a, [rSVBK]
    push af
    ld a, 1
    ldh [rSVBK], a
    ld a, [wCurPartyMon]
    call MoveDiscovery_PartySlot
    jp MoveDiscovery_RestoreContext

MoveDiscovery_Gift::
    ld a, b
    and a
    jp z, MoveDiscovery_LastParty
    cp 1
    ret nz
    jp MoveDiscovery_FirstBox

MoveDiscovery_FirstBox::
    push af
    push bc
    push de
    push hl
    ldh a, [rSVBK]
    push af
    ld a, 1
    ldh [rSVBK], a
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sBox)
    call OpenSRAM
    ld a, [sBoxCount]
    and a
    jr z, .done
    cp MONS_PER_BOX + 1
    jr nc, .done
    ld a, [sBoxSpecies]
    call MoveDiscovery_EligibleSpecies
    jr nc, .done
    ld hl, sBoxMon1Moves
    call MoveDiscovery_LiveMoves
.done
    pop af
    call MoveDiscovery_RestoreAcquisitionSRAM
    jp MoveDiscovery_RestoreContext

MoveDiscovery_RestoreContext:
    pop af
    ldh [rSVBK], a
    pop hl
    pop de
    pop bc
    pop af
    ret

MoveDiscovery_RestoreAcquisitionSRAM:
    cp NUM_SRAM_BANKS
    jp c, OpenSRAM
    jp CloseSRAM

MoveDiscovery_PartySlot:
    cp PARTY_LENGTH
    ret nc
    ld b, a
    ld a, [wPartyCount]
    cp b
    ret z
    ret c
    ld c, b
    ld b, 0
    ld hl, wPartySpecies
    add hl, bc
    ld a, [hl]
    call MoveDiscovery_EligibleSpecies
    ret nc
    ld a, c
    ld hl, wPartyMon1Moves
    ld bc, PARTYMON_STRUCT_LENGTH
    call AddNTimes
    jp MoveDiscovery_LiveMoves

MoveDiscovery_EligibleSpecies:
    and a
    ret z
    cp EGG
    ret z
    cp -1
    ret z
    scf
    ret

MoveDiscovery_LiveMoves:
    ld b, NUM_MOVES
.loop
    ld a, [hli]
    ld c, a
    push hl
    call MoveDiscovery_MarkLiveID
    pop hl
    dec b
    jr nz, .loop
    ret

; Packed inactive-box IDs are decoded without allocating transient IDs.
MoveDiscovery_PackedMoves::
    push af
    push bc
    push de
    push hl
    ld h, d
    ld l, e
    ld bc, MON_PP - MON_MOVES
    add hl, bc
    ld b, NUM_MOVES
.loop
    push bc
    push hl
    push de
    ld a, [de]
    ld c, a
    ld a, [hl]
    and $3f
    ld d, a
    ld e, c
    farcall MoveDiscovery_MarkIndex
    pop de
    pop hl
    pop bc
    inc de
    inc hl
    dec b
    jr nz, .loop
    pop hl
    pop de
    pop bc
    pop af
    ret

MoveDiscovery_BootstrapPrimary::
    call MoveDiscovery_NeedsBootstrap
    ret nc
    call MoveDiscovery_BootstrapOwned
    farcall MoveDiscovery_RepairPrimary
    ret

MoveDiscovery_BootstrapBackup::
    call MoveDiscovery_NeedsBootstrap
    ret nc
    call MoveDiscovery_BootstrapOwned
    farcall MoveDiscovery_RepairBackup
    ret

MoveDiscovery_NeedsBootstrap:
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    ld a, [wMoveDiscoveryWriteBlocked]
    and a
    jr nz, .no
    ld a, [wMoveDiscoveryStatus]
    cp MOVE_DISCOVERY_RECOVERED
    jr c, .no
    cp MOVE_DISCOVERY_UNSUPPORTED
    jr nc, .no
    scf
    jr .done
.no
    and a
.done
    pop bc
    ld a, b
    ldh [rSVBK], a
    ret

; Read-only scan: current sBox is live; its stored copy is deliberately skipped.
MoveDiscovery_BootstrapOwned::
    push af
    push bc
    push de
    push hl
    ldh a, [rSVBK]
    push af
    ld a, 1
    ldh [rSVBK], a
    ldh a, [hSRAMBank]
    push af
    ld c, 0
.party
    ld a, c
    push bc
    call MoveDiscovery_PartySlot
    pop bc
    inc c
    ld a, c
    cp PARTY_LENGTH
    jr c, .party
    ld a, [wDayCareMan]
    bit 0, a
    jr z, .lady
    ld hl, wBreedMon1Moves
    ld a, [wBreedMon1Species]
    call MoveDiscovery_EligibleSpecies
    call c, MoveDiscovery_LiveMoves
.lady
    ld a, [wDayCareLady]
    bit 0, a
    jr z, .boxes
    ld hl, wBreedMon2Moves
    ld a, [wBreedMon2Species]
    call MoveDiscovery_EligibleSpecies
    call c, MoveDiscovery_LiveMoves
.boxes
    ld a, BANK(sBox)
    call OpenSRAM
    ld hl, sBox
    ld c, 0
    call MoveDiscovery_ScanBox
    ld hl, .BoxAddresses
    ld b, 0
.box
    ld a, [wCurBox]
    and $7f
    cp b
    ld a, [hli]
    ld e, [hl]
    inc hl
    ld d, [hl]
    inc hl
    jr z, .next
    push bc
    push hl
    call OpenSRAM
    ld h, d
    ld l, e
    ld c, 1
    call MoveDiscovery_ScanBox
    pop hl
    pop bc
.next
    inc b
    ld a, b
    cp NUM_BOXES
    jr c, .box
    pop af
    call MoveDiscovery_RestoreAcquisitionSRAM
    jp MoveDiscovery_RestoreContext

.BoxAddresses:
for n, 1, NUM_BOXES + 1
    dba sBox{d:n}
endr

MoveDiscovery_ScanBox:
    ld a, [hl]
    cp MONS_PER_BOX + 1
    jr c, .count
    ld a, MONS_PER_BOX
.count
    and a
    ret z
    ld b, a
    inc hl
    ld d, h
    ld e, l
    push hl
    ld hl, MONS_PER_BOX + 1 + MON_MOVES
    add hl, de
    pop de
.mon
    ld a, [de]
    call MoveDiscovery_EligibleSpecies
    jr nc, .next
    push bc
    push de
    push hl
    bit 0, c
    jr nz, .packed
    call MoveDiscovery_LiveMoves
    jr .restore
.packed
    ld d, h
    ld e, l
    call MoveDiscovery_PackedMoves
.restore
    pop hl
    pop de
    pop bc
.next
    inc de
    push de
    ld de, BOXMON_STRUCT_LENGTH
    add hl, de
    pop de
    dec b
    jr nz, .mon
    ret

POPS
