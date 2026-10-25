	db "Frost Tree@"
	dw 303, 1113

.page1::
.line0:
	db "Seemingly curious"
ASSERT @ - .line0 == 17
.line1:
	next "about people, they"
ASSERT @ - .line1 == 19
.line2:
	next "gather around@"
ASSERT @ - .line2 == 15

.page2::
.line3:
	db "footsteps they"
ASSERT @ - .line3 == 14
.line4:
	next "find on snowy"
ASSERT @ - .line4 == 14
.line5:
	next "mountains.@"
ASSERT @ - .line5 == 12
