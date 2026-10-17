	db "Flash@"
	dw 108, 209

.page1::
.line0:
	db "The extension and"
ASSERT @ - .line0 == 17
.line1:
	next "contraction of its"
ASSERT @ - .line1 == 19
.line2:
	next "muscles generates@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "electricity. It"
ASSERT @ - .line3 == 15
.line4:
	next "glows when in"
ASSERT @ - .line4 == 14
.line5:
	next "trouble.@"
ASSERT @ - .line5 == 10
