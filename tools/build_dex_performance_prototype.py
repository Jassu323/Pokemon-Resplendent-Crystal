"""Build private, pinned Dex performance variants without changing production."""
import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from dex_timing.assets import Repository, offset, sha256
from dex_timing.area_ui import nests
from pokedex_info_assets import Compiler, width

ROOT = Path(__file__).resolve().parents[1]
BASE = '2cec80517'
BASE_ROM_SHA256 = '7e8525b279a5a748f876d3fdc09a0e519a2f09c5283b8070adc1e86bd2a92666'


def replace(path, before, after):
    text = path.read_text()
    if text.count(before) != 1:
        raise ValueError(f'Prototype anchor changed: {path}: {before[:60]}')
    path.write_text(text.replace(before, after))


def build(output, variant, jobs):
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()
    baseline = subprocess.run(['git', 'rev-parse', BASE], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    if head != baseline or sha256((ROOT / 'pokecrystal.gbc').read_bytes()) != BASE_ROM_SHA256:
        raise ValueError('Reconstruct this historical experiment from its pinned baseline checkout/ROM')
    checkout = output / 'candidate'
    if checkout.exists():
        raise ValueError('Use a new output directory')
    checkout.mkdir(parents=True)
    archive = subprocess.run(['git', 'archive', BASE], cwd=ROOT, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as data:
        data.extractall(checkout, filter='data')
    assets = checkout / 'build/dex-performance-assets'
    assets.mkdir(parents=True)
    repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
    palmap = repo.rom[offset(repo.symbols['TownMapPals.PalMap']):offset(repo.symbols['TownMapPals.PalMap'])+48]
    (assets / 'town-pals.bin').write_bytes(bytes((palmap[i//2] >> (4*(i&1))) & 7 if i < 96 else 0 for i in range(256)))
    for name in ('performance_fast.asm', 'performance_queue.asm'):
        shutil.copy2(ROOT / 'tools/dex_timing/probes' / name, checkout / 'engine/pokedex' / name)
    info = checkout / 'engine/pokedex/pokedex_info.asm'
    replace(info, 'PokedexInfo_Activate:\n', 'PokedexInfo_Activate:\n\tcall PokedexPerf_QueueInfo\n\tret c\n')
    replace(info, '\tld [wPokedexInfoState], a\n\tld [wPokedexMovesState], a',
                  '\tld [wPokedexInfoState], a\n\tld [wPokedexInfoPendingPage], a\n\tld [wPokedexMovesState], a')
    replace(info, '\tld a, [wPokedexOwnerTransition]\n\tcp POKEDEX_OWNER_TRANSITION_INFO\n\tjr z, .request',
                  '\tcall PokedexPerf_BeginPendingInfo\n\tld a, [wPokedexOwnerTransition]\n\tcp POKEDEX_OWNER_TRANSITION_INFO\n\tjr z, .request')
    replace(info, 'PokedexInfo_CopyTiles:\n', 'PokedexInfo_CopyTiles:\n'
            '\tfarcall PokedexPerf_FastCopyTiles\n\tret\nPokedexInfo_CopyTiles_Legacy:\n')
    replace(checkout / 'ram/wram.asm', 'wPokedexInfoWorkspaceEnd::', 'wPokedexInfoPendingPage:: db\nwPokedexInfoWorkspaceEnd::')
    main = checkout / 'main.asm'
    replace(main, 'INCLUDE "engine/pokedex/pokedex_info.asm"', 'INCLUDE "engine/pokedex/pokedex_info.asm"\nINCLUDE "engine/pokedex/performance_queue.asm"')
    replace(main, 'SECTION "Pokedex Moves", ROMX', 'INCLUDE "engine/pokedex/performance_fast.asm"\n\nSECTION "Pokedex Moves", ROMX')
    gear = checkout / 'engine/pokegear/pokegear.asm'
    text = gear.read_text()
    begin, end = text.index('Pokedex_GetArea:'), text.index('\n.loop', text.index('Pokedex_GetArea:'))
    body = text[begin:end].replace('call LoadTownMapGFX', 'farcall PokedexPerf_FastTownGFX')
    body = body.replace('call TownMapPals', 'farcall PokedexPerf_FastTownPals')
    body = body.replace('call TownMapBGUpdate', 'ld d, h\n\tld e, l\n\tfarcall PokedexPerf_FastTownMap')
    gear.write_text(text[:begin] + body + text[end:])
    if variant in ('indexed', 'idle', 'batch', 'repair'):
        compiler = Compiler()
        data = compiler.compile()
        table = []
        if variant not in ('batch', 'repair'):
            table += ['PokedexPerf_StatsIndex:']
            for name in data['names']:
                table += [f'\tdb BANK(PokedexPerf_Stats_{name})', f'\tdw PokedexPerf_Stats_{name}']
        table += ['PokedexPerf_NestIndex:']
        for name in data['names']:
            table += [f'\tdw PokedexPerf_Nest_{name}_0, PokedexPerf_Nest_{name}_1']
        for index, name in enumerate(data['names'], 1):
            for region in (0, 1):
                locations = nests(repo, index, region)
                table += [f'PokedexPerf_Nest_{name}_{region}:', '\tdb ' + ', '.join(map(str, [len(locations), *locations]))]
        (assets / 'indexed-tables.asm').write_text('\n'.join(table) + '\n')
        rows = []
        for i, name in enumerate(data['names']):
            if i % 59 == 0:
                rows += [f'SECTION "Dex Performance Stats {i//59}", ROMX, BANK[${0xba+i//59:x}]']
            rows += [f'PokedexPerf_Stats_{name}:']
            for row, value in enumerate(data['stats'][name]):
                tiles = data['labels'][row] + [255] * (3-len(data['labels'][row])) + list(range(15+row*4, 19+row*4))
                attrs = [8 if tile != 255 else 0 for tile in tiles]
                attrs[-1] = 8 | (row+2)
                remaining = max(0, width(value)-3)
                while remaining and len(tiles) < 19:
                    tiles.append(14 if remaining > 8 else 10+(remaining-1)//2)
                    attrs.append(8 | (row+2))
                    remaining -= min(8, remaining)
                attrs += [0]*(19-len(tiles))
                tiles += [255]*(19-len(tiles))
                rows += ['\tdb ' + ', '.join(map(str, tiles+attrs)), '\tdw ' + ', '.join(
                    f'PokedexInfoTileGFX + {tile} * TILE_SIZE' for tile in data['numbers'][value])]
        (assets / 'stats-tables.asm').write_text('\n'.join(rows) + '\n')
        shutil.copy2(ROOT / 'tools/dex_timing/probes/performance_indexed.asm', checkout / 'engine/pokedex/performance_indexed.asm')
        indexed_include = 'INCLUDE "engine/pokedex/performance_indexed.asm"\n'
        if variant in ('batch', 'repair'):
            indexed = checkout / 'engine/pokedex/performance_indexed.asm'
            indexed.write_text('PokedexPerf_FastNests:' + indexed.read_text().split('PokedexPerf_FastNests:', 1)[1])
        else:
            indexed_include += 'INCLUDE "build/dex-performance-assets/stats-tables.asm"\n'
            replace(info, 'PokedexInfo_PlanStats:\n', 'PokedexInfo_PlanStats:\n\tfarcall PokedexPerf_FastStatsRow\n\tret\nPokedexInfo_PlanStats_Legacy:\n')
        replace(main, 'SECTION "Pokedex Moves", ROMX', 'SECTION "Dex Performance Index", ROMX, BANK[$b9]\n' + indexed_include + '\nSECTION "Pokedex Moves", ROMX')
        replace(gear, 'farcall FindNest ; load nest landmarks into wTilemap[0,0]',
                      'farcall PokedexPerf_FastNests ; generated landmarks + live roamers')
    if variant in ('idle', 'batch', 'repair'):
        shutil.copy2(ROOT / 'tools/dex_timing/probes/performance_idle.asm', checkout / 'engine/pokedex/performance_idle.asm')
        replace(main, 'INCLUDE "engine/pokedex/performance_queue.asm"',
                      'INCLUDE "engine/pokedex/performance_queue.asm"\nINCLUDE "engine/pokedex/performance_idle.asm"')
        replace(info, '\tld b, POKEDEX_INFO_SERVICE_SLICES\n.slice',
                      '\tcall PokedexPerf_CanBatch\n\tld b, POKEDEX_INFO_SERVICE_SLICES\n\tjr nc, .slice\n\tld b, 6\n.slice')
        if variant == 'idle':
            replace(info, 'PokedexInfo_UploadSafeGFX:\n',
                'PokedexInfo_UploadSafeGFX:\n\tpush bc\n\tpush hl\n\tcall PokedexPerf_CanBatch\n\tpop hl\n\tpop bc\n\tjr nc, .streaming\n\tjp PokedexPerf_IdleUpload\n.streaming\n')
        else:
            idle = checkout / 'engine/pokedex/performance_idle.asm'
            idle.write_text(idle.read_text().split('PokedexPerf_IdleUpload:', 1)[0])
    if variant == 'repair':
        shutil.copy2(ROOT / 'tools/dex_timing/probes/performance_cache.asm', checkout / 'engine/pokedex/performance_cache.asm')
        replace(main, 'INCLUDE "engine/pokedex/pokedex_3.asm"',
                      'INCLUDE "engine/pokedex/pokedex_3.asm"\nINCLUDE "engine/pokedex/performance_cache.asm"')
        replace(info, '\tld a, $ff\n\tld hl, wPokedexGridCacheRowOffsets\n\tld bc, POKEDEX_GRID_CACHE_ROWS * 2\n\tcall ByteFill',
                      '\tfarcall PokedexPerf_RepairFrame0')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['make', '-s', '-j' + str(jobs), 'pokecrystal.gbc'], cwd=checkout, check=True, stdout=log, stderr=subprocess.STDOUT)
    for ext in ('gbc', 'sym', 'map'):
        shutil.copy2(checkout / ('pokecrystal.' + ext), output / (f'pokecrystal-dex-performance-{variant}.' + ext))
    provenance = dict(baseline=BASE, variant=variant, private_only=True,
        baseline_rom_sha256=sha256(repo.rom), rom_sha256=sha256((checkout / 'pokecrystal.gbc').read_bytes()))
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variant', choices=('lean', 'indexed', 'idle', 'batch', 'repair'), default='lean')
    parser.add_argument('--jobs', type=int, default=12)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'build'):
        parser.error('Private outputs must be under build/')
    output.mkdir(parents=True, exist_ok=True)
    build(output, args.variant, args.jobs)
