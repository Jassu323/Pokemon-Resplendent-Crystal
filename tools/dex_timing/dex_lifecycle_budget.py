"""Budgeted, ROMX-only lifecycle alternatives on immutable private ROMs."""
import argparse
import gzip
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess

from .assets import Repository, offset, read_symbols, sha256
from .cold_listing import ROOT, FRAME
from .performance import HZ
from .performance import core
from .cold_listing import Driver
from .info_ui import BOOT
from .performance_lifecycle import open_menu
from . import dex_lifecycle_review as life
from pokedex_info_assets import constants

ORIGIN = ROOT / 'build/dex-entry-exit-review-20261013'
BASE = ROOT / 'build/dex-lifecycle-budget-20261013'
FRAME_MS = FRAME * 1000 / HZ


class Builder:
    def __init__(self, variant):
        self.folder = BASE / variant
        self.folder.mkdir(parents=True, exist_ok=True)
        self.origin = json.loads((ORIGIN / 'config.json').read_text())
        self.repo = Repository(ROOT, Path(self.origin['variants']['local-late-guarded']['rom']),
                               Path(self.origin['sym']))
        self.data = bytearray(self.repo.rom)
        self.mapping = (ORIGIN / 'baseline/pokecrystal.map').read_text()
        self.symbols = dict(self.repo.symbols)
        self.cost = 92
        self.helpers = []
        self.wram = 0

    def padding(self, bank, size, alignment=1):
        block = self.mapping.split(f'ROMX bank #{bank}:')[1].split('ROMX bank #')[0]
        for a,b in re.findall(r'EMPTY: \$([0-9a-f]+)-\$([0-9a-f]+)',block):
            for pc in range(int(a,16),int(b,16)-size+2):
                if pc % alignment:
                    continue
                at = offset((bank,pc))
                if bytes(self.data[at:at+size]) in (bytes(size),bytes([255])*size):
                    return pc
        raise ValueError(f'No unused {size}-byte span in bank {bank}')

    def assemble(self, name, bank, extras=None):
        source = ROOT / 'tools/dex_timing/probes' / (name+'.asm')
        text = source.read_text()
        words = set(re.findall(r'\b[A-Za-z_]\w*\b',text))
        declared = set(re.findall(r'^(\w+):',text,re.M))
        needed = {k:v for k,v in self.symbols.items() if k in words and k not in declared}
        defs = {k:v[1] for k,v in needed.items()}
        defs.update({'B_'+k:v[0] for k,v in needed.items()})
        for file in ('scgb_constants.asm','tileset_constants.asm'):
            defs.update({k:v for k,v in constants(ROOT / 'constants' / file).items() if k in words})
        defs.update(VBLANK_POKEDEX=constants(ROOT / 'constants/ram_constants.asm')['VBLANK_POKEDEX'],
                    PROBE_BANK=bank,**(extras or {}))
        obj,rom,sym = (self.folder / (name+s) for s in ('.o','.gbc','.sym'))
        def link(pc):
            args = ['rgbasm',*(f'-D{k}={v}' for k,v in dict(defs,PROBE_PC=pc).items()),
                    '-o',str(obj),str(source)]
            subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
            subprocess.run(['rgblink','-o',str(rom),'-n',str(sym),str(obj)],check=True)
            labels = {k:v for k,v in read_symbols(sym).items() if k.startswith('Budget')}
            finish = next(v for k,v in labels.items() if k.endswith('End'))
            return labels,rom.read_bytes()[offset((bank,pc)):offset(finish)]
        _,trial = link(0x4000)
        pc = self.padding(bank,len(trial),16 if (extras or {}).get('USE_GDMA') else 1)
        labels,payload = link(pc)
        if len(payload)!=len(trial):
            raise ValueError('Relocation changed helper width')
        at = offset((bank,pc))
        self.data[at:at+len(payload)] = payload
        self.symbols.update(labels)
        self.cost += len(payload)
        self.helpers.append(dict(name=name,bank=bank,pc=pc,bytes=len(payload)))
        return labels

    def payload(self, bank, raw, name):
        pc = self.padding(bank,len(raw))
        at = offset((bank,pc))
        self.data[at:at+len(raw)] = raw
        self.cost += len(raw)
        self.helpers.append(dict(name=name,bank=bank,pc=pc,bytes=len(raw)))
        return bank,pc

    def replace(self, start, end, old, new):
        a,b = offset(self.repo.symbols[start]),offset(self.repo.symbols[end])
        body = bytes(self.data[a:b])
        if body.count(old)!=1 or len(old)!=len(new):
            raise ValueError('Unexpected patch span: '+start)
        at = a+body.index(old)
        self.data[at:at+len(old)] = new

    def near(self, start, end, old_label, target):
        bank,pc = target
        if bank != self.repo.symbols[start][0]:
            raise ValueError('Near replacement crosses bank')
        self.replace(start,end,life.call(self.repo,old_label),bytes((0xcd,pc&255,pc>>8)))

    def stage(self):
        target = self.repo.symbols['CGB_PokedexStageListLayout']
        trampoline = self.payload(16,life.farcall(self.repo,*target)+b'\xc9','stage-layout')
        self.near('Pokedex_InitMainScreen.cgb_cold_layout','Pokedex_InitMainScreen.sgb_layout',
                  'Pokedex_GetSGBLayout',trampoline)
        self.replace('PokedexLegacy_InitMainScreen','PokedexLegacy_UpdateMainScreen',
                     life.farcall(self.repo,*self.repo.symbols['Pokedex_GetDexSGBLayout']),
                     life.farcall(self.repo,*target))

    def cold(self, music=False, unroll=False):
        extras = {}
        if music:
            block = self.mapping.split('WRAMX bank #2:')[1].split('WRAMX bank #')[0]
            a,b = re.findall(r'EMPTY: \$([0-9a-f]+)-\$([0-9a-f]+)',block)[-1]
            if int(b,16)-int(a,16)+1<5:
                raise ValueError('No unallocated five-byte clock record')
            self.music_ram = (2,int(a,16))
            self.wram = 5
            self.assemble('dex_budget_music',0xa0,dict(MUSIC_BANK=2,MUSIC_RAM=int(a,16)))
            extras['MUSIC_SYNC']=1
        if unroll:
            extras['UNROLL_MAP']=1
        labels = self.assemble('dex_budget_cold',0xa0,extras)
        edge = read_symbols(ORIGIN / 'local-late-guarded/dex_entry_edge.sym')['ProbeEntryEdge']
        at = offset(edge)
        old = bytes((0xc3,*life.call(self.repo,'EnableLCD')[1:]))
        body = bytes(self.data[at:at+35])
        if body.count(old)!=1:
            raise ValueError('Edge enable changed')
        p = at+body.index(old)
        self.data[p:p+3] = b'\xc9\0\0'
        target = labels['BudgetColdStart']
        # Keep non-CGB's original frame wait; only cold CGB entry is diverted.
        raw = bytes((0xf0,0x40,0xcb,0x7f,0xc2,*life.call(self.repo,'DelayFrame')[1:]))
        raw += life.farcall(self.repo,*target)+b'\xc9'
        trampoline = self.payload(16,raw,'cold-entry-call')
        self.near('Pokedex','Pokedex.exit','DelayFrame',trampoline)

    def exit_off(self):
        if 'BudgetCopyOff' not in self.symbols:
            self.assemble('dex_budget_cold',0xa0)
        labels = self.assemble('dex_budget_exit_off',4)
        self.near_original_close(labels['BudgetExitOff'])
        # The source reference contains the 57-byte close helper but not the
        # diagnostic-only nine-byte caller trampoline. Keep the mask's cost.
        self.cost -= 57

    def near_original_close(self,target):
        start = offset(self.repo.symbols['StartMenu_Pokedex'])
        finish = offset(self.repo.symbols['StartMenu_Pokedex.empty'])
        bank,pc = target
        if bank != 4 or self.data[finish-3]!=0xc3:
            raise ValueError('Private close trampoline changed')
        self.data[finish-3:finish] = bytes((0xcd,pc&255,pc>>8))
        self.close_probe = target

    def font(self, prepared=False, gdma=False, unroll=1):
        extras = dict(UNROLL=unroll)
        if prepared:
            at = offset(self.repo.symbols['Font'])
            pixels = self.repo.rom[at:at+1024]
            file = self.folder / 'inverted-font.2bpp'
            file.write_bytes(b''.join(bytes((0,b^255)) for b in pixels))
            extras.update(PREPARED_FONT=1,PREPARED_FONT_PATH='"'+str(file)+'"')
            if gdma:
                extras['USE_GDMA']=1
        labels = self.assemble('dex_budget_font',self.repo.symbols['Font'][0],extras)
        trampoline = self.payload(16,life.farcall(self.repo,*labels['BudgetFont'])+b'\xc9','font-call')
        self.near('Pokedex_LoadGFX','Pokedex_LoadListStaticGFX','Pokedex_LoadInvertedFont',trampoline)

    def isolate_font(self):
        a,b = offset(self.repo.symbols['Pokedex_LoadGFX']),offset(self.repo.symbols['Pokedex_LoadListStaticGFX'])
        clone = bytes(self.data[a:b])
        self.data[a:b] = self.repo.rom[a:b]
        target = self.payload(16,clone,'cold-only-gfx-loader')
        self.near('InitPokedex','Pokedex_ClearLockedIDs','Pokedex_LoadGFX',target)

    def exit_lcd(self, overlap):
        self.assemble('dex_budget_font_lcd',self.repo.symbols['Font'][0])
        labels = self.assemble('dex_budget_exit_lcd',4)
        self.near_original_close(labels['BudgetExitLCD'])
        self.cost -= 57
        if overlap:
            self.replace('Pokedex.exit','InitPokedex',life.call(self.repo,'WaitSFX'),bytes(3))
            self.cost -= 3

    def fades(self, delay):
        labels = self.assemble('dex_budget_fades',self.repo.symbols['FadeInFromWhite'][0],dict(FADE_DELAY=delay))
        raw = b'\xaf'+bytes((0xe0,self.repo.symbols['hBGMapMode'][1]&255))
        raw += life.call(self.repo,'LoadStandardMenuHeader')
        raw += life.farcall(self.repo,*labels['BudgetFadeOut'])
        raw += life.call(self.repo,'ClearSprites')+bytes((0xc3,*life.call(self.repo,'DisableSpriteUpdates')[1:]))
        target = self.payload(4,raw,'fast-fade-menu')
        self.near('StartMenu_Pokedex','StartMenu_Pokedex.empty','FadeToMenu',target)
        helper = self.symbols.get('BudgetExitOff')
        if helper is None:
            helper = read_symbols(ORIGIN / 'local-late-guarded/dex_exit_local.sym')['ProbeExitLocal']
        at = offset(helper)
        old = life.farcall(self.repo,*self.repo.symbols['FadeInFromWhite'])
        body = bytes(self.data[at:at+200])
        if body.count(old)!=1:
            raise ValueError('Exit fade call changed')
        p = at+body.index(old)
        self.data[p:p+len(old)] = life.farcall(self.repo,*labels['BudgetFadeIn'])

    def finish(self):
        self.data[0x14e:0x150] = bytes(2)
        self.data[0x14e:0x150] = (sum(self.data)&65535).to_bytes(2,'big')
        path = self.folder / 'pokecrystal-diagnostic.gbc'
        path.write_bytes(self.data)
        return dict(rom=str(path),sha256=sha256(self.data),proposed_romx_delta=self.cost,
                    wram_delta=self.wram,rom0_delta=0,hram_delta=0,helpers=self.helpers,
                    music_ram=list(self.music_ram) if self.wram else None,
                    close_probe=list(self.close_probe) if hasattr(self,'close_probe') else None,
                    probe_symbols={k:list(v) for k,v in self.symbols.items() if k.startswith('Budget')},
                    address_stable_binary_ablation=True)


def prepare(extended=False):
    BASE.mkdir(parents=True,exist_ok=True)
    cfg = json.loads((ORIGIN / 'config.json').read_text())
    old = cfg['variants']
    cfg['variants'] = dict(baseline=old['baseline'],reference=old['local-late-guarded'])
    cfg['variants']['reference']['proposed_romx_delta'] = 92
    variants = ('stage','cold','cold-exit','font-fused','font-prepared','cold-font',
                'cold-exit-font','short-fades','hard-cuts')
    if extended:
        cfg = json.loads((BASE / 'config.json').read_text())
        variants = ('font-gdma','cold-font-gdma','lcd-exit','lcd-overlap','isolated-best',
                    'isolated-short','music-best','music-short','music-hard','music-unrolled')
    for name in variants:
        b = Builder(name)
        if name=='stage': b.stage()
        if name in ('cold','cold-exit','cold-font','cold-exit-font','short-fades','hard-cuts',
                    'cold-font-gdma','lcd-exit','lcd-overlap','isolated-best','isolated-short'): b.cold()
        if name in ('music-best','music-short'): b.cold(True)
        if name in ('music-hard','music-unrolled'): b.cold(True,name=='music-unrolled')
        if name in ('cold-exit','cold-exit-font','short-fades','hard-cuts'): b.exit_off()
        if name in ('font-fused','cold-font','cold-exit-font'): b.font()
        if name=='font-prepared': b.font(True)
        if name=='font-gdma': b.font(True,True)
        if name=='cold-font-gdma': b.font(True,True)
        if name in ('lcd-exit','lcd-overlap'): b.exit_lcd(name=='lcd-overlap')
        if name in ('isolated-best','isolated-short','music-best','music-short'):
            b.exit_off(); b.font(); b.isolate_font()
        if name in ('music-hard','music-unrolled'):
            b.exit_off(); b.font(unroll=2 if name=='music-unrolled' else 1); b.isolate_font()
        if name in ('isolated-short','music-short'): b.fades(1)
        if name=='music-hard': b.fades(0)
        if name=='short-fades': b.fades(1)
        if name=='hard-cuts': b.fades(0)
        cfg['variants'][name] = b.finish()
    life.write(BASE / 'config.json',cfg)
    print(json.dumps({name:row['proposed_romx_delta'] for name,row in cfg['variants'].items()},indent=2))


def report():
    cfg = json.loads((BASE / 'config.json').read_text())
    rows = [r for p in BASE.glob('profile-*.json') for r in json.loads(p.read_text())['rows']]
    key = lambda r:tuple(r[n] for n in ('style','order','phase','iteration'))
    baselines = {key(r):r for r in rows if r['variant']=='baseline'}
    references = {key(r):r for r in rows if r['variant']=='reference'}
    output = {}
    def metric(values):
        return dict(min_ms=min(values),median_ms=statistics.median(values),max_ms=max(values),
                    min_frames=min(values)/FRAME_MS,median_frames=statistics.median(values)/FRAME_MS,
                    max_frames=max(values)/FRAME_MS)
    for name,resource in cfg['variants'].items():
        group = [r for r in rows if r['variant']==name]
        if not group: continue
        record = dict(cases=len(group),resources=resource,issues=[])
        sound=[]
        for row in group:
            old = baselines[key(row)]
            for surface in ('listing','menu'):
                audit = visual_audit(old[surface],row[surface],row['style'],surface)
                if audit['issues']:
                    record['issues'].append(dict(case=key(row),surface=surface,issues=audit['issues']))
            folder=BASE / name / f'style-{row["style"]}-order-{row["order"]}-q{row["phase"]}'
            with gzip.open(folder / f'exit-{row["iteration"]}-events.json.gz','rt') as stream:
                events=json.load(stream)
            sounds=[e for e in events if e['event']=='life_sfx']
            cleanup=next(e['t'] for e in events if e['event']=='perf_phase' and e['name']=='cleanup')
            begin=next((e for e in sounds if e['t']>=cleanup and e['mask']),None)
            end=next((e for e in sounds if begin and e['t']>begin['t'] and not e['mask']),None)
            if begin and end:
                sound.append((end['t']-begin['t'])*1000/HZ)
        record['exit_sfx_active']=metric(sound)
        for direction in ('entry','exit'):
            record[direction] = dict(ready=metric([r[direction]['input_to_ready_ms'] for r in group]),
                vs_production=metric([r[direction]['input_to_ready_ms']-baselines[key(r)][direction]['input_to_ready_ms'] for r in group]),
                vs_reference=metric([r[direction]['input_to_ready_ms']-references[key(r)][direction]['input_to_ready_ms'] for r in group]))
        output[name] = record
    original=Path(cfg['rom']).read_bytes()
    allocation=[]
    for name,resource in cfg['variants'].items():
        candidate=Path(resource['rom']).read_bytes()
        unchanged=original[:0x14e]==candidate[:0x14e] and original[0x150:0x4000]==candidate[0x150:0x4000]
        if not unchanged:
            raise ValueError('A diagnostic changed fixed-bank code: '+name)
        allocation.append(dict(variant=name,fixed_bank_code_unchanged=True,
                               checksum_header_only_exception=True))
    life.write(BASE / 'comparison.json',dict(variants=output,frame_ms=FRAME_MS,cases=len(rows),
               allocation_audit=allocation,production_unchanged=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym').hashes==cfg['baseline_hashes']))
    print(json.dumps({n:dict(entry=r['entry']['ready']['median_ms'],exit=r['exit']['ready']['median_ms'],
                            issues=len(r['issues']),romx=r['resources']['proposed_romx_delta']) for n,r in output.items()},indent=2))


def visual_audit(old,new,style,surface):
    result=life.visible_ui_differences(old,new,style,surface)
    if surface=='menu' and 'palettes' in result['issues']:
        a,b=bytes.fromhex(old['palettes']),bytes.fromhex(new['palettes'])
        if a[:24]==b[:24] and a[26:]==b[26:] and b[24:26] in (a[24:26],a[26:28],a[28:30]):
            result['issues'].remove('palettes')
            result['allowances'].append('native_water_palette_animation_phase')
    return result


def qualify(variants, models):
    config=json.loads((BASE / 'config.json').read_text())
    rows=[]
    for variant in variants:
        resource=config['variants'][variant]
        repo=Repository(ROOT,Path(resource['rom']),Path(config['sym']))
        repo.symbols.update({k:tuple(v) for k,v in resource['probe_symbols'].items()})
        music=resource['music_ram']
        for model in models:
            folder=BASE / 'clock-qualification' / variant / model
            folder.mkdir(parents=True,exist_ok=True)
            header=folder / 'clock-symbols.h'
            mb,mp=repo.symbols['BudgetMusicBegin.sampled']
            cp=repo.symbols['BudgetMusicCheckpoint.sampled'][1]
            header.write_text(f'#define LIFE_AUDIO_BANK {repo.symbols["wChannel5Flags1"][0]}\n'+
                '\n'.join(f'#define LIFE_{name} {repo.symbols[name][1]}' for name in ('hSCX','hWX','hWY'))+
                f'\n#define LIFE_MUSIC_BANK {mb}\n#define LIFE_MUSIC_BEGIN {mp}\n#define LIFE_MUSIC_CHECK {cp}\n')
            binary=core(repo,folder,life.PROFILE,('-DDEX_LIFECYCLE_TRACE',
                f'-DDEX_LIFECYCLE_SYMBOLS="{header}"',f'-DDEX_TEST_MODEL=GB_MODEL_CGB_{model}'))
            for style in (0,1):
                for order,phase in ((order,phase) for order in (0,1,2) for phase in (0,17556,35112,52668)):
                    target=folder / f'{style}-{order}-{phase}'
                    target.mkdir(exist_ok=True)
                    driver=Driver(binary,resource['rom'],BOOT,config['fixtures'][f'{style}-{order}'],target / 'driver.log')
                    try:
                        open_menu(driver)
                        driver.command(f'run 0 {phase} 0')
                        driver.command('perf 1')
                        driver.events.clear()
                        ready=life.reach(driver,repo,'Pokedex_UpdateMainScreen','a')
                        driver.run(frames=4)
                        driver.command('perf 0')
                        samples=[e for e in driver.events if e['event']=='life_music']
                        data=bytes.fromhex(driver.command(f'perfram {music[0]} {music[1]} 5')['bytes'])
                        issues=[]
                        gaps=[]
                        if len(samples)!=4 or samples[0]['phase']!='begin':
                            issues.append('missing_clock_checkpoints')
                        else:
                            count=sum((b['sample']-a['sample'])&255 for a,b in zip(samples,samples[1:]))
                            expected_ticks,remainder=divmod(count*32,4389)
                            if (data[3],int.from_bytes(data[1:3],'little'),data[4]) != (expected_ticks,remainder,1):
                                issues.append('wrong_clock_accumulator')
                            gaps=[(b['t']-a['t'])*1000/HZ for a,b in zip(samples,samples[1:])]
                            if max(gaps)>=31.25:
                                issues.append('timer_poll_gap_exceeds_wrap')
                            if any((e['tac']&7,e['tma'])!=(4,0) for e in samples):
                                issues.append('timer_configuration_changed')
                        if not ready['double_speed']:
                            issues.append('clock_policy_changed')
                        if bytes.fromhex(driver.command(f'perfram 0 {repo.symbols["hVBlank"][1]} 1')['bytes']) != b'\x07':
                            issues.append('wrong_dex_vblank_owner')
                        phases=[]
                        for _ in range(20):
                            driver.run(frames=1)
                            phases.append(driver.command('ui')['oam'][4:6])
                        if style==0 and len(set(phases))!=2:
                            issues.append('grid_icon_animation_not_running')
                        row=dict(variant=variant,model=model,style=style,order=order,phase=phase,issues=issues,
                                 samples=samples,data=list(data),ticks=data[3],max_poll_gap_ms=max(gaps,default=0),
                                 max_poll_gap_frames=max(gaps,default=0)/FRAME_MS)
                        rows.append(row)
                    finally:
                        driver.close()
    result=dict(cases=len(rows),failures=sum(bool(r['issues']) for r in rows),rows=rows)
    life.write(BASE / ('clock-qualification-'+'-'.join(variants)+'-'+'-'.join(models)+'.json'),result)
    life.write(BASE / 'clock-qualification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


def capture_audit():
    from PIL import Image
    rows=[r for p in BASE.glob('profile-*.json') for r in json.loads(p.read_text())['rows']
          if r['phase']==0 and r['iteration']==0]
    references={}
    masks={}
    results=[]
    for row in sorted(rows,key=lambda r:r['variant']!='baseline'):
        folder=BASE / row['variant'] / f'style-{row["style"]}-order-{row["order"]}-q0'
        for direction in ('entry','exit'):
            key=(row['style'],row['order'],direction)
            if row['variant']=='baseline':
                mask=[]
                if direction=='entry' and row['style']==0:
                    mask=[(x,y,x+16,y+16) for x in (72,104,136) for y in (40,72,104)]
                elif direction=='exit':
                    mask=[(88,16,96,24)]
                    attrs=bytes.fromhex(row['menu']['attrs'])
                    mask.extend((x*8,y*8,x*8+8,y*8+8) for y in range(18) for x in range(20)
                                if attrs[y*21+x]&7==3)
                masks[key]=mask
            def pixels(path):
                with Image.open(path) as source:
                    picture=source.convert('RGB')
                    for box in masks[key]:
                        picture.paste((0,0,0),box)
                    return picture.tobytes()
            paths=sorted(folder.glob(direction+'-0-*.ppm'))
            target=pixels(paths[-1])
            if row['variant']=='baseline': references[key]=target
            with gzip.open(folder / (direction+'-0-events.json.gz'),'rt') as stream:
                events=json.load(stream)
            frames={e['display']:e for e in events if e['event']=='perf_frame'}
            matches=[pixels(p)==target for p in paths]
            first=next(i for i,v in enumerate(matches) if v)
            frame=int(paths[first].stem.rsplit('-',1)[1])
            origin=row[direction]['ready']['t']-row[direction]['input_to_ready_ms']*HZ/1000
            ms=(frames[frame]['boundary_t']-origin)*1000/HZ
            results.append(dict(variant=row['variant'],style=row['style'],order=row['order'],direction=direction,
                static_destination_ms=ms,static_destination_frames=ms/FRAME_MS,
                same_static_pixels=target==references[key],reverted=not all(matches[first:]),
                ignored_regions=masks[key]))
    result=dict(cases=len(results),failures=sum(not r['same_static_pixels'] or r['reverted'] for r in results),rows=results)
    life.write(BASE / 'capture-audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


def exit_audit(variants):
    rows=[]
    for variant in variants:
        folder=BASE / 'exit-matrix' / variant / 'results'
        report=json.loads((folder / 'report.json').read_text())
        blocked_palette=blocked_vram=0
        for path in folder.glob('*/trace.jsonl'):
            for line in path.open():
                event=json.loads(line)
                if event['event']!='write':
                    continue
                blocked_palette += event['address'] in (0xff69,0xff6b) and bool(event['pal_blocked'])
                blocked_vram += 0x8000<=event['address']<0xa000 and bool(event['vram_blocked'])
        rows.append(dict(variant=variant,cases=len(report['results']),
            shifted_cases=sum(bool(r['shifted_frames']) for r in report['results']),
            blocked_palette_writes=blocked_palette,blocked_vram_writes=blocked_vram))
    result=dict(cases=sum(r['cases'] for r in rows),
        failures=sum(bool(r['shifted_cases'] or r['blocked_palette_writes'] or r['blocked_vram_writes']) for r in rows),
        rows=rows)
    life.write(BASE / 'exit-hardware-audit.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','extend','profile','report','routes','qualify','exit-matrix','exit-audit','capture-audit'))
    p.add_argument('--variants',nargs='+',default=['baseline','reference'])
    p.add_argument('--jobs',type=int,default=6)
    p.add_argument('--models',nargs='+',default=['E'])
    args=p.parse_args()
    life.BASE=BASE
    if args.action=='prepare': prepare()
    elif args.action=='extend': prepare(True)
    elif args.action=='profile': life.profile(args.variants,args.jobs)
    elif args.action=='routes': life.routes(args.variants,args.jobs)
    elif args.action=='qualify': qualify(args.variants,args.models)
    elif args.action=='exit-matrix': life.exit_matrix(args.variants)
    elif args.action=='exit-audit': exit_audit(args.variants)
    elif args.action=='capture-audit': capture_audit()
    else: report()
