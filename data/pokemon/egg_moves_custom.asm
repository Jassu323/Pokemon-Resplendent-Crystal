SECTION "Egg Moves 3", ROMX

EggMovePointers3::
	dw NoEggMoves3 ; TREECKO
	dw NoEggMoves3 ; GROVYLE
	dw NoEggMoves3 ; SCEPTILE
.IndirectEnd::

NoEggMoves3:
	dw -1 ; end
