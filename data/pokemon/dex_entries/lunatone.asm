	db "Meteorite@"
	dw 303, 3704

.page1::
.line0:
	db "It becomes very"
ASSERT @ - .line0 == 15
.line1:
	next "active on the"
ASSERT @ - .line1 == 14
.line2:
	next "night of a full@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "moon. This Pokémon"
ASSERT @ - .line3 == 18
.line4:
	next "was first"
ASSERT @ - .line4 == 10
.line5:
	next "discovered 40@"
ASSERT @ - .line5 == 15

.page3::
.line6:
	db "years ago at the"
ASSERT @ - .line6 == 16
.line7:
	next "site of a meteor"
ASSERT @ - .line7 == 17
.line8:
	next "strike.@"
ASSERT @ - .line8 == 9
