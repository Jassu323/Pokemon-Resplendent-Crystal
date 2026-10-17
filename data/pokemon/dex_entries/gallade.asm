	db "Blade@"
	dw 503, 1146

.page1::
.line0:
	db "When trying to"
ASSERT @ - .line0 == 14
.line1:
	next "protect someone,"
ASSERT @ - .line1 == 17
.line2:
	next "it extends its@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "elbows as if they"
ASSERT @ - .line3 == 17
.line4:
	next "were swords and"
ASSERT @ - .line4 == 16
.line5:
	next "fights savagely.@"
ASSERT @ - .line5 == 18
