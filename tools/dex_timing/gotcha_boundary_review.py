"""Paired data checks and timestamped recordings for Gotcha-boundary review."""
from bisect import bisect_right
import copy
import gzip
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont

from .cold_listing import ROOT
from .gotcha_boundary import BASE, SEED, repo_for, compiler
from .assets import sha256
from .shared_menu_fixtures import make_fixture

HZ, FRAME = 4194304, 70224


def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def span(t):
    return dict(ms=t*1000/HZ, frames=t/FRAME)


def events(folder):
    with gzip.open(folder / 'events.jsonl.gz', 'rt') as stream:
        return [json.loads(line) for line in stream]


def delivery_checks(before, received, boxed):
    fields=('dvs',) if boxed else ('dvs','stats')
    return {key:received[key]==before[key] for key in fields}


def comparison_value(value, stage, field, scenario):
    result=copy.deepcopy(value)
    if stage!='after_exp':
        if field=='mons' and not scenario.startswith('pc'):
            for key in ('dvs','stats'):result[-1].pop(key)
        elif field=='box' and scenario.startswith('pc'):
            result.pop('dvs')
    return result


def delivery():
    from .cold_listing import Driver
    from . import gotcha_boundary as boundary, shared_menu_regression as menu
    configs=json.loads((BASE/'config.json').read_text())
    source=json.loads((BASE/'report.json').read_text())['results']
    results=[]
    for variant in ('production','candidate'):
        config=configs[variant];repo=repo_for(config)
        driver=Driver(config['core'],config['rom'],menu.BOOT,config['battery'],
                      BASE/('delivery-'+variant+'.log'))
        try:
            for row in source:
                if row['variant']!=variant:continue
                folder=BASE/'runs'/variant/f'{row["scenario"]}-{row["species"]}-q{row["phase"]}'
                driver.command('load '+str(folder/'fixture.s0'))
                boundary.audio.until(driver,repo,'BattleMenu.loop')
                menu.run(driver,repo,frames=24+row['phase']/4)
                menu.tap(driver,repo,'down')
                boundary.audio.until(driver,repo,'BattlePack.loop')
                for _ in range(10):
                    if boundary.number(driver,repo,'wCurPocket')==1:break
                    menu.tap(driver,repo,'right',released=30)
                boundary.audio.until(driver,repo,'@gotcha')
                before=dict(dvs=boundary.ram(driver,repo,'wEnemyMonDVs',2).hex(),
                            stats=boundary.ram(driver,repo,'wEnemyMonHP',14).hex())
                boxed=row['scenario'].startswith('pc')
                checks={}
                for stage in ('after_delivery','after'):
                    mon=row[stage]['box'] if boxed else row[stage]['mons'][-1]
                    checks.update({stage+':'+key:value for key,value in
                                   delivery_checks(before,mon,boxed).items()})
                results.append(dict(variant=variant,scenario=row['scenario'],species=row['species'],
                    phase=row['phase'],rom_sha256=sha256(repo.rom),before_handoff=before,
                    checks=checks,passed=all(checks.values())))
        finally:driver.close()
    report=dict(cases=len(results),failures=sum(not row['passed'] for row in results),
        scope='Replay each matching-link fixture only to Gotcha before the speed helper; compare its native wild DVs/stats with recorded delivery and map return',
        results=results)
    write(BASE/'delivery-proof.json',report)
    if report['cases']!=104 or report['failures']:raise AssertionError('Capture delivery proof failed')
    print(json.dumps({key:value for key,value in report.items() if key!='results'},indent=2))


def analyze():
    report = json.loads((BASE/'report.json').read_text())
    assert len(report['results']) == 104 and not any(r['issues'] or r['native_warnings'] for r in report['results'])
    baseline = {(r['scenario'],r['species'],r['phase']):r for r in report['results'] if r['variant']=='production'}
    proof=json.loads((BASE/'delivery-proof.json').read_text())
    assert proof['cases']==104 and not proof['failures']
    by_case={(r['variant'],r['scenario'],r['species'],r['phase']):r for r in proof['results']}
    assert len(by_case)==104 and all(r['passed'] and r['checks'] and
        all(r['checks'].values()) for r in by_case.values())
    configs=json.loads((BASE/'config.json').read_text())
    hashes={variant:sha256(repo_for(config).rom) for variant,config in configs.items()}
    for row in report['results']:
        item=by_case[row['variant'],row['scenario'],row['species'],row['phase']]
        assert item['rom_sha256']==hashes[row['variant']]
    pairs, mismatches, costs, wild_differences = [], [], [], []
    palette_costs={0:[],1:[]}
    margins=[]
    for row in report['results']:
        if row['variant'] != 'candidate': continue
        old = baseline[row['scenario'],row['species'],row['phase']]
        issues = []
        for stage in ('after_exp','after_delivery','after'):
            for field in ('mons','party_count','seen','box'):
                # Per-run native preservation is required above before excluding
                # only the newly caught individual's initial DVs/stat values.
                a=comparison_value(old[stage][field],stage,field,row['scenario'])
                b=comparison_value(row[stage][field],stage,field,row['scenario'])
                if a != b:
                    issues.append(stage+':'+field)
        if row['scenario']=='exp-share':
            assert row['after']['mons'][0]['level'] == row['after']['mons'][1]['level'] == 7
        if row['scenario']=='multi-level':
            assert row['after']['mons'][0]['level'] >= 8
        p = dict(scenario=row['scenario'], species=row['species'], phase=row['phase'], issues=issues)
        pairs.append(p)
        mismatches += [p] if issues else []
        native=[by_case[v,row['scenario'],row['species'],row['phase']]['before_handoff']
                for v in ('production','candidate')]
        if native[0]!=native[1]:
            wild_differences.append(dict(scenario=row['scenario'],species=row['species'],phase=row['phase'],
                production=native[0],candidate=native[1],preserved_in_delivery=True))
        costs += [e['elapsed'] for e in row['milestones'] if e['event']=='perf_cost' and e['name']=='handoff']
        folder=BASE/'runs/candidate'/f'{row["scenario"]}-{row["species"]}-q{row["phase"]}'
        trace=events(folder)
        starts={e['t']:e for e in trace if e['event']=='perf_phase' and e['name']=='palette_build'}
        for e in trace:
            if e['event']!='perf_cost' or e['name']!='palette_build': continue
            start=starts[e['t']]
            palette_costs[start['speed']].append(e['elapsed'])
            available=((144-start['ly'])%154)*456
            assert e['elapsed'] < available,(row['scenario'],start,e)
            margins.append(available-e['elapsed'])
    result = dict(pairs=len(pairs), mismatches=mismatches,rom_hashes=hashes,
        native_pre_handoff_differences=wild_differences,
        delivery_proof=str(BASE/'delivery-proof.json'),
        handoff=dict(minimum=span(min(costs)), median=span(statistics.median(costs)), maximum=span(max(costs))),
        palette_preparation_maximum={str(k):span(max(v)) for k,v in palette_costs.items() if v},
        palette_preparation_minimum_vblank_margin=span(min(margins)) if margins else None,
        palette_publication_gate='No handoff palette producer' if not margins else
            'Dirty flag remains zero until complete RGB preparation',
        results=pairs, no_full_regression_claim=True)
    write(BASE/'comparison.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('results','native_pre_handoff_differences')} |
        dict(native_pre_handoff_difference_pairs=len(wild_differences)),indent=2))


class Clip:
    def __init__(self, folder):
        self.folder = folder
        self.row = json.loads((folder/'result.json').read_text())
        all_events = events(folder)
        by_id = {e['display']:e for e in all_events if e['event']=='perf_frame'}
        self.paths = sorted(folder.glob('frame-*.ppm'))
        self.times = [(by_id[int(p.stem.rsplit('-',1)[1])]['boundary_t']-self.row['video_start_t'])/HZ for p in self.paths]
        assert self.paths and all(b>=a for a,b in zip(self.times,self.times[1:]))
        self.last = None
        self.picture = None

    def at(self, t):
        n = max(0,bisect_right(self.times,t)-1)
        if n != self.last:
            with Image.open(self.paths[n]) as image:
                self.picture = image.convert('RGB').resize((480,432),Image.Resampling.NEAREST)
            self.last = n
        return self.picture


def visuals():
    target = BASE/'review'
    target.mkdir(exist_ok=True)
    fps = HZ/FRAME
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',19)
    receipts = []
    for scenario,species in (('party-name','dusknoir'),('evolve','caterpie')):
        clips = [Clip(BASE/'runs'/v/f'{scenario}-{species}-q0') for v in ('production','candidate')]
        duration = max(c.times[-1] for c in clips)
        path = target/f'{scenario}-production-vs-prototype.mp4'
        process = subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y',
            '-f','rawvideo','-pixel_format','rgb24','-video_size','1024x510','-framerate',str(fps),
            '-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p',
            '-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
        for n in range(round(duration*fps)+1):
            elapsed=n/fps
            canvas=Image.new('RGB',(1024,510),(26,26,26))
            draw=ImageDraw.Draw(canvas)
            for x,label,clip in ((16,'PRODUCTION',clips[0]),(528,'GOTCHA PROTOTYPE',clips[1])):
                draw.text((x,10),label,font=font,fill='white')
                canvas.paste(clip.at(elapsed),(x,44))
            draw.text((16,484),f'{scenario} | real time | {elapsed:.2f}s | same Gotcha callback origin',font=font,fill='white')
            process.stdin.write(canvas.tobytes())
        process.stdin.close()
        assert process.wait()==0
        receipts.append(dict(path=str(path), duration_s=duration, silent=True,
            alignment='same executable Gotcha callback; native physical display timestamps',
            shorter_side_holds_last_frame=True))
    clip=Clip(BASE/'runs/candidate/party-name-dusknoir-q0')
    sheet=Image.new('RGB',(1280,3*320),(26,26,26))
    draw=ImageDraw.Draw(sheet)
    for n in range(12):
        x,y=(n%4)*320,(n//4)*320
        picture=clip.at(n/fps).resize((320,288),Image.Resampling.NEAREST)
        sheet.paste(picture,(x,y+28))
        draw.text((x+5,y+4),f'{n}: {1000*n/fps:.1f} ms',font=font,fill='white')
    sheet.save(target/'gotcha-first-12-frames.png')
    # Listening A/B uses caught-fanfare start, not a retimed video soundtrack.
    chunks=[]
    for variant in ('production','candidate'):
        folder=BASE/'runs'/variant/'party-name-dusknoir-q0'
        marks=events(folder)
        cue=next(e['t'] for e in marks if e['event']=='perf_phase' and e['name']=='sfx' and e['de']==2)
        with wave.open(str(folder/'audio.wav'),'rb') as wav:
            wav.setpos(round((cue/HZ-.15)*44100))
            chunks.append(wav.readframes(round(6.5*44100)))
    wav_path=target/'capture-audio-production-then-prototype.wav'
    with wave.open(str(wav_path),'wb') as wav:
        wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(44100)
        wav.writeframes(chunks[0]+bytes(round(.7*44100)*4)+chunks[1])
    write(target/'recordings.json',dict(videos=receipts,audio=str(wav_path),
        audio_order='production, 0.7-second silence, prototype',
        listening_and_visual_approval_pending=True))
    print(json.dumps(dict(videos=receipts,audio=str(wav_path)),indent=2))


def publish():
    manifest=json.loads((BASE/'manifest.json').read_text())
    comparison=json.loads((BASE/'comparison.json').read_text())
    supplement=json.loads((BASE/'supplement.json').read_text())
    registration=json.loads((BASE/'registration.json').read_text())
    oracle=json.loads((BASE/'palette-oracle.json').read_text())
    contracts=json.loads((BASE/'contracts.json').read_text())
    assert not comparison['mismatches']
    assert not any(r['issues'] or r['native_warnings'] for r in supplement['results'])
    assert registration['cases']==240 and registration['failures']==0
    assert oracle['rgb_color_strength_checks']==131072
    assert oracle['mapped_palette_publication_checks']==112
    assert all(r['cases']==20 and not r['failures'] and not r['errors'] and not r['skips'] for r in contracts)
    for path,expected in manifest['protected'].items():
        assert sha256(Path(path).read_bytes())==expected
    target=BASE/'review'
    target.mkdir(exist_ok=True)
    stem='pokecrystal-gotcha-boundary'
    for ext in ('gbc','sym','map'):
        shutil.copy2(BASE/'candidate'/('pokecrystal.'+ext),target/(stem+'.'+ext))
    config=json.loads((BASE/'config.json').read_text())['candidate']
    repo=repo_for(config)
    # Match the private seed's declared party ID order, not cartridge indexes.
    make_fixture(repo,Path(config['battery']),target/(stem+'.sav'),('ROUTE_30',13,49),capture=True,
        extra_fields={'wPartyCount':bytes((4,)), 'wPartySpecies':bytes((1,2,3,4,255,6,255)),
            'wPartyMon1Exp':(235).to_bytes(3,'big'),
            'wPartyMon2Exp':(342).to_bytes(3,'big'), 'wPartyMon2Item':bytes((0x39,))})
    write(target/'receipt.json',dict(rom=str(target/(stem+'.gbc')),rom_sha256=manifest['rom_sha256'],
        delta=manifest['delta'],production_unchanged=True,interactive_registration=False,
        test_save='Route 30; four Pokemon, Master Balls; Bulbasaur and Exp Share Caterpie one EXP below level 7; not main save'))


def visual_audit():
    config=json.loads((BASE/'config.json').read_text())['candidate']
    if 'BattleSpeed_CaptureHandoff.Resumed' in repo_for(config).symbols:
        rows=[]
        for scenario,species in (('party-name','dusknoir'),('evolve','caterpie')):
            folder=BASE/'runs/candidate'/f'{scenario}-{species}-q0'
            clip=Clip(folder);trace=events(folder)
            origin=clip.row['video_start_t']
            frames=[e for e in trace if e['event']=='perf_frame' and
                    origin<=e['boundary_t']<=origin+round(.2*HZ)]
            assert frames and all(e['white']<23040 and e['black']<23040 and e['lcdc']&128 for e in frames)
            stops=[e for e in trace if e['event']=='perf_phase' and e['name']=='capture_stop']
            assert stops and all(e['stat']&3==3 and not e['nr52']&128 and not e['ie'] for e in stops)
            rows.append(dict(scenario=scenario,scanouts=len(frames),no_blank_scanout=True,mode3_stops=len(stops)))
        write(BASE/'visual-audit.json',dict(cases=len(rows),results=rows,
            rom_sha256=sha256(repo_for(config).rom),
            check='No full white/black or LCD-off scanout during first 200 ms after Gotcha; STOP in mode 3 with sound/interrupts inactive',
            human_visual_approval=False))
        return
    rows=[]
    for scenario,species in (('party-name','dusknoir'),('evolve','caterpie')):
        clip=Clip(BASE/'runs/candidate'/f'{scenario}-{species}-q0')
        levels=[]
        for n in range(15):
            panel=clip.at(n*FRAME/HZ).resize((160,144),Image.Resampling.NEAREST).crop((0,115,160,144))
            levels.append(min(sum(pixel) for pixel in panel.get_flattened_data()))
        changes=[n for i,n in enumerate(levels) if i==0 or n!=levels[i-1]]
        assert len(changes)==7 and changes[0]==changes[-1]==0 and changes[3]==765,changes
        assert 0<changes[1]<changes[2]<765 and changes[:3]==list(reversed(changes[4:])),changes
        rows.append(dict(scenario=scenario,minimum_panel_rgb_sums=levels,
            distinct_fade_sequence=changes,complete_fade_out_and_back=True))
    write(BASE/'visual-audit.json',dict(cases=len(rows),results=rows,
        check='Native lower text panel brightens through two distinct grays to white and restores in reverse order'))
    print(json.dumps(rows,indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('delivery','analyze','visuals','publish','visual_audit'))
    parser.add_argument('--output',type=Path,default=BASE)
    args=parser.parse_args()
    BASE=args.output.resolve()
    globals()[args.action]()
