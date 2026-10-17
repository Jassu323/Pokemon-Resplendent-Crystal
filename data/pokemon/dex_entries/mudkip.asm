	db "Mud Fish@"
	dw 104, 168

.page1::
.line0:
	db "On land, it can"
ASSERT @ - .line0 == 15
.line1:
	next "powerfully lift"
ASSERT @ - .line1 == 16
.line2:
	next "large boulders by@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "planting its four"
ASSERT @ - .line3 == 17
.line4:
	next "feet and heaving."
ASSERT @ - .line4 == 18
.line5:
	next "It sleeps by@"
ASSERT @ - .line5 == 14

.page3::
.line6:
	db "burying itself in"
ASSERT @ - .line6 == 17
.line7:
	next "soil at the water's"
ASSERT @ - .line7 == 19
.line8:
	next "edge.@"
ASSERT @ - .line8 == 7
