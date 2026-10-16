"""Freeze and verify the explicitly approved interactive-registration promotion."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .assets import sha256
from .cold_listing import ROOT
from tools.build_dex_unown_prototype import resources

SOURCE = ROOT / 'build/interactive-registration-fixed-full-20261016/candidate'
BASELINE = SOURCE.parent / 'baseline-source'
REVIEW = ROOT / 'build/interactive-registration-review-20261016'
OUTPUT = ROOT / 'build/interactive-registration-production-20261016'
FILES = (
    'Makefile', 'main.asm', 'tools/pokedex_info_assets.py',
    'data/pokemon/evos_attacks_custom.asm', 'data/pokemon/evos_attacks_johto.asm',
    'data/pokemon/evos_attacks_kanto.asm', 'data/pokemon/first_stages.asm',
    'engine/battle/start_battle.asm', 'engine/battle/capture_speed.asm',
    'engine/events/specials.asm', 'engine/items/item_effects.asm',
    'engine/pokedex/new_pokedex_entry.asm', 'engine/pokedex/pokedex_animation.asm',
    'engine/pokedex/pokedex_info.asm',
)


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def digest(path):
    return sha256(path.read_bytes())


def freeze(output):
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh integration directory under build/')
    qualification = json.loads((REVIEW / 'qualification.json').read_text())
    if not qualification['automated_qualification_pass'] or not all(qualification['checks'].values()):
        raise AssertionError('Reviewed candidate is not qualified')
    if digest(SOURCE / 'pokecrystal.gbc') != qualification['rom_sha256']:
        raise AssertionError('Reviewed ROM changed')
    if digest(ROOT / 'pokecrystal.gbc') != digest(BASELINE / 'pokecrystal.gbc'):
        raise AssertionError('Production no longer matches the qualified baseline')
    for name in FILES:
        path, old = ROOT / name, BASELINE / name
        if path.exists() != old.exists() or (path.exists() and path.read_bytes() != old.read_bytes()):
            raise AssertionError('Do not overwrite changed production source: ' + name)
    output.mkdir(parents=True)
    rollback = output / 'rollback'
    rollback.mkdir()
    sources = {}
    for name in FILES:
        path = ROOT / name
        sources[name] = digest(path) if path.exists() else None
        if path.exists():
            target = rollback / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    for extension in ('gbc', 'sym', 'map'):
        shutil.copy2(ROOT / ('pokecrystal.' + extension), rollback / ('pokecrystal.' + extension))
    saves = set(ROOT.glob('*.sav')) | {Path('/Applications/SameBoy/Games/pokecrystal.sav')}
    record = dict(baseline_sha256=digest(ROOT / 'pokecrystal.gbc'),
        candidate_sha256=qualification['rom_sha256'], sources_before=sources,
        source=str(SOURCE), review=str(REVIEW), protected_saves={str(p):digest(p) for p in saves if p.is_file()},
        approval='2026-10-16: user approved production integration and explicitly retained all reviewed temporary evolution requirements',
        gameplay_source_files=list(FILES), production_integrated=False)
    write(output / 'inputs.json', record)
    print(json.dumps(record, indent=2))


def verify(output):
    record = json.loads((output / 'inputs.json').read_text())
    for name in FILES:
        if (ROOT / name).read_bytes() != (SOURCE / name).read_bytes():
            raise AssertionError('Production source differs from reviewed candidate: ' + name)
    for extension in ('gbc', 'sym', 'map'):
        if (ROOT / ('pokecrystal.' + extension)).read_bytes() != (SOURCE / ('pokecrystal.' + extension)).read_bytes():
            raise AssertionError('Production build differs from reviewed ' + extension)
    for name, expected in record['protected_saves'].items():
        if digest(Path(name)) != expected:
            raise AssertionError('Protected save changed: ' + name)
    patch=[]
    for name in FILES:
        old=output/'rollback'/name
        before=old.read_text().splitlines(True) if old.exists() else []
        patch.extend(difflib.unified_diff(before,(ROOT/name).read_text().splitlines(True),
            fromfile='a/'+name if old.exists() else '/dev/null',tofile='b/'+name))
    (output/'promotion.patch').write_text(''.join(patch))
    old, new = resources(output / 'rollback/pokecrystal.map'), resources(ROOT / 'pokecrystal.map')
    result = dict(production_integrated=True, exact_reviewed_rom_symbols_map=True,
        rom_sha256=digest(ROOT / 'pokecrystal.gbc'),
        protected_saves_unchanged=True, source_files=len(FILES),
        delta={name:new[name]-value for name,value in old.items()},
        approved_temporary_evolution_requirements=20,
        full_qualification=str(REVIEW / 'qualification.json'),
        manual_approval='2026-10-16: user accepted reviewed prototype and requested integration')
    write(output / 'verification.json', result)
    print(json.dumps(result, indent=2))


def checks(output, jobs=6):
    from .type_full_regression import host
    from .interactive_full_regression import capture_gate
    verify(output)
    folder=output/'root-checks'
    folder.mkdir()
    host_root=folder/'host'
    (host_root/'campaign-logs').mkdir(parents=True)
    (host_root/'candidate').symlink_to(ROOT,target_is_directory=True)
    (host_root/'baseline').mkdir()
    (host_root/'baseline/candidate').symlink_to(BASELINE,target_is_directory=True)
    if host(host_root):raise AssertionError('Root host regression failed')

    def run(name, arguments):
        with (folder/(name+'.log')).open('w') as stream:
            subprocess.run([sys.executable,'-B',*map(str,arguments)],cwd=ROOT,
                           stdout=stream,stderr=subprocess.STDOUT,check=True)

    run('context',('tools/test_interactive_registration.py','--root',ROOT,'--baseline',BASELINE,
        '--report',folder/'context.json'))
    run('controls',('-c',
        'import unittest;from pathlib import Path;import tools.test_capture_handoff as t;'
        't.SOURCE=Path.cwd();r=unittest.TextTestRunner(verbosity=2).run('
        'unittest.defaultTestLoader.loadTestsFromNames(("tools.test_battle_tower_suite",'
        '"tools.test_interactive_registration_regression","tools.test_capture_handoff")));'
        'raise SystemExit(not (r.testsRun==36 and r.wasSuccessful() and not r.skipped))'))
    run('evolution',('tools/audit_evolution_data.py','--root',ROOT,
        '--output',folder/'evolution','--canonical',
        ROOT/'build/evolution-audit-20261015/canonical/manifest.json',
        '--rom',ROOT/'pokecrystal.gbc','--symbols',ROOT/'pokecrystal.sym',
        '--self-test','--require-complete','--jobs',jobs,'--temporary-approval',
        '2026-10-16: user explicitly approved retaining all reviewed temporary requirements in production; final species-data revision remains deferred.'))
    native=folder/'capture'
    native.mkdir()
    (native/'candidate').symlink_to(ROOT,target_is_directory=True)
    common=('--output',native,'--baseline-source',BASELINE,'--jobs',jobs)
    run('capture-setup',('-m','tools.dex_timing.gotcha_boundary','setup',*common))
    run('capture-smoke',('-m','tools.dex_timing.gotcha_boundary','smoke',*common))
    smoke=json.loads((native/'smoke.json').read_text())
    valid,gate=capture_gate(smoke,6,0)
    if not valid:raise AssertionError('Root capture gate failed: '+str(gate))
    run('payday',('-m','tools.dex_timing.registration_payday','--baseline',BASELINE,
        '--candidate',ROOT,'--output',folder/'payday','--jobs',jobs))
    payday=json.loads((folder/'payday/report.json').read_text())
    host_report=json.loads((host_root/'campaign-logs/host.json').read_text())
    if host_report['cases']!=87 or host_report['skipped'] or host_report['failures'] or host_report['errors']:
        raise AssertionError('Incomplete root host group')
    if payday['cases']!=8 or payday['failures']:raise AssertionError('Root Pay Day matrix failed')
    result=dict(rom_sha256=digest(ROOT/'pokecrystal.gbc'),host_cases=87,context_cases=10,
        control_tests=36,capture_cases=6,payday_cases=8,capture_gate=gate,
        evolution_report=str(folder/'evolution/report.json'),passed=True)
    write(output/'root-checks.json',result)
    verify(output)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'verify', 'checks'))
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--jobs',type=int,default=6)
    args = parser.parse_args()
    if args.action=='checks':checks(args.output.resolve(),args.jobs)
    else:globals()[args.action](args.output.resolve())
