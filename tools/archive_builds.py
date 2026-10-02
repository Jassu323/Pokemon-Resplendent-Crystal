"""Preserve small historical recipes and notes before removing generated builds.

The archive contains no cartridges, battery saves, emulator states, screenshots,
compiled programs or raw instruction traces. Cleanup is a separate explicit step
and verifies the complete top-level inventory and every archived source hash.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
ARCHIVE = ROOT / 'tools/dex_timing/historical_builds'
NOTES = ROOT / 'docs/archived/build-history'
REFERENCE = 'dex-scheduler-reference-20260920'
REFERENCE_COMMIT = '0ebdaea76'
SOURCE_SUFFIXES = {'.py', '.sh', '.asm', '.c', '.inc'}
PARAMETERS = {
    'scope', 'species', 'policy', 'policies', 'mode', 'variant', 'cutoff', 'dispatch_t',
    'guard_t', 'viewport_guard_t', 'finish_guard_t', 'finish_margin_t', 'timer_delay_t',
    'forced_entry_phase', 'quiet_oam', 'admission', 'prefix_bounds', 'actual_states',
    'initial_state_scope', 'rom_sha256', 'sym_sha256', 'state_sha256', 'core_revision',
    'input_sha256', 'fixture_sha256', 'accepted_sha256', 'prototype_sha256',
    'background_control_sha256', 'helper_bytes', 'helper_sizes', 'patches',
    'existing_scratch_byte', 'additional_vram_tiles', 'additional_vram_bytes',
    'no_new_rom0_wram0_wramx_hram_allocations', 'provenance', 'private_experiment',
    'fixture', 'configs', 'configuration', 'parameters', 'jobs',
}
DETAIL_KEYS = {'host', 'trace', 'events', 'lifecycle', 'instructions', 'operations',
               'core_points', 'publications', 'ledger', 'decisions', 'waits', 'writes',
               'frames', 'displayed_frames', 'irq_ledger', 'open_ledger', 'points',
               'payload_zlib_base85', 'host_sources', 'cases', 'results'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(value, depth=0):
    if depth > 5:
        return {'count': len(value)} if isinstance(value, (dict, list)) else value
    if isinstance(value, dict):
        return {key: ({'count': len(item)} if isinstance(item, (dict, list)) else item)
                if key in DETAIL_KEYS else compact(item, depth + 1)
                for key, item in value.items() if key != 'payload_zlib_base85'}
    if isinstance(value, list):
        if len(value) <= 24:
            return [compact(item, depth + 1) for item in value]
        return {'count': len(value), 'examples': [compact(item, depth + 1) for item in value[:3]]}
    if isinstance(value, str) and len(value) > 1024:
        return {'characters': len(value)}
    return value


def family(name):
    if name == '.DS_Store':
        return ('Finder folder metadata; not a build or test input.', 'none', 'docs/index.md')
    if name == REFERENCE:
        return ('Frozen instrumented scheduler reference, before the production scheduler replacement.',
                'reference', 'docs/archived/dex-scheduler/dex_scheduler_implementation_preflight.md')
    if name.startswith('dex-icon-buffer') or name == 'dex-buffered-icons-test':
        descriptions = {
            'dex-icon-buffer-preflight': 'First alternate footprint/type allocation; normal-entry repair added a display interval in some return tests.',
            'dex-icon-buffer-fast-repair': 'Fast footprint-only reentry repair; still one extra display interval in four of twelve paired returns.',
            'dex-icon-buffer-return-repair': 'Final prototype: restore footprint set A during B-return, invalidate its old tag when set B is written; accepted by the user.',
            'dex-buffered-icons-test': 'User-facing copy of the accepted return-repair prototype, not a separate implementation.',
        }
        return (descriptions[name], 'overlay', 'docs/pokedex_internal_transition_investigation.md')
    if name in ('dex-selective-mask-ab', 'dex-background-mask-ab'):
        return ('Private A/B palette mask: ' + ('whiten the portrait, footprint and badges; rejected presentation.'
                if name == 'dex-selective-mask-ab' else
                'white portrait with panel-colored icon masks; superseded by retaining the outgoing icons.'),
                'overlay', 'docs/pokedex_internal_transition_investigation.md')
    if name.startswith('dex-internal-transitions'):
        return ('Selected-to-Selected handoff investigation: ' + name.removeprefix('dex-internal-transitions').strip('-') +
                '; compare palette-only, atomic maps, delayed hiding and integrated final-link controls.',
                'tools.dex_timing.internal_transitions', 'docs/pokedex_internal_transition_investigation.md')
    if name == 'dex-buffered-icons-production':
        return ('Production integration of the accepted buffered icons; all-species entry, playback, mask, return and buffer-alternation regressions.',
                'production-icons', 'docs/pokedex_internal_transition_investigation.md')
    if name.startswith('dex-timing-budget'):
        return ('Host-only upload/publication admission experiment: ' + name.removeprefix('dex-timing-budget').strip('-') +
                '; LY windows, quiet owner IRQs, timer phases and conservative dispatch bounds.',
                'tools.dex_timing.budget_experiment', 'docs/archived/dex-scheduler/dex_publication_budget_results.md')
    if name.startswith('dex-timing-policies'):
        return ('Host-only completion-ledger policy experiment: ' + name.removeprefix('dex-timing-policies').strip('-') +
                '; compare producer-clock, readiness, early work and bounded tail work.',
                'tools.dex_timing.scheduler_experiment', 'docs/archived/dex-scheduler/dex_scheduler_policy_experiments.md')
    if name.startswith('dex-timing-steady'):
        return ('Steady-state recovery experiment: ' + name.removeprefix('dex-timing-steady').strip('-') +
                '; budgeted publication and return-to-owner wait behavior.',
                'tools.dex_timing.recovery_experiment', 'docs/archived/dex-scheduler/dex_steady_publication_results.md')
    if name.startswith('dex-timing-finish'):
        return ('Finishing-upload experiment: ' + name.removeprefix('dex-timing-finish').strip('-') +
                '; complete a ready stage only inside the validated timer/publication reserve.',
                'tools.dex_timing.finish_experiment', 'docs/archived/dex-scheduler/dex_garchomp_finishing_results.md')
    if name.startswith('dex-timing-queue'):
        return ('Exact map-queue assembly cost experiment: ' + name.removeprefix('dex-timing-queue').strip('-') +
                '; native, row-unrolled and tile-unrolled alternatives.',
                'tools.dex_timing.queue_experiment', 'docs/archived/dex-scheduler/dex_queue_construction_results.md')
    if name.startswith('dex-timing-gather') or name.startswith('dex-timing-headroom'):
        return ('Gather/queue optimization and finishing-headroom experiment: ' + name +
                '; ordered source tiles, unrolled map construction and larger reserves.',
                'tools.dex_timing.gather_experiment', 'docs/archived/dex-scheduler/dex_headroom_synth_results.md')
    if name.startswith('dex-timing-synth'):
        return ('Synthesized-cry controls for the proposed shared-clock producer and finishing reserve.',
                'tools.dex_timing.gather_experiment', 'docs/archived/dex-scheduler/dex_headroom_synth_results.md')
    if name == 'dex-timing-implementation-preflight':
        return ('Assembled cost-only production-policy draft and decision/admission contracts; not an end-to-end game build.',
                'tools.dex_timing.implementation_preflight', 'docs/archived/dex-scheduler/dex_scheduler_implementation_preflight.md')
    if name.startswith('dex-target') or name.startswith('dex-scheduler-') or name == 'dex-timing-additional-actual-states':
        return ('Compiled scheduler integration/target-regression work: ' + name +
                '; Groudon late-event targets and Spheal/Sealeo/Snorlax unused-tail controls.',
                'tools.dex_timing.target_regression', 'docs/archived/dex-scheduler/dex_target_regression_results.md')
    if name.startswith('dex-full-replays'):
        return ('Full main/hold/idle linked replay and independent SameBoy comparison; actual captured inputs distinguished from synthetic continuation.',
                'tools.dex_timing.full_replay', 'docs/archived/dex-scheduler/dex_full_replay_results.md')
    if name.startswith('dex-timing') or name.startswith('dex-host') or name.startswith('luxray-') or name == 'dex-boundary-comparison.json':
        return ('Host timing calibration/boundary evidence: ' + name +
                '; linked instruction costs, IRQ/timer phase, LCD waits and captured-state comparisons.',
                'tools/verify_dex_timing.py', 'docs/archived/dex-scheduler/dex_timing_model_history.md')
    if name.startswith('dex-listing') or name == 'dex-grid-presence':
        return ('Listing restoration/cache ownership diagnostic: ' + name +
                '; skipped/late palettes, LCD-off flashes and presence flags instead of stale transient IDs.',
                'tools.dex_timing.listing_restoration', 'docs/pokedex_listing_restoration_investigation.md')
    if name.startswith('dex-category'):
        return ('Mew embedded terminator/category control-character investigation and corrected Mew/Drapion category-data regressions.',
                'archived-script', 'docs/pokedex_selected_bug_backlog.md')
    if name.startswith('dex-cry-ownership'):
        return ('Early Dex-local cry cancellation and ownership handoff: synth resumption, outgoing exhaustion and active incoming-header overwrite.',
                'tools.dex_timing.cry_ownership', 'docs/pokedex_cry_ownership_investigation.md')
    if name == 'dex-description-ui':
        return ('Description shell/page-badge, footprint background and compact type-badge implementation with all-species UI audits.',
                'tools.dex_timing.description_ui', 'docs/pokedex_description_ui.md')
    if name in ('dex-cold-listing', 'dex-instrumentation-cleanup'):
        return ('All-species real-input cold entry and instrumentation-free linked timing/pixel/audio acceptance.',
                'tools.dex_timing.cold_listing', 'docs/dex_instrumentation_cleanup.md')
    if name.startswith('new-dex-entry-sweep'):
        return ('New Dex Entry input-timing/species/phase sweep: ' + name +
                '; uninterrupted, A, B and A+B interruption plus exact publication and cry completion.',
                'tools.dex_timing.new_entry_sweep', 'docs/new_dex_entry_regression_results.md')
    if name.startswith('new-dex-entry') or name == 'new-entry-page-experiment':
        return ('New Dex Entry resident dictionary/owner implementation and catch-to-entry transaction experiment: ' + name +
                '; standard/restored Master Ball, delayed publication and Mewtwo description acknowledgment controls.',
                'tools.dex_timing.new_entry', 'docs/new_dex_entry_regression_results.md')
    if name == 'new-dex-save-setup':
        return ('Historical backed-up caught-flag test setup; never run the old live-save editing script automatically.',
                'manual-only', 'docs/dex_new_entry_testing.md')
    if name == 'pack-transition-review':
        return ('Pack between-pouch transition comparison used as a presentation/ownership reference for Dex paging.',
                'archived-script', 'docs/pokedex_internal_transition_investigation.md')
    raise ValueError('Unclassified historical output: ' + name)


def archive():
    if (ARCHIVE / 'manifest.json').exists():
        raise ValueError('Archive already exists; do not overwrite its historical inventory')
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)
    original = {}
    snapshot = BUILD / REFERENCE
    if snapshot.exists():
        stream = io.BytesIO(subprocess.check_output(['git', 'archive', REFERENCE_COMMIT], cwd=ROOT))
        with tarfile.open(fileobj=stream) as tar:
            original = {entry.name: tar.extractfile(entry).read() for entry in tar if entry.isfile()}
    records, preserved = [], []
    for entry in sorted(BUILD.iterdir()):
        purpose, recipe, document = family(entry.name)
        paths = sorted(entry.rglob('*')) if entry.is_dir() else [entry]
        files = [path for path in paths if path.is_file()]
        record = dict(name=entry.name, purpose=purpose, recipe=recipe, document=document,
                      generated_bytes=sum(path.stat().st_size for path in files),
                      files=len(files), sources=[], notes=[], parameters=[], identities={})
        for path in files:
            relative = path.relative_to(entry) if entry.is_dir() else Path(path.name)
            source = path.suffix in SOURCE_SUFFIXES or path.name == 'Makefile'
            if entry.name == REFERENCE:
                source = source or ('fixtures' in relative.parts and path.suffix in ('.json', '.txt'))
                if source and original.get(str(relative)) == path.read_bytes():
                    source = False
            if source:
                target = ARCHIVE / entry.name / 'sources' / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                item = dict(path=str(target.relative_to(ROOT)), sha256=digest(target))
                preserved.append(item)
                record['sources'].append(str(relative))
            if path.suffix == '.md':
                target = NOTES / entry.name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                record['notes'].append(str(target.relative_to(ROOT)))
                preserved.append(dict(path=str(target.relative_to(ROOT)), sha256=digest(target)))
            if path.suffix == '.json' and path.stat().st_size < 24_000_000 and len(record['parameters']) < 150:
                try:
                    data = json.loads(path.read_text())
                except (ValueError, UnicodeError):
                    continue
                if isinstance(data, dict):
                    parameters = {key: compact(value) for key, value in data.items() if key in PARAMETERS}
                    if parameters and parameters not in [r['values'] for r in record['parameters']]:
                        record['parameters'].append(dict(file=str(relative), values=parameters))
                    if path.name.endswith('summary.json') or path.name in ('provenance.json', 'builds.json'):
                        record.setdefault('outcomes', {})[str(relative)] = compact(data)
                elif isinstance(data, list) and path.name.endswith('summary.json'):
                    record.setdefault('outcomes', {})[str(relative)] = compact(data)
            if relative.parent == Path('.') and path.suffix in ('.gbc', '.sym'):
                record['identities'][str(relative)] = digest(path)
        records.append(record)
    manifest = dict(format='historical-build-recipes-v1', archived='2026-10-01',
        current_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        sameboy_revision=subprocess.check_output(['git', '-C', str(Path.home() / 'Documents/GitHub/SameBoy'),
                                                 'rev-parse', 'HEAD'], text=True).strip(),
        reference_commit=REFERENCE_COMMIT, records=records, preserved_files=preserved)
    (ARCHIVE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    catalog = [
        '# Historical Build Catalog', '', 'Archived 2026-10-01 after accepting buffered Description icons.', '',
        'Generated cartridges, copied saves/states, images, raw traces, compiled runners and large reports',
        'were removed from the ignored `build/` directory. This catalog lists every former top-level',
        'output, including calibration files that were not distinct ROM builds.', '',
        '## Reproduction', '',
        'The basic rebuild/restore script is `tools/rebuild_historical.py`. List IDs with `--list`;',
        'inspect or restore one with `--id NAME --output /private/tmp/reproduction`. It copies only',
        'the preserved sources and parameters, never a user save. `--build-reference` recreates the',
        'instrumented reference from Git plus archived source overrides and checks its ROM hash.', '',
        'Private overlays retain their original assembly, patch sites, fixed addresses and input hashes.',
        'Use `--overlay --base-rom PATH --base-sym PATH` with the matching baseline to reconstruct a',
        'supported overlay. Old fixed-address helpers must not be applied to a new link.', '',
        'Host experiments often were counterfactual policies rather than playable ROMs. Their maintained',
        'module and recorded parameter grid are listed below; use the module help and the linked',
        'investigation for the complete command. Some early scripts contain original absolute paths.',
        'Restore them under their former directory or adjust input paths in an isolated checkout.', '',
        'Matching battery saves, authentic catch/start states and the licensed CGB boot ROM are external',
        'inputs, not retained here. New fresh checkpoints can test current behavior, but they do not',
        'recreate a historical captured timer/LCD phase. Portable sanitized timing fixtures already',
        'tracked under `tools/dex_timing/fixtures/` remain available. No bit-identical capture replay is',
        'promised without matching inputs. Nothing in this archive is selected by ordinary `make`.', '',
        'RGBDS: 1.0.1. SameBoy source revision: `' + manifest['sameboy_revision'] + '`.', '',
        'Machine-readable identities, parameter grids and compact outcomes: ',
        '`tools/dex_timing/historical_builds/manifest.json`. Detailed retained notes are below.', '',
    ]
    for record in records:
        catalog += ['## ' + record['name'], '', record['purpose'], '',
                    '- Basic recipe: `' + record['recipe'] + '`; inspect with',
                    '  `python3 tools/rebuild_historical.py --id ' + record['name'] + '`.',
                    '- Details: [' + Path(record['document']).stem + '](' +
                    '../' + record['document'].removeprefix('docs/') + ').',
                    f'- Preserved: {len(record["sources"])} source/recipe files, {len(record["notes"])} notes; '
                    f'{len(record["parameters"])} parameter records. Removed output: {record["generated_bytes"]:,} bytes.', '']
        for note in record['notes']:
            catalog += ['- [' + Path(note).name + '](' + note.removeprefix('docs/archived/') + ').']
        if record['notes']:
            catalog.append('')
    (ROOT / 'docs/archived/build-history.md').write_text('\n'.join(catalog) + '\n')
    print(json.dumps(dict(entries=len(records), preserved_files=len(preserved),
                         generated_bytes=sum(record['generated_bytes'] for record in records))))


def clean():
    manifest = json.loads((ARCHIVE / 'manifest.json').read_text())
    expected = {record['name'] for record in manifest['records']}
    actual = {entry.name for entry in BUILD.iterdir()}
    if actual != expected or BUILD.is_symlink():
        raise ValueError('Build inventory changed; cleanup refused')
    for item in manifest['preserved_files']:
        path = ROOT / item['path']
        if not path.is_file() or digest(path) != item['sha256']:
            raise ValueError('Preserved source verification failed: ' + str(path))
    if not (ROOT / 'docs/archived/build-history.md').is_file():
        raise ValueError('Build notes are missing')
    for entry in BUILD.iterdir():
        if entry.is_symlink() or entry.is_file():
            entry.unlink()
        else:
            shutil.rmtree(entry)
    print(json.dumps(dict(removed_entries=len(expected), retained_root_rom=(ROOT / 'pokecrystal.gbc').is_file())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean', action='store_true', help='Remove inventoried generated outputs after archive verification')
    args = parser.parse_args()
    clean() if args.clean else archive()
