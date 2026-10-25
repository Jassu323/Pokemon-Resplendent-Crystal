	db "Rock Head@"
	dw 200, 928

.page1::
.line0:
	db "Although it is"
ASSERT @ - .line0 == 14
.line1:
	next "small, this"
ASSERT @ - .line1 == 12
.line2:
	next "Pokémon is very@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "powerful because"
ASSERT @ - .line3 == 16
.line4:
	next "its body is a"
ASSERT @ - .line4 == 14
.line5:
	next "bundle of muscles.@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "It launches"
ASSERT @ - .line6 == 11
.line7:
	next "head-butts with"
ASSERT @ - .line7 == 16
.line8:
	next "its ironlike@"
ASSERT @ - .line8 == 14

.page4::
.line9:
	db "skull.@"
ASSERT @ - .line9 == 7
