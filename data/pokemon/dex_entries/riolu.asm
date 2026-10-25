	db "Emanation@"
	dw 204, 445

.page1::
.line0:
	db "It has the"
ASSERT @ - .line0 == 10
.line1:
	next "peculiar power of"
ASSERT @ - .line1 == 18
.line2:
	next "being able to see@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "emotions such as"
ASSERT @ - .line3 == 16
.line4:
	next "joy and rage in"
ASSERT @ - .line4 == 16
.line5:
	next "the form of waves.@"
ASSERT @ - .line5 == 20
