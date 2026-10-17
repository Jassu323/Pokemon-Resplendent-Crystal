	db "Clay Doll@"
	dw 108, 474

.page1::
.line0:
	db "A Baltoy moves by"
ASSERT @ - .line0 == 17
.line1:
	next "spinning on its"
ASSERT @ - .line1 == 16
.line2:
	next "single foot. It@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "has been depicted"
ASSERT @ - .line3 == 17
.line4:
	next "in murals adorning"
ASSERT @ - .line4 == 19
.line5:
	next "the walls of a@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "once-bustling city"
ASSERT @ - .line6 == 18
.line7:
	next "in an ancient age.@"
ASSERT @ - .line7 == 20
