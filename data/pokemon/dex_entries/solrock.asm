	db "Meteorite@"
	dw 311, 3395

.page1::
.line0:
	db "Solar energy is"
ASSERT @ - .line0 == 15
.line1:
	next "the source of this"
ASSERT @ - .line1 == 19
.line2:
	next "Pokémon's power. On@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "sunny days, groups"
ASSERT @ - .line3 == 18
.line4:
	next "of Solrock line up"
ASSERT @ - .line4 == 19
.line5:
	next "facing the sun and@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "absorb its light.@"
ASSERT @ - .line6 == 18
