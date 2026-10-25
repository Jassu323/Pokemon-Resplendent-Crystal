	db "Kitten@"
	dw 200, 243

.page1::
.line0:
	db "A Skitty's adorably"
ASSERT @ - .line0 == 18
.line1:
	next "cute behavior"
ASSERT @ - .line1 == 14
.line2:
	next "makes it highly@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "popular. In"
ASSERT @ - .line3 == 11
.line4:
	next "battle, it makes"
ASSERT @ - .line4 == 17
.line5:
	next "its tail puff out.@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "It threatens foes"
ASSERT @ - .line6 == 17
.line7:
	next "with a sharp"
ASSERT @ - .line7 == 13
.line8:
	next "growl.@"
ASSERT @ - .line8 == 8
