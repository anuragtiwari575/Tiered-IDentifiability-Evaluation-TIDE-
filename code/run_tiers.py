#!/usr/bin/env python3
"""
Step 3 - Redundancy-tier identity probe (pilot, frozen features).

Fixed n_fit: the probe is always fit on K reference slices (offset 0) of the
FIRST scan of the FIRST session of each subject. The same fitted probe is then
evaluated on eval sets that differ only in their relation to the fit data:

  same_scan_adjacent  same scan, slice +1                 near-duplicate
  same_scan_far       same scan, slice +far offset        same acquisition, other anatomy
  repeat_scan         other mpr-N of the same session     new acquisition, same sitting
  rescan_90d          OASIS-1 MR2 reliability session     (OASIS1_reliability pool only)
  next_visit          OASIS-2 second visit                months-years later

Pools: OASIS1_all, OASIS1_reliability (20 subj), OASIS2.
Probes: multinomial logistic regression and cosine 1-NN.
Pool size is controlled by subsampling subjects (default 20, 50) plus the full
pool, so chance level is matched across pools. Accuracy is also reported
chance-adjusted: (acc - 1/S) / (1 - 1/S).

CIs: subsampled pools -> 2.5/97.5 percentiles across repeats;
     full pool        -> subject-level bootstrap (1000x).

Usage:
  python run_tiers.py --feats feats/ --out results/
"""
import argparse
import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from joblib import Parallel, delayed  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.exceptions import ConvergenceWarning  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

warnings.filterwarnings("ignore", category=ConvergenceWarning)

TIER_ORDER = ["same_scan_adjacent", "same_scan_far", "repeat_scan", "rescan_90d", "next_visit"]
BASE = TIER_ORDER[:3]


def adj(acc, s):
    return (acc - 1.0 / s) / (1.0 - 1.0 / s)


def build_pools(scans, offsets, off_far):
    o0, o1, of = offsets.index(0), offsets.index(1), offsets.index(off_far)
    ok = scans[scans["ok"].astype(bool)]
    pools = {}
    for ds in sorted(ok["dataset"].unique()):
        recs = []
        for subj, g in ok[ok["dataset"] == ds].groupby("subject"):
            sess = sorted(g["session"].unique(), key=lambda s: int(s.split("_MR")[-1]))
            first = g[g["session"] == sess[0]].sort_values("scan")
            if len(first) < 2:
                continue
            a_row, b_row = int(first.index[0]), int(first.index[1])
            tiers = {"same_scan_adjacent": (a_row, o1),
                     "same_scan_far": (a_row, of),
                     "repeat_scan": (b_row, o0)}
            if len(sess) > 1:
                nxt = int(g[g["session"] == sess[1]].sort_values("scan").index[0])
                tiers["rescan_90d" if ds == "OASIS1" else "next_visit"] = (nxt, o0)
            recs.append({"subject": subj, "fit": (a_row, o0), "tiers": tiers})
        if ds == "OASIS1":
            pools["OASIS1_all"] = (recs, BASE)
            rel = [r for r in recs if "rescan_90d" in r["tiers"]]
            if rel:
                pools["OASIS1_reliability"] = (rel, BASE + ["rescan_90d"])
        else:
            vis = [r for r in recs if "next_visit" in r["tiers"]]
            if vis:
                pools[ds] = (vis, BASE + ["next_visit"])
    return pools


def gather(feat, recs, tier=None):
    X, y = [], []
    for j, r in enumerate(recs):
        row, oi = r["fit"] if tier is None else r["tiers"][tier]
        x = np.asarray(feat[row, :, oi, :], dtype=np.float32)       # K, D
        X.append(x)
        y.append(np.full(len(x), j))
    return np.concatenate(X), np.concatenate(y)


def run_one(feat, recs, tiers, is_pixel, seed):
    """Fit once on the fixed fit set, evaluate every tier. Returns tier -> probe -> per-subject acc."""
    Xf, yf = gather(feat, recs)
    scaler = StandardScaler().fit(Xf)
    if is_pixel:
        ncomp = int(min(256, Xf.shape[0] - 1, Xf.shape[1]))
        pca = PCA(n_components=ncomp, random_state=seed).fit(scaler.transform(Xf))
        def tf(X):
            return pca.transform(scaler.transform(X))
    else:
        def tf(X):
            return scaler.transform(X)
    Zf = tf(Xf)
    clf = LogisticRegression(C=1.0, max_iter=3000).fit(Zf, yf)
    Zfn = Zf / np.clip(np.linalg.norm(Zf, axis=1, keepdims=True), 1e-8, None)
    S = len(recs)
    out = {}
    for t in tiers:
        Xe, ye = gather(feat, recs, t)
        Ze = tf(Xe)
        Zen = Ze / np.clip(np.linalg.norm(Ze, axis=1, keepdims=True), 1e-8, None)
        preds = {"logreg": clf.predict(Ze), "1nn": yf[np.argmax(Zen @ Zfn.T, axis=1)]}
        out[t] = {}
        for probe, p in preds.items():
            hit = (p == ye).astype(float)
            out[t][probe] = np.bincount(ye, weights=hit, minlength=S) / np.bincount(ye, minlength=S)
    return out


def subsample_run(feat, recs, tiers, is_pixel, s, seed):
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(recs), size=s, replace=False)
    return run_one(feat, [recs[i] for i in pick], tiers, is_pixel, seed)


def plot_pool(summary, pool, tiers, models, size, path):
    """Heatmap: rows = models (sorted by the hardest tier), cols = tiers, cell = chance-adjusted acc."""
    d = summary[(summary["pool"] == pool) & (summary["size"] == size) & (summary["probe"] == "logreg")]
    if d.empty:
        return
    tab = d.pivot(index="model", columns="tier", values="mean_adj").reindex(columns=tiers)
    tab = tab.reindex([m for m in models if m in tab.index])
    tab = tab.sort_values(tiers[-1], ascending=False)
    fig, ax = plt.subplots(figsize=(1.6 * len(tiers) + 3.5, 0.32 * len(tab) + 1.5))
    im = ax.imshow(tab.values, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels([t.replace("_", "\n") for t in tiers], fontsize=8)
    ax.set_yticks(range(len(tab)))
    ax.set_yticklabels(tab.index, fontsize=7)
    for r in range(tab.shape[0]):
        for c in range(tab.shape[1]):
            v = tab.values[r, c]
            if np.isfinite(v):
                ax.text(c, r, f"{v:.2f}", ha="center", va="center", fontsize=6,
                        color="white" if v < 0.6 else "black")
    ax.set_title(f"{pool}: {size} subjects, n_fit fixed (chance-adjusted, logreg)", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.03)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pool-sizes", type=int, nargs="+", default=[20, 50])
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--off-far", type=int, default=None, help="default: largest offset")
    ap.add_argument("--models", nargs="+", default=None)
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--plot-size", type=int, default=20)
    a = ap.parse_args()

    fdir, out = Path(a.feats), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    scans = pd.read_csv(fdir / "scans.csv")
    meta = json.loads((fdir / "meta.json").read_text())
    offsets = meta["offsets"]
    off_far = a.off_far if a.off_far is not None else max(offsets)
    feats = {p.stem[len("feats_"):]: np.load(p, mmap_mode="r") for p in sorted(fdir.glob("feats_*.npy"))}
    models = a.models or (["pixel"] + sorted(k for k in feats if k != "pixel"))

    pools = build_pools(scans, offsets, off_far)
    for name, (recs, tiers) in pools.items():
        print(f"pool {name}: {len(recs)} subjects, tiers {tiers}")

    rng = np.random.default_rng(a.seed)
    runs, summ, per_subj = [], [], []
    for pool, (recs, tiers) in pools.items():
        N = len(recs)
        names = [r["subject"] for r in recs]
        for model in models:
            feat, is_pix = feats[model], model == "pixel"
            print(f"  {pool} / {model}")
            # full pool + subject bootstrap
            res = run_one(feat, recs, tiers, is_pix, a.seed)
            for t in tiers:
                for probe, v in res[t].items():
                    acc = float(v.mean())
                    boot = rng.choice(v, size=(1000, N), replace=True).mean(axis=1)
                    lo, hi = np.percentile(boot, [2.5, 97.5])
                    runs.append(dict(pool=pool, model=model, size=N, repeat=-1, tier=t, probe=probe,
                                     acc=acc, acc_adj=adj(acc, N)))
                    summ.append(dict(pool=pool, model=model, size=N, tier=t, probe=probe,
                                     mean=acc, lo=lo, hi=hi, mean_adj=adj(acc, N),
                                     lo_adj=adj(lo, N), hi_adj=adj(hi, N),
                                     n_runs=1, ci="subject_bootstrap"))
                    per_subj += [dict(pool=pool, model=model, subject=s, tier=t, probe=probe, acc=float(x))
                                 for s, x in zip(names, v)]
            # matched-size subsamples
            for s in a.pool_sizes:
                if s >= N:
                    continue
                seeds = [a.seed * 1000 + r for r in range(a.repeats)]
                outs = Parallel(n_jobs=a.n_jobs)(
                    delayed(subsample_run)(feat, recs, tiers, is_pix, s, sd) for sd in seeds)
                for r, res_r in enumerate(outs):
                    for t in tiers:
                        for probe, v in res_r[t].items():
                            acc = float(v.mean())
                            runs.append(dict(pool=pool, model=model, size=s, repeat=r, tier=t,
                                             probe=probe, acc=acc, acc_adj=adj(acc, s)))
                rr = pd.DataFrame([x for x in runs if x["pool"] == pool and x["model"] == model
                                   and x["size"] == s])
                for (t, probe), g in rr.groupby(["tier", "probe"]):
                    lo, hi = np.percentile(g["acc"], [2.5, 97.5])
                    m = float(g["acc"].mean())
                    summ.append(dict(pool=pool, model=model, size=s, tier=t, probe=probe,
                                     mean=m, lo=lo, hi=hi, mean_adj=adj(m, s),
                                     lo_adj=adj(lo, s), hi_adj=adj(hi, s),
                                     n_runs=len(g), ci="repeat_percentile"))

    runs, summ, per_subj = pd.DataFrame(runs), pd.DataFrame(summ), pd.DataFrame(per_subj)
    runs.to_csv(out / "results_runs.csv", index=False)
    summ.to_csv(out / "summary.csv", index=False)
    per_subj.to_csv(out / "per_subject_full_pool.csv", index=False)

    for pool, (recs, tiers) in pools.items():
        size = a.plot_size if a.plot_size < len(recs) else len(recs)
        plot_pool(summ, pool, tiers, models, size, out / f"tiers_{pool}.png")
        d = summ[(summ["pool"] == pool) & (summ["size"] == size) & (summ["probe"] == "logreg")]
        if not d.empty:
            tab = d.pivot(index="model", columns="tier", values="mean_adj").reindex(models)
            print(f"\n== {pool} (S={size}, logreg, chance-adjusted)")
            print(tab[[t for t in tiers if t in tab.columns]].round(3).to_string())
    print(f"\nWrote results to {out}")


if __name__ == "__main__":
    main()
