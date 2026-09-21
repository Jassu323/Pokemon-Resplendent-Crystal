"""Execute the shipped scheduler, not a counterfactual policy override.

Captured asset/audio/viewport memory is retained; the first-publication call
stack is rebuilt by executing the new link. This is a relocated steady-owner
test input, NOT a new SameBoy capture or a startup-latency measurement.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import struct
import subprocess

from .assets import Repository, offset, sha256
from .budget_experiment import audit_hardware
from .costs import machine, run_to
from .cpu import ModelError
from .model import FRAME
from .recovery_experiment import initial_replay, initial_asset_maps, VIEWPORT, REQUESTS
from .replay import OwnerReplay, ReplayCPU
from .scheduler_experiment import candidate_summary
from .probes.compare_save_state import compare_instructions

ROOT = Path(__file__).resolve().parents[2]
SPECIES = ('weavile', 'luxray', 'dusknoir', 'garchomp', 'bastiodon',
           'rampardos', 'rayquaza', 'kyogre', 'metagross', 'exeggcute')


class IntegratedReplay(OwnerReplay):
    def set_timer_phase(self, delay_t):
        """Perturb future reload timing only; retain any already latched IRQ."""
        if (not self.timer_tac & 4 or self.clock.timer_period not in (12800, 262144)
                or not 64 <= delay_t <= self.clock.timer_period or delay_t % 4):
            raise ModelError('Unsupported initial timer phase perturbation')
        self.div_origin += self.clock.next_timer-self.clock.t-delay_t
        self.clock.next_timer = self.clock.t+delay_t
        self.points = [self.snapshot('Publication')]

    def configure_linked(self, repo):
        old, prior = self.repo, self.cpu
        asset = repo.load([self.asset.name])[0]
        if (asset.plans, asset.events, asset.dictionary) != (
                self.asset.plans, self.asset.events, self.asset.dictionary):
            raise ModelError('Relocated fixture must preserve animation assets')
        # Only production aliases change in the Dex union. All other recorded
        # RAM addresses and sound/data banks used by this continuation must agree.
        for name, symbol in old.symbols.items():
            if symbol[1] >= 0xc000 and name in repo.symbols and symbol != repo.symbols[name]:
                raise ModelError(f'RAM moved: {name}; explicit migration required')
        for kind in ('front', 'plan', 'timeline', 'sample'):
            if kind in asset.labels and old.symbols[self.asset.labels[kind]] != repo.symbols[asset.labels[kind]]:
                raise ModelError(f'{kind} ROM data moved; explicit pointer migration required')
        fresh = machine(repo, asset, ReplayCPU)
        fresh.allowed_io.update(prior.allowed_io | {0xff4d})
        fresh.ram[:] = prior.ram
        fresh.wram = [bytearray(x) for x in prior.wram]
        fresh.vram = [bytearray(x) for x in prior.vram]
        # Build the new outer farcall/wait and VBlank return chain, not guessed
        # address substitutions in an old stack. No animation work in this setup.
        fresh.field('wPokedexAnimFlags', 0)
        fresh.field('wPokedexAnimPlaybackState', 0)
        fresh.field('hVBlank', 0x80)
        fresh.field('wPokedexAnimSchedulerControl', 0)
        top = fresh.sp
        run_to(fresh, 'Pokedex.main', 'Pokedex_EndOwnerLoop.wait')
        fresh.pc += 1
        returning = fresh.pc
        stack = bytes(fresh.ram[fresh.sp:top])
        fresh.ram[:] = prior.ram
        fresh.ram[fresh.sp:top] = stack
        fresh.field('hROMBank', fresh.bank)
        fresh.field('hVBlank', 0x87)
        fresh.field('hOAMUpdate', 1)
        tick = prior.ram[old.symbols['hVBlankCounter'][1]]
        fresh.field('wPokedexAnimLoopTick', tick)
        fresh.field('wPokedexAnimWorkTick', (tick - 1) & 255)
        fresh.field('wPokedexAnimSchedulerControl', 0)
        fresh.ram[0xff44] = 145
        fresh.ram[0xff4d] = 0
        saved_return = fresh.sp - 2
        run_to(fresh, 'VBlank', 'Pokedex_VBlankAnimationFrontpicMap.deadline_reached')
        if fresh.data(saved_return, 2) != b'\xff\xff':
            raise ModelError('Unexpected rebuilt VBlank stack')
        fresh.block(saved_return, returning.to_bytes(2, 'little'))
        fresh.r, fresh.f = list(prior.r), prior.f
        # The initial OAM helper contains no relocated ROM pointer.
        begin, end = (offset(repo.symbols[n]) for n in ('OAMDMACode', 'OAMDMACode.End'))
        fresh.block(repo.symbols['hTransferShadowOAM'][1], repo.rom[begin:end])
        self.repo, self.asset, self.cpu = repo, asset, fresh
        fresh.replay = self
        self.start_steps = fresh.steps
        self.operation_hooks = {repo.symbols[name]: name for name in self.operation_hooks.values()
                                if name in repo.symbols}
        for name in ('Pokedex_ChooseAnimationWork', 'Pokedex_TryFinishAnimationStage',
                     'Pokedex_CheckAnimationAudioRunway', 'Pokedex_EndOwnerLoop'):
            self.operation_hooks[repo.symbols[name]] = name
        self.points = [self.snapshot('Publication')]
        self.reset_audio_audit()
        self.gdma_spans, self.hardware_writes, self.publication_checks = [], [], []
        self.map_checks, self.finishes = [], []
        self.open_finish = None
        self.stack_low = fresh.sp
        self.initial_rebuilt_sp = fresh.sp
        original_write = fresh.write
        def audit_write(address, value):
            if address in (0xff42, 0xff43, 0xff4a, 0xff4b, 0xff46):
                self.hardware_writes.append(dict(t=self.clock.t, address=address,
                                                value=value, interrupt=self.in_interrupt or self.masked))
            original_write(address, value)
        fresh.write = audit_write

    def field(self, name):
        bank, address = self.repo.symbols[name]
        return self.cpu.wram[bank][address-0xd000] if 0xd000 <= address < 0xe000 else self.cpu.ram[address]

    def observe(self):
        super().observe()
        if not hasattr(self, 'map_checks'):
            return
        cpu = self.cpu
        key = (cpu.bank if cpu.pc >= 0x4000 else 0, cpu.pc)
        if key == self.repo.symbols['VBlank_Normal']:
            if any(self.field(n) for n in REQUESTS):
                raise ModelError('Competing request in quiet playback')
            if not self.field('hOAMUpdate') or not self.field('hVBlank') & 0x80:
                raise ModelError('Quiet display ownership lost')
            for name, address in VIEWPORT:
                if self.field(name) != cpu.ram[address]:
                    raise ModelError('Viewport changed while tagged quiet')
        if key == self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.deadline_reached']:
            frame, slot = self.field('wPokedexAnimStageFrameID'), self.field('wPokedexAnimStageSlot')
            base = 0x800 if slot == 0 else 0x1330
            mismatch = [i for i, source in enumerate(self.asset.plans[frame].sources)
                        if bytes(cpu.vram[1][base+i*16:base+(i+1)*16]) !=
                        self.asset.dictionary[source*16:(source+1)*16]] if frame else []
            self.publication_checks.append(dict(t=self.clock.t, mismatched_slot_tiles=mismatch))
        if key == self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.display_recorded']:
            expected = b''.join(initial_asset_maps(self.asset, self.field('wPokedexAnimStageFrameID'),
                                                   self.field('wPokedexAnimStageSlot')))
            actual = bytes(cpu.vram[b][0x1821+y*32+x] for b in (0,1) for y in range(7) for x in range(7))
            self.map_checks.append(dict(t=self.clock.t, mismatched_cells=[
                i for i, (a,b) in enumerate(zip(actual, expected)) if a != b]))
        if key == self.repo.symbols['Pokedex_ServiceAnimationUploadChunk'] and self.open_finish:
            self.open_finish['upload_t'] = self.clock.t
        if key == self.repo.symbols['Pokedex_TryFinishAnimationStage']:
            self.open_finish = dict(entry_t=self.clock.t, return_pc=cpu.read(cpu.sp) |
                                   cpu.read(cpu.sp+1)<<8, return_sp=cpu.sp+2)
        if self.open_finish and (cpu.pc, cpu.sp) == (self.open_finish['return_pc'], self.open_finish['return_sp']):
            if 'upload_t' in self.open_finish:
                self.finishes.append(dict(self.open_finish, end_t=self.clock.t,
                    margin_t=FRAME-(self.clock.t % FRAME)))
            self.open_finish = None

    def step(self, kind='mainline'):
        if hasattr(self, 'gdma_spans') and self.gdma_due:
            source, dest, size = self.gdma_transfer
            self.gdma_spans.append(dict(start_t=self.clock.t, end_t=self.clock.t+self.gdma_due,
                source=source, destination=dest, size=size))
        super().step(kind)
        if hasattr(self, 'stack_low'):
            self.stack_low = min(self.stack_low, self.cpu.sp)

    def export(self):
        cpu = self.cpu
        h = [self.clock.t, cpu.r[7]*256+cpu.f, *(cpu.pair(i) for i in range(3)),
             cpu.sp, cpu.pc, cpu.bank, cpu.ram[0xff70], cpu.ram[0xff4f],
             int(self.div_origin+self.clock.t) & 65535, self.read_tima(),
             self.timer_tma, self.timer_tac, sum(bit for bit,n in
                ((1,'vblank'),(2,'lcd'),(4,'timer')) if n in self.clock.pending), self.clock.enabled]
        return b'DEXCORE1'+struct.pack('<16I', *h)+cpu.ram+b''.join(cpu.wram)+b''.join(cpu.vram)


def make_replay(reference, repo, species):
    replay, identity = initial_replay(reference, species, IntegratedReplay, True)
    replay.configure_linked(repo)
    return replay, identity


def run_case(job):
    reference_path, root, name, output, core, phase = job
    reference = Repository(reference_path, reference_path/'pokecrystal.gbc', reference_path/'pokecrystal.sym')
    repo = Repository(root, root/'pokecrystal.gbc', root/'pokecrystal.sym')
    replay, identity = make_replay(reference, repo, name)
    if phase is not None:
        replay.set_timer_phase(phase)
    case_name = name if phase is None else f'{name}-phase-{phase}'
    payload = replay.export()
    (output/f'{case_name}.memory.bin').write_bytes(payload)
    comparison = None
    if core:
        trace = output/f'{case_name}.trace.txt'
        reference_run = subprocess.run([str(core), '--full', str(root/'pokecrystal.gbc'),
            str(output/f'{case_name}.memory.bin'), str(trace)], check=True, text=True, capture_output=True)
        (output/f'{case_name}.core.txt').write_text(reference_run.stdout)
        run, comparison = compare_instructions(replay, trace.read_text(), full=True)
    else:
        run = replay.run(full=True)
    summary = candidate_summary(run, replay.asset)
    audit = audit_hardware(replay)
    result = dict(species=name, timer_phase=phase, intervals=summary['full_sequence_intervals'],
        misses=len(summary['misses']), late=sum(p['late_intervals'] != 0 for p in summary['publications']),
        duplicates=len(summary['duplicate_publications']),
        wrong_tiles=sum(bool(p['mismatched_slot_tiles']) for p in replay.publication_checks),
        wrong_maps=sum(bool(p['mismatched_cells']) for p in replay.map_checks),
        audio_underruns=sum(p['reason']=='underrun' for p in summary['audio_stops']),
        finishes=len(replay.finishes), minimum_finish_margin=min((p['margin_t'] for p in replay.finishes), default=None),
        stack_low=replay.stack_low,
        **{k:audit[k] for k in ('gdma_outside_vblank', 'writes_outside_vblank', 'latest_gdma_end_phase')})
    if comparison:
        result.update(core_identical=comparison['identical'], instruction_starts=comparison['host_instructions'])
    (output/f'{case_name}.json').write_text(json.dumps(dict(scope='LINKED_CODE_RELOCATED_STEADY_OWNER_INPUT',
        **repo.hashes, reference=reference.hashes, input=identity, relocated_sha256=sha256(payload),
        result=result, summary=summary, hardware=audit, finishes=replay.finishes, host=run,
        instruction_comparison=comparison), indent=2)+'\n')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--output', type=Path, default=ROOT/'build/dex-scheduler-integrated/replays')
    p.add_argument('--species', nargs='+', choices=SPECIES, default=SPECIES)
    p.add_argument('--jobs', type=int, default=8)
    p.add_argument('--timer-phases', type=int, nargs='+',
                   help='Additional sampled-timer phases in T-cycles; omit for captured phase')
    p.add_argument('--sameboy-source', type=Path, help='Compile an independent core for this exact link')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    core = None
    if a.sameboy_source:
        repo = Repository(a.root, a.root/'pokecrystal.gbc', a.root/'pokecrystal.sym')
        core = (a.output/'sameboy-linked-replay').resolve()
        header = a.output/'linked-symbols.h'
        symbols = dict(DEX_PUBLICATION_PC='Pokedex_VBlankAnimationFrontpicMap.deadline_reached',
            DEX_STAGE_PC='Pokedex_PrepareNextAnimationStage', DEX_PRODUCER_PC='Pokedex_ServiceAnimationProducer',
            DEX_WAIT_PC='Pokedex_EndOwnerLoop.wait', DEX_MISS_PC='Pokedex_CountAnimationUnderflow',
            DEX_STOP_PC='StopSampledCryAsync_NoInterruptControl')
        header.write_text(''.join(f'#define {k} 0x{repo.symbols[v][1]:04x}\n' for k,v in symbols.items())+
                          '#define DEX_WAIT_BANK 0xa0\n')
        files = ('apu camera display gb joypad mbc memory printer random rumble save_state sgb '
                 'sm83_cpu timing workboy').split()
        subprocess.run(['clang', '-O2', '-std=c11', '-I'+str(a.sameboy_source),
            '-DGB_INTERNAL', '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_REWIND', '-DGB_DISABLE_CHEATS',
            '-DGB_DISABLE_CHEAT_SEARCH', '-DGB_DISABLE_TIMEKEEPING', '-DGB_VERSION="dex-linked-replay"',
            '-include', str(header), str(ROOT/'tools/dex_timing/probes/core_replay.c'),
            *(str(a.sameboy_source/'Core'/f'{f}.c') for f in files), '-o', str(core)], check=True)
    with ProcessPoolExecutor(a.jobs) as pool:
        rows = list(pool.map(run_case, [(a.reference, a.root, n, a.output, core, phase)
            for n in a.species for phase in (a.timer_phases or [None])]))
    (a.output/'summary.json').write_text(json.dumps(rows, indent=2)+'\n')
    for row in rows:
        print(json.dumps(row), flush=True)
    return int(any(not row.get('core_identical', True) or any(row[k] for k in
        ('misses', 'late', 'duplicates', 'wrong_tiles', 'wrong_maps', 'audio_underruns',
         'gdma_outside_vblank', 'writes_outside_vblank')) for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
