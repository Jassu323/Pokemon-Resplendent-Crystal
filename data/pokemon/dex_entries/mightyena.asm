	db "Bite@"
	dw 303, 816

.page1::
.line0:
	db "In the wild,"
ASSERT @ - .line0 == 12
.line1:
	next "Mightyena live in"
ASSERT @ - .line1 == 18
.line2:
	next "a pack. They never@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "defy their leader's"
ASSERT @ - .line3 == 18
.line4:
	next "orders. They"
ASSERT @ - .line4 == 13
.line5:
	next "defeat foes with@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "perfectly"
ASSERT @ - .line6 == 9
.line7:
	next "coordinated"
ASSERT @ - .line7 == 12
.line8:
	next "teamwork.@"
ASSERT @ - .line8 == 11
