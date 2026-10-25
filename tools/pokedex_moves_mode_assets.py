"""Generate permanent-index orders for the visual Moves Dex prototype."""
import json
from pathlib import Path
import re

from pokedex_info_assets import constants

ROOT = Path(__file__).resolve().parents[1]
TYPES = ('BUG', 'DARK', 'DRAGON', 'ELECTRIC', 'FAIRY', 'FIGHTING', 'FIRE',
         'FLYING', 'GHOST', 'GRASS', 'GROUND', 'ICE', 'NORMAL', 'POISON',
         'PSYCHIC', 'ROCK', 'STEEL', 'WATER')


def compile_tables(root=ROOT):
    ids = constants(root / 'constants/move_constants.asm')
    names = re.findall(r'^\s*li "([^"]+)"', (root / 'data/moves/names.asm').read_text(), re.M)
    records = re.findall(r'^\s*move\s+(\w+),\s*(\d+),\s*(\w+),\s*(\d+),\s*(\d+),\s*(\d+)\b',
                         (root / 'data/moves/moves.asm').read_text(), re.M)
    if len(names) != len(records) or not names:
        raise ValueError('Move names and records differ')
    moves = []
    symbols = {value: symbol for symbol, value in ids.items()
               if value > 0 and not symbol.startswith('ANIM_')}
    if sorted(symbols) != list(range(1, len(names) + 1)):
        raise ValueError('Permanent move constants and names differ')
    for index, (name, record) in enumerate(zip(names, records), 1):
        effect, power, type_, accuracy, pp, chance = record
        type_ = 'PSYCHIC' if type_ == 'PSYCHIC_TYPE' else type_
        symbol = symbols.get(index)
        if symbol is None or type_ not in TYPES or len(name) > 12:
            raise ValueError(f'Invalid move record {index}: {symbol}')
        moves.append(dict(index=index, symbol=symbol, name=name, type=type_,
                          effect=effect, power=int(power), accuracy=int(accuracy),
                          pp=int(pp), chance=int(chance)))
    key = lambda m: (re.sub(r"[^a-z0-9]", '', m['name'].lower()), m['index'])
    orders = [sorted(moves, key=lambda m: (TYPES.index(m['type']), *key(m))),
              sorted(moves, key=key)]
    asm = ['; Generated from permanent move identities; no runtime sorting.']
    for label, order in zip(('PokedexMovesModeTypeOrder', 'PokedexMovesModeNameOrder'), orders):
        asm += [label + ':', *[f"\tdw {m['symbol']}" for m in order], '\tdw 0',
                f'ASSERT (@ - {label}) / 2 == NUM_ATTACKS + 1']
    manifest = dict(moves=moves, types=TYPES, orders=[[m['index'] for m in o] for o in orders],
                    sort_bytes=4 * (len(moves) + 1),
                    unknown=[m['index'] for m in orders[0][1::5]])
    return '\n'.join(asm) + '\n', manifest


if __name__ == '__main__':
    tables, manifest = compile_tables()
    output = ROOT / 'build/dex-moves-mode-assets'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'tables.asm').write_text(tables)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
