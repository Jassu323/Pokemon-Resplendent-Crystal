	db "Iron Claw@"
	dw 311, 4464

.page1::
.line0:
	db "The claws tipping"
ASSERT @ - .line0 == 17
.line1:
	next "its arms pack the"
ASSERT @ - .line1 == 18
.line2:
	next "destructive power@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "to tear through"
ASSERT @ - .line3 == 15
.line4:
	next "thick iron sheets"
ASSERT @ - .line4 == 18
.line5:
	next "as if they were@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "silk. It flies at"
ASSERT @ - .line6 == 17
.line7:
	next "over 60 miles per"
ASSERT @ - .line7 == 18
.line8:
	next "hour.@"
ASSERT @ - .line8 == 7
