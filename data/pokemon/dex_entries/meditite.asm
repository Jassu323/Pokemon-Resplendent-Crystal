	db "Meditate@"
	dw 200, 247

.page1::
.line0:
	db "It continually"
ASSERT @ - .line0 == 14
.line1:
	next "meditates for"
ASSERT @ - .line1 == 14
.line2:
	next "hours every day.@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "As a result of"
ASSERT @ - .line3 == 14
.line4:
	next "rigorous and"
ASSERT @ - .line4 == 13
.line5:
	next "dedicated yoga@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "training, it has"
ASSERT @ - .line6 == 16
.line7:
	next "tempered its"
ASSERT @ - .line7 == 13
.line8:
	next "spiritual power so@"
ASSERT @ - .line8 == 20

.page4::
.line9:
	db "much it can fly.@"
ASSERT @ - .line9 == 17
