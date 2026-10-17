	db "Sea Basin@"
	dw 1409, 7760

.page1::
.line0:
	db "Kyogre has"
ASSERT @ - .line0 == 10
.line1:
	next "appeared in"
ASSERT @ - .line1 == 12
.line2:
	next "mythology as the@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "creator of the"
ASSERT @ - .line3 == 14
.line4:
	next "sea. After long"
ASSERT @ - .line4 == 16
.line5:
	next "years of feuding@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "with Groudon, it"
ASSERT @ - .line6 == 16
.line7:
	next "took to sleep at"
ASSERT @ - .line7 == 17
.line8:
	next "the bottom of the@"
ASSERT @ - .line8 == 19

.page4::
.line9:
	db "sea.@"
ASSERT @ - .line9 == 5
