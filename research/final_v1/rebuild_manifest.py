"""Restore the ignored input manifest from relocated unchanged raw files.

Writes no model, protocol, inventory statistics or empirical output. Not a collector.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research'))
import oos


def main(root):
    groups,files=oos.catalog(root)
    fingerprint=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    expected=json.loads((oos.OUT/'inventory.json').read_text())['inventory_fingerprint']
    if fingerprint!=expected:raise ValueError('Archive differs from the recorded inventory; no manifest written')
    result=dict(files=files,sessions=groups);path=oos.OUT/'input_manifest.json'
    if path.exists():
        if json.loads(path.read_text())!=result:raise ValueError('Existing manifest differs; refusing replacement')
    else:oos.save(path,result)
    print('Recorded archive fingerprint verified;',len(files),'files; ignored manifest ready')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bbo-root',type=Path,required=True);main(parser.parse_args().bbo_root)
