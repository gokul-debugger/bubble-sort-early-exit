"""Regenerate the article chart from a validated combined summary CSV."""

import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(summary,output):
    with summary.open() as f:all_rows=list(csv.DictReader(f))
    orders=['paired_shuffled','paired_sorted','paired_reversed']
    series=[]
    for dataset in ['dataset-1','dataset-2']:
        selected={r['distribution']:r for r in all_rows if r['dataset']==dataset and r['size']=='2000' and r['algorithm']=='bubble'}
        series.append([selected[o] for o in orders])
    output.mkdir(parents=True,exist_ok=False)
    HERE=output
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'first-post-bubble-v1','savefig.facecolor':'white'})
    fig,axes=plt.subplots(1,2,figsize=(10,4.4),layout='constrained',sharex=True,sharey=True)
    lo=min(float(r['q1_ns']) for group in series for r in group)/1e6/3
    hi=max(float(r['q3_ns']) for group in series for r in group)/1e6*5
    for i,(ax,rows) in enumerate(zip(axes,series)):
        for position,r in enumerate(rows):
            center,q1,q3=(float(r[k])/1e6 for k in ('median_ns','q1_ns','q3_ns'))
            ax.errorbar(center,position,xerr=[[center-q1],[q3-center]],fmt='o',color='#4169b1',capsize=4,markersize=7)
            ax.annotate(f'{center:.4g} ms',(q3,position),xytext=(9,0),textcoords='offset points',va='center')
        ax.set(title=f'Dataset {i+1}',xscale='log',xlabel='Median time per call (ms, log scale)',xlim=(lo,hi),ylim=(2.6,-.6))
        ax.set_yticks(range(3),['Shuffled','Sorted','Reversed']);ax.grid(axis='x',alpha=.2)
    fig.suptitle('Bubble Sort with early exit · same 2,000 values in three orders\nDots: medians; whiskers: descriptive IQR across ten sets',fontsize=14)
    fig.savefig(HERE/'first-post-bubble.png',dpi=180)
    fig.savefig(HERE/'first-post-bubble.svg',metadata={'Date':None})
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--summary',type=Path,default=Path(__file__).resolve().parent/'results/summary.csv')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();plot(a.summary,a.output)
