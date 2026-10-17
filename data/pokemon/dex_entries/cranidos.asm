	db "Head Butt@"
	dw 211, 694

.page1::
.line0:
	db "A lifelong jungle"
ASSERT @ - .line0 == 17
.line1:
	next "dweller from 100"
ASSERT @ - .line1 == 17
.line2:
	next "million years ago,@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "it would snap"
ASSERT @ - .line3 == 13
.line4:
	next "obstructing trees"
ASSERT @ - .line4 == 18
.line5:
	next "with head butts.@"
ASSERT @ - .line5 == 18
