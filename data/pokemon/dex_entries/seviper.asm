	db "Fang Snake@"
	dw 810, 1157

.page1::
.line0:
	db "Seviper and"
ASSERT @ - .line0 == 11
.line1:
	next "Zangoose are"
ASSERT @ - .line1 == 13
.line2:
	next "eternal rivals. It@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "counters a"
ASSERT @ - .line3 == 10
.line4:
	next "Zangoose's dazzling"
ASSERT @ - .line4 == 19
.line5:
	next "agility with its@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "swordlike tail,"
ASSERT @ - .line6 == 15
.line7:
	next "which also oozes a"
ASSERT @ - .line7 == 19
.line8:
	next "horrible poison.@"
ASSERT @ - .line8 == 18
