	db "Shield@"
	dw 108, 1257

.page1::
.line0:
	db "It is"
ASSERT @ - .line0 == 5
.line1:
	next "outstandingly"
ASSERT @ - .line1 == 14
.line2:
	next "armored. As a@"
ASSERT @ - .line2 == 15

.page2::
.line3:
	db "result, it can eat"
ASSERT @ - .line3 == 18
.line4:
	next "grass and berries"
ASSERT @ - .line4 == 18
.line5:
	next "without having to@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "fight.@"
ASSERT @ - .line6 == 7
