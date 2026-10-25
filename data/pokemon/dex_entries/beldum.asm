	db "Iron Ball@"
	dw 200, 2099

.page1::
.line0:
	db "When Beldum gather"
ASSERT @ - .line0 == 18
.line1:
	next "in a swarm, they"
ASSERT @ - .line1 == 17
.line2:
	next "move in perfect@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "unison as if they"
ASSERT @ - .line3 == 17
.line4:
	next "were but one"
ASSERT @ - .line4 == 13
.line5:
	next "Pokémon. They@"
ASSERT @ - .line5 == 15

.page3::
.line6:
	db "communicate with"
ASSERT @ - .line6 == 16
.line7:
	next "each other using"
ASSERT @ - .line7 == 17
.line8:
	next "brain waves.@"
ASSERT @ - .line8 == 14
