	db "Plate@"
	dw 411, 1504

.page1::
.line0:
	db "Armaldo usually"
ASSERT @ - .line0 == 15
.line1:
	next "lives on land."
ASSERT @ - .line1 == 15
.line2:
	next "However, when it@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "hunts for prey, it"
ASSERT @ - .line3 == 18
.line4:
	next "dives beneath the"
ASSERT @ - .line4 == 18
.line5:
	next "ocean. It swims@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "around using its"
ASSERT @ - .line6 == 16
.line7:
	next "two large wings.@"
ASSERT @ - .line7 == 18
