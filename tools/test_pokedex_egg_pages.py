"""Disposable long-list fixtures for Dex breeding-page contracts."""
from contextlib import contextmanager
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from dex_timing.cold_listing import ROOT
from pokedex_info_assets import constants, evolution_graph
from pokedex_moves_assets import compile as compile_moves


@contextmanager
def egg_fixture():
    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='egg-page-control-', dir=build) as name:
        root = Path(name)
        for folder in ('constants', 'data/pokemon', 'data/moves', 'gfx/font'):
            shutil.copytree(ROOT / folder, root / folder)
        yield root


def replace_treecko_eggs(root, moves):
    graph = evolution_graph(root)
    family, pending = set(), ['TREECKO']
    while pending:
        name = pending.pop()
        if name not in family:
            family.add(name)
            pending.extend(child for child, _ in graph[name])
    path = root / 'data/pokemon/egg_moves_custom.asm'
    text = path.read_text()
    header, body = text.split('.IndirectEnd::', 1)
    for name in family:
        header, count = re.subn(r'^(\s*dw )\w+( ; ' + name + r')$',
            r'\g<1>NoEggMoves3\2', header, flags=re.M)
        if count != 1:
            raise AssertionError('Missing fixture family pointer: ' + name)
    header = header.replace('\tdw NoEggMoves3 ; TREECKO\n',
        '\tdw QualificationTreeckoEggMoves ; TREECKO\n', 1)
    path.write_text(header + '.IndirectEnd::' + body +
        '\nQualificationTreeckoEggMoves:\n' +
        ''.join('\tdw ' + move + '\n' for move in moves) + '\tdw -1\n')
    return family


def valid_moves(root):
    ids = constants(root / 'constants/move_constants.asm')
    return [name for name, value in sorted(ids.items(), key=lambda row: row[1])
        if value > 0 and not name.startswith('ANIM_')]


class EggPageContracts(unittest.TestCase):
    def test_two_and_three_page_lists_share_complete_rows_across_the_family(self):
        for length in (6, 10, 11, 15):
            with self.subTest(moves=length), egg_fixture() as root:
                before = compile_moves(root, validate_only=True)
                all_moves = valid_moves(root)
                selected = [all_moves[i - 1] for i in (1, 255, 256, 333)]
                selected += [name for name in all_moves if name not in selected][:length - 4]
                family = replace_treecko_eggs(root, selected)
                after = compile_moves(root, validate_only=True)
                self.assertEqual(family, {'TREECKO', 'GROVYLE', 'SCEPTILE'})
                for member in family:
                    data = after[member]
                    pages = [rows for kind, rows in data['pages'] if kind == 3]
                    self.assertEqual(len(pages), (length + 4) // 5)
                    self.assertEqual([move for page in pages for _, move in page], selected)
                    self.assertEqual([len(page) for page in pages],
                        [min(5, length - first) for first in range(0, length, 5)])
                    self.assertEqual(data['egg_source'], 'TREECKO')
                    self.assertEqual(data['egg_pointer'], 'QualificationTreeckoEggMoves')
                    self.assertEqual(data['streams'][:3], before[member]['streams'][:3])
                for name in after.keys() - family:
                    self.assertEqual(after[name], before[name], name)

    def test_total_mov_page_limit_accepts_nineteen_and_rejects_twenty(self):
        for limit, accepted in ((19, True), (20, False)):
            with self.subTest(total_pages=limit), egg_fixture() as root:
                before = compile_moves(root, validate_only=True)
                family = ('TREECKO', 'GROVYLE', 'SCEPTILE')
                other = max(sum(kind != 3 for kind, _ in before[n]['pages']) for n in family)
                count = (limit - other) * 5
                self.assertGreater(count, 0)
                replace_treecko_eggs(root, valid_moves(root)[:count])
                if accepted:
                    data = compile_moves(root, validate_only=True)
                    self.assertEqual(max(len(data[n]['pages']) for n in family), 19)
                else:
                    with self.assertRaisesRegex(ValueError, 'Moves pages; limit is 19'):
                        compile_moves(root, validate_only=True)

    def test_unknown_move_is_rejected_before_linking(self):
        with egg_fixture() as root:
            replace_treecko_eggs(root, ['NOT_A_REAL_MOVE'])
            with self.assertRaisesRegex(ValueError, 'Invalid Moves data: TREECKO'):
                compile_moves(root, validate_only=True)

    def test_conflicting_descendant_list_is_not_silently_merged(self):
        with egg_fixture() as root:
            replace_treecko_eggs(root, valid_moves(root)[:11])
            path = root / 'data/pokemon/egg_moves_custom.asm'
            text = path.read_text().replace('\tdw NoEggMoves3 ; GROVYLE\n',
                '\tdw QualificationGrovyleEggMoves ; GROVYLE\n', 1)
            path.write_text(text + '\nQualificationGrovyleEggMoves:\n\tdw REST\n\tdw -1\n')
            with self.assertRaisesRegex(ValueError, 'Conflicting egg-move lists in evolution family'):
                compile_moves(root, validate_only=True)


if __name__ == '__main__':
    unittest.main()
