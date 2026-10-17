	db "Tender@"
	dw 2004, 3571

.page1::
.line0:
	db "It is said to live"
ASSERT @ - .line0 == 18
.line1:
	next "at the bottom of"
ASSERT @ - .line1 == 17
.line2:
	next "large lakes.@"
ASSERT @ - .line2 == 14

.page2::
.line3:
	db "Considered to be"
ASSERT @ - .line3 == 16
.line4:
	next "the most beautiful"
ASSERT @ - .line4 == 19
.line5:
	next "of all Pokémon, it@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "has been depicted"
ASSERT @ - .line6 == 17
.line7:
	next "in paintings and"
ASSERT @ - .line7 == 17
.line8:
	next "statues.@"
ASSERT @ - .line8 == 10
