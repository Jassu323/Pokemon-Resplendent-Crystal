"""Private species-information prototype and focused Description qualification."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
from concurrent.futures import ProcessPoolExecutor
import unittest

from .assets import Repository, offset, sha256
from .cold_listing import ROOT
from .footprints import protected
from tools.build_dex_unown_prototype import resources

DEFAULT = ROOT/'build/dex-species-information-20261016'
BASE = ROOT/'build/dex-footprints-20261016'
SCOPE = ROOT/'build/dex-species-information-scope-20261016'
STEM = 'pokecrystal-dex-species-information'


def write(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def verify(output):
    for path,digest in json.loads((output/'manifest.json').read_text())['protected'].items():
        assert sha256(Path(path).read_bytes()) == digest, path


def prepare(output):
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Use a fresh private build folder')
    output.mkdir(parents=True)
    saved = protected()
    for ext in ('gbc','sym','map','sav'):
        p=BASE/f'pokecrystal-dex-footprints.{ext}'
        saved[str(p)] = sha256(p.read_bytes())
    candidate=output/'candidate'
    shutil.copytree(BASE/'candidate',candidate,
        ignore=shutil.ignore_patterns('*.o','*.d','__pycache__','*.pyc','*.gbc','*.sym','*.map'))
    # Harness changes are current checkout work; game source stays the accepted base.
    shutil.copytree(ROOT/'tools',candidate/'tools',dirs_exist_ok=True,
        ignore=shutil.ignore_patterns('*.o','*.d','__pycache__','*.pyc'))
    module_spec=importlib.util.spec_from_file_location('species_scope',SCOPE/'assess.py')
    scope=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(scope)
    entries={r['constant']:r for r in scope.rows}
    pointers=re.findall(r'^\s*dba\s+(\w+)',(candidate/'data/pokemon/dex_entry_pointers.asm').read_text(),re.M)
    metadata=['; Relative to page one; zero denotes an absent later page.',
              'PokedexDescriptionPageOffsets:']
    imports=[]
    for constant in scope.constants[251:]:
        row=entries[constant]
        path=candidate/row['current_source']
        category=re.search(r'\bdb\s+"([^"]+)"',path.read_text())[1]
        weight=row['current_weight_word'] if constant=='TORKOAL' else row['crystal_weight_word']
        lines=[f'\tdb "{category}"',f'\tdw {row["crystal_height_word"]}, {weight}','']
        text_lines=scope.planned_lines[constant]
        for page in range(row['pages']):
            lines += [f'.page{page+1}::']
            group=text_lines[page*3:page*3+3]
            for index,line in enumerate(group):
                command='db' if index==0 else 'next'
                suffix='@' if index==len(group)-1 else ''
                lines += [f'.line{page*3+index}:',f'\t{command} '+json.dumps(line+suffix,ensure_ascii=False),
                    f'ASSERT @ - .line{page*3+index} == {len(scope.encode(line))+int(index>0)+len(suffix)}']
            lines += ['']
        path.write_text('\n'.join(lines)+'\n')
        label=pointers[scope.constants.index(constant)]
        values=[]
        for page in range(2,5):
            value=f'{label}.page{page} - {label}.page1' if page<=row['pages'] else '0'
            values.append(value)
            if page<=row['pages']:
                metadata.append(f'ASSERT {value} > 0 && {value} <= 255')
        metadata.append('\tdb '+', '.join(values))
        imports.append(dict(species=row['species'],constant=constant,path=row['current_source'],
            pages=row['pages'],height=row['crystal_height_word'],weight=weight,
            source_text_sha256=row['text_sha256']))
    metadata += ['ASSERT @ - PokedexDescriptionPageOffsets == (NUM_POKEMON - TREECKO + 1) * 3','']
    (candidate/'data/pokemon/dex_description_page_offsets.asm').write_text('\n'.join(metadata))
    path=candidate/'data/pokemon/dex_entries.asm'
    text=path.read_text()
    text=text.replace('ShinxPokedexEntry::', 'SECTION "Pokedex Entries Custom 2", ROMX\n\nShinxPokedexEntry::',1)
    path.write_text(text)
    write(output/'manifest.json',dict(protected=saved,base=str(BASE),imports=imports,state='prepared'))
    verify(output)
    print(json.dumps(dict(prepared=str(candidate),species=len(imports))),flush=True)


def build(output,jobs):
    verify(output)
    candidate=output/'candidate'
    shutil.copytree(ROOT/'tools',candidate/'tools',dirs_exist_ok=True,
        ignore=shutil.ignore_patterns('*.o','*.d','__pycache__','*.pyc'))
    with (output/'build.log').open('w') as log:
        subprocess.run(['make','-s',f'-j{jobs}','pokecrystal.gbc'],cwd=candidate,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    for ext in ('gbc','sym','map'):
        shutil.copy2(candidate/f'pokecrystal.{ext}',output/f'{STEM}.{ext}')
    shutil.copy2(BASE/'pokecrystal-dex-footprints.sav',output/f'{STEM}.sav')
    repo=Repository(candidate,candidate/'pokecrystal.gbc',candidate/'pokecrystal.sym')
    baseline=Repository(BASE/'candidate',BASE/'pokecrystal-dex-footprints.gbc',BASE/'pokecrystal-dex-footprints.sym')
    for name,value in baseline.symbols.items():
        if name.startswith(('w','s','h')) and value[1]>=0xa000 and name in repo.symbols:
            assert value==repo.symbols[name], ('RAM label moved',name)
    delta={k:resources(candidate/'pokecrystal.map')[k]-v for k,v in resources(BASE/'pokecrystal-dex-footprints.map').items()}
    assert all(v==0 for k,v in delta.items() if k!='ROMX'),delta
    for i in range(251):
        def record(r):
            table=offset(r.symbols['PokedexDataPointerTable'])+i*3
            bank=r.rom[table]
            at=offset((bank,int.from_bytes(r.rom[table+1:table+3],'little')))
            end=r.rom.index(0x50,at)+5
            end=r.rom.index(0x50,end)+1
            end=r.rom.index(0x50,end)+1
            return r.rom[at:end]
        assert record(repo)==record(baseline),('Original entry changed',i)
    write(output/'build.json',dict(delta=delta,rom_sha256=sha256(repo.rom),
        baseline_sha256=sha256(baseline.rom),original_251_entries_unchanged=True,
        renderer_growth_bytes=delta['ROMX']-12767,page_metadata_bytes=366,
        production_integrated=False))
    verify(output)
    print(json.dumps(json.loads((output/'build.json').read_text())),flush=True)


def regression_prepare(output):
    from . import type_full_regression
    verify(output)
    for ext in ('gbc','sym','map','sav'):
        shutil.copy2(output/f'{STEM}.{ext}',output/f'pokecrystal-dex-types.{ext}')
    with tarfile.open(output/'rollback-source.tar','w') as archive:
        def retain(member):
            return None if member.name.endswith(('.o','.d','.pyc')) or '__pycache__' in member.name else member
        for path in (BASE/'candidate').iterdir():
            archive.add(path,arcname=path.name,filter=retain)
    type_full_regression.prepare(output,output/'regression',BASE/'candidate')
    verify(output)


def pages_case(task):
    from .cold_listing import Driver,move,predecessor,audit
    from .description_paging import description_pages
    from .description_ui import settle,settle_description_text
    from .footprints import context,capture
    from .info_ui import BOOT,press
    config,index=task
    repo,assets,masks=context(config['root'],config['rom'],config['sym'])
    name=config['names'][index]
    folder=Path(config['output'])/f'{index:03}-{name}'
    folder.mkdir(parents=True)
    driver=Driver(config['core'],config['rom'],BOOT,config['battery'],folder/'native.log')
    result=dict(species=name,style=config['style'],screens=[],issues=[])
    try:
        prior,direction=predecessor(index) if config['style']=='modern' else ((index-1)%373,'down')
        driver.command(f'load {config["states"]}/listing-{prior:03}.s0')
        driver.command('rawcolor')
        move(driver,direction,index)
        driver.events.clear();driver.command('audit 1')
        accepted=driver.run(('accept',),key='a')
        final=settle(driver)
        result['playback']=audit(assets[name],accepted,driver.events,final,expected_double_speed=1)
        result['issues']+=result['playback']['issues']
        pages=description_pages(repo,name)
        for page in [0,*range(1,len(pages)),0]:
            if result['screens']: press(driver,'a')
            settle_description_text(driver,pages[page])
            label=('wrap' if len(result['screens'])==len(pages) else f'page-{page+1}')
            snap=capture(driver,repo,masks,name,label,folder)
            if driver.command('ui')['page']!=page: snap['issues'].append('page_index')
            result['screens'].append(snap)
            result['issues']+=snap['issues']
    except Exception as error:
        result['issues'].append(str(error));driver.evidence(folder/'failure')
    finally: driver.close()
    write(folder/'result.json',result)
    return result


def native_pages(output,jobs):
    from .listing_options import configuration
    from . import area_ui
    folder=output/'multipage'
    folder.mkdir(exist_ok=True)
    pages=[];areas=[]
    for style in ('modern','legacy'):
        config=configuration(output/'regression/dex-regression',style)
        config=dict(config,style=style,output=str(folder/style))
        Path(config['output']).mkdir(exist_ok=True)
        assert config['hashes']['rom_sha256']==json.loads((output/'build.json').read_text())['rom_sha256']
        if (folder/f'{style}.json').exists():
            rows=json.loads((folder/f'{style}.json').read_text())
        else:
            with ProcessPoolExecutor(max_workers=jobs) as pool:
                rows=list(pool.map(pages_case,[(config,i) for i in range(373)]))
        write(folder/f'{style}.json',rows)
        pages+=rows
        config=dict(config,output=str(folder/f'area-{style}'),expected_double_speed=1,repeat_area=True)
        Path(config['output']).mkdir(exist_ok=True)
        repo=Repository(Path(config['root']),Path(config['rom']),Path(config['sym']))
        from .description_paging import description_pages
        tasks=[(config,name,'page2',phase,key,page) for name in config['names']
               for page in range(2,len(description_pages(repo,name)))
               for phase,key in (('settled','a'),('settled','b'),('0','b'))]
        if (folder/f'area-{style}.json').exists():
            rows=json.loads((folder/f'area-{style}.json').read_text())
        else:
            with ProcessPoolExecutor(max_workers=jobs) as pool:
                rows=list(pool.map(area_ui.run_case,tasks))
        write(folder/f'area-{style}.json',rows)
        areas+=rows
    result=dict(species_presentation_cases=len(pages),screens=sum(len(r['screens']) for r in pages),
        page_failures=[r for r in pages if r['issues']],area_cases=len(areas),
        area_failures=[r for r in areas if r['issues']],protected_inputs_unchanged=True)
    write(folder/'summary.json',result)
    verify(output)
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)}),flush=True)
    if result['page_failures'] or result['area_failures']:
        raise AssertionError('Extended Description qualification failed; inspect retained results')


def host(output):
    from .type_full_regression import host as standard_host
    import tools.test_pokedex_description_pages as extra
    target=output/'host'
    (target/'campaign-logs').mkdir(parents=True,exist_ok=True)
    if not (target/'candidate').exists():
        (target/'candidate').symlink_to(output/'candidate',target_is_directory=True)
    (target/'baseline').mkdir(exist_ok=True)
    if not (target/'baseline/candidate').exists():
        (target/'baseline/candidate').symlink_to(
            ROOT/'build/interactive-registration-fixed-full-20261016/baseline-source',target_is_directory=True)
    assert standard_host(target)==0
    extra.ROOT=output/'candidate'
    with (target/'multipage.log').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(extra))
    write(target/'multipage.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)))
    assert result.wasSuccessful() and not result.skipped
    verify(output)


def media(output):
    from PIL import Image,ImageDraw
    from . import interactive_registration_regression as reg
    config=json.loads((output/'registration/config.json').read_text())
    target=output/'review'
    target.mkdir(exist_ok=True)
    config=dict(config,output=str(target/'captures'))
    names=('treecko','aggron','mismagius','honchkrow','cradily','claydol')
    rows=[next(row for row in config['catalog'] if row['base']==name) for name in names]
    results=[]
    for mode in ('selected','registration'):
        for row in rows:
            results.append(reg.run_species((config,row,mode,False,True)))
    assert all(r['status']=='pass' for r in results)
    sheet=Image.new('RGB',(4*320,32+len(rows)*314),'#eeeeee')
    draw=ImageDraw.Draw(sheet)
    draw.text((8,8),'Prototype: full sourced text, actual in-game screens at 2x',fill='black')
    for index,row in enumerate(rows):
        draw.text((8,36+index*314),row['base'],fill='black')
        for page in range(row['description_pages']):
            with Image.open(target/f'captures/runs/selected/{row["base"]}/desc-{page+1}.png') as frame:
                sheet.paste(frame.resize((320,288),Image.Resampling.NEAREST),(page*320,54+index*314))
    sheet.save(target/'description-pages.png')
    write(target/'capture-results.json',dict(cases=len(results),failures=0,recordings='captures/runs/*/*/audio.wav'))
    verify(output)


def summarize(output):
    import statistics
    from PIL import Image,ImageDraw
    verify(output)
    campaign=json.loads((output/'registration/campaign.json').read_text())
    assert len(campaign)==746 and all(r['status']=='pass' for r in campaign)
    timings=[]
    for mode in ('selected','registration'):
        for page in range(4):
            rows=[op['request_to_displayed'] for case in campaign if case['mode']==mode
                  for op in case['operations'] if op['view']==0 and op['page']==page
                  and op['name'].startswith('desc-')]
            timings.append(dict(mode=mode,page=page+1,cases=len(rows),
                median_ms=statistics.median(r['ms'] for r in rows),maximum_ms=max(r['ms'] for r in rows),
                median_display_frames=statistics.median(r['display_frames'] for r in rows),
                maximum_display_frames=max(r['display_frames'] for r in rows)))
    write(output/'description-timings.json',timings)
    baseline=json.loads((output/'baseline-registration/campaign.json').read_text())
    assert len(baseline)==40 and all(r['status']=='pass' for r in baseline)
    new={(r['species'],r['mode']):r for r in campaign}
    originals={'caterpie','exeggcute','mewtwo','eevee','tyrogue','slowpoke','poliwhirl','gloom','magnemite','swinub'}
    pairs=[]
    for old in baseline:
        current=new[old['species'],old['mode']]
        before=next(op['request_to_displayed'] for op in old['operations'] if op['name']=='desc-2')
        after=next(op['request_to_displayed'] for op in current['operations'] if op['name']=='desc-2')
        pairs.append(dict(species=old['species'],mode=old['mode'],original_species=old['species'] in originals,
            baseline_ms=before['ms'],candidate_ms=after['ms'],delta_ms=after['ms']-before['ms'],
            delta_display_frames=after['display_frames']-before['display_frames'],
            cry_content_signature_matches=current['audio_signature']==old['audio_signature']))
    groups={}
    for original in (True,False):
        selected=[r for r in pairs if r['original_species']==original]
        groups['unchanged_original_text' if original else 'placeholder_replaced_with_full_text']=dict(
            cases=len(selected),median_delta_ms=statistics.median(r['delta_ms'] for r in selected),
            minimum_delta_ms=min(r['delta_ms'] for r in selected),maximum_delta_ms=max(r['delta_ms'] for r in selected),
            median_delta_display_frames=statistics.median(r['delta_display_frames'] for r in selected),
            minimum_delta_display_frames=min(r['delta_display_frames'] for r in selected),
            maximum_delta_display_frames=max(r['delta_display_frames'] for r in selected))
    write(output/'baseline-description-comparison.json',dict(pairs=pairs,groups=groups,
        cry_content_signature_matches=sum(r['cry_content_signature_matches'] for r in pairs),
        comparison='Same first Desc page-two request; wrap requests excluded because later-page navigation changes their input phase.'))
    review=output/'review'
    selected=('treecko','cradily','claydol')
    comparison=Image.new('RGB',(640,40+3*314),'#eeeeee')
    draw=ImageDraw.Draw(comparison)
    draw.text((8,8),'Accepted footprint prototype',fill='black')
    draw.text((328,8),'Species-information prototype',fill='black')
    for row,name in enumerate(selected):
        draw.text((8,40+row*314),name,fill='black')
        old=next((BASE/'checks/candidate/modern/screens').glob(f'*-{name}/description-1.png'))
        new=review/f'captures/runs/selected/{name}/desc-1.png'
        for col,path in enumerate((old,new)):
            with Image.open(path) as frame:
                comparison.paste(frame.resize((320,288),Image.Resampling.NEAREST),(col*320,58+row*314))
    comparison.save(review/'before-after.png')
    write(output/'development-notes.json',dict(
        initial_link_fixes=['Moved enlarged custom entry sections out of the pinned 0x74 bank into 0xbb/0xbc.',
                           'Exported per-page labels because entry data and lookup code assemble in separate objects.'],
        harness_correction='A misplaced preparation block caused a post-test NameError after all 2482 screen and 732 Area cases passed. The block was moved back; corrected qualification returned zero using the same complete exact-link case reports.',
        no_runtime_fix_needed_after_native_qualification=True))
    print(json.dumps(timings,indent=2),flush=True)


def description_stress(output,jobs):
    from . import interactive_registration_regression as reg
    config=json.loads((output/'registration/config.json').read_text())
    tasks=[(config,row,phase,'rapid-desc',False) for row in config['catalog'] if row['index']>=252
           for phase in (0,17556,35112,52668)]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows=list(pool.map(reg.stress_species,tasks))
    result=dict(cases=len(rows),failures=sum(bool(r['issues']) for r in rows),rows=rows)
    write(output/'registration/rapid-description.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)
    assert not result['failures']


def qualify(output):
    verify(output)
    build_record=json.loads((output/'build.json').read_text())
    digest=build_record['rom_sha256']
    assert sha256((output/f'{STEM}.gbc').read_bytes())==digest
    assert sha256((output/'candidate/pokecrystal.gbc').read_bytes())==digest
    phases={}
    for phase,count in (('setup',4),('dex',11),('moves',11)):
        record=json.loads((output/f'regression/campaign-logs/{phase}.json').read_text())
        assert len(record['results'])==count and not record['issues']
        assert all(r['exit_code']==0 for r in record['results'])
        phases[phase]=dict(commands=count,failures=0)
    dex=json.loads((output/'regression/dex-regression/summary.json').read_text())
    assert dex['cases']==4479 and dex['failures']==0 and dex['rom_sha256']==digest
    pages=json.loads((output/'multipage/summary.json').read_text())
    assert pages['species_presentation_cases']==746 and pages['screens']==2482
    assert pages['area_cases']==732 and not pages['area_failures'] and not pages['page_failures']
    registration=json.loads((output/'registration/campaign.json').read_text())
    assert len(registration)==746 and all(r['status']=='pass' for r in registration)
    stress=json.loads((output/'registration/stress.json').read_text())
    rapid=json.loads((output/'registration/rapid-description.json').read_text())
    assert len(stress)==224 and all(not r['issues'] for r in stress)
    assert rapid['cases']==488 and rapid['failures']==0
    host_record=json.loads((output/'host/campaign-logs/host.json').read_text())
    assert host_record['cases']==87 and not any(host_record[k] for k in ('skipped','failures','errors'))
    extra=json.loads((output/'host/multipage.json').read_text())
    assert extra==dict(tests=6,failures=0,errors=0,skipped=0)
    comparison=json.loads((output/'baseline-description-comparison.json').read_text())
    assert len(comparison['pairs'])==40 and comparison['cry_content_signature_matches']==40
    types=json.loads((output/'type-tests/summary.json').read_text())
    assert types['rom_sha256']==digest and types['selections']==18 and types['navigation_cases']==72
    for phase in ('raster','idle'):
        assert not any(types[phase][key] for key in ('bad_mode_writes','bad_palette_indexes','register_or_bank_errors'))
    arrows=json.loads((output/'arrow-tests/summary.json').read_text())
    assert arrows['locations']==52 and arrows['helpers']['counter_bank_cases']==1792
    source=output/'candidate'
    for path in (BASE/'candidate/home').glob('*.asm'):
        assert path.read_bytes()==(source/'home'/path.name).read_bytes(),path
    assert (source/'engine/pokedex/pokedex_3.asm').read_bytes()==(BASE/'candidate/engine/pokedex/pokedex_3.asm').read_bytes()
    before=Repository(BASE/'candidate',BASE/'pokecrystal-dex-footprints.gbc',BASE/'pokecrystal-dex-footprints.sym')
    after=Repository(source,output/f'{STEM}.gbc',output/f'{STEM}.sym')
    a,b=offset(before.symbols['Footprints']),offset(after.symbols['Footprints'])
    assert before.rom[a:a+373*32]==after.rom[b:b+373*32]
    changed=[]
    with tarfile.open(output/'source-overlay.tar.gz','w:gz') as archive:
        for path in source.rglob('*'):
            relative=path.relative_to(source)
            if path.suffix not in ('.asm','.link') or relative.parts[0] in ('tools','build'):
                continue
            original=BASE/'candidate'/relative
            if not original.is_file() or original.read_bytes()!=path.read_bytes():
                archive.add(path,arcname=str(relative))
                changed.append(str(relative))
    result=dict(dex_regression_passed=True,rom_sha256=digest,delta=build_record['delta'],
        renderer_romx=466,text_data_romx=12767,new_allocated_ram_bytes=0,
        standard_dex_cases=dex['cases'],multipage_screens=2482,late_page_area_cases=732,
        selected_registration_cases=746,registration_operations=sum(len(r['operations']) for r in registration),
        rapid_and_cancellation_stress_cases=712,host_tests=93,baseline_comparison_cases=40,
        matching_baseline_cry_signatures=40,phases=phases,
        changed_game_sources=changed,footprint_prototype_retained=True,
        shared_interrupt_sources_unchanged=True,full_game_regression_run=False,battle_tower_run=False,
        production_integrated=False,main_save_unchanged=True,
        source_overlay_base=str(BASE),source_overlay_sha256=sha256((output/'source-overlay.tar.gz').read_bytes()),
        manual_visual_approval=False,manual_listening_approval=False)
    write(output/'qualification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='changed_game_sources'},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','build','regression-prepare','pages','host','media','summarize','desc-stress','qualify'))
    parser.add_argument('--output',type=Path,default=DEFAULT)
    parser.add_argument('--jobs',type=int,default=6)
    args=parser.parse_args()
    if args.action=='prepare': prepare(args.output.resolve())
    elif args.action=='build': build(args.output.resolve(),args.jobs)
    elif args.action=='regression-prepare': regression_prepare(args.output.resolve())
    elif args.action=='pages': native_pages(args.output.resolve(),args.jobs)
    elif args.action=='host': host(args.output.resolve())
    elif args.action=='media': media(args.output.resolve())
    elif args.action=='summarize': summarize(args.output.resolve())
    elif args.action=='desc-stress': description_stress(args.output.resolve(),args.jobs)
    else: qualify(args.output.resolve())
