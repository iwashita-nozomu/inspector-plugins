"""Maintainer-only offline assembly from downloaded, pinned release archives.

Never run by plugin installation or at runtime. Does not download or execute files.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import zipfile
from catalog import NAMES, TARGETS, catalog

ROOT = Path(__file__).resolve().parents[1]
MAX_UNPACKED = 200 * 1024 * 1024


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_name(name, plugin):
    path = PurePosixPath(name)
    if '\\' in name or path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Unsafe archive member')
    if path.parts[0] != plugin or len(path.parts) < 2 or ':' in name:
        raise ValueError('Unexpected archive root')
    return path


def unpack(archive, destination, plugin):
    """Extract only regular files/directories, bounded, without archive extract APIs."""
    total = 0
    seen = set()
    inventory = {}

    def write(name, data, executable=False):
        nonlocal total
        relative = safe_name(name, plugin)
        if str(relative) in seen:
            raise ValueError('Duplicate archive member')
        seen.add(str(relative))
        total += len(data)
        if total > MAX_UNPACKED:
            raise ValueError('Archive exceeds size bound')
        path = destination.joinpath(*relative.parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o755 if executable or relative.parts[1] == 'bin' else 0o644)
        inventory['/'.join(relative.parts[1:])] = hashlib.sha256(data).hexdigest()

    if archive.suffix == '.zip':
        with zipfile.ZipFile(archive) as source:
            if sum(item.file_size for item in source.infolist()) > MAX_UNPACKED:
                raise ValueError('Archive exceeds size bound')
            for item in source.infolist():
                if item.is_dir():
                    safe_name(item.filename.rstrip('/'), plugin)
                    continue
                mode = item.external_attr >> 16
                if mode & 0o170000 not in (0, 0o100000):
                    raise ValueError('Non-regular ZIP member')
                write(item.filename, source.read(item), bool(mode & 0o111))
    else:
        with tarfile.open(archive, 'r:gz') as source:
            members = source.getmembers()
            if sum(item.size for item in members) > MAX_UNPACKED:
                raise ValueError('Archive exceeds size bound')
            for item in members:
                if not item.isfile():
                    raise ValueError('Non-regular tar member')
                with source.extractfile(item) as stream:
                    write(item.name, stream.read(), bool(item.mode & 0o111))
    return inventory


def assemble(platform, archives, output):
    if output.exists():
        raise ValueError('Output must not already exist')
    lock = json.loads((ROOT / 'releases.lock.json').read_text())
    assert tuple(p['name'] for p in lock['plugins']) == NAMES
    # Validate every archive before writing any package.
    for plugin in lock['plugins']:
        pin = plugin['archives'][platform]
        archive = archives / pin['name']
        if archive.stat().st_size != pin['size'] or sha256(archive) != pin['sha256']:
            raise ValueError('Archive integrity check failed: ' + pin['name'])
    output.mkdir(parents=True)
    for filename in ('README.md', 'LICENSE', 'SECURITY.md', 'AGENTS.md',
                     '.gitignore', '.gitattributes', 'releases.lock.json'):
        shutil.copy2(ROOT / filename, output / filename)
    for directory in ('scripts', 'tests', 'docs', '.github'):
        shutil.copytree(ROOT / directory, output / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    inventories = {}
    for plugin in lock['plugins']:
        pin = plugin['archives'][platform]
        inventories[plugin['name']] = unpack(archives / pin['name'], output / 'plugins', plugin['name'])
    marketplace = output / '.agents/plugins/marketplace.json'
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(json.dumps(catalog(), indent=2) + '\n')
    (output / 'distribution.json').write_text(json.dumps({
        'schema_version': 1, 'platform': platform, 'target': TARGETS[platform],
        'lock_sha256': sha256(ROOT / 'releases.lock.json'), 'files': inventories,
    }, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', required=True, choices=TARGETS)
    parser.add_argument('--archives', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    assemble(args.platform, args.archives.resolve(), args.output.resolve())
    print(json.dumps({'assembled': args.platform, 'packages': list(NAMES)}))
