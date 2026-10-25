"""Read-only production checks for bounded Selected Description transactions."""
import argparse
import json
from pathlib import Path
import shutil

from .assets import Repository
from .cold_listing import Driver, KEY, ROOT
from .description_paging import compile_observer, description_pages, run_to, summarize_trace, validate_starts
from .description_ui import audit as audit_ui, audit_footprint, settle, settle_description_text
from .cry_ownership import validate_output


def wait_text(driver, pages, page):
    settle_description_text(driver, pages[page])


def toggle(driver, repo):
    run_to(driver, repo, 'PokedexSelectedMon_ToggleDescriptionPage', frames=4, keys=KEY['a'])
    run_to(driver, repo, 'PokedexSelectedMon_Update', frames=10)


def compare_controls(changed, control):
    """Compare deadlines and canonical publications, not scanline jitter."""
    rows = []
    for case in json.loads((changed / 'report.json').read_text()):
        label = f'{case["species"]}-{case["offset"] if case["offset"] is not None else "done"}'
        runs = [json.loads((directory / f'{label}-audit.json').read_text())
                for directory in (changed, control)]
        publications = [[(e['tick'], e['frame'], e['map'], e['picture'])
                         for e in events if e['event'] == 'publish'] for events in runs]
        stops = [[e for e in events if e['event'] == 'audio_stop'] for events in runs]
        natural = [next((e['t'] for e in events if not e['remaining']), None) for events in stops]
        rows.append(dict(species=case['species'], offset=case['offset'],
            exact_publication_deadlines=publications[0] == publications[1],
            publications=[len(p) for p in publications],
            natural_audio_completion=[t is not None for t in natural],
            natural_audio_delta=natural[0] - natural[1] if all(t is not None for t in natural) else None,
            requested_text_published=bool(case['physical_pages'] and case['physical_pages'][-1] == 1)))
    return rows


def run_case(driver, repo, starts, output, asset, action, delay):
    name = asset.name
    label = f'{name}-{action}-{delay}'
    prefix = output / label
    pages = description_pages(repo, name)
    driver.command(f'load {starts / f"{name}-start.s0"}')
    if delay:
        run_to(driver, repo, frames=delay)
    driver.command(f'dptrace {prefix} 0')
    driver.command('audit 1')
    driver.events.clear()
    outgoing_end = None
    result = dict(species=name, action=action, offset=delay)
    try:
        if action == 'a+b':
            run_to(driver, repo, 'PokedexSelectedMon_Leave', frames=4, keys=KEY['a'] | KEY['b'])
            outgoing_end = driver.command('peek')['t']
        elif action == 'held-a':
            run_to(driver, repo, frames=24, keys=KEY['a'])
        else:
            if action != 'area-control':
                toggle(driver, repo)
            if action == 'two-pages':
                wait_text(driver, pages, 1)
                run_to(driver, repo, frames=2)
                toggle(driver, repo)
            elif action == 'rapid-a':
                for _ in range(7):
                    run_to(driver, repo, frames=2)
                    toggle(driver, repo)
            elif action == 'b-pending':
                run_to(driver, repo, 'PokedexSelectedMon_Leave', frames=4, keys=KEY['b'])
                outgoing_end = driver.command('peek')['t']
            elif action == 'species-pending':
                run_to(driver, repo, 'PokedexSelectedMon_ChangeSpecies', frames=4, keys=KEY['down'])
                outgoing_end = driver.command('peek')['t']
            elif action in ('area-pending', 'area-control'):
                for _ in range(8):
                    if driver.command('dpstatus')['footer'] == 3:
                        break
                    driver.run(('selected',), key='right')
                    driver.run(('selected',))
                    driver.run(('selected',))
                else:
                    raise RuntimeError('Footer navigation did not reach Area')
                run_to(driver, repo, 'PokedexSelectedMon_Area', frames=4, keys=KEY['a'])
                outgoing_end = driver.command('peek')['t']

        if action in ('a+b', 'b-pending'):
            state = driver.run(('listing',), frames=600)
            if state['hit'] != 'listing':
                raise RuntimeError('B cancellation did not restore Listing')
            driver.run(frames=3)
            result['returned_to_listing'] = True
        elif action in ('area-pending', 'area-control'):
            state = run_to(driver, repo, 'Pokedex_GetArea.loop', frames=600)
            if state['state'] != 4:
                raise RuntimeError('Area action did not enter its owner')
            run_to(driver, repo, 'Pokedex_GetArea.a_b', frames=4, keys=KEY['b'])
            state = driver.run(('selected', 'animation_miss', 'audio_miss'), frames=600)
            if state['hit'] != 'selected':
                raise RuntimeError('Area return did not restore Selected')
            settle(driver)
            driver.run(frames=3)
            result['ui_issues'] = audit_ui(repo, driver.command('ui')) + audit_footprint(repo, name, driver.command('ui'))
        else:
            settle(driver)
            if action == 'species-pending':
                driver.run(frames=3)
                state = driver.command('peek')
                ui = driver.command('ui')
                if ui['page']:
                    raise RuntimeError('Species handoff retained the outgoing requested page')
                result['ui_issues'] = audit_ui(repo, ui)
            else:
                ui = driver.command('ui')
                desired = ui['page']
                wait_text(driver, pages, desired)
                driver.run(frames=3)
                result['ui_issues'] = audit_ui(repo, driver.command('ui')) + audit_footprint(repo, name, ui)
                result['final_page'] = desired
        driver.command('dpstop')
        driver.command('audit 0')
        trace = [json.loads(line) for line in prefix.with_suffix('.jsonl').read_text().splitlines()]
        outgoing = [e for e in trace if outgoing_end is None or e['t'] < outgoing_end]
        result.update(summarize_trace(outgoing, asset, pages))
        end = trace[-1]
        result['pending_job_at_end'] = bool(end['text_state'] or end['owner_request'])
        result['animation_misses'] = [e for e in driver.events if e['event'] == 'animation_miss']
        # Owner cancellation can exhaust the outgoing cry during a transition.
        # Distinguish that from a miss while this Selected portrait is active.
        result['active_audio_misses'] = [e for e in driver.events if e['event'] == 'audio_miss'
            and (outgoing_end is None or e['t'] < outgoing_end)]
        result['transition_audio_misses'] = [e for e in driver.events if e['event'] == 'audio_miss'
            and outgoing_end is not None and e['t'] >= outgoing_end]
        result['accepted_toggles'] = sum(e['event'] == 'phase' and e['phase'] == 'toggle' for e in trace)
        if action == 'held-a' and result['accepted_toggles'] != 1:
            raise RuntimeError('Held A generated unexpected repeated toggles')
        if action == 'rapid-a' and result['accepted_toggles'] != 8:
            raise RuntimeError('Rapid A did not accept all eight distinct presses')
        result['issues'] = [field for field in (
            'ui_issues', 'pending_job_at_end', 'animation_misses', 'active_audio_misses',
            'invalid_vram_portrait_frames', 'invalid_rendered_portrait_frames',
            'changed_header_frames', 'invalid_text_frames', 'invalid_rendered_text_frames') if result.get(field)]
        result['status'] = 'fail' if result['issues'] else 'pass'
    except (RuntimeError, ValueError) as error:
        driver.command('dpstop')
        driver.command('audit 0')
        result.update(status='error', error=str(error), failure=driver.evidence(prefix))
    prefix.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return {k: v for k, v in result.items() if k not in ('physical_pages', 'half_copy_timing')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--starts', type=Path)
    parser.add_argument('--compare-controls', type=Path)
    parser.add_argument('--rom', type=Path, default=ROOT / 'pokecrystal.gbc')
    parser.add_argument('--sym', type=Path, default=ROOT / 'pokecrystal.sym')
    parser.add_argument('--species', nargs='+', default=['meganium', 'dusknoir', 'luxray', 'garchomp', 'weavile'])
    parser.add_argument('--offsets', nargs='+', type=int, default=[0, 4, 16])
    parser.add_argument('--actions', nargs='+', default=[
        'two-pages', 'rapid-a', 'held-a', 'a+b', 'b-pending', 'species-pending', 'area-pending'],
        choices=('two-pages', 'rapid-a', 'held-a', 'a+b', 'b-pending', 'species-pending', 'area-pending', 'area-control'))
    args = parser.parse_args()
    if not args.starts:
        parser.error('--starts is required')
    inputs = [args.starts, args.rom, args.sym]
    if args.compare_controls:
        inputs.append(args.compare_controls)
    output = validate_output(args.output, inputs)
    output.mkdir(parents=True, exist_ok=True)
    if args.compare_controls:
        result = compare_controls(args.starts, args.compare_controls)
        (output / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(dict(cases=len(result), exact_deadline_matches=sum(r['exact_publication_deadlines'] for r in result),
            text_published=sum(r['requested_text_published'] for r in result),
            audio_delta_range=[min(r['natural_audio_delta'] for r in result if r['natural_audio_delta'] is not None),
                               max(r['natural_audio_delta'] for r in result if r['natural_audio_delta'] is not None)]), indent=2))
        return
    for source, suffix in ((args.rom, 'gbc'), (args.sym, 'sym')):
        shutil.copy2(source, output / f'pokecrystal-desc-diagnostic.{suffix}')
    repo = Repository(ROOT, output / 'pokecrystal-desc-diagnostic.gbc', output / 'pokecrystal-desc-diagnostic.sym')
    validate_starts(args.starts, dict(original_rom_sha256=repo.hashes['rom_sha256']), repo.hashes['sym_sha256'])
    shutil.copy2(args.starts / 'test-only-caught.sav', output / 'test-only-caught.sav')
    core = compile_observer(repo, Path('/Users/jakeadams/Documents/GitHub/SameBoy'), output)
    driver = Driver(core, output / 'pokecrystal-desc-diagnostic.gbc',
        Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin'),
        output / 'test-only-caught.sav', output / 'core.log')
    results = []
    try:
        for asset in repo.load(set(args.species)):
            for action in args.actions:
                for delay in args.offsets:
                    result = run_case(driver, repo, args.starts, output, asset, action, delay)
                    results.append(result)
                    print(json.dumps(result), flush=True)
    finally:
        driver.close()
    (output / 'report.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
