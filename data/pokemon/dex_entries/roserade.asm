	db "Bouquet@"
	dw 211, 320

.page1::
.line0:
	db "Each of its hands"
ASSERT @ - .line0 == 17
.line1:
	next "contains different"
ASSERT @ - .line1 == 19
.line2:
	next "toxins, but both@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "hands can jab with"
ASSERT @ - .line3 == 18
.line4:
	next "near-fatal power.@"
ASSERT @ - .line4 == 19
