	db "Bronze@"
	dw 108, 1334

.page1::
.line0:
	db "There are"
ASSERT @ - .line0 == 9
.line1:
	next "researchers who"
ASSERT @ - .line1 == 16
.line2:
	next "believe this@"
ASSERT @ - .line2 == 14

.page2::
.line3:
	db "Pokémon reflected"
ASSERT @ - .line3 == 17
.line4:
	next "like a mirror in"
ASSERT @ - .line4 == 17
.line5:
	next "the distant past.@"
ASSERT @ - .line5 == 19
