	db "Licking@"
	dw 507, 3086

.page1::
.line0:
	db "The long tongue is"
ASSERT @ - .line0 == 18
.line1:
	next "always soggy with"
ASSERT @ - .line1 == 18
.line2:
	next "slobber. The@"
ASSERT @ - .line2 == 14

.page2::
.line3:
	db "saliva contains a"
ASSERT @ - .line3 == 17
.line4:
	next "solvent that"
ASSERT @ - .line4 == 13
.line5:
	next "causes numbness.@"
ASSERT @ - .line5 == 18
