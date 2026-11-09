"""Publication failures must be explicit and must not repair reviewed evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication', ROOT/'examples/verify_publication.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


@pytest.fixture
def package(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path/'README.md').write_text('A public fixture, not research evidence.\n')
    subprocess.run(['git', 'add', 'README.md'], cwd=tmp_path, check=True)
    data = (tmp_path/'README.md').read_bytes()
    manifest = dict(version='publication-current-v1', manifest_excludes_itself=True,
                    historical_snapshot=publication.HISTORICAL_SNAPSHOT,
                    files=[dict(path='README.md', bytes=len(data),
                                sha256=hashlib.sha256(data).hexdigest())])
    (tmp_path/publication.CURRENT_MANIFEST).write_text(json.dumps(manifest))
    return tmp_path


def test_current_package_and_pinned_historical_snapshot_verify():
    assert publication.verify_current(ROOT) > 0
    assert publication.verify_historical(ROOT) == 107


@pytest.mark.parametrize('change', ['modified', 'missing', 'untracked', 'tracked', 'symlink'])
def test_current_manifest_rejects_drift_without_repair(package, change):
    readme = package/'README.md'
    if change == 'modified':
        readme.write_text('Unreviewed change')
    elif change == 'missing':
        readme.unlink()
    elif change in {'untracked', 'tracked'}:
        (package/'extra.txt').write_text('Unlisted public file')
        if change == 'tracked':
            subprocess.run(['git', 'add', 'extra.txt'], cwd=package, check=True)
    else:
        readme.rename(package/'target.txt')
        readme.symlink_to('target.txt')
    before = (package/publication.CURRENT_MANIFEST).read_bytes()
    with pytest.raises(ValueError):
        publication.verify_current(package)
    assert (package/publication.CURRENT_MANIFEST).read_bytes() == before


@pytest.mark.parametrize('change', ['duplicate', 'unsafe', 'self', 'snapshot'])
def test_current_manifest_rejects_ambiguous_or_reassigned_records(package, change):
    path = package/publication.CURRENT_MANIFEST
    manifest = json.loads(path.read_text())
    if change == 'duplicate':
        manifest['files'].append(manifest['files'][0])
    elif change == 'unsafe':
        manifest['files'][0]['path'] = '../README.md'
    elif change == 'self':
        manifest['files'][0]['path'] = publication.CURRENT_MANIFEST
    else:
        manifest['historical_snapshot'] = dict(publication.HISTORICAL_SNAPSHOT, commit='0'*40)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        publication.verify_current(package)


def test_historical_manifest_cannot_be_reblessed(package):
    path = package/publication.HISTORICAL_MANIFEST
    path.write_text('{"version":"publication-v1","files":[]}')
    with pytest.raises(ValueError, match='Original historical manifest changed'):
        publication.verify_historical(package)


def test_missing_historical_git_objects_fail_explicitly(package):
    (package/publication.HISTORICAL_MANIFEST).write_bytes((ROOT/publication.HISTORICAL_MANIFEST).read_bytes())
    with pytest.raises(ValueError, match='original history'):
        publication.verify_historical(package)


def test_optimized_python_still_rejects_a_modified_publication(package):
    (package/'README.md').write_text('Unreviewed change')
    code = ('import runpy,sys; p=runpy.run_path(sys.argv[1]); '
            "p['verify_current'](sys.argv[2])")
    result = subprocess.run([sys.executable, '-B', '-O', '-c', code,
                             str(ROOT/'examples/verify_publication.py'), str(package)],
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Publication size/hash mismatch' in result.stderr
