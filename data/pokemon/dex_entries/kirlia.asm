	db "Emotion@"
	dw 207, 445

.page1::
.line0:
	db "A Kirlia has the"
ASSERT @ - .line0 == 16
.line1:
	next "psychic power to"
ASSERT @ - .line1 == 17
.line2:
	next "create a rip in@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "the dimensions and"
ASSERT @ - .line3 == 18
.line4:
	next "see into the"
ASSERT @ - .line4 == 13
.line5:
	next "future. It is said@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "to dance with"
ASSERT @ - .line6 == 13
.line7:
	next "pleasure on sunny"
ASSERT @ - .line7 == 18
.line8:
	next "mornings.@"
ASSERT @ - .line8 == 11
