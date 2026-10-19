import csv
import gc
import itertools
import unittest

from bubble_sort import bubble_sort
from measurement import timed_batch
from analyze import summarize
from data_io import ROOT,configuration,load_inputs,read_rows,validate_rows,validate_calibration


class BundleChecks(unittest.TestCase):
    def test_exhaustive_small_sort_and_nonmutation(self):
        for n in range(7):
            for values in itertools.product((-1,0,1),repeat=n):
                original=list(values);out=bubble_sort(original)
                self.assertEqual(out,sorted(values));self.assertEqual(original,list(values));self.assertIsNot(out,original)

    def test_comparison_formulas_and_examples(self):
        class Counted(int):
            comparisons=0
            def __gt__(self,other):
                Counted.comparisons+=1;return int.__gt__(self,other)
        for n in (3,5,10,100):
            for values,expected in [(range(n),n-1),(range(n-1,-1,-1),n*(n-1)//2)]:
                Counted.comparisons=0;bubble_sort([Counted(v) for v in values])
                self.assertEqual(Counted.comparisons,expected)
        for values,expected in [([2,1,3],3),([2,3,4,5,1],10)]:
            Counted.comparisons=0;bubble_sort([Counted(v) for v in values]);self.assertEqual(Counted.comparisons,expected)

    def test_gc_state_restored_after_success_and_failure(self):
        before=gc.isenabled()
        try:
            for enabled in (True,False):
                gc.enable() if enabled else gc.disable()
                timed_batch(bubble_sort,(2,1),[1,2],2)
                self.assertEqual(gc.isenabled(),enabled)
                def fail(values):raise RuntimeError('controlled failure')
                with self.assertRaises(RuntimeError):timed_batch(fail,(2,1),[1,2],1)
                self.assertEqual(gc.isenabled(),enabled)
        finally:gc.enable() if before else gc.disable()

    def test_all_recorded_inputs_and_batches(self):
        inputs=load_inputs(regenerate=True);config=configuration()
        self.assertEqual(len(inputs),240)
        for dataset in config['datasets']:
            rows=read_rows(ROOT/'data'/f'{dataset}-measurements.csv')
            self.assertEqual(len(rows),600)
            validate_rows(rows,dataset,inputs,config['settings'])
            validate_calibration(ROOT/'data'/f'{dataset}-calibration.jsonl',rows,dataset,inputs,config['settings'])

    def test_invalid_measurements_rejected(self):
        config=configuration();inputs=load_inputs();dataset='dataset-1'
        rows=read_rows(ROOT/'data/dataset-1-measurements.csv')
        for changed in [rows[:-1],rows+[rows[0]], [dict(r,input_sha256='wrong') if i==0 else r for i,r in enumerate(rows)], [dict(r,target_met='False') if i==0 else r for i,r in enumerate(rows)]]:
            with self.assertRaises(ValueError):validate_rows(changed,dataset,inputs,config['settings'])

    def test_batch_repeats_are_not_extra_input_units(self):
        rows=[]
        for sample,values in [(0,[1,2,3,4,100]),(1,[10,20,30,40,1000])]:
            for v in values:rows.append(dict(distribution='paired_shuffled',size=100,sample=sample,ns_per_call=v))
        per_input,summary=summarize([('synthetic-unit-test',rows)])
        self.assertEqual([r['median_ns'] for r in per_input],[3,30])
        self.assertEqual(summary[0]['median_ns'],16.5);self.assertEqual(summary[0]['inputs'],2)


if __name__=='__main__':unittest.main()
