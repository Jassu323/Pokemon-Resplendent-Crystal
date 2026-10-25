	db "Mushroom@"
	dw 311, 864

.page1::
.line0:
	db "It scatters spores"
ASSERT @ - .line0 == 18
.line1:
	next "from holes in the"
ASSERT @ - .line1 == 18
.line2:
	next "cap on its head.@"
ASSERT @ - .line2 == 18

.page2::
.line3:
	db "It loves warm and"
ASSERT @ - .line3 == 17
.line4:
	next "humid climates. It"
ASSERT @ - .line4 == 19
.line5:
	next "feeds on trees and@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "plants in fields"
ASSERT @ - .line6 == 16
.line7:
	next "and forests.@"
ASSERT @ - .line7 == 14
