	db 0 ; species ID placeholder

	db  70,  90, 110,  95,  60,  75
	;   hp  atk  def  spd  sat  sdf

	db POISON, DARK ; type
	db 45 ; catch rate
	db 204 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_F50 ; gender ratio
	db 70 ; base friendship
	db 20 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/drapion/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_SLOW ; growth rate
	dn EGG_BUG, EGG_WATER_3 ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
