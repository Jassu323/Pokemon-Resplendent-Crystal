	db "Mushroom@"
	dw 104, 99

.page1::
.line0:
	db "It loves to eat"
ASSERT @ - .line0 == 15
.line1:
	next "damp, composted"
ASSERT @ - .line1 == 16
.line2:
	next "soil in forests.@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "If you enter a"
ASSERT @ - .line3 == 14
.line4:
	next "forest after a"
ASSERT @ - .line4 == 15
.line5:
	next "long rain, you can@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "see many Shroomish"
ASSERT @ - .line6 == 18
.line7:
	next "feasting on"
ASSERT @ - .line7 == 12
.line8:
	next "composted soil.@"
ASSERT @ - .line8 == 17
