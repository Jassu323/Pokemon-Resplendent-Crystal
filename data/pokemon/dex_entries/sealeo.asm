	db "Ball Roll@"
	dw 307, 1931

.page1::
.line0:
	db "Sealeo live in"
ASSERT @ - .line0 == 14
.line1:
	next "herds on ice"
ASSERT @ - .line1 == 13
.line2:
	next "floes. Using its@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "powerful flippers,"
ASSERT @ - .line3 == 18
.line4:
	next "it shatters ice."
ASSERT @ - .line4 == 17
.line5:
	next "It dives into the@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "sea to hunt prey"
ASSERT @ - .line6 == 16
.line7:
	next "five times a day.@"
ASSERT @ - .line7 == 19
