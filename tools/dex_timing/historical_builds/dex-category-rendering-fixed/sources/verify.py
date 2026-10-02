"""Read-only category investigation using the unchanged ROM and normal inputs."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from dex_timing.assets import Repository, offset, sha256
from dex_timing.cold_listing import Driver, build_core, move, predecessor
from dex_timing.description_ui import audit, settle

OUT = Path(__file__).resolve().parent
CHECKPOINTS = OUT / 'cold'
ROM = OUT / 'diagnostic-input.gbc'
BOOT = Path('/Applications/SameBoy/SameBoy.app/Contents/Resources/cgb_boot.bin')
repo = Repository(ROOT, ROM, ROOT / 'pokecrystal.sym')
origin = json.loads((CHECKPOINTS / 'provenance.json').read_text())
assert all(origin[k] == v for k, v in repo.hashes.items())
main_charmap = (ROOT / 'constants/charmap.asm').read_text().split('newcharmap')[0]
chars = {m[1]: int(m[2], 16) for m in re.finditer(r'charmap\s+"([^"]+)",\s*\$([0-9a-fA-F]+)', main_charmap)}
text = (ROOT / 'data/pokemon/dex_order_new.asm').read_text()
names = [m.lower() for m in re.findall(r'^\s*dw (\w+)\s*$', text, re.M)]


def category(name):
    source = ROOT / f'data/pokemon/dex_entries/{name}.asm'
    match = re.search(r'^\s*db\s+"([^"]+)@"\s*; species name', source.read_text(), re.M)
    if match is None:
        raise ValueError(f'Category not found in {source}')
    label = name.capitalize() + 'PokedexEntry'
    encoded = bytes(chars[c] for c in match[1])
    at = offset(repo.symbols[label])
    linked = repo.rom[at:at + len(encoded) + 1]
    assert linked == encoded + bytes((chars['@'],))
    return dict(text=match[1], width=len(encoded), label=label,
                bank=repo.symbols[label][0], address=repo.symbols[label][1],
                linked_hex=linked.hex()), encoded


sources = {name: category(name)[0] for name in ('mew', 'natu', 'bronzong', 'skorupi', 'drapion')}
assert sources['mew']['text'] == 'New Species'
assert sources['skorupi']['text'] == sources['drapion']['text'] == 'Scorpion'
widths = []
for source in sorted((ROOT / 'data/pokemon/dex_entries').glob('*.asm')):
    match = re.search(r'^\s*db\s+"([^"]*)@"\s*(?:;[^\n]*)?$', source.read_text(), re.M)
    if match is None:
        raise ValueError(f'Unrecognized category definition in {source}')
    widths.append(dict(species=source.stem, text=match[1], width=len(match[1])))
labels = re.findall(r'^\s*dba (\w+)\s*$',
                    (ROOT / 'data/pokemon/dex_entry_pointers.asm').read_text(), re.M)
mew_slot = labels.index('MewPokedexEntry')
pointer = offset(repo.symbols['PokedexDataPointerTable']) + 3 * mew_slot
linked_pointer = repo.rom[pointer:pointer + 3]
mew_bank, mew_address = repo.symbols['MewPokedexEntry']
assert linked_pointer == bytes((mew_bank, mew_address & 255, mew_address >> 8))
assert all(c['width'] <= 11 for c in widths)

# Verify every relocated entry pointer and terminator-relative numeric fields.
includes = dict(re.findall(r'^(\w+)::\s+INCLUDE "([^"]+)"',
                          (ROOT / 'data/pokemon/dex_entries.asm').read_text(), re.M))
table = offset(repo.symbols['PokedexDataPointerTable'])
for slot, label in enumerate(labels):
    source = (ROOT / includes[label]).read_text()
    value = re.search(r'^\s*db\s+"([^"]*)@"', source, re.M)[1]
    encoded = bytes(chars[c] for c in value) + bytes((chars['@'],))
    height, weight = map(int, re.search(r'^\s*dw\s+(\d+),\s*(\d+)', source, re.M).groups())
    bank, address = repo.symbols[label]
    pointer = repo.rom[table + 3 * slot:table + 3 * slot + 3]
    assert pointer == bytes((bank, address & 255, address >> 8)), label
    data = offset((bank, address))
    assert repo.rom[data:data + len(encoded)] == encoded, label
    numerics = repo.rom[data + len(encoded):data + len(encoded) + 4]
    assert numerics == height.to_bytes(2, 'little') + weight.to_bytes(2, 'little'), label

core = build_core(repo, Path.home() / 'Documents/GitHub/SameBoy', OUT)
driver = Driver(core, ROM, BOOT, CHECKPOINTS / 'input-copy.sav', OUT / 'core.log')
results = []


def snapshot(name, label, expected_page, image=False):
    info, encoded = category(name)
    ui = driver.command('ui')
    data, attrs = bytes.fromhex(ui['map']), bytes.fromhex(ui['attrs'])
    field = slice(4 * 21 + 9, 4 * 21 + 20)
    expected = encoded + bytes((0x32,)) * (11 - len(encoded))
    issues = []
    if data[field] != expected:
        issues.append('category_tiles_differ_from_linked_text')
    if any(attrs[field]):
        issues.append('category_attrs_changed')
    if ui['page'] != expected_page:
        issues.append('wrong_description_page')
    issues += audit(repo, ui)
    if image:
        driver.command(f'image {OUT / label}.ppm')
        (OUT / f'{label}.json').write_text(json.dumps(ui, indent=2) + '\n')
    return dict(text=info['text'], cells=data[field].hex(), attrs=attrs[field].hex(),
                page=ui['page'], issues=issues)


def wait_and_observe(name):
    sampled = 0
    issues = []
    for _ in range(2400):
        state = driver.run(('selected', 'animation_miss', 'audio_miss'), frames=120)
        if state['hit'] != 'selected':
            raise RuntimeError(f'Unexpected stop: {state}')
        check = snapshot(name, '', 0)
        sampled += 1
        issues += check['issues']
        if state['playback'] == 3 and not state['audio'] and not state['sfx']:
            return sampled, sorted(set(issues)), state
    raise RuntimeError('Animation failed to finish')


try:
    for name, paths in (('mew', ('cold_immediate', 'cold_hovered', 'warm_hovered',
                               'mewtwo_to_mew', 'celebi_to_mew')),
                        ('skorupi', ('cold_immediate', 'drapion_to_skorupi')),
                        ('drapion', ('cold_immediate', 'skorupi_to_drapion')),
                        ('natu', ('cold_immediate',)), ('bronzong', ('cold_immediate',))):
        index = names.index(name)
        for path in paths:
            for phase in (0, 1, 2):
                label = f'{name}-{path}-phase{phase}'
                driver.events.clear()
                driver.command('audit 1')
                if '_to_' in path:
                    before = names.index(path.split('_to_')[0])
                    driver.command(f'load {CHECKPOINTS / "listing-states" / f"listing-{before:03}.s0"}')
                    driver.run(('accept',), key='a')
                    settle(driver)
                    driver.run(frames=2 + phase)
                    accepted = driver.run(('change_species',), key='down' if index > before else 'up')
                    assert accepted['hit'] == 'change_species'
                elif path == 'cold_hovered':
                    driver.command(f'load {CHECKPOINTS / "listing-states" / f"listing-{index:03}.s0"}')
                    driver.run(frames=phase)
                    accepted = driver.run(('accept',), key='a')
                else:
                    prior, direction = predecessor(index)
                    driver.command(f'load {CHECKPOINTS / "listing-states" / f"listing-{prior:03}.s0"}')
                    move(driver, direction, index)
                    driver.run(frames=(300 if path == 'warm_hovered' else 0) + phase)
                    accepted = driver.run(('accept',), key='a')
                assert accepted['hit'] in ('accept', 'change_species')
                driver.command('rawcolor')
                observed, issues, final = wait_and_observe(name)
                assert final['selected_index'] == index
                pages = []
                for page in (0, 1, 0):
                    driver.run(frames=2)
                    pages.append(snapshot(name, f'{label}-page{page + 1}', page, image=True))
                    if page == 0 and len(pages) == 3:
                        break
                    driver.run(frames=2, key='a')
                    driver.run(frames=2)
                result = dict(species=name, path=path, phase=phase,
                              accepted_state=accepted,
                              animation_loop_observations=observed,
                              animation_issues=issues, pages=pages,
                              events=[e for e in driver.events if e['event'] in
                                      ('animation_miss', 'audio_miss')])
                results.append(result)
                print(json.dumps(dict(species=name, path=path, phase=phase,
                                      observations=observed, issues=issues,
                                      page_issues=[p['issues'] for p in pages])), flush=True)
finally:
    driver.close()

report = dict(production_rom_unchanged=True, hashes=repo.hashes,
              diagnostic_script_sha256=sha256(Path(__file__).read_bytes()),
              fields=dict(x=9, y=4, backing_width=20, available_characters=11),
              mew_pointer=dict(stable_species_index=mew_slot + 1, linked_hex=linked_pointer.hex()),
              verified_entry_pointers_and_numeric_fields=len(labels),
              linked_categories=sources, category_count=len(widths),
              overflow_categories=[c for c in widths if c['width'] > 11],
              results=results)
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
assert all(not r['animation_issues'] and not r['events'] and
           not any(p['issues'] for p in r['pages']) for r in results)
print(json.dumps(dict(complete=len(results), status='pass')), flush=True)
