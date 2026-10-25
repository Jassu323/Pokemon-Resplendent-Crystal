	db "Cave@"
	dw 407, 1235

.page1::
.line0:
	db "It loves sparkly"
ASSERT @ - .line0 == 16
.line1:
	next "things. It seeks"
ASSERT @ - .line1 == 17
.line2:
	next "treasures in caves@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "and hoards the"
ASSERT @ - .line3 == 14
.line4:
	next "loot in its nest.@"
ASSERT @ - .line4 == 19
