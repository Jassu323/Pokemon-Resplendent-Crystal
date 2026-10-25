	db "Drill@"
	dw 710, 6235

.page1::
.line0:
	db "It can launch a"
ASSERT @ - .line0 == 15
.line1:
	next "rock held in its"
ASSERT @ - .line1 == 17
.line2:
	next "hand like a@"
ASSERT @ - .line2 == 13

.page2::
.line3:
	db "missile by"
ASSERT @ - .line3 == 10
.line4:
	next "tightening then"
ASSERT @ - .line4 == 16
.line5:
	next "expanding muscles@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "instantly.@"
ASSERT @ - .line6 == 11
