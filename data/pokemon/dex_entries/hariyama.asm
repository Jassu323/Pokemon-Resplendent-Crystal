	db "Arm Thrust@"
	dw 707, 5595

.page1::
.line0:
	db "It has the habit"
ASSERT @ - .line0 == 16
.line1:
	next "of challenging"
ASSERT @ - .line1 == 15
.line2:
	next "others without@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "hesitation to"
ASSERT @ - .line3 == 13
.line4:
	next "tests of strength."
ASSERT @ - .line4 == 19
.line5:
	next "It's been known to@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "stand on train"
ASSERT @ - .line6 == 14
.line7:
	next "tracks and stop"
ASSERT @ - .line7 == 16
.line8:
	next "trains using@"
ASSERT @ - .line8 == 14

.page4::
.line9:
	db "forearm thrusts.@"
ASSERT @ - .line9 == 17
