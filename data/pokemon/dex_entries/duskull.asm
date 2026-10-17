	db "Requiem@"
	dw 207, 331

.page1::
.line0:
	db "A glare from its"
ASSERT @ - .line0 == 16
.line1:
	next "single scarlet eye"
ASSERT @ - .line1 == 19
.line2:
	next "makes even burly@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "grown-ups freeze"
ASSERT @ - .line3 == 16
.line4:
	next "in utter fear. It"
ASSERT @ - .line4 == 18
.line5:
	next "is a nocturnal@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "Pokémon that roams"
ASSERT @ - .line6 == 18
.line7:
	next "about under the"
ASSERT @ - .line7 == 16
.line8:
	next "cloak of darkness.@"
ASSERT @ - .line8 == 20
