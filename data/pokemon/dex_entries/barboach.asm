	db "Whiskers@"
	dw 104, 42

.page1::
.line0:
	db "Its body is"
ASSERT @ - .line0 == 11
.line1:
	next "covered with a"
ASSERT @ - .line1 == 15
.line2:
	next "slimy film. The@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "film acts as a"
ASSERT @ - .line3 == 14
.line4:
	next "barrier to prevent"
ASSERT @ - .line4 == 19
.line5:
	next "germs in muddy@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "water from"
ASSERT @ - .line6 == 10
.line7:
	next "entering the"
ASSERT @ - .line7 == 13
.line8:
	next "Barboach's body.@"
ASSERT @ - .line8 == 17
