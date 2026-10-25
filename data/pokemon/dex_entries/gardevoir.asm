	db "Embrace@"
	dw 503, 1067

.page1::
.line0:
	db "It apparently does"
ASSERT @ - .line0 == 18
.line1:
	next "not feel the pull"
ASSERT @ - .line1 == 18
.line2:
	next "of gravity because@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "it supports itself"
ASSERT @ - .line3 == 18
.line4:
	next "with psychic"
ASSERT @ - .line4 == 13
.line5:
	next "power. It will@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "give its life to"
ASSERT @ - .line6 == 16
.line7:
	next "protect its"
ASSERT @ - .line7 == 12
.line8:
	next "TRAINER.@"
ASSERT @ - .line8 == 10
