	db "Clay Doll@"
	dw 411, 2381

.page1::
.line0:
	db "A Claydol sleeps"
ASSERT @ - .line0 == 16
.line1:
	next "while hovering in"
ASSERT @ - .line1 == 18
.line2:
	next "midair. Its arms@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "are separate from"
ASSERT @ - .line3 == 17
.line4:
	next "its body. They are"
ASSERT @ - .line4 == 19
.line5:
	next "kept floating by@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "the Pokémon's"
ASSERT @ - .line6 == 12
.line7:
	next "manipulation of"
ASSERT @ - .line7 == 16
.line8:
	next "psychic power.@"
ASSERT @ - .line8 == 16
