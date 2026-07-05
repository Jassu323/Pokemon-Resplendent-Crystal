	db 0 ; species ID placeholder

	db  60,  52, 168,  30,  47, 138
	;   hp  atk  def  spd  sat  sdf

	db ROCK, STEEL ; type
	db 45 ; catch rate
	db 199 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_F12_5 ; gender ratio
	db 70 ; base friendship
	db 30 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/bastiodon/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_MEDIUM_SLOW ; growth rate
	dn EGG_MONSTER, EGG_MONSTER ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
