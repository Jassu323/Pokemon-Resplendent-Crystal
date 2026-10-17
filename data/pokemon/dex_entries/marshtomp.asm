	db "Mud Fish@"
	dw 204, 617

.page1::
.line0:
	db "Its toughened hind"
ASSERT @ - .line0 == 18
.line1:
	next "legs enable it to"
ASSERT @ - .line1 == 18
.line2:
	next "stand upright.@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "Because it weakens"
ASSERT @ - .line3 == 18
.line4:
	next "if its skin dries"
ASSERT @ - .line4 == 18
.line5:
	next "out, it@"
ASSERT @ - .line5 == 9

.page3::
.line6:
	db "replenishes fluids"
ASSERT @ - .line6 == 18
.line7:
	next "by playing in mud.@"
ASSERT @ - .line7 == 20
