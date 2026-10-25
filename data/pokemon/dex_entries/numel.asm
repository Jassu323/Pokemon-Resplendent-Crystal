	db "Numb@"
	dw 204, 529

.page1::
.line0:
	db "A Numel stores"
ASSERT @ - .line0 == 14
.line1:
	next "boiling magma in"
ASSERT @ - .line1 == 17
.line2:
	next "the hump on its@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "back. It is a"
ASSERT @ - .line3 == 13
.line4:
	next "hardy Pokémon that"
ASSERT @ - .line4 == 19
.line5:
	next "can transport a@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "220-pound load. It"
ASSERT @ - .line6 == 18
.line7:
	next "has served humans"
ASSERT @ - .line7 == 18
.line8:
	next "at work since long@"
ASSERT @ - .line8 == 20

.page4::
.line9:
	db "ago.@"
ASSERT @ - .line9 == 5
