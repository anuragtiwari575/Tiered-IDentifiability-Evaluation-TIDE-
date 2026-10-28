# Cross-release linkage: sensitivity to the threshold rule

Output of `code/link_threshold_audit.py --cache-root . --out tide_extras`, run on the analysis
machine against the existing feature caches. Counts and concordance only; no subject identifiers.

The decision threshold tau gates the pixel score; the other three representations contribute only
votes to the agreement criterion (>= 3 of 4 choosing the same gallery subject). Rules marked
"uses queries" compute tau partly from the query-gallery scores, so tau is not independent of the
data it is applied to; they are shown for comparison only.

```
variant                           rule      tau  n_agree_ge3  queries_above_tau  n_linked  calibration_recall_at_tau  sex_agreement  median_abs_age_diff
 masked   agreement only, no threshold     -inf          103                144       103                     1.0000            1.0                  0.0
 masked     calibration impostors, q99 0.714517          103                 94        91                     1.0000            1.0                  0.0
 masked   calibration impostors, q99.9 0.731169          103                 88        86                     1.0000            1.0                  0.0
 masked calibration impostors, maximum 0.739291          103                 83        82                     1.0000            1.0                  0.0
 masked    query-gallery scores, q99.9 0.784016          103                 60        59                     0.9375            1.0                  0.0
 masked  max of the two (as published) 0.784016          103                 60        59                     0.9375            1.0                  0.0
    gfc   agreement only, no threshold     -inf           10                144        10                     1.0000            1.0                  1.0
    gfc     calibration impostors, q99 0.656408           10                  1         1                     0.9375            1.0                  2.0
    gfc   calibration impostors, q99.9 0.704989           10                  0         0                     0.8125            NaN                  NaN
    gfc calibration impostors, maximum 0.756582           10                  0         0                     0.6250            NaN                  NaN
    gfc    query-gallery scores, q99.9 0.496163           10                 40         7                     0.9375            1.0                  0.0
    gfc  max of the two (as published) 0.704989           10                  0         0                     0.8125            NaN                  NaN

random-pair baseline: sex agreement 0.52, median |age difference| 22 y
```

Gallery 416 OASIS-1 subjects; 144 OASIS-2 queries; 16 calibration subjects processed by both
pipelines. Calibration impostor scores: 16 x 415 = 6,640 pairs. Query-gallery scores:
144 x 416 = 59,904 pairs, so its 99.9th percentile is by construction near the 60th highest pair,
which is why the "uses queries" rules return close to 60 regardless of the data.
