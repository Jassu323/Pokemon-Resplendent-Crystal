	db "Iron Armor@"
	dw 211, 2646

.page1::
.line0:
	db "When two Lairon"
ASSERT @ - .line0 == 15
.line1:
	next "meet in the wild,"
ASSERT @ - .line1 == 18
.line2:
	next "they fight for@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "territory by"
ASSERT @ - .line3 == 12
.line4:
	next "bashing into each"
ASSERT @ - .line4 == 18
.line5:
	next "other with their@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "steel bodies. The"
ASSERT @ - .line6 == 17
.line7:
	next "sound of their"
ASSERT @ - .line7 == 15
.line8:
	next "collision carries@"
ASSERT @ - .line8 == 19

.page4::
.line9:
	db "for miles.@"
ASSERT @ - .line9 == 11
