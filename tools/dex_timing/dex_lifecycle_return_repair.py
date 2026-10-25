"""Repair Stage's queued-white reveal without changing entry or shared code."""
import argparse
import array
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
import math
from pathlib import Path
import shutil
import statistics
import wave

from .assets import Repository, offset, read_symbols, sha256
from . import dex_lifecycle_budget as budget
from . import dex_lifecycle_review as life
from .performance import HZ, core

BASE = budget.BASE / 'stage-return-repair'
VARIANT = 'stage-mask-commit'


def prepare():
    cfg = json.loads((budget.BASE / 'config.json').read_text())
    b = budget.Builder(VARIANT)
    b.stage()
    labels = b.assemble('dex_budget_mask_commit',16)
    old = read_symbols(budget.ORIGIN / 'local-late-guarded/dex_exit_mask_late.sym')['ProbeLateMask']
    new = labels['BudgetMaskCommit']
    if old[0] != new[0]:
        raise ValueError('Exit mask moved across banks')
    b.replace('Pokedex.exit','InitPokedex',bytes((0xcd,old[1]&255,old[1]>>8)),
              bytes((0xcd,new[1]&255,new[1]>>8)))
    b.cost -= 6
    b.close_probe = read_symbols(budget.ORIGIN / 'local-late-guarded/dex_exit_local.sym')['ProbeExitLocal']
    fixed = b.finish()
    cfg['variants'][VARIANT] = fixed
    life.write(budget.BASE / 'config.json',cfg)
    cfg['variants'] = {v:cfg['variants'][v] for v in ('baseline','stage',VARIANT)}
    BASE.mkdir(exist_ok=True)
    life.write(BASE / 'config.json',cfg)
    print(json.dumps(dict(variant=VARIANT,romx=fixed['proposed_romx_delta'],
                         wramx=fixed['wram_delta'],rom=fixed['rom']),indent=2))


def reveal_frames(events):
    frames = [e for e in events if e['event']=='perf_frame']
    enables = [e for e in events if e['event']=='perf_phase' and e['name']=='enable_lcd']
    if not frames or not enables:
        raise ValueError('Missing native exit display boundaries')
    old_palettes = frames[0]['bgpals']
    return [e for e in frames if e['boundary_t']>=enables[-1]['t'] and e['type']==0
            and e['lcdc']&128 and e['white']<23040 and e['bgpals']==old_palettes]


def audit():
    rows = [r for p in BASE.glob('profile-*.json') for r in json.loads(p.read_text())['rows']]
    results = []
    for row in rows:
        folder = BASE / row['variant'] / f'style-{row["style"]}-order-{row["order"]}-q{row["phase"]}'
        with gzip.open(folder / f'exit-{row["iteration"]}-events.json.gz','rt') as stream:
            events = json.load(stream)
        bad = reveal_frames(events)
        origin = row['exit']['ready']['t']-row['exit']['input_to_ready_ms']*HZ/1000
        results.append(dict(variant=row['variant'],style=row['style'],order=row['order'],
            phase=row['phase'],iteration=row['iteration'],premature_frames=[dict(display=e['display'],
            ms=(e['boundary_t']-origin)*1000/HZ,frames=(e['boundary_t']-origin)/budget.FRAME)
            for e in bad]))
    summary = {v:dict(cases=sum(r['variant']==v for r in results),
                     failures=sum(r['variant']==v and bool(r['premature_frames']) for r in results),
                     bad_frames=sum(len(r['premature_frames']) for r in results if r['variant']==v))
               for v in ('baseline','stage',VARIANT)}
    life.write(BASE / 'reveal-audit.json',dict(summary=summary,rows=results))
    print(json.dumps(summary,indent=2))


def report():
    cfg = json.loads((BASE / 'config.json').read_text())
    rows = [r for p in BASE.glob('profile-*.json') for r in json.loads(p.read_text())['rows']]
    key = lambda r:tuple(r[n] for n in ('style','order','phase','iteration'))
    old = {key(r):r for r in rows if r['variant']=='stage'}
    production = {key(r):r for r in rows if r['variant']=='baseline'}
    def metric(values):
        return dict(median_ms=statistics.median(values),min_ms=min(values),max_ms=max(values),
                    median_frames=statistics.median(values)/budget.FRAME_MS,
                    min_frames=min(values)/budget.FRAME_MS,max_frames=max(values)/budget.FRAME_MS)
    output = {}
    for variant in cfg['variants']:
        group = [r for r in rows if r['variant']==variant]
        issues = []
        for row in group:
            for surface in ('listing','menu'):
                found = budget.visual_audit(production[key(row)][surface],row[surface],row['style'],surface)['issues']
                if found:
                    issues.append(dict(case=key(row),surface=surface,issues=found))
        output[variant] = dict(cases=len(group),final_ui_issues=issues,
            entry=metric([r['entry']['input_to_ready_ms'] for r in group]),
            exit=metric([r['exit']['input_to_ready_ms'] for r in group]),
            entry_vs_stage=metric([r['entry']['input_to_ready_ms']-old[key(r)]['entry']['input_to_ready_ms'] for r in group]),
            exit_vs_stage=metric([r['exit']['input_to_ready_ms']-old[key(r)]['exit']['input_to_ready_ms'] for r in group]),
            exit_vs_production=metric([r['exit']['input_to_ready_ms']-production[key(r)]['exit']['input_to_ready_ms'] for r in group]))
    current = Repository(budget.ROOT,budget.ROOT/'pokecrystal.gbc',budget.ROOT/'pokecrystal.sym')
    baseline_rom = Path(cfg['rom']).read_bytes()
    fixed_rom = Path(cfg['variants'][VARIANT]['rom']).read_bytes()
    fixed_bank = fixed_rom[:0x14e]==baseline_rom[:0x14e] and fixed_rom[0x150:0x4000]==baseline_rom[0x150:0x4000]
    life.write(BASE / 'comparison.json',dict(variants=output,resources=cfg['variants'][VARIANT],
        production_unchanged=current.hashes==cfg['baseline_hashes'],fixed_bank_code_unchanged=fixed_bank))
    print(json.dumps(output,indent=2))


def models(jobs):
    cfg = json.loads((BASE / 'config.json').read_text())
    resource = cfg['variants'][VARIANT]
    repo = Repository(budget.ROOT,Path(resource['rom']),Path(cfg['sym']))
    tasks = []
    for model in ('0','A','B','C','D','E'):
        folder = BASE / 'models' / model
        folder.mkdir(parents=True,exist_ok=True)
        header = folder / 'lifecycle-symbols.h'
        header.write_text(f'#define LIFE_AUDIO_BANK {repo.symbols["wChannel5Flags1"][0]}\n' +
            '\n'.join(f'#define LIFE_{name} {repo.symbols[name][1]}' for name in ('hSCX','hWX','hWY'))+'\n')
        binary = core(repo,folder,life.PROFILE,('-DDEX_LIFECYCLE_TRACE',
            f'-DDEX_LIFECYCLE_SYMBOLS="{header}"',f'-DDEX_TEST_MODEL=GB_MODEL_CGB_{model}'))
        local = dict(cfg,core=str(binary))
        life.write(folder / 'config.json',local)
        tasks.extend((str(folder),VARIANT,style,order,phase) for style in (0,1)
                     for order in (0,1,2) for phase in (0,17556,35112,52668))
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for task,batch in zip(tasks,pool.map(life.case,tasks)):
            model = Path(task[0]).name
            for row in batch:
                folder = Path(task[0])/VARIANT/f'style-{row["style"]}-order-{row["order"]}-q{row["phase"]}'
                with gzip.open(folder/f'exit-{row["iteration"]}-events.json.gz','rt') as stream:
                    bad = reveal_frames(json.load(stream))
                results.append(dict(model=model,style=row['style'],order=row['order'],phase=row['phase'],
                    iteration=row['iteration'],bad_frames=len(bad),
                    double_speed=bool(row['entry']['ready']['double_speed'] and row['exit']['ready']['double_speed'])))
    result = dict(cases=len(results),failures=sum(bool(r['bad_frames']) or not r['double_speed'] for r in results),
                  rows=results)
    life.write(BASE / 'model-qualification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


def audio_audit():
    rows = [r for p in BASE.glob('profile-*.json') for r in json.loads(p.read_text())['rows']
            if r['phase']==0 and r['iteration']==0]
    lookup = {(r['variant'],r['style'],r['order']):r for r in rows}
    results = []
    for style in (0,1):
        for order in (0,1,2):
            for direction in ('entry','exit'):
                signals,spans = [],[]
                for variant in ('stage',VARIANT):
                    row = lookup[variant,style,order]
                    folder = BASE/variant/f'style-{style}-order-{order}-q0'
                    with gzip.open(folder/f'{direction}-0-events.json.gz','rt') as stream:
                        events = json.load(stream)
                    origin = row[direction]['ready']['t']-row[direction]['input_to_ready_ms']*HZ/1000
                    gate = next(e['t'] for e in events if e['event']=='perf_phase' and
                                e['name']==('cleanup' if direction=='exit' else 'menu_accept'))
                    sound = [e for e in events if e['event']=='life_sfx']
                    prior = [e for e in sound if e['t']<=gate]
                    if prior and prior[-1]['mask']:
                        start = prior[-1]['t']
                    else:
                        start = next(e['t'] for e in sound if e['t']>=gate and e['mask'])
                    end = next(e['t'] for e in events if e['event']=='life_sfx' and e['t']>start and not e['mask'])
                    start_s,end_s = (start-origin)/HZ,(end-origin)/HZ
                    spans.append(dict(start_s=start_s,end_s=end_s,duration_ms=(end-start)*1000/HZ,
                                      duration_frames=(end-start)/budget.FRAME))
                    data = array.array('h',(folder/f'{direction}-0.pcm').read_bytes())
                    signals.append(data[2*math.ceil(start_s*44100):2*math.floor(end_s*44100)])
                n = min(map(len,signals))
                a,b = (s[:n] for s in signals)
                square = sum(x*x for x in a)
                relative = math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/square)
                sx,sy = sum(a),sum(b)
                covariance = sum(x*y for x,y in zip(a,b))-sx*sy/n
                variance = (square-sx*sx/n)*(sum(y*y for y in b)-sy*sy/n)
                correlation = covariance/math.sqrt(variance)
                results.append(dict(style=style,order=order,direction=direction,spans=spans,
                    duration_delta_ms=spans[1]['duration_ms']-spans[0]['duration_ms'],
                    relative_rms_difference=relative,correlation=correlation,identical=list(a)==list(b)))
                if order==0:
                    folder = BASE / 'audio-review'
                    folder.mkdir(exist_ok=True)
                    for label,signal in zip(('original-stage','fixed-stage'),signals):
                        with wave.open(str(folder/f'{label}-{style}-{direction}-beep.wav'),'wb') as file:
                            file.setnchannels(2)
                            file.setsampwidth(2)
                            file.setframerate(44100)
                            file.writeframes(signal.tobytes())
    result = dict(cases=len(results),duration_mismatches=sum(abs(r['duration_delta_ms'])>.001 for r in results),
        max_relative_rms_difference=max(r['relative_rms_difference'] for r in results),
        min_correlation=min(r['correlation'] for r in results),rows=results,
        scope='Native mixed PCM during active click/beep; not an all-song audible equivalence claim')
    life.write(BASE / 'audio-audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


def package():
    cfg = json.loads((BASE / 'config.json').read_text())
    resource = cfg['variants'][VARIANT]
    path = BASE / 'review/pokecrystal-dex-entry-stage-fixed.gbc'
    path.parent.mkdir(exist_ok=False)
    shutil.copy2(resource['rom'],path)
    shutil.copy2(cfg['fixtures']['0-0'],path.with_suffix('.sav'))
    if sha256(path.read_bytes())!=resource['sha256']:
        raise ValueError('Packaged image differs from tested prototype')
    life.write(path.parent / 'manifest.json',dict(rom=str(path),rom_sha256=resource['sha256'],
        save=str(path.with_suffix('.sav')),source_save=cfg['fixtures']['0-0'],
        projected_romx_bytes=resource['proposed_romx_delta'],wramx_bytes=0,
        original_stage_entry_unchanged=True,normal_fades_retained=True))
    print(str(path))


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','profile','audit','report','exit-matrix','routes','capture-audit','models','audio-audit','package'))
    p.add_argument('--jobs',type=int,default=6)
    args = p.parse_args()
    life.BASE = BASE
    if args.action=='prepare': prepare()
    elif args.action=='profile': life.profile(('baseline','stage',VARIANT),args.jobs)
    elif args.action=='audit': audit()
    elif args.action=='report': report()
    elif args.action=='exit-matrix': life.exit_matrix((VARIANT,))
    elif args.action=='routes': life.routes(('baseline',VARIANT),args.jobs)
    elif args.action=='models': models(args.jobs)
    elif args.action=='audio-audit': audio_audit()
    elif args.action=='capture-audit':
        original = budget.BASE
        budget.BASE = BASE
        try: budget.capture_audit()
        finally: budget.BASE = original
    else: package()
