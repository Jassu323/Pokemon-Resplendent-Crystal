	db "Blaze@"
	dw 603, 1146

.page1::
.line0:
	db "It learns martial"
ASSERT @ - .line0 == 17
.line1:
	next "arts that use"
ASSERT @ - .line1 == 14
.line2:
	next "punches and kicks.@"
ASSERT @ - .line2 == 20

.page2::
.line3:
	db "Every several"
ASSERT @ - .line3 == 13
.line4:
	next "years, its old"
ASSERT @ - .line4 == 15
.line5:
	next "feathers burn off,@"
ASSERT @ - .line5 == 20

.page3::
.line6:
	db "and new, supple"
ASSERT @ - .line6 == 15
.line7:
	next "feathers grow back"
ASSERT @ - .line7 == 19
.line8:
	next "in their place.@"
ASSERT @ - .line8 == 17
