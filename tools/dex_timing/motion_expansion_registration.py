"""Retain authentic current-link catches for the New Entry input sweep."""
import argparse
import json
from pathlib import Path
import shutil

from .animation_reference import OUTPUT, configuration
from .assets import Repository, sha256
from .new_entry_sweep import ORIGINAL


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant',default='expanded')
    args=parser.parse_args()
    cfg=configuration(args.variant)
    repo=Repository(Path(cfg['root']),Path(cfg['rom']),Path(cfg['sym']))
    root=OUTPUT/(args.variant+'-qualification')
    target=root/'registration'
    target.mkdir(exist_ok=True)
    catches=[]
    for species in ORIGINAL:
        source=root/'audio/q0'/f'{species}-catch'
        result=json.loads((source/'result.json').read_text())
        assert not result['issues'], result
        state=source/'registration.s0'
        output=target/f'{species}-registration.s0'
        shutil.copy2(state,output)
        catches.append(dict(species=species,registration_sha256=sha256(output.read_bytes()),
                            source=str(source),source_report_sha256=sha256((source/'result.json').read_bytes()),
                            result=result))
    report=dict(**repo.hashes,catches=catches,
                provenance='Real catch input; checkpoint at NewPokedexEntry; matching delivered ROM')
    (target/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(catches=len(catches),registration=str(target))))


if __name__=='__main__':main()
