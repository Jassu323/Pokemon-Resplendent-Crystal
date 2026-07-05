	db 0 ; species ID placeholder

	db  70, 110,  70,  90, 115,  70
	;   hp  atk  def  spd  sat  sdf

	db FIGHTING, STEEL ; type
	db 45 ; catch rate
	db 204 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_F12_5 ; gender ratio
	db 70 ; base friendship
	db 25 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/lucario/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_MEDIUM_SLOW ; growth rate
	dn EGG_GROUND, EGG_HUMANSHAPE ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
