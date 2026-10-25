	db "Virtual@"
	dw 211, 750

.page1::
.line0:
	db "Its programming"
ASSERT @ - .line0 == 15
.line1:
	next "was modified to"
ASSERT @ - .line1 == 16
.line2:
	next "enable work in@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "alien dimensions."
ASSERT @ - .line3 == 17
.line4:
	next "It did not work as"
ASSERT @ - .line4 == 19
.line5:
	next "planned.@"
ASSERT @ - .line5 == 10
