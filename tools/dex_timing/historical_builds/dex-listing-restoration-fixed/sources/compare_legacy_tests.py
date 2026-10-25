import io
import json
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'tools'))
import test_dex_timing as timing

original = timing.Repository
reports = {}
for name, folder in (('baseline', root / 'build/dex-listing-restoration-fixed/baseline-source'),
                     ('fixed', root)):
    timing.Repository = lambda source, *args, folder=folder: original(
        source, folder / 'pokecrystal.gbc', folder / 'pokecrystal.sym')
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromModule(timing))
    reports[name] = dict(tests=result.testsRun, skipped=len(result.skipped),
        failures=[dict(test=str(test), message=trace.splitlines()[-1]) for test, trace in result.failures],
        errors=[dict(test=str(test), message=trace.splitlines()[-1]) for test, trace in result.errors])
    (Path(__file__).parent / f'legacy-{name}.txt').write_text(stream.getvalue())
baseline = {r['test'] for kind in ('failures', 'errors') for r in reports['baseline'][kind]}
fixed = {r['test'] for kind in ('failures', 'errors') for r in reports['fixed'][kind]}
reports['new_failures'] = sorted(fixed - baseline)
(Path(__file__).parent / 'legacy-test-comparison.json').write_text(json.dumps(reports, indent=2) + '\n')
print(json.dumps({name: {k: len(v) if isinstance(v, list) else v for k, v in result.items()}
                  for name, result in reports.items() if isinstance(result, dict)}))
print('New failures:', reports['new_failures'])
