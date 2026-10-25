	db "Snow Hat@"
	dw 204, 370

.page1::
.line0:
	db "They tend to move"
ASSERT @ - .line0 == 17
.line1:
	next "about in groups of"
ASSERT @ - .line1 == 19
.line2:
	next "around five@"
ASSERT @ - .line2 == 13

.page2::
.line3:
	db "Snorunt. In snowy"
ASSERT @ - .line3 == 17
.line4:
	next "regions, it is"
ASSERT @ - .line4 == 15
.line5:
	next "said that when@"
ASSERT @ - .line5 == 16

.page3::
.line6:
	db "they are seen late"
ASSERT @ - .line6 == 18
.line7:
	next "at night, snowfall"
ASSERT @ - .line7 == 19
.line8:
	next "will arrive by@"
ASSERT @ - .line8 == 16

.page4::
.line9:
	db "morning.@"
ASSERT @ - .line9 == 9
