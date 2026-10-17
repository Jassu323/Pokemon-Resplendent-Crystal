	db "Big Boss@"
	dw 211, 602

.page1::
.line0:
	db "If one utters a"
ASSERT @ - .line0 == 15
.line1:
	next "deep cry, many"
ASSERT @ - .line1 == 15
.line2:
	next "Murkrow gather@"
ASSERT @ - .line2 == 16

.page2::
.line3:
	db "quickly. For this,"
ASSERT @ - .line3 == 18
.line4:
	next "it is called"
ASSERT @ - .line4 == 13
.line5:
	next "'Summoner of@"
ASSERT @ - .line5 == 14

.page3::
.line6:
	db "Night.'@"
ASSERT @ - .line6 == 8
