	db "Lightning@"
	dw 200, 335

.page1::
.line0:
	db "It generates"
ASSERT @ - .line0 == 12
.line1:
	next "electricity using"
ASSERT @ - .line1 == 18
.line2:
	next "friction from the@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "atmosphere. In"
ASSERT @ - .line3 == 14
.line4:
	next "seasons with"
ASSERT @ - .line4 == 13
.line5:
	next "especially arid@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "air, its entire"
ASSERT @ - .line6 == 15
.line7:
	next "body blazes with"
ASSERT @ - .line7 == 17
.line8:
	next "violent showers of@"
ASSERT @ - .line8 == 20

.page4::
.line9:
	db "sparks.@"
ASSERT @ - .line9 == 8
