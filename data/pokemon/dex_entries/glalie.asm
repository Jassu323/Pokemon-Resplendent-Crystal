	db "Face@"
	dw 411, 5655

.page1::
.line0:
	db "A Glalie has the"
ASSERT @ - .line0 == 16
.line1:
	next "power to"
ASSERT @ - .line1 == 9
.line2:
	next "instantaneously@"
ASSERT @ - .line2 == 17

.page2::
.line3:
	db "freeze moisture in"
ASSERT @ - .line3 == 18
.line4:
	next "the atmosphere. A"
ASSERT @ - .line4 == 18
.line5:
	next "dazzling cloud of@"
ASSERT @ - .line5 == 19

.page3::
.line6:
	db "diamondlike ice"
ASSERT @ - .line6 == 15
.line7:
	next "crystals forms"
ASSERT @ - .line7 == 15
.line8:
	next "around its body.@"
ASSERT @ - .line8 == 18
