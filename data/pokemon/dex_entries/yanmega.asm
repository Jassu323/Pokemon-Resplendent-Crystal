	db "Ogre Darner@"
	dw 603, 1135

.page1::
.line0:
	db "Its jaw power is"
ASSERT @ - .line0 == 16
.line1:
	next "incredible. It is"
ASSERT @ - .line1 == 18
.line2:
	next "adept at biting@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "apart foes while"
ASSERT @ - .line3 == 16
.line4:
	next "flying by at high"
ASSERT @ - .line4 == 18
.line5:
	next "speed.@"
ASSERT @ - .line5 == 8
