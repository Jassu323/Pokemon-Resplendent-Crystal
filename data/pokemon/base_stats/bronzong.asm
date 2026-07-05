	db 0 ; species ID placeholder

	db  67,  89, 116,  33,  79, 116
	;   hp  atk  def  spd  sat  sdf

	db STEEL, PSYCHIC_TYPE ; type
	db 90 ; catch rate
	db 188 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_UNKNOWN ; gender ratio
	db 70 ; base friendship
	db 20 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/bronzong/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_MEDIUM_FAST ; growth rate
	dn EGG_MINERAL, EGG_MINERAL ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
