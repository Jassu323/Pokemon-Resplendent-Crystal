	db "Feeling@"
	dw 104, 146

.page1::
.line0:
	db "A Ralts has the"
ASSERT @ - .line0 == 15
.line1:
	next "power to sense the"
ASSERT @ - .line1 == 19
.line2:
	next "emotions of people@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "and Pokémon with"
ASSERT @ - .line3 == 16
.line4:
	next "the horns on its"
ASSERT @ - .line4 == 17
.line5:
	next "head. It takes@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "cover if it senses"
ASSERT @ - .line6 == 18
.line7:
	next "any hostility.@"
ASSERT @ - .line7 == 16
