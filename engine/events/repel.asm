DoRepelStep::
	ld a, [wRepelEffect]
	and a
	ret z

	dec a
	ld [wRepelEffect], a
	ret nz

	ld a, [wRepelType]
	ld [wCurItem], a
	ld hl, wNumItems
	call CheckItem
	ld a, BANK(RepelWoreOffScript)
	ld hl, RepelWoreOffScript
	jr nc, .got_script
	ld a, BANK(UseAnotherRepelScript)
	ld hl, UseAnotherRepelScript
.got_script
	call CallScript
	scf
	ret

RepelWoreOffScript::
	opentext
	writetext .RepelWoreOffText
	waitbutton
	closetext
	end

.RepelWoreOffText:
	text_far _RepelWoreOffText
	text_end

UseAnotherRepelScript::
	opentext
	readmem wRepelType
	getitemname STRING_BUFFER_3, USE_SCRIPT_VAR
	writetext .UseAnotherRepelText
	yesorno
	iffalse .done
	callasm DoItemEffect
.done
	closetext
	end

.UseAnotherRepelText:
	text_far _UseAnotherRepelText
	text_end
