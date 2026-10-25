	db "Mystic@"
	dw 607, 1808

.page1::
.line0:
	db "The flapping of"
ASSERT @ - .line0 == 15
.line1:
	next "its wings sounds"
ASSERT @ - .line1 == 17
.line2:
	next "like singing. To@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "prevent detection"
ASSERT @ - .line3 == 17
.line4:
	next "by enemies, it"
ASSERT @ - .line4 == 15
.line5:
	next "hides itself by@"
ASSERT @ - .line5 == 17

.page3::
.line6:
	db "flapping up a"
ASSERT @ - .line6 == 13
.line7:
	next "cloud of desert"
ASSERT @ - .line7 == 16
.line8:
	next "sand.@"
ASSERT @ - .line8 == 7
