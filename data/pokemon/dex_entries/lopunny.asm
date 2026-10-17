	db "Rabbit@"
	dw 311, 734

.page1::
.line0:
	db "The ears appear to"
ASSERT @ - .line0 == 18
.line1:
	next "be delicate. If"
ASSERT @ - .line1 == 16
.line2:
	next "they are touched@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "roughly, it kicks"
ASSERT @ - .line3 == 17
.line4:
	next "with its graceful"
ASSERT @ - .line4 == 18
.line5:
	next "legs.@"
ASSERT @ - .line5 == 7
