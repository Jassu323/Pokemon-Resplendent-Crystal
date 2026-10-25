"""Assemble executable counterfactuals in private ROM copies, never the game."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OUT = Path(os.environ.get('REGISTRATION_OUT', SOURCE))
sys.path.insert(0, str(ROOT))
from tools.dex_timing.assets import Repository, offset, read_symbols, sha256


def build():
    repo = Repository(ROOT, OUT/'fixture.gbc', OUT/'fixture.sym')
    assert sha256(repo.rom) == os.environ.get('REGISTRATION_ROM_SHA256', '407c4d29e08a47c5e5cce165eb4d171b62d4afbced665938950aa0a21b5d9fd3')
    source = SOURCE/'resident_preflight.asm'
    words = set(re.findall(r'[A-Za-z_][A-Za-z0-9_.]*', source.read_text()))
    lines = []
    for name in sorted(words & repo.symbols.keys()):
        bank, address = repo.symbols[name]
        lines.append(f'DEF {name} EQU ${address:04x}')
        if 'BANK_'+name in words:
            lines.append(f'DEF BANK_{name} EQU ${bank:x}')
    (OUT/'preflight_linked.inc').write_text('\n'.join(lines)+'\n')
    subprocess.run(['rgbasm','-I',str(OUT)+'/', '-o',str(OUT/'draft.o'),str(source)],check=True)
    subprocess.run(['rgblink','-o',str(OUT/'draft.bin'),'-n',str(OUT/'draft.sym'),
                    '-m',str(OUT/'draft.map'),str(OUT/'draft.o')],check=True)
    sym = read_symbols(OUT/'draft.sym')
    raw = (OUT/'draft.bin').read_bytes()
    image = bytearray(repo.rom)
    changes = []

    def install(name, location, old, new):
        assert len(old) == len(new)
        at = offset(location)
        assert image[at:at+len(old)] == old, (name, location, image[at:at+len(old)].hex(), old.hex())
        image[at:at+len(new)] = new
        changes.append(dict(name=name,bank=location[0],address=location[1],old=old.hex(),new=new.hex()))

    for start,end in [('ProtoHomeStart','ProtoHomeEnd'),('ProtoStart','ProtoEnd')]:
        a,b=offset(sym[start]),offset(sym[end])
        assert not any(repo.rom[a:b]), (start,end)
        install(start,sym[start],bytes(b-a),raw[a:b])

    def branch(op, target):
        return bytes([op])+target.to_bytes(2,'little')

    def replace_call(label, end, old_target, new_target):
        bank, lo=repo.symbols[label]
        hi=repo.symbols[end][1]
        old=branch(0xcd,repo.symbols[old_target][1])
        region=repo.rom[offset((bank,lo)):offset((bank,hi))]
        indexes=[i for i in range(len(region)-2) if region[i:i+3]==old]
        assert len(indexes)==1,(label,indexes)
        install(label,(bank,lo+indexes[0]),old,branch(0xcd,sym[new_target][1]))

    target=repo.symbols['NewPokedexEntry.AnimateFrontpicFrame']
    install('step',target,repo.rom[offset(target):offset(target)+3],branch(0xc3,sym['ProtoHomeStep'][1]))
    replace_call('VBlank_Normal.viewport_owned','VBlank_Normal.done',
                 'UpdateBGMapBuffer','ProtoHomeVBlank')
    lo=repo.symbols['DelayFrame'][1]
    hi=repo.symbols['DelayFrames'][1]
    old=branch(0xcd,repo.symbols['ServiceSampledCryAsync'][1])+b'\xc9'
    assert repo.rom[hi-4:hi]==old
    install('frame-tail',(0,hi-4),old,branch(0xc3,sym['ProtoHomeDelayTail'][1])+b'\x00')
    bank,lo=repo.symbols['NewPokedexEntry']
    hi=repo.symbols['NewPokedexEntry.ReturnFromDexRegistration'][1]
    region=repo.rom[offset((bank,lo)):offset((bank,hi))]
    old=b'\xaf\xea'+repo.symbols['wFrameCounter'][1].to_bytes(2,'little')
    assert region.count(old)==1
    install('exit',(bank,lo+region.index(old)),old,branch(0xcd,sym['ProtoHomeCancel'][1])+b'\x00')
    (OUT/'resident-private.gbc').write_bytes(image)
    scheduler_changes=list(changes)

    old_target=repo.symbols['Get2bpp'][1]
    for start,end in [('_GetFrontpic','_PrepareFrontpic'),('GetAnimatedEnemyFrontpic','LoadFrontpicTiles')]:
        bank,lo=repo.symbols[start]
        hi=repo.symbols[end][1]
        for opcode in [0xcd,0xc3]:
            old=branch(opcode,old_target)
            region=repo.rom[offset((bank,lo)):offset((bank,hi))]
            for i in range(len(region)-2):
                if region[i:i+3]==old:
                    install('startup-upload',(bank,lo+i),old,branch(opcode,sym['ProtoHomeUpload'][1]))
    assert len(changes)-len(scheduler_changes)==4
    (OUT/'resident-bulk-private.gbc').write_bytes(image)
    manifest=dict(scope='HOST_ONLY_EXECUTABLE_COUNTERFACTUAL_NOT_A_GAME_BUILD',
                  base_sha256=sha256(repo.rom),
                  rom0_bytes=sym['ProtoHomeEnd'][1]-sym['ProtoHomeStart'][1],
                  owner_romx_bytes=sym['ProtoOwnerEnd'][1]-sym['ProtoStart'][1],
                  bulk_romx_bytes=sym['ProtoEnd'][1]-sym['ProtoUpload'][1],
                  new_ram_bytes=0, reused_packed_map_bytes=49, reused_pair_scratch_bytes=98,
                  reused_sram_staging_bytes=512,
                  resident_sha256=sha256((OUT/'resident-private.gbc').read_bytes()),
                  resident_bulk_sha256=sha256((OUT/'resident-bulk-private.gbc').read_bytes()),
                  scheduler_changes=scheduler_changes, startup_changes=changes[len(scheduler_changes):])
    (OUT/'preflight-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return repo,sym,manifest


if __name__=='__main__':
    _,_,m=build()
    print({k:v for k,v in m.items() if not k.endswith('changes')})
