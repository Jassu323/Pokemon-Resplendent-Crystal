"""Host-only complete-stage finishing probes. No game ROM is modified.

Compare the historical <=8-tile heuristic with an unrestricted <=20-tile
feasibility control and a conservative visible-only, full-chain admission rule.
The feasibility control is deliberately NOT a safe scheduling recommendation.
The early-budget variant submits a completed frame before (not instead of) the
regular producer's diagnostic bookkeeping. All linked bookkeeping still runs.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import math
from pathlib import Path

from .assets import Repository, sha256
from .budget_experiment import audit_hardware, visible_prefix_bound
from .costs import machine, run_to, interrupt_cost
from .cpu import ModelError
from .full_replay import ACTUAL, PARTIAL
from .model import FRAME, LINE
from .recovery_experiment import RecoveryReplay, initial_replay
from .scheduler_experiment import (ROOT, VALID, READY, PENDING, PUBLISHED, ENDED,
                                   ready_prefix, candidate_summary, ledger_summary)


def drained_visible_bound(work_t, timer_enabled=True, timer_irq_t=1480):
    """Visible-only response bound after all enabled pending IRQs are serviced.

    Arbitrary future phase is still allowed. Unlike the generic unknown-entry
    bound, this does not add an old pending IRQ as well as the next periodic one.
    No VBlank, alternate STAT handler, fast-pitch timer or masked caller is in
    this contract. Hardware waits are charged as work, deliberately overcounting
    interrupts that overlap autonomous HDMA progress.
    """
    if work_t <= 0 or work_t%4 or timer_irq_t < 0 or timer_irq_t%4:
        raise ModelError('Finishing costs must be M-cycle multiples with positive work')
    elapsed = work_t
    for _ in range(100):
        new = work_t+(math.ceil(elapsed/12800)*timer_irq_t if timer_enabled else 0)+math.ceil(elapsed/LINE)*108
        if new == elapsed:
            return new
        elapsed = new
    raise ModelError('Finishing response bound did not converge')


def finishing_costs(repo, queue_rom=None, upload_rom=None):
    """Count linked CPU paths; price the hardware helper separately.

    Both slots, source-list offsets, ready-lead branches and trace-ring positions
    are covered. No helper wait is measured as zero in the resulting envelope.
    The helper body is skipped only to isolate the caller's post-transfer cost.
    """
    rows = {}
    for count in range(1,21):
        prefix, suffix = 0, 0
        for slot in (0,1):
            for uploaded in (0,20,49-count):
                cpu = machine(repo)
                if upload_rom is not None:
                    cpu.rom = upload_rom
                for name,value in (('wPokedexAnimFlags',7),('wPokedexAnimStageSlot',slot),
                        ('wPokedexAnimStageFrameID',1),('wPokedexAnimStageTileCount',uploaded+count),
                        ('wPokedexAnimDictionaryTileCount',255),('wPokedexAnimDictionaryTilesRemaining',0),
                        ('wPokedexAnimUploadOffset',uploaded)):
                    cpu.field(name,value)
                cpu.block(repo.symbols['wPokedexWRAM0Scratch'][1]+0x460,bytes(range(49)))
                cpu.allowed_io.add(0xff40)
                cpu.ram[0xff40] = 0x80
                run_to(cpu,'Pokedex_ServiceAnimationUploadChunk','HDMATransfer_Exact_NoDI_Arbitrary')
                if cpu.r[1] != count:
                    raise ModelError('Finishing fixture gathered an unexpected number of tiles')
                prefix = max(prefix,cpu.cycles)
                cpu.pc = cpu.pop()
                before = cpu.cycles
                while cpu.pc != 0xffff:
                    cpu.step()
                suffix = max(suffix,cpu.cycles-before)
                if cpu.read(repo.symbols['wPokedexAnimFlags'][1]) != 15:
                    raise ModelError('Finishing fixture did not mark the stage ready')
        rows[count] = dict(upload_prefix_t=prefix,upload_suffix_t=suffix)
    queue = 0
    for slot in (0,1):
        for publishes in (0,1,255):
            for lead in (0,255):
                for ring in range(5):
                    cpu = machine(repo)
                    if queue_rom is not None:
                        cpu.rom = queue_rom
                    for name,value in (('wPokedexAnimFlags',15),('wPokedexAnimPlaybackState',2),
                            ('wPokedexAnimStageFrameID',1),('wPokedexAnimStageSlot',slot),
                            ('wPokedexAnimDebugMapPublishes',publishes),
                            ('wPokedexAnimDebugMinReadyLead',lead)):
                        cpu.field(name,value)
                    # Trace index is bounded by the linked record writer.
                    cpu.field('wPokedexAnimTraceHead',ring)
                    queue = max(queue,cpu.run('Pokedex_CommitDescriptionAnimation'))
    cpu = machine(repo)
    cpu.field('hSampledCryTimer',0)
    inactive_timer_t = interrupt_cost(cpu,0x50,'SampledCryTimer')
    # Includes the real helper setup, a complete scanline of launch-phase wait,
    # one line per tile, final DMA stall and poll/RET allowance. Treat the entire
    # elapsed hardware allowance as interruptible work: pessimistic but finite.
    for count,row in rows.items():
        row['queue_t'] = queue
        row['helper_allowance_t'] = 124+LINE+count*LINE+32+128
        row['wrapper_allowance_t'] = 256  # CALL, guard, branch/carry slack.
        row['chain_work_t'] = sum(row[k] for k in ('upload_prefix_t','upload_suffix_t',
            'queue_t','helper_allowance_t','wrapper_allowance_t'))
        row['unknown_entry_chain_bound_t'] = visible_prefix_bound(row['chain_work_t'])
        row['chain_bound_t'] = drained_visible_bound(row['chain_work_t'])
        row['chain_bound_no_timer_t'] = drained_visible_bound(row['chain_work_t'],False)
        row['inactive_timer_irq_t'] = inactive_timer_t
        row['chain_bound_inactive_timer_t'] = drained_visible_bound(row['chain_work_t'],True,inactive_timer_t)
        row['launch_bound_t'] = drained_visible_bound(row['upload_prefix_t']+124+LINE+128+64)
        row['launch_bound_no_timer_t'] = drained_visible_bound(row['upload_prefix_t']+124+LINE+128+64,False)
        row['launch_bound_inactive_timer_t'] = drained_visible_bound(row['upload_prefix_t']+124+LINE+128+64,True,inactive_timer_t)
    return rows


def finish_admission(state, count, costs, active_audio, cache, period, remaining_audio,
                     timer_enabled=True, minimum_margin_t=0):
    """Hardware-readable coarse clock only: discard the rest of the current LY.

    This bound excludes VBlank, so reject any job that would cross it even when
    its authored deadline is later. Fail closed outside the measured normal-
    speed, normal-pitch envelope. Two display intervals of cache runway reserve
    the subsequent owner return and one complete eight-block refill; replays
    additionally audit that the actual service occurs within that allowance.
    """
    if not 1 <= count <= 20 or not 0 <= remaining_audio <= 65535:
        raise ModelError('Invalid finishing extent or remaining cry length')
    if minimum_margin_t<0 or minimum_margin_t%4:
        raise ModelError('Finishing reserve must be a nonnegative M-cycle multiple')
    if active_audio and not timer_enabled:
        raise ModelError('Active sampled audio requires its timer envelope')
    costs=dict(costs)
    if not timer_enabled:
        costs['chain_bound_t']=costs['chain_bound_no_timer_t']
        costs['launch_bound_t']=costs['launch_bound_no_timer_t']
    elif not active_audio:
        # This call chain cannot start a cry. A restored, still-running timer
        # therefore stays on the measured short handler until we return.
        costs['chain_bound_t']=costs['chain_bound_inactive_timer_t']
        costs['launch_bound_t']=costs['launch_bound_inactive_timer_t']
    delta = (state['deadline']-((state['counter']+1)&255))&255
    if delta >= 128 or not 0 <= state['ly'] < 144:
        return dict(admitted=False,reason='outside_visible_future_window')
    available = (143-state['ly'])*LINE
    launch_line = state['ly']+1+math.ceil(costs['launch_bound_t']/LINE)
    reserve = min(remaining_audio,1+math.ceil((costs['chain_bound_t']+2*FRAME)/12800))
    audio_ok = not active_audio or (period == 200 and cache >= reserve)
    fits = costs['chain_bound_t']+minimum_margin_t <= available and launch_line < 128-count
    return dict(admitted=fits and audio_ok,reason='admitted' if fits and audio_ok else
                'insufficient_audio_runway' if not audio_ok else 'insufficient_visible_time',
                available_t=available,launch_line_bound=launch_line,cache_reserve=reserve,
                minimum_margin_t=minimum_margin_t,
                timer_enabled=timer_enabled,**costs)


class FinishReplay(RecoveryReplay):
    def configure_finish(self, mode='budget', dispatch_t=1024, viewport_guard_t=64,
                         finish_guard_t=256):
        self.configure_recovery(dispatch_t,viewport_guard_t)
        if mode not in ('eight','probe','budget','early-budget') or finish_guard_t < 4 or finish_guard_t%4:
            raise ModelError('Invalid finishing probe configuration')
        self.finish_mode,self.finish_guard_t = mode,finish_guard_t
        self.finish_margin_t=0
        self.finish_costs = finishing_costs(self.repo)
        self.finish_attempts,self.finish_spans = [],[]
        self.open_finish = None

    def try_finish_stage(self):
        if self.finish_mode == 'eight':
            return super().try_finish_stage()
        early = self.finish_mode == 'early-budget'
        if early and self.cpu.pc != self.repo.symbols['Pokedex_ServiceAnimationProducer.record_dictionary'][1]:
            return False
        self.charge(self.guard_t,'policy_tail_guard')
        state = self.state()
        left = state['needed']-state['uploaded']
        source = self.repo.symbols['wPokedexWRAM0Scratch'][1]+0x460
        if not (state['flags'] & VALID and not state['flags'] & (READY|PENDING|PUBLISHED|ENDED)
                and state['slot'] != state['display_slot'] and 0 < left <= 20
                and ready_prefix(self.cpu.ram[source:source+49],state['uploaded'],
                                 state['needed'],state['loaded']) == left):
            return False
        self.charge(self.finish_guard_t,'policy_finish_admission')
        # charge() ends on an interruptible boundary and drains enabled pending
        # IRQs. A runtime admission check needs this same entry contract.
        if self.clock.pending_enabled() or self.masked or self.in_interrupt:
            raise ModelError('Finishing admission has unbudgeted pending interrupts')
        if (self.field_value('hLCDCPointer') or
                (self.timer_tac & 4 and self.clock.timer_period < 12800)):
            raise ModelError('Finishing admission left its measured interrupt envelope')
        state = self.state()
        remaining_address = self.repo.symbols['hSampledCryBlocks'][1]
        remaining_audio = self.cpu.read(remaining_address)|self.cpu.read(remaining_address+1)<<8
        decision = finish_admission(state,left,self.finish_costs[left],
            self.field_value('hSampledCryTimer'),state['cache'],
            self.field_value('wSampledCryBlockPeriod'),remaining_audio,bool(self.timer_tac & 4),
            self.finish_margin_t)
        attempt = dict(state,count=left,remaining_audio=remaining_audio,
                       active_audio=bool(self.field_value('hSampledCryTimer')),
                       **decision,probe_override=self.finish_mode=='probe')
        self.finish_attempts.append(attempt)
        if not decision['admitted'] and self.finish_mode != 'probe':
            return False
        self.tail_retried = True
        self.tail_calls.append(state)
        self.open_finish = dict(start=attempt,early=early,phase='upload',
            return_pc=self.cpu.pc if early else self.cpu.read(self.cpu.sp)|self.cpu.read(self.cpu.sp+1)<<8,
            return_sp=self.cpu.sp if early else self.cpu.sp+2)
        self.cpu.push(self.cpu.pc)
        self.cpu.pc = self.repo.symbols['Pokedex_ServiceAnimationUploadChunk'][1]
        self.cpu.cycles += 24
        self.clock.work(24,'policy_tail_call',masked=True)
        return True

    def step(self,kind='mainline'):
        if getattr(self,'finish_mode',None) == 'early-budget' and not self.in_interrupt:
            key = (self.cpu.bank if self.cpu.pc >= 0x4000 else 0,self.cpu.pc)
            if key == self.repo.symbols['Pokedex_ServiceAnimationProducer.record_dictionary']:
                if self.open_finish and self.open_finish['phase'] == 'upload':
                    self.open_finish['phase'] = 'queue'
                    self.cpu.push(self.cpu.pc)
                    self.cpu.pc = self.repo.symbols['Pokedex_CommitDescriptionAnimation'][1]
                    self.cpu.cycles += 24
                    self.clock.work(24,'policy_early_commit_call',masked=True)
                    return
                if not self.tail_retried and self.try_finish_stage():
                    return
        return super().step(kind)

    def observe(self):
        super().observe()
        if not getattr(self,'open_finish',None):
            return
        span = self.open_finish
        key = (self.cpu.bank if self.cpu.pc >= 0x4000 else 0,self.cpu.pc)
        if key == self.repo.symbols['Pokedex_CommitDescriptionAnimation'] or (
                span['early'] and self.cpu.pc == span['return_pc']):
            span.setdefault('upload_end',self.state())
        if ((not span['early'] or span['phase']=='queue') and
                (self.cpu.pc,self.cpu.sp) == (span['return_pc'],span['return_sp'])):
            span['end'] = self.state()
            span['elapsed_t'] = self.clock.t-span['start']['t']
            span['within_bound'] = span['elapsed_t'] <= span['start'].get('chain_bound_t',0)
            span['crossed_vblank'] = span['start']['interval'] != span['end']['interval']
            self.finish_spans.append(span)
            self.open_finish = None


def audit_audio_reserve(replay):
    """Check the scheduling assumption behind the two-interval cache reserve.

    A fully buffered remaining cry cannot starve, so it needs no further refill.
    Otherwise require service entry within one interval of queue completion and
    the whole service to return within another. This is a replay assertion, not
    a proof for other owners, input paths, timer pitches, or future ROM changes.
    """
    checks=[]
    services=[s for s in replay.ledger if s['kind']=='ServiceSampledCryAsync']
    for span in replay.finish_spans:
        start,end=span['start'],span['end']
        if not start['active_audio'] or start['remaining_audio'] <= start['cache']:
            continue
        following=next((s for s in services if s['start']['t'] >= end['t']),None)
        entry=None if following is None else following['start']['t']-end['t']
        service=None if following is None else following['elapsed_t']
        checks.append(dict(event=start['event'],entry_delay_t=entry,service_t=service,
            ok=entry is not None and entry <= FRAME and service <= FRAME))
    return checks


def replay_document(repo, replay, identity, run, parameters):
    summary,audit = candidate_summary(run,replay.asset),audit_hardware(replay)
    reserve=audit_audio_reserve(replay)
    result = dict(parameters,**identity,
        misses=len(summary['misses']),
        late_publications=sum(p['late_intervals'] > 0 for p in summary['publications']),
        duplicates=len(summary['duplicate_publications']),
        wrong_slots=sum(bool(p['mismatched_slot_tiles']) for p in replay.publication_checks),
        wrong_maps=sum(bool(p['mismatched_cells']) for p in replay.map_checks),
        cry_underruns=sum(p['reason']=='underrun' for p in summary['audio_stops']),
        attempts=len(replay.finish_attempts),finishes=len(replay.finish_spans),
        bound_overruns=sum(not s['within_bound'] for s in replay.finish_spans),
        finishing_vblank_crossings=sum(s['crossed_vblank'] for s in replay.finish_spans),
        audio_reserve_violations=sum(not s['ok'] for s in reserve),
        competing_transfers=len(replay.competing_transfers),
        **{k:audit[k] for k in ('gdma_outside_vblank','writes_outside_vblank',
                               'latest_gdma_end_phase','latest_write_end_phase')})
    return dict(scope='HOST_COMPLETE_STAGE_FINISH_COUNTERFACTUAL',**repo.hashes,
        host_sources={str(p.relative_to(ROOT)):sha256(p.read_bytes())
                      for p in sorted((ROOT/'tools/dex_timing').rglob('*.py'))},
        result=result,summary=summary,costs=replay.finish_costs,finish_attempts=replay.finish_attempts,
        finish_spans=replay.finish_spans,audio_reserve_checks=reserve,ledger=ledger_summary(replay,run),
        decisions=replay.decisions,hardware_audit=audit,host=run)


def run_case(job):
    species,mode,dispatch,guard,finish_guard,phase,actual,directory = job
    repo = Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    replay,identity = initial_replay(repo,species,FinishReplay,use_additional_actual=actual)
    replay.configure_finish(mode,dispatch,guard,finish_guard)
    if phase is not None:
        replay.perturb_timer_phase(phase)
    run = replay.run(full=True)
    document = replay_document(repo,replay,identity,run,dict(species=species,mode=mode,
        dispatch_t=dispatch,viewport_guard_t=guard,finish_guard_t=finish_guard,timer_delay_t=phase))
    name=f'{species}-{mode}-d{dispatch}-g{guard}-f{finish_guard}-p{phase}.json'
    Path(directory,name).write_text(json.dumps(document,indent=2)+'\n')
    return document['result']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--species',nargs='+',choices=[*ACTUAL,*PARTIAL],default=[*ACTUAL,*PARTIAL])
    parser.add_argument('--mode',nargs='+',choices=('eight','probe','budget','early-budget'),default=['budget'])
    parser.add_argument('--dispatch-t',nargs='+',type=int,default=[1024])
    parser.add_argument('--viewport-guard-t',nargs='+',type=int,default=[64])
    parser.add_argument('--finish-guard-t',nargs='+',type=int,default=[256])
    parser.add_argument('--timer-delay-t',nargs='+',type=int,default=[None])
    parser.add_argument('--jobs',type=int,default=8)
    parser.add_argument('--actual-states',action='store_true',
                        help='Use all nine actual starting fixtures; retain partial controls otherwise')
    args=parser.parse_args()
    if args.jobs < 1 or any(v < 4 or v%4 for v in [*args.dispatch_t,*args.viewport_guard_t,*args.finish_guard_t]):
        parser.error('Positive workers and M-cycle-aligned positive costs required')
    if any(p is not None and (not 64 <= p <= 12800 or p%4) for p in args.timer_delay_t):
        parser.error('Timer phase must be 64..12800 T in M-cycle multiples')
    args.output.mkdir(parents=True,exist_ok=True)
    tasks=[(s,m,d,g,f,p,args.actual_states,args.output) for s in args.species for m in args.mode
           for d in args.dispatch_t for g in args.viewport_guard_t
           for f in args.finish_guard_t for p in args.timer_delay_t]
    with ProcessPoolExecutor(args.jobs) as pool:
        results=[]
        for result in pool.map(run_case,tasks):
            results.append(result)
            print(json.dumps(result,sort_keys=True),flush=True)
    (args.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
