#!/usr/bin/env python3
"""
Sanity check: are OASIS-1 MR1 and MR2 processed (T88) volumes genuinely different acquisitions?

For every reliability subject (MR1 + MR2) and both variants it reports:
  same_md5            .img files byte-identical?
  identical_voxels    voxel arrays exactly equal?
  corr_MR1_MR2        voxel correlation between the two sessions (same subject)
  corr_MR1_others     mean correlation of MR1 with 3 other subjects' MR1 (reference)
  rel_abs_diff        mean |MR1 - MR2| / mean |MR1|

Expected if the data are fine: same_md5 = False, identical_voxels = False,
corr_MR1_MR2 high but < 1, clearly above corr_MR1_others.

Usage:
  python check_t88_pairs.py tide_oasis1\\index_t88.csv
"""
import hashlib
import sys

import nibabel as nib
import numpy as np
import pandas as pd


def vol(p):
    return np.squeeze(nib.load(p).get_fdata(dtype=np.float32))


def md5(p):
    with open(p[:-4] + ".img", "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def corr(a, b, mask):
    return float(np.corrcoef(a[mask], b[mask])[0, 1])


def main():
    idx = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "tide_oasis1/index_t88.csv")
    for var in ["t88_masked", "t88_gfc"]:
        d = idx[idx["variant"] == var]
        rel = [s for s, g in d.groupby("subject") if g["visit"].nunique() >= 2]
        others = list(d[d["visit"] == 1]["subject"].unique())
        rows = []
        for s in rel:
            g = d[d["subject"] == s].sort_values("visit")
            p1, p2 = g["path"].iloc[0], g["path"].iloc[1]
            v1, v2 = vol(p1), vol(p2)
            m = (v1 > 0) | (v2 > 0)
            ref = [x for x in others if x != s][:3]
            co = np.mean([corr(v1, vol(d[(d["subject"] == x) & (d["visit"] == 1)]["path"].iloc[0]), m) for x in ref])
            rows.append(dict(subject=s, same_md5=md5(p1) == md5(p2), identical_voxels=bool(np.array_equal(v1, v2)),
                             corr_MR1_MR2=round(corr(v1, v2, m), 4), corr_MR1_others=round(float(co), 4),
                             rel_abs_diff=round(float(np.abs(v1 - v2).mean() / (np.abs(v1).mean() + 1e-6)), 4)))
        df = pd.DataFrame(rows)
        print(f"\n== {var}: {len(rel)} subjects with MR1 + MR2")
        print(df.to_string(index=False))
        print(f"   any byte-identical: {df['same_md5'].any()} | any voxel-identical: {df['identical_voxels'].any()} "
              f"| median corr MR1-MR2 {df['corr_MR1_MR2'].median():.4f} vs other subjects {df['corr_MR1_others'].median():.4f}")


if __name__ == "__main__":
    main()
