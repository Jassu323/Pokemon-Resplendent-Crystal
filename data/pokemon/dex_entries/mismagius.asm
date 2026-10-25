	db "Magical@"
	dw 211, 97

.page1::
.line0:
	db "Its cry sounds"
ASSERT @ - .line0 == 14
.line1:
	next "like an"
ASSERT @ - .line1 == 8
.line2:
	next "incantation. It is@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "said the cry may"
ASSERT @ - .line3 == 16
.line4:
	next "rarely be imbued"
ASSERT @ - .line4 == 17
.line5:
	next "with@"
ASSERT @ - .line5 == 6

.page3::
.line6:
	db "happiness-giving"
ASSERT @ - .line6 == 16
.line7:
	next "power.@"
ASSERT @ - .line7 == 8
