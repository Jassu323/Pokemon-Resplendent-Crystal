"""Independent exhaustive RGB oracle for the linked capture fade."""
import argparse
import json
from pathlib import Path

from .assets import Repository
from .cpu import CounterCPU


def test(root):
    repo=Repository(root,root/'pokecrystal.gbc',root/'pokecrystal.sym')
    cases=0
    maximum=0
    guards=0
    publications=0
    class FrameWaitCPU(CounterCPU):
        def step(self):
            if self.pc==self.symbols['DelayFrame'][1]:
                self.r[7]=0
                self.f=self.Z
                self.pc=self.pop()
                self.cycles+=100
                self.steps+=1
                return
            super().step()
    for battle_type,speed in ((3,0),(3,128),(0,128)):
        for pattern in ((0x1234,0xabcd,0x9876),(0,0xffff,0x5555)):
            cpu=CounterCPU(repo.rom,repo.symbols)
            cpu.field('wBattleType',battle_type)
            cpu.allowed_io.add(0xff4d)
            cpu.ram[0xff4d]=speed
            for n,value in enumerate(pattern): cpu.set_pair(n,value)
            cpu.run('BattleSpeed_CaptureHandoff')
            assert [cpu.pair(n) for n in range(3)]==list(pattern)
            assert cpu.sp==0xc0f0 and cpu.ram[0xff4d]==speed
            assert cpu.read(repo.symbols['hCGBPalUpdate'][1])==0
            guards+=1
    for strength in (0,8,16,31):
        for incoming in range(1,8):
            for mappings in ((228,228,228),(0,228,27),(144,64,228),(27,0,255)):
                cpu=FrameWaitCPU(repo.rom,repo.symbols)
                colors=[n*521%32768 for n in range(64)]
                source=b''.join(n.to_bytes(2,'little') for n in colors)
                cpu.field('wBGPals1',int.from_bytes(source,'little'),128)
                cpu.ram[0xff70]=incoming
                for at,value in zip((0xff47,0xff48,0xff49),mappings):
                    cpu.allowed_io.add(at)
                    cpu.ram[at]=value
                cpu.r[7]=strength
                cpu.record_writes=True
                cpu.run('BattleSpeed_CaptureHandoff.FadeStep')
                expected=[]
                for pal in range(16):
                    mapping=mappings[0 if pal<8 else 1 if pal==8 else 2]
                    for color in range(4):
                        value=colors[pal*4+((mapping>>(2*color))&3)]
                        value=sum(min(31,((value>>shift)&31)+strength)<<shift for shift in (0,5,10))
                        expected.append(value)
                bank,at=repo.symbols['wBGPals2']
                assert cpu.wram[bank][at-0xd000:at-0xd000+128]==b''.join(n.to_bytes(2,'little') for n in expected)
                assert cpu.wram[bank][:128]==source
                dirty=repo.symbols['hCGBPalUpdate'][1]
                dirty_writes=[(t,v) for t,a,v in cpu.writes if a==dirty]
                palette_writes=[t for t,a,v in cpu.writes if at<=a<at+128]
                assert [v for _,v in dirty_writes]==[0,1]
                assert dirty_writes[0][0]<min(palette_writes)<=max(palette_writes)<dirty_writes[1][0]
                assert cpu.ram[0xff70]==incoming and cpu.sp==0xc0f0
                assert tuple(cpu.ram[a] for a in (0xff47,0xff48,0xff49))==mappings
                publications+=1
    for strength in (0,8,16,31):
        for start in range(0,32768,64):
            cpu=CounterCPU(repo.rom,repo.symbols)
            data=b''.join(n.to_bytes(2,'little') for n in range(start,start+64))
            cpu.field('wBGPals2',int.from_bytes(data,'little'),128)
            bank,at=repo.symbols['wBGPals2']
            cpu.wram[bank][at-0xd000-8:at-0xd000]=bytes((0x5a,))*8
            cpu.wram[bank][at-0xd000+128:at-0xd000+136]=bytes((0xa5,))*8
            incoming=(start//64)%7+1
            cpu.ram[0xff70]=incoming
            cpu.r[3]=strength
            cycles=cpu.run('BattleSpeed_CaptureHandoff.blend_palettes')
            maximum=max(maximum,cycles)
            bank,at=repo.symbols['wBGPals2']
            actual=cpu.wram[bank][at-0xd000:at-0xd000+128]
            expected=b''.join(sum(min(31,((n>>shift)&31)+strength)<<shift
                                 for shift in (0,5,10)).to_bytes(2,'little')
                              for n in range(start,start+64))
            assert actual==expected,(strength,start)
            assert cpu.ram[0xff70]==incoming
            assert cpu.sp==0xc0f0
            assert cpu.read(repo.symbols['hCGBPalUpdate'][1])==1
            assert cpu.wram[bank][at-0xd000-8:at-0xd000]==bytes((0x5a,))*8
            assert cpu.wram[bank][at-0xd000+128:at-0xd000+136]==bytes((0xa5,))*8
            cases+=64
    record=dict(rgb_color_strength_checks=cases,all_colors=32768,strengths=[0,8,16,31],
        no_op_guard_checks=guards,adjacent_palette_bytes_unchanged=True,
        mapped_palette_publication_checks=publications,
        dirty_flag_queued_only_after_complete_palette=True,
        frame_wait_clobbers_brightness_negative_control=True,
        wram_bank_restored=True,stack_restored=True,maximum_blend_cpu_t=maximum,
        maximum_blend_normal_ms=maximum*1000/4194304,
        maximum_blend_normal_frames=maximum/70224,
        limitations='CPU-only oracle; native runs separately qualify publication and interrupts')
    print(json.dumps(record,indent=2))
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    args.report.write_text(json.dumps(test(args.root.resolve()),indent=2)+'\n')
