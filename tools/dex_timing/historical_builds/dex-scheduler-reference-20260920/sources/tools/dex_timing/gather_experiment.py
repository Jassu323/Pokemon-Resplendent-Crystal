"""HOST-ONLY fixed 16-byte gather-copy prototype in a private ROM image.

Keep the original entry as a JP trampoline so all existing hooks still observe
the real call. Its extra 16 T is included, making this slightly slower than a
future in-place body replacement. No game source or cartridge file is written.
"""
from dataclasses import dataclass

from .assets import offset,sha256
from .cpu import ModelError
from .queue_experiment import PINNED_ROM


NAME='Pokedex_GatherReadyAnimationTiles'
ORIGINAL=bytes.fromhex(
    '0e 00 21 2f c7 cb 56 c8 cb 5e c0 fa 43 c7 21 42 c7 96 ea ef c6 af ea f0 c6 '
    'fa 37 c7 4f 06 00 79 6f 26 00 29 29 29 29 11 00 c8 19 54 5d fa 37 c7 4f '
    '06 00 21 60 cc 09 fa 37 c7 47 fa f0 c6 80 47 fa 33 c7 b8 28 2f fa f0 c6 '
    'fe 14 28 28 2a 47 fa ef c6 b8 38 20 28 1e e5 68 26 00 29 29 29 29 01 '
    '00 d0 09 06 10 2a 12 13 05 20 fa e1 fa f0 c6 3c ea f0 c6 18 c2 fa f0 c6 4f c9')


@dataclass(frozen=True)
class GatherPrototype:
    image: bytes
    manifest: dict


def gather_prototype(repo,base_image=None):
    if sha256(repo.rom)!=PINNED_ROM:
        raise ModelError('Gather prototype requires the captured link')
    bank,address=repo.symbols[NAME]
    original=offset((bank,address))
    image=bytearray(repo.rom if base_image is None else base_image)
    if image[original:original+len(ORIGINAL)]!=ORIGINAL:
        raise ModelError('Gather helper contract changed')
    begin=repo.symbols[NAME+'.copy_tile'][1]-address-2
    end=begin+8
    if ORIGINAL[begin:end]!=bytes.fromhex('06 10 2a 12 13 05 20 fa'):
        raise ModelError('Fixed-size tile copy moved')
    replacement=bytes((0x06,0))+bytes((0x2a,0x12,0x13))*16
    delta=len(replacement)-(end-begin)
    body=bytearray(ORIGINAL[:begin]+replacement+ORIGINAL[end:])
    def relocated(position):
        return position+delta if position>=end else position
    branches=[]
    for pattern in ('28 2f','28 28','38 20','28 1e','18 c2'):
        raw=bytes.fromhex(pattern)
        if ORIGINAL.count(raw)!=1:
            raise ModelError('Ambiguous gather branch')
        old=ORIGINAL.index(raw)
        target=old+2+int.from_bytes(raw[1:],'little',signed=True)
        new=relocated(old)
        displacement=relocated(target)-new-2
        if not -128<=displacement<128:
            raise ModelError('Gather branch exceeds relative range')
        body[new+1]=displacement&255
        branches.append(dict(old=old,new=new,old_target=target,new_target=relocated(target)))
    target_address=0x7800
    target=offset((bank,target_address))
    if bank!=0xa0 or any(image[target:target+len(body)]):
        raise ModelError('Gather prototype padding is not empty')
    image[target:target+len(body)]=body
    image[original:original+3]=bytes((0xc3,target_address&255,target_address>>8))
    image=bytes(image)
    return GatherPrototype(image,dict(scope='HOST_PRIVATE_INSTRUCTION_IMAGE_NOT_A_GAME_BUILD',
        base_rom_sha256=sha256(repo.rom),input_image_sha256=sha256(repo.rom if base_image is None else base_image),
        private_image_sha256=sha256(image),bank=bank,entry=address,target=target_address,
        original_bytes=ORIGINAL.hex(),replacement_bytes=body.hex(),branches=branches,
        trampoline_t=16,per_tile_saving_t=252,eventual_replacement_romx_delta=delta,
        rom0_delta=0,wram0_delta=0,wramx_delta=0,hram_delta=0))
