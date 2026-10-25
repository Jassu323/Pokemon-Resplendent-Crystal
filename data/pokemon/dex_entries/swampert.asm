	db "Mud Fish@"
	dw 411, 1806

.page1::
.line0:
	db "If it senses the"
ASSERT @ - .line0 == 16
.line1:
	next "approach of a"
ASSERT @ - .line1 == 14
.line2:
	next "storm and a tidal@"
ASSERT @ - .line2 == 19

.page2::
.line3:
	db "wave, it protects"
ASSERT @ - .line3 == 17
.line4:
	next "its seaside nest"
ASSERT @ - .line4 == 17
.line5:
	next "by piling up@"
ASSERT @ - .line5 == 14

.page3::
.line6:
	db "boulders. It swims"
ASSERT @ - .line6 == 18
.line7:
	next "as fast as a jet"
ASSERT @ - .line7 == 17
.line8:
	next "ski.@"
ASSERT @ - .line8 == 6
