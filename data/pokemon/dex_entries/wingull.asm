	db "Seagull@"
	dw 200, 209

.page1::
.line0:
	db "It makes its nest"
ASSERT @ - .line0 == 17
.line1:
	next "on a sheer cliff"
ASSERT @ - .line1 == 17
.line2:
	next "at the edge of the@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "sea. It has"
ASSERT @ - .line3 == 11
.line4:
	next "trouble keeping"
ASSERT @ - .line4 == 16
.line5:
	next "its wings flapping@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "in flight."
ASSERT @ - .line6 == 10
.line7:
	next "Instead, it soars"
ASSERT @ - .line7 == 18
.line8:
	next "on updrafts.@"
ASSERT @ - .line8 == 14
