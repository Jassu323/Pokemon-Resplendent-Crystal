"""Require fresh evidence and collect the two private-owner comparison results."""
import argparse
import json
from pathlib import Path
import re

from PIL import Image, ImageChops

from .assets import sha256
from .cold_listing import ROOT


def read(path):
    return json.loads(path.read_text())


def assembly(path, start=None, end=None):
    text = path.read_text()
    if start:
        text = text.split(start,1)[1]
    if end:
        text = text.split(end,1)[0]
    return [line.split(';',1)[0].strip() for line in text.splitlines()
            if line.split(';',1)[0].strip() and line.strip() != '.return']


def usage(path):
    text = path.read_text().split('\nROM0 bank')[0]
    return {kind:dict(used=int(used),free=int(free)) for kind,used,free in
            re.findall(r'(ROM0|ROMX|SRAM|WRAM0|WRAMX|HRAM): (\d+) bytes used / (\d+) free',text)}


def main(base):
    animations = read(base / 'all-animations/report.json')
    assert all(animations['qualification'][key] for key in
               ('complete_coverage','restoration_passed','logical_sequence_passed',
                'all_variant_timing_exact','visual_sequence_passed',
                'native_coverage_passed','native_issue_identities_match'))
    assert animations['native']['summary']['differing_issue_pairs'] == 0
    rows = {}
    original = Path(read(base / 'manifest.json')['source'])
    old_usage = usage(original / 'pokecrystal-dex-types.map')
    baseline = base / 'runtime-regression/baseline/candidate'
    for variant in ('runtime','precomputed'):
        folder = base / variant
        campaign = read(base / (variant+'-regression/full-regression.json'))
        assert campaign['merge_ready'],campaign['issues']
        phases = read(base / (variant+'-regression/phase-results.json'))
        assert not any(row['exit_code'] for row in phases),phases
        digest = sha256((folder / 'pokecrystal-dex-types.gbc').read_bytes())
        assert animations['rom_sha256s'][variant] == campaign['rom_sha256'] == digest
        models = {m:read(folder / 'type-tests' / ('' if m=='E' else 'cgb-'+m) / 'summary.json')
                  for m in ('0','A','B','C','D','E')}
        assert all(row.get('rom_sha256')==digest for row in models.values())
        assert all(row['raster']['register_or_bank_errors']==0 and row['idle']['bad_mode_writes']==0
                   for row in models.values())
        source = folder / 'candidate'
        identical = dict(
            lcd=assembly(source/'home/lcd.asm')==assembly(baseline/'home/lcd.asm'),
            normal_vblank=assembly(source/'home/vblank.asm','VBlank_Normal::','VBlank_SoundOnly::')==
                          assembly(baseline/'home/vblank.asm','VBlank_Normal::','VBlank_SoundOnly::'),
            wrapper=assembly(source/'home/vblank.asm','VBlank::','VBlankHandlers:')==
                    assembly(baseline/'home/vblank.asm','VBlank::','VBlankHandlers:'),
            ordinary_audio_engine=(source/'audio/engine.asm').read_bytes()==(baseline/'audio/engine.asm').read_bytes())
        assert all(identical.values()),identical
        current = usage(folder / 'pokecrystal-dex-types.map')
        delta = {key:current[key]['used']-old_usage[key]['used'] for key in current}
        audio = read(folder / 'audio-stress/summary.json')
        assert audio['songs']==122 and not audio['issues'] and audio['rom_sha256']==digest
        navigation = read(folder / 'audio-navigation/summary.json')
        assert navigation['songs']==122 and navigation['held_input'] and not navigation['issues'] and navigation['rom_sha256']==digest
        rows[variant] = dict(rom_sha256=digest,usage=current,delta_from_review_prototype=delta,
            ordinary_source_paths_identical=identical,
            performance=read(folder / 'comparison/summary.json'),
            type_models=models,audio={k:v for k,v in audio.items() if k!='rows'},
            audio_navigation={k:v for k,v in navigation.items() if k!='rows'},
            dex_cases=campaign['dex']['cases'],full_regression_issues=campaign['issues'],
            host_known_failures=len(campaign['host']['failures']),
            baseline_host_same=campaign['host']['no_new_failures'],
            battle=animations['summaries'][variant],phase_results=phases)
    result = dict(variants=rows,animations={k:animations[k] for k in
                  ('moves','catalogue_entries','renderer_calls','coverage','qualification','native')},
                  production_unchanged=sha256((ROOT/'pokecrystal.gbc').read_bytes())==
                                      read(base/'manifest.json')['production_sha256'],
                  linked_precomputed_extra_bytes=rows['precomputed']['usage']['ROMX']['used']-
                                                rows['runtime']['usage']['ROMX']['used'],
                  issues=[])
    assert result['production_unchanged']
    names = read(ROOT / 'tools/dex_timing/probes/type_matchups_workbook.json')['names']
    views = []
    for index,name in enumerate(names):
        pictures = [Image.open(base / variant / 'type-tests' / (name.lower()+'.png')).convert('RGB')
                    for variant in ('runtime','precomputed')]
        x,y = 8+(index%3)*48,8+(index//3)*14
        for picture in pictures:
            picture.paste((41,41,41),(x,y,x+8,y+8))
        assert pictures[0].size==pictures[1].size==(160,144)
        assert ImageChops.difference(*pictures).getbbox() is None,name
        views.append(dict(type=name,pixels_equal_except_cursor_blink=True))
    result['visual_equivalence'] = dict(selections=len(views),pixels_checked=len(views)*(160*144-64),views=views)
    chart = read(base / 'chart-phase-check/summary.json')
    assert chart['all_original_chart_durations_exact']
    assert chart['candidate_rom_sha256']==rows['runtime']['rom_sha256']
    proven = {(r['move'],r['side'],r['quarter']):r for r in chart['comparisons']}
    for row in animations['native']['comparisons']:
        if row['delta_frames'] not in (0,None):
            evidence = proven[row['move'],row['side'],0]
            assert evidence['original_chart_delta_t']==0 and evidence['changed_chart_delta_frames']==row['delta_frames']
    result['chart_start_phase_investigation'] = chart
    (base / 'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(production_unchanged=result['production_unchanged'],
          precomputed_extra_bytes=result['linked_precomputed_extra_bytes'],
          variants={v:{k:r[k] for k in ('rom_sha256','dex_cases','delta_from_review_prototype')}
                    for v,r in rows.items()}),indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True)
    main(parser.parse_args().base.resolve())
