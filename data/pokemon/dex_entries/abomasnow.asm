	db "Frost Tree@"
	dw 703, 2987

.page1::
.line0:
	db "They appear when"
ASSERT @ - .line0 == 16
.line1:
	next "the snow flowers"
ASSERT @ - .line1 == 17
.line2:
	next "bloom. When the@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "petals fall, they"
ASSERT @ - .line3 == 17
.line4:
	next "retreat to places"
ASSERT @ - .line4 == 18
.line5:
	next "unknown again.@"
ASSERT @ - .line5 == 16
