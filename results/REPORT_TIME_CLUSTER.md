# Participant-clustered bootstrap of the time slope

Output of `code/time_cluster_bootstrap.py --cache-root . --out tide_time_matched`, run on the
analysis machine (10.4 min). Within OASIS-2 only, 4 delay bins, S = 12, 300 cluster-bootstrap
replicates, sparse design. Participants are resampled with replacement and kept or dropped
consistently across bins, so between-bin dependence is carried into the interval. 261 of 300
replicates were usable; the rest were discarded because a delay bin held fewer than 12 of the
resampled participants. The slope is fitted over the four OASIS-2 bins only, so the OASIS-1
short-delay cohort is not used as an anchor.

## reg (registered, skull present)

- 0 mm: pixel slope -0.0066/yr [-0.0613, +0.0600]; encoders median -0.0060/yr, 0/30 with interval below zero
- 1 mm: pixel slope -0.0034/yr [-0.0625, +0.0623]; encoders median -0.0051/yr, 0/30 with interval below zero
- 2 mm: pixel slope -0.0039/yr [-0.0609, +0.0628]; encoders median -0.0005/yr, 0/30 with interval below zero

## regmask (registered, skull-stripped)

- 0 mm: pixel slope -0.0041/yr [-0.0441, +0.0202]; encoders median -0.0100/yr, 0/30 with interval below zero
- 1 mm: pixel slope -0.0053/yr [-0.0404, +0.0192]; encoders median -0.0098/yr, 0/30 with interval below zero
- 2 mm: pixel slope -0.0062/yr [-0.0465, +0.0237]; encoders median -0.0064/yr, 0/30 with interval below zero

Per-encoder values are in `time_cluster_bootstrap.csv` (columns: cond, design, model, group, d_mm,
S, n_replicates, slope_per_year, lo, hi, frac_negative, significant_decline).

Comparison with the draw-level bootstrap over five points (REPORT_TIME.md), which included the
OASIS-1 anchor and resampled draws rather than participants:

| Condition | d | Draw-level, 5 points | Participant-clustered, OASIS-2 only |
|:---|:--|:---|:---|
| skull-stripped | 0 mm | 8/30 encoders declining | 0/30 |
| skull-stripped | 1 mm | 0/30 | 0/30 |
| skull-stripped | 2 mm | 0/30 | 0/30 |
| skull present | 0 mm | 19/30 (sparse), 24/30 (dense) | 0/30 |
| skull present | 1 mm | 15/30 (sparse), 28/30 (dense) | 0/30 |
| skull present | 2 mm | 14/30 (sparse), 22/30 (dense) | 0/30 |

The with-skull declines do not survive either change. Two causes are confounded in the earlier
figure: the OASIS-1 to OASIS-2 step is a cohort difference as well as a time difference, and the
draw-level interval did not carry the dependence between delay bins.
