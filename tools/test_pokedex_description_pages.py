"""Independent metadata/seek contracts for the multipage Description prototype."""
import json
import hashlib
import re
from pathlib import Path
import unittest

from dex_timing.assets import Repository, offset
from dex_timing.cold_listing import ROOT
from dex_timing.cpu import CounterCPU


class RegistrationCoverageContracts(unittest.TestCase):
    def test_multiscreen_coverage_counts_every_description_page(self):
        from dex_timing.interactive_registration_regression import coverage_plan
        rows=[dict(base='three', species='three', description_pages=3, info_pages=2, moves_pages=1),
              dict(base='four', species='four', description_pages=4, info_pages=1, moves_pages=2)]
        plan=coverage_plan(rows)
        self.assertEqual(plan['description_pages'],7)
        self.assertEqual(plan['committed_B_End_exits'],26)

    def test_legacy_catalog_still_defaults_to_two_pages(self):
        from dex_timing.interactive_registration_regression import coverage_plan
        row=dict(base='legacy', species='legacy', info_pages=2, moves_pages=1)
        plan=coverage_plan([row])
        self.assertEqual(plan['description_pages'],2)
        self.assertEqual(plan['committed_B_End_exits'],10)


class MultipageContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
        if 'PokedexDescriptionPageOffsets' not in cls.repo.symbols:
            raise unittest.SkipTest('multipage prototype required')
        from dex_timing.regression_fixtures import require
        assessment = require('build/dex-species-information-scope-20261016/assessment.json')
        rows=json.loads(assessment.read_text())['records']
        cls.counts=[2]*251+[r['pages'] for r in rows]
        cls.rows=rows

    def entry(self,index):
        r=self.repo
        at=offset(r.symbols['PokedexDataPointerTable'])+index*3
        bank=r.rom[at]
        address=int.from_bytes(r.rom[at+1:at+3],'little')
        start=offset((bank,address))
        text=r.rom.index(0x50,start)+5
        pages=[]
        pos=text
        for _ in range(self.counts[index]):
            end=r.rom.index(0x50,pos)
            pages.append((pos-text,r.rom[pos:end]))
            pos=end+1
        return bank,0x4000+text%0x4000,pages

    def cpu(self,index):
        cpu=CounterCPU(self.repo.rom,self.repo.symbols)
        cpu.ram[0xff70]=6
        cpu.ram[0xff4f]=1
        cpu.field('wPokemonIndexTableEntries',index+1,2)
        cpu.field('wTempSpecies',1)
        return cpu

    def test_offsets_and_page_counts_match_sequential_record_boundaries(self):
        start=offset(self.repo.symbols['PokedexDescriptionPageOffsets'])
        for index in range(251,373):
            _,_,pages=self.entry(index)
            expected=bytes([p[0] for p in pages[1:]]+[0]*(4-len(pages)))
            self.assertEqual(self.repo.rom[start+(index-251)*3:start+(index-250)*3],expected)
            self.assertEqual([len(p[1].split(b'\x4e')) for p in pages],self.rows[index-251]['page_line_counts'])
            for _,page in pages:
                self.assertTrue(all(len(line)<=18 for line in page.split(b'\x4e')))

    def test_all_species_counts_and_reused_transient_id(self):
        cpu=self.cpu(0)
        for index in range(373):
            cpu.field('wPokemonIndexTableEntries',index+1,2)
            cpu.r[7]=1
            cpu.run('PokedexDescription_GetPageCount')
            self.assertEqual(cpu.r[7],self.counts[index],index)
            self.assertEqual(cpu.ram[0xff70],6)
            self.assertEqual(cpu.ram[0xff4f],1)

    def test_every_static_seek_preserves_bank_and_stack(self):
        for index in range(373):
            bank,first,pages=self.entry(index)
            for page,(relative,_) in enumerate(pages):
                cpu=self.cpu(index)
                cpu.r[0],cpu.r[1]=bank,page
                cpu.set_pair(1,first)
                sp=cpu.sp
                cpu.run('PokedexDescription_SeekStaticPage')
                self.assertEqual(cpu.pair(1),first+relative,(index,page))
                self.assertEqual(cpu.r[0],bank)
                self.assertEqual(cpu.ram[0xff70],6)
                self.assertEqual(cpu.sp,sp)
                self.assertEqual(cpu.bank,self.repo.symbols['PokedexDescription_SeekStaticPage'][0])

    def test_out_of_range_custom_offsets_do_not_read_neighbor_records(self):
        for index in (251,254,255,372):
            for page in (4,19,255):
                cpu=self.cpu(index)
                cpu.r[7],cpu.r[1]=1,page
                cpu.run('PokedexDescription_GetPageOffset')
                self.assertEqual(cpu.r[7],0)
                self.assertTrue(cpu.f & cpu.C)

    def test_measurement_words_and_rounding_exception(self):
        for index,row in enumerate(self.rows,251):
            table=offset(self.repo.symbols['PokedexDataPointerTable'])+index*3
            address=offset((self.repo.rom[table],int.from_bytes(self.repo.rom[table+1:table+3],'little')))
            at=self.repo.rom.index(0x50,address)+1
            expected_weight=row['current_weight_word'] if row['constant']=='TORKOAL' else row['crystal_weight_word']
            self.assertEqual(int.from_bytes(self.repo.rom[at:at+2],'little'),row['crystal_height_word'])
            self.assertEqual(int.from_bytes(self.repo.rom[at+2:at+4],'little'),expected_weight)

    def test_full_text_matches_pinned_normalized_source_hashes(self):
        text=(ROOT/'constants/charmap.asm').read_text().split('; Japanese control')[0]
        reverse={int(code,16):glyph for glyph,code in re.findall(r'charmap\s+"([^"]+)"\s*,\s*\$([0-9a-fA-F]+)',text)}
        for index,row in enumerate(self.rows,251):
            _,_,pages=self.entry(index)
            encoded=b'\x7f'.join(line for _,page in pages for line in page.split(b'\x4e'))
            decoded=''.join(reverse[c] for c in encoded)
            self.assertEqual(hashlib.sha256(decoded.encode()).hexdigest(),row['text_sha256'],row['species'])


if __name__=='__main__': unittest.main()
