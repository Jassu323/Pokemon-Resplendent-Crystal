	db "Whiskers@"
	dw 211, 520

.page1::
.line0:
	db "Mysteriously, it"
ASSERT @ - .line0 == 16
.line1:
	next "can foretell"
ASSERT @ - .line1 == 13
.line2:
	next "earthquakes. In@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "the daytime, it"
ASSERT @ - .line3 == 15
.line4:
	next "sleeps in mud at"
ASSERT @ - .line4 == 17
.line5:
	next "the bottom of a@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "pond. When it"
ASSERT @ - .line6 == 13
.line7:
	next "awakens, it"
ASSERT @ - .line7 == 12
.line8:
	next "continually feeds@"
ASSERT @ - .line8 == 19

.page4::
.line9:
	db "throughout the"
ASSERT @ - .line9 == 14
.line10:
	next "night.@"
ASSERT @ - .line10 == 8
