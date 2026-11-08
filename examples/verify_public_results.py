"""Audit published aggregates with Python's standard library; no market inputs.

This is a consistency example, not a rerun of the historical market experiment.
It cannot reconstruct ranking AUC, source clocks or bootstrap CIs from matrices.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def main():
    primary = load('results/final_v1/primary_holdout.json')
    exploratory = load('results/final_v1/exploration.json')
    protocol = load('results/final_v1/protocol.json')
    state = load('results/final_v1/consumption.json')
    for path, expected in [
        ('results/oos/frozen_models.json', protocol['models_sha256']),
        ('research/final_v1/run.py', protocol['analysis_source_sha256']),
        ('results/final_v1/primary_holdout.json', state['primary_sha256']),
    ]:
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    assert state['seen_forever'] and state['status'] == 'complete'
    inventory = load('results/oos/inventory.json')
    model = load('results/oos/frozen_models.json')
    assert protocol['archive_fingerprint'] == inventory['inventory_fingerprint'] == model['inventory_fingerprint']
    print('Published aggregate consistency check; no raw-data replay')
    for horizon, result in primary['horizons'].items():
        assert result['labels'] == result['up'] + result['down'] + result['zero']
        for model in result['models'].values():
            matrix = model['confusion_matrix']
            n = sum(map(sum, matrix))
            accuracy = (matrix[0][0] + matrix[1][1]) / n
            balanced = (matrix[0][0] / sum(matrix[0]) + matrix[1][1] / sum(matrix[1])) / 2
            assert abs(accuracy - model['accuracy']) < 1e-12
            assert abs(balanced - model['balanced_accuracy']) < 1e-12
            assert n == result['directional']
        obi = result['models']['obi']
        all_time = exploratory['holdout'][horizon]['three_action']['forced']['accuracy']
        assert abs(all_time - result['directional'] / result['labels'] * obi['accuracy']) < 1e-12
        print(f"{horizon}s: nonzero N={obi['n']}, conditional BA={obi['balanced_accuracy']:.3f}, "
              f"all-label N={result['labels']}, forced agreement={all_time:.3f}")
    print('12 model/horizon matrices and recorded model/source/consumption hashes verified.')


if __name__ == '__main__':
    main()
