	db "Chick@"
	dw 104, 55

.page1::
.line0:
	db "If attacked, it"
ASSERT @ - .line0 == 15
.line1:
	next "strikes back by"
ASSERT @ - .line1 == 16
.line2:
	next "spitting balls of@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "fire it forms in"
ASSERT @ - .line3 == 16
.line4:
	next "its stomach. A"
ASSERT @ - .line4 == 15
.line5:
	next "Torchic dislikes@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "darkness because"
ASSERT @ - .line6 == 16
.line7:
	next "it can't see its"
ASSERT @ - .line7 == 16
.line8:
	next "surroundings.@"
ASSERT @ - .line8 == 15
