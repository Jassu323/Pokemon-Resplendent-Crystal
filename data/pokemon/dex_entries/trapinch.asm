	db "Ant Pit@"
	dw 204, 331

.page1::
.line0:
	db "Its big jaws"
ASSERT @ - .line0 == 12
.line1:
	next "crunch through"
ASSERT @ - .line1 == 15
.line2:
	next "boulders. Because@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "its head is so"
ASSERT @ - .line3 == 14
.line4:
	next "big, it has a hard"
ASSERT @ - .line4 == 19
.line5:
	next "time getting back@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "upright if it tips"
ASSERT @ - .line6 == 18
.line7:
	next "over onto its"
ASSERT @ - .line7 == 14
.line8:
	next "back.@"
ASSERT @ - .line8 == 7
