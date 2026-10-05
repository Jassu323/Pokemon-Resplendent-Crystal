; Admit lower-panel work against the physical display clock.
; Normal-speed measured non-VBlank maxima + 2048 T guard + 8182 T finishing
; reserve, rounded up to whole scanlines. Double speed keeps these stricter
; bounds; no speed-up is assumed for DMA. Each admitted slice is rechecked.
PokedexPerf_AdmitInfo:
    ldh a, [hVBlankCounter]
    ld hl, wPokedexAnimLoopTick
    cp [hl]
    jr nz, .reject
    ld a, [wPokedexAnimSchedulerControl]
    bit POKEDEX_ANIM_UPLOAD_ACTIVE_F, a
    jr nz, .reject
    ldh a, [hSampledCryTimer]
    and a
    jr z, .clock
    ldh a, [rSVBK]
    push af
    ld a, BANK(wSampledCryCacheCount)
    ldh [rSVBK], a
    ld a, [wSampledCryCacheCount]
    ld c, a
    pop af
    ldh [rSVBK], a
    ldh a, [hSampledCryBlocks + 1]
    and a
    ld a, 5
    jr nz, .cache
    ldh a, [hSampledCryBlocks]
    cp 5
    jr c, .cache
    ld a, 5
.cache
    cp c
    jr z, .clock
    jr nc, .reject
.clock
    ld a, [wPokedexInfoState]
    ld e, a
    ld d, 0
    ld hl, PokedexPerf_InfoLatestLY
    add hl, de
    ld b, [hl]
    ldh a, [rLY]
    cp b
    ret
.reject
    and a
    ret

PokedexPerf_InfoLatestLY:
    ; idle, clear, plan, copy, upload, ready, initialize, mini, record
    db 0, 65, 81, 104, 87, 84, 113, 94, 108
