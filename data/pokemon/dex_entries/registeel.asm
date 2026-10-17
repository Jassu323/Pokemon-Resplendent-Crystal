	db "Iron@"
	dw 603, 4519

.page1::
.line0:
	db "Its body is harder"
ASSERT @ - .line0 == 18
.line1:
	next "than any other"
ASSERT @ - .line1 == 15
.line2:
	next "kind of metal. The@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "body metal is"
ASSERT @ - .line3 == 13
.line4:
	next "composed of a"
ASSERT @ - .line4 == 14
.line5:
	next "mysterious@"
ASSERT @ - .line5 == 12

.page3::
.line6:
	db "substance. Not"
ASSERT @ - .line6 == 14
.line7:
	next "only is it hard,"
ASSERT @ - .line7 == 17
.line8:
	next "it shrinks and@"
ASSERT @ - .line8 == 16

.page4::
.line9:
	db "stretches"
ASSERT @ - .line9 == 9
.line10:
	next "flexibly.@"
ASSERT @ - .line10 == 11
