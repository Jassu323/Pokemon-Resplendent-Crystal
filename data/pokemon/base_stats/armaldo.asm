	db 0 ; species ID placeholder

	db  75, 125, 100,  45,  70,  80
	;   hp  atk  def  spd  sat  sdf

	db ROCK, BUG ; type
	db 45 ; catch rate
	db 199 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_F12_5 ; gender ratio
	db 100 ; unknown 1
	db 30 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/armaldo/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_MEDIUM_SLOW ; growth rate
	dn EGG_WATER_3, EGG_WATER_3 ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
