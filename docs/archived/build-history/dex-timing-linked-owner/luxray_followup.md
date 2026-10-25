# Luxray Five-Stop Follow-Up

Use the existing instrumented ROM. No new build is needed.

ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`

One cold Listing -> Luxray attempt is sufficient initially. No video is needed.
Do not change Description text pages or press navigation buttons during playback.
Capture all five stops in the same attempt; do not restart or change species
between them. If a stop is not reached, break manually and capture that state.

## Breakpoints

Remove the preceding test breakpoint before setting the next one, so each stop
is the first occurrence after the previous stop. Do not set all five at once:
some of these routines also run before publication or on later animation events.

1. Before selecting Luxray, set `breakpoint $77:$5ea5`. Label the dump Publication.
2. While stopped there, replace it with `breakpoint $a0:$6483`, continue, and label the dump Stage Entry.
3. Replace it with `breakpoint $a0:$6282`, continue, and label the dump Producer Entry.
4. Replace it with `breakpoint $0:$047e`, continue, and label the dump Frame Wait.
5. Replace it with `breakpoint $a0:$67fc`, continue, and label the dump First Miss.

## At Every Stop

Capture before continuing:

```text
registers
backtrace
x/27 $0:$c72e
x/139 $0:$c758
x/4 $0:$ff04
print/x [$ff0f]
print/x [$ffff]
print/x [$ff9b]
print/x [$ff44]
print/x [$ff41]
print/x [$ff4f]
print/x [$ff70]
x/6 $0:$ffee
x/8 $4:$dff4
```

## Additional Values at Publication Only

These identify the owner and VBlank branches previously left as fixtures:

```text
x/2 $0:$c6dc
x/1 $0:$cfb2
x/1 $0:$cfbc
x/1 $0:$c727
x/1 $0:$ff9d
x/1 $0:$ff9e
x/1 $0:$ffd8
x/1 $0:$ffc6
print/x [$ff4d]
```

The two bytes at `$c6dc` are the cursor delay/blink counters. `$cfb2` is the text
delay, `$cfbc` the game-timer pause flag, `$c727` the Selected owner state,
`$ff9d/$ff9e` the ROM-bank/VBlank selectors, and `$ffd8` the OAM-update control.
`$ffc6` verifies the short LCD-handler path; KEY1 confirms normal CPU speed.

The goal is to carry one known initial state through Luxray's intervening stage
builds, uploads and waits, then compare its first miss. Existing captures already
establish that it misses event 7/frame 2; this asks why and when at finer precision.
