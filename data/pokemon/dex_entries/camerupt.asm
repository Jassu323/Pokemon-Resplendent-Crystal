	db "Eruption@"
	dw 603, 4850

.page1::
.line0:
	db "A Pokémon that"
ASSERT @ - .line0 == 14
.line1:
	next "lives in the"
ASSERT @ - .line1 == 13
.line2:
	next "crater of a@"
ASSERT @ - .line2 == 13

.page2::
.line3:
	db "volcano. Every 10"
ASSERT @ - .line3 == 17
.line4:
	next "years, the"
ASSERT @ - .line4 == 11
.line5:
	next "volcanoes on its@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "back erupt"
ASSERT @ - .line6 == 10
.line7:
	next "violently."
ASSERT @ - .line7 == 11
.line8:
	next "Research is under@"
ASSERT @ - .line8 == 19

.page4::
.line9:
	db "way on the cause"
ASSERT @ - .line9 == 16
.line10:
	next "of eruption.@"
ASSERT @ - .line10 == 14
