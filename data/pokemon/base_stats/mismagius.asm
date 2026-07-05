	db 0 ; species ID placeholder

	db  60,  60,  60, 105, 105, 105
	;   hp  atk  def  spd  sat  sdf

	db GHOST, GHOST ; type
	db 45 ; catch rate
	db 187 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_F50 ; gender ratio
	db 35 ; base friendship
	db 25 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/mismagius/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_FAST ; growth rate
	dn EGG_INDETERMINATE, EGG_INDETERMINATE ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
