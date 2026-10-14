SECTION "Budget Committed Exit Mask", ROMX[PROBE_PC], BANK[PROBE_BANK]
BudgetMaskCommit:
    call ClearSprites
    call ClearPalettes
    ; DisableLCD suppresses VBlank; publish white before that can happen.
    jp DelayFrame
BudgetMaskCommitEnd:
