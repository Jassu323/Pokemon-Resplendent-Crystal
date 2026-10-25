	db "Puppet@"
	dw 200, 51

.page1::
.line0:
	db "This Pokémon roams"
ASSERT @ - .line0 == 18
.line1:
	next "about deep in the"
ASSERT @ - .line1 == 18
.line2:
	next "night seeking such@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "negative emotions"
ASSERT @ - .line3 == 17
.line4:
	next "as grudges and"
ASSERT @ - .line4 == 15
.line5:
	next "envy. It retreats@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "to its nest when"
ASSERT @ - .line6 == 16
.line7:
	next "the sun begins to"
ASSERT @ - .line7 == 18
.line8:
	next "rise.@"
ASSERT @ - .line8 == 7
