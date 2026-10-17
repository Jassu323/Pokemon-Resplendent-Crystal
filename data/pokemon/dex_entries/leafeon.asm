	db "Verdant@"
	dw 303, 562

.page1::
.line0:
	db "It basically does"
ASSERT @ - .line0 == 17
.line1:
	next "not fight. With"
ASSERT @ - .line1 == 16
.line2:
	next "cells similar to@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "those of plants,"
ASSERT @ - .line3 == 16
.line4:
	next "it can perform"
ASSERT @ - .line4 == 15
.line5:
	next "photosynthesis.@"
ASSERT @ - .line5 == 17
