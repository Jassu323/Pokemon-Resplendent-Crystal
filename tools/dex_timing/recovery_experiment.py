"""Host-only steady-display publication admission and recovery controls.

This is a costed counterfactual, not an assembled implementation. During settled,
input-free Selected playback, retain already-published OAM and viewport registers.
The host enforces that contract; a hypothetical owner-route guard is charged in
place of the redundant linked viewport stores. All map transfers, bookkeeping,
audio, and remaining interrupt instructions still execute. No ROM is changed.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from .assets import Repository, sha256
from .budget_experiment import (BudgetReplay, audit_hardware, publication_budget,
                                viewport_write_block)
from .cpu import ModelError
from .fixtures import unpack
from .followup import read_stops
from .full_replay import ACTUAL, PARTIAL
from .model import FRAME, LINE, Profile
from .probes.compare_save_state import replay_from_export
from .probes.export_core_fixture import fixture_bytes
from .replay import OwnerReplay
from .scheduler_experiment import ROOT, candidate_summary, ledger_summary

VIEWPORT = (('hSCX',0xff43),('hSCY',0xff42),('hWY',0xff4a),('hWX',0xff4b))
REQUESTS = ('hBGMapUpdate','hCGBPalUpdate','hDMATransfer','hBGMapMode',
            'wRequested1bppSize','wRequested2bppSize','hMapAnims','wPokedexOwnerTransition')


class RecoveryReplay(BudgetReplay):
    def configure_recovery(self, dispatch_t=1024, viewport_guard_t=64,
                           forced_entry_phase=None, cutoff=149):
        if viewport_guard_t < 4 or viewport_guard_t % 4:
            raise ModelError('Viewport guard cost must be a positive M-cycle multiple')
        if forced_entry_phase is not None and not 0 <= forced_entry_phase < FRAME:
            raise ModelError('Forced entry phase must lie within one physical frame')
        self.configure_budget(cutoff,'tail',dispatch_t,quiet_oam=True)
        self.viewport_guard_t = viewport_guard_t
        self.viewport_start,self.viewport_end = viewport_write_block(self.repo)
        self.viewport = tuple(self.cpu.ram[address] for _,address in VIEWPORT)
        self.viewport_skips, self.range_checks = [], []
        self.forced_entry_phase, self.forced_entry = forced_entry_phase, None
        self.check_owner_contract()

    def check_owner_contract(self):
        if self.field_value('wPokedexSelectedState') != 1:
            raise ModelError('Steady-display experiment left Selected playback')
        if any(self.field_value(name) for name in REQUESTS):
            raise ModelError('Steady-display experiment has competing display requests')
        for (name,address),expected in zip(VIEWPORT,self.viewport):
            if self.field_value(name) != expected or self.cpu.ram[address] != expected:
                raise ModelError('Steady-display viewport ownership was violated')

    def step(self, kind='mainline'):
        if not hasattr(self,'viewport'):
            return super().step(kind)
        cpu = self.cpu
        key = (cpu.bank if cpu.pc >= 0x4000 else 0,cpu.pc)
        if key in (self.repo.symbols['VBlank'],
                   self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.deadline_reached']):
            self.check_owner_contract()
        if key == (0,self.viewport_start):
            if not (self.in_interrupt or self.masked):
                raise ModelError('Viewport route entered outside VBlank')
            self.check_owner_contract()
            self.viewport_skips.append(self.state())
            # Owner-route cost, not four runtime equality tests. The owner must
            # relinquish this route before input/transition/UI changes require it.
            cpu.cycles += self.viewport_guard_t
            self.clock.work(self.viewport_guard_t,'policy_viewport_guard',masked=True)
            cpu.pc = self.viewport_end
            return
        if key == (self.cutoff_pc[0],self.cutoff_pc[1]-2):
            state = self.state()
            due = ((state['counter']+1-state['deadline']) & 255) < 128
            if (self.forced_entry_phase is not None and self.forced_entry is None
                    and state['event'] >= 2 and due):
                phase = self.clock.t % FRAME
                if phase > self.forced_entry_phase:
                    raise ModelError('Recovery injection would move time backwards')
                delay = (self.forced_entry_phase-phase+3)//4*4
                self.forced_entry = dict(state,delay_t=delay,target_phase=self.forced_entry_phase)
                cpu.cycles += delay
                self.clock.work(delay,'forced_masked_entry_delay',masked=True)
                return
        if key == self.cutoff_pc:
            self.check_owner_contract()
            sampled = cpu.r[7]
            self.range_checks.append(dict(self.state(),sampled_ly=sampled,
                                          admitted=144 <= sampled < self.cutoff))
            # CP 144 / JR C: keep the sampled LY in A. A reports zero early on
            # physical line 153; an upper-bound-only gate wrongly accepts it.
            cost = 20 if sampled < 144 else 16
            cpu.cycles += cost
            self.clock.work(cost,'policy_lower_ly_guard',masked=True)
            if sampled < 144:
                cpu.f = 0x50
                cpu.pc = self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.defer'][1]
                return
        return super().step(kind)


def initial_asset_maps(asset, frame, slot):
    tiles,attrs = [x*7+y for y in range(7) for x in range(7)],[1]*49
    index = 0
    if frame:
        for position,source in asset.plans[frame].pairs:
            if position & 128:
                tiles[position & 127] = source
            else:
                tiles[position] = (0x80 if slot == 0 else 0x33)+index
                attrs[position] = 9
                index += 1
    return bytes(tiles),bytes(attrs)


def seed_partial_residents(replay):
    """Complete uncaptured graphics already declared resident, never future work.

    Older text captures do not contain VRAM or the queued map buffers. Canonical
    asset bytes here are an explicit initial-state assumption, not measured data.
    No animation flag, count, source list, or decoded dictionary lead is changed.
    """
    cpu,repo,asset = replay.cpu,replay.repo,replay.asset
    scratch = repo.symbols['wPokedexWRAM0Scratch'][1]
    residents = cpu.data(repo.symbols['wPokedexAnimResidentFrameIDs'][1],2)
    for slot,frame in enumerate(residents):
        if frame == 255:
            continue
        if not 0 < frame < len(asset.plans):
            raise ModelError('Partial capture has an invalid resident frame')
        plan = asset.plans[frame]
        if any(source >= replay.initial_dictionary_tiles for source in plan.sources):
            raise ModelError('Resident assumption would introduce undecoded future tiles')
        dest = 0x800 if slot == 0 else 0x1330
        for index,source in enumerate(plan.sources):
            cpu.vram[1][dest+16*index:dest+16*(index+1)] = asset.dictionary[16*source:16*(source+1)]
        cpu.block(scratch+(0x39c if slot == 0 else 0x3fe),
                  b''.join(initial_asset_maps(asset,frame,slot)))
    frame = cpu.read(repo.symbols['wPokedexAnimStageFrameID'][1])
    slot = cpu.read(repo.symbols['wPokedexAnimStageSlot'][1])
    if frame and residents[slot] != frame:
        raise ModelError('Partial first publication is not a declared resident frame')
    for name,data in zip(('wPokedexOwnerTilemapBuffer','wPokedexOwnerAttrmapBuffer'),
                         initial_asset_maps(asset,frame,slot)):
        bank,address = repo.symbols[name]
        for row in range(7):
            start = address-0xd000+32*(row+1)+1
            cpu.wram[bank][start:start+7] = data[7*row:7*(row+1)]


def initial_replay(repo, species, replay_class=RecoveryReplay, use_additional_actual=False):
    if species in ACTUAL or use_additional_actual:
        source = ROOT/f'tools/dex_timing/fixtures/{species}_initial_volatile.json'
        payload,points = unpack(json.loads(source.read_text()),repo)
        scope = 'ACTUAL_INITIAL_VOLATILE_MEMORY'
    else:
        source = ROOT/f'tools/dex_timing/fixtures/{species}_owner_followup.txt'
        stops = read_stops(source.read_text(),repo.symbols)
        phase,low = PARTIAL[species]
        seed = OwnerReplay(repo,repo.load([species])[0],stops,
            Profile(hblank_dot=257,audio_phase_t=phase,audio_played_at_publication=4),606,low)
        seed.cpu.field('hSampledCrySavedIE',15)
        seed.cpu.field('hSampledCrySavedTAC',0)
        # The reference runner explicitly establishes these hardware registers
        # before importing a synthetic fixture. Keep its control values in the
        # portable CPU register view as well as the fixed PPU profile.
        for _,address in VIEWPORT:
            seed.cpu.ram[address] = {0xff43:5,0xff4b:167}.get(address,0)
        seed_partial_residents(seed)
        payload = fixture_bytes(seed,stops,606,low)
        # The same explicit PPU envelope as full_replay's core-validated partial
        # continuation. These are assumptions, not a new complete user capture.
        points = [dict(div_cycles=-3,div_state=2,pending_cycles=0,ly=145,remain=300,
                       ime=False,model=0x205,scx=5,wx=167,wy=0)]
        scope = 'PARTIAL_CAPTURE_CANONICAL_INITIAL_RESIDENTS_SILENT_POST_CRY'
    replay = replay_from_export(repo,payload,points,species,replay_class)
    return replay, dict(initial_state_scope=scope,input_sha256=sha256(payload),
                        fixture_sha256=sha256(source.read_bytes()))


def run_case(job):
    species,dispatch,guard,delay,forced,cutoff,directory = job
    repo = Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    replay,identity = initial_replay(repo,species)
    replay.configure_recovery(dispatch,guard,forced,cutoff)
    if delay is not None:
        replay.perturb_timer_phase(delay)
    run = replay.run(full=True)
    summary,audit = candidate_summary(run,replay.asset),audit_hardware(replay)
    result = dict(species=species,dispatch_t=dispatch,viewport_guard_t=guard,
        timer_delay_t=delay,forced_entry_phase=forced,cutoff=cutoff,**identity,
        misses=len(summary['misses']),
        late_publications=sum(p['late_intervals'] > 0 for p in summary['publications']),
        duplicates=len(summary['duplicate_publications']),
        wrong_slots=sum(bool(p['mismatched_slot_tiles']) for p in replay.publication_checks),
        wrong_maps=sum(bool(p['mismatched_cells']) for p in replay.map_checks),
        cry_underruns=sum(p['reason']=='underrun' for p in summary['audio_stops']),
        competing_transfers=len(replay.competing_transfers),
        viewport_skips=len(replay.viewport_skips),
        **{key:audit[key] for key in ('gdma_outside_vblank','writes_outside_vblank',
                                    'latest_gdma_end_phase','latest_write_end_phase')})
    document = dict(scope='HOST_STEADY_DISPLAY_RECOVERY_COUNTERFACTUAL',**repo.hashes,
        host_sources={str(p.relative_to(ROOT)):sha256(p.read_bytes())
                      for p in sorted((ROOT/'tools/dex_timing').rglob('*.py'))},
        result=result,summary=summary,hardware_audit=audit,range_checks=replay.range_checks,
        forced_entry=replay.forced_entry,viewport_skips=replay.viewport_skips,
        guard_reads=replay.guard_reads,publication_entries=replay.publication_entries,
        publication_checks=replay.publication_checks,map_checks=replay.map_checks,
        decisions=replay.decisions,ledger=ledger_summary(replay,run),host=run)
    name = f'{species}-d{dispatch}-g{guard}-ly{cutoff}-phase{delay}-forced{forced}.json'
    Path(directory,name).write_text(json.dumps(document,indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--species',nargs='+',choices=[*ACTUAL,*PARTIAL],default=[*ACTUAL,*PARTIAL])
    parser.add_argument('--dispatch-t',nargs='+',type=int,default=[1024])
    parser.add_argument('--viewport-guard-t',nargs='+',type=int,default=[64])
    parser.add_argument('--timer-delay-t',nargs='+',type=int,default=[None])
    parser.add_argument('--forced-entry-phase',nargs='+',type=int,default=[None])
    parser.add_argument('--cutoff',nargs='+',type=int,choices=range(146,151),default=[149])
    parser.add_argument('--jobs',type=int,default=8)
    args = parser.parse_args()
    if args.jobs < 1 or any(x < 4 or x % 4 for x in [*args.dispatch_t,*args.viewport_guard_t]):
        parser.error('Positive worker count and M-cycle work costs required')
    if any(x is not None and (not 64 <= x <= 12800 or x % 4) for x in args.timer_delay_t):
        parser.error('Timer phase must be 64..12800 T in M-cycle multiples')
    if any(x is not None and not 0 <= x < FRAME for x in args.forced_entry_phase):
        parser.error('Forced entry must lie within one physical frame')
    args.output.mkdir(parents=True,exist_ok=True)
    repo = Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    (args.output/'publication-bounds.json').write_text(json.dumps(
        publication_budget(repo,hold_viewport=True),indent=2)+'\n')
    tasks = [(s,d,g,t,f,c,args.output) for s in args.species for d in args.dispatch_t
             for g in args.viewport_guard_t for t in args.timer_delay_t
             for f in args.forced_entry_phase for c in args.cutoff]
    with ProcessPoolExecutor(args.jobs) as pool:
        results = []
        for result in pool.map(run_case,tasks):
            results.append(result)
            print(json.dumps(result,sort_keys=True),flush=True)
    (args.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
