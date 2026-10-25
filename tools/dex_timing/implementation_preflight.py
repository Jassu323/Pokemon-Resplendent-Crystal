"""Assemble a cost-only owner-policy draft, without linking or changing the game.

Counts selected replacement fragments and runs CPU-only decision contracts.
This is NOT an end-to-end timing certification of an integrated implementation.
Generated files live under the ignored host-analysis build directory.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

from .assets import Repository, offset, read_symbols, sha256
from .costs import machine, run_to
from .cpu import CounterCPU, ModelError
from .finish_experiment import finishing_costs
from .finish_bounds import finish_tables, verify_tables
from .gather_experiment import gather_prototype
from .queue_experiment import PINNED_ROM, queue_prototype
from .scheduler_experiment import ROOT


def measured_span(symbols, start, end):
    bank, begin = symbols[start]
    end_bank, finish = symbols[end]
    if bank != end_bank or finish < begin:
        raise ModelError(f'Invalid size boundary: {start}, {end}')
    return finish-begin


def tail_call_packing(repo):
    """Six existing CALL/RET tails in the full Dex bank, no metadata relocation."""
    entries = (
        ('Pokedex_DrawMainScreenBG.PlaceScrollbarRow', 'Pokedex_PlaceSelectedFrontpicTopLeftCorner'),
        ('Pokedex_DrawDexEntryScreenBG.Number', 'Pokedex_PlaceFrontpicTopLeftCorner'),
        ('Pokedex_LoadPointer', 'DmgToCgbObjPal0'),
        ('Pokedex_PrepareSelectedMonTiles', 'CloseSRAM'),
        ('Pokedex_PrepareSelectedMonTiles.question_mark', 'Pokedex_PrepareCurrentFootprint'),
        ('Pokedex_LoadCurrentFootprint', 'CloseSRAM'),
    )
    rows = []
    for following, callee in entries:
        bank, end = repo.symbols[following]
        target = repo.symbols[callee][1]
        at = offset((bank, end))-4
        expected = bytes((0xcd, target & 255, target >> 8, 0xc9))
        if bank != 0x10 or repo.rom[at:at+4] != expected:
            raise ModelError(f'Dex tail-call packing site changed before {following}')
        rows.append(dict(bank=bank, address=end-4, callee=callee,
                         old_hex=expected.hex(), new_hex=bytes((0xc3, target & 255, target >> 8)).hex(),
                         romx_delta=-1, raw_cpu_saving_t=24))
    return rows


def duplicate_payloads(repo, assets, kind):
    groups = {}
    for asset in assets:
        address = repo.symbols[asset.labels[kind]]
        start = offset(address)
        size = asset.sizes[kind]
        digest = sha256(repo.rom[start:start+size])
        group = groups.setdefault((size, digest), {})
        group.setdefault(address, []).append(asset.name)
    duplicates = []
    for (size, digest), locations in groups.items():
        if len(locations) > 1 and size:
            duplicates.append(dict(size=size, sha256=digest,
                recoverable_bytes=(len(locations)-1)*size,
                locations=[dict(bank=bank, address=address, forms=names)
                           for (bank, address), names in locations.items()]))
    return dict(recoverable_bytes=sum(g['recoverable_bytes'] for g in duplicates),
                groups=sorted(duplicates, key=lambda g:g['recoverable_bytes'], reverse=True))


class DraftCounter(CounterCPU):
    """Only instruction cost for DI/EI; no timed IRQs exist in these fixtures."""
    def step(self):
        op = self.read(self.pc)
        if op in (0xf3, 0xfb):
            if op == 0xf3:
                self.draft_mask_start = self.cycles
            else:
                self.draft_ei_pending = True
            self.pc += 1
            self.cycles += 4
            self.steps += 1
            self.opcodes[f'{op:02x}'] += 1
            return
        result = super().step()
        if getattr(self, 'draft_ei_pending', False):
            self.draft_mask_max = max(getattr(self, 'draft_mask_max', 0),
                                      self.cycles-self.draft_mask_start)
            self.draft_ei_pending = False
        return result


def draft_cpu(repo, symbols, image):
    cpu = machine(repo, cpu_class=DraftCounter)
    cpu.rom = image
    cpu.symbols = {**cpu.symbols, **symbols}
    cpu.allowed_io.update((0xff40, 0xff41, 0xff44, 0xff4d, 0xff06, 0xff07))
    return cpu


def test_decisions(repo, symbols, image, limits, audio):
    cases, maximum = 0, 0
    for flags in range(128):
        for already in (False, True):
            for ready in (False, True):
                for below in (False, True):
                    cpu = draft_cpu(repo, symbols, image)
                    for name, value in (
                        ('hVBlankCounter', 17),
                        ('wPokedexAnimScheduleAddress', 0),
                        ('wPokedexAnimFlags', flags),
                        ('wPokedexAnimStageTileCount', 7),
                        ('wPokedexAnimUploadOffset', 2),
                        ('wPokedexAnimDictionaryTileCount', 100),
                        ('wPokedexAnimDictionaryTilesRemaining', 20),
                        ('wPokedexAnimDictionaryTarget', 81 if below else 80),
                    ):
                        cpu.field(name, value)
                    address = repo.symbols['wPokedexAnimScheduleAddress'][1]+1
                    cpu.write(address, 17 if already else 16)
                    cpu.block(repo.symbols['wPokedexWRAM0Scratch'][1]+0x460,
                              bytes([70, 71, 79 if ready else 80, 81, 82, 83, 84]))
                    valid = (flags & 0x7c) == 4
                    expected = 0 if already else 0xc0 if valid and ready else 0x40 if below else 0
                    elapsed = cpu.run('PolicyChooseAction')
                    if cpu.r[7] != expected or cpu.read(address) != (17 if expected or already else 16):
                        raise ModelError('Draft work decision differs from readiness policy')
                    cases += 1
                    maximum = max(maximum, elapsed)

    admission_cases, admission_max, masked_max = 0, 0, 0
    for timer_class in range(3):
        for count in range(1, 21):
            for ly in (0, max(0, limits[timer_class][count-1]-1),
                       limits[timer_class][count-1], 143, 144):
                for enough in (False, True):
                    cpu = draft_cpu(repo, symbols, image)
                    cpu.r[2] = count  # D
                    cpu.ram[0xff40] = 0x80
                    cpu.ram[0xff41] = 1 if ly >= 144 else 0
                    cpu.ram[0xff44] = ly
                    cpu.ram[0xff4d] = 0
                    cpu.ram[0xff07] = (0, 4, 6)[timer_class]
                    cpu.ram[0xff06] = 56 if timer_class == 2 else 0
                    cpu.field('hSampledCryTimer', 1 if timer_class == 2 else 0)
                    cpu.field('hLCDCPointer', 0)
                    cpu.field('hVBlankCounter', 10)
                    cpu.field('wPokedexAnimDeadline', 12)
                    cpu.field('hSampledCryBlocks', 557, 2)
                    cpu.field('wSampledCryBlockPeriod', 200)
                    minimum = audio[count-1]
                    cpu.field('wSampledCryCacheCount', minimum if enough else minimum-1)
                    bank_before = cpu.ram[0xff70]
                    elapsed = cpu.run('PolicyAdmitFinish')
                    expected = (ly < limits[timer_class][count-1]
                                and (timer_class != 2 or enough))
                    if bool(cpu.f & 0x10) != expected or cpu.ram[0xff70] != bank_before:
                        raise ModelError(f'Draft admission mismatch: {timer_class}, {count}, {ly}, {enough}')
                    admission_cases += 1
                    admission_max = max(admission_max, elapsed)
                    masked_max = max(masked_max, getattr(cpu, 'draft_mask_max', 0))
    finish_prefix = 0
    for count in range(1, 21):
        cpu = draft_cpu(repo, symbols, image)
        for name, value in (
            ('hVBlank', 0x80), ('wPokedexAnimScheduleRun', 0),
            ('wPokedexAnimPlaybackState', 2), ('wPokedexAnimFlags', 7),
            ('wPokedexAnimStageSlot', 1), ('wPokedexAnimDisplaySlot', 0),
            ('wPokedexAnimStageTileCount', count), ('wPokedexAnimUploadOffset', 0),
            ('wPokedexAnimDictionaryTileCount', 127), ('wPokedexAnimDictionaryTilesRemaining', 0),
            ('hSampledCryTimer', 1), ('hLCDCPointer', 0), ('hVBlankCounter', 10),
            ('wPokedexAnimDeadline', 12), ('wSampledCryBlockPeriod', 200),
            ('wSampledCryCacheCount', 32),
        ):
            cpu.field(name, value)
        cpu.field('hSampledCryBlocks', 557, 2)
        cpu.block(repo.symbols['wPokedexWRAM0Scratch'][1]+0x460, bytes(range(49)))
        cpu.ram[0xff40] = 0x80
        cpu.ram[0xff41] = 0
        cpu.ram[0xff44] = 0
        cpu.ram[0xff4d] = 0
        cpu.ram[0xff07] = 6
        cpu.ram[0xff06] = 56
        elapsed = run_to(cpu, 'PolicyTryFinish', 'Pokedex_ServiceAnimationUploadChunk')
        if cpu.read(repo.symbols['wPokedexAnimScheduleRun'][1]) & 2 != 2:
            raise ModelError('Finishing attempt was not limited to one per owner iteration')
        finish_prefix = max(finish_prefix, elapsed)
    return dict(work_decision_cases=cases, work_decision_max_cpu_t=maximum,
                admission_cases=admission_cases, admission_max_cpu_t=admission_max,
                finishing_prefix_cases=20, finishing_prefix_max_cpu_t=finish_prefix,
                audio_snapshot_max_masked_cpu_t=masked_max,
                scope='CPU-only; hardware registers frozen; no timed IRQ injection')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'build/dex-timing-implementation-preflight')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    repo = Repository(ROOT, ROOT/'pokecrystal.gbc', ROOT/'pokecrystal.sym')
    if sha256(repo.rom) != PINNED_ROM:
        raise ModelError('Cost draft requires the calibrated link; re-audit against the new link')
    queue = queue_prototype(repo)
    gather = gather_prototype(repo, queue.image)
    costs = finishing_costs(repo, queue_rom=gather.image, upload_rom=gather.image)
    limits, audio = finish_tables(costs)
    source = ROOT/'tools/dex_timing/preflight/owner_policy.asm'
    raw = source.read_text()
    words = set(re.findall(r'[A-Za-z_][A-Za-z0-9_.]*', raw))
    references = sorted(words & repo.symbols.keys())
    definitions = [f'DEF {name} EQU ${repo.symbols[name][1]:04x}' for name in references]
    definitions.append('DEF LinkedPublicationDefer EQU $'+format(
        repo.symbols['Pokedex_VBlankAnimationFrontpicMap.defer'][1], '04x'))
    (output/'linked.inc').write_text('\n'.join(definitions)+'\n')
    table_lines = ['PolicyLatestLY::']
    table_lines += ['\tdb '+', '.join(map(str, row)) for row in limits]
    table_lines += ['PolicyAudioMinimum::', '\tdb '+', '.join(map(str, audio))]
    (output/'finish_tables.inc').write_text('\n'.join(table_lines)+'\n')
    subprocess.run(['rgbasm', '-I', str(output)+'/', '-o', str(output/'draft.o'), str(source)], check=True)
    subprocess.run(['rgblink', '-o', str(output/'cost-only.bin'), '-n', str(output/'draft.sym'),
                    '-m', str(output/'draft.map'), str(output/'draft.o')], check=True)
    symbols = read_symbols(output/'draft.sym')
    sizes = {name.removeprefix('Cost_').removesuffix('Start'):
             measured_span(symbols, name, name.removesuffix('Start')+'End')
             for name in symbols if name.startswith('Cost_') and name.endswith('Start')}
    # Install only this standalone fragment in an in-memory fixture.
    image = bytearray(repo.rom)
    draft = (output/'cost-only.bin').read_bytes()
    start = offset(symbols['Cost_ActionStart'])
    end = offset(symbols['Cost_HookCallsEnd'])
    if end > 0xa1*0x4000 or any(image[start:end]):
        raise ModelError('Draft fixture is not confined to empty analysis space')
    image[start:end] = draft[start:end]
    tests = test_decisions(repo, symbols, bytes(image), limits, audio)
    tests['table_equivalence_cases'] = verify_tables(costs, limits, audio)
    assets = repo.load()
    tests['asset_forms_checked'] = len(assets)
    tests['sorted_frame_plans_checked'] = sum(len(asset.plans)-1 for asset in assets)
    metadata = {kind: sum(asset.sizes[kind] for asset in assets)
                for kind in ('plan', 'timeline', 'schedule')}
    # Pointer tables include 373 species and 26 Unown forms; Egg has a direct pointer.
    pointers = min(repo.symbols[a.labels['timeline']][1] for a in assets)-repo.symbols['DexAnimationTimelinePointers'][1]
    metadata.update(timeline_pointers=pointers, schedule_pointers=pointers,
                    plan_pointers=pointers//2*3)
    metadata['timeline_high_water_bytes'] = sum(len(asset.events) for asset in assets)
    duplicates = {kind: duplicate_payloads(repo, assets, kind) for kind in ('plan', 'timeline')}
    old = dict(
        action_reader=measured_span(repo.symbols, 'Pokedex_GetNextAnimationScheduleAction',
                                  'Pokedex_ServiceAnimationDictionaryChunk'),
        producer_arm=measured_span(repo.symbols, 'Pokedex_ServiceAnimationProducer.scheduled',
                                 'Pokedex_ServiceAnimationProducer.record_dictionary'),
        schedule_pointer_lookup=measured_span(repo.symbols, 'GetMonDexAnimationSchedulePointer',
                                            'PokeAnim_GetDexFramePlanPointer'),
        schedule_pointer_init=15,
        schedule_bank_reader=49,
        queue_route=4,
        publish_route=3,
        publish_guard=7,
        outer_calls=6,
    )
    # These are code/data deltas, excluding instrumentation deletion and tail-call
    # packing in bank $10. Runtime hooks are represented by counted CALL fragments.
    banks = {
        '00': sizes['HomeGuard'],
        '10': sizes['OuterCalls']-old['outer_calls'],
        '34': -old['schedule_pointer_lookup']-old['schedule_pointer_init'],
        '77': queue.manifest['eventual_replacement_romx_delta'] + sizes['QueueGuard']
              + sizes['QueueRoute']-old['queue_route']
              + sizes['PublishRoute']-old['publish_route']
              + sizes['PublishGuard']-old['publish_guard'],
        'a0': sum(sizes[k] for k in ('Action', 'Pacing', 'Lifetime', 'Finish', 'Tables', 'HookCalls'))
              + sizes['ProducerArm']-old['producer_arm']-old['action_reader']
              + gather.manifest['eventual_replacement_romx_delta'],
        'a6': -metadata['schedule']-metadata['schedule_pointers']-old['schedule_bank_reader'],
    }
    packing = tail_call_packing(repo)
    packed_banks = dict(banks)
    packed_banks['10'] += sum(row['romx_delta'] for row in packing)
    report = dict(scope='ASSEMBLED_COST_ONLY_DRAFT_NOT_A_GAME_IMPLEMENTATION',
        **repo.hashes, draft_source_sha256=sha256(source.read_bytes()),
        assembler=subprocess.check_output(['rgbasm', '--version'], text=True).strip(),
        draft_part_bytes=sizes, old_part_bytes=old, per_bank_delta_before_packing=banks,
        per_bank_delta_after_packing=packed_banks, tail_call_packing=packing,
        rom0_delta=banks['00'], romx_delta_before_packing=sum(v for k,v in banks.items() if k!='00'),
        romx_delta_after_packing=sum(v for k,v in packed_banks.items() if k!='00'),
        metadata_bytes=metadata, finish_latest_ly_exclusive=limits,
        optional_identical_payload_deduplication=duplicates,
        finish_audio_minimum=audio, tests=tests,
        assumptions=['Retain current diagnostic work in all measured linked helpers.',
                     'Reuse the existing three schedule-state bytes; no added WRAM or HRAM.',
                     'Quiet-owner tag uses bit 7 of existing hVBlank; dispatch still masks low 3 bits.',
                     'Six bytes of bank-$10 packing are required before a real link.',
                     'The new owner/guard instructions have NOT replaced allowances in full replays.',
                     'Compact table values must be regenerated from the integrated linked code.'])
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if sha256((ROOT/'pokecrystal.gbc').read_bytes()) != repo.hashes['rom_sha256']:
        raise ModelError('Game ROM changed during cost-only work')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
