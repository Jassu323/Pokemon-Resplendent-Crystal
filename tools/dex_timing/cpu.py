"""Instruction-path counter for isolated ROM routines, NOT a Game Boy emulator.

No LCD, interrupts, timer, DMA, mapper RAM, sound or instruction prefetch is
emulated here. Hardware accesses other than explicit fixture registers fail.
The display model accounts for elapsed hardware time separately. Unsupported
instructions and runaway paths fail closed instead of acquiring a guessed cost.
Timing units are SM83 T-cycles (four per machine cycle).
"""

from collections import Counter


class ModelError(ValueError):
    pass


class CounterCPU:
    Z, N, H, C = 0x80, 0x40, 0x20, 0x10

    def __init__(self, rom, symbols):
        self.rom, self.symbols = rom, symbols
        self.r = [0] * 8  # B C D E H L (HL) A
        self.f = 0
        self.pc, self.sp, self.bank = 0, 0xC0F0, 1
        self.ram = bytearray(65536)
        self.wram = [bytearray(4096) for _ in range(8)]
        self.vram = [bytearray(8192) for _ in range(2)]
        self.ram[0xFF70] = 1
        self.ram[0xFF4F] = 0
        self.allowed_io = {0xFF70, 0xFF4F}
        self.io_read_values = {}
        self.cycles, self.steps = 0, 0
        self.opcodes = Counter()
        self.writes = []
        self.io_reads = []
        self.record_writes = False

    def pair(self, n):
        return self.sp if n == 3 else self.r[2*n] * 256 + self.r[2*n+1]

    def set_pair(self, n, v):
        v &= 0xFFFF
        if n == 3:
            self.sp = v
        else:
            self.r[2*n], self.r[2*n+1] = v >> 8, v & 255

    def read(self, a):
        a &= 0xFFFF
        if a < 0x8000:
            offset = a if a < 0x4000 else self.bank * 0x4000 + a - 0x4000
            if offset >= len(self.rom):
                raise ModelError(f"ROM bank outside image: {self.bank:02x}:{a:04x}")
            return self.rom[offset]
        if a < 0xA000:
            return self.vram[self.ram[0xFF4F] & 1][a - 0x8000]
        if 0xA000 <= a < 0xC000 or 0xE000 <= a < 0xFF00:
            raise ModelError(f"Unsupported memory read ${a:04x}")
        if 0xD000 <= a < 0xE000:
            return self.wram[(self.ram[0xFF70] & 7) or 1][a - 0xD000]
        if 0xFF00 <= a < 0xFF80 and a not in self.allowed_io:
            raise ModelError(f"Unmodeled hardware read ${a:04x}")
        value = self.io_read_values.get(a, self.ram[a])
        if self.record_writes and 0xFF00 <= a < 0xFF80:
            self.io_reads.append((self.cycles, a, value))
        return value

    def write(self, a, v):
        a, v = a & 0xFFFF, v & 255
        if self.record_writes:
            self.writes.append((self.cycles, a, v))
        if 0x2000 <= a < 0x4000:
            self.bank = v or 1
        elif a < 0x8000:
            raise ModelError(f"Unsupported mapper write ${a:04x}")
        elif a < 0xA000:
            self.vram[self.ram[0xFF4F] & 1][a - 0x8000] = v
        elif 0xD000 <= a < 0xE000:
            self.wram[(self.ram[0xFF70] & 7) or 1][a - 0xD000] = v
        elif 0xA000 <= a < 0xC000 or 0xE000 <= a < 0xFF00:
            raise ModelError(f"Unsupported memory write ${a:04x}")
        elif 0xFF00 <= a < 0xFF80 and a not in self.allowed_io:
            raise ModelError(f"Unmodeled hardware write ${a:04x}")
        else:
            self.ram[a] = v

    def field(self, name, value, size=1):
        bank, address = self.symbols[name]
        for i in range(size):
            v = (value >> (8*i)) & 255
            if 0xD000 <= address+i < 0xE000:
                self.wram[bank][address+i-0xD000] = v
            else:
                self.write(address+i, v)

    def block(self, address, data):
        for i, v in enumerate(data):
            self.write(address+i, v)

    def data(self, address, length):
        return bytes(self.read(address+i) for i in range(length))

    def get(self, n):
        return self.read(self.pair(2)) if n == 6 else self.r[n]

    def put(self, n, v):
        if n == 6:
            self.write(self.pair(2), v)
        else:
            self.r[n] = v & 255

    def byte(self):
        v = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return v

    def word(self):
        lo = self.byte()
        return lo | self.byte() << 8

    def push(self, v):
        self.sp = (self.sp - 1) & 0xFFFF
        self.write(self.sp, v >> 8)
        self.sp = (self.sp - 1) & 0xFFFF
        self.write(self.sp, v)

    def pop(self):
        lo = self.read(self.sp)
        hi = self.read((self.sp+1) & 0xFFFF)
        self.sp = (self.sp + 2) & 0xFFFF
        return lo | hi << 8

    def cond(self, n):
        return (not self.f & self.Z, bool(self.f & self.Z),
                not self.f & self.C, bool(self.f & self.C))[n]

    def alu(self, op, v):
        a, carry = self.r[7], bool(self.f & self.C)
        if op < 2:
            c = int(carry and op == 1)
            result = a + v + c
            self.f = (self.H if (a & 15)+(v & 15)+c > 15 else 0) | (self.C if result > 255 else 0)
        elif op in (2, 3, 7):
            c = int(carry and op == 3)
            result = a - v - c
            self.f = self.N | (self.H if (a & 15) < (v & 15)+c else 0) | (self.C if result < 0 else 0)
        else:
            result = (a & v, a ^ v, a | v)[op-4]
            self.f = self.H if op == 4 else 0
        if result & 255 == 0:
            self.f |= self.Z
        if op != 7:
            self.r[7] = result & 255

    def step(self):
        at, bank = self.pc, self.bank
        op = self.byte()
        self.opcodes[f"{op:02x}"] += 1
        self.steps += 1
        t = 0
        if op == 0:
            t = 4
        elif 0x40 <= op < 0x80 and op != 0x76:
            dst, src = (op >> 3) & 7, op & 7
            self.put(dst, self.get(src))
            t = 8 if 6 in (dst, src) else 4
        elif 0x80 <= op < 0xC0:
            self.alu((op >> 3) & 7, self.get(op & 7))
            t = 8 if op & 7 == 6 else 4
        elif op & 0xC7 == 0x06:
            self.put((op >> 3) & 7, self.byte())
            t = 12 if (op >> 3) & 7 == 6 else 8
        elif op & 0xC7 in (0x04, 0x05):
            n, dec = (op >> 3) & 7, op & 1
            old = self.get(n)
            v = (old + (-1 if dec else 1)) & 255
            self.f = (self.f & self.C) | (self.N if dec else 0) | (self.Z if v == 0 else 0)
            if (old & 15) == (0 if dec else 15):
                self.f |= self.H
            self.put(n, v)
            t = 12 if n == 6 else 4
        elif op & 0xCF == 0x01:
            self.set_pair(op >> 4, self.word())
            t = 12
        elif op & 0xCF in (0x03, 0x0B):
            n = op >> 4
            self.set_pair(n, self.pair(n) + (-1 if op & 8 else 1))
            t = 8
        elif op & 0xCF == 0x09:
            a, b = self.pair(2), self.pair(op >> 4)
            self.set_pair(2, a+b)
            self.f = (self.f & self.Z) | (self.H if (a & 4095)+(b & 4095) > 4095 else 0) | (self.C if a+b > 65535 else 0)
            t = 8
        elif op in (0x02, 0x12, 0x22, 0x32, 0x0A, 0x1A, 0x2A, 0x3A):
            n = min(op >> 4, 2)
            if op & 8:
                self.r[7] = self.read(self.pair(n))
            else:
                self.write(self.pair(n), self.r[7])
            if op >= 0x20:
                self.set_pair(2, self.pair(2) + (-1 if op & 0x10 else 1))
            t = 8
        elif op in (0xEA, 0xFA, 0xE0, 0xF0, 0xE2, 0xF2):
            address = self.word() if op & 15 == 10 else 0xFF00 + (self.r[1] if op & 2 else self.byte())
            if op & 0x10:
                self.r[7] = self.read(address)
            else:
                self.write(address, self.r[7])
            t = 16 if op & 15 == 10 else (8 if op & 2 else 12)
        elif op & 0xC7 == 0xC6:
            self.alu((op >> 3) & 7, self.byte())
            t = 8
        elif op in (0x18, 0x20, 0x28, 0x30, 0x38):
            rel = self.byte()
            take = op == 0x18 or self.cond((op-0x20) >> 3)
            if take:
                self.pc = (self.pc + (rel if rel < 128 else rel-256)) & 65535
            t = 12 if take else 8
        elif op in (0xC3, 0xC2, 0xCA, 0xD2, 0xDA, 0xCD, 0xC4, 0xCC, 0xD4, 0xDC):
            target = self.word()
            call = op in (0xCD, 0xC4, 0xCC, 0xD4, 0xDC)
            take = op in (0xC3, 0xCD) or self.cond((op >> 3) & 3)
            if take:
                if call:
                    self.push(self.pc)
                self.pc = target
            t = (24 if call else 16) if take else 12
        elif op in (0xF3, 0xFB):
            # Counter-only cost. OwnerReplay applies IME and delayed EI.
            t = 4
        elif op in (0xC9, 0xD9, 0xC0, 0xC8, 0xD0, 0xD8):
            unconditional = op in (0xC9, 0xD9)
            take = unconditional or self.cond((op >> 3) & 3)
            if take:
                self.pc = self.pop()
            t = 16 if unconditional else (20 if take else 8)
        elif op == 0xE9:
            self.pc = self.pair(2)
            t = 4
        elif op & 0xC7 == 0xC7:
            self.push(self.pc)
            self.pc = op & 0x38
            t = 16
        elif op & 0xCF in (0xC1, 0xC5):
            n = (op >> 4) & 3
            if op & 4:
                self.push(self.r[7] * 256 + self.f if n == 3 else self.pair(n))
                t = 16
            else:
                v = self.pop()
                if n == 3:
                    self.r[7], self.f = v >> 8, v & 0xF0
                else:
                    self.set_pair(n, v)
                t = 12
        elif op in (0x07, 0x0F, 0x17, 0x1F):
            v, carry = self.r[7], int(bool(self.f & self.C))
            right = bool(op & 8)
            bit = v & 1 if right else v >> 7
            incoming = carry if op & 16 else bit
            self.r[7] = ((v >> 1) | (incoming << 7)) if right else ((v << 1) | incoming) & 255
            self.f = self.C if bit else 0
            t = 4
        elif op == 0x2F:
            self.r[7] ^= 255
            self.f |= self.N | self.H
            t = 4
        elif op in (0x37, 0x3F):
            self.f = (self.f & self.Z) | (self.C if op == 0x37 or not self.f & self.C else 0)
            t = 4
        elif op == 0xCB:
            cb = self.byte()
            self.opcodes[f"cb{cb:02x}"] += 1
            n, group, sub = cb & 7, cb >> 6, (cb >> 3) & 7
            v = self.get(n)
            if group == 1:
                self.f = (self.f & self.C) | self.H | (0 if v & (1 << sub) else self.Z)
            elif group in (2, 3):
                self.put(n, v & ~(1 << sub) if group == 2 else v | (1 << sub))
            else:
                carry = int(bool(self.f & self.C))
                out = v & 1 if sub in (1, 3, 5, 7) else v >> 7
                if sub == 0: result = (v << 1) | out
                elif sub == 1: result = (v >> 1) | (out << 7)
                elif sub == 2: result = (v << 1) | carry
                elif sub == 3: result = (v >> 1) | (carry << 7)
                elif sub == 4: result = v << 1
                elif sub == 5: result = (v >> 1) | (v & 128)
                elif sub == 6: result, out = (v << 4) | (v >> 4), 0
                else: result = v >> 1
                self.put(n, result)
                self.f = (self.C if out else 0) | (self.Z if result & 255 == 0 else 0)
            t = (12 if group == 1 else 16) if n == 6 else 8
        else:
            raise ModelError(f"Unsupported instruction ${op:02x} at ${bank:02x}:${at:04x}")
        self.cycles += t

    def run(self, symbol, max_steps=2_000_000):
        bank, self.pc = self.symbols[symbol]
        if bank:
            self.bank = bank
        self.field("hROMBank", self.bank)
        self.push(0xFFFF)
        start, steps = self.cycles, self.steps
        while self.pc != 0xFFFF:
            if self.steps - steps >= max_steps:
                raise ModelError(f"Instruction budget exceeded in {symbol} at ${self.pc:04x}")
            self.step()
        return self.cycles - start
