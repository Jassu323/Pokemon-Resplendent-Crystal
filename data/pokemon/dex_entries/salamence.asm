	db "Dragon@"
	dw 411, 2262

.page1::
.line0:
	db "After many long"
ASSERT @ - .line0 == 15
.line1:
	next "years, its"
ASSERT @ - .line1 == 11
.line2:
	next "cellular structure@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "underwent a sudden"
ASSERT @ - .line3 == 18
.line4:
	next "mutation to grow"
ASSERT @ - .line4 == 17
.line5:
	next "wings. When@"
ASSERT @ - .line5 == 13

.page3::
.line6:
	db "angered, it loses"
ASSERT @ - .line6 == 17
.line7:
	next "all thought and"
ASSERT @ - .line7 == 16
.line8:
	next "rampages out of@"
ASSERT @ - .line8 == 17

.page4::
.line9:
	db "control.@"
ASSERT @ - .line9 == 9
