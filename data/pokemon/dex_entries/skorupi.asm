	db "Scorpion@"
	dw 207, 265

.page1::
.line0:
	db "As soon as the"
ASSERT @ - .line0 == 14
.line1:
	next "tail claws close,"
ASSERT @ - .line1 == 18
.line2:
	next "its needle tips@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "secrete poison. It"
ASSERT @ - .line3 == 18
.line4:
	next "can survive a year"
ASSERT @ - .line4 == 19
.line5:
	next "without food.@"
ASSERT @ - .line5 == 15
