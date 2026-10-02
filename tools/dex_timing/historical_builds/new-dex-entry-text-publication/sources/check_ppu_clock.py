"""Explain the two newly covered Yanmega phase-clock assertions without relaxing them."""
import gzip
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from dex_timing.assets import Repository
from dex_timing.new_entry import compile_core, run, display_clock_matches
from dex_timing.new_entry_sweep import audit

base = ROOT / 'build/new-dex-entry-text-publication'
out = base / 'ppu-clock-control'
out.mkdir(exist_ok=True)
repo = Repository(ROOT, ROOT / 'pokecrystal.gbc', ROOT / 'pokecrystal.sym')
binary = compile_core(repo, Path.home() / 'Documents/GitHub/SameBoy', out, 'trace')
os.environ['REGISTRATION_TIMER_FIRST_CLOCKS'] = '182'
os.environ['REGISTRATION_COMPACT'] = '1'
asset = repo.load(['yanmega'])[0]
report = []
for mode in (1, 2):
    name = f'yanmega-182-{mode}'
    old = [json.loads(line) for line in gzip.open(base / 'phases' / (name + '.jsonl.gz'), 'rt')]
    new = run(binary, [ROOT / 'pokecrystal.gbc', base / 'full/yanmega-generated.s0',
                       base / 'full/yanmega.references', mode], out / name)
    def original_events(trace):
        return [{k: v for k, v in e.items() if k not in ('ppu_t', 'ppu_pending_8mhz')} for e in trace]
    assert original_events(new) == old, 'Observation changed linked execution'
    row = audit(asset, new, dict(name=name, family='stress'))
    frames = [e for e in new if e['event'] == 'display' and e['phase'] == 1 and e['serial'] and e['type'] == 0]
    assert display_clock_matches(frames) and row['status'] == 'pass', row
    drift = [e for e in frames if abs(e['t']-frames[0]['t']-(e['number']-frames[0]['number'])*70224)>4]
    row.update(original_trace_unchanged=True, first_frame=frames[0], cpu_clock_outliers=drift)
    report.append(row)
    print(json.dumps(row), flush=True)
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
