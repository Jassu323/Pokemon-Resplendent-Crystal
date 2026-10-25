	db "Young Fowl@"
	dw 211, 430

.page1::
.line0:
	db "It lashes out with"
ASSERT @ - .line0 == 18
.line1:
	next "10 kicks per"
ASSERT @ - .line1 == 13
.line2:
	next "second. Its strong@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "fighting instinct"
ASSERT @ - .line3 == 17
.line4:
	next "compels it to keep"
ASSERT @ - .line4 == 19
.line5:
	next "up its offensive@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "until the opponent"
ASSERT @ - .line6 == 18
.line7:
	next "gives up.@"
ASSERT @ - .line7 == 11
