"""Build two private mode-7 Type owners from the retained review prototype."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/dex-types-cursors-20261011'
OUTPUT = ROOT / 'build/dex-types-mode7-20261012'
STEM = 'pokecrystal-dex-types'
PATCHES = ROOT / 'tools/dex_timing/probes'
SOURCES = ('home/lcd.asm','home/vblank.asm','main.asm',
           'engine/pokedex/pokedex_types.asm','engine/pokedex/pokedex_types_mode7.asm',
           'engine/pokedex/pokedex_types_mode7_config.asm','Makefile','audio.asm')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if OUTPUT.exists():
        raise ValueError('Private output already exists')
    OUTPUT.mkdir(parents=True)
    manifest = dict(source=str(BASE), source_rom_sha256=digest(BASE / f'{STEM}.gbc'),
                    source_save_sha256=digest(BASE / f'{STEM}.sav'),
                    production_sha256=digest(ROOT / 'pokecrystal.gbc'))
    rollback = OUTPUT / 'rollback'
    rollback.mkdir()
    for suffix in ('gbc', 'sym', 'map', 'sav'):
        shutil.copy2(BASE / f'{STEM}.{suffix}', rollback / f'{STEM}.{suffix}')
    for variant in ('runtime', 'precomputed'):
        target = OUTPUT / variant
        shutil.copytree(BASE / 'candidate', target / 'candidate')
        shutil.copy2(BASE / f'{STEM}.sav', target / f'{STEM}.sav')
        shutil.copy2(BASE / 'rollback-source.tar', target / 'rollback-source.tar')
        patch = PATCHES / f'type_mode7_{variant}.patch'
        subprocess.run(['patch','--batch','-p1','-i',str(patch)],cwd=target / 'candidate',check=True)
        shutil.copy2(ROOT / 'tools/pokedex_type_panels.py',target / 'candidate/tools/pokedex_type_panels.py')
        if (target / 'candidate/audio.asm').read_text().count('pokedex_types_audio.asm'):
            shutil.copy2(ROOT / 'tools/pokedex_type_audio.py',target / 'candidate/tools/pokedex_type_audio.py')
            subprocess.run(['python3','tools/pokedex_type_audio.py','--output',
                            'engine/pokedex/pokedex_types_audio.asm'],cwd=target / 'candidate',check=True)
        if variant == 'precomputed':
            subprocess.run(['python3','tools/pokedex_type_panels.py','--output',
                            'engine/pokedex/pokedex_types_mode7_records.asm'],
                           cwd=target / 'candidate',check=True)
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(OUTPUT)


def capture_sources():
    for variant in ('runtime','precomputed'):
        parts = []
        names = (*SOURCES,'engine/pokedex/pokedex_types_mode7_records.asm')
        for name in names:
            original = BASE / 'candidate' / name
            changed = OUTPUT / variant / 'candidate' / name
            before = original.read_text() if original.exists() else ''
            after = changed.read_text()
            if name.endswith('_records.asm'):
                after = '; Runtime variant has no precomputed lower-panel records.\n'
            parts.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),
                         fromfile='a/'+name if original.exists() else '/dev/null',tofile='b/'+name))
        path = PATCHES / f'type_mode7_{variant}.patch'
        path.write_text(''.join(parts))
        print(path)


def build(variant):
    target = OUTPUT / variant
    with (target / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', '-j6', 'pokecrystal.gbc'], cwd=target / 'candidate',
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for suffix in ('gbc', 'sym', 'map'):
        shutil.copy2(target / 'candidate' / f'pokecrystal.{suffix}', target / f'{STEM}.{suffix}')
    manifest = json.loads((OUTPUT / 'manifest.json').read_text())
    assert digest(ROOT / 'pokecrystal.gbc') == manifest['production_sha256']
    assert digest(BASE / f'{STEM}.gbc') == manifest['source_rom_sha256']
    assert digest(BASE / f'{STEM}.sav') == manifest['source_save_sha256']
    print(json.dumps(dict(variant=variant, rom_sha256=digest(target / f'{STEM}.gbc'))))


def synchronize():
    source = OUTPUT / 'runtime/candidate'
    target = OUTPUT / 'precomputed/candidate'
    for name in ('home/lcd.asm', 'home/vblank.asm', 'main.asm',
                 'engine/pokedex/pokedex_types.asm', 'engine/pokedex/pokedex_types_mode7.asm'):
        shutil.copy2(source / name, target / name)
    for variant in ('runtime', 'precomputed'):
        shutil.copy2(BASE / 'rollback-source.tar', OUTPUT / variant / 'rollback-source.tar')
    shutil.copy2(ROOT / 'tools/pokedex_type_panels.py', target / 'tools/pokedex_type_panels.py')
    print('Shared source synchronized; variant configuration is retained separately.')


def animation_configs():
    battery = OUTPUT / 'runtime-regression/legacy-input.sav'
    paths = [('production', OUTPUT / 'runtime-regression/baseline', 'pokecrystal-dex-moves-mode')]
    paths += [(variant, OUTPUT / variant, STEM) for variant in ('runtime','precomputed')]
    configs = [dict(variant=variant,root=str(folder / 'candidate'),
                    rom=str(folder / f'{stem}.gbc'),sym=str(folder / f'{stem}.sym'),
                    battery=str(battery),expected_double_speed=0,expected_battle_speed=0,
                    fresh_battle_fixture=True) for variant,folder,stem in paths]
    path = OUTPUT / 'animation-inputs.json'
    path.write_text(json.dumps(configs,indent=2)+'\n')
    print(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'build', 'sync', 'animation-configs','capture'))
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--source',type=Path,default=BASE)
    parser.add_argument('--variant', choices=('runtime', 'precomputed'), default='runtime')
    args = parser.parse_args()
    OUTPUT, BASE = args.output.resolve(), args.source.resolve()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'sync':
        synchronize()
    elif args.action == 'animation-configs':
        animation_configs()
    elif args.action == 'capture':
        capture_sources()
    else:
        build(args.variant)
