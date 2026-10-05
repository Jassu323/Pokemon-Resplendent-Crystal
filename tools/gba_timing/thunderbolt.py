"""Native Thunderbolt comparison fixtures and read-only host captures."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/thunderbolt-comparison-20261004'
EMERALD = OUT / 'emerald'


def symbols():
    data = subprocess.check_output(['/opt/devkitpro/devkitARM/bin/arm-none-eabi-nm', '-n',
                                    str(EMERALD / 'pokeemerald.elf')], text=True)
    result = {}
    for line in data.splitlines():
        parts = line.split()
        if len(parts) == 3:
            result.setdefault(parts[2], int(parts[0], 16))
    # Three translation units have a private Cmd_end. Resolve the one in
    # battle_anim.c, rather than silently tracing an unrelated interpreter.
    result['BattleAnimEnd'] = min(int(p[0],16) for l in data.splitlines()
        if len(p := l.split()) == 3 and p[2] == 'Cmd_end' and int(p[0],16) > result['DoMoveAnim'])
    return result


class Runner:
    def __init__(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        self.log = (folder / 'console.log').open('w')
        self.process = subprocess.Popen([str(OUT / 'mgba/replay'), str(EMERALD / 'pokeemerald.gba')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log, text=True, bufsize=1)
        self.receive()

    def receive(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError('mGBA exited')
            self.log.write(line)
            if line.startswith('{'):
                return json.loads(line)

    def command(self, text):
        self.log.write('> ' + text + '\n'); self.log.flush()
        self.process.stdin.write(text + '\n'); self.process.stdin.flush()
        return self.receive()

    def read(self, addr, n):
        return bytes.fromhex(self.command(f'read {addr:x} {n}')['bytes'])

    def write(self, addr, value, size=4):
        return self.command(f'write {addr:x} {value:x} {size}')

    def close(self):
        self.process.stdin.write('quit\n'); self.process.stdin.flush()
        self.process.wait(timeout=60); self.log.close()


def fixture_side(side):
    sy = symbols()
    folder = OUT / 'emerald-fixtures' / side
    r = Runner(folder)
    try:
        r.command('run 240 0')
        # Native new-game initialization establishes save pointers, map data,
        # interrupts, heap and audio before entering a regular wild battle.
        r.write(sy['gMain'] + 4, sy['CB2_NewGame'] | 1)
        r.command('run 240 0')
        r.command(f'until {sy["WaitForVBlank"]:x} 30')
        for owner, party in [('player', sy['gPlayerParty']), ('foe', sy['gEnemyParty'])]:
            result = r.command(f'call {sy["CreateMon"]:x} {party:x} 19 32 1f 1 0 0 0')
            assert result['ok'], result  # Pikachu, level 50, fixed personality.
        r.write(sy['gPlayerPartyCount'], 1, 1)
        r.write(sy['gEnemyPartyCount'], 1, 1)
        for owner, party in [('player', sy['gPlayerParty']), ('foe', sy['gEnemyParty'])]:
            for slot in range(4):
                move = 85 if side == owner else 150
                r.command(f'call {sy["SetMonMoveSlot"]:x} {party:x} {move:x} {slot:x}')
        r.write(sy['gBattleTypeFlags'], 0)
        r.write(sy['gMain'], 0)
        r.write(sy['gMain'] + 4, sy['CB2_InitBattle'] | 1)
        r.write(sy['gMain'] + 0x438, 0, 1)
        r.command('run 700 0')
        for _ in range(40):
            pointer = int.from_bytes(r.read(sy['gBattlerControllerFuncs'], 4), 'little')
            if pointer == sy['HandleInputChooseAction'] | 1:
                break
            r.command('run 1 1'); r.command('run 30 0')
        else:
            r.command(f'image {folder / "failure.ppm"}')
            r.command(f'save {folder / "failure.state"}')
            raise RuntimeError('Did not reach the native battle action menu')
        r.command(f'image {folder / "battle.ppm"}')
        r.command(f'save {folder / "battle.state"}')
    finally:
        r.close()


def fixture():
    with ProcessPoolExecutor(max_workers=2) as pool:
        list(pool.map(fixture_side, ['player', 'foe']))


def emerald_job(item):
    side, phase, traced = item
    sy = symbols()
    folder = OUT / 'gba' / f'{side}-q{phase}-{"trace" if traced else "plain"}'
    r = Runner(folder)
    try:
        r.command(f'load {OUT / "emerald-fixtures" / side / "battle.state"}')
        r.command(f'symbols {sy["gSprites"]:x} {sy["gTasks"]:x} {sy["gMain"]:x} {sy["sBattleAnimScriptPtr"]:x} {sy["gAnimScriptActive"]:x}')
        r.command(f'owners {sy["gBattleAnimAttacker"]:x} {sy["gBattleAnimTarget"]:x}')
        points = ['DoMoveAnim', 'RunAnimScriptCommand', 'WaitAnimFrameCount', 'BattleMainCB2',
                  'BuildOamBuffer', 'LoadOam', 'TransferPlttBuffer', 'AnimTask_ElectricBolt',
                  'AnimTask_ElectricBolt_Step', 'AnimElectricBoltSegment', 'AnimThunderboltOrb',
                  'AnimThunderboltOrb_Step', 'AnimSparkElectricityFlashing', 'AnimSparkElectricityFlashing_Step',
                  'BattleAnimEnd', 'PlaySE', 'PlaySE12WithPanning', 'PlaySE1WithPanning', 'PlaySE2WithPanning']
        if traced:
            for name in points:
                if name in sy:
                    r.command(f'point {sy[name]:x} {name}')
        r.command(f'events {folder / "events.jsonl"}')
        start = r.command(f'video {folder / "video.rgb"}') if phase == 0 and traced else r.command('run 0 0')
        if phase == 0 and traced:
            r.command(f'audio {folder / "audio.raw"}')
        r.command('run 1 1'); r.command(f'run {8 + phase} 0')
        r.command('run 1 1'); r.command('run 1200 0')
        r.command('video -'); r.command('audio -'); r.command('events -')
        r.command(f'image {folder / "final.ppm"}')
        result = dict(side=side, phase=phase, traced=traced, capture_start=start, final=r.command('run 0 0'))
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
    finally:
        r.close()


def emerald():
    with ProcessPoolExecutor(max_workers=12) as pool:
        list(pool.map(emerald_job, [(s, q, t) for s in ['player','foe'] for q in [0,1,2,3] for t in [True,False]]))


def crystal_prepare(variant):
    from tools.dex_timing import global_animation_timing as timing, global_speed as speed
    from tools.dex_timing import performance, shared_menu_regression as menu
    from tools.dex_timing.assets import Repository
    cfg = speed.configuration(variant)
    cfg.update(variant=variant, output_root=str(OUT / 'crystal'), capture_images=True,
               capture_moves=['THUNDERBOLT'])
    repo = Repository(Path(cfg['root']), Path(cfg['rom']), Path(cfg['sym']))
    folder = OUT / 'observers' / variant
    performance.core(repo, folder, dict(timing.POINTS, sound_cue=('PlaySFX', False),
                                       stereo_cue=('PlayStereoSFX',False)))
    header = folder / 'performance-symbols.h'
    with header.open('a') as stream:
        for label in ['wBattleAnimAddress', 'wBattleAnimDelay', 'wBattleAnimParam', 'wActiveAnimObjects']:
            stream.write(f'#define S_{label} {repo.symbols[label][1]}\n')
    cfg['core'] = str(menu.compile_observer(repo, Path.home() / 'Documents/GitHub/SameBoy', folder,
        ('-DDEX_PERFORMANCE_TRACE', '-DDEX_BACKLOG_REVALIDATION_TRACE', '-DDEX_BATTLE_TIMING_TRACE',
         '-DDEX_THUNDERBOLT_OBJECT_TRACE', f'-DDEX_PERFORMANCE_SYMBOLS="{header.resolve()}"')))
    cfg['battery'] = str(speed.BASE / 'menus' / variant / 'battle/private.sav')
    cfg['fixtures'] = {'THUNDERBOLT': {s: str(speed.BASE / 'moves' / variant / f'thunderbolt-{s}.s0')
                                    for s in ['player', 'foe']}}
    return cfg


def crystal():
    from tools.dex_timing import global_speed as speed
    from tools.pokedex_info_assets import constants
    index = constants(ROOT / 'constants/move_constants.asm')['THUNDERBOLT']
    configs = [crystal_prepare(v) for v in ['production', 'final']]
    tasks = [(c, 'THUNDERBOLT', index, s, q) for c in configs for s in ['player', 'foe']
             for q in [0, 17556, 35112, 52668]]
    with ProcessPoolExecutor(max_workers=16) as pool:
        for result in pool.map(speed.move_job, tasks):
            print(json.dumps({k: v for k, v in result.items() if k in ['variant','side','quarter','issues']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['fixture', 'crystal', 'emerald'])
    args = parser.parse_args()
    globals()[args.action]()
