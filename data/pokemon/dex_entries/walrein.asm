	db "Ice Break@"
	dw 407, 3320

.page1::
.line0:
	db "To protect its"
ASSERT @ - .line0 == 14
.line1:
	next "herd, the leader"
ASSERT @ - .line1 == 17
.line2:
	next "battles anything@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "that invades its"
ASSERT @ - .line3 == 16
.line4:
	next "territory, even at"
ASSERT @ - .line4 == 19
.line5:
	next "the cost of its@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "life. Its tusks"
ASSERT @ - .line6 == 15
.line7:
	next "may snap off in"
ASSERT @ - .line7 == 16
.line8:
	next "battle.@"
ASSERT @ - .line8 == 9
