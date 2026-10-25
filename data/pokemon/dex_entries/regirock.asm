	db "Rock Peak@"
	dw 507, 5071

.page1::
.line0:
	db "A Pokémon that is"
ASSERT @ - .line0 == 17
.line1:
	next "made entirely of"
ASSERT @ - .line1 == 17
.line2:
	next "rocks and@"
ASSERT @ - .line2 == 11

.page2::
.line3:
	db "boulders. If parts"
ASSERT @ - .line3 == 18
.line4:
	next "of its body chip"
ASSERT @ - .line4 == 17
.line5:
	next "off in battle,@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "Regirock repairs"
ASSERT @ - .line6 == 16
.line7:
	next "itself by adding"
ASSERT @ - .line7 == 17
.line8:
	next "new rocks.@"
ASSERT @ - .line8 == 12
