; Compatibility stubs for removed Mobile System GB battle/menu code.

_LinkBattleSendReceiveAction:
	call .StageForSend
	ld [wLinkBattleSentAction], a
	vc_hook Wireless_start_exchange
	farcall PlaceWaitingText
	call .LinkBattle_SendReceiveAction
	ret

.StageForSend:
	ld a, [wBattlePlayerAction]
	and a ; BATTLEPLAYERACTION_USEMOVE?
	jr nz, .switch
	ld a, [wCurPlayerMove]
	call GetMoveIndexFromID
	ld b, BATTLEACTION_STRUGGLE
	ld a, h
	if HIGH(STRUGGLE)
		cp HIGH(STRUGGLE)
	else
		and a
	endc
	jr nz, .not_struggle
	ld a, l
	cp LOW(STRUGGLE)
	jr z, .struggle
.not_struggle
	ld b, BATTLEACTION_SKIPTURN
	cp $ff
	jr z, .struggle
	ld a, [wCurMoveNum]
	jr .use_move

.switch
	ld a, [wCurPartyMon]
	add BATTLEACTION_SWITCH1
	jr .use_move

.struggle
	ld a, b

.use_move
	and $0f
	ret

.LinkBattle_SendReceiveAction:
	ld a, [wLinkBattleSentAction]
	ld [wPlayerLinkAction], a
	ld a, $ff
	ld [wOtherPlayerLinkAction], a
.waiting
	call LinkTransfer
	call DelayFrame
	ld a, [wOtherPlayerLinkAction]
	inc a
	jr z, .waiting

	vc_hook Wireless_end_exchange
	vc_patch Wireless_net_delay_3
if DEF(_CRYSTAL_VC)
	ld b, 26
else
	ld b, 10
endc
	vc_patch_end
.receive
	call DelayFrame
	call LinkTransfer
	dec b
	jr nz, .receive

	vc_hook Wireless_start_send_zero_bytes
	vc_patch Wireless_net_delay_4
if DEF(_CRYSTAL_VC)
	ld b, 26
else
	ld b, 10
endc
	vc_patch_end
.acknowledge
	call DelayFrame
	call LinkDataReceived
	dec b
	jr nz, .acknowledge

	vc_hook Wireless_end_send_zero_bytes
	ld a, [wOtherPlayerLinkAction]
	ld [wBattleAction], a
	ret

Function10032e:
	ret

Function100337:
AdvanceMobileInactivityTimerAndCheckExpired:
Function100dc0:
	xor a
	ret

StartMobileInactivityTimer:
	xor a
	ld [wMobileInactivityTimerMinutes], a
	ld [wMobileInactivityTimerSeconds], a
	ld [wMobileInactivityTimerFrames], a
	ret

Function100da5:
Mobile_SetOverworldDelay:
	ret

Function100dd8:
MobileComms_CheckInactivityTimer:
Mobile_LoadBattleMenu:
	xor a
	ld [wcd2b], a
	ret

Mobile_MoveSelectionScreen:
Mobile_PartyMenuSelect:
MobileBattleMonMenu:
	scf
	ret

Function1011f1:
Function101220:
	xor a
	ld [wLinkMode], a
	ld [wScriptVar], a
	ret

Function101225:
Function101231:
Function102142:
Function103780:
Function1037c2:
Function1037eb:
	xor a
	ld [wScriptVar], a
	ret

AskMobileOrCable:
	ld a, $2 ; cable
	ld [wScriptVar], a
	ret

Mobile_SelectThreeMons:
	xor a
	ld [wScriptVar], a
	ret

Function10383c:
	ld a, TRUE
	ld [wScriptVar], a
	ret

Function10387b:
	ret
