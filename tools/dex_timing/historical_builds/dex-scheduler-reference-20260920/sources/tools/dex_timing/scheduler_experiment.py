"""Host-only counterfactual policies over the calibrated linked owner replay.

The baseline executes the unchanged ROM. Candidates replace only the schedule
decision and/or Selected owner's wait guard, with explicit hypothetical CPU
costs. All stage/decode/gather/upload/queue/IRQ/audio routines still execute.
Candidate results are conditional experiments, NOT instruction-exact predictions
for an implementation that does not yet exist. No ROM or emulator state is saved.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import json
from pathlib import Path

from .assets import Repository, sha256
from .cpu import ModelError
from .fixtures import unpack
from .full_replay import summarize
from .model import FRAME
from .probes.compare_save_state import replay_from_export
from .replay import OwnerReplay

ROOT = Path(__file__).resolve().parents[2]
POLICIES = ('baseline', 'wait', 'handoff', 'clock', 'early', 'window', 'work-first', 'tail')
ACTIVE, VALID, READY, ENDED, PENDING, PUBLISHED = 1, 4, 8, 16, 32, 64


@dataclass(frozen=True)
class Job:
    release: int
    action: int
    event: int
    target: int


def jobs_from_schedule(asset, initial_loaded):
    """Tag existing non-idle actions with progress targets, not call indices."""
    event, boundary, loaded, uploaded = 0, asset.events[0].duration, initial_loaded, {}
    jobs = []
    for tick, action in enumerate(asset.actions):
        while tick >= boundary and event+1 < len(asset.events):
            event += 1
            boundary += asset.events[event].duration
        if action == 1:
            loaded = min(asset.total, loaded+6)
            jobs.append(Job(tick, 0x40, 0, loaded))
        elif action == 3:
            if event+1 >= len(asset.events):
                raise ModelError('Upload scheduled after final event')
            target_event = event+2  # Instrumentation numbers timeline reads from one.
            frame = asset.events[event+1].frame
            count = len(asset.plans[frame].sources) if frame else 0
            uploaded[target_event] = min(count, uploaded.get(target_event, 0)+20)
            jobs.append(Job(tick, 0xc0, target_event, uploaded[target_event]))
        elif action:
            raise ModelError('Unsupported reserved schedule action')
    return jobs


def ready_prefix(sources, offset, count, loaded):
    if not 0 <= offset <= count <= 49 or len(sources) < count:
        raise ModelError('Invalid stage extent')
    ready = 0
    for source in sources[offset:min(count, offset+20)]:
        if source >= loaded:
            break
        ready += 1
    return ready


class ExperimentReplay(OwnerReplay):
    def configure(self, policy, dispatch_t=1024, guard_t=64):
        if policy not in POLICIES or dispatch_t < 4 or dispatch_t % 4 or guard_t < 4 or guard_t % 4:
            raise ModelError('Unsupported policy or nonpositive/non-M-cycle cost')
        self.policy, self.dispatch_t, self.guard_t = policy, dispatch_t, guard_t
        self.owner_tick = None
        self.last_action_tick = None
        self.ledger, self.decisions, self.waits = [], [], []
        self.expired_jobs, self.publication_checks = [], []
        self.deferred_audio, self.audio_resuming = False, False
        self.audio_moves, self.vblank_checks = [], []
        self.tail_retried = False
        self.tail_calls = []
        self.irq_ledger = []
        self.open_ledger = []
        self.jobs = jobs_from_schedule(self.asset, self.initial_dictionary_tiles)
        self.retired_jobs = set()
        self.extra_hooks = {self.repo.symbols[name]:name for name in (
            'PokedexSelectedMon_Update', 'Pokedex_PrepareNextAnimationStage',
            'Pokedex_GetNextAnimationScheduleAction', 'Pokedex_BuildAnimationStage',
            'Pokedex_ServiceAnimationDictionaryChunk', 'Pokedex_ServiceAnimationUploadChunk',
            'Pokedex_GatherReadyAnimationTiles', 'HDMATransfer_Exact_NoDI_Arbitrary',
            'Pokedex_CommitAnimationFrontpicMap', 'ServiceSampledCryAsync',
            'SampledCry_FillRollingCache')}
        self.operation_hooks.update(self.extra_hooks)
        main = self.repo.symbols['Pokedex.main']
        address = main[0]*0x4000+main[1]-0x4000
        delay = self.repo.symbols['DelayFrame'][1]
        if self.repo.rom[address+13:address+16] != bytes((0xcd, delay & 255, delay >> 8)):
            raise ModelError('Selected outer wait call moved; re-audit caller guard')
        self.outer_wait_return = main[1]+16

    def field_value(self, name):
        bank, address = self.repo.symbols[name]
        return self.cpu.wram[bank][address-0xd000] if address >= 0xd000 and address < 0xe000 else self.cpu.ram[address]

    def perturb_timer_phase(self, delay_t):
        """A synthetic phase control, never presented as another captured state."""
        if (not self.timer_tac & 4 or self.clock.timer_period not in (12800,262144)
                or not 64 <= delay_t <= self.clock.timer_period or delay_t % 4):
            raise ModelError('Unsupported initial timer phase perturbation')
        old_delay = self.clock.next_timer-self.clock.t
        self.div_origin += old_delay-delay_t
        self.clock.next_timer = self.clock.t+delay_t
        # IF is a separate latch. Retain any already-pending sample interrupt;
        # only the future reload phase and corresponding divider are perturbed.
        self.points = [self.snapshot('Publication')]

    def state(self):
        fields = {'event':'wPokedexAnimDebugEventReads', 'frame':'wPokedexAnimStageFrameID',
                  'flags':'wPokedexAnimFlags', 'slot':'wPokedexAnimStageSlot',
                  'display_slot':'wPokedexAnimDisplaySlot', 'needed':'wPokedexAnimStageTileCount',
                  'uploaded':'wPokedexAnimUploadOffset', 'target':'wPokedexAnimDictionaryTarget',
                  'remaining_dictionary':'wPokedexAnimDictionaryTilesRemaining',
                  'deadline':'wPokedexAnimDeadline', 'counter':'hVBlankCounter',
                  'cache':'wSampledCryCacheCount'}
        return dict(t=self.clock.t, interval=self.clock.t//FRAME, ly=self.clock.ly,
                    loaded=self.asset.total-self.field_value('wPokedexAnimDictionaryTilesRemaining'),
                    **{key:self.field_value(name) for key,name in fields.items()})

    def observe(self):
        super().observe()
        if not self.full or not hasattr(self, 'policy'):
            return
        cpu = self.cpu
        key = (cpu.bank if cpu.pc >= 0x4000 else 0, cpu.pc)
        while self.open_ledger:
            span = self.open_ledger[-1]
            if (cpu.pc, cpu.sp) != (span['return_pc'], span['return_sp']):
                break
            self.open_ledger.pop()
            span['end'] = self.state()
            span['elapsed_t'] = self.clock.t-span['start']['t']
            self.ledger.append(span)
        if key == self.repo.symbols['Pokedex.main'] and not self.in_interrupt:
            self.owner_tick = self.field_value('hVBlankCounter')
            self.tail_retried = False
        if key in self.extra_hooks:
            self.open_ledger.append({'kind':self.extra_hooks[key], 'start':self.state(),
                'return_pc':cpu.read(cpu.sp) | cpu.read(cpu.sp+1)<<8, 'return_sp':cpu.sp+2})
        if key == self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.deadline_reached']:
            state = self.state()
            frame, slot = state['frame'], state['slot']
            mismatches = []
            if frame and slot in (0,1):
                base = (0x8800 if slot == 0 else 0x9330)-0x8000
                for index, source in enumerate(self.asset.plans[frame].sources):
                    expected = self.asset.dictionary[16*source:16*(source+1)]
                    actual = bytes(cpu.vram[1][base+16*index:base+16*(index+1)])
                    if expected != actual:
                        mismatches.append(index)
            self.publication_checks.append(dict(state, mismatched_slot_tiles=mismatches))
        if key == self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap']:
            self.vblank_checks.append(dict(self.state(),
                map_update=self.field_value('hBGMapUpdate'), dma=self.field_value('hDMATransfer')))

    def charge(self, cycles, kind):
        """Hypothetical work in interruptible 4-T quanta; not linked instructions."""
        if self.masked or self.in_interrupt or self.dma_remaining or self.gdma_due:
            raise ModelError('Policy entered from an unsafe/masked/DMA context')
        for _ in range(cycles//4):
            self.clock._due()
            self.cpu.cycles += 4
            self.clock.work(4, kind, masked=True)
        self.clock._due()

    def interrupt(self, ignored):
        start, returning = self.clock.t, self.cpu.pc
        counts = {name:len(rows) for name,rows in self.irq_cycles.items()}
        super().interrupt(ignored)
        if not hasattr(self,'irq_ledger'):
            return
        names = [name for name,rows in self.irq_cycles.items() if len(rows) != counts[name]]
        if len(names) != 1:
            raise ModelError('Unexpected nested interrupt in scheduler ledger')
        name = names[0]
        if name != 'lcd' or start//FRAME != self.clock.t//FRAME:
            self.irq_ledger.append({'kind':name, 'start_t':start, 'end_t':self.clock.t,
                'return_pc':returning})

    def choose_action(self, state):
        # Clock is a release constraint, never a substitute for completed bytes.
        if self.last_action_tick == state['counter']:
            return 0, 'already_serviced_this_display_interval'
        flags = state['flags']
        can_upload = bool(flags & VALID and not flags & (READY | PENDING | PUBLISHED | ENDED))
        source = self.repo.symbols['wPokedexWRAM0Scratch'][1]+0x460
        count = ready_prefix(self.cpu.ram[source:source+49], state['uploaded'],
                             state['needed'], state['loaded']) if can_upload else 0
        if self.policy == 'clock':
            for index, job in enumerate(self.jobs):
                if index in self.retired_jobs:
                    continue
                if job.action == 0x40 and state['loaded'] >= job.target:
                    self.retired_jobs.add(index)
                    continue
                if job.action == 0xc0 and state['event'] > job.event:
                    self.expired_jobs.append(dict(job.__dict__, expired_at=state))
                    self.retired_jobs.add(index)
                    continue
                resident_address = self.repo.symbols['wPokedexAnimResidentFrameIDs'][1]
                resident = (flags & READY and state['slot'] in (0,1) and
                            self.cpu.ram[resident_address+state['slot']] == state['frame'])
                if job.action == 0xc0 and state['event'] == job.event and (resident or state['uploaded'] >= job.target):
                    self.retired_jobs.add(index)
                    continue
                if job.release > state['interval']:
                    break
                if job.action == 0x40:
                    return 0x40, f'released_decode_to_{job.target}'
                if state['event'] == job.event and count:
                    return 0xc0, f'released_upload_event_{job.event}_to_{job.target}'
            return 0, 'no_released_eligible_job'
        if count:
            # Experimental coarse admission margin for *gather before launch*.
            # This is deliberately a sensitivity bound, not a certified WCET.
            if self.policy != 'window' or state['ly'] < 128-count-48:
                return 0xc0, 'ready_prefix'
        if state['loaded'] < state['target'] and state['remaining_dictionary']:
            return 0x40, 'below_retained_high_water'
        return 0, 'no_eligible_work_or_upload_window'

    def try_finish_stage(self):
        """Historical <=8-tile probe; subclasses can test stricter admission."""
        self.charge(self.guard_t, 'policy_tail_guard')
        state = self.state()
        left = state['needed']-state['uploaded']
        source = self.repo.symbols['wPokedexWRAM0Scratch'][1]+0x460
        if (state['flags'] & VALID and not state['flags'] & (READY|PENDING|PUBLISHED|ENDED)
                and 0 < left <= 8 and ready_prefix(self.cpu.ram[source:source+49],
                state['uploaded'],state['needed'],state['loaded']) == left):
            # Bounded feasibility probe, not a guaranteed admission rule:
            # one <=8-tile suffix per owner iteration, never a catch-up loop.
            self.tail_retried = True
            self.tail_calls.append(state)
            self.cpu.push(self.cpu.pc)
            self.cpu.pc = self.repo.symbols['Pokedex_ServiceAnimationUploadChunk'][1]
            self.cpu.cycles += 24
            self.clock.work(24, 'policy_tail_call', masked=True)
            return True
        return False

    def step(self, kind='mainline'):
        if not hasattr(self, 'policy') or self.policy == 'baseline' or self.in_interrupt:
            return super().step(kind)
        cpu = self.cpu
        key = (cpu.bank if cpu.pc >= 0x4000 else 0, cpu.pc)
        if self.policy in ('work-first','tail') and key == self.repo.symbols['ServiceSampledCryAsync']:
            returning = cpu.read(cpu.sp) | cpu.read(cpu.sp+1)<<8
            if returning == self.repo.symbols['DelayFrame.halt'][1]+11 and cpu.bank == 0x10:
                self.charge(self.guard_t, 'policy_audio_order_guard')
                self.deferred_audio = True
                self.audio_moves.append(dict(self.state(),kind='deferred'))
                cpu.pc = cpu.pop()
                cpu.cycles += 16
                self.clock.work(16, 'policy_return', masked=True)
                return
        if self.policy == 'tail' and key == self.repo.symbols['Pokedex_CommitDescriptionAnimation'] and not self.tail_retried:
            if self.try_finish_stage():
                return
        if self.policy not in ('baseline','wait') and key == self.repo.symbols['Pokedex_CommitAnimationFrontpicMap']:
            self.charge(self.guard_t, 'policy_publication_guard')
            if self.field_value('wPokedexAnimFlags') & (PENDING | PUBLISHED):
                # A publication during preceding work belongs to Finalize, not
                # a second submission. Check at the actual submission boundary:
                # an earlier owner-entry check can race a VBlank publication.
                cpu.pc = cpu.pop()
                cpu.cycles += 16
                self.clock.work(16, 'policy_return', masked=True)
                return
        if key == self.repo.symbols['DelayFrame'] and self.owner_tick is not None:
            # Only the outer Dex Selected loop, never another caller's wait.
            returning = cpu.read(cpu.sp) | cpu.read(cpu.sp+1)<<8
            if returning == self.outer_wait_return and cpu.bank == 0x10:
                if self.deferred_audio and not self.audio_resuming:
                    self.charge(self.guard_t, 'policy_audio_order_guard')
                    self.deferred_audio, self.audio_resuming = False, True
                    self.audio_moves.append(dict(self.state(),kind='serviced_after_owner'))
                    cpu.push(cpu.pc)
                    cpu.pc = self.repo.symbols['ServiceSampledCryAsync'][1]
                    cpu.cycles += 24
                    self.clock.work(24, 'policy_audio_call', masked=True)
                    return
                self.audio_resuming = False
                self.charge(self.guard_t, 'policy_wait_guard')
                now = self.state()
                skip = now['counter'] != self.owner_tick
                self.waits.append(dict(now, owner_counter=self.owner_tick, skipped=skip))
                if skip:
                    # Keep DelayFrame's existing audio service and return; omit
                    # only arming and waiting for one additional VBlank.
                    cpu.pc = self.repo.symbols['DelayFrame.halt'][1]+8
                    return
        if self.policy not in ('wait', 'baseline', 'handoff') and key == self.repo.symbols['Pokedex_GetNextAnimationScheduleAction']:
            self.charge(self.dispatch_t, 'policy_dispatch')
            state = self.state()
            action, reason = self.choose_action(state)
            if action:
                self.last_action_tick = state['counter']
            self.decisions.append(dict(state, action=action, reason=reason))
            cpu.r[7], cpu.f = action, 0x80 if not action else 0
            cpu.pc = cpu.pop()
            cpu.cycles += 16  # RET, in addition to the explicit decision budget.
            self.clock.work(16, 'policy_return', masked=True)
            return
        return super().step(kind)


def ledger_summary(replay, run):
    groups = {}
    for span in replay.ledger:
        group = groups.setdefault(span['kind'], {'calls':0, 'total_t':0, 'max_t':0, 'crossed_vblank':0})
        group['calls'] += 1
        group['total_t'] += span['elapsed_t']
        group['max_t'] = max(group['max_t'], span['elapsed_t'])
        group['crossed_vblank'] += span['start']['interval'] != span['end']['interval']
    publications = [p for p in run['lifecycle'] if p['kind'].endswith('.display_recorded')]
    events, deadlines, due = [], [], 0
    for event in replay.asset.events:
        deadlines.append(due)
        due += event.duration
    deadlines.append(due)
    for publication in publications:
        event = publication['trace'][5]
        rows = [s for s in replay.ledger if s['end' if s['kind'] == 'Pokedex_PrepareNextAnimationStage' else 'start']['event'] == event and
                s['kind'] != 'PokedexSelectedMon_Update']
        events.append({'event':event, 'due_interval':deadlines[event-1],
            'published_interval':publication['t']//FRAME,
            'operations':rows})
    return {'groups':groups, 'events':events}


def candidate_summary(run, asset):
    """Do not hide duplicate publications when the wait-only control regresses."""
    expected = []
    due = 0
    for event in asset.events:
        expected.append(due)
        due += event.duration
    expected.append(due)
    pubs = [p for p in run['lifecycle'] if p['kind'].endswith('.display_recorded')]
    seen, duplicates = set(), []
    unique = []
    for p in pubs:
        event = p['trace'][5]
        if not 1 <= event <= len(expected):
            raise ModelError('Publication references an invalid timeline event')
        if event in seen:
            duplicates.append({'event':event,'interval':p['t']//FRAME})
        else:
            unique.append(p)
            seen.add(event)
    if [p['trace'][5] for p in unique] != list(range(1,len(expected)+1)):
        raise ModelError('Counterfactual skipped or reordered timeline events')
    filtered = dict(run,lifecycle=[p for p in run['lifecycle'] if not p['kind'].endswith('.display_recorded')]+unique)
    summary = summarize(filtered,asset)
    summary['duplicate_publications'] = duplicates
    return summary


def run_case(job):
    species, policy, dispatch, delay, directory = job
    repo = Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym')
    fixture = ROOT/f'tools/dex_timing/fixtures/{species}_initial_volatile.json'
    payload, points = unpack(json.loads(fixture.read_text()), repo)
    replay = replay_from_export(repo, payload, points, species, ExperimentReplay)
    replay.configure(policy, dispatch)
    if delay is not None:
        replay.perturb_timer_phase(delay)
    run = replay.run(full=True)
    summary = candidate_summary(run, replay.asset)
    document = {'scope':'EXACT_BASELINE_LEDGER' if policy == 'baseline' else 'HOST_POLICY_COUNTERFACTUAL',
        **repo.hashes, 'input_sha256':sha256(payload), 'fixture_sha256':sha256(fixture.read_bytes()),
        'host_sources':{str(path.relative_to(ROOT)):sha256(path.read_bytes())
                        for path in sorted((ROOT/'tools/dex_timing').rglob('*.py'))},
        'policy':policy, 'dispatch_budget_t':dispatch, 'wait_guard_t':replay.guard_t,
        'timer_delay_t':delay, 'initial_state_scope':'ACTUAL' if delay is None else 'SYNTHETIC_TIMER_PHASE_PERTURBATION',
        'assumptions':['Same initial publication state; startup latency is not modeled',
            'Normal speed, no new input, two existing slots, unchanged 96-tail startup and 32-block prefill',
            'Linked stage/decode/gather/upload/queue/publication/audio costs retained',
            'Candidate decisions cost a hypothetical budget, not assembled code',
            'Window policy reserves 48 lines for gathering before the existing helper cutoff',
            'One regular animation action per display counter; tail policy adds at most one <=8-tile suffix per owner iteration',
            'Tail probe has a bounded call count, not a certified elapsed-time admission bound',
            'Deadline/underflow/publication behavior unchanged, including visible failed stages'],
        'summary':summary, 'ledger':ledger_summary(replay,run), 'decisions':replay.decisions,
        'waits':replay.waits, 'expired_jobs':replay.expired_jobs,
        'publication_checks':replay.publication_checks, 'audio_moves':replay.audio_moves,
        'vblank_checks':replay.vblank_checks, 'tail_calls':replay.tail_calls,
        'irq_ledger':replay.irq_ledger, 'host':run}
    suffix = '' if delay is None else f'-phase-{delay}'
    Path(directory, f'{species}-{policy}-{dispatch}{suffix}.json').write_text(json.dumps(document,indent=2)+'\n')
    return {'species':species, 'policy':policy, 'dispatch_t':dispatch,
        'timer_delay_t':delay,
        'misses':len(summary['misses']),
        'duplicate_publications':len(summary['duplicate_publications']),
        'late_publications':sum(p['late_intervals'] > 0 for p in summary['publications']),
        'max_late_intervals':max(p['late_intervals'] for p in summary['publications']),
        'audio':summary['audio_stops'], 'completion_t':summary['completion_t'],
        'skipped_waits':sum(w['skipped'] for w in replay.waits),
        'publications_with_wrong_tile_bytes':sum(bool(p['mismatched_slot_tiles']) for p in replay.publication_checks),
        'hypothetical_policy_t':sum(v for k,v in run['totals_t'].items() if k.startswith('policy_'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--species', nargs='+', choices=('weavile','luxray','dusknoir'),
                        default=['weavile','luxray','dusknoir'])
    parser.add_argument('--policies', nargs='+', choices=POLICIES, default=list(POLICIES))
    parser.add_argument('--dispatch-t', nargs='+', type=int, default=[1024])
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--timer-delay-t', nargs='+', type=int, default=[None],
                        help='Synthetic delay to next sample timer edge, not a new capture')
    args = parser.parse_args()
    if args.jobs < 1 or any(n < 4 or n % 4 for n in args.dispatch_t):
        parser.error('Use positive workers and positive M-cycle-aligned dispatch costs')
    args.output.mkdir(parents=True, exist_ok=True)
    if any(t is not None and (not 64 <= t <= 12800 or t % 4) for t in args.timer_delay_t):
        parser.error('Timer delays must be M-cycle-aligned values in 64..12800 T')
    tasks = [(s,p,d,t,args.output) for s in args.species for p in args.policies
             for d in (args.dispatch_t[:1] if p in ('baseline','wait','handoff') else args.dispatch_t)
             for t in args.timer_delay_t]
    with ProcessPoolExecutor(args.jobs) as pool:
        results = []
        for result in pool.map(run_case, tasks):
            results.append(result)
            print(json.dumps(result,sort_keys=True),flush=True)
    (args.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
