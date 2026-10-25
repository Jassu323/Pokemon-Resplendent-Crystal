; PRIVATE ROUND-2 EXPERIMENT. Three resident rows, no speculative neighbor
; loads. Keep five physical slots for tear-free scrolling/wrapping staging.
PokedexPerf_PrepareIncomingGridRow:
    ld hl, wDexListingScrollOffset
    ld e, [hl]
    inc hl
    ld d, [hl]
    ld a, [wPokedexGridTopPhysicalRow]
    ld b, a
    ld a, [wPokedexGridScrollDirection]
    cp POKEDEX_GRID_SCROLL_UP
    jr z, .incoming
    ld a, b
    add POKEDEX_GRID_HEIGHT - 1
    cp POKEDEX_GRID_CACHE_ROWS
    jr c, .physical
    sub POKEDEX_GRID_CACHE_ROWS
.physical
    ld b, a
    ld a, e
    add 2 * POKEDEX_GRID_WIDTH
    ld e, a
    jr nc, .incoming
    inc d
.incoming
    call Pokedex_EnsureGridCache.CheckRowTag
    ret c
    ld a, b
    call Pokedex_PrepareGridCacheRow
    jp Pokedex_UploadPendingGridCacheRow
