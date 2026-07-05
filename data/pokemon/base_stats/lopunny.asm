	db 0 ; species ID placeholder

	db  65,  76,  84, 105,  54,  96
	;   hp  atk  def  spd  sat  sdf

	db NORMAL, NORMAL ; type
	db 60 ; catch rate
	db 168 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_F50 ; gender ratio
	db 140 ; base friendship
	db 20 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/lopunny/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_MEDIUM_FAST ; growth rate
	dn EGG_GROUND, EGG_HUMANSHAPE ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
