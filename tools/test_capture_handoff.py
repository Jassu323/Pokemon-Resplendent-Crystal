"""Negative controls for the narrowly scoped visible capture speed switch."""
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest

from dex_timing.assets import offset
from dex_timing.assets import Repository
from dex_timing.cpu import CounterCPU
from dex_timing.gotcha_boundary import validate_speed_changes
from dex_timing.gotcha_boundary_review import comparison_value, delivery_checks

SOURCE = Path(__file__).resolve().parents[1]/'build/interactive-registration-fixed-full-20261016/candidate'


class CaptureHandoffTests(unittest.TestCase):
    def fixture(self, synchronized=True, second_capture=False):
        stop = (11, 0x7000)
        rom = bytearray(12 * 0x4000)
        rom[offset(stop):offset(stop)+2] = b'\x10\x00'
        symbols = {'BattleSpeed_CaptureHandoff.SwitchNow': stop,
                   'BattleSpeed_CaptureHandoff.Resumed': (11, 0x7002)} if synchronized else {}
        repo = SimpleNamespace(rom=rom, symbols=symbols)
        def change(t, speed, live=False):
            return dict(event='speed_change', initial=0, t=t, speed=speed,
                lcdc=0xe3 if live else 0x63, nr52=0, sampled_active=0,
                bank=11 if live else 0, pc=0x7002 if live else 0x2cb5)
        def phase(t):
            return dict(event='perf_phase',name='capture_stop',t=t,stat=0x8b,
                        lcdc=0xe3,speed=0,nr52=0,ie=0)
        events = [change(20,1,synchronized),change(40,0),change(60,1,second_capture)]
        if synchronized:
            events.insert(0,phase(10))
        if second_capture:
            events.insert(-1,phase(50))
        return repo,events

    def test_synchronized_capture_and_hidden_other_switches(self):
        repo,events=self.fixture()
        self.assertEqual(validate_speed_changes(repo,events)['live_capture_switches'],1)

    def test_following_capture_uses_the_same_narrow_exception(self):
        repo,events=self.fixture(second_capture=True)
        self.assertEqual(validate_speed_changes(repo,events)['mode3_stops'],2)

    def test_old_hidden_policy_still_passes(self):
        repo,events=self.fixture(synchronized=False)
        self.assertEqual(validate_speed_changes(repo,events)['live_capture_switches'],0)

    def test_other_display_phases_are_rejected(self):
        repo,events=self.fixture()
        for mode in (0,1,2):
            with self.subTest(mode=mode):
                bad=copy.deepcopy(events);bad[0]['stat']=0x88|mode
                with self.assertRaises(AssertionError):validate_speed_changes(repo,bad)

    def test_missing_hardware_evidence_is_rejected(self):
        repo,events=self.fixture()
        with self.assertRaises(AssertionError):validate_speed_changes(repo,events[1:])

    def test_wrong_live_return_pc_is_rejected(self):
        repo,events=self.fixture();events[1]['pc']+=1
        with self.assertRaises(AssertionError):validate_speed_changes(repo,events)

    def test_reverse_switch_cannot_use_the_exception(self):
        repo,events=self.fixture();events[2]['lcdc']=0xe3
        with self.assertRaises(AssertionError):validate_speed_changes(repo,events)

    def test_sound_samples_interrupts_and_speed_must_be_inactive(self):
        for index,field,value in ((0,'nr52',0x80),(0,'ie',1),(0,'speed',1),
                                  (1,'nr52',0x80),(1,'sampled_active',1)):
            with self.subTest(index=index,field=field):
                repo,events=self.fixture();events[index][field]=value
                with self.assertRaises(AssertionError):validate_speed_changes(repo,events)

    def test_old_policy_does_not_allow_a_live_switch(self):
        repo,events=self.fixture(synchronized=False);events[0]['lcdc']=0xe3
        with self.assertRaises(AssertionError):validate_speed_changes(repo,events)

    def test_changed_stop_opcode_or_layout_is_rejected(self):
        for layout in (False,True):
            repo,events=self.fixture()
            if layout:repo.symbols['BattleSpeed_CaptureHandoff.Resumed']=(11,0x7003)
            else:repo.rom[offset((11,0x7000))]=0
            with self.assertRaises(AssertionError):validate_speed_changes(repo,events)

    def test_native_delivery_proof_rejects_changed_dvs_or_stats(self):
        original=dict(dvs='b350',stats='00100010000b000d00080008000d')
        self.assertTrue(all(delivery_checks(original,original,False).values()))
        self.assertTrue(all(delivery_checks(original,original,True).values()))
        for field in ('dvs','stats'):
            changed=dict(original);changed[field]='00'
            self.assertFalse(all(delivery_checks(original,changed,False).values()))
        changed=dict(original,dvs='b250')
        self.assertFalse(all(delivery_checks(original,changed,True).values()))

    def test_pair_comparison_keeps_existing_party_and_other_fields_strict(self):
        original=[dict(dvs='ffff',stats='a',moves=[1]),dict(dvs='b350',stats='b',moves=[2])]
        changed=copy.deepcopy(original);changed[-1].update(dvs='b250',stats='c')
        normalize=lambda value,stage='after':comparison_value(value,stage,'mons','party')
        self.assertEqual(normalize(original),normalize(changed))
        self.assertNotEqual(normalize(original,'after_exp'),normalize(changed,'after_exp'))
        for index,field,value in ((0,'dvs','0000'),(0,'stats','bad'),(1,'moves',[3])):
            changed=copy.deepcopy(original);changed[index][field]=value
            self.assertNotEqual(normalize(original),normalize(changed))
        self.assertEqual(original[-1]['dvs'],'b350')

    def test_linked_tutorial_and_already_double_guards_preserve_registers(self):
        root=SOURCE
        repo=Repository(root,root/'pokecrystal.gbc',root/'pokecrystal.sym')
        for battle_type,speed in ((3,0),(3,128),(0,128)):
            for pattern in ((0x1234,0xabcd,0x9876),(0,0xffff,0x5555)):
                with self.subTest(battle_type=battle_type,speed=speed,pattern=pattern):
                    cpu=CounterCPU(repo.rom,repo.symbols)
                    cpu.field('wBattleType',battle_type)
                    cpu.allowed_io.add(0xff4d);cpu.ram[0xff4d]=speed
                    for n,value in enumerate(pattern):cpu.set_pair(n,value)
                    cpu.run('BattleSpeed_CaptureHandoff')
                    self.assertEqual([cpu.pair(n) for n in range(3)],list(pattern))
                    self.assertEqual(cpu.sp,0xc0f0)
                    self.assertEqual(cpu.ram[0xff4d],speed)
                    self.assertEqual(cpu.read(repo.symbols['hCGBPalUpdate'][1]),0)


if __name__=='__main__':unittest.main()
