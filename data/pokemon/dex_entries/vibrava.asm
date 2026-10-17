	db "Vibration@"
	dw 307, 337

.page1::
.line0:
	db "It looses"
ASSERT @ - .line0 == 9
.line1:
	next "ultrasonic waves"
ASSERT @ - .line1 == 17
.line2:
	next "by rubbing its@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "wings together."
ASSERT @ - .line3 == 15
.line4:
	next "Since a Vibrava's"
ASSERT @ - .line4 == 17
.line5:
	next "wings are still in@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "the process of"
ASSERT @ - .line6 == 14
.line7:
	next "growing, it can"
ASSERT @ - .line7 == 16
.line8:
	next "only fly short@"
ASSERT @ - .line8 == 16

.page4::
.line9:
	db "distances.@"
ASSERT @ - .line9 == 11
