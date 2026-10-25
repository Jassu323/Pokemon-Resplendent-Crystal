	db "Aura@"
	dw 311, 1190

.page1::
.line0:
	db "A well-trained one"
ASSERT @ - .line0 == 18
.line1:
	next "can sense auras to"
ASSERT @ - .line1 == 19
.line2:
	next "identify and take@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "in the feelings of"
ASSERT @ - .line3 == 18
.line4:
	next "creatures over"
ASSERT @ - .line4 == 15
.line5:
	next "half a mile away.@"
ASSERT @ - .line5 == 19
