PUSHS
SECTION "Move Pokedex Gift", ROMX

; Every Pokemon can use Struggle. Reveal it when Oak awards the Pokedex.
MoveDiscovery_PokedexGift::
    push af
    push bc
    push de
    push hl
    ld de, STRUGGLE
    farcall MoveDiscovery_MarkIndex
    pop hl
    pop de
    pop bc
    pop af
    ret

POPS
