	db 0 ; species ID placeholder

	db  80,  50, 100,  50, 100, 200
	;   hp  atk  def  spd  sat  sdf

	db ICE, ICE ; type
	db 3 ; catch rate
	db 216 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_UNKNOWN ; gender ratio
	db 35 ; unknown 1
	db 80 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/regice/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_SLOW ; growth rate
	dn EGG_NONE, EGG_NONE ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
