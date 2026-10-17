	db "Deceiver@"
	dw 200, 254

.page1::
.line0:
	db "Its giant jaws are"
ASSERT @ - .line0 == 18
.line1:
	next "actually steel"
ASSERT @ - .line1 == 15
.line2:
	next "horns that@"
ASSERT @ - .line2 == 12

.page2::
.line3:
	db "transformed. It"
ASSERT @ - .line3 == 15
.line4:
	next "fools foes into"
ASSERT @ - .line4 == 16
.line5:
	next "complacency with@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "its adorable"
ASSERT @ - .line6 == 12
.line7:
	next "gestures, then"
ASSERT @ - .line7 == 15
.line8:
	next "chomps them with@"
ASSERT @ - .line8 == 18

.page4::
.line9:
	db "its huge jaws.@"
ASSERT @ - .line9 == 15
