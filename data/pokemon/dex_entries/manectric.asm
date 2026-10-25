	db "Discharge@"
	dw 411, 886

.page1::
.line0:
	db "Because lightning"
ASSERT @ - .line0 == 17
.line1:
	next "falls in their"
ASSERT @ - .line1 == 15
.line2:
	next "vicinities,@"
ASSERT @ - .line2 == 13

.page2::
.line3:
	db "Manectric were"
ASSERT @ - .line3 == 14
.line4:
	next "thought to have"
ASSERT @ - .line4 == 16
.line5:
	next "been born from@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "lightning. In"
ASSERT @ - .line6 == 13
.line7:
	next "battle, they"
ASSERT @ - .line7 == 13
.line8:
	next "create@"
ASSERT @ - .line8 == 8

.page4::
.line9:
	db "thunderclouds.@"
ASSERT @ - .line9 == 15
