	db 0 ; species ID placeholder

	db  95,  60,  79,  81, 100, 125
	;   hp  atk  def  spd  sat  sdf

	db WATER, FAIRY ; type
	db 60 ; catch rate
	db 213 ; base exp
	db NO_ITEM, NO_ITEM ; items
	db GENDER_F50 ; gender ratio
	db 100 ; unknown 1
	db 20 ; step cycles to hatch
	db 5 ; unknown 2
	INCBIN "gfx/pokemon/milotic/front.dimensions"
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_MEDIUM_SLOW ; growth rate
	dn EGG_WATER_1, EGG_DRAGON ; egg groups

	; tm/hm learnset
	tmhm REST
	; end
