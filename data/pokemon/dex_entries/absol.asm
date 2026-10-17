	db "Disaster@"
	dw 311, 1036

.page1::
.line0:
	db "It sharply senses"
ASSERT @ - .line0 == 17
.line1:
	next "even subtle"
ASSERT @ - .line1 == 12
.line2:
	next "changes in the sky@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "and the land to"
ASSERT @ - .line3 == 15
.line4:
	next "predict natural"
ASSERT @ - .line4 == 16
.line5:
	next "disasters. It is a@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "long-lived Pokémon"
ASSERT @ - .line6 == 18
.line7:
	next "that has a"
ASSERT @ - .line7 == 11
.line8:
	next "life-span of 100@"
ASSERT @ - .line8 == 18

.page4::
.line9:
	db "years.@"
ASSERT @ - .line9 == 7
