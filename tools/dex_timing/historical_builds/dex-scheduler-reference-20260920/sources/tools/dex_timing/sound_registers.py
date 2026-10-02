"""CPU-visible sound controls for the captured Exeggcute path, not an APU.

SameBoy Core/apu.c GB_apu_read/write supplies the register contracts. No waveform,
envelope, length-clock or sweep simulation is claimed. Reject accesses whose
CPU-visible results require that missing state instead of inventing a result.
"""
from .assets import sha256
from .cpu import ModelError
from .model import FRAME


READ_MASK = bytes.fromhex(
    '80 3f 00 ff bf ff 3f 00 ff bf 7f ff 9f ff bf ff ff 00 00 bf '
    '00 00 70 ff ff ff ff ff ff ff ff ff')
TRIGGERS = (0xff14,0xff19,0xff1e,0xff23)
DACS = (0xff12,0xff17,0xff1a,0xff21)


def summarize_synth(audit):
    """Compare sound-engine work, not generated analogue audio samples."""
    ticks=[row['t']//FRAME for row in audit['sound_updates']]
    return dict(completed=audit['completed'],initial_flags=audit['initial_flags'],
        final_flags=audit['final_flags'],sound_updates=len(ticks),
        max_update_gap_intervals=max((b-a for a,b in zip(ticks,ticks[1:])),default=0),
        hardware_write_count=len(audit['hardware_writes']),
        hardware_sequence_sha256=sha256(bytes(v for _,address,value in audit['hardware_writes']
                                              for v in (address&255,value))),
        channel_completion_intervals=[(t//FRAME,address,value) for t,address,value in audit['channel_writes']])


class SoundRegisters:
    def __init__(self,ram):
        self.ram=ram
        self.enabled=bool(ram[0xff26]&0x80)
        self.active=ram[0xff26]&15
        if any(ram[a]&0x40 for a in TRIGGERS):
            raise ModelError('Initial APU length clocks are outside the synth control')
        self.check_sweep(ram[0xff10])

    @staticmethod
    def check_sweep(value):
        if value & 7:
            raise ModelError('APU frequency sweep requires a fuller model')

    def read(self,address):
        if address==0xff26:
            return 0x70 | (0x80 if self.enabled else 0) | self.active
        if address>=0xff30:
            if self.active & 4:
                raise ModelError('Active wave-RAM reads require sample phase')
            return self.ram[address]
        return self.ram[address] | READ_MASK[address-0xff10]

    def write(self,address,value):
        if address==0xff26:
            if bool(value&0x80)!=self.enabled:
                raise ModelError('APU power transitions are outside the synth control')
            return  # Status bits are read-only, including the low four bits.
        if address==0xff10:
            self.check_sweep(value)
        if address in DACS:
            channel=DACS.index(address)
            if not value & (0x80 if channel==2 else 0xf8):
                self.active &= ~(1<<channel)
        if address in TRIGGERS:
            if value & 0x40:
                raise ModelError('APU length clocks require a fuller model')
            channel=TRIGGERS.index(address)
            dac=self.ram[DACS[channel]] & (0x80 if channel==2 else 0xf8)
            if value & 0x80 and dac and self.enabled:
                self.active |= 1<<channel
