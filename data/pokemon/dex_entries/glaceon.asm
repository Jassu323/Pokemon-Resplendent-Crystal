	db "Fresh Snow@"
	dw 207, 571

.page1::
.line0:
	db "By controlling its"
ASSERT @ - .line0 == 18
.line1:
	next "body heat, it can"
ASSERT @ - .line1 == 18
.line2:
	next "freeze the@"
ASSERT @ - .line2 == 12

.page2::
.line3:
	db "atmosphere around"
ASSERT @ - .line3 == 17
.line4:
	next "it to make a"
ASSERT @ - .line4 == 13
.line5:
	next "diamond-dust@"
ASSERT @ - .line5 == 14

.page3::
.line6:
	db "flurry.@"
ASSERT @ - .line6 == 8
