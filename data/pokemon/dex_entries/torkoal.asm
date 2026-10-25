	db "Coal@"
	dw 108, 1773

.page1::
.line0:
	db "It battles using"
ASSERT @ - .line0 == 16
.line1:
	next "energy it gets"
ASSERT @ - .line1 == 15
.line2:
	next "from burning coal.@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "When loosing smoke"
ASSERT @ - .line3 == 18
.line4:
	next "from its nostrils,"
ASSERT @ - .line4 == 19
.line5:
	next "it lets off a@"
ASSERT @ - .line5 == 15

.page3::
.line6:
	db "sound that is"
ASSERT @ - .line6 == 13
.line7:
	next "similar to a"
ASSERT @ - .line7 == 13
.line8:
	next "locomotive's horn.@"
ASSERT @ - .line8 == 19
