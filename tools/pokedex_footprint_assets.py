"""Convert verified Emerald/Platinum footprint originals for a private Dex build."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def convert(original):
    if original.size not in ((16, 16), (32, 16)):
        raise ValueError('Expected a 16x16 footprint or padded 32x16 Platinum image')
    rgb = original.convert('RGB')
    if original.width == 32 and len(rgb.crop((16, 0, 32, 16)).getcolors(257)) != 1:
        raise ValueError('The Platinum padding contains nonuniform pixels')
    crop = rgb.crop((0, 0, 16, 16))
    allowed = {(255, 255, 255), (0, 0, 0), (98, 98, 98)}
    colors = {color for count, color in crop.getcolors(257)}
    if not colors <= allowed or len(colors) > 2:
        raise ValueError(f'Unexpected source footprint colors: {colors}')
    # RGBGFX maps white to bit 0 (white mark), black to bit 1 (panel color).
    output = Image.new('P', (16, 16))
    output.putpalette([255, 255, 255, 0, 0, 0] + [0] * 762)
    output.putdata([int(crop.getpixel((x, y)) == (255, 255, 255))
                    for y in range(16) for x in range(16)])
    return output


def import_assets(source_manifest, target):
    source_manifest, target = source_manifest.resolve(), target.resolve()
    if not target.is_relative_to(ROOT / 'build'):
        raise ValueError('Stage this prototype under build/; do not modify production')
    manifest = json.loads(source_manifest.read_text())
    records = manifest['records']
    if len(records) != 122 or len({r['species'] for r in records}) != 122:
        raise ValueError('Expected the complete reviewed 122-species source set')
    table = target / 'gfx/footprints.asm'
    text = table.read_text()
    rows = []
    for record in records:
        source = source_manifest.parent / record['file']
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('Source PNG changed: ' + record['species'])
        before = f'INCBIN "gfx/footprints/bulbasaur.1bpp" ; {record["species"]} placeholder'
        after = f'INCBIN "gfx/footprints/{record["species"]}.1bpp"'
        if text.count(before) != 1:
            raise ValueError('Expected one placeholder: ' + record['species'])
        text = text.replace(before, after)
        with Image.open(source) as original:
            converted = convert(original)
        path = target / 'gfx/footprints' / (record['species'] + '.png')
        if path.exists():
            raise ValueError('Do not overwrite an existing asset: ' + str(path))
        converted.save(path, bits=1, optimize=True)
        rows.append(dict(species=record['species'], source=record['source'],
            original_sha256=record['sha256'], source_url=record['url'],
            converted_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            foreground_pixels=sum(converted.getpixel((x, y)) == 0
                                  for y in range(16) for x in range(16))))
    if len(re.findall(r'^INCBIN ', text, re.M)) != 373 or 'placeholder' in text:
        raise ValueError('Unexpected footprint table shape')
    # This is a mechanical table substitution driven by the verified manifest.
    table.write_text(text)
    result = dict(species=122, blank=sum(r['foreground_pixels'] == 0 for r in rows),
                  source_manifest_sha256=hashlib.sha256(source_manifest.read_bytes()).hexdigest(),
                  records=rows)
    (target.parent / 'footprint-import.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    args = parser.parse_args()
    result = import_assets(args.source_manifest, args.target)
    print(json.dumps({key: value for key, value in result.items() if key != 'records'}, indent=2))
