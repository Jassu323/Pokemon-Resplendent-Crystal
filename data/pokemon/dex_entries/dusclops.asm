	db "Beckon@"
	dw 503, 675

.page1::
.line0:
	db "It is thought that"
ASSERT @ - .line0 == 18
.line1:
	next "its body is hollow"
ASSERT @ - .line1 == 19
.line2:
	next "with only a@"
ASSERT @ - .line2 == 13

.page2::
.line3:
	db "spectral ball of"
ASSERT @ - .line3 == 16
.line4:
	next "fire burning"
ASSERT @ - .line4 == 13
.line5:
	next "inside. However,@"
ASSERT @ - .line5 == 18

.page3::
.line6:
	db "no one has been"
ASSERT @ - .line6 == 15
.line7:
	next "able to confirm"
ASSERT @ - .line7 == 16
.line8:
	next "this theory as@"
ASSERT @ - .line8 == 16

.page4::
.line9:
	db "fact.@"
ASSERT @ - .line9 == 6
