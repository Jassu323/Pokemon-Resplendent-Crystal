	db "Sharp Claw@"
	dw 307, 750

.page1::
.line0:
	db "Evolution made it"
ASSERT @ - .line0 == 17
.line1:
	next "even more devious."
ASSERT @ - .line1 == 19
.line2:
	next "It communicates by@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "clawing signs in"
ASSERT @ - .line3 == 16
.line4:
	next "boulders.@"
ASSERT @ - .line4 == 11
