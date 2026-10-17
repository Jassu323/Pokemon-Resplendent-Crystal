	db "Colossal@"
	dw 1202, 9259

.page1::
.line0:
	db "It is said to have"
ASSERT @ - .line0 == 18
.line1:
	next "made Pokémon that"
ASSERT @ - .line1 == 18
.line2:
	next "look like itself@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "from a special ice"
ASSERT @ - .line3 == 18
.line4:
	next "mountain, rocks,"
ASSERT @ - .line4 == 17
.line5:
	next "and magma.@"
ASSERT @ - .line5 == 12
