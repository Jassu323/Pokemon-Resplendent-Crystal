	db "Gripper@"
	dw 703, 2350

.page1::
.line0:
	db "It is said to take"
ASSERT @ - .line0 == 18
.line1:
	next "lost spirits into"
ASSERT @ - .line1 == 18
.line2:
	next "its pliant body@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "and guide them"
ASSERT @ - .line3 == 14
.line4:
	next "home.@"
ASSERT @ - .line4 == 7
