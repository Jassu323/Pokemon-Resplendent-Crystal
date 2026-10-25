	db "Iron Armor@"
	dw 611, 7937

.page1::
.line0:
	db "Its iron horns"
ASSERT @ - .line0 == 14
.line1:
	next "grow longer a"
ASSERT @ - .line1 == 14
.line2:
	next "little at a time.@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "They are used to"
ASSERT @ - .line3 == 16
.line4:
	next "determine the"
ASSERT @ - .line4 == 14
.line5:
	next "Aggron's age. The@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "gouges in its"
ASSERT @ - .line6 == 13
.line7:
	next "armor are worn"
ASSERT @ - .line7 == 15
.line8:
	next "with pride as@"
ASSERT @ - .line8 == 15

.page4::
.line9:
	db "mementos from"
ASSERT @ - .line9 == 13
.line10:
	next "battles.@"
ASSERT @ - .line10 == 10
