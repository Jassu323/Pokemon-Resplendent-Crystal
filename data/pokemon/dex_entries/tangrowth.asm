	db "Vine@"
	dw 607, 2835

.page1::
.line0:
	db "Its arms are made"
ASSERT @ - .line0 == 17
.line1:
	next "of plants that"
ASSERT @ - .line1 == 15
.line2:
	next "bind themselves to@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "things. They grow"
ASSERT @ - .line3 == 17
.line4:
	next "back right away if"
ASSERT @ - .line4 == 19
.line5:
	next "cut.@"
ASSERT @ - .line5 == 6
