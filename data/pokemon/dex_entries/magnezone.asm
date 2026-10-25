	db "Magnet Area@"
	dw 311, 3968

.page1::
.line0:
	db "A group tried to"
ASSERT @ - .line0 == 16
.line1:
	next "use scientific"
ASSERT @ - .line1 == 15
.line2:
	next "means to make@"
ASSERT @ - .line2 == 15

.page2::
.line3:
	db "Magnezone evolve,"
ASSERT @ - .line3 == 17
.line4:
	next "but their efforts"
ASSERT @ - .line4 == 18
.line5:
	next "ended in failure.@"
ASSERT @ - .line5 == 19
