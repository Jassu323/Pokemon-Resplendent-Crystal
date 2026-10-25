	db "Toxic Mouth@"
	dw 403, 979

.page1::
.line0:
	db "It has a poison"
ASSERT @ - .line0 == 15
.line1:
	next "sac at its throat."
ASSERT @ - .line1 == 19
.line2:
	next "When it croaks,@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "the stored poison"
ASSERT @ - .line3 == 17
.line4:
	next "is churned for"
ASSERT @ - .line4 == 15
.line5:
	next "greater potency.@"
ASSERT @ - .line5 == 18
