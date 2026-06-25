_GiveOddEgg:
	; Figure out which egg to give.

	; Compare a random word to probabilities out of $ffff.
	call Random
	ld hl, OddEggProbabilities
	ld c, 0
	ld b, c
.loop
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a

	; Break on $ffff.
	ld a, d
	cp HIGH($ffff)
	jr nz, .not_done
	ld a, e
	cp LOW($ffff)
	jr z, .done
.not_done

	; Break when the random word <= the next probability in de.
	ldh a, [hRandomSub]
	cp d
	jr c, .done
	jr z, .ok
	jr .next
.ok
	ldh a, [hRandomAdd]
	cp e
	jr c, .done
	jr z, .done
.next
	inc bc
	jr .loop
.done

	push bc
	ld hl, OddEggs
	ld a, NICKNAMED_MON_STRUCT_LENGTH
	call AddNTimes

	; Writes to wOddEgg, wOddEggName, and wOddEggOT,
	; even though OddEggs does not have data for wOddEggOT
	ld de, wOddEgg
	ld bc, NICKNAMED_MON_STRUCT_LENGTH + NAME_LENGTH
	call CopyBytes

	; Loads the actual species and overwrites the zero in wOddEggSpecies
	pop hl
	add hl, hl
	push hl
	ld bc, OddEggSpecies
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
	call GetPokemonIDFromIndex
	ld [wOddEggSpecies], a

	; And likewise with moves
	pop hl
	add hl, hl
	add hl, hl
	ld bc, OddEggMoves
	add hl, bc
	ld c, NUM_MOVES
	ld de, wOddEggMoves
.move_loop
	ld a, [hli]
	push hl
	ld h, [hl]
	ld l, a
	call GetMoveIDFromIndex
	pop hl
	inc hl
	ld [de], a
	inc de
	dec c
	jr nz, .move_loop

	ld a, EGG_TICKET
	ld [wCurItem], a
	ld a, 1
	ld [wItemQuantityChange], a
	ld a, -1
	ld [wCurItemQuantity], a
	ld hl, wNumItems
	call TossItem

	call .AddOddEggToParty
	ret

.Odd:
	dname "Odd", MON_NAME_LENGTH + 1

.AddOddEggToParty:
	ld hl, wPartyCount
	ld a, [hl]
	ld e, a
	inc [hl]

	ld bc, wPartySpecies
	ld d, e
.party_species_loop
	inc bc
	dec d
	jr nz, .party_species_loop
	ld a, e
	ld [wCurPartyMon], a
	ld a, EGG
	ld [bc], a
	inc bc
	ld a, -1
	ld [bc], a

	ld hl, wPartyMon1Species
	ld bc, PARTYMON_STRUCT_LENGTH
	ld a, [wCurPartyMon]
.party_struct_loop
	add hl, bc
	dec a
	and a
	jr nz, .party_struct_loop
	ld e, l
	ld d, h
	ld hl, wOddEgg
	ld bc, PARTYMON_STRUCT_LENGTH
	call CopyBytes

	ld hl, wPartyMonOTs
	ld bc, NAME_LENGTH
	ld a, [wCurPartyMon]
.ot_loop
	add hl, bc
	dec a
	and a
	jr nz, .ot_loop
	ld e, l
	ld d, h
	ld hl, .Odd
	ld bc, MON_NAME_LENGTH - 1
	call CopyBytes
	ld a, '@'
	ld [de], a

	ld hl, wPartyMonNicknames
	ld bc, MON_NAME_LENGTH
	ld a, [wCurPartyMon]
.nickname_loop
	add hl, bc
	dec a
	and a
	jr nz, .nickname_loop
	ld e, l
	ld d, h
	ld hl, wOddEggName
	ld bc, MON_NAME_LENGTH - 1
	call CopyBytes
	ld a, '@'
	ld [de], a
	ret

INCLUDE "data/events/odd_eggs.asm"
