	db "Sky High@"
	dw 2300, 4552

.page1::
.line0:
	db "A Pokémon that"
ASSERT @ - .line0 == 14
.line1:
	next "flies endlessly in"
ASSERT @ - .line1 == 19
.line2:
	next "the ozone layer.@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "It is said it"
ASSERT @ - .line3 == 13
.line4:
	next "would descend to"
ASSERT @ - .line4 == 17
.line5:
	next "the ground if@"
ASSERT @ - .line5 == 15

.page3::
.line6:
	db "Kyogre and Groudon"
ASSERT @ - .line6 == 18
.line7:
	next "were to fight.@"
ASSERT @ - .line7 == 16
