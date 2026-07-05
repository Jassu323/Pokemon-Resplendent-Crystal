; Source copy used to initialize wSampledCryMinMax2BitLevels in WRAMX4.
; The decoder reads the WRAMX4 copy so sampled payload banks can stay mapped.
MinMax2BitLevels::
for minlevel, 0, 16
	for maxlevel, 0, 16
		if maxlevel >= minlevel
			db minlevel, minlevel + (((maxlevel - minlevel) + 1) / 3), minlevel + (((maxlevel - minlevel) * 2 + 1) / 3), maxlevel
		else
			db minlevel, minlevel, minlevel, minlevel
		endc
	endr
endr
MinMax2BitLevelsEnd:
	assert MinMax2BitLevelsEnd - MinMax2BitLevels == SAMPLED_CRY_MINMAX2_BIT_LEVELS_SIZE
