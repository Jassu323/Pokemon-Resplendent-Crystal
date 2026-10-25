; Area owns bank-0 tiles, not either Info atlas.
; Only an already committed, idle Info page may use this cache. Its immutable
; record holds the tilemap; dead glyph-copy scratch holds 224 attribute bytes.
PokedexPerf_CacheInfoAcrossArea:
    ldh a, [rSVBK]
    push af
    ld a, BANK(wPokedexInfoState)
    ldh [rSVBK], a
    xor a
    ld [wPokedexPerfRetainedInfo], a
    ld a, [wPokedexSelectedView]
    cp DEXSELECT_VIEW_INFO
    jr nz, .done
    ld a, [wPokedexOwnerTransition]
    ld b, a
    ld a, [wPokedexInfoState]
    or b
    ld b, a
    ld a, [wPokedexInfoPendingPage]
    or b
    jr nz, .done
    ld a, [wPokedexInfoVisible]
    and a
    jr z, .done
    ld hl, wPokedexOwnerAttrmapBuffer + 9 * TILEMAP_WIDTH
    ld de, wPokedexInfoGFX
    ld bc, 7 * TILEMAP_WIDTH
    call CopyBytes
    ld a, TRUE
    ld [wPokedexPerfRetainedInfo], a
.done
    pop af
    ldh [rSVBK], a
    ret

PokedexPerf_RestoreInfoAcrossArea:
; Caller selected bank 3. Carry means no renderer/reupload is necessary.
    ld a, [wPokedexPerfRetainedInfo]
    ld b, a
    xor a
    ld [wPokedexPerfRetainedInfo], a
    ld a, b
    and a
    ret z
    ld a, [wPokedexSelectedState]
    cp DEXSELECT_STATE_AREA_ACTIVE
    ret nz
    ld a, [wPokedexInfoActiveAtlasBuffer]
    ld [wPokedexInfoAtlasBuffer], a
    call PokedexInfo_RecordAddress
    ld h, d
    ld l, e
    ld de, wPokedexOwnerTilemapBuffer + 9 * TILEMAP_WIDTH
    ld bc, 7 * TILEMAP_WIDTH
    call CopyBytes
    ld de, wPokedexInfoTileSources
    ld bc, POKEDEX_INFO_TILES * 2
    call CopyBytes
    ld a, [hl]
    ld [wPokedexInfoTileCount], a
    ld hl, wPokedexInfoGFX
    ld de, wPokedexOwnerAttrmapBuffer + 9 * TILEMAP_WIDTH
    ld bc, 7 * TILEMAP_WIDTH
    call CopyBytes
    call PokedexInfo_DrawBadge
    ld a, POKEDEX_INFO_READY
    ld [wPokedexInfoState], a
    call PokedexInfo_StagePalettes
    call PokedexInfo_StageOAM
    scf
    ret
