	db "Iron Leg@"
	dw 503, 12125

.page1::
.line0:
	db "Metagross has four"
ASSERT @ - .line0 == 18
.line1:
	next "brains that are"
ASSERT @ - .line1 == 16
.line2:
	next "joined by a@"
ASSERT @ - .line2 == 13

.page2::
.line3:
	db "complex neural"
ASSERT @ - .line3 == 14
.line4:
	next "network. As a"
ASSERT @ - .line4 == 14
.line5:
	next "result of@"
ASSERT @ - .line5 == 11

.page3::
.line6:
	db "integration, this"
ASSERT @ - .line6 == 17
.line7:
	next "Pokémon is smarter"
ASSERT @ - .line7 == 19
.line8:
	next "than a@"
ASSERT @ - .line8 == 8

.page4::
.line9:
	db "supercomputer.@"
ASSERT @ - .line9 == 15
