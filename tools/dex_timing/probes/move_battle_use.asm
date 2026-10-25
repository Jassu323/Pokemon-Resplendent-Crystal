PUSHS
SECTION "Move Battle Discovery", ROMX

; Record the presented actor move, not menu selection or generated movesets.
MoveDiscovery_BattleUse::
    push af
    push bc
    push de
    push hl
    ldh a, [rSVBK]
    push af
    ld a, 1
    ldh [rSVBK], a
    ld a, [wBattleMode]
    and a
    jr z, .done
    cp 3
    jr nc, .done
    ld a, BATTLE_VARS_MOVE_ANIM
    call GetBattleVar
    ld c, a
    farcall MoveDiscovery_MarkLiveID
.done
    pop af
    ldh [rSVBK], a
    pop hl
    pop de
    pop bc
    pop af
    ret

POPS
