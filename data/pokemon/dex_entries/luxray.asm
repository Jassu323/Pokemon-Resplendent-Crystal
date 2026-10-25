	db "Gleam Eyes@"
	dw 407, 926

.page1::
.line0:
	db "It can see clearly"
ASSERT @ - .line0 == 18
.line1:
	next "through walls to"
ASSERT @ - .line1 == 17
.line2:
	next "track down its@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "prey and seek its"
ASSERT @ - .line3 == 17
.line4:
	next "lost young.@"
ASSERT @ - .line4 == 13
