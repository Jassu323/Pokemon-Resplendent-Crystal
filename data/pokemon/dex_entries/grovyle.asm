	db "Wood Gecko@"
	dw 211, 476

.page1::
.line0:
	db "Leaves grow out of"
ASSERT @ - .line0 == 18
.line1:
	next "this Pokémon's"
ASSERT @ - .line1 == 14
.line2:
	next "body. They help@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "obscure a Grovyle"
ASSERT @ - .line3 == 17
.line4:
	next "from the eyes of"
ASSERT @ - .line4 == 17
.line5:
	next "its enemies while@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "it is in a thickly"
ASSERT @ - .line6 == 18
.line7:
	next "overgrown forest.@"
ASSERT @ - .line7 == 19
