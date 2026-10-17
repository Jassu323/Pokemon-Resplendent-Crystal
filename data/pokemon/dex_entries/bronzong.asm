	db "Bronze Bell@"
	dw 403, 4123

.page1::
.line0:
	db "It brought rains"
ASSERT @ - .line0 == 16
.line1:
	next "by opening portals"
ASSERT @ - .line1 == 19
.line2:
	next "to another world.@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "It was revered as"
ASSERT @ - .line3 == 17
.line4:
	next "a bringer of"
ASSERT @ - .line4 == 13
.line5:
	next "plentiful@"
ASSERT @ - .line5 == 11

.page3::
.line6:
	db "harvests.@"
ASSERT @ - .line6 == 10
