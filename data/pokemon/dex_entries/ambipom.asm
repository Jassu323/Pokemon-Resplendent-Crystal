	db "Long Tail@"
	dw 311, 448

.page1::
.line0:
	db "Split into two,"
ASSERT @ - .line0 == 15
.line1:
	next "the tails are so"
ASSERT @ - .line1 == 17
.line2:
	next "adept at handling@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "and doing things,"
ASSERT @ - .line3 == 17
.line4:
	next "Ambipom rarely"
ASSERT @ - .line4 == 15
.line5:
	next "uses its hands.@"
ASSERT @ - .line5 == 17
