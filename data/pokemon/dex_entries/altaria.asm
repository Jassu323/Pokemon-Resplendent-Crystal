	db "Humming@"
	dw 307, 454

.page1::
.line0:
	db "It hums in a"
ASSERT @ - .line0 == 12
.line1:
	next "beautiful soprano"
ASSERT @ - .line1 == 18
.line2:
	next "voice. It flies@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "among white clouds"
ASSERT @ - .line3 == 18
.line4:
	next "in the blue sky."
ASSERT @ - .line4 == 17
.line5:
	next "It launches@"
ASSERT @ - .line5 == 13

.page3::
.line6:
	db "intensely hot"
ASSERT @ - .line6 == 13
.line7:
	next "fireballs from its"
ASSERT @ - .line7 == 19
.line8:
	next "mouth.@"
ASSERT @ - .line8 == 8
