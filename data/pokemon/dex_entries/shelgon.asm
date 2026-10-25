	db "Endurance@"
	dw 307, 2436

.page1::
.line0:
	db "It hardly eats"
ASSERT @ - .line0 == 14
.line1:
	next "while it awaits"
ASSERT @ - .line1 == 16
.line2:
	next "evolution. It@"
ASSERT @ - .line2 == 15

.page2::
.line3:
	db "becomes hardier by"
ASSERT @ - .line3 == 18
.line4:
	next "enduring hunger."
ASSERT @ - .line4 == 17
.line5:
	next "Its shell peels@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "off the instant it"
ASSERT @ - .line6 == 18
.line7:
	next "begins to evolve.@"
ASSERT @ - .line7 == 19
