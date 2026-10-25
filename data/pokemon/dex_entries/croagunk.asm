	db "Toxic Mouth@"
	dw 204, 507

.page1::
.line0:
	db "It rarely fights"
ASSERT @ - .line0 == 16
.line1:
	next "fairly, but that"
ASSERT @ - .line1 == 17
.line2:
	next "is strictly to@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "ensure survival."
ASSERT @ - .line3 == 16
.line4:
	next "It is popular as a"
ASSERT @ - .line4 == 19
.line5:
	next "mascot.@"
ASSERT @ - .line5 == 9
