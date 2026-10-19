# Methods and limitations

## Historical data

Two separate datasets use master seeds 20261020 and 20261021. These integers are
seeds, not dates. For each size n in 100, 500, 1,000 and 2,000, ten sets of n
unique integers were sampled without replacement from [-10n, 10n], inclusive.
Each set appears as a seeded shuffle, ascending tuple and exact reverse. The
canonical sorted-value hash checks matching values across all three orders.

Each dataset has 40 base sets, 120 ordered inputs, 600 Bubble timing batches and
120 Bubble calibration records. All 1,200 exported historical batches succeeded;
there are no excluded or below-target Bubble batches. Other algorithms' results
and private research material are outside this bundle's scope.

The full historical benchmark interleaved five methods. Export selection is
algorithm == bubble, across every size/order/input/repeat in both datasets. No
Bubble seed/input was chosen by its outcome. Schedule position 0..4 is retained
in `order`. A Bubble-only dataset cannot independently reconstruct the full
historical cross-method schedule or its effects on cache/thermal state.

## Timing boundaries

The recorded environment was CPython 3.12.13, macOS 27.0.1, ARM64, an Apple M1 Pro
with 16 GB RAM and eight logical CPUs. These are reproducibility specifications;
no hardware serial number, device UUID, account name or hostname is included.

The function copies the input and returns a new list; copying/allocation are timed.
One correctness-checked warmup precedes calibration. Calibration starts with one
call, scales toward a 3,000,000 ns batch target, and caps at 10,000 calls. The soft
calibration limit is one second per call, checked after execution rather than by
interrupting a sort. A batch uses `time.perf_counter_ns()` with Python GC disabled
and restores the caller's previous GC state. The final result is validated outside
the timer; the input is an immutable tuple. Five measured batches follow each
calibration. `ns_per_call = elapsed_ns / calls`; calibration is excluded from summaries.

These are warm repeated-call measurements. They do not characterize cold caches,
first-call latency, peak memory, energy or application-level latency. Background
activity, scheduling and thermal/power conditions were not controlled. Randomized
measurement order cannot guarantee identical machine state between observations.
No causal hardware-counter attribution or universal speed ranking is claimed.

## Analysis

Within each ordered input, take the median of its five batch averages. Within
each dataset/order/size, report the median and inclusive interquartile range across
ten input-level medians. Technical batches are not additional independent inputs.
Keep the two datasets separate. The IQR is descriptive, not a confidence interval;
no p-value, outlier removal or statistical significance claim is made.

`results/summary.csv` contains 24 groups (2 datasets x 3 orders x 4 sizes).
`results/input-medians.csv` contains 240 input medians. The article and chart use
the six n=2,000 groups. The figure uses a logarithmic time axis; some IQR whiskers
are hidden by markers. Count formulas describe the actual loop structure, not
an estimate obtained from milliseconds.

## Portable reruns

`benchmark.py` is a new driver using the extracted original function, timer and
calibrator, and the saved input fixtures. It runs only Bubble Sort. Its metadata
labels `bubble_only_rerun_v1`, uses schedule position zero, and records basic
Python/OS/architecture and code hashes without collecting host/account identifiers,
Git history, full environment dumps or absolute command/workspace paths.

Its output is new evidence and must not be substituted for the historical files.
Exact input hashes and summary calculations are reproducible; exact elapsed times
and the full historical interleaving are not. Rerun flags permit small engineering
checks; the default covers all saved Bubble conditions for one dataset.
