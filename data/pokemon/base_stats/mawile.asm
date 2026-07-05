	db 0 ; species ID placeholder

	db  50,  85,  85,  50,  55,  55
	;   hp  atk  def  spd  sat  sdf

	db STEEL, FAIRY ; type
	db 45 ; catch rate
	db 98 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_F50 ; gender ratio
	db 100 ; unknown 1
	db 20 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/mawile/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_FAST ; growth rate
	dn EGG_FAIRY, EGG_GROUND ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
