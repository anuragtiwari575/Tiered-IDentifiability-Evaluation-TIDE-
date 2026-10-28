#!/usr/bin/env python3
"""
time_cluster_bootstrap.py - participant-clustered bootstrap for the time slope.

The matched-pool time analysis in tide_time_matched.py resamples draws, not participants, and a
participant with several later visits contributes a point to every delay bin the visit falls into.
The bins are therefore not independent and the published interval does not carry that dependence.

This script redoes the slope with a cluster bootstrap over participants:

  for each replicate
      resample the OASIS-2 participants with replacement
      keep, in every delay bin, only the participants drawn in this replicate
      draw S distinct participants per bin from what remains, fit the probe on their first visit,
          evaluate on their visit inside the bin
      fit the slope of chance-adjusted identifiability against the mean delay of the bins

A participant is in or out of a replicate consistently across all four bins, so the between-bin
dependence is propagated into the interval. The slope is fitted within OASIS-2 only, over the four
delay bins, so the OASIS-1 short-delay cohort, which is a different population, is not used as an
anchor.

S is lower than in the main analysis because a bootstrap replicate contains about 63% of the
participants and the smallest delay bin has 22. S is matched across bins, so the slope remains
comparable; only the absolute level shifts.

Run from the directory holding tide_time_matched.py and tide_run.py:

    python time_cluster_bootstrap.py --cache-root . --out tide_time_matched

Writes <out>/time_cluster_bootstrap.csv and prints a summary table.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import tide_run as T
import tide_time_matched as TM

CONDS = TM.CONDS
BINS = TM.BINS


def replicate(feat_path, recs, by_bin, S, d_max, design_idx, offsets, seed, is_pix):
    """One cluster-bootstrap replicate. Returns {(d): slope} over the OASIS-2 bins, or None."""
    rng = np.random.default_rng(seed)
    subjects = sorted({j for cand in by_bin for j, _, _ in cand})
    drawn = set(rng.choice(subjects, len(subjects), replace=True).tolist())

    feat = np.load(feat_path, mmap_mode="r")
    xs, ys = [], {}
    for cand in by_bin:
        by_s = {}
        for j, row, y in cand:
            if j in drawn:
                by_s.setdefault(j, []).append((row, y))
        if len(by_s) < S:
            return None
        pick = rng.choice(sorted(by_s), S, replace=False)
        chosen = [by_s[j][rng.integers(len(by_s[j]))] for j in pick]
        o = TM.eval_pairs(feat, [recs[j] for j in pick], [c[0] for c in chosen],
                          design_idx, offsets, int(rng.integers(1 << 31)), is_pix, d_max)
        xs.append(float(np.mean([c[1] for c in chosen])))
        for d in range(d_max + 1):
            v = o.get(("cross", d))
            if v is not None:
                ys.setdefault(d, []).append(float(T.adj(v, S).mean()))
    out = {}
    for d, vals in ys.items():
        if len(vals) == len(by_bin):
            out[d] = float(np.polyfit(np.asarray(xs), np.asarray(vals), 1)[0])
    return out


def main():
    from joblib import Parallel, delayed
    from encode_slices import REGISTRY

    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-root", default=".")
    ap.add_argument("--sheet-dirs", nargs="+", default=["Datasets", "."])
    ap.add_argument("--out", default="tide_time_matched")
    ap.add_argument("--S", type=int, default=12, help="matched pool size for the clustered analysis")
    ap.add_argument("--boot", type=int, default=300, help="cluster-bootstrap replicates")
    ap.add_argument("--max-d", type=int, default=2)
    ap.add_argument("--design", default="sparse", choices=["sparse", "dense"])
    ap.add_argument("--models", nargs="+", default=None, help="default: pixel + all pretrained encoders")
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    t0 = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    T.LOGFILE = out / "time_cluster_log.txt"
    info = {"pixel": ("floor", "pixel"), **{k: (v[4], v[5]) for k, v in REGISTRY.items()}}
    names = a.models or (["pixel"] + list(REGISTRY))
    years, src = TM.load_delays(a.sheet_dirs)
    T.log(f"[cluster] delays for {len(years)} sessions from {src}")

    rows = []
    for cname, (o2dir, _o1dir) in CONDS.items():
        o2dir = Path(a.cache_root) / o2dir
        if not (o2dir / "scans.csv").exists():
            T.log(f"[cluster] {cname}: cache missing, skipped")
            continue
        offsets = json.loads((o2dir / "meta.json").read_text())["offsets"]
        recs2 = TM.mv_records(pd.read_csv(o2dir / "scans.csv"), False)
        K = int(np.load(o2dir / "feats_pixel.npy", mmap_mode="r").shape[1])
        design_idx = np.arange(K) if a.design == "dense" else np.arange(0, K, 2)

        by_bin = [[] for _ in BINS]
        for j, r in enumerate(recs2):
            for v, row in r["visits"].items():
                y = years.get(r["sessions"][v])
                if y is None:
                    continue
                for b, (lo, hi) in enumerate(BINS):
                    if lo <= y < hi:
                        by_bin[b].append((j, row, y))
        n_sub = len({j for cand in by_bin for j, _, _ in cand})
        T.log(f"[cluster] {cname}: {n_sub} participants, bin sizes "
              + ", ".join(str(len({p[0] for p in cand})) for cand in by_bin))

        for m in names:
            fp = o2dir / f"feats_{m}.npy"
            if not fp.exists():
                continue
            t1 = time.time()
            reps = Parallel(n_jobs=a.n_jobs)(
                delayed(replicate)(str(fp), recs2, by_bin, a.S, a.max_d, design_idx, offsets,
                                   a.seed + 7919 * b, m == "pixel")
                for b in range(a.boot))
            ok = [r for r in reps if r]
            for d in range(a.max_d + 1):
                sl = np.array([r[d] for r in ok if d in r])
                if len(sl) < 20:
                    continue
                rows.append(dict(cond=cname, design=a.design, model=m,
                                 group=T.PT_GROUP.get(info[m][1], info[m][1]) if m in info else m,
                                 d_mm=d, S=a.S, n_replicates=len(sl),
                                 slope_per_year=float(np.median(sl)),
                                 lo=float(np.percentile(sl, 2.5)), hi=float(np.percentile(sl, 97.5)),
                                 frac_negative=float((sl < 0).mean()),
                                 significant_decline=bool(np.percentile(sl, 97.5) < 0)))
            T.log(f"[cluster] {cname}/{m}: {len(ok)}/{a.boot} usable replicates ({time.time() - t1:.0f}s)")

    R = pd.DataFrame(rows)
    if R.empty:
        T.log("[cluster] nothing computed - check --cache-root")
        return
    p = out / "time_cluster_bootstrap.csv"
    R.to_csv(p, index=False)

    L = ["# Participant-clustered bootstrap of the time slope", "",
         f"Within OASIS-2 only, {len(BINS)} delay bins, S = {a.S}, {a.boot} cluster-bootstrap replicates, "
         f"{a.design} design. Participants are resampled with replacement and kept or dropped "
         f"consistently across bins, so between-bin dependence is carried into the interval.", ""]
    for cname, g in R.groupby("cond"):
        L += [f"## {cname}", ""]
        pre = g[~g["group"].isin(["pixel", "random"])]
        for d in sorted(g["d_mm"].unique()):
            px = g[(g["model"] == "pixel") & (g["d_mm"] == d)]
            q = pre[pre["d_mm"] == d]
            if px.empty or q.empty:
                continue
            L.append(f"- {d} mm: pixel slope {px['slope_per_year'].iloc[0]:+.4f}/yr "
                     f"[{px['lo'].iloc[0]:+.4f}, {px['hi'].iloc[0]:+.4f}]; "
                     f"encoders median {q['slope_per_year'].median():+.4f}/yr, "
                     f"{int(q['significant_decline'].sum())}/{len(q)} with interval below zero")
        L.append("")
        L += [g.round(4).to_markdown(index=False), ""]
    (out / "REPORT_TIME_CLUSTER.md").write_text("\n".join(L), encoding="utf-8")
    T.log(f"[cluster] wrote {p} and REPORT_TIME_CLUSTER.md ({(time.time() - t0) / 60:.1f} min)")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main()
