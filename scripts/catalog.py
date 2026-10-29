"""Codex's documented local source format; no platform/source extensions."""
NAMES = ('github-work-inspector', 'code-structure-inspector', 'experiment-model-inspector')
TARGETS = {
    'macos-arm64': 'aarch64-apple-darwin',
    'linux-x64': 'x86_64-unknown-linux-gnu',
    'windows-x64': 'x86_64-pc-windows-msvc',
}


def catalog():
    return {
        'name': 'inspector-plugins',
        'interface': {'displayName': 'Inspector Plugins'},
        'plugins': [
            {'name': name, 'source': {'source': 'local', 'path': './plugins/' + name},
             'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
             'category': 'Developer Tools'} for name in NAMES
        ],
    }
