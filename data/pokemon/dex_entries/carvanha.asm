	db "Savage@"
	dw 207, 459

.page1::
.line0:
	db "Carvanha attack"
ASSERT @ - .line0 == 15
.line1:
	next "ships in swarms,"
ASSERT @ - .line1 == 17
.line2:
	next "making them sink.@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "Although it is"
ASSERT @ - .line3 == 14
.line4:
	next "said to be a very"
ASSERT @ - .line4 == 18
.line5:
	next "vicious Pokémon,@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "it timidly flees"
ASSERT @ - .line6 == 16
.line7:
	next "as soon as it"
ASSERT @ - .line7 == 14
.line8:
	next "finds itself@"
ASSERT @ - .line8 == 14

.page4::
.line9:
	db "alone.@"
ASSERT @ - .line9 == 7
