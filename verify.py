"""Check the exact file manifest, published inputs, observations and summaries."""

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath

from analyze import summarize,table
from data_io import ROOT,configuration,load_inputs,read_rows,validate_rows,validate_calibration


def verify(regenerate=False):
    manifest=json.loads((ROOT/'MANIFEST.json').read_text())
    expected=set(manifest['files'])|{'MANIFEST.json'}
    observed={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.relative_to(ROOT).parts[0] != '.git'}
    if observed!=expected:raise ValueError('Unexpected or missing payload files')
    for name,entry in manifest['files'].items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or (ROOT/name).is_symlink():raise ValueError('Unsafe payload path')
        content=(ROOT/name).read_bytes()
        if len(content)!=entry['bytes'] or hashlib.sha256(content).hexdigest()!=entry['sha256']:
            raise ValueError(f'File integrity mismatch: {name}')
    config=configuration();fixtures=load_inputs(regenerate);datasets=[]
    for dataset in config['datasets']:
        rows=read_rows(ROOT/'data'/f'{dataset}-measurements.csv')
        validate_rows(rows,dataset,fixtures,config['settings'])
        validate_calibration(ROOT/'data'/f'{dataset}-calibration.jsonl',rows,dataset,fixtures,config['settings'])
        datasets.append((dataset,rows))
    per_input,summary=summarize(datasets)
    for filename,calculated in [('input-medians.csv',per_input),('summary.csv',summary)]:
        with (ROOT/'results'/filename).open() as f:saved=list(csv.DictReader(f))
        if len(saved)!=len(calculated) or any(any(str(v)!=r[k] for k,v in c.items()) for r,c in zip(saved,calculated)):
            raise ValueError(f'Derived summary mismatch: {filename}')
    if (ROOT/'results/article-table.md').read_text()!=table(summary):raise ValueError('Article table mismatch')
    print(f'Verified {len(expected)} files, {len(fixtures)} inputs, {sum(len(r) for d,r in datasets)} historical batches and all summaries')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--regenerate-inputs',action='store_true',help='Also compare seeded regeneration; use recorded Python version')
    verify(p.parse_args().regenerate_inputs)
