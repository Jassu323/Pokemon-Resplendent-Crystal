	db "Iceberg@"
	dw 511, 3858

.page1::
.line0:
	db "Its entire body is"
ASSERT @ - .line0 == 18
.line1:
	next "made of Antarctic"
ASSERT @ - .line1 == 18
.line2:
	next "ice. After@"
ASSERT @ - .line2 == 12

.page2::
.line3:
	db "extensive studies,"
ASSERT @ - .line3 == 18
.line4:
	next "researchers"
ASSERT @ - .line4 == 12
.line5:
	next "believe the ice@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "was formed during"
ASSERT @ - .line6 == 17
.line7:
	next "an ice age.@"
ASSERT @ - .line7 == 13
