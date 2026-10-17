	db "Old Shrimp@"
	dw 204, 276

.page1::
.line0:
	db "It was resurrected"
ASSERT @ - .line0 == 18
.line1:
	next "from a fossil"
ASSERT @ - .line1 == 14
.line2:
	next "using the power of@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "science. It swims"
ASSERT @ - .line3 == 17
.line4:
	next "by undulating the"
ASSERT @ - .line4 == 18
.line5:
	next "eight wings at its@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "sides. They were"
ASSERT @ - .line6 == 16
.line7:
	next "feet that adapted"
ASSERT @ - .line7 == 18
.line8:
	next "to life in the@"
ASSERT @ - .line8 == 16

.page4::
.line9:
	db "sea.@"
ASSERT @ - .line9 == 5
