	db "Brutal@"
	dw 511, 1958

.page1::
.line0:
	db "The vicious and"
ASSERT @ - .line0 == 15
.line1:
	next "sly gangster of"
ASSERT @ - .line1 == 16
.line2:
	next "the sea. Its skin@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "is specially"
ASSERT @ - .line3 == 12
.line4:
	next "textured to"
ASSERT @ - .line4 == 12
.line5:
	next "minimize drag in@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "water. Its speed"
ASSERT @ - .line6 == 16
.line7:
	next "tops out at over"
ASSERT @ - .line7 == 17
.line8:
	next "75 miles per hour.@"
ASSERT @ - .line8 == 20
