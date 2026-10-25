	db "Wood Gecko@"
	dw 108, 110

.page1::
.line0:
	db "It makes its nest"
ASSERT @ - .line0 == 17
.line1:
	next "in a giant tree in"
ASSERT @ - .line1 == 19
.line2:
	next "the forest. It@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "ferociously guards"
ASSERT @ - .line3 == 18
.line4:
	next "against anything"
ASSERT @ - .line4 == 17
.line5:
	next "nearing its@"
ASSERT @ - .line5 == 13

.page3::
.line6:
	db "territory. It is"
ASSERT @ - .line6 == 16
.line7:
	next "said to be the"
ASSERT @ - .line7 == 15
.line8:
	next "protector of the@"
ASSERT @ - .line8 == 18

.page4::
.line9:
	db "forest's trees.@"
ASSERT @ - .line9 == 15
