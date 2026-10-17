	db "Rogue@"
	dw 307, 723

.page1::
.line0:
	db "A brutish Pokémon"
ASSERT @ - .line0 == 17
.line1:
	next "that loves to"
ASSERT @ - .line1 == 14
.line2:
	next "battle. A veteran@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "Crawdaunt that has"
ASSERT @ - .line3 == 18
.line4:
	next "prevailed in"
ASSERT @ - .line4 == 13
.line5:
	next "hundreds of@"
ASSERT @ - .line5 == 13

.page3::
.line6:
	db "battles has giant"
ASSERT @ - .line6 == 17
.line7:
	next "pincers marked"
ASSERT @ - .line7 == 15
.line8:
	next "with countless@"
ASSERT @ - .line8 == 16

.page4::
.line9:
	db "scars.@"
ASSERT @ - .line9 == 7
