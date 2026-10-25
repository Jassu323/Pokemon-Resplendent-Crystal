"""Export the host's synthetic starting state for an independent core comparison.

Does not write the ROM or read/load any user save. Uncaptured memory retains the
host fixture's values; this is explicitly not a complete emulator save state.
"""
import argparse
from pathlib import Path
import struct
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from dex_timing.assets import Repository
from dex_timing.followup import read_stops
from dex_timing.model import Profile
from dex_timing.probes.boundary_sensitivity import DeferredClock, DeferredReplay


def fixture_bytes(replay, stops, origin, div_low, zero_scroll_shadows=False):
    cpu=replay.cpu
    memory=bytearray(cpu.ram)
    # VBlank copies these uncaptured shadows into the captured hardware
    # configuration. Retaining zeroed shadows would change the test's PPU.
    if not zero_scroll_shadows:
        hardware=stops[0]['capture']['hardware']
        for name, value in (('hSCX', hardware.get(str(0xff43),5)),
                            ('hWX', hardware.get(str(0xff4b),167)), ('hWY', 0)):
            memory[cpu.symbols[name][1]]=value
    header=[origin,cpu.r[7]*256+cpu.f,*(cpu.pair(i) for i in range(3)),cpu.sp,cpu.pc,cpu.bank,
            cpu.ram[0xff70],cpu.ram[0xff4f],stops[0]['div']*256+div_low,
            stops[0]['tima'],56,6,int(stops[0]['capture']['hardware'][str(0xff0f)])&15,15]
    assert len(header)==16
    return b'DEXCORE1'+struct.pack('<16I', *header)+memory+b''.join(cpu.wram)+b''.join(cpu.vram)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--phase', type=int, default=658)
    parser.add_argument('--div-low', type=int, default=16)
    parser.add_argument('--zero-scroll-shadows', action='store_true',
                        help='Negative control: retain zeroed synthetic scroll/window shadows')
    args=parser.parse_args()
    repo=Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym')
    if repo.hashes['rom_sha256']!='7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f':
        parser.error('Core probe addresses require the captured ROM')
    stops=read_stops((ROOT/'tools/dex_timing/fixtures/luxray_exact_followup.txt').read_text(), repo.symbols)
    profile=Profile(hblank_dot=257, audio_phase_t=args.phase, audio_played_at_publication=4)
    with patch('dex_timing.replay.ReplayClock', DeferredClock):
        replay=DeferredReplay(repo, repo.load(['luxray'])[0], stops, profile, 606, args.div_low)
    payload=fixture_bytes(replay, stops, 606, args.div_low, args.zero_scroll_shadows)
    Path(args.output).write_bytes(payload)
    print(f'Exported synthetic fixture: {len(payload)} bytes; ROM unchanged')


if __name__=='__main__':
    main()
