"""Check unused palette bytes and valid returned-map phases in native inventories."""
import json
from pathlib import Path
from PIL import Image, ImageChops

from .battle_normal_speed import BASE
from . import global_speed as speed, performance_audio as audio, shared_menu_regression as menu
from .assets import Repository
from .cold_listing import Driver, KEY


def main():
    rows = []
    for variant in ('final', 'battle-normal'):
        local = speed.configuration(variant)
        repo = Repository(Path(local['root']), Path(local['rom']), Path(local['sym']))
        source = speed.BASE / 'menus' / variant / 'standard'
        folder = speed.BASE / 'custom-menus' / variant
        driver = Driver(folder / 'cold-listing-core', local['rom'], menu.BOOT,
                        source / 'private.sav', folder / 'palette-audit.log')
        try:
            for label, state, button in [('apricorn', folder / 'apricorn-0.s0', 'right'),
                                         ('tmhm', folder / 'tmhm-0.s0', 'right'),
                                         ('pack', source / 'pack-pocket-0.s0', 'right'),
                                         *[(f'pack-return-{p}', source / f'pack-pocket-{p}.s0', 'b') for p in range(5)]]:
                driver.command(f'load {state}')
                menu.run(driver, repo, frames=4)
                menu.run(driver, repo, frames=4, keys=KEY[button])
                menu.run(driver, repo, frames=92)
                fields = driver.command('ui')
                path = folder / (label + '-palette-audit.ppm')
                driver.command(f'image {path}')
                rows.append(dict(variant=variant, label=label, image=str(path), fields=fields,
                                 time_of_day=audio.value(driver, repo, 'wTimeOfDay')))
        finally:
            driver.close()
    old = {r['label']: r for r in rows if r['variant'] == 'final'}
    comparisons = []
    for new in (r for r in rows if r['variant'] == 'battle-normal'):
        prior = old[new['label']]
        a = bytes.fromhex(prior['fields']['obj_palettes'])
        b = bytes.fromhex(new['fields']['obj_palettes'])
        oam = bytes.fromhex(new['fields']['oam'])
        used = {oam[i+3] & 7 for i in range(0, 160, 4)
                if 0 < oam[i] < 160 and 0 < oam[i+1] < 168}
        colors = [(i//8, (i%8)//2) for i in range(0, 64, 2) if a[i:i+2] != b[i:i+2]]
        diff = ImageChops.difference(Image.open(prior['image']), Image.open(new['image']))
        comparisons.append(dict(label=new['label'], differing_obj_colors=colors,
            time_of_day=[prior['time_of_day'], new['time_of_day']],
            visible_obj_palettes=sorted(used), visible_nontransparent_palette_differences=
                [(p,c) for p,c in colors if p in used and c != 0], pixel_difference_box=diff.getbbox()))
    (BASE / 'inventory-palette-audit.json').write_text(json.dumps(dict(rows=rows,comparisons=comparisons),indent=2)+'\n')
    print(json.dumps(comparisons))


if __name__ == '__main__':
    main()
