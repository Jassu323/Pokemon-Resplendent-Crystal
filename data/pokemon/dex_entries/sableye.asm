	db "Darkness@"
	dw 108, 243

.page1::
.line0:
	db "It digs branching"
ASSERT @ - .line0 == 17
.line1:
	next "holes in caves"
ASSERT @ - .line1 == 15
.line2:
	next "using its sharp@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "claws in search of"
ASSERT @ - .line3 == 18
.line4:
	next "food--raw gems. A"
ASSERT @ - .line4 == 18
.line5:
	next "Sableye lurks in@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "darkness and is"
ASSERT @ - .line6 == 15
.line7:
	next "seen only rarely.@"
ASSERT @ - .line7 == 19
