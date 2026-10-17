	db "Thorn@"
	dw 100, 44

.page1::
.line0:
	db "A Roselia that"
ASSERT @ - .line0 == 14
.line1:
	next "drinks"
ASSERT @ - .line1 == 7
.line2:
	next "nutritionally rich@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "springwater blooms"
ASSERT @ - .line3 == 18
.line4:
	next "with lovely"
ASSERT @ - .line4 == 12
.line5:
	next "flowers. The@"
ASSERT @ - .line5 == 14

.page3::
.line6:
	db "fragrance of its"
ASSERT @ - .line6 == 16
.line7:
	next "flowers has the"
ASSERT @ - .line7 == 16
.line8:
	next "effect of making@"
ASSERT @ - .line8 == 18

.page4::
.line9:
	db "its foes careless.@"
ASSERT @ - .line9 == 19
