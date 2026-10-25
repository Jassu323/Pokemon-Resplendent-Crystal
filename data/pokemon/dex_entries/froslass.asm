	db "Snow Land@"
	dw 403, 586

.page1::
.line0:
	db "It freezes prey by"
ASSERT @ - .line0 == 18
.line1:
	next "blowing its -58"
ASSERT @ - .line1 == 16
.line2:
	next "degrees F breath.@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "It is said to then"
ASSERT @ - .line3 == 18
.line4:
	next "secretly display"
ASSERT @ - .line4 == 17
.line5:
	next "its prey.@"
ASSERT @ - .line5 == 11
