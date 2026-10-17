	db "Clap@"
	dw 207, 871

.page1::
.line0:
	db "It is completely"
ASSERT @ - .line0 == 16
.line1:
	next "covered with"
ASSERT @ - .line1 == 13
.line2:
	next "plushy fur. As a@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "result, it never"
ASSERT @ - .line3 == 16
.line4:
	next "feels the cold"
ASSERT @ - .line4 == 15
.line5:
	next "even when it is@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "rolling about on"
ASSERT @ - .line6 == 16
.line7:
	next "ice floes or"
ASSERT @ - .line7 == 13
.line8:
	next "diving in the sea.@"
ASSERT @ - .line8 == 20
