	db "Head Butt@"
	dw 503, 2260

.page1::
.line0:
	db "If two were to"
ASSERT @ - .line0 == 14
.line1:
	next "smash their heads"
ASSERT @ - .line1 == 18
.line2:
	next "together, their@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "foot-thick skulls"
ASSERT @ - .line3 == 17
.line4:
	next "would keep them"
ASSERT @ - .line4 == 16
.line5:
	next "from fainting.@"
ASSERT @ - .line5 == 16
