"""Diagnostic replay of an actual current-link first-publication save state.

The baseline uses no relocation, later-state injection, or policy override.
The independent core and host resume the original captured mainline stack.
An optional data-only control changes a private host image, never the ROM file.
Raw volatile exports and reports belong in an ignored diagnostic directory.
"""
import argparse
import json
from pathlib import Path
import subprocess

from ..assets import Repository, offset, sha256
from ..budget_experiment import audit_hardware
from ..cpu import ModelError
from ..integrated_replay import IntegratedReplay
from ..model import LINE, Profile
from ..scheduler_experiment import candidate_summary
from .compare_core import parse_core
from .compare_save_state import read_export, compare_instructions

ROOT = Path(__file__).resolve().parents[3]
RECORDED_SPECIES = ('groudon', 'milotic', 'drapion', 'rhyperior', 'yanmega',
                    'spheal', 'sealeo', 'snorlax')


class CurrentStateReplay(IntegratedReplay):
    def enable_ledger(self):
        names = (
            'Pokedex_ChooseAnimationWork', 'Pokedex_TryFinishAnimationStage',
            'Pokedex_AdmitAnimationFinish', 'Pokedex_CheckAnimationAudioRunway',
            'Pokedex_ServiceAnimationDictionaryChunk',
            'Pokedex_ServiceAnimationUploadChunk', 'Pokedex_PrepareNextAnimationStage',
            'Pokedex_BeginOwnerLoop', 'Pokedex_EndOwnerLoop',
            'Pokedex_CommitDescriptionAnimation', 'ServiceSampledCryAsync',
        )
        self.ledger_hooks = {self.repo.symbols[n]: n for n in names}
        self.ledger, self.open_ledger = [], []
        self.gdma_spans, self.hardware_writes, self.publication_checks = [], [], []
        self.map_checks, self.finishes = [], []
        self.open_finish = None
        self.stack_low = self.cpu.sp
        self.initial_rebuilt_sp = self.cpu.sp
        original_write = self.cpu.write

        def audit_write(address, value):
            if address in (0xff42, 0xff43, 0xff4a, 0xff4b, 0xff46):
                self.hardware_writes.append(dict(t=self.clock.t, address=address,
                    value=value, interrupt=self.in_interrupt or self.masked))
            original_write(address, value)

        self.cpu.write = audit_write

    def work_state(self):
        fields = {
            'event': 'wPokedexAnimDebugEventReads', 'frame': 'wPokedexAnimStageFrameID',
            'flags': 'wPokedexAnimFlags', 'needed': 'wPokedexAnimStageTileCount',
            'uploaded': 'wPokedexAnimUploadOffset', 'target': 'wPokedexAnimDictionaryTarget',
            'remaining': 'wPokedexAnimDictionaryTilesRemaining',
            'deadline': 'wPokedexAnimDeadline', 'counter': 'hVBlankCounter',
            'work_tick': 'wPokedexAnimWorkTick', 'control': 'wPokedexAnimSchedulerControl',
        }
        result = {k: self.cpu.ram[self.repo.symbols[v][1]] for k, v in fields.items()}
        return dict(result, t=self.clock.t, ly=self.clock.ly, dot=self.clock.dot,
                    loaded=self.asset.total-result['remaining'], a=self.cpu.r[7], f=self.cpu.f,
                    cache=self.cpu.wram[4][0xff4])

    def observe(self):
        super().observe()
        if not hasattr(self, 'ledger_hooks'):
            return
        cpu = self.cpu
        key = (cpu.bank if cpu.pc >= 0x4000 else 0, cpu.pc)
        while self.open_ledger:
            span = self.open_ledger[-1]
            if (cpu.pc, cpu.sp) != (span['return_pc'], span['return_sp']):
                break
            self.open_ledger.pop()
            span['end'] = self.work_state()
            self.ledger.append(span)
        if key in self.ledger_hooks:
            self.open_ledger.append(dict(kind=self.ledger_hooks[key], start=self.work_state(),
                return_pc=cpu.read(cpu.sp) | cpu.read(cpu.sp+1) << 8, return_sp=cpu.sp+2))


def validate_capture_timer(asset, memory, timer):
    if timer == (56, 6):
        return
    if timer == (0, 4) and not asset.sample_blocks and not memory[0xfff1]:
        return
    raise ModelError('Expected sampled timer or inactive-sampled normal timer for a synth cry')


def from_export(repo, payload, initial, species):
    h, memory, banks, vram = read_export(payload)
    asset = repo.load([species])[0]
    if (tuple(reversed(h[6:8])) != repo.symbols['Pokedex_VBlankAnimationFrontpicMap.deadline_reached']
            or h[15] != 15):
        raise ModelError('Expected current-link first publication with normal interrupt enables')
    validate_capture_timer(asset, memory, (h[12], h[13] & 7))
    if (initial['ly'] != 145 or initial['mode'] != 1 or initial['ime']
            or initial['model'] != 0x205 or initial['display'] != 13
            or not 0 < initial['remain'] <= LINE or initial['div_state'] != 2
            or initial['div_cycles'] != -3 or initial['pending_cycles']
            or (initial['scx'], initial['wx'], initial['wy']) != (5, 167, 0)):
        raise ModelError('Captured hardware phase is outside the calibrated CGB-E owner envelope')
    # Model origin precedes the core display-sleep boundary by six T. Derive
    # the phase from the captured LCD state, not the old export header's 606.
    phase = 2 * LINE - initial['remain'] - 6
    regs = dict(zip(('AF', 'BC', 'DE', 'HL', 'SP', 'PC'), h[1:7]))
    captured = [(0, a, memory[a]) for a in (*range(0xc000, 0xd000), *range(0xff80, 0x10000))]
    captured += [(b, 0xd000+i, banks[b*4096+i]) for b in range(1, 8) for i in range(4096)]
    stops = [dict(label='Publication', ly=145, div=h[10] >> 8, tima=h[11],
                  capture=dict(registers=regs, memory=captured, hardware={str(0xff0f): h[14]}))]
    stops += [dict(label=n) for n in ('StageEntry', 'ProducerEntry', 'FrameWait', 'FirstMiss')]
    timer_phase = (phase + 64*(256-h[11]) - (h[10] & 63) + 3) % 12800 + 1
    replay = CurrentStateReplay(repo, asset, stops,
        Profile(hblank_dot=257, audio_phase_t=timer_phase, audio_played_at_publication=4),
        phase, h[10] & 255, timer_state=tuple(h[10:14]))
    cpu = replay.cpu
    cpu.allowed_io.add(0xff4d)
    cpu.ram[:] = memory
    cpu.wram = [bytearray(banks[i:i+4096]) for i in range(0, 32768, 4096)]
    cpu.vram = [bytearray(vram[i:i+8192]) for i in range(0, 16384, 8192)]
    cpu.r[7], cpu.f = h[1] >> 8, h[1] & 0xf0
    for i, value in enumerate(h[2:5]):
        cpu.set_pair(i, value)
    cpu.sp, cpu.pc, cpu.bank = h[5:8]
    cpu.ram[0xff70], cpu.ram[0xff4f] = h[8:10]
    replay.points = [replay.snapshot('Publication')]
    replay.reset_audio_audit()
    replay.enable_ledger()
    return replay


def eager_tail_control(replay):
    """Private ROM-data-only control; leave startup event and captured RAM alone.

    This is a feasibility test, not a proposed all-species production policy.
    The unchanged linked decoder still performs every later six-tile chunk.
    """
    asset = replay.asset
    start = offset(replay.repo.symbols[asset.labels['timeline']])
    rom = bytearray(replay.cpu.rom)
    at, changes = start, []
    for i, event in enumerate(asset.events):
        header = rom[at]
        if header >> 4 != event.frame or header >= 0xf0:
            raise ModelError('Unexpected timeline control layout')
        at += 1 + int((header & 15) == 0)
        if rom[at] != event.target:
            raise ModelError('Unexpected timeline target')
        if i and rom[at] != asset.total:
            changes.append(dict(event=i+1, offset=at, before=rom[at], after=asset.total))
            rom[at] = asset.total
        at += 1
    replay.cpu.rom = bytes(rom)
    return changes


def audit(replay):
    return dict(hardware=audit_hardware(replay),
        wrong_tile_publications=sum(bool(p['mismatched_slot_tiles']) for p in replay.publication_checks),
        wrong_map_publications=sum(bool(p['mismatched_cells']) for p in replay.map_checks),
        publication_checks=replay.publication_checks, map_checks=replay.map_checks,
        finishes=replay.finishes)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--sym', type=Path, default=ROOT/'pokecrystal.sym')
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--species', choices=RECORDED_SPECIES, required=True)
    p.add_argument('--core', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--eager-tail-control', action='store_true',
                   help='Also run a private host-only earlier-decoding metadata control')
    a = p.parse_args()
    repo = Repository(ROOT, a.rom, a.sym)
    source_hashes = {str(path.resolve()): sha256(path.read_bytes())
                     for path in (a.rom, a.sym, a.state)}
    if a.output.resolve() == a.state.parent.resolve():
        p.error('Reports must not be written in the emulator state directory')
    a.output.mkdir(parents=True, exist_ok=True)
    trace, memory = (a.output/f'{a.species}.{suffix}' for suffix in ('trace.txt', 'memory.bin'))
    result = subprocess.run([str(a.core), '--full', '--state', str(a.rom), str(a.state),
                             str(trace), str(memory)], check=True, text=True, capture_output=True)
    (a.output/f'{a.species}.core.txt').write_text(result.stdout)
    points = parse_core(result.stdout, full=True, allow_no_miss=True)
    replay = from_export(repo, memory.read_bytes(), points[0], a.species)
    run, comparison = compare_instructions(replay, trace.read_text(), full=True)
    summary = candidate_summary(run, replay.asset)
    document = dict(scope='ACTUAL_CURRENT_LINK_SAVE_STATE_FULL_REPLAY', **repo.hashes,
        sources=source_hashes, core_sha256=sha256(a.core.read_bytes()),
        initial_model_phase_t=replay.points[0]['t'], core_points=points,
        instruction_comparison=comparison, host=run, summary=summary, ledger=replay.ledger,
        audit=audit(replay))
    if a.eager_tail_control:
        if not comparison['identical']:
            raise ModelError('Refusing a policy control without exact baseline calibration')
        control = from_export(repo, memory.read_bytes(), points[0], a.species)
        changes = eager_tail_control(control)
        control_run = control.run(full=True)
        control_summary = candidate_summary(control_run, control.asset)
        document['eager_tail_control'] = dict(scope='HOST_ONLY_ROM_DATA_COUNTERFACTUAL',
            changes=changes, private_rom_sha256=sha256(control.cpu.rom),
            host=control_run, summary=control_summary, ledger=control.ledger, audit=audit(control))
    for path, before in source_hashes.items():
        if sha256(Path(path).read_bytes()) != before:
            raise ModelError(f'Diagnostic input changed: {path}')
    (a.output/f'{a.species}.json').write_text(json.dumps(document, indent=2)+'\n')
    print(json.dumps(dict(comparison=comparison, misses=summary['misses'],
                         audio=summary['audio_stops'], intervals=summary['full_sequence_intervals'])))
    if a.eager_tail_control:
        print(json.dumps(dict(control='HOST_ONLY_EAGER_TAIL', misses=control_summary['misses'],
            audio=control_summary['audio_stops'], intervals=control_summary['full_sequence_intervals'],
            wrong_tiles=document['eager_tail_control']['audit']['wrong_tile_publications'],
            wrong_maps=document['eager_tail_control']['audit']['wrong_map_publications'])))
    return int(not comparison['identical'])


if __name__ == '__main__':
    raise SystemExit(main())
