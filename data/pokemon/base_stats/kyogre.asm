	db 0 ; species ID placeholder

	db 100, 100,  90,  90, 150, 140
	;   hp  atk  def  spd  sat  sdf

	db WATER, WATER ; type
	db 5 ; catch rate
	db 218 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_UNKNOWN ; gender ratio
	db 0 ; unknown 1
	db 120 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/kyogre/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_SLOW ; growth rate
	dn EGG_NONE, EGG_NONE ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
