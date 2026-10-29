"""Offline release/catalog verification and optional native stdio MCP smoke."""
import argparse
import hashlib
import json
import platform as host_platform
from pathlib import Path
import re
import subprocess
import tempfile
from catalog import NAMES, TARGETS, catalog

EXPECTED_TOOLS = {
    'github-work-inspector': {'list_repositories', 'repository_metadata', 'repository_snapshot'},
    'code-structure-inspector': {'inspect_repository', 'related_files'},
    'experiment-model-inspector': {'inspect_experiment'},
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_platform():
    pair = (host_platform.system(), host_platform.machine().lower())
    return {('Darwin', 'arm64'): 'macos-arm64', ('Linux', 'x86_64'): 'linux-x64',
            ('Windows', 'amd64'): 'windows-x64'}.get(pair)


def smoke(plugin):
    name = plugin.name
    config = json.loads((plugin / '.mcp.json').read_text())['mcpServers'][name]
    binary = plugin / config['command']
    requests = [
        {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2025-06-18', 'capabilities': {},
            'clientInfo': {'name': 'distribution-check', 'version': '1.0.0'}}},
        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
        {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
    ]
    with tempfile.TemporaryDirectory(prefix='inspector-synthetic-') as directory:
        fixture = Path(directory)
        (fixture / 'example.py').write_text('def double(value):\n    return value * 2\n')
        (fixture / 'experiment-model.json').write_text(json.dumps({
            'version': 1, 'sources': ['example.py'], 'nodes': [
                {'id': 'double', 'kind': 'model', 'label': 'Synthetic double',
                 'evidence': [{'file': 'example.py', 'line': 2,
                               'exact': 'return value * 2'}]}], 'edges': []}))
        if name == 'github-work-inspector':
            # Fixed invalid identifier: must fail validation before any gh/network call.
            call = {'name': 'repository_metadata', 'arguments': {'repository': '../invalid'}}
        elif name == 'code-structure-inspector':
            call = {'name': 'inspect_repository', 'arguments': {'root': str(fixture)}}
        else:
            call = {'name': 'inspect_experiment', 'arguments': {
                'root': str(fixture), 'manifest': 'experiment-model.json'}}
        requests.append({'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': call})
        before = {p.name: digest(p) for p in fixture.iterdir()}
        run = subprocess.run([str(binary.resolve()), *config.get('args', [])],
                             cwd=plugin, input=''.join(json.dumps(r) + '\n' for r in requests),
                             text=True, capture_output=True, check=True, timeout=30)
        replies = {item['id']: item for item in map(json.loads, run.stdout.splitlines())}
        assert 'result' in replies[1], 'MCP initialize failed'
        tools = replies[2]['result']['tools']
        assert {tool['name'] for tool in tools} == EXPECTED_TOOLS[name]
        assert all(tool.get('annotations', {}).get('readOnlyHint') is True for tool in tools)
        result = replies[3]
        if name == 'github-work-inspector':
            assert 'error' in result or result.get('result', {}).get('isError') is True
        else:
            assert 'error' not in result and not result['result'].get('isError', False), result
        assert before == {p.name: digest(p) for p in fixture.iterdir()}, 'Fixture modified'
        return sorted(tool['name'] for tool in tools)


def verify(root, run_smoke=False):
    lock = json.loads((root / 'releases.lock.json').read_text())
    assert lock['schema_version'] == 1
    assert tuple(p['name'] for p in lock['plugins']) == NAMES
    for plugin in lock['plugins']:
        assert re.fullmatch(r'[0-9a-f]{40}', plugin['source_commit'])
        assert re.fullmatch(r'\d+\.\d+\.\d+', plugin['version'])
        assert plugin['repository'] == 'https://github.com/iwashita-nozomu/' + plugin['name']
        assert plugin['release'] == plugin['repository'] + '/releases/tag/v' + plugin['version']
        assert set(plugin['archives']) == set(TARGETS)
        for pin in plugin['archives'].values():
            assert re.fullmatch(r'[0-9a-f]{64}', pin['sha256'])
            assert pin['url'] == plugin['repository'] + '/releases/download/v' + plugin['version'] + '/' + pin['name']
            assert 0 < pin['size'] < 50 * 1024 * 1024
    metadata_path = root / 'distribution.json'
    if not metadata_path.exists():
        assert not (root / '.agents/plugins/marketplace.json').exists()
        assert not run_smoke, 'main is documentation/tooling only; select a distribution branch'
        return {'lock': 'verified', 'plugins': len(NAMES), 'platforms': len(TARGETS)}
    metadata = json.loads(metadata_path.read_text())
    selected = metadata['platform']
    assert metadata['schema_version'] == 1 and metadata['target'] == TARGETS[selected]
    assert metadata['lock_sha256'] == digest(root / 'releases.lock.json')
    assert json.loads((root / '.agents/plugins/marketplace.json').read_text()) == catalog()
    assert set(metadata['files']) == set(NAMES)
    assert {p.name for p in (root / 'plugins').iterdir()} == set(NAMES)
    discovered = {}
    for pin in lock['plugins']:
        name = pin['name']
        package = root / 'plugins' / name
        assert not any(p.is_symlink() for p in package.rglob('*'))
        actual = {p.relative_to(package).as_posix(): digest(p)
                  for p in package.rglob('*') if p.is_file()}
        assert actual == metadata['files'][name], 'Release package inventory differs: ' + name
        for file in ('LICENSE', 'THIRD_PARTY_NOTICES.md',
                     'plugin.json', '.codex-plugin/plugin.json', 'mcp.json', '.mcp.json'):
            assert (package / file).is_file(), (name, file)
        assert any(p.is_file() for p in (package / 'third-party').rglob('*'))
        if name != 'experiment-model-inspector':
            assert (package / 'third-party/manifest.json').is_file()
        portable = json.loads((package / 'plugin.json').read_text())
        codex = json.loads((package / '.codex-plugin/plugin.json').read_text())
        assert portable['name'] == codex['name'] == name
        assert portable['version'] == codex['version'] == pin['version']
        assert portable['license'] == codex['license'] == 'MIT'
        for filename in ('mcp.json', '.mcp.json'):
            config = json.loads((package / filename).read_text())
            assert set(config['mcpServers']) == {name}
            server = config['mcpServers'][name]
            executable = name + ('.exe' if selected == 'windows-x64' else '')
            assert server['command'] == './bin/' + executable
            assert server['cwd'] == '${PLUGIN_ROOT}' and server['args'] == ['mcp']
        binary = package / 'bin' / executable
        magic = binary.read_bytes()[:4]
        assert {'macos-arm64': magic == b'\xcf\xfa\xed\xfe',
                'linux-x64': magic == b'\x7fELF',
                'windows-x64': magic[:2] == b'MZ'}[selected], 'Wrong OS binary'
        skills = list((package / 'skills').glob('*/SKILL.md'))
        assert skills
        assert not (package / 'hooks.json').exists()
        if run_smoke:
            assert native_platform() == selected, 'Refusing foreign binary execution'
            discovered[name] = smoke(package)
    return {'platform': selected, 'packages': 'verified', 'tools': discovered}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve(), args.smoke), sort_keys=True))
