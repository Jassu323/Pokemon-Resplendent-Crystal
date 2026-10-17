	db "Twin Tusk@"
	dw 802, 6415

.page1::
.line0:
	db "A frozen one was"
ASSERT @ - .line0 == 16
.line1:
	next "dug up from soil"
ASSERT @ - .line1 == 17
.line2:
	next "dating back 10,000@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "years. It woke up"
ASSERT @ - .line3 == 17
.line4:
	next "to much amazement.@"
ASSERT @ - .line4 == 20
