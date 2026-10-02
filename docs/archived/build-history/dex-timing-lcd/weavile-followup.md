# Weavile Follow-Up: First Miss Explained

Status: focused diagnostic, not cycle-exact calibration. No game or ROM changes.

Capture: `/Users/jakeadams/Downloads/Weavile Follow-Up Capture.txt`.
ROM SHA-256: `7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f`.

## Observed Sequence

| Stop | Display counter | LY | Audio blocks cached | Audio blocks remaining |
|---|---:|---:|---:|---:|
| First map publication | AA, advancing to AB in this ISR | 145 | 28 | 201 |
| Next stage entry | AB | 73 | 33 | 198 |
| First producer entry | AB | 139 | 30 | 195 |
| DelayFrame wait | AC | 0, still VBlank | 30 | 195 |
| First miss | AD | 76 | 30 | 187 |

The LY-zero value at the fourth stop is not visible scanline zero. STAT=$8d
reports mode 1. LY resets to zero during the final physical VBlank line 153.
This matters when calculating elapsed time from a register dump.

Elapsed intervals, constrained by the timer, DIV and scanline observations:

| Interval | Approximate T-cycles | Approximate time |
|---|---:|---:|
| Publication breakpoint to stage entry | 37,504 | 8.942 ms |
| Stage entry to producer entry | 30,144 | 7.187 ms |
| Producer entry to DelayFrame wait | 6,080 | 1.450 ms |
| DelayFrame wait to first miss | 105,408 | 25.131 ms |

These are wall times including interrupts, not isolated routine CPU costs.
Timer-register quantization leaves roughly +/-64 T per interval; startup
alignment and timer reload details are not a cycle-perfect reconstruction.

## Failure Mechanism

The first publication anchors the animation to AB. Event 2, animation frame 2,
is due at AE (+3 display intervals). The dictionary is fully decoded: 128/128
tiles. This stage requires 18 uploads; zero have happened at the first miss.

The first production call enters late in AB and takes the first scheduled idle
action. Its return/commit path reaches DelayFrame after the AC VBlank has
already happened. DelayFrame arms a fresh wait and therefore waits for AD.
The second production call, in AD, consumes the second scheduled idle action.
The upcoming-deadline check sees AE is next and reports the stage unfinished.
The upload action has not yet been reached.

Thus this particular miss is not a slow HDMA transfer, a dictionary shortage,
or an empty sampled-cry cache. It is a call-index schedule falling behind the
display clock, with substantial stage/owner/interrupt work consuming the first
iteration. The cache remains 28-33 blocks at all five stops. Exactly one
eight-block refill occurs before stage entry, none during stage construction,
and another eight-block refill occurs between the frame wait and first miss.

## Host Comparison

The linked publication fixture reaches the first breakpoint 600 T after an
undelayed VBlank entry. TIMA=$fe puts the next overflow about 64-128 T away
there, not a fresh 12,800-T period. LY145 also allows some interrupt-entry
delay. A phase-only sweep of 664-1,044 T in four-T steps covers that wider
uncertainty plus timer-reload latency. The existing corrected model reproduces
event 2/frame 2/+3/0-of-18 in all 96 cases. These phases were bounded by the
capture, not selected to fit a failure. This still does not reconstruct the
complete history of an initially delayed VBlank handler.

Full timing agreement is still incomplete. The existing owner fixture forces
STAT ready, so the four footer VRAM-poll loops never wait. With the measured
timer phase, that fixture reaches stage entry roughly three scanlines early.
A diagnostic instruction-path replay with changing STAT adds real busy polls
and overlaps the observed stage-entry interval for ordinary HBlank lengths.
The added cost comes from executing the existing polling instructions, not an
invented fixed per-species penalty.

This is a concrete missing modeled operation, not yet proof of the precise
per-line PPU history. Extreme short-HBlank profiles can delay those polling
loops much more: a 108-T LCD handler can consume the remaining accessible
window. Such conservative profiles must not be mistaken for the actual PPU
phase in this capture or used to claim an exact replay.

## Next Step

Correct the host owner-loop polling and fine-grained return/wait accounting,
then rerun the existing Weavile and Luxray captures. No further user capture
or video is required for that correction. Do not broaden the species suite
or treat this as universal timing certification yet. The game scheduler and
sampled-cry settings remain unchanged.

Reproduction: `python3 -B build/dex-timing-lcd/followup_analysis.py`.
Detailed observations and phase trials: `weavile-followup-analysis.json`.

Hardware reference: [SameBoy display implementation](https://github.com/LIJI32/SameBoy/blob/master/Core/display.c).
