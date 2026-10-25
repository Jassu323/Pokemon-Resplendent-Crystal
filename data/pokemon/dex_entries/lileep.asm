	db "Sea Lily@"
	dw 303, 525

.page1::
.line0:
	db "It disguises"
ASSERT @ - .line0 == 12
.line1:
	next "itself as seaweed"
ASSERT @ - .line1 == 18
.line2:
	next "by making its@"
ASSERT @ - .line2 == 15

.page2::
.line3:
	db "tentacles sway."
ASSERT @ - .line3 == 15
.line4:
	next "Unsuspecting prey"
ASSERT @ - .line4 == 18
.line5:
	next "that come too@"
ASSERT @ - .line5 == 15

.page3::
.line6:
	db "close are"
ASSERT @ - .line6 == 9
.line7:
	next "swallowed whole."
ASSERT @ - .line7 == 17
.line8:
	next "It became extinct@"
ASSERT @ - .line8 == 19

.page4::
.line9:
	db "100 million years"
ASSERT @ - .line9 == 17
.line10:
	next "ago.@"
ASSERT @ - .line10 == 6
