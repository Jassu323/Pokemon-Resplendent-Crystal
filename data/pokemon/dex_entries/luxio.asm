	db "Spark@"
	dw 211, 672

.page1::
.line0:
	db "Strong electricity"
ASSERT @ - .line0 == 18
.line1:
	next "courses through"
ASSERT @ - .line1 == 16
.line2:
	next "the tips of its@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "sharp claws. A"
ASSERT @ - .line3 == 14
.line4:
	next "light scratch"
ASSERT @ - .line4 == 14
.line5:
	next "causes fainting in@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "foes.@"
ASSERT @ - .line6 == 6
