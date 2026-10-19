# Bubble Sort’s Early Exit: code and data

Gokul Krishna · educational computational experiment.

This bundle accompanies “Bubble Sort’s Early Exit: Why Input Order Matters.” It
contains only the Bubble Sort implementation, synthetic paired inputs, its recorded
timings/calibration, analysis and figure. These observations illustrate an early
exit and measurement practice; they are not a novelty or peer-reviewed publication
claim. See `RIGHTS.md` for licensing: MIT for code; CC BY 4.0 for data,
documentation and figures. Release: v1.0.1.

## What is here

- `bubble_sort.py`: the measured copying implementation, extracted without a body change.
- `workloads.py`: the paired generator and stable seed/hash helpers.
- `measurement.py`: the original timer/calibrator functions, without workspace tooling.
- `benchmark.py`: a new, portable Bubble-only rerun driver.
- `data_io.py`, `analyze.py`, `plot.py`, `verify.py`: validation, summaries, chart and integrity checks.
- `tests/test_bundle.py`: correctness, count, GC-state, input/provenance and aggregation checks.
- `data/`: both datasets' original Bubble-only timing/calibration records and all exact inputs.
- `results/`: regenerated input medians, summaries and the article table.
- `figures/`: the article PNG and SVG, plus figure provenance.
- `METHODS.md`, `DATA_DICTIONARY.md`, `PROVENANCE.json`, `config.json`: interpretation and settings.
- `requirements-figures.txt`: pinned optional plotting dependencies; analysis uses only the standard library.
- `MANIFEST.json`: exact payload inventory, byte counts and SHA-256 hashes (excluding itself).
- `LICENSE`, `LICENSE-CC-BY-4.0.txt`, `RIGHTS.md`: license terms and their scope.

## Verify and reproduce saved results

Use the recorded CPython 3.12.13 environment when possible. Run from this directory.
The first four commands need no third-party packages or network access:

```sh
python3.12 -m venv /tmp/bubble-review-env
/tmp/bubble-review-env/bin/python verify.py --regenerate-inputs
/tmp/bubble-review-env/bin/python -m unittest discover -s tests -v
/tmp/bubble-review-env/bin/python analyze.py --output /tmp/bubble-summary
```

Use new output paths: existing output directories are never replaced. Seed
regeneration is an additional check; `verify.py` without that flag checks the exact
saved fixtures and hashes without depending on a future PRNG sampling implementation.

To regenerate the chart:

```sh
/tmp/bubble-review-env/bin/python -m pip install -r requirements-figures.txt
/tmp/bubble-review-env/bin/python plot.py --summary /tmp/bubble-summary/summary.csv --output /tmp/bubble-figures
```

The pinned figure environment was used on macOS ARM64/Python 3.12.13. Other platforms
may need compatible wheels; record any dependency changes. The supplied figure can
also be viewed without installing plotting dependencies.

## Collect a new timing run

A small engineering run:

```sh
/tmp/bubble-review-env/bin/python benchmark.py --dataset dataset-1 --size 100 --inputs 1 --repeats 2 --output /tmp/bubble-smoke
/tmp/bubble-review-env/bin/python analyze.py --run /tmp/bubble-smoke --output /tmp/bubble-smoke-summary
```

Omit `--size`, `--inputs` and `--repeats` for all 600 Bubble batches in that dataset.
Use `dataset-2` and a different output directory for the second dataset. New wall
clock times will differ. Do not overwrite or pool them with historical observations.

**Collection context matters:** historical Bubble observations were interleaved
with four other sorting methods. Their original `order` positions are retained.
This driver runs only Bubble Sort and does not reconstruct that cross-method
schedule. It reproduces the exact input values, function, calibration rules and
timing boundaries. See `METHODS.md` for this limitation and the summary procedure.

## Article-size results

At n=2,000, median milliseconds per call (rounded):

| Order | Dataset 1 | Dataset 2 |
| --- | ---: | ---: |
| Shuffled | 112.7 | 112.6 |
| Sorted | 0.06917 | 0.07046 |
| Reversed | 140.6 | 141 |

The linear best-case comparison count is n−1 for an already sorted input of n≥2
values; descending distinct inputs make n(n−1)/2 comparisons. Those formulas are
not elapsed-time ratios. Swaps, copying and interpreter/machine costs also matter.

AI tools assisted with code, experiments, analysis and documentation. The named author remains
responsible for reviewing the scientific content and any publication.
