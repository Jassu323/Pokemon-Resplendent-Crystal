	db "Ruffian@"
	dw 200, 254

.page1::
.line0:
	db "Once it grips prey"
ASSERT @ - .line0 == 18
.line1:
	next "with its large"
ASSERT @ - .line1 == 15
.line2:
	next "pincers, it will@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "never let go, no"
ASSERT @ - .line3 == 16
.line4:
	next "matter what. It is"
ASSERT @ - .line4 == 19
.line5:
	next "a hardy Pokémon@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "that can thrive in"
ASSERT @ - .line6 == 18
.line7:
	next "any environment.@"
ASSERT @ - .line7 == 18
