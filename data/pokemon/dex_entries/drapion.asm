	db "Scorpion@"
	dw 403, 1356

.page1::
.line0:
	db "Possessing a"
ASSERT @ - .line0 == 12
.line1:
	next "sturdy build, it"
ASSERT @ - .line1 == 17
.line2:
	next "takes pride in its@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "strength, taking"
ASSERT @ - .line3 == 16
.line4:
	next "down foes without"
ASSERT @ - .line4 == 18
.line5:
	next "using toxins.@"
ASSERT @ - .line5 == 15
