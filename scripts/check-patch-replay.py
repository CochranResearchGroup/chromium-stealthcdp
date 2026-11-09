#!/usr/bin/env python3
"""Replay the real queue against pinned source blobs without changing that source.

Only touched files are materialized; this checks git-am compatibility, not builds.
"""
import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile


def main():
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--src', type=Path, required=True, help='Existing Chromium Git checkout')
    parser.add_argument('--revision', help='Override the pinned base for upgrade checks')
    args = parser.parse_args()
    revision = args.revision or (repo / 'upstream-revision.txt').read_text().strip()
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        parser.error('revision must be an immutable 40-character SHA')
    patches = sorted((repo / 'patches').glob('*.patch'))
    if not patches:
        parser.error('patch queue is empty')
    paths = set()
    for patch in patches:
        pairs = re.findall(r'^diff --git a/(\S+) b/(\S+)$', patch.read_text(), re.M)
        if not pairs:
            parser.error(f'unsupported or empty patch: {patch.name}')
        for before, after in pairs:
            for name in (before, after):
                path = PurePosixPath(name)
                if path.is_absolute() or '..' in path.parts or '.git' in path.parts:
                    parser.error('unsafe patch path')
                paths.add(name)
    with tempfile.TemporaryDirectory(prefix='chromium-patch-replay-') as directory:
        root = Path(directory)
        for name in sorted(paths):
            # All current queue paths exist at the pinned base. Missing blobs fail
            # closed rather than silently substituting the current working tree.
            blob = subprocess.run(['git', '-C', str(args.src), 'show', f'{revision}:{name}'],
                                  check=True, capture_output=True).stdout
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
        def git(*command):
            return subprocess.run(['git', '-C', directory, '-c', 'user.name=Patch Replay Check',
                                   '-c', 'user.email=replay@localhost', '-c', 'commit.gpgsign=false',
                                   '-c', 'core.hooksPath=/dev/null', *command], check=True)
        git('init', '--quiet')
        git('add', '.')
        git('commit', '--quiet', '-m', f'Touched source files at {revision}')
        git('am', *(str(p.resolve()) for p in patches))
        git('diff', '--check', 'HEAD~' + str(len(patches)), 'HEAD')
    print(f'PASS: {len(patches)} patches replay on {revision} ({len(paths)} source files)')


if __name__ == '__main__':
    main()
