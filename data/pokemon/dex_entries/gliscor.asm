	db "Fang Scorpn@"
	dw 607, 937

.page1::
.line0:
	db "If it succeeds in"
ASSERT @ - .line0 == 17
.line1:
	next "catching even a"
ASSERT @ - .line1 == 16
.line2:
	next "faint breeze@"
ASSERT @ - .line2 == 14

.page2::
.line3:
	db "properly, it can"
ASSERT @ - .line3 == 16
.line4:
	next "circle the globe"
ASSERT @ - .line4 == 17
.line5:
	next "without flapping@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "once.@"
ASSERT @ - .line6 == 6
