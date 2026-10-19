"""Recompute summaries/table from preserved observations or a portable rerun."""

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import median, quantiles

from data_io import ROOT, configuration, load_inputs, read_rows, validate_rows, validate_calibration


def summarize(datasets):
    per_input = []
    for dataset, rows in datasets:
        groups = defaultdict(list)
        for r in rows:
            groups[(r['distribution'], int(r['size']), int(r['sample']))].append(float(r['ns_per_call']))
        for (d, n, s), values in sorted(groups.items()):
            per_input.append(dict(dataset=dataset, distribution=d, size=n, sample=s,
                                  batches=len(values), median_ns=median(values)))
    groups = defaultdict(list)
    for r in per_input:
        groups[(r['dataset'], r['distribution'], r['size'])].append(r['median_ns'])
    summary = []
    for (dataset, d, n), values in sorted(groups.items()):
        q1, _, q3 = quantiles(values, n=4, method='inclusive') if len(values)>1 else [values[0]]*3
        summary.append(dict(dataset=dataset, distribution=d, size=n, algorithm='bubble',
                            inputs=len(values), median_ns=median(values), q1_ns=q1, q3_ns=q3))
    return per_input, summary


def write_csv(path, rows):
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def table(summary):
    values = {(r['dataset'],r['distribution']):r['median_ns']/1e6 for r in summary if r['size']==2000}
    datasets = sorted({r['dataset'] for r in summary if r['size']==2000})
    if not datasets:
        return 'This rerun does not include the article size n=2,000.\n'
    lines = ['| Order | '+' | '.join(d+' (ms)' for d in datasets)+' |',
             '| --- | '+' | '.join('---:' for _ in datasets)+' |']
    for order, label in [('paired_shuffled','Shuffled'),('paired_sorted','Sorted'),('paired_reversed','Reversed')]:
        lines.append('| '+label+' | '+' | '.join(f'{values[(d,order)]:.4g}' for d in datasets)+' |')
    return '\n'.join(lines)+'\n'


def analyze(output, run=None):
    config = configuration(); fixtures = load_inputs(); datasets = []
    if run:
        metadata = json.loads((run/'metadata.json').read_text())
        if metadata['status'] != 'complete':
            raise ValueError('Rerun incomplete or failed')
        for name,digest in metadata['artifacts_sha256'].items():
            if hashlib.sha256((run/name).read_bytes()).hexdigest()!=digest:raise ValueError('Rerun evidence changed')
        dataset, settings = metadata['dataset'], metadata['settings']
        rows = read_rows(run/'measurements.csv')
        validate_rows(rows,dataset,fixtures,settings)
        validate_calibration(run/'calibration.jsonl',rows,dataset,fixtures,settings)
        datasets.append((dataset,rows))
    else:
        for dataset in config['datasets']:
            rows = read_rows(ROOT/'data'/f'{dataset}-measurements.csv')
            validate_rows(rows,dataset,fixtures,config['settings'])
            validate_calibration(ROOT/'data'/f'{dataset}-calibration.jsonl',rows,dataset,fixtures,config['settings'])
            datasets.append((dataset,rows))
    inputs, summary = summarize(datasets)
    output.mkdir(parents=True,exist_ok=False)
    write_csv(output/'input-medians.csv',inputs); write_csv(output/'summary.csv',summary)
    (output/'article-table.md').write_text(table(summary))
    (output/'analysis.json').write_text(json.dumps(dict(datasets=[d for d,r in datasets],
        successful_batches=sum(len(r) for d,r in datasets),batches_below_target=sum(r['target_met']=='False' for d,rows in datasets for r in rows),
        method='median of batch-average times per input; median and inclusive IQR across inputs; datasets separate',
        uncertainty='descriptive IQR, not a confidence interval',
        evidence='new portable rerun' if run else 'preserved historical observations'),indent=2)+'\n')
    print(f'Validated {sum(len(r) for d,r in datasets)} batches; wrote {len(summary)} groups')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--run',type=Path)
    args=parser.parse_args(); analyze(args.output,args.run)
