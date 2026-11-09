"""Verify current package coverage and the original public Git snapshot; read-only."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CURRENT_MANIFEST = 'PUBLICATION_CURRENT.json'
HISTORICAL_MANIFEST = 'PUBLICATION_FILES.json'
HISTORICAL_COMMIT = '587eb6c69b422a347612aaf83bb00c155f21a030'
HISTORICAL_SHA256 = 'baaac3e9be8a01f51325dc08004bee400d589e61cc1d453af2eaf7a91205697e'
HISTORICAL_SNAPSHOT = dict(commit=HISTORICAL_COMMIT, manifest=HISTORICAL_MANIFEST,
                           manifest_sha256=HISTORICAL_SHA256)


def _git(root, *args):
    try:
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        raise ValueError('Git verification requires the original history; for a shallow clone, '
                         'run git fetch --unshallow origin') from error


def _records(document, version):
    if (not isinstance(document, dict) or document.get('version') != version
            or document.get('manifest_excludes_itself') is not True
            or not isinstance(document.get('files'), list)):
        raise ValueError('Invalid publication manifest schema')
    records = {}
    for entry in document['files']:
        if not isinstance(entry, dict) or set(entry) != {'path', 'bytes', 'sha256'}:
            raise ValueError('Invalid publication file record')
        name = entry['path']
        if (not isinstance(name, str) or not name or '\\' in name or '\x00' in name
                or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
                or PurePosixPath(name).as_posix() != name or name == '.'):
            raise ValueError('Unsafe publication path')
        if name in records:
            raise ValueError('Duplicate publication path: '+name)
        if (type(entry['bytes']) is not int or entry['bytes'] < 0
                or not isinstance(entry['sha256'], str)
                or re.fullmatch('[0-9a-f]{64}', entry['sha256']) is None):
            raise ValueError('Invalid publication size or hash: '+name)
        records[name] = entry
    return records


def _matches(data, entry):
    return len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']


def verify_current(root=ROOT):
    root = Path(root).resolve()
    document = json.loads((root/CURRENT_MANIFEST).read_text())
    records = _records(document, 'publication-current-v1')
    if document.get('historical_snapshot') != HISTORICAL_SNAPSHOT:
        raise ValueError('Historical snapshot identity changed')
    if CURRENT_MANIFEST in records:
        raise ValueError('Current manifest must exclude itself')
    for name, entry in records.items():
        path = root/name
        if (path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(root)):
            raise ValueError('Missing or nonregular publication file: '+name)
        if not _matches(path.read_bytes(), entry):
            raise ValueError('Publication size/hash mismatch: '+name)
    # Support an uncommitted review patch as well as a committed checkout. Ignored
    # private inputs stay excluded; unreviewed nonignored additions fail coverage.
    paths = _git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z')
    present = {name for name in paths.decode().split('\x00') if name
               and ((root/name).exists() or (root/name).is_symlink())}
    expected = set(records) | {CURRENT_MANIFEST}
    if present != expected:
        raise ValueError('Publication coverage mismatch; unlisted='+str(sorted(present-expected))
                         +'; absent from Git working tree='+str(sorted(expected-present)))
    return len(records)


def verify_historical(root=ROOT):
    root = Path(root)
    payload = (root/HISTORICAL_MANIFEST).read_bytes()
    if hashlib.sha256(payload).hexdigest() != HISTORICAL_SHA256:
        raise ValueError('Original historical manifest changed')
    records = _records(json.loads(payload), 'publication-v1')
    if len(records) != 107:
        raise ValueError('Historical snapshot must have 107 entries')
    if _git(root, 'show', HISTORICAL_COMMIT+':'+HISTORICAL_MANIFEST) != payload:
        raise ValueError('Historical manifest differs from pinned Git snapshot')
    names = _git(root, 'ls-tree', '-r', '--name-only', '-z', HISTORICAL_COMMIT)
    if set(names.decode().rstrip('\x00').split('\x00')) != set(records) | {HISTORICAL_MANIFEST}:
        raise ValueError('Historical snapshot coverage mismatch')
    for name, entry in records.items():
        if not _matches(_git(root, 'show', HISTORICAL_COMMIT+':'+name), entry):
            raise ValueError('Historical snapshot size/hash mismatch: '+name)
    return len(records)


def main():
    try:
        current = verify_current()
        historical = verify_historical()
    except (ValueError, OSError) as error:
        print('Publication verification failed: '+str(error), file=sys.stderr)
        return 1
    print(f'Current publication: {current} files verified; exact Git working-tree coverage (manifest excluded).')
    print(f'Historical publication: {historical} entries and exact snapshot coverage verified at {HISTORICAL_COMMIT}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
