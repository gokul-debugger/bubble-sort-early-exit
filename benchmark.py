"""Bubble-only rerun on exact saved inputs; historical interleaving is not reproduced."""

import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import sys

from bubble_sort import bubble_sort
from data_io import ROOT,FIELDS,PROVENANCE,configuration,load_inputs
from measurement import calibrate,timed_batch


def run(dataset,output,size=None,inputs=None,repeats=None):
    config=configuration(); settings=dict(config['settings'])
    if dataset not in config['datasets']:raise ValueError('Unknown dataset')
    if size is not None:
        if size not in settings['sizes']:raise ValueError('Size outside saved inputs')
        settings['sizes']=[size]
    if inputs is not None:
        if not 1<=inputs<=settings['inputs']:raise ValueError('Invalid input count')
        settings['inputs']=inputs
    if repeats is not None:
        if repeats<1:raise ValueError('Repeats must be positive')
        settings['repeats']=repeats
    settings['methods_per_repeat']=1
    fixtures=load_inputs()
    blocks=[r for (ds,d,n,s),r in fixtures.items() if ds==dataset and n in settings['sizes'] and s<settings['inputs']]
    random.Random(config['datasets'][dataset]['master_seed']).shuffle(blocks)
    if sys.gettrace() is not None:raise RuntimeError('Refusing an instrumented timing run')
    output.mkdir(parents=True,exist_ok=False)
    metadata=dict(status='running',dataset=dataset,settings=settings,
        collection_design='bubble_only_rerun_v1',
        comparison='same inputs and timer boundaries; not the original five-method schedule',
        started_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),
        os=platform.system(),os_release=platform.release(),architecture=platform.machine(),
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['bubble_sort.py','workloads.py','measurement.py','benchmark.py']})
    (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    totals=dict(ok=0,failed=0,skipped=0)
    try:
        with (output/'measurements.csv').open('x',newline='') as raw, (output/'calibration.jsonl').open('x') as cal:
            writer=csv.DictWriter(raw,fieldnames=FIELDS);writer.writeheader()
            for fixture in blocks:
                values=tuple(fixture['values']); expected=sorted(values)
                base={k:fixture[k] for k in ['distribution','size','sample']+PROVENANCE}
                for _ in range(settings['warmups']):
                    if bubble_sort(values)!=expected:raise AssertionError('Incorrect warmup')
                calls,trials=calibrate(bubble_sort,values,expected,settings)
                cal.write(json.dumps(dict(base,algorithm='bubble',trials=trials))+'\n')
                for repeat in range(settings['repeats']):
                    row=dict(base,algorithm='bubble',repeat=repeat,order=0,calls=calls)
                    try:
                        elapsed=timed_batch(bubble_sort,values,expected,calls)
                        row.update(elapsed_ns=elapsed,ns_per_call=elapsed/calls,
                            target_met=elapsed>=settings['target_batch_ns'],status='ok',reason='')
                        totals['ok']+=1
                    except BaseException as exc:
                        row.update(status='failed',reason=type(exc).__name__)
                        totals['failed']+=1;writer.writerow(row);raw.flush();raise
                    writer.writerow(row)
                raw.flush();cal.flush()
        metadata['status']='complete'
    except BaseException as exc:
        metadata.update(status='aborted',error_type=type(exc).__name__);raise
    finally:
        metadata.update(finished_utc=datetime.now(timezone.utc).isoformat(),totals=totals,
            artifacts_sha256={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in ['measurements.csv','calibration.jsonl'] if (output/name).exists()})
        (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(f'Completed {totals["ok"]} new batches in {output}')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--size',type=int);p.add_argument('--inputs',type=int);p.add_argument('--repeats',type=int)
    a=p.parse_args();run(a.dataset,a.output,a.size,a.inputs,a.repeats)
