	db "Meditate@"
	dw 403, 694

.page1::
.line0:
	db "Through crushingly"
ASSERT @ - .line0 == 18
.line1:
	next "harsh yoga"
ASSERT @ - .line1 == 11
.line2:
	next "training, it@"
ASSERT @ - .line2 == 14

.page2::
.line3:
	db "gained the power"
ASSERT @ - .line3 == 16
.line4:
	next "to foretell its"
ASSERT @ - .line4 == 16
.line5:
	next "foe's actions. It@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "battles with"
ASSERT @ - .line6 == 12
.line7:
	next "elegant, dance-"
ASSERT @ - .line7 == 16
.line8:
	next "like movement.@"
ASSERT @ - .line8 == 16
