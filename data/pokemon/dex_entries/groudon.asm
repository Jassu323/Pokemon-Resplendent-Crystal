	db "Continent@"
	dw 1106, 20944

.page1::
.line0:
	db "Groudon has"
ASSERT @ - .line0 == 11
.line1:
	next "appeared in"
ASSERT @ - .line1 == 12
.line2:
	next "mythology as the@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "creator of the"
ASSERT @ - .line3 == 14
.line4:
	next "land. It sleeps in"
ASSERT @ - .line4 == 19
.line5:
	next "magma underground@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "and is said to"
ASSERT @ - .line6 == 14
.line7:
	next "make volcanoes"
ASSERT @ - .line7 == 15
.line8:
	next "erupt on@"
ASSERT @ - .line8 == 10

.page4::
.line9:
	db "awakening.@"
ASSERT @ - .line9 == 11
