	db "Guts@"
	dw 303, 1905

.page1::
.line0:
	db "It loves to"
ASSERT @ - .line0 == 11
.line1:
	next "toughen up its"
ASSERT @ - .line1 == 15
.line2:
	next "body above all@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "else. If you hear"
ASSERT @ - .line3 == 17
.line4:
	next "quaking rumbles in"
ASSERT @ - .line4 == 19
.line5:
	next "a cave, it is the@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "sound of Makuhita"
ASSERT @ - .line6 == 17
.line7:
	next "undertaking"
ASSERT @ - .line7 == 12
.line8:
	next "strenuous@"
ASSERT @ - .line8 == 11

.page4::
.line9:
	db "training.@"
ASSERT @ - .line9 == 10
