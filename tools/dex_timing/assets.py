"""Read linked assets and independently validate their structural contracts."""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

from .cpu import ModelError


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_symbols(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]+):([0-9a-fA-F]{4}) (\S+)", line)
        if match:
            bank, address, name = match.groups()
            result[name] = int(bank, 16), int(address, 16)
    if not result:
        raise ModelError(f"No RGBDS symbols in {path}")
    return result


def offset(symbol):
    bank, address = symbol
    if bank == 0 and address < 0x4000:
        return address
    if bank and 0x4000 <= address < 0x8000:
        return bank * 0x4000 + address - 0x4000
    raise ModelError(f"Not a ROM symbol: {bank:02x}:{address:04x}")


def incbins(root, path):
    text = (root / path).read_text()
    return {m[1]: m[2] for m in re.finditer(r'^(\w+)::?\s+INCBIN\s+"([^"]+)"', text, re.M)}


@dataclass
class Stream:
    start: int
    end: int
    output: bytes
    commands: tuple


def decompress(data, start=0, output_limit=4096):
    """Independent LZ3 reference, including overlapping and reverse rewrites."""
    at, out, commands = start, bytearray(), []

    def take():
        nonlocal at
        if at >= len(data):
            raise ModelError("Truncated LZ stream")
        value = data[at]
        at += 1
        return value

    while True:
        header = take()
        if header == 255:
            return Stream(start, at, bytes(out), tuple(commands))
        command, size = header >> 5, (header & 31)+1
        if command == 7:
            command, size = (header >> 2) & 7, ((header & 3) << 8) + take() + 1
        if command > 6:
            raise ModelError("Reserved LZ command")
        if len(out) + size > output_limit:
            raise ModelError("LZ output exceeds declared dictionary/stream size")
        commands.append((command, size))
        if command == 0:
            out.extend(take() for _ in range(size))
        elif command == 1:
            out.extend([take()] * size)
        elif command == 2:
            first, second = take(), take()
            out.extend(first if i % 2 == 0 else second for i in range(size))
        elif command == 3:
            out.extend(bytes(size))
        else:
            lo = take()
            source = len(out) - (lo & 127) - 1 if lo & 128 else (lo << 8) | take()
            for i in range(size):
                pos = source + (-i if command == 6 else i)
                if not 0 <= pos < len(out):
                    raise ModelError("LZ rewrite references data outside this stream")
                value = out[pos]
                if command == 5:
                    value = int(f"{value:08b}"[::-1], 2)
                out.append(value)


@dataclass(frozen=True)
class Plan:
    high_water: int
    pairs: tuple

    @property
    def sources(self):
        return tuple(source for pos, source in self.pairs if not pos & 128)


@dataclass(frozen=True)
class Event:
    frame: int
    duration: int
    target: int


def plans(data, width, total, tilemap):
    count = len(tilemap) // (width * width) - 1
    result = [Plan(width * width, ())]
    cursor = count * 2
    for i in range(count):
        if i*2+2 > len(data) or int.from_bytes(data[i*2:i*2+2], "little") != cursor:
            raise ModelError("Non-contiguous/invalid frame-plan offsets")
        if cursor + 2 > len(data):
            raise ModelError("Truncated frame-plan header")
        n, high = data[cursor:cursor+2]
        end = cursor+2+2*n
        if end > len(data):
            raise ModelError("Truncated frame-plan pairs")
        pairs = tuple(zip(data[cursor+2:end:2], data[cursor+3:end:2]))
        positions = [p & 127 for p, _ in pairs]
        if len(set(positions)) != n or any(p >= 49 for p in positions):
            raise ModelError("Invalid/duplicate frame-plan position")
        if any(s >= (49 if p & 128 else total) for p, s in pairs):
            raise ModelError("Frame-plan source outside its dictionary")
        tail = [s for p, s in pairs if not p & 128]
        if tail != sorted(tail) or high != max([width*width] + [s+1 for s in tail]):
            raise ModelError("Invalid frame-plan high-water mark or source order")
        # Independently reconstruct the padded picture, not just its counts.
        base_ids = list(range(49))
        base_map = [x*7+y for y in range(7) for x in range(7)]
        actual = [("base", s) for s in base_map]
        for p, s in pairs:
            actual[p & 127] = ("base" if p & 128 else "tail", s)
        expected = [("base", s) for s in base_map]
        row_offset, col_offset = 7-width, 0 if width == 7 else 1
        for x in range(width):
            for y in range(width):
                source = tilemap[(i+1)*width*width+x*width+y]
                position = (y+row_offset)*7 + x+col_offset
                if source < width*width:
                    source = (source//width+col_offset)*7 + source%width+row_offset
                    expected[position] = ("base", base_ids[source])
                else:
                    expected[position] = ("tail", source)
        if actual != expected:
            raise ModelError(f"Frame plan {i+1} does not reconstruct its source tilemap")
        result.append(Plan(high, pairs))
        cursor = end
    if cursor != len(data):
        raise ModelError("Trailing frame-plan bytes")
    return result


def timeline(data, frame_count, total):
    cursor, result, offsets = 0, [], {}
    while cursor < len(data):
        offsets[cursor] = len(result)
        value = data[cursor]
        cursor += 1
        if value == 0xF0:
            if cursor != len(data):
                raise ModelError("Trailing timeline bytes")
            return result, None
        if value == 0xF1:
            if cursor+2 != len(data):
                raise ModelError("Invalid timeline loop")
            rewind = int.from_bytes(data[cursor:cursor+2], "little")
            target = cursor+2-rewind
            if target not in offsets or offsets[target] >= len(result):
                raise ModelError("Timeline loop is not a backwards event boundary")
            return result, offsets[target]
        frame, duration = value >> 4, value & 15
        if not duration:
            if cursor >= len(data):
                raise ModelError("Truncated timeline duration")
            duration = data[cursor]
            cursor += 1
        if cursor >= len(data) or not 0 < duration < 128 or frame >= frame_count:
            raise ModelError("Invalid timeline event")
        target = data[cursor]
        cursor += 1
        if target > total:
            raise ModelError("Timeline target outside dictionary")
        result.append(Event(frame, duration, target))
    raise ModelError("Unterminated timeline")


def schedule(data):
    cursor, actions, offsets = 0, [], {}
    while cursor < len(data):
        offsets[cursor] = len(actions)
        value = data[cursor]
        cursor += 1
        if value == 0:
            if cursor != len(data):
                raise ModelError("Trailing schedule bytes")
            return actions, None
        if value == 0x40:
            if cursor+2 != len(data):
                raise ModelError("Invalid schedule loop")
            target = cursor+2-int.from_bytes(data[cursor:cursor+2], "little")
            if target not in offsets or offsets[target] >= len(actions):
                raise ModelError("Schedule loop is not a backwards run boundary")
            return actions, offsets[target]
        action, count = value >> 6, value & 63
        if not count or action == 2:
            raise ModelError("Unsupported/reserved schedule action")
        actions.extend([action]*count)
    raise ModelError("Unterminated schedule")


@dataclass
class Asset:
    name: str
    stem: str
    width: int
    total: int
    streams: list
    dictionary: bytes
    plans: list
    events: list
    event_loop: object
    actions: list
    action_loop: object
    labels: dict
    sample_blocks: int
    sizes: dict


class Repository:
    def __init__(self, root, rom_path, sym_path):
        self.root = Path(root).resolve()
        self.rom = Path(rom_path).read_bytes()
        self.symbols = read_symbols(sym_path)
        self.hashes = {"rom_sha256": sha256(self.rom), "sym_sha256": sha256(Path(sym_path).read_bytes())}
        if len(self.rom) != 4*1024*1024:
            raise ModelError("Expected the current 4 MiB MBC30 image")
        self.files = {}

    def linked(self, label, path):
        if label not in self.symbols:
            raise ModelError(f"Missing linked symbol {label}")
        data = (self.root / path).read_bytes()
        pos = offset(self.symbols[label])
        address = self.symbols[label][1]
        if address+len(data) > (0x4000 if address < 0x4000 else 0x8000):
            raise ModelError(f"{label} crosses a ROM bank")
        if self.rom[pos:pos+len(data)] != data:
            raise ModelError(f"ROM/asset mismatch: {label}, {path}; rebuild this ROM")
        self.files[path] = sha256(data)
        return data

    def load(self, names=None):
        tables = {}
        for kind, path in (("plan", "gfx/pokemon/dex_animation_plans.asm"),
                           ("timeline", "gfx/pokemon/dex_animation_timelines.asm"),
                           ("schedule", "gfx/pokemon/dex_animation_schedules.asm"),
                           ("front", "gfx/pics.asm")):
            if kind == "schedule" and "DexAnimationSchedulePointers" not in self.symbols:
                continue
            tables[kind] = {str(Path(p).parent): (label, p) for label, p in incbins(self.root, path).items()
                            if kind != "front" or p.endswith("front.animated.2bpp.lz")}
        selected = set(names or [])
        assets = []
        for directory, (label, _) in sorted(tables["plan"].items()):
            name, stem = Path(directory).name, label.removesuffix("DexAnimationPlan")
            if selected and name not in selected:
                continue
            if any(directory not in t for t in tables.values()):
                raise ModelError(f"Incomplete linked animation assets: {name}")
            labels = {k: v[directory][0] for k, v in tables.items()}
            data = {k: self.linked(*v[directory]) for k, v in tables.items()}
            width = (self.root / directory / "front.dimensions").read_bytes()[0] & 15
            tilemap = (self.root / directory / "front.animated.tilemap").read_bytes()
            if width not in (5, 6, 7) or len(tilemap) < width*width or len(tilemap) % (width*width):
                raise ModelError(f"Invalid dimensions/tilemap: {name}")
            total, at, streams = data["front"][0], 1, []
            if total < width*width:
                raise ModelError(f"Dictionary smaller than base frame: {name}")
            remaining = total
            while remaining:
                tiles = width*width if not streams else min(6, remaining)
                stream = decompress(data["front"], at, tiles*16)
                if len(stream.output) != tiles*16:
                    raise ModelError(f"Wrong dictionary chunk size: {name}")
                streams.append(stream)
                at, remaining = stream.end, remaining-tiles
                if remaining < 0:
                    raise ModelError(f"Dictionary smaller than base frame: {name}")
            dictionary = b"".join(s.output for s in streams)
            if at != len(data["front"]) or dictionary != (self.root / directory / "front.animated.2bpp").read_bytes():
                raise ModelError(f"Compressed dictionary differs from generated graphics: {name}")
            frame_plans = plans(data["plan"], width, total, tilemap)
            events, event_loop = timeline(data["timeline"], len(frame_plans), total)
            actions, action_loop = schedule(data["schedule"]) if "schedule" in data else ([], None)
            if not events or any(e.target < frame_plans[e.frame].high_water for e in events):
                raise ModelError(f"Invalid timeline target: {name}")
            sample_blocks = 0
            sample = stem + "SampledCry"
            if sample in self.symbols:
                sample_offset = offset(self.symbols[sample])
                sample_blocks = int.from_bytes(self.rom[sample_offset:sample_offset+2], "little")
                end = offset(self.symbols[sample+"End"])
                if sample_offset + 2 + sample_blocks*9 != end:
                    raise ModelError(f"Invalid sampled cry size: {sample}")
                labels["sample"] = sample
            assets.append(Asset(name, stem, width, total, streams, dictionary, frame_plans,
                                events, event_loop, actions, action_loop, labels, sample_blocks,
                                {k: len(v) for k, v in data.items()}))
        missing = selected - {a.name for a in assets}
        if missing:
            raise ModelError(f"Unknown species/form: {', '.join(sorted(missing))}")
        return assets

    def manifest(self):
        sources = ["home/decompress.asm", "home/copy.asm", "home/farcall.asm", "home/gfx.asm",
                   "home/delay.asm", "home/audio.asm", "home/mobile.asm", "home/vblank.asm",
                   "home/sampled_cry_player.asm", "audio/sampled_cry_pair_lookup.asm",
                   "engine/gfx/dma_transfer.asm", "engine/gfx/pic_animation.asm",
                   "engine/pokedex/pokedex_animation.asm", "engine/pokedex/pokedex.asm",
                   "engine/pokedex/pokedex_detail.asm", "engine/pokedex/pokedex_3.asm",
                   "engine/pokedex/pokedex_animation_timeline.asm",
                   "constants/audio_constants.asm", "constants/gfx_constants.asm", "ram/wram.asm",
                   "tools/pokemon_animation.c", "tools/frontpic_lz.c"]
        sources += [p for p in ("engine/pokedex/pokedex_animation_policy.asm",
                                "engine/pokedex/pokedex_animation_schedule.asm")
                    if (self.root/p).exists()]
        return {**self.hashes, "assets": self.files,
                "sources": {p: sha256((self.root/p).read_bytes()) for p in sources}}
