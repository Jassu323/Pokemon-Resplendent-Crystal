	db "Barnacle@"
	dw 411, 1332

.page1::
.line0:
	db "It drags its heavy"
ASSERT @ - .line0 == 18
.line1:
	next "body along the"
ASSERT @ - .line1 == 15
.line2:
	next "seafloor. It makes@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "its nest in the"
ASSERT @ - .line3 == 15
.line4:
	next "shallows of warm"
ASSERT @ - .line4 == 17
.line5:
	next "seas. Cradily can@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "be seen on beaches"
ASSERT @ - .line6 == 18
.line7:
	next "when the tide goes"
ASSERT @ - .line7 == 19
.line8:
	next "out.@"
ASSERT @ - .line8 == 6
