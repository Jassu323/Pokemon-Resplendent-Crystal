	db "Rabbit@"
	dw 104, 121

.page1::
.line0:
	db "Its ears are"
ASSERT @ - .line0 == 12
.line1:
	next "always rolled up."
ASSERT @ - .line1 == 18
.line2:
	next "They can be@"
ASSERT @ - .line2 == 13

.page2::
.line3:
	db "forcefully"
ASSERT @ - .line3 == 10
.line4:
	next "extended to"
ASSERT @ - .line4 == 12
.line5:
	next "shatter even a@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "large boulder.@"
ASSERT @ - .line6 == 15
