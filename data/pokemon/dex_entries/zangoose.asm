	db "Cat Ferret@"
	dw 403, 888

.page1::
.line0:
	db "When it battles,"
ASSERT @ - .line0 == 16
.line1:
	next "it stands on its"
ASSERT @ - .line1 == 17
.line2:
	next "hind legs and@"
ASSERT @ - .line2 == 15

.page2::
.line3:
	db "attacks with its"
ASSERT @ - .line3 == 16
.line4:
	next "sharply clawed"
ASSERT @ - .line4 == 15
.line5:
	next "forelegs. Its fur@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "bristles if it"
ASSERT @ - .line6 == 14
.line7:
	next "encounters any"
ASSERT @ - .line7 == 15
.line8:
	next "Seviper.@"
ASSERT @ - .line8 == 10
