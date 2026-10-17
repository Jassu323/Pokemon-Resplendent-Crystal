	db "Water Bird@"
	dw 311, 617

.page1::
.line0:
	db "It skims the tops"
ASSERT @ - .line0 == 17
.line1:
	next "of waves as it"
ASSERT @ - .line1 == 15
.line2:
	next "flies. When it@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "spots prey, it"
ASSERT @ - .line3 == 14
.line4:
	next "uses its large"
ASSERT @ - .line4 == 15
.line5:
	next "beak to scoop up@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "the victim with"
ASSERT @ - .line6 == 15
.line7:
	next "water. It protects"
ASSERT @ - .line7 == 19
.line8:
	next "its eggs in its@"
ASSERT @ - .line8 == 17

.page4::
.line9:
	db "beak.@"
ASSERT @ - .line9 == 6
