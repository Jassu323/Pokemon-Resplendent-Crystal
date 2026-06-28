SECTION "Egg Moves 3", ROMX

EggMovePointers3::
	dw NoEggMoves3 ; TREECKO
	dw NoEggMoves3 ; GROVYLE
	dw NoEggMoves3 ; SCEPTILE
	dw NoEggMoves3 ; TORCHIC
	dw NoEggMoves3 ; COMBUSKEN
	dw NoEggMoves3 ; BLAZIKEN
	dw NoEggMoves3 ; MUDKIP
	dw NoEggMoves3 ; MARSHTOMP
	dw NoEggMoves3 ; SWAMPERT
.IndirectEnd::

NoEggMoves3:
	dw -1 ; end
