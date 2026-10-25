"""One-off, verified test-save edit. No ROM or production source changes."""

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from dex_timing.assets import read_symbols

SAVE = Path("/Applications/SameBoy/Games/pokecrystal.sav")
EXPECTED_ROM = "02e49d8db9186ceae4efe2634d19121398a22f0a40eaf30c7e961dd8a9acb224"
EXPECTED_INSTALLED_ROM = "407c4d29e08a47c5e5cce165eb4d171b62d4afbced665938950aa0a21b5d9fd3"
SPECIES = {"MEWTWO": 0x96, "EXEGGCUTE": 0x66, "GARCHOMP": 0x160, "VIBRAVA": 0x124}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    symbols = read_symbols(ROOT / "pokecrystal.sym")
    require(digest((ROOT / "pokecrystal.gbc").read_bytes()) == EXPECTED_ROM, "Repository ROM changed")
    require(digest(SAVE.with_suffix(".gbc").read_bytes()) == EXPECTED_INSTALLED_ROM, "Installed ROM does not match")
    require(symbols == read_symbols(ROOT / "build/new-dex-entry-catches/fixture.sym"),
            "Linked layout changed from installed fixture")

    names = re.findall(r"^\s*const\s+(\w+)", (ROOT / "constants/pokemon_constants.asm").read_text().split("DEF NUM_POKEMON")[0], re.M)
    for name, index in SPECIES.items():
        require(names[index - 1] == name, f"Species index changed: {name}")

    def ram(name):
        return symbols[name][1]

    def sram(name):
        bank, address = symbols[name]
        require(0xA000 <= address <= 0xC000, f"Not SRAM: {name}")
        return bank * 0x2000 + address - 0xA000

    move_size = ram("wMoveIndexTableEnd") - ram("wMoveIndexTable")
    records = []
    for prefix in ("s", "sBackup"):
        records.append(dict(
            prefix=prefix,
            start=sram(prefix + "SaveData"), end=sram(prefix + "SaveDataEnd"),
            checksum=sram(prefix + "Checksum"), moves=sram(prefix + "MoveIndexTable"),
            conversion=sram(prefix + "ConversionTableChecksum"),
            caught=sram(prefix + "PokemonData") + ram("wPokedexCaught") - ram("wPokemonData"),
            seen=sram(prefix + "PokemonData") + ram("wPokedexSeen") - ram("wPokemonData"),
        ))

    def verify(data):
        for record in records:
            for suffix, expected in (("CheckValue1", 0xB9), ("CheckValue2", 0x6F)):
                require(data[sram(record["prefix"] + suffix)] == expected, "Save marker is invalid")
            for begin, end, at in ((record["start"], record["end"], record["checksum"]),
                                   (record["moves"], record["moves"] + move_size, record["conversion"])):
                require(sum(data[begin:end]) & 0xFFFF == int.from_bytes(data[at:at + 2], "little"),
                        f"Checksum is invalid: {record['prefix']} at {at:#x}")

    before = SAVE.read_bytes()
    require(len(before) == 0x8000 + 48, "Unexpected SRAM/RTC file size")
    verify(before)
    after = bytearray(before)
    allowed = set()
    flags = []
    for record in records:
        for name, index in SPECIES.items():
            byte, bit = divmod(index - 1, 8)
            mask = 1 << bit
            at = record["caught"] + byte
            require(bool(before[record["seen"] + byte] & mask), f"{name} is not seen")
            after[at] &= ~mask
            allowed.add(at)
            flags.append(dict(record=record["prefix"], species=name, index=index,
                              offset=f"{at:04x}", was_caught=bool(before[at] & mask), caught=False, seen=True))
        at = record["checksum"]
        after[at:at + 2] = (sum(after[record["start"]:record["end"]]) & 0xFFFF).to_bytes(2, "little")
        allowed.update((at, at + 1))
    verify(after)
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    require(set(changed) <= allowed, "Unexpected changes outside caught flags/checksums")
    require(before[0x8000:] == after[0x8000:], "RTC trailer changed")
    for record in records:
        at = record["seen"]
        require(before[at:at + 64] == after[at:at + 64], "Seen flags changed")
        for index in range(512):
            mask, byte = 1 << (index % 8), record["caught"] + index // 8
            if index + 1 not in SPECIES.values():
                require(before[byte] & mask == after[byte] & mask, "Unrelated caught flag changed")

    report = dict(applied=False, save=str(SAVE), size=len(before), rom_sha256=EXPECTED_ROM,
                  installed_rom_sha256=EXPECTED_INSTALLED_ROM,
                  before_sha256=digest(before), after_sha256=digest(after), flags=flags,
                  changed_bytes=[dict(offset=f"{i:04x}", before=before[i], after=after[i]) for i in changed],
                  checksums_valid=True, seen_flags_unchanged=True, all_other_bytes_unchanged=True)
    if args.apply:
        require(SAVE.read_bytes() == before, "Save changed while preparing the edit")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = SAVE.with_name(f"{SAVE.stem}.before-new-dex-entry-tests-{stamp}.sav")
        with backup.open("xb") as stream:
            stream.write(before)
            stream.flush()
            os.fsync(stream.fileno())
        require(backup.read_bytes() == before, "Backup verification failed")
        fd, temp = tempfile.mkstemp(prefix=".pokecrystal-new-dex-", suffix=".sav", dir=SAVE.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(after)
                stream.flush()
                os.fsync(stream.fileno())
            shutil.copystat(SAVE, temp)
            require(SAVE.read_bytes() == before, "Save changed before replacement")
            os.replace(temp, SAVE)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        require(SAVE.read_bytes() == after, "Replacement verification failed")
        verify(SAVE.read_bytes())
        report.update(applied=True, backup=str(backup))
        (Path(__file__).parent / f"save-edit-{stamp}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
