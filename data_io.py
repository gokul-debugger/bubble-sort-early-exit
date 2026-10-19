"""Validate published observations and fixtures without private workspace access."""

import csv
import json
import math
from pathlib import Path

from workloads import PAIRED_DISTRIBUTIONS, input_hash, input_seed, paired_workload

ROOT = Path(__file__).resolve().parent
FIELDS = ['distribution', 'size', 'sample', 'input_seed', 'input_sha256', 'algorithm',
          'repeat', 'order', 'calls', 'elapsed_ns', 'ns_per_call', 'target_met',
          'status', 'reason', 'pair_id', 'shuffle_seed', 'multiset_sha256']
PROVENANCE = ['input_seed', 'input_sha256', 'pair_id', 'shuffle_seed', 'multiset_sha256']


def configuration():
    return json.loads((ROOT / 'config.json').read_text())


def load_inputs(regenerate=False):
    config = configuration()
    result = {}
    with (ROOT / 'data/inputs.jsonl').open() as f:
        for line in f:
            row = json.loads(line)
            d, n, s = row['distribution'], row['size'], row['sample']
            dataset = row['dataset']
            master = config['datasets'][dataset]['master_seed']
            key = (dataset, d, n, s)
            if key in result or d not in PAIRED_DISTRIBUTIONS or n not in config['settings']['sizes'] or not 0 <= s < config['settings']['inputs']:
                raise ValueError('Unexpected or duplicate fixture')
            values = tuple(row['values'])
            if len(values) != n or any(type(v) is not int or not -10*n <= v <= 10*n for v in values) or len(set(values)) != n:
                raise ValueError('Invalid distinct-integer fixture')
            ascending = tuple(sorted(values))
            if input_hash(values) != row['input_sha256'] or input_hash(ascending) != row['multiset_sha256']:
                raise ValueError('Fixture hash mismatch')
            if str(row['input_seed']) != str(input_seed(master, 'paired_base_v1', n, s)) or str(row['shuffle_seed']) != str(input_seed(master, 'paired_shuffle_v1', n, s)) or row['pair_id'] != f'{master}:{n}:{s}':
                raise ValueError('Fixture seed provenance mismatch')
            if d == 'paired_sorted' and values != ascending or d == 'paired_reversed' and values != tuple(reversed(ascending)):
                raise ValueError('Ordered fixture mismatch')
            if regenerate:
                rebuilt, provenance = paired_workload(master, d, n, s)
                if rebuilt != values or any(str(row[k]) != str(v) for k, v in provenance.items()):
                    raise ValueError('Seed regeneration differs from recorded fixture')
            result[key] = row
    expected = {(dataset, d, n, s) for dataset in config['datasets'] for d in PAIRED_DISTRIBUTIONS
                for n in config['settings']['sizes'] for s in range(config['settings']['inputs'])}
    if set(result) != expected:
        raise ValueError('Missing fixture')
    for dataset, d, n, s in result:
        reference = result[(dataset, 'paired_sorted', n, s)]['multiset_sha256']
        if result[(dataset, d, n, s)]['multiset_sha256'] != reference:
            raise ValueError('Orders do not contain matching values')
    return result


def read_rows(path):
    with path.open(newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            raise ValueError('Unexpected measurement columns')
        return list(reader)


def validate_rows(rows, dataset, fixtures, settings):
    expected = {(d, n, s, r) for d in PAIRED_DISTRIBUTIONS for n in settings['sizes']
                for s in range(settings['inputs']) for r in range(settings['repeats'])}
    seen = set()
    for row in rows:
        d, n, s, r = row['distribution'], int(row['size']), int(row['sample']), int(row['repeat'])
        key = (d, n, s, r)
        if key not in expected or key in seen or row['algorithm'] != 'bubble' or row['status'] != 'ok' or row['reason']:
            raise ValueError('Missing, duplicate, failed or unexpected observation')
        seen.add(key)
        fixture = fixtures[(dataset, d, n, s)]
        if any(row[k] != str(fixture[k]) for k in PROVENANCE):
            raise ValueError('Measurement input provenance mismatch')
        calls, elapsed = int(row['calls']), int(row['elapsed_ns'])
        average = float(row['ns_per_call'])
        if not 1 <= calls <= settings['max_calls'] or elapsed <= 0 or not math.isfinite(average) or average != elapsed/calls:
            raise ValueError('Invalid batch average')
        if row['target_met'] != str(elapsed >= settings['target_batch_ns']) or not 0 <= int(row['order']) < settings['methods_per_repeat']:
            raise ValueError('Invalid target flag or original schedule position')
    if seen != expected:
        raise ValueError('Incomplete observation matrix')


def validate_calibration(path, rows, dataset, fixtures, settings):
    observed = {(r['distribution'], int(r['size']), int(r['sample'])):int(r['calls']) for r in rows}
    seen = set()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        key = (row['distribution'], row['size'], row['sample'])
        if key not in observed or key in seen or row['algorithm'] != 'bubble':
            raise ValueError('Unexpected/duplicate calibration')
        seen.add(key)
        fixture = fixtures[(dataset, *key)]
        if any(str(row[k]) != str(fixture[k]) for k in PROVENANCE):
            raise ValueError('Calibration provenance mismatch')
        trials = row['trials']
        if not trials or any(type(t['calls']) is not int or not 1 <= t['calls'] <= settings['max_calls'] or type(t['elapsed_ns']) is not int or t['elapsed_ns'] <= 0 for t in trials):
            raise ValueError('Invalid calibration trials')
        if any(int(r['calls']) != trials[-1]['calls'] for r in rows if (r['distribution'], int(r['size']), int(r['sample'])) == key):
            raise ValueError('Timing call counts differ from calibration')
    if seen != set(observed):
        raise ValueError('Missing calibration')
