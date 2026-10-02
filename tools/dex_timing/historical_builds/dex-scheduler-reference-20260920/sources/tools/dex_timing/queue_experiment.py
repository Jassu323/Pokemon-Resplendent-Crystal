"""HOST-ONLY queue-copy experiment; no game source, ROM file or save is written.

Execute two proposed seven-byte unrolled row helpers in a private memory image.
Keep both backing maps, both owner buffers, bank restoration, publication flags,
all diagnostic work and the previously costed scheduling policy unchanged.
This is an executable instruction prototype, not a discount applied to time.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import json
from pathlib import Path

from .assets import Repository, offset, sha256
from .costs import machine
from .cpu import ModelError
from .finish_experiment import FinishReplay, finishing_costs, replay_document
from .full_replay import ACTUAL, PARTIAL
from .recovery_experiment import initial_replay
from .scheduler_experiment import ROOT


PACKED = 'Pokedex_CopyPackedFrontpicMapToBacking'
STRIDED = 'Pokedex_StageCurrentFrontpicOwnerMaps.CopyMap'
PINNED_ROM = '7f4f64cbaeaa958aef31fa3700a75ff1188cc0047fbb732dfb495a1672921c4f'
ORIGINAL = {
    PACKED: bytes.fromhex('06 07 0e 07 2a 12 13 0d 20 fa 7b c6 0d 5f 30 01 14 05 20 ee c9'),
    STRIDED: bytes.fromhex('06 07 0e 07 2a 12 13 0d 20 fa c5 01 0d 00 09 c1 7b c6 19 5f 30 01 14 05 20 e8 c9'),
}


def row_helper(strided):
    # LD B,7 / LD C,0. C still exits zero, as in the original counted loop.
    code = bytearray((0x06,7,0x0e,0))
    row = len(code)
    code.extend(bytes((0x2a,0x12,0x13))*7)  # LD A,[HLI] / LD [DE],A / INC DE
    if strided:
        code.extend((0xc5,0x01,13,0,0x09,0xc1))  # PUSH BC / LD BC,13 / ADD HL,BC / POP BC
    code.extend((0x7b,0xc6,25 if strided else 13,0x5f,0x30,1,0x14,0x05))
    # LD A,E / ADD stride / LD E,A / JR NC,+1 / INC D / DEC B / JR NZ,row / RET
    displacement = row-(len(code)+2)
    if not -128 <= displacement < 128:
        raise ModelError('Unrolled row branch is out of range')
    code.extend((0x20,displacement & 255,0xc9))
    return bytes(code)


@dataclass(frozen=True)
class QueuePrototype:
    image: bytes
    entries: dict
    manifest: dict


def queue_prototype(repo):
    """Relocate only in verified padding of a private, captured-ROM copy.

    The padding is zero-filled in this pinned link. A future production link
    would replace the old bodies (+30 bytes net), not retain these relocations.
    Nothing here writes an alternate cartridge image to disk.
    """
    if sha256(repo.rom) != PINNED_ROM:
        raise ModelError('Queue prototype requires the pinned captured ROM')
    image = bytearray(repo.rom)
    bank,address = 0x77,0x7c00
    entries,helpers,calls = {},[],[]
    callers = {
        PACKED: ('Pokedex_StageAnimationFrontpicMap','Pokedex_CommitCurrentFrontpicMap'),
        STRIDED: ('Pokedex_StageCurrentFrontpicOwnerMaps',STRIDED),
    }
    for name in (PACKED,STRIDED):
        original = ORIGINAL[name]
        old_bank,old_address = repo.symbols[name]
        start = offset((old_bank,old_address))
        if old_bank != bank or repo.rom[start:start+len(original)] != original:
            raise ModelError('Queue helper contract changed')
        replacement = row_helper(name==STRIDED)
        target = offset((bank,address))
        if address+len(replacement) > 0x8000 or any(image[target:target+len(replacement)]):
            raise ModelError('Queue prototype padding is not empty')
        entries[name] = bank,address
        image[target:target+len(replacement)] = replacement
        lo,hi = (offset(repo.symbols[n]) for n in callers[name])
        call = bytes((0xcd,old_address & 255,old_address >> 8))
        positions = [p for p in range(lo,hi-2) if repo.rom[p:p+3] == call]
        if len(positions) != 2:
            raise ModelError('Expected exactly two queue helper call sites')
        for p in positions:
            image[p+1:p+3] = address.to_bytes(2,'little')
            calls.append(dict(bank=bank,address=p-bank*0x4000+0x4000,
                              old_target=old_address,new_target=address))
        helpers.append(dict(name=name,bank=bank,old_address=old_address,new_address=address,
            original_bytes=original.hex(),replacement_bytes=replacement.hex(),
            old_size=len(original),new_size=len(replacement)))
        address += len(replacement)
    image = bytes(image)
    manifest = dict(scope='HOST_PRIVATE_INSTRUCTION_IMAGE_NOT_A_GAME_BUILD',
        base_rom_sha256=sha256(repo.rom),private_image_sha256=sha256(image),
        helpers=helpers,calls=calls,private_padding_bytes=sum(h['new_size'] for h in helpers),
        eventual_replacement_romx_delta=sum(h['new_size']-h['old_size'] for h in helpers),
        rom0_delta=0,wram0_delta=0,wramx_delta=0,hram_delta=0)
    return QueuePrototype(image,entries,manifest)


def queue_profile(repo, prototype=None):
    """Worst linked ready-queue fixture, including all four copy calls."""
    cpu=machine(repo)
    if prototype:
        cpu.rom=prototype.image
    for name,value in (('wPokedexAnimFlags',15),('wPokedexAnimPlaybackState',2),
            ('wPokedexAnimStageFrameID',1),('wPokedexAnimStageSlot',1),
            ('wPokedexAnimDebugMapPublishes',1),('wPokedexAnimDebugMinReadyLead',255)):
        cpu.field(name,value)
    cpu.field('wPokedexAnimTraceHead',4)
    entries=prototype.entries if prototype else {n:repo.symbols[n] for n in ORIGINAL}
    names={value:key for key,value in entries.items()}
    bank,cpu.pc=repo.symbols['Pokedex_CommitDescriptionAnimation']
    cpu.bank=bank
    cpu.field('hROMBank',bank)
    cpu.push(0xffff)
    spans=[]
    opened=None
    while cpu.pc != 0xffff:
        if opened and (cpu.pc,cpu.sp)==(opened['return_pc'],opened['return_sp']):
            spans.append(dict(name=opened['name'],t=cpu.cycles-opened['start']))
            opened=None
        name=names.get((cpu.bank,cpu.pc))
        if name:
            if opened:
                raise ModelError('Unexpected nested row helper')
            opened=dict(name=name,start=cpu.cycles,
                        return_pc=cpu.read(cpu.sp)|cpu.read(cpu.sp+1)<<8,return_sp=cpu.sp+2)
        if cpu.steps > 100000:
            raise ModelError('Queue profile did not return')
        cpu.step()
    if opened or len(spans)!=4:
        raise ModelError('Queue profile missed its four map copies')
    copies=sum(s['t'] for s in spans)
    return dict(total_t=cpu.cycles,row_copies_t=copies,other_queue_t=cpu.cycles-copies,helpers=spans)


class QueueReplay(FinishReplay):
    def configure_queue(self, mode='row-unrolled', dispatch_t=1024, viewport_guard_t=64,
                        finish_guard_t=256, finish_margin_t=0):
        if mode not in ('native','row-unrolled','tile-unrolled'):
            raise ModelError('Unknown queue-copy experiment')
        self.configure_finish('early-budget',dispatch_t,viewport_guard_t,finish_guard_t)
        if finish_margin_t<0 or finish_margin_t%4:
            raise ModelError('Nonnegative M-cycle-aligned finishing reserve required')
        self.finish_margin_t=finish_margin_t
        self.queue_mode=mode
        self.queue_prototype=queue_prototype(self.repo) if mode!='native' else None
        self.gather_prototype=None
        if self.queue_prototype:
            self.cpu.rom=self.queue_prototype.image
            if mode=='tile-unrolled':
                from .gather_experiment import gather_prototype
                self.gather_prototype=gather_prototype(self.repo,self.cpu.rom)
                self.cpu.rom=self.gather_prototype.image
            self.finish_costs=finishing_costs(self.repo,queue_rom=self.cpu.rom,upload_rom=self.cpu.rom)


def run_case(job):
    species,mode,dispatch,guard,finish_guard,phase,directory,*reserve=job
    margin=reserve[0] if reserve else 0
    repo=Repository(ROOT,ROOT/'pokecrystal.gbc',ROOT/'pokecrystal.sym')
    replay,identity=initial_replay(repo,species,QueueReplay,use_additional_actual=True)
    replay.configure_queue(mode,dispatch,guard,finish_guard,margin)
    if phase is not None:
        replay.perturb_timer_phase(phase)
    run=replay.run(full=True)
    parameters=dict(species=species,mode=mode,dispatch_t=dispatch,viewport_guard_t=guard,
                    finish_guard_t=finish_guard,timer_delay_t=phase,finish_margin_t=margin)
    document=replay_document(repo,replay,identity,run,parameters)
    document['scope']='HOST_QUEUE_ROW_UNROLL_COUNTERFACTUAL'
    document['queue_prototype']=None if replay.queue_prototype is None else replay.queue_prototype.manifest
    document['gather_prototype']=None if replay.gather_prototype is None else replay.gather_prototype.manifest
    if run['synth_audio'] is not None:
        from .sound_registers import summarize_synth
        document['synth_summary']=summarize_synth(run['synth_audio'])
        document['result']['synth_completed']=run['synth_audio']['completed']
    document['queue_profile']=queue_profile(repo,replay.queue_prototype)
    suffix=f'-r{margin}' if margin else ''
    name=f'{species}-{mode}-d{dispatch}-g{guard}-f{finish_guard}-p{phase}{suffix}.json'
    Path(directory,name).write_text(json.dumps(document,indent=2)+'\n')
    return document['result']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--species',nargs='+',choices=[*ACTUAL,*PARTIAL,'exeggcute'],default=[*ACTUAL,*PARTIAL])
    parser.add_argument('--mode',nargs='+',choices=('native','row-unrolled','tile-unrolled'),default=['row-unrolled'])
    parser.add_argument('--dispatch-t',nargs='+',type=int,default=[1024])
    parser.add_argument('--viewport-guard-t',nargs='+',type=int,default=[64])
    parser.add_argument('--finish-guard-t',nargs='+',type=int,default=[256])
    parser.add_argument('--finish-margin-t',nargs='+',type=int,default=[0])
    parser.add_argument('--timer-delay-t',nargs='+',type=int,default=[None])
    parser.add_argument('--jobs',type=int,default=8)
    args=parser.parse_args()
    if args.jobs < 1 or any(v < 4 or v%4 for v in [*args.dispatch_t,*args.viewport_guard_t,*args.finish_guard_t]):
        parser.error('Positive workers and positive M-cycle-aligned costs required')
    if any(v<0 or v%4 for v in args.finish_margin_t):
        parser.error('Nonnegative M-cycle-aligned finishing reserve required')
    limit=262144 if args.species==['exeggcute'] else 12800
    if any(p is not None and (not 64 <= p <= limit or p%4) for p in args.timer_delay_t):
        parser.error(f'Timer phase must be 64..{limit} T in M-cycle multiples')
    args.output.mkdir(parents=True,exist_ok=True)
    tasks=[(s,m,d,g,f,p,args.output,r) for s in args.species for m in args.mode for d in args.dispatch_t
           for g in args.viewport_guard_t for f in args.finish_guard_t for p in args.timer_delay_t
           for r in args.finish_margin_t]
    results=[]
    with ProcessPoolExecutor(args.jobs) as pool:
        for result in pool.map(run_case,tasks):
            results.append(result)
            print(json.dumps(result,sort_keys=True),flush=True)
    (args.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
