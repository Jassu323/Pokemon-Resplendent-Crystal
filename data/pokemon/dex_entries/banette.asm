	db "Marionette@"
	dw 307, 276

.page1::
.line0:
	db "An abandoned plush"
ASSERT @ - .line0 == 18
.line1:
	next "doll became this"
ASSERT @ - .line1 == 17
.line2:
	next "Pokémon. They are@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "said to live in"
ASSERT @ - .line3 == 15
.line4:
	next "garbage dumps and"
ASSERT @ - .line4 == 18
.line5:
	next "wander about in@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "search of the"
ASSERT @ - .line6 == 13
.line7:
	next "children that"
ASSERT @ - .line7 == 14
.line8:
	next "threw them away.@"
ASSERT @ - .line8 == 18
