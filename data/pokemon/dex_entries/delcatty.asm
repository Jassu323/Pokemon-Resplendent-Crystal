	db "Prim@"
	dw 307, 719

.page1::
.line0:
	db "Rather than"
ASSERT @ - .line0 == 11
.line1:
	next "keeping a"
ASSERT @ - .line1 == 10
.line2:
	next "permanent lair, it@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "habitually seeks"
ASSERT @ - .line3 == 16
.line4:
	next "comfortable spots"
ASSERT @ - .line4 == 18
.line5:
	next "and sleeps there.@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "It is nocturnal"
ASSERT @ - .line6 == 15
.line7:
	next "and becomes active"
ASSERT @ - .line7 == 19
.line8:
	next "at dusk.@"
ASSERT @ - .line8 == 10
