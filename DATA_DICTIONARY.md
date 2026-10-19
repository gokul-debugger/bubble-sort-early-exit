# Data dictionary

`dataset-1` uses master seed 20261020; `dataset-2` uses 20261021. Filenames keep the
datasets separate. No timing observations from other algorithms are exported.

## Measurement CSVs (600 rows per dataset)

| Column | Meaning |
| --- | --- |
| distribution | paired_shuffled, paired_sorted or paired_reversed |
| size | Number of distinct integers |
| sample | Base-set index 0..9, shared across three orders |
| input_seed | SHA-256-derived seed for the base set |
| input_sha256 | Hash of the compact JSON array of this ordered input |
| algorithm | Always bubble |
| repeat | Technical batch index 0..4 |
| order | Original method position 0..4 within the interleaved repeat; 0 for a Bubble-only rerun |
| calls | Number of sorting calls in this batch |
| elapsed_ns | Total measured batch wall time, nanoseconds |
| ns_per_call | elapsed_ns divided by calls; a batch average, not an individual-call latency |
| target_met | Whether elapsed_ns reached the 3,000,000 ns target |
| status | All historical exports are ok; rerun failures are retained as failed |
| reason | Empty for successful observations |
| pair_id | master-seed:size:sample; same set across orders |
| shuffle_seed | SHA-256-derived shuffle seed |
| multiset_sha256 | Hash of the canonical sorted array; shared across orders |

Seed integers may exceed JavaScript's exact Number range. Keep their CSV strings
or use arbitrary-precision integers, as the supplied Python code does.

## Calibration JSONL (120 records per dataset)

Each record holds distribution/size/sample, input provenance, algorithm and a
`trials` array of `{calls, elapsed_ns}` attempts. The final trial chooses the call
count used by all five measured batches for that input. Calibration timings are
not included in summary medians.

## Input fixtures JSONL (240 records)

Each record adds `dataset` and an explicit `values` array to size/order/sample and
seed/hash provenance. Each order has the same n distinct values within a pair.
The exact fixtures support rerunning without relying only on seed regeneration.

## Derived files

`input-medians.csv`: dataset/order/size/sample, batch count and median_ns.
`summary.csv`: dataset/order/size/algorithm, input count, median_ns, q1_ns, q3_ns.
The quartiles use inclusive sample quantiles across input medians. `article-table.md`
converts the n=2,000 medians to milliseconds and rounds to four significant digits.
`analysis.json` records the scope and descriptive method.
