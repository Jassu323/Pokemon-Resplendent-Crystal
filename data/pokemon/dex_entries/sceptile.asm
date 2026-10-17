	db "Forest@"
	dw 507, 1151

.page1::
.line0:
	db "In the jungle, its"
ASSERT @ - .line0 == 18
.line1:
	next "power is without"
ASSERT @ - .line1 == 17
.line2:
	next "equal. This@"
ASSERT @ - .line2 == 13

.page2::
.line3:
	db "Pokémon carefully"
ASSERT @ - .line3 == 17
.line4:
	next "grows trees and"
ASSERT @ - .line4 == 16
.line5:
	next "plants. It@"
ASSERT @ - .line5 == 12

.page3::
.line6:
	db "regulates its body"
ASSERT @ - .line6 == 18
.line7:
	next "temperature by"
ASSERT @ - .line7 == 15
.line8:
	next "basking in@"
ASSERT @ - .line8 == 12

.page4::
.line9:
	db "sunlight.@"
ASSERT @ - .line9 == 10
