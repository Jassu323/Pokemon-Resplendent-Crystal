	db "Shield@"
	dw 403, 3296

.page1::
.line0:
	db "When they lined up"
ASSERT @ - .line0 == 18
.line1:
	next "side by side, no"
ASSERT @ - .line1 == 17
.line2:
	next "foe could break@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "through. They"
ASSERT @ - .line3 == 13
.line4:
	next "shielded their"
ASSERT @ - .line4 == 15
.line5:
	next "young in that way.@"
ASSERT @ - .line5 == 20
