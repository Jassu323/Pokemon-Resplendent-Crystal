	db "Jubilee@"
	dw 411, 838

.page1::
.line0:
	db "It shares many"
ASSERT @ - .line0 == 14
.line1:
	next "blessings with"
ASSERT @ - .line1 == 15
.line2:
	next "people who respect@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "one another's"
ASSERT @ - .line3 == 12
.line4:
	next "rights and avoid"
ASSERT @ - .line4 == 17
.line5:
	next "needless strife.@"
ASSERT @ - .line5 == 18
