	db "Land Shark@"
	dw 204, 452

.page1::
.line0:
	db "It attacks using"
ASSERT @ - .line0 == 16
.line1:
	next "its huge mouth."
ASSERT @ - .line1 == 16
.line2:
	next "While its attacks@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "are powerful, it"
ASSERT @ - .line3 == 16
.line4:
	next "hurts itself out"
ASSERT @ - .line4 == 17
.line5:
	next "of clumsiness,@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "too.@"
ASSERT @ - .line6 == 5
