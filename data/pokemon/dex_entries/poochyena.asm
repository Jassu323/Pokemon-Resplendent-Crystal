	db "Bite@"
	dw 108, 300

.page1::
.line0:
	db "It savagely"
ASSERT @ - .line0 == 11
.line1:
	next "threatens foes"
ASSERT @ - .line1 == 15
.line2:
	next "with bared fangs.@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "It chases after"
ASSERT @ - .line3 == 15
.line4:
	next "fleeing targets"
ASSERT @ - .line4 == 16
.line5:
	next "tenaciously. It@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "turns tail and"
ASSERT @ - .line6 == 14
.line7:
	next "runs, however, if"
ASSERT @ - .line7 == 18
.line8:
	next "the foe strikes@"
ASSERT @ - .line8 == 17

.page4::
.line9:
	db "back.@"
ASSERT @ - .line9 == 6
