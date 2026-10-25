"""Host-only publication-window and upload-admission experiments.

The ROM remains immutable. A hypothetical CP-immediate operand can widen the
publication guard without changing instruction timing. All transfer, owner,
interrupt, and audio instructions still execute in the linked replay.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import math
from itertools import product
from pathlib import Path

from .assets import Repository, sha256, offset
from .cpu import ModelError
from .costs import machine, run_to
from .fixtures import unpack
from .model import FRAME, LINE
from .probes.compare_save_state import replay_from_export
from .scheduler_experiment import (ROOT, ExperimentReplay, candidate_summary,
                                   ledger_summary, ready_prefix, VALID, READY,
                                   PENDING, PUBLISHED, ENDED)


def upload_prefix_costs(repo):
    """Linked CPU-only gather/wrapper costs through actual HDMA-helper entry.

    Enumerate both slots and both ways to terminate a short ready prefix.
    128 T covers the caller branch/CALL and trace counter-carry variation.
    This is not an estimate of the HDMA transfer or map queue itself.
    """
    result = {}
    for count in range(1,21):
        maximum = 0
        for slot in (0,1):
            for end_stage in (False,True):
                cpu = machine(repo)
                cpu.field('wPokedexAnimFlags',7)
                cpu.field('wPokedexAnimStageSlot',slot)
                cpu.field('wPokedexAnimStageTileCount',count if end_stage else 49)
                cpu.field('wPokedexAnimDictionaryTileCount',255)
                cpu.field('wPokedexAnimDictionaryTilesRemaining',255-count)
                source = repo.symbols['wPokedexWRAM0Scratch'][1]+0x460
                cpu.block(source,bytes(range(49)))
                cpu.allowed_io.add(0xff40)
                cpu.ram[0xff40] = 0x80
                run_to(cpu,'Pokedex_ServiceAnimationUploadChunk','HDMATransfer_Exact_NoDI_Arbitrary')
                if cpu.r[1] != count:
                    raise ModelError('Upload prefix fixture produced wrong count')
                maximum = max(maximum,cpu.cycles)
        result[count] = maximum+128
    return result


def visible_prefix_bound(cpu_t):
    """Fixed-point envelope ONLY while no VBlank is crossed.

    Includes one potentially pending timer/STAT IRQ and pessimistic periodic
    arrivals. 1,480 T is the current linked normal-pitch timer upper branch;
    108 T is the short STAT handler. No VBlank is hidden inside this bound.
    """
    if cpu_t <= 0 or cpu_t % 4:
        raise ModelError('Prefix cost must be a positive M-cycle multiple')
    elapsed = cpu_t
    for _ in range(100):
        new = cpu_t+(1+math.ceil(elapsed/12800))*1480+(1+math.ceil(elapsed/LINE))*108
        if new == elapsed:
            return new
        elapsed = new
    raise ModelError('Upload prefix response bound did not converge')


def viewport_write_block(repo):
    """Locate all four linked scroll/window copies as one checked block."""
    pattern = b''.join(bytes((0xf0, repo.symbols[name][1] & 255, 0xe0, hardware))
                       for name,hardware in (('hSCX',0x43),('hSCY',0x42),
                                             ('hWY',0x4a),('hWX',0x4b)))
    start = repo.symbols['VBlank_Normal'][1]
    code = repo.rom[start:start+96]
    if code.count(pattern) != 1:
        raise ModelError('Normal VBlank viewport writes moved; re-audit the probe')
    start += code.index(pattern)
    return start, start+len(pattern)


def publication_budget(repo, hold_viewport=False, viewport_guard_t=64):
    """Enumerate short branch/carry variants with all other transfers idle.

    IME is already off in VBlank. Count the linked path plus both GDMA stalls,
    through the final critical register write / conservative OAM completion.
    This bounds this quiet transaction, not arbitrary VBlank requests.
    """
    if viewport_guard_t < 4 or viewport_guard_t % 4:
        raise ModelError('Viewport guard cost must be a positive M-cycle multiple')
    viewport_start,viewport_end = viewport_write_block(repo)
    rows = []
    for oam, frame, published, late, carry, max_late in product(
            (0,1),(0,1),(0,1,255),(0,1,127),(0,255),(0,255)):
        cpu = machine(repo)
        cpu.allowed_io.update((0xff00,0xff04,0xff40,0xff42,0xff43,0xff46,
                               0xff4a,0xff4b,*range(0xff51,0xff56)))
        cpu.io_read_values[0xff00] = 15
        cpu.ram[0xff44] = 144
        for name,value in (('hSampledCryTimer',1),('wGameTimerPaused',1),
                ('wPokedexSelectedState',1),('hVBlank',7),('wPokedexAnimFlags',0x23),
                ('wPokedexAnimDeadline',(1-late)&255),('hOAMUpdate',oam),
                ('wPokedexAnimStageFrameID',frame),('wPokedexAnimDebugMapPublishes',published),
                ('wPokedexAnimDebugTotalLate',carry),('wPokedexAnimDebugMaxLate',max_late)):
            cpu.field(name,value)
        begin,end = (offset(repo.symbols[n]) for n in ('OAMDMACode','OAMDMACode.End'))
        cpu.block(repo.symbols['hTransferShadowOAM'][1],repo.rom[begin:end])
        # Locate the checked CP immediate exactly as in the linked guard.
        bank,pending = repo.symbols['Pokedex_VBlankAnimationFrontpicMap.pending']
        raw = repo.rom[offset((bank,pending)):offset((bank,pending))+32]
        guard = pending+raw.index(bytes((0xf0,0x44,0xfe,146,0xd2)))+2
        cpu.symbols = dict(cpu.symbols,__publication_guard=(bank,guard))
        run_to(cpu,'VBlank','__publication_guard')
        origin, dma_t, critical = cpu.cycles,0,0
        if hold_viewport:
            # Accepted CP 144 / JR C, before the existing upper comparison.
            cpu.cycles += 16
        cpu.record_writes = True
        while cpu.pc != repo.symbols['VBlank_Normal.done_oam'][1]:
            if hold_viewport and cpu.pc == viewport_start:
                cpu.pc = viewport_end
                cpu.cycles += viewport_guard_t
                continue
            before, index = cpu.cycles,len(cpu.writes)
            cpu.step()
            for _,address,value in cpu.writes[index:]:
                if address == 0xff55:
                    if value & 128:
                        raise ModelError('Unexpected HDMA in publication fixture')
                    dma_t += (value+1)*32+4
                    critical = max(critical,cpu.cycles-origin+dma_t)
                elif address in (0xff42,0xff43,0xff4a,0xff4b,0xff46):
                    # All these linked stores are LDH [imm8],A.
                    critical = max(critical,before-origin+dma_t+8+(648 if address==0xff46 else 4))
        rows.append(dict(quiet_oam=bool(oam),frame=frame,published=published,late=late,
                         carry=carry,max_late=max_late,critical_from_cp_t=critical,
                         done_oam_from_cp_t=cpu.cycles-origin+dma_t,
                         cp_from_irq_entry_t=origin+32))
    return {'scope':'No queued palette/BG/tile work; short linked branch/carry variants',
        'hold_viewport':hold_viewport,'viewport_guard_t':viewport_guard_t if hold_viewport else 0,
        'rows':rows,'maxima':{f'{q}:{l}':max(r['critical_from_cp_t'] for r in rows
            if r['quiet_oam']==q and bool(r['late'])==l) for q in (False,True) for l in (False,True)}}


class BudgetReplay(ExperimentReplay):
    def configure_budget(self, cutoff=146, policy='tail', dispatch_t=1024,
                         quiet_oam=False, admission=False):
        self.configure(policy, dispatch_t)
        if not 146 <= cutoff <= 150:
            raise ModelError('Publication cutoff outside this investigation')
        self.cutoff = cutoff
        bank, pending = self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.pending']
        # Pin the full LY check, not a guessed address in a potentially new ROM.
        pattern = bytes((0xf0, 0x44, 0xfe, 146, 0xd2))
        code = self.repo.rom[bank*0x4000+pending-0x4000:bank*0x4000+pending-0x4000+32]
        if code.count(pattern) != 1:
            raise ModelError('Publication LY guard changed; re-audit the probe')
        self.cutoff_pc = (bank, pending+code.index(pattern)+2)
        self.hardware_writes, self.gdma_spans, self.publication_entries = [], [], []
        self.guard_reads, self.map_checks, self.competing_transfers = [], [], []
        self.quiet_oam, self.admission = quiet_oam, admission
        self.oam_locked = False
        base = self.repo.symbols['wShadowOAM'][1]
        self.initial_shadow = bytes(self.cpu.ram[base:base+160])
        if quiet_oam and (any(self.initial_shadow) or self.initial_shadow != bytes(self.cpu.ram[0xfe00:0xfea0])):
            raise ModelError('Quiet-OAM control requires already-published empty OAM')
        self.upload_prefix_bounds = {n:visible_prefix_bound(t+124+LINE+128)
            for n,t in upload_prefix_costs(self.repo).items()} if admission else {}
        self.native_step = self.cpu.step
        self.cpu.step = self.observe_cpu_step

    def observe_cpu_step(self):
        # This boundary is after any queued GDMA/HDMA stalls in OwnerReplay.
        # Measuring in the outer step wrapper would timestamp writes too early
        # whenever a pending DMA block runs before the native instruction.
        cpu = self.cpu
        op = cpu.read(cpu.pc)
        address, bus_offset = None, 0
        if op == 0xe0:
            address, bus_offset = 0xff00+cpu.read(cpu.pc+1), 8
        elif op == 0xe2:
            address, bus_offset = 0xff00+cpu.r[1], 4
        elif op == 0xea:
            address, bus_offset = cpu.read(cpu.pc+1) | cpu.read(cpu.pc+2)<<8, 12
        if address in (0xff40,0xff42,0xff43,0xff46,0xff4a,0xff4b,
                       0xff68,0xff69,0xff6a,0xff6b):
            self.hardware_writes.append(dict(t=self.clock.t+bus_offset,address=address,
                value=cpu.r[7],pc=cpu.pc,bank=cpu.bank if cpu.pc >= 0x4000 else 0,
                interrupt=bool(self.in_interrupt or self.masked)))
        return self.native_step()

    def choose_action(self,state):
        action, reason = super().choose_action(state)
        if not self.admission or action != 0xc0:
            return action, reason
        source = self.repo.symbols['wPokedexWRAM0Scratch'][1]+0x460
        count = ready_prefix(self.cpu.ram[source:source+49],state['uploaded'],state['needed'],state['loaded'])
        # The envelope includes helper setup/poll slack as well as gather.
        # Both endpoints must stay visible; otherwise it makes no fit claim.
        current_line = self.clock.physical_line
        predicted = self.clock.t+self.upload_prefix_bounds[count]
        predicted_line = (144+predicted//LINE) % 154
        fits = (current_line < 144 and self.clock.t//FRAME == predicted//FRAME and
                predicted_line < 128-count)
        state['prefix_bound_t'] = self.upload_prefix_bounds[count]
        state['prefix_window_fits'] = fits
        if not fits and state['loaded'] < state['target'] and state['remaining_dictionary']:
            return 0x40, 'decode_instead_of_poor_upload_window'
        return action, 'upload_prefix_window_fits' if fits else 'upload_required_no_decode_alternative'

    def observe(self):
        super().observe()
        if not self.full or not hasattr(self, 'cutoff'):
            return
        cpu = self.cpu
        key = (cpu.bank if cpu.pc >= 0x4000 else 0, cpu.pc)
        if self.quiet_oam and self.oam_locked and key == self.repo.symbols['Pokedex.main']:
            base = self.repo.symbols['wShadowOAM'][1]
            if bytes(cpu.ram[base:base+160]) != self.initial_shadow or not self.field_value('hOAMUpdate'):
                raise ModelError('Quiet-OAM lifetime was violated; do not hide a needed transfer')
        if key == self.repo.symbols['VBlank_Normal']:
            competing = {name:self.field_value(name) for name in (
                'hBGMapUpdate','hCGBPalUpdate','hDMATransfer','hBGMapMode',
                'wRequested1bppSize','wRequested2bppSize','hMapAnims')}
            if any(competing.values()):
                self.competing_transfers.append(dict(self.state(), requests=competing))
        if key == self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.deadline_reached']:
            self.publication_entries.append(self.state())
        if key == self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.display_recorded']:
            frame,slot = self.state()['frame'],self.state()['slot']
            tiles = [x*7+y for y in range(7) for x in range(7)]
            attributes = [1]*49
            tail = 0
            if frame:
                for pos,source in self.asset.plans[frame].pairs:
                    if pos & 128:
                        tiles[pos & 127] = source
                    else:
                        tiles[pos] = (0x80 if slot==0 else 0x33)+tail
                        attributes[pos] = 9
                        tail += 1
            actual = [cpu.vram[bank][0x1821+y*32+x] for bank in (0,1)
                      for y in range(7) for x in range(7)]
            self.map_checks.append(dict(self.state(), mismatched_cells=[
                i for i,(got,want) in enumerate(zip(actual,tiles+attributes)) if got != want]))

    def step(self, kind='mainline'):
        if not hasattr(self, 'cutoff'):
            return super().step(kind)
        cpu = self.cpu
        key = (cpu.bank if cpu.pc >= 0x4000 else 0, cpu.pc)
        if self.quiet_oam and not self.oam_locked:
            if key != self.repo.symbols['Pokedex_VBlankAnimationFrontpicMap.deadline_reached'] or not self.masked:
                raise ModelError('Quiet-OAM experiment must begin at masked first publication')
            # Hypothetical PUSH AF / LD A,1 / LDH [hOAMUpdate],A / POP AF.
            # Existing suppression flag, not a magic skipped DMA or new byte.
            self.oam_locked = True
            cpu.field('hOAMUpdate',1)
            cpu.cycles += 48
            self.clock.work(48,'policy_oam_lock',masked=True)
            return
        if key == self.cutoff_pc:
            # Execute exactly CP imm8's ALU, length and cost. Only the operand is
            # hypothetical; never patch repository or emulator ROM bytes.
            self.guard_reads.append(dict(self.state(), sampled_ly=cpu.r[7]))
            if self.cutoff != 146:
                cpu.alu(7, self.cutoff)
                cpu.pc += 2
                cpu.steps += 1
                cpu.cycles += 8
                cpu.opcodes['fe'] += 1
                self.clock.work(8, kind, masked=True)
                self.clock._collect()
                return
        if self.gdma_due:
            source, destination, size = self.gdma_transfer
            self.gdma_spans.append(dict(start_t=self.clock.t, end_t=self.clock.t+self.gdma_due,
                source=source, destination=destination, size=size,
                vram_bank=cpu.ram[0xff4f] & 1, event=self.state()['event']))
        return super().step(kind)


def within_vblank(start, end):
    """A complete positive interval inside one physical VBlank."""
    origin = start//FRAME*FRAME
    return origin <= start < end <= origin+10*LINE


def audit_hardware(replay):
    """Conservative all-VBlank requirement, not a rendered-pixel assertion."""
    transfers, writes = [], []
    for span in replay.gdma_spans:
        # Both ends must be in the same physical VBlank, not LY=0 at line 153.
        end = span['end_t']
        start = span['start_t']
        safe = within_vblank(start,end)
        transfers.append(dict(span, end_phase=end % FRAME, inside_vblank=safe))
    for write in replay.hardware_writes:
        if not write['interrupt']:
            continue
        # OAM DMA needs 160 M-cycles plus a conservative 8-T startup allowance.
        end = write['t']+(648 if write['address'] == 0xff46 else 4)
        safe = within_vblank(write['t'],end)
        writes.append(dict(write, end_t=end, end_phase=end % FRAME, inside_vblank=safe))
    return {'scope':'Conservative completion before physical line 0; OAM includes 648-T allowance',
        'gdma':transfers, 'interrupt_hardware_writes':writes,
        'gdma_outside_vblank':sum(not x['inside_vblank'] for x in transfers),
        'writes_outside_vblank':sum(not x['inside_vblank'] for x in writes),
        'latest_gdma_end_phase':max((x['end_phase'] for x in transfers),default=0),
        'latest_write_end_phase':max((x['end_phase'] for x in writes),default=0)}


def run_case(job):
    species, cutoff, policy, dispatch, delay, quiet, admission, directory = job
    repo = Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym')
    fixture = ROOT/f'tools/dex_timing/fixtures/{species}_initial_volatile.json'
    payload, points = unpack(json.loads(fixture.read_text()),repo)
    replay = replay_from_export(repo,payload,points,species,BudgetReplay)
    replay.configure_budget(cutoff,policy,dispatch,quiet,admission)
    if delay is not None:
        replay.perturb_timer_phase(delay)
    run = replay.run(full=True)
    summary = candidate_summary(run,replay.asset)
    audit = audit_hardware(replay)
    doc = {'scope':'HOST_BUDGET_COUNTERFACTUAL', **repo.hashes,
        'input_sha256':sha256(payload), 'fixture_sha256':sha256(fixture.read_bytes()),
        'host_sources':{str(p.relative_to(ROOT)):sha256(p.read_bytes())
                        for p in sorted((ROOT/'tools/dex_timing').rglob('*.py'))},
        'species':species,'cutoff':cutoff,'policy':policy,'dispatch_t':dispatch,'timer_delay_t':delay,
        'quiet_oam':quiet,'admission':admission,'prefix_bounds':replay.upload_prefix_bounds,
        'initial_state_scope':'ACTUAL' if delay is None else 'SYNTHETIC_TIMER_PHASE_PERTURBATION',
        'summary':summary,'hardware_audit':audit,'publication_entries':replay.publication_entries,
        'guard_reads':replay.guard_reads,'competing_transfers':replay.competing_transfers,
        'ledger':ledger_summary(replay,run),
        'decisions':replay.decisions,'publication_checks':replay.publication_checks,
        'map_checks':replay.map_checks,'irq_ledger':replay.irq_ledger,'host':run}
    suffix = ('-quiet' if quiet else '')+('-admit' if admission else '')+('' if delay is None else f'-phase-{delay}')
    Path(directory,f'{species}-{policy}-ly{cutoff}-{dispatch}{suffix}.json').write_text(json.dumps(doc,indent=2)+'\n')
    return {'species':species,'cutoff':cutoff,'policy':policy,'dispatch_t':dispatch,'timer_delay_t':delay,
        'quiet_oam':quiet,'admission':admission,
        'misses':len(summary['misses']),
        'late_publications':sum(p['late_intervals'] > 0 for p in summary['publications']),
        'duplicates':len(summary['duplicate_publications']),
        'wrong_slot_bytes':sum(bool(p['mismatched_slot_tiles']) for p in replay.publication_checks),
        'wrong_maps':sum(bool(p['mismatched_cells']) for p in replay.map_checks),
        'competing_transfers':len(replay.competing_transfers),
        'cry_underruns':sum(p['reason']=='underrun' for p in summary['audio_stops']),
        **{k:audit[k] for k in ('gdma_outside_vblank','writes_outside_vblank',
                               'latest_gdma_end_phase','latest_write_end_phase')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--species',nargs='+',choices=('weavile','luxray','dusknoir'),
                        default=['weavile','luxray','dusknoir'])
    parser.add_argument('--cutoff',nargs='+',type=int,choices=range(146,151),default=[146,147,148,149])
    parser.add_argument('--policy',choices=('baseline','tail'),default='tail')
    parser.add_argument('--dispatch-t',nargs='+',type=int,default=[1024])
    parser.add_argument('--timer-delay-t',nargs='+',type=int,default=[None])
    parser.add_argument('--jobs',type=int,default=6)
    parser.add_argument('--quiet-oam',action='store_true')
    parser.add_argument('--admission',action='store_true')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('Positive workers required')
    if any(t < 4 or t % 4 for t in args.dispatch_t):
        parser.error('Dispatch costs must be positive M-cycle multiples')
    if any(t is not None and (not 64 <= t <= 12800 or t % 4) for t in args.timer_delay_t):
        parser.error('Timer delays must be 64..12800 T in M-cycle multiples')
    args.output.mkdir(parents=True,exist_ok=True)
    tasks = [(s,c,args.policy,d,t,args.quiet_oam,args.admission,args.output) for s in args.species
             for c in args.cutoff for d in args.dispatch_t for t in args.timer_delay_t]
    with ProcessPoolExecutor(args.jobs) as pool:
        results = []
        for result in pool.map(run_case,tasks):
            results.append(result)
            print(json.dumps(result,sort_keys=True),flush=True)
    (args.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
