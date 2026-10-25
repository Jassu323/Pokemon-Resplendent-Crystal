	db "Mach@"
	dw 603, 2094

.page1::
.line0:
	db "It is said that"
ASSERT @ - .line0 == 15
.line1:
	next "when one runs at"
ASSERT @ - .line1 == 17
.line2:
	next "high speed, its@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "wings create"
ASSERT @ - .line3 == 12
.line4:
	next "blades of wind"
ASSERT @ - .line4 == 15
.line5:
	next "that can fell@"
ASSERT @ - .line5 == 15

.page3::
.line6:
	db "nearby trees.@"
ASSERT @ - .line6 == 14
