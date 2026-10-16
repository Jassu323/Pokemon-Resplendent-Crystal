"""Independently audit every evolution and ancestor against pinned game data.

All downloaded references and generated reports belong under build/. No ROM,
save, registration source, or generated game assets are changed by this tool.

Use --patch to audit a fresh private source copy, or --root with --rom and
--symbols to audit an already-linked candidate. --self-test exercises negative
cases; --require-complete fails if any of the 190 in-roster edges is absent.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLATINUM_REVISION = "1dc13dcea40c04ab53f1f607de46023dc409ef20"
PLATINUM_BASE = f"https://raw.githubusercontent.com/pret/pokeplatinum/{PLATINUM_REVISION}/res/pokemon"
DEFAULT_OUTPUT = ROOT / "build/evolution-audit-20261015"
EVOLUTION_FILES = tuple(f"data/pokemon/evos_attacks_{part}.asm" for part in ("kanto", "johto", "custom"))
METHOD_LENGTHS = {"EVOLVE_LEVEL": 4, "EVOLVE_ITEM": 4, "EVOLVE_TRADE": 4,
                  "EVOLVE_HAPPINESS": 4, "EVOLVE_STAT": 5}
ALIASES = {"MR__MIME": "MR_MIME", "FARFETCH_D": "FARFETCHD"}
METHOD_MAP = {
    "EVO_LEVEL": ("EVOLVE_LEVEL", None),
    "EVO_USE_ITEM": ("EVOLVE_ITEM", None),
    "EVO_TRADE": ("EVOLVE_TRADE", "-1"),
    "EVO_TRADE_WITH_HELD_ITEM": ("EVOLVE_TRADE", None),
    "EVO_LEVEL_HAPPINESS": ("EVOLVE_HAPPINESS", "TR_ANYTIME"),
    "EVO_LEVEL_HAPPINESS_DAY": ("EVOLVE_HAPPINESS", "TR_MORNDAY"),
    "EVO_LEVEL_HAPPINESS_NIGHT": ("EVOLVE_HAPPINESS", "TR_EVENITE"),
    "EVO_LEVEL_ATK_GT_DEF": ("EVOLVE_STAT", "ATK_GT_DEF"),
    "EVO_LEVEL_ATK_LT_DEF": ("EVOLVE_STAT", "ATK_LT_DEF"),
    "EVO_LEVEL_ATK_EQ_DEF": ("EVOLVE_STAT", "ATK_EQ_DEF"),
}
# User-approved prototype substitutions, not claims about canonical mechanics.
TEMPORARY_METHODS = {
    ("MAGNETON", "MAGNEZONE"): (("EVOLVE_LEVEL", "40"), "Level 40 replaces magnetic-field level-up."),
    ("LICKITUNG", "LICKILICKY"): (("EVOLVE_LEVEL", "33"), "Level 33 replaces knowing Rollout."),
    ("RHYDON", "RHYPERIOR"): (("EVOLVE_TRADE", "METAL_COAT"), "Held Metal Coat replaces Protector."),
    ("TANGELA", "TANGROWTH"): (("EVOLVE_LEVEL", "40"), "Level 40 replaces knowing AncientPower."),
    ("EEVEE", "LEAFEON"): (("EVOLVE_ITEM", "LEAF_STONE"), "Leaf Stone replaces Moss Rock level-up; also a later canonical alternative."),
    ("EEVEE", "GLACEON"): (("EVOLVE_ITEM", "MOON_STONE"), "Moon Stone replaces Ice Rock level-up; avoids existing Water Stone branch."),
    ("TOGETIC", "TOGEKISS"): (("EVOLVE_ITEM", "SUN_STONE"), "Sun Stone replaces Shiny Stone."),
    ("AIPOM", "AMBIPOM"): (("EVOLVE_LEVEL", "32"), "Level 32 replaces knowing Double Hit."),
    ("YANMA", "YANMEGA"): (("EVOLVE_LEVEL", "33"), "Level 33 replaces knowing AncientPower."),
    ("MURKROW", "HONCHKROW"): (("EVOLVE_ITEM", "MOON_STONE"), "Moon Stone replaces Dusk Stone."),
    ("MISDREAVUS", "MISMAGIUS"): (("EVOLVE_ITEM", "MOON_STONE"), "Moon Stone replaces Dusk Stone."),
    ("GLIGAR", "GLISCOR"): (("EVOLVE_LEVEL", "40"), "Level 40 replaces held Razor Fang plus nighttime level-up."),
    ("SNEASEL", "WEAVILE"): (("EVOLVE_LEVEL", "40"), "Level 40 replaces held Razor Claw plus nighttime level-up."),
    ("PILOSWINE", "MAMOSWINE"): (("EVOLVE_LEVEL", "40"), "Level 40 replaces knowing AncientPower."),
    ("PORYGON2", "PORYGON_Z"): (("EVOLVE_TRADE", "UP_GRADE"), "A second held Up-Grade replaces Dubious Disc."),
    ("KIRLIA", "GALLADE"): (("EVOLVE_ITEM", "SUN_STONE"), "Sun Stone replaces male plus Dawn Stone; no gender check."),
    ("ROSELIA", "ROSERADE"): (("EVOLVE_ITEM", "SUN_STONE"), "Sun Stone replaces Shiny Stone."),
    ("FEEBAS", "MILOTIC"): (("EVOLVE_ITEM", "WATER_STONE"), "Water Stone replaces beauty; no Prism Scale trade."),
    ("DUSCLOPS", "DUSKNOIR"): (("EVOLVE_TRADE", "SPELL_TAG"), "Held Spell Tag replaces Reaper Cloth."),
    ("SNORUNT", "FROSLASS"): (("EVOLVE_ITEM", "MOON_STONE"), "Moon Stone replaces female plus Dawn Stone; no gender check."),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_source(root, path, revision=None):
    if revision:
        return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=root, text=True)
    return (root / path).read_text()


def species_names(root, revision=None):
    text = read_source(root, "constants/pokemon_constants.asm", revision).split("DEF NUM_POKEMON")[0]
    return re.findall(r"^\s*const\s+(\w+)", text, re.M)


def graph_source(root, names, revision=None):
    pointers, blocks, learnsets = [], {}, {}
    for path in EVOLUTION_FILES:
        text = read_source(root, path, revision)
        pointers += re.findall(r"^\s*dw\s+(\w+EvosAttacks)\s*(?:;.*)?$", text, re.M)
        for block in re.finditer(r"^(\w+EvosAttacks):\s*\n(.*?)(?=^\w+EvosAttacks:|\Z)", text, re.M | re.S):
            label, body = block.groups()
            if label in blocks:
                raise ValueError(f"Duplicate evolution label {label}")
            edges = []
            lines = body.splitlines(keepends=True)
            for index, line in enumerate(lines):
                line = line.split(";")[0].strip()
                if not line:
                    continue
                if re.fullmatch(r"db\s+0", line):
                    learnsets[label] = "".join(lines[index + 1:])
                    break
                record = re.fullmatch(r"(dbbw|dbbbw)\s+(EVOLVE_\w+)\s*,\s*(.*)", line)
                if not record or record[2] not in METHOD_LENGTHS:
                    raise ValueError(f"Unrecognized evolution row in {label}: {line}")
                macro, method, rest = record.groups()
                fields = tuple(field.strip() for field in rest.split(","))
                if len(fields) != (3 if method == "EVOLVE_STAT" else 2):
                    raise ValueError(f"Wrong field count in {label}: {line}")
                if macro != ("dbbbw" if method == "EVOLVE_STAT" else "dbbw"):
                    raise ValueError(f"Wrong row size in {label}: {line}")
                edges.append((fields[-1], (method, *fields[:-1])))
            else:
                raise ValueError(f"Missing evolution terminator in {label}")
            blocks[label] = edges
    if len(names) != 373 or len(pointers) != len(names) or len(set(pointers)) != len(pointers):
        raise ValueError("Expected exactly 373 unique species and evolution pointers")
    if set(blocks) != set(pointers):
        raise ValueError("Evolution labels and pointers disagree")
    return dict(zip(names, (blocks[p] for p in pointers))), dict(zip(names, (learnsets[p] for p in pointers)))


def first_stages(root, names, revision=None):
    text = read_source(root, "data/pokemon/first_stages.asm", revision)
    rows = re.findall(r"^\s*dw\s+(\w+)", text, re.M)
    if len(rows) != len(names) or not set(rows) <= set(names):
        raise ValueError("First-stage table must contain one valid species per row")
    return dict(zip(names, rows))


def fetch_canonical(names, output, jobs):
    directory = output / "canonical"
    directory.mkdir(parents=True, exist_ok=True)

    def fetch(name):
        slug = ALIASES.get(name, name).lower()
        path = directory / f"{slug}.json"
        url = f"{PLATINUM_BASE}/{slug}/data.json"
        if not path.exists():
            for attempt in range(3):
                try:
                    raw = subprocess.check_output(["curl", "-L", "--fail", "--silent", "--show-error",
                                                   "--connect-timeout", "5", "--max-time", "20", url])
                    json.loads(raw)
                    path.write_bytes(raw)
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(1 + attempt)
        raw = path.read_bytes()
        data = json.loads(raw)
        return name, dict(url=url, sha256=digest(raw), evolutions=data.get("evolutions", []))

    rows = {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        # Submit one bounded batch so a network failure cannot queue 373 retries.
        for start in range(0, len(names), jobs):
            rows.update(pool.map(fetch, names[start:start + jobs]))
    manifest = dict(repository="pret/pokeplatinum", revision=PLATINUM_REVISION, species=rows)
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def canonical_graph(manifest, names):
    reverse_aliases = {value: key for key, value in ALIASES.items()}
    result, outside = {name: [] for name in names}, []
    if manifest["revision"] != PLATINUM_REVISION or set(manifest["species"]) != set(names):
        raise ValueError("Canonical manifest revision/species disagree")
    for source in names:
        for entry in manifest["species"][source]["evolutions"]:
            target = entry[-1].removeprefix("SPECIES_")
            target = reverse_aliases.get(target, target)
            if target not in result:
                outside.append(dict(source=source, target=target, canonical=entry[:-1]))
                continue
            result[source].append((target, tuple(entry[:-1])))
    return result, outside


def native_method(method, items):
    kind, *parameters = method
    if kind not in METHOD_MAP:
        return None, f"Unsupported canonical method: {kind}"
    native, fixed = METHOD_MAP[kind]
    if native in ("EVOLVE_ITEM", "EVOLVE_TRADE") and fixed is None:
        item = parameters[0].removeprefix("ITEM_")
        if item not in items:
            return None, f"Missing canonical item: {item}"
        return (native, item), None
    if native == "EVOLVE_STAT":
        return (native, str(parameters[0]), fixed), None
    if fixed is not None:
        return (native, fixed), None
    return (native, str(parameters[0])), None


def walk_forward(graph, name, path=()):
    if name in path:
        raise ValueError(f"Evolution cycle: {path + (name,)}")
    result = []
    for target, method in graph[name]:
        if target not in graph:
            raise ValueError(f"Evolution target outside roster: {name} -> {target}")
        result.append((target, method))
        result += walk_forward(graph, target, path + (name,))
    return result


def ancestors(graph, name):
    parents = {}
    for parent, edges in graph.items():
        for target, method in edges:
            if target in parents:
                raise ValueError(f"Multiple parents for {target}")
            parents[target] = parent, method
    result, visited = [], {name}
    while name in parents:
        name, method = parents[name]
        if name in visited:
            raise ValueError(f"Ancestor cycle at {name}")
        visited.add(name)
        result.append((name, method))
    return result[::-1]


def flattened(graph):
    return [(source, target, method) for source, edges in graph.items() for target, method in edges]


def choose_evolution(edges, context):
    """Model the existing engine's ordered first-match checks, not new methods."""
    for target, method in edges:
        kind, parameter, *extra = method
        if kind == "EVOLVE_TRADE":
            ready = context["link"] and (parameter == "-1" or context["held"] == parameter)
        elif context["link"]:
            ready = False
        elif kind == "EVOLVE_ITEM":
            ready = context["force"] and context["item"] == parameter
        elif context["force"]:
            ready = False
        elif kind == "EVOLVE_LEVEL":
            ready = context["level"] >= int(parameter)
        elif kind == "EVOLVE_HAPPINESS":
            ready = context["happy"] >= 220 and (parameter == "TR_ANYTIME"
                    or (parameter == "TR_MORNDAY" and context["time"] in ("morning", "day"))
                    or (parameter == "TR_EVENITE" and context["time"] in ("evening", "night")))
        else:
            ready = context["level"] >= int(parameter) and context["comparison"] == extra[0]
        if ready:
            return target
    return None


def branch_witnesses(graph):
    witnesses, failures = [], []
    for source, edges in graph.items():
        for target, method in edges:
            kind, parameter, *extra = method
            context = dict(link=False, force=False, item=None, held=None, level=1,
                           happy=0, time="day", comparison="ATK_EQ_DEF")
            if kind == "EVOLVE_TRADE":
                context.update(link=True, held=None if parameter == "-1" else parameter)
            elif kind == "EVOLVE_ITEM":
                context.update(force=True, item=parameter)
            elif kind == "EVOLVE_HAPPINESS":
                context.update(happy=220, time="night" if parameter == "TR_EVENITE" else "day")
            else:
                context.update(level=int(parameter))
                if extra:
                    context["comparison"] = extra[0]
            actual = choose_evolution(edges, context)
            if actual != target:
                failures.append(f"Unreachable branch {source} -> {target}; first match was {actual}")
            witnesses.append(dict(source=source, target=target, context=context, actual=actual))
    return witnesses, failures


def verify_manifest(manifest, directory):
    for name, row in manifest["species"].items():
        slug = ALIASES.get(name, name).lower()
        raw = (directory / f"{slug}.json").read_bytes()
        if digest(raw) != row["sha256"] or json.loads(raw).get("evolutions", []) != row["evolutions"]:
            raise ValueError(f"Canonical cache hash/data mismatch for {name}")


def private_source(root, patch, output):
    destination = output / "candidate-source"
    for path in (*EVOLUTION_FILES, "data/pokemon/first_stages.asm",
                 "constants/pokemon_constants.asm", "constants/item_constants.asm",
                 "constants/pokemon_data_constants.asm"):
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / path, target)
    result = subprocess.run(["patch", "--batch", "--fuzz=0", "-p1", "-d", str(destination),
                             "-i", str(patch)], capture_output=True, text=True, check=True)
    (output / "patch-application.log").write_text(result.stdout + result.stderr)
    return destination


def constant_values(text):
    values, cursor = {}, 0
    for line in text.splitlines():
        if found := re.match(r"\s*const_def(?:\s+(\d+))?\s*(?:;.*)?$", line):
            cursor = int(found[1] or 0)
        elif found := re.match(r"\s*const\s+(\w+)\b", line):
            values[found[1]] = cursor
            cursor += 1
    return values


def linked_audit(root, report, rom_path, symbols_path):
    rom = rom_path.read_bytes()
    symbols = {name: (int(bank, 16), int(address, 16)) for bank, address, name in
               re.findall(r"^([\da-fA-F]+):([\da-fA-F]+)\s+(\S+)", symbols_path.read_text(), re.M)}
    names = [row["species"] for row in report["all_species"]]
    graph, _ = graph_source(root, names)
    ids = constant_values((root / "constants/item_constants.asm").read_text())
    ids.update(constant_values((root / "constants/pokemon_data_constants.asm").read_text()))

    def number(value):
        return ids[value] if value in ids else int(value)

    def read(bank, address, count):
        if count < 0 or not (0x4000 <= address < address + count <= 0x8000 if bank else
                             0 <= address < address + count <= 0x4000):
            raise ValueError(f"Invalid linked range {bank:02x}:{address:04x}+{count}")
        at = bank * 0x4000 + (address & 0x3fff)
        if at + count > len(rom):
            raise ValueError("Linked range outside ROM")
        return rom[at:at + count]

    def word(bank, address):
        return int.from_bytes(read(bank, address, 2), "little")

    linked, mismatches, index = {}, [], 0
    for label, count in (("EvosAttacksPointers1", 151), ("EvosAttacksPointers2", 100),
                         ("EvosAttacksPointers3", 122)):
        bank, address = symbols[label]
        for row in range(count):
            pointer = word(bank, address + row * 2)
            edges = []
            for _ in range(20):
                kind = read(bank, pointer, 1)[0]
                if kind == 0:
                    break
                if kind not in range(1, 6):
                    raise ValueError(f"Invalid linked evolution method {kind}")
                length = 5 if kind == 5 else 4
                record = read(bank, pointer, length)
                target = int.from_bytes(record[-2:], "little")
                if not 1 <= target <= len(names):
                    raise ValueError(f"Invalid linked target {target}")
                edges.append((names[target - 1], tuple(record[:-2])))
                pointer += length
            else:
                raise ValueError("Unterminated linked evolution list")
            name = names[index]
            linked[name] = edges
            expected = [(target, tuple(number(field) & 255 for field in method))
                        for target, method in graph[name]]
            if expected != edges:
                mismatches.append(name)
            index += 1
    first_bank, first_address = symbols["FirstEvoStages"]
    first_mismatches = [name for index, name in enumerate(names)
                        if word(first_bank, first_address + index * 2) != names.index(report["all_species"][index]["first_stage"]) + 1]
    future_mismatches, ancestor_mismatches = [], []
    for name in names:
        if [n for n, _ in walk_forward(graph, name)] != [n for n, _ in walk_forward(linked, name)]:
            future_mismatches.append(name)
        if [n for n, _ in ancestors(graph, name)] != [n for n, _ in ancestors(linked, name)]:
            ancestor_mismatches.append(name)
    info_mismatches = []
    if "PokedexInfoSpecies" in symbols:
        bank, address = symbols["PokedexInfoSpecies"]
        for index, name in enumerate(names):
            entry = read(bank, address + index * 6, 6)
            for start, expected in ((0, walk_forward(graph, name)), (3, ancestors(graph, name))):
                count = entry[start]
                pointer = int.from_bytes(entry[start + 1:start + 3], "little")
                targets = []
                for record in range(count):
                    target = word(bank, word(bank, pointer + record * 2))
                    if not 1 <= target <= len(names):
                        raise ValueError(f"Invalid linked Info target {target}")
                    targets.append(names[target - 1])
                if targets != [target for target, _ in expected]:
                    info_mismatches.append(dict(species=name,
                                                direction="forward" if start == 0 else "ancestor"))
    return dict(rom=str(rom_path), symbols=str(symbols_path), rom_sha256=digest(rom),
                symbols_sha256=digest(symbols_path.read_bytes()), species=len(names),
                direct_edges=len(flattened(linked)), direct_mismatches=mismatches,
                first_stage_mismatches=first_mismatches, forward_mismatches=future_mismatches,
                ancestor_mismatches=ancestor_mismatches,
                info_lists_checked="PokedexInfoSpecies" in symbols,
                info_list_mismatches=info_mismatches,
                passed=not any((mismatches, first_mismatches, future_mismatches, ancestor_mismatches, info_mismatches)))


class EvolutionAuditTests(unittest.TestCase):
    def test_rejects_forward_cycle(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            walk_forward({"A": [("B", ())], "B": [("A", ())]}, "A")

    def test_rejects_ancestor_cycle(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            ancestors({"A": [("B", ())], "B": [("A", ())]}, "A")

    def test_rejects_multiple_parents(self):
        with self.assertRaisesRegex(ValueError, "Multiple parents"):
            ancestors({"A": [("C", ())], "B": [("C", ())], "C": []}, "C")

    def test_rejects_missing_species(self):
        with self.assertRaisesRegex(ValueError, "outside roster"):
            walk_forward({"A": [("B", ())]}, "A")

    def test_forward_is_depth_first_and_ancestors_are_root_first(self):
        graph = {"A": [("B", ()), ("D", ())], "B": [("C", ())], "C": [], "D": []}
        self.assertEqual([n for n, _ in walk_forward(graph, "A")], ["B", "C", "D"])
        self.assertEqual([n for n, _ in ancestors(graph, "C")], ["A", "B"])

    def test_native_mapping_rejects_unavailable_item_and_condition(self):
        self.assertEqual(native_method(("EVO_LEVEL", 37), set()), (("EVOLVE_LEVEL", "37"), None))
        self.assertIsNone(native_method(("EVO_USE_ITEM", "ITEM_DUSK_STONE"), {"MOON_STONE"})[0])
        self.assertIsNone(native_method(("EVO_LEVEL_KNOW_MOVE", "MOVE_ROLLOUT"), set())[0])

    def test_gender_method_is_not_silently_replaced_with_item(self):
        self.assertIsNone(native_method(("EVO_USE_ITEM_MALE", "ITEM_DAWN_STONE"), {"DAWN_STONE"})[0])

    def test_temporary_allowlist_is_explicit_and_narrow(self):
        self.assertEqual(len(TEMPORARY_METHODS), 20)
        self.assertEqual(TEMPORARY_METHODS[("MAGNETON", "MAGNEZONE")][0], ("EVOLVE_LEVEL", "40"))
        self.assertNotIn(("STANTLER", "WYRDEER"), TEMPORARY_METHODS)

    def test_duplicate_item_branch_is_unreachable(self):
        graph = {"A": [("B", ("EVOLVE_ITEM", "WATER_STONE")), ("C", ("EVOLVE_ITEM", "WATER_STONE"))]}
        self.assertTrue(branch_witnesses(graph)[1])

    def test_day_night_and_distinct_item_branches_remain_reachable(self):
        graph = {"A": [("B", ("EVOLVE_HAPPINESS", "TR_MORNDAY")),
                        ("C", ("EVOLVE_HAPPINESS", "TR_EVENITE")),
                        ("D", ("EVOLVE_ITEM", "LEAF_STONE")),
                        ("E", ("EVOLVE_ITEM", "MOON_STONE"))]}
        self.assertEqual(branch_witnesses(graph)[1], [])

    def test_item_can_bypass_earlier_level_branch(self):
        graph = {"KIRLIA": [("GARDEVOIR", ("EVOLVE_LEVEL", "30")),
                             ("GALLADE", ("EVOLVE_ITEM", "SUN_STONE"))]}
        context = branch_witnesses(graph)[0][1]["context"]
        context["level"] = 100
        self.assertEqual(choose_evolution(graph["KIRLIA"], context), "GALLADE")

    def test_trade_and_nontrade_checks_do_not_shadow_one_another(self):
        graph = {"A": [("B", ("EVOLVE_LEVEL", "37")), ("C", ("EVOLVE_TRADE", "KINGS_ROCK"))]}
        self.assertEqual(branch_witnesses(graph)[1], [])


def self_tests(output):
    with (output / "self-tests.log").open("w") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(EvolutionAuditTests))
    return dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                passed=result.wasSuccessful())


def audit(root, manifest, baseline_revision):
    names = species_names(root)
    baseline_names = species_names(root, baseline_revision)
    if baseline_names != names:
        raise ValueError("Baseline roster differs from current 373-species roster")
    graph, learnsets = graph_source(root, names)
    baseline, baseline_learnsets = graph_source(root, names, baseline_revision)
    first = first_stages(root, names)
    canonical, outside = canonical_graph(manifest, names)
    item_text = (root / "constants/item_constants.asm").read_text()
    items = set(re.findall(r"^\s*const\s+(\w+)", item_text, re.M))
    problems, missing, additions, changed_existing, custom_existing = [], [], [], [], []
    baseline_rows = flattened(baseline)
    current_rows = flattened(graph)
    for source, target, method in baseline_rows:
        if (source, target, method) not in current_rows:
            changed_existing.append(dict(source=source, target=target, method=method))
        canonical_method = next((m for t, m in canonical[source] if t == target), None)
        native = native_method(canonical_method, items)[0] if canonical_method else None
        if native != method:
            custom_existing.append(dict(source=source, target=target, method=method,
                                        canonical=canonical_method))
    for source, target, method in current_rows:
        if (source, target, method) not in baseline_rows:
            canonical_method = next((m for t, m in canonical[source] if t == target), None)
            temporary = TEMPORARY_METHODS.get((source, target))
            additions.append(dict(source=source, target=target, method=method,
                                  bytes=METHOD_LENGTHS[method[0]], canonical=canonical_method,
                                  temporary=temporary is not None,
                                  explanation=temporary[1] if temporary else "Original canonical method and requirement.",
                                  url=manifest["species"][source]["url"]))
        if target not in names:
            problems.append(f"Invalid target {source} -> {target}")
        if method[0] == "EVOLVE_LEVEL" and not 1 <= int(method[1]) <= 100:
            problems.append(f"Invalid level {source}: {method}")
        if method[0] == "EVOLVE_HAPPINESS" and method[1] not in ("TR_ANYTIME", "TR_MORNDAY", "TR_EVENITE"):
            problems.append(f"Invalid happiness trigger {source}: {method}")
        if method[0] in ("EVOLVE_ITEM", "EVOLVE_TRADE") and method[1] not in items | {"-1"}:
            problems.append(f"Invalid item {source}: {method}")
        if not any(t == target for t, _ in canonical[source]):
            if (source, target, method) not in baseline_rows:
                problems.append(f"Added noncanonical edge {source} -> {target}")
    for source, edges in canonical.items():
        for target, method in edges:
            expected, reason = native_method(method, items)
            actual = next((m for t, m in graph[source] if t == target), None)
            previous = next((m for t, m in baseline[source] if t == target), None)
            if actual is None:
                missing.append(dict(source=source, target=target, canonical=method,
                                    supported=expected is not None, native=expected, reason=reason,
                                    url=manifest["species"][source]["url"]))
            elif previous is None and expected != actual:
                temporary = TEMPORARY_METHODS.get((source, target))
                if temporary is None or temporary[0] != actual:
                    problems.append(f"Unapproved canonical conversion {source} -> {target}: {actual}")
    for source, edges in baseline.items():
        retained = [row for row in graph[source] if row in edges]
        if retained != edges:
            problems.append(f"Reordered existing branches: {source}")
    problems += [f"Changed existing row: {row}" for row in changed_existing]
    problems += [f"Changed learnset: {name}" for name in names if learnsets[name] != baseline_learnsets[name]]
    rows = []
    for number, name in enumerate(names, 1):
        forward, backward = walk_forward(graph, name), ancestors(graph, name)
        canonical_forward = walk_forward(canonical, name)
        canonical_backward = ancestors(canonical, name)
        canonical_root = canonical_backward[0][0] if canonical_backward else name
        if first[name] != canonical_root:
            problems.append(f"Wrong first stage for {name}: {first[name]}, expected {canonical_root}")
        for target, _ in forward:
            if name not in {parent for parent, _ in ancestors(graph, target)}:
                problems.append(f"Forward/ancestor mismatch: {name} -> {target}")
        for parent, _ in backward:
            if name not in {target for target, _ in walk_forward(graph, parent)}:
                problems.append(f"Ancestor/forward mismatch: {parent} -> {name}")
        rows.append(dict(id=number, species=name, direct=graph[name],
                         forward=forward, ancestors=backward,
                         canonical_forward=canonical_forward, canonical_ancestors=canonical_backward,
                         first_stage=first[name],
                         missing_forward=[t for t, _ in canonical_forward if t not in {n for n, _ in forward}],
                         missing_ancestors=[t for t, _ in canonical_backward if t not in {n for n, _ in backward}]))
    witnesses, branch_failures = branch_witnesses(graph)
    problems += branch_failures
    supported_missing = [row for row in missing if row["supported"]]
    first_before = first_stages(root, names, baseline_revision)
    first_changes = [dict(species=n, before=first_before[n], after=first[n])
                     for n in names if first_before[n] != first[n]]
    total_bytes = sum(METHOD_LENGTHS[method[0]] for _, _, method in current_rows)
    baseline_bytes = sum(METHOD_LENGTHS[method[0]] for _, _, method in baseline_rows)
    return dict(species=len(names), baseline_revision=baseline_revision,
                canonical_revision=manifest["revision"], canonical_edges=len(flattened(canonical)),
                baseline_edges=len(baseline_rows), actual_edges=len(current_rows),
                added_edges=len(additions), missing_edges=len(missing),
                supported_missing=len(supported_missing), unsupported_missing=len(missing) - len(supported_missing),
                gameplay_romx_bytes=total_bytes, baseline_gameplay_romx_bytes=baseline_bytes,
                added_gameplay_romx_bytes=total_bytes - baseline_bytes,
                baseline_rows_preserved=not changed_existing,
                learnsets_preserved=all(learnsets[n] == baseline_learnsets[n] for n in names),
                complete=not missing and not problems, validation_pass=not problems and not supported_missing,
                canonical_new_edges=sum(not row["temporary"] for row in additions),
                temporary_new_edges=sum(row["temporary"] for row in additions),
                canonical_requirements_complete=not missing and not any(row["temporary"] for row in additions) and not problems,
                temporary_approval="2026-10-15: user approved temporary existing methods for prototype testing only.",
                first_stage_changes=first_changes, branch_witnesses=witnesses,
                unreachable_branches=branch_failures,
                problems=problems, additions=additions, missing=missing,
                existing_custom_rows=custom_existing, outside_roster=outside,
                all_species=rows,
                source_sha256={path: digest((root / path).read_bytes())
                               for path in (*EVOLUTION_FILES, "data/pokemon/first_stages.asm")},
                automated_only=True, runtime_tested=False, visual_approval=False,
                notes=["No production ROM or save is written.",
                       "Friendship uses the existing engine threshold and daylight buckets.",
                       "ROMX growth counts gameplay rows only; no ROM0/WRAM/HRAM changes.",
                       "Info asset cost and runtime screenshots belong to the parent prototype build.",
                       "All 20 temporary substitutions must be reconsidered before production integration."])


def markdown(report):
    lines = ["# Evolution Data Audit", "", f"- Species audited: {report['species']}",
             f"- Canonical / baseline / current direct edges: {report['canonical_edges']} / {report['baseline_edges']} / {report['actual_edges']}",
             f"- Added: {report['added_edges']} links, +{report['added_gameplay_romx_bytes']} gameplay ROMX bytes",
             f"- Missing: {report['missing_edges']} ({report['supported_missing']} supported, {report['unsupported_missing']} unsupported)",
             f"- Existing rows preserved: {report['baseline_rows_preserved']}",
             f"- Learnsets preserved: {report['learnsets_preserved']}",
             f"- Structural validation passed: {report['validation_pass']}",
             f"- All canonical relationships present: {report['complete']}",
             f"- Added original canonical / temporary requirements: {report['canonical_new_edges']} / {report['temporary_new_edges']}",
             f"- All canonical requirements implemented: {report['canonical_requirements_complete']}", "",
             report["temporary_approval"],
             "Automated source/graph checks only. No runtime timing, listening, or visual approval is claimed.",
             "No ROM or save was changed. Info/generated-asset cost must be measured in the parent's candidate build.", "",
             f"Canonical reference: [Platinum game-data reconstruction](https://github.com/pret/pokeplatinum/tree/{report['canonical_revision']}/res/pokemon).", "",
             "## Added Links", "", "| Source | Target | Native requirement | Canonical requirement | Status | ROMX bytes |", "| --- | --- | --- | --- | --- | ---: |"]
    for row in report["additions"]:
        lines.append(f"| [{row['source']}]({row['url']}) | {row['target']} | {', '.join(row['method'])} | {', '.join(map(str, row['canonical'] or []))} | {'TEMPORARY: ' + row['explanation'] if row['temporary'] else 'Canonical original'} | {row['bytes']} |")
    lines += ["", "## Family Metadata", ""]
    lines += [f"- {row['species']}: {row['before']} -> {row['after']}" for row in report["first_stage_changes"]] or ["Unchanged."]
    lines += ["", f"Every direct edge has an ordered-method reachability witness: {len(report['branch_witnesses'])} checked; {len(report['unreachable_branches'])} unreachable."]
    lines += ["", "## Missing Canonical Links", "", "| Source | Target | Canonical requirement | Status |", "| --- | --- | --- | --- |"]
    for row in report["missing"]:
        lines.append(f"| [{row['source']}]({row['url']}) | {row['target']} | {', '.join(map(str, row['canonical']))} | {row['reason'] or 'Supported; must add'} |")
    if report.get("linked"):
        linked = report["linked"]
        lines += ["", "## Linked Candidate", "", f"- ROM: `{linked['rom']}`",
                  f"- ROM SHA-256: `{linked['rom_sha256']}`",
                  f"- All {linked['species']} direct, forward, ancestor, and first-stage records match source: {linked['passed']}"]
    if report.get("self_tests"):
        tests = report["self_tests"]
        lines += ["", f"Audit negative/branch tests: {tests['tests']} cases, {tests['failures']} failures, {tests['errors']} errors."]
    lines += ["", "## Problems", ""] + (report["problems"] or ["None."])
    lines += ["", "## All 373 Species", "", "Forward and ancestor columns reflect actual source data, not the canonical oracle.", "",
              "| ID | Species | First stage | Forward targets | Ancestors | Missing canonical targets |", "| ---: | --- | --- | --- | --- | --- |"]
    for row in report["all_species"]:
        lines.append(f"| {row['id']} | {row['species']} | {row['first_stage']} | {', '.join(n for n, _ in row['forward']) or '-'} | {', '.join(n for n, _ in row['ancestors']) or '-'} | {', '.join(row['missing_forward']) or '-'} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fetch-canonical", action="store_true")
    parser.add_argument("--canonical", type=Path, help="Pinned manifest.json; sibling species JSON hashes are verified")
    parser.add_argument("--patch", type=Path, help="Apply only to a private output/candidate-source copy before auditing")
    parser.add_argument("--rom", type=Path, help="Optionally decode a linked candidate ROM read-only")
    parser.add_argument("--symbols", type=Path, help="Matching candidate .sym file for --rom")
    parser.add_argument("--self-test", action="store_true", help="Run audit negative and branch reachability tests")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--baseline-ref", default="3ed28c430b67e8a7c695459a568fc71568cfb7df")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--temporary-approval", help="Explicit user decision to record for temporary requirements")
    args = parser.parse_args()
    args.root, args.output = args.root.resolve(), args.output.resolve()
    if not 1 <= args.jobs <= 32:
        parser.error("--jobs must be between 1 and 32")
    if not args.output.is_relative_to((ROOT / "build").resolve()):
        parser.error("Audit output must be under the repository's build/ directory")
    if bool(args.rom) != bool(args.symbols):
        parser.error("--rom and --symbols must be supplied together")
    args.output.mkdir(parents=True, exist_ok=True)
    names = species_names(args.root)
    if args.fetch_canonical:
        manifest = fetch_canonical(names, args.output, args.jobs)
        manifest_path = args.output / "canonical/manifest.json"
    else:
        manifest_path = args.canonical or args.output / "canonical/manifest.json"
        manifest = json.loads(manifest_path.read_text())
    verify_manifest(manifest, manifest_path.parent)
    source_root = private_source(args.root, args.patch.resolve(), args.output) if args.patch else args.root
    report = audit(source_root, manifest, args.baseline_ref)
    if args.temporary_approval:
        report["temporary_approval"] = args.temporary_approval
    report["source_root"] = str(source_root)
    report["canonical_manifest"] = str(manifest_path.resolve())
    if args.patch:
        report["patch"] = str(args.patch.resolve())
        report["patch_sha256"] = digest(args.patch.read_bytes())
    if args.self_test:
        report["self_tests"] = self_tests(args.output)
        if not report["self_tests"]["passed"]:
            report["validation_pass"] = False
    if args.rom:
        report["linked"] = linked_audit(source_root, report, args.rom.resolve(), args.symbols.resolve())
        if not report["linked"]["passed"]:
            report["validation_pass"] = False
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "report.md").write_text(markdown(report))
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, (list, dict))}, indent=2))
    if not report["validation_pass"] or (args.require_complete and not report["complete"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
