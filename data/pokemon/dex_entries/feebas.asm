	db "Fish@"
	dw 200, 163

.page1::
.line0:
	db "Feebas live in"
ASSERT @ - .line0 == 14
.line1:
	next "ponds that are"
ASSERT @ - .line1 == 15
.line2:
	next "heavily infested@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "with weeds."
ASSERT @ - .line3 == 11
.line4:
	next "Because of its"
ASSERT @ - .line4 == 15
.line5:
	next "hopelessly shabby@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "appearance, it"
ASSERT @ - .line6 == 14
.line7:
	next "seems as if few"
ASSERT @ - .line7 == 16
.line8:
	next "TRAINERS raise it.@"
ASSERT @ - .line8 == 20
