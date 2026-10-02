# Focused Weavile Startup Capture

Purpose: establish the actual timer phase and locate the remaining time between
first map publication and the first production call. Do not expand to additional
species yet. One cold Listing -> Weavile attempt is sufficient for this check.

No new ROM or runtime instrumentation is needed. Both the workspace ROM and the
SameBoy Games copy still have SHA-256:
`7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`.

Keep the normal-speed build. Do not change Description pages during playback.
Temporarily remove other breakpoints that would interrupt this sequence. Add
only one of the following breakpoints at a time; remove the previous one before
continuing. Repeat the same cold-entry procedure as the existing recordings.

## Stops

1. Before selecting Weavile, set `breakpoint $77:$5ea5`. This is the first
   frontpic-map publication after its deadline check, before the map transfer.
   Label this dump **Publication**.
2. While paused there, replace it with `breakpoint $a0:$6483` and continue.
   This is entry to preparing the next animation stage. Label it **Stage Entry**.
3. Replace it with `breakpoint $a0:$6282` and continue. This is the producer
   function entry following that stage build. Label it **Producer Entry**.
4. Replace it with `breakpoint $0:$047e` and continue. This is the next
   `DelayFrame` wait, after production and the mainline commit check.
   Label it **Frame Wait**.
5. Replace it with `breakpoint $a0:$67fc` and continue. Capture the first
   underrun as before, labeled **First Miss**. If no stop occurs, let the
   animation finish, break manually, and label that explicitly instead.

## Same Outputs At Every Stop

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
x/6 $0:$ffee
x/8 $4:$dff4
```

The timer registers and IF/IE establish which audio/LCD requests are pending,
rather than assuming a fresh timer period at publication. The three following
stops separate the refill/owner prefix, stage construction, and producer/return
work. The existing first-miss capture then checks whether the service-call gap
is reproduced. This requires no video, extra encounters, or full suite rerun.
