"""Preserve the approved Thunderbolt evidence outside disposable build outputs."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

from .thunderbolt import OUT, ROOT

DEST = ROOT / 'research_artifacts' / OUT.name


def digest(stream):
    value = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        value.update(block)
    return value.hexdigest()


def file_digest(path):
    with path.open('rb') as stream:
        return digest(stream)


def members():
    for name in ['gba', 'crystal', 'emerald-fixtures', 'observers']:
        for path in sorted((OUT / name).rglob('*')):
            if path.is_file() and not path.is_symlink():
                yield path, 'captures/' + str(path.relative_to(OUT))
    yield OUT / 'measurements.json', 'captures/measurements.json'
    for name in ['pokeemerald.gba', 'pokeemerald.elf', 'pokeemerald.map']:
        yield OUT / 'emerald' / name, 'roms/emerald/' + name
    for label, base, name in [
        ('production', ROOT, 'pokecrystal'),
        ('double-speed', ROOT / 'build/global-speed-20261004/final', 'pokecrystal-global-double-speed'),
    ]:
        for suffix in ['.gbc', '.sym']:
            yield base / (name + suffix), f'roms/{label}/{name}{suffix}'
    for directory in ['tools/gba_timing', 'tools/dex_timing']:
        for path in sorted((ROOT / directory).rglob('*')):
            if (path.is_file() and not path.is_symlink()
                    and '__pycache__' not in path.parts):
                yield path, 'host-source/' + str(path.relative_to(ROOT))
    for name in ['tools/pokedex_info_assets.py', 'tools/build_global_speed_prototype.py',
                 'tools/build_dex_performance_prototype.py', 'tools/build_dex_performance_round2.py',
                 'docs/thunderbolt_three_way_comparison.md', 'docs/archived/thunderbolt-reference.md']:
        yield ROOT / name, 'host-source/' + name


def verify_manifest():
    data = json.loads((DEST / 'manifest.json').read_text())
    for item in [data['archive'], *data['videos']]:
        path = DEST / item['path']
        assert path.stat().st_size == item['bytes'] and file_digest(path) == item['sha256'], path
    expected = {m['path']: m for m in data['members']}
    with tarfile.open(DEST / data['archive']['path'], 'r:gz') as archive:
        entries = archive.getmembers()
        assert len(entries) == len(expected)
        for member in entries:
            assert member.isfile() and member.name in expected
            record = expected[member.name]
            with archive.extractfile(member) as stream:
                assert member.size == record['bytes'] and digest(stream) == record['sha256'], member.name
    return data


def main():
    if (DEST / 'manifest.json').exists():
        data = verify_manifest()
        print(f'Existing archive verified: {DEST} ({len(data["members"])} members)')
        return
    DEST.mkdir(parents=True, exist_ok=True)
    archive_path = DEST / 'captures-and-replay-inputs.tar.gz'
    if archive_path.exists():
        raise FileExistsError(f'Refusing to overwrite an archive without its manifest: {archive_path}')
    entries = list(members())
    assert len({name for _, name in entries}) == len(entries)
    records = []
    pending = archive_path.with_suffix('.partial')
    with tarfile.open(pending, 'w:gz', compresslevel=6) as archive:
        for path, name in entries:
            size = path.stat().st_size
            before = file_digest(path)
            archive.add(path, arcname=name, recursive=False)
            assert path.stat().st_size == size and file_digest(path) == before, path
            records.append(dict(path=name, bytes=size, sha256=before, source=str(path)))
    expected = {r['path']: r for r in records}
    with tarfile.open(pending, 'r:gz') as archive:
        assert len(archive.getmembers()) == len(records)
        for member in archive.getmembers():
            with archive.extractfile(member) as stream:
                assert digest(stream) == expected[member.name]['sha256'], member.name
    pending.rename(archive_path)
    videos = []
    (DEST / 'videos').mkdir(exist_ok=True)
    for source in sorted((OUT / 'videos').glob('*')):
        if not source.is_file():
            continue
        target = DEST / 'videos' / source.name
        if target.exists():
            assert file_digest(source) == file_digest(target), target
        else:
            shutil.copy2(source, target)
        assert file_digest(source) == file_digest(target), target
        videos.append(dict(path=str(target.relative_to(DEST)), bytes=target.stat().st_size,
                           sha256=file_digest(target), source=str(source)))
    data = dict(purpose='Retained Thunderbolt reference; exclude from build cleanup.',
                archive=dict(path=archive_path.name, bytes=archive_path.stat().st_size,
                             sha256=file_digest(archive_path)), members=records, videos=videos)
    (DEST / 'manifest.json').write_text(json.dumps(data, indent=2) + '\n')
    verify_manifest()
    print(json.dumps(dict(directory=str(DEST), members=len(records), media=len(videos),
                          archive_bytes=archive_path.stat().st_size), indent=2))


if __name__ == '__main__':
    main()
