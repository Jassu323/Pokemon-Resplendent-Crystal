DEF MOVE_DISCOVERY_BYTES EQU 64
DEF MOVE_DISCOVERY_VERSION EQU 1
DEF MOVE_DISCOVERY_VALID EQU 1
DEF MOVE_DISCOVERY_RECOVERED EQU 2
DEF MOVE_DISCOVERY_LEGACY EQU 3
DEF MOVE_DISCOVERY_DAMAGED EQU 4
DEF MOVE_DISCOVERY_UNSUPPORTED EQU 5
ASSERT NUM_ATTACKS <= MOVE_DISCOVERY_BYTES * 8

PUSHS
SECTION "Move Discovery", ROMX

; DE is a permanent move index. Carry means seen; BC/DE and SVBK survive.
MoveDiscovery_CheckIndex::
    push bc
    push de
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    call MoveDiscovery_BitAddress
    jr c, .unseen
    ld a, [hl]
    and b
    jr z, .unseen
    scf
    jr .done
.unseen
    and a
.done
    pop bc
    ld a, b
    ldh [rSVBK], a
    pop de
    pop bc
    ret

; DE is a permanent move index. Invalid indices cannot change any memory.
MoveDiscovery_MarkIndex::
    push bc
    push de
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    call MoveDiscovery_BitAddress
    jr c, .invalid
    ld a, [hl]
    or b
    ld [hl], a
    scf
    jr .done
.invalid
    and a
.done
    pop bc
    ld a, b
    ldh [rSVBK], a
    pop de
    pop bc
    ret

MoveDiscovery_BitAddress:
    ld a, d
    or e
    jr z, .invalid
    ld a, d
    cp HIGH(NUM_ATTACKS + 1)
    jr c, .valid
    jr nz, .invalid
    ld a, e
    cp LOW(NUM_ATTACKS + 1)
    jr nc, .invalid
.valid
    dec de
    ld a, e
    and 7
    ld c, a
    ld b, 1
    jr z, .mask_ready
.mask
    sla b
    dec c
    jr nz, .mask
.mask_ready
    srl d
    rr e
    srl d
    rr e
    srl d
    rr e
    ld hl, wMoveDiscoverySeen
    add hl, de
    and a
    ret
.invalid
    scf
    ret

MoveDiscovery_Clear::
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    ld hl, wMoveDiscoverySeen
    ld bc, wMoveDiscoveryEnd - wMoveDiscoverySeen
    xor a
    call ByteFill
    pop af
    ldh [rSVBK], a
    ret

MoveDiscovery_LoadPrimary::
    call MoveDiscovery_ValidatePrimary
    jr c, .recover
    call MoveDiscovery_ReadPrimary
    ld a, MOVE_DISCOVERY_VALID
    call MoveDiscovery_SetStatus
    farcall VerifyBackupChecksum
    ret nz
    call MoveDiscovery_BackupIdentity
    ret nz
    call MoveDiscovery_ValidateBackup
    jp MoveDiscovery_ProtectUnsupported
.recover
    ld a, c
    call MoveDiscovery_SetStatus
    call MoveDiscovery_ProtectUnsupported
    farcall VerifyBackupChecksum
    ret nz
    call MoveDiscovery_BackupIdentity
    ret nz
    call MoveDiscovery_ValidateBackup
    jr c, MoveDiscovery_ProtectUnsupported
    call MoveDiscovery_ReadBackup
    ld a, MOVE_DISCOVERY_RECOVERED
    call MoveDiscovery_SetStatus
    ret

MoveDiscovery_LoadBackup::
    call MoveDiscovery_ValidateBackup
    jr c, .recover
    call MoveDiscovery_ReadBackup
    ld a, MOVE_DISCOVERY_VALID
    call MoveDiscovery_SetStatus
    farcall VerifyChecksum
    ret nz
    call MoveDiscovery_PrimaryIdentity
    ret nz
    call MoveDiscovery_ValidatePrimary
    jp MoveDiscovery_ProtectUnsupported
.recover
    ld a, c
    call MoveDiscovery_SetStatus
    call MoveDiscovery_ProtectUnsupported
    farcall VerifyChecksum
    ret nz
    call MoveDiscovery_PrimaryIdentity
    ret nz
    call MoveDiscovery_ValidatePrimary
    jr c, MoveDiscovery_ProtectUnsupported
    call MoveDiscovery_ReadPrimary
    ld a, MOVE_DISCOVERY_RECOVERED
    call MoveDiscovery_SetStatus
    ret

MoveDiscovery_SetStatus:
    push bc
    ld b, a
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    ld a, b
    ld [wMoveDiscoveryStatus], a
    pop af
    ldh [rSVBK], a
    pop bc
    ret

; A valid but unsupported extension is opaque. Preserve both records.
MoveDiscovery_ProtectUnsupported:
    ld a, c
    cp MOVE_DISCOVERY_UNSUPPORTED
    ret nz
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    ld a, 1
    ld [wMoveDiscoveryWriteBlocked], a
    pop af
    ldh [rSVBK], a
    ret

MoveDiscovery_PrimaryIdentity:
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sPlayerData)
    call OpenSRAM
    ld hl, sPlayerData
    jr MoveDiscovery_CompareIdentity
MoveDiscovery_BackupIdentity:
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sBackupPlayerData)
    call OpenSRAM
    ld hl, sBackupPlayerData
MoveDiscovery_CompareIdentity:
    ld de, wPlayerID
    ld b, 2
.player
    ld a, [de]
    cp [hl]
    jr nz, .done
    inc de
    inc hl
    dec b
    jr nz, .player
    ld bc, wSecretID - wPlayerID - 2
    add hl, bc
    ld de, wSecretID
    ld b, 2
.secret
    ld a, [de]
    cp [hl]
    jr nz, .done
    inc de
    inc hl
    dec b
    jr nz, .secret
.done
    ld c, 0
    jr z, .result
    inc c
.result
    pop af
    call MoveDiscovery_RestoreSRAM
    ld a, c
    and a
    ret

MoveDiscovery_ValidatePrimary::
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sMoveDiscovery)
    call OpenSRAM
    ld hl, sMoveDiscovery
    ld bc, sPlayerData
    ld de, sChecksum
    jr MoveDiscovery_ValidateCopy
MoveDiscovery_ValidateBackup::
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sBackupMoveDiscovery)
    call OpenSRAM
    ld hl, sBackupMoveDiscovery
    ld bc, sBackupPlayerData
    ld de, sBackupChecksum
MoveDiscovery_ValidateCopy:
    call MoveDiscovery_ValidateRecord
    ld e, c
    pop af
    call MoveDiscovery_RestoreSRAM
    ld c, e
    ld a, c
    and a
    ret z
    scf
    ret

; HL record, BC saved player data, DE parent checksum address. C is status.
MoveDiscovery_ValidateRecord:
    ld a, [hli]
    cp $4d
    jr nz, .legacy
    ld a, [hli]
    cp $44
    jr nz, .legacy
    inc hl
    ld a, [hli]
    and a
    jr z, .bad
    cp 129
    jr nc, .bad
    ld a, [de]
    cp [hl]
    jr nz, .bad
    inc hl
    inc de
    ld a, [de]
    cp [hl]
    jr nz, .bad
    ld de, -5
    add hl, de
    push hl
    call MoveDiscovery_ComputeCRC
    pop hl
    ld bc, 6
    add hl, bc
    ld a, [hli]
    cp e
    jr nz, .bad
    ld a, [hl]
    cp d
    jr nz, .bad
    ld bc, -5
    add hl, bc
    ld a, [hli]
    cp MOVE_DISCOVERY_VERSION
    jr nz, .unsupported
    ld a, [hl]
    cp MOVE_DISCOVERY_BYTES
    jr nz, .unsupported
    ld c, 0
    and a
    ret
.legacy
    ld c, MOVE_DISCOVERY_LEGACY
    scf
    ret
.bad
    ld c, MOVE_DISCOVERY_DAMAGED
    scf
    ret
.unsupported
    ld c, MOVE_DISCOVERY_UNSUPPORTED
    scf
    ret

; CCITT-FALSE: magic/version/length/parent, player+secret IDs, then bitmap.
; The fixed magic lets writers compute the CRC before committing the marker.
MoveDiscovery_ComputeCRC::
    push bc
    push hl
    inc hl
    inc hl
    inc hl
    ld a, [hl]
    pop hl
    push af
    ld de, $ffff
    ld a, $4d
    call MoveDiscovery_CRCByte
    ld a, $44
    call MoveDiscovery_CRCByte
    inc hl
    inc hl
    ld b, 4
.metadata
    ld a, [hli]
    call MoveDiscovery_CRCByte
    dec b
    jr nz, .metadata
    pop af
    pop bc
    push af
    push hl
    ld h, b
    ld l, c
    ld a, [hli]
    call MoveDiscovery_CRCByte
    ld a, [hli]
    call MoveDiscovery_CRCByte
    ld bc, wSecretID - wPlayerID - 2
    add hl, bc
    ld a, [hli]
    call MoveDiscovery_CRCByte
    ld a, [hl]
    call MoveDiscovery_CRCByte
    pop hl
    inc hl
    inc hl
    pop af
    ld b, a
.bitmap
    ld a, [hli]
    call MoveDiscovery_CRCByte
    dec b
    jr nz, .bitmap
    ret

MoveDiscovery_CRCByte:
    push bc
    xor d
    ld d, a
    ld b, 8
.bit
    sla e
    rl d
    jr nc, .next
    ld a, d
    xor $10
    ld d, a
    ld a, e
    xor $21
    ld e, a
.next
    dec b
    jr nz, .bit
    pop bc
    ret

MoveDiscovery_ReadPrimary:
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sMoveDiscovery)
    call OpenSRAM
    ld hl, sMoveDiscovery + 8
    jr MoveDiscovery_ReadCopy
MoveDiscovery_ReadBackup:
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sBackupMoveDiscovery)
    call OpenSRAM
    ld hl, sBackupMoveDiscovery + 8
MoveDiscovery_ReadCopy:
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    ld de, wMoveDiscoverySeen
    ld bc, MOVE_DISCOVERY_BYTES
    call CopyBytes
    pop af
    ldh [rSVBK], a
    pop af
    jp MoveDiscovery_RestoreSRAM

; DE is the newly computed parent checksum. Existing main ranges are unchanged.
MoveDiscovery_SavePrimary::
    call MoveDiscovery_CanWrite
    ret c
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sMoveDiscovery)
    call OpenSRAM
    ld hl, sMoveDiscovery
    ld bc, sPlayerData
    jr MoveDiscovery_WriteCopy
MoveDiscovery_SaveBackup::
    call MoveDiscovery_CanWrite
    ret c
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sBackupMoveDiscovery)
    call OpenSRAM
    ld hl, sBackupMoveDiscovery
    ld bc, sBackupPlayerData
MoveDiscovery_WriteCopy:
    call MoveDiscovery_WriteRecord
    pop af
    jp MoveDiscovery_RestoreSRAM

; Recover the selected extension before the normal loader replaces its donor.
MoveDiscovery_RepairPrimary:
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sChecksum)
    call OpenSRAM
    ld a, [sChecksum]
    ld e, a
    ld a, [sChecksum + 1]
    ld d, a
    call MoveDiscovery_SavePrimary
    pop af
    jp MoveDiscovery_RestoreSRAM

MoveDiscovery_RepairBackup:
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sBackupChecksum)
    call OpenSRAM
    ld a, [sBackupChecksum]
    ld e, a
    ld a, [sBackupChecksum + 1]
    ld d, a
    call MoveDiscovery_SaveBackup
    pop af
    jp MoveDiscovery_RestoreSRAM

MoveDiscovery_CanWrite:
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    ld a, [wMoveDiscoveryWriteBlocked]
    and a
    jr z, .allowed
    scf
.allowed
    pop bc
    ld a, b
    ldh [rSVBK], a
    ret

MoveDiscovery_WriteRecord:
    push bc
    push hl
    xor a
    ld [hli], a
    ld [hli], a
    ld a, MOVE_DISCOVERY_VERSION
    ld [hli], a
    ld a, MOVE_DISCOVERY_BYTES
    ld [hli], a
    ld a, e
    ld [hli], a
    ld a, d
    ld [hli], a
    inc hl
    inc hl
    ld d, h
    ld e, l
    ldh a, [rSVBK]
    push af
    ld a, BANK(wMoveDiscoverySeen)
    ldh [rSVBK], a
    ld hl, wMoveDiscoverySeen
    ld bc, MOVE_DISCOVERY_BYTES
    call CopyBytes
    pop af
    ldh [rSVBK], a
    pop hl
    pop bc
    push hl
    call MoveDiscovery_ComputeCRC
    pop hl
    push hl
    ld bc, 6
    add hl, bc
    ld a, e
    ld [hli], a
    ld [hl], d
    pop hl
    ld a, $4d
    ld [hli], a
    ld [hl], $44
    ret

MoveDiscovery_Invalidate::
    ldh a, [hSRAMBank]
    push af
    ld a, BANK(sMoveDiscovery)
    call OpenSRAM
    xor a
    ld [sMoveDiscovery], a
    ld [sMoveDiscovery + 1], a
    ld a, BANK(sBackupMoveDiscovery)
    call OpenSRAM
    xor a
    ld [sBackupMoveDiscovery], a
    ld [sBackupMoveDiscovery + 1], a
    pop af
    jp MoveDiscovery_RestoreSRAM

MoveDiscovery_RestoreSRAM:
    cp NUM_SRAM_BANKS
    jp c, OpenSRAM
    jp CloseSRAM

POPS
