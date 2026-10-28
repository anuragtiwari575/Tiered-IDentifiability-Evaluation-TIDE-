#!/usr/bin/env python3
"""
tide_time_matched.py - the TIME effect on identifiability at a matched pool size, same registration pipeline.

Problem it fixes: OASIS-2 (118 subjects -> 118-way probe) and the OASIS-1 reliability set (16 subjects) are not
comparable, because chance-adjusted accuracy depends on the number of probe classes. Here every point uses
S subjects (default 16 = OASIS-1 validation size) and the same own registration pipeline:

  OASIS-1 reliability  : MR1 -> MR2 (<= 90 days), own registration, all 16 subjects (subject bootstrap CI)
  OASIS-2, binned by MR delay (years): [0,1.5) [1.5,2.5) [2.5,3.5) [3.5,8)
                         R random draws of S distinct subjects per bin; probe fit on their MR1,
                         evaluated on their visit inside the bin (repeat-percentile CI)

For every point: identifiability at distance-to-nearest-fit-slice d = 0..4 mm, cross-session and
within-session (same acquisition). Per encoder: slope of identifiability vs years at d = 0 / 1 / 2 mm,
the distance slope (per mm) at S, and the mm-equivalent of one year.

Needs the caches from tide_full_oasis2.py and the two OASIS sheets (oasis_longitudinal*, oasis_cross-sectional*)
anywhere under --sheet-dirs.

Usage:
  python tide_time_matched.py
"""
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

import tide_run as T
from tide_full_oasis2 import mv_records

BINS = [(0.0, 1.5), (1.5, 2.5), (2.5, 3.5), (3.5, 8.0)]
CONDS = {"regmask": ("feats_oasis2_regmask", "feats_oasis1val_regmask"),
         "reg": ("feats_oasis2_reg", "feats_oasis1val_reg")}


def find_sheet(dirs, key):
    for d in dirs:
        for ext in ("xlsx", "csv"):
            for f in Path(d).rglob(f"*{key}*.{ext}"):
                if f.is_file():
                    return f
    return None


def load_delays(dirs):
    years, src = {}, []
    f = find_sheet(dirs, "longitudinal")
    if f is not None:
        df = pd.read_csv(f) if f.suffix == ".csv" else pd.read_excel(f)
        cols = {c.lower().strip(): c for c in df.columns}
        for s, v in zip(df[cols["mri id"]], df[cols["mr delay"]]):
            if pd.notna(v):
                years[str(s).strip()] = float(v) / 365.25
        src.append(str(f))
    f = find_sheet(dirs, "cross-sectional")
    if f is not None:
        df = pd.read_csv(f) if f.suffix == ".csv" else pd.read_excel(f)
        cols = {c.lower().strip(): c for c in df.columns}
        if "id" in cols and "delay" in cols:
            for s, v in zip(df[cols["id"]], df[cols["delay"]]):
                if pd.notna(v):
                    years[str(s).strip()] = float(v) / 365.25
        src.append(str(f))
    return years, src


def eval_pairs(feat, recs, rows, fit_idx, offsets, seed, is_pix, maxd):
    """Fit on MR1 of recs; evaluate 'within' (same acquisition) and 'cross' (rows[j]). Returns (sess,d) -> per-subject acc."""
    S, K = len(recs), feat.shape[1]
    o0 = offsets.index(0)
    Xf = np.concatenate([np.asarray(feat[r["a"], fit_idx, o0, :], dtype=np.float32) for r in recs])
    yf = np.repeat(np.arange(S), len(fit_idx))
    tf = T._fit_tf(Xf, is_pix, seed)
    clf = T._lr().fit(tf(Xf), yf)
    out = {}
    for sess in ("within", "cross"):
        X, meta = [], []
        for j, r in enumerate(recs):
            row = r["a"] if sess == "within" else rows[j]
            fpos, epos = r["pos"][r["a"]][fit_idx], r["pos"][row]
            x = np.asarray(feat[row], dtype=np.float32)
            for i in range(K):
                for oi, o in enumerate(offsets):
                    d = int(np.min(np.abs(fpos - (epos[i] + o))))
                    if (sess == "within" and d == 0) or d > maxd:
                        continue
                    X.append(x[i, oi])
                    meta.append((j, d))
        meta = np.asarray(meta)
        p = clf.predict(tf(np.stack(X)))
        for d in np.unique(meta[:, 1]):
            m = meta[:, 1] == d
            cnt = np.bincount(meta[m, 0], minlength=S)
            if cnt.min() == 0:
                continue
            out[(sess, int(d))] = np.bincount(meta[m, 0], weights=(p[m] == meta[m, 0]).astype(float),
                                              minlength=S) / cnt
    return out


def job_o2(feat_path, recs, pairs, S, R, designs, offsets, seed, is_pix, maxd):
    """pairs: list per bin of (j, row, years). Returns {(design, bin): {"cells": {cell: [R means]}, "years": [R]}}."""
    feat = np.load(feat_path, mmap_mode="r")
    res = {}
    for dname, fidx in designs.items():
        for b, cand in enumerate(pairs):
            subj = sorted({j for j, _, _ in cand})
            if len(subj) < S:
                continue
            by_s = {}
            for j, row, y in cand:
                by_s.setdefault(j, []).append((row, y))
            rng = np.random.default_rng(seed + 1000 * b)
            cells, yrs = {}, []
            for r in range(R):
                pick = rng.choice(subj, S, replace=False)
                chosen = [by_s[j][rng.integers(len(by_s[j]))] for j in pick]
                o = eval_pairs(feat, [recs[j] for j in pick], [c[0] for c in chosen], fidx, offsets,
                               seed + r, is_pix, maxd)
                yrs.append(float(np.mean([c[1] for c in chosen])))
                for k, v in o.items():
                    cells.setdefault(k, []).append(float(T.adj(v, S).mean()))
            res[(dname, b)] = {"cells": cells, "years": yrs}
    return res


def job_o1(feat_path, recs, rows, S, designs, offsets, seed, is_pix, maxd):
    feat = np.load(feat_path, mmap_mode="r")
    return {dname: eval_pairs(feat, recs, rows, fidx, offsets, seed, is_pix, maxd) for dname, fidx in designs.items()}


def main():
    from joblib import Parallel, delayed
    from encode_slices import REGISTRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-root", default=".")
    ap.add_argument("--sheet-dirs", nargs="+", default=["Datasets", "."])
    ap.add_argument("--out", default="tide_time_matched")
    ap.add_argument("--S", type=int, default=16)
    ap.add_argument("--repeats", type=int, default=50)
    ap.add_argument("--max-d", type=int, default=4, help="max distance (slices = mm) evaluated")
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    t0 = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    T.LOGFILE = out / "time_log.txt"
    info = {"pixel": ("floor", "pixel"), **{k: (v[4], v[5]) for k, v in REGISTRY.items()}}
    names = ["pixel"] + list(REGISTRY)
    years, src = load_delays(a.sheet_dirs)
    T.log(f"delays loaded for {len(years)} sessions from {src}")
    if not any(k.startswith("OAS2") for k in years):
        raise SystemExit("OASIS-2 longitudinal sheet not found under --sheet-dirs")
    rng = np.random.default_rng(a.seed)
    rows_out, slope_rows = [], []

    for cname, (o2dir, o1dir) in CONDS.items():
        o2dir, o1dir = Path(a.cache_root) / o2dir, Path(a.cache_root) / o1dir
        if not (o2dir / "scans.csv").exists() or not (o1dir / "scans.csv").exists():
            T.log(f"[{cname}] caches missing, skipped")
            continue
        import json
        offsets = json.loads((o2dir / "meta.json").read_text())["offsets"]
        recs2 = mv_records(pd.read_csv(o2dir / "scans.csv"), False)
        recs1 = mv_records(pd.read_csv(o1dir / "scans.csv"), False)
        S = min(a.S, len(recs1))
        K = int(np.load(o2dir / "feats_pixel.npy", mmap_mode="r").shape[1])
        designs = {"dense": np.arange(K), "sparse": np.arange(0, K, 2)}
        pairs = [[] for _ in BINS]
        for j, r in enumerate(recs2):
            for v, row in r["visits"].items():
                y = years.get(r["sessions"][v])
                if y is None:
                    continue
                for b, (lo, hi) in enumerate(BINS):
                    if lo <= y < hi:
                        pairs[b].append((j, row, y))
        T.log(f"[{cname}] S={S}; OASIS-2 subjects per delay bin: "
              + ", ".join(f"{BINS[b]}: {len({p[0] for p in pairs[b]})}" for b in range(len(BINS))))
        rows1 = [min(r["visits"].items())[1] for r in recs1]
        y1 = float(np.nanmean([years.get(min(r["sessions"].items())[1], np.nan) for r in recs1]))
        if not np.isfinite(y1):
            y1 = 90 / 365.25
        models = [m for m in names if (o2dir / f"feats_{m}.npy").exists() and (o1dir / f"feats_{m}.npy").exists()]
        t1 = time.time()
        R2 = Parallel(n_jobs=a.n_jobs)(delayed(job_o2)(str(o2dir / f"feats_{m}.npy"), recs2, pairs, S, a.repeats,
                                                       designs, offsets, a.seed, m == "pixel", a.max_d) for m in models)
        R1 = Parallel(n_jobs=a.n_jobs)(delayed(job_o1)(str(o1dir / f"feats_{m}.npy"), recs1, rows1, S, designs,
                                                       offsets, a.seed, m == "pixel", a.max_d) for m in models)
        T.log(f"[{cname}] probes done ({time.time() - t1:.0f}s)")
        for m, r2, r1 in zip(models, R2, R1):
            g = T.PT_GROUP.get(info[m][1], info[m][1])
            for dname in designs:
                pts = {}
                for (sess, d), v in r1[dname].items():
                    av = T.adj(v, len(recs1))
                    lo, hi = T.ci(T.boot_vec(av, a.boot, rng))
                    rows_out.append(dict(cond=cname, design=dname, model=m, group=g, point="OASIS-1 rescan",
                                         years=y1, session=sess, d_mm=d, mean=av.mean(), lo=lo, hi=hi, n=len(av)))
                    pts.setdefault((sess, d), []).append((y1, av.mean(), T.boot_vec(av, 200, rng)))
                for b in range(len(BINS)):
                    if (dname, b) not in r2:
                        continue
                    blk = r2[(dname, b)]
                    ym = float(np.mean(blk["years"]))
                    for (sess, d), vals in blk["cells"].items():
                        vals = np.asarray(vals)
                        rows_out.append(dict(cond=cname, design=dname, model=m, group=g,
                                             point=f"OASIS-2 {BINS[b][0]}-{BINS[b][1]} y", years=ym, session=sess,
                                             d_mm=d, mean=vals.mean(), lo=np.percentile(vals, 2.5),
                                             hi=np.percentile(vals, 97.5), n=len(vals)))
                        pts.setdefault((sess, d), []).append((ym, vals.mean(), vals))
                c0 = pts.get(("cross", 0))
                for (sess, d), P in pts.items():
                    if sess != "cross" or len(P) < 3:
                        continue
                    x = np.array([p[0] for p in P])
                    y = np.array([p[1] for p in P])
                    s = np.polyfit(x, y, 1)[0]
                    bs = [np.polyfit(x, np.array([rng.choice(p[2]) for p in P]), 1)[0] for _ in range(a.boot)]
                    lo, hi = T.ci(bs)
                    dist = np.nan
                    if c0 is not None and ("cross", 2) in pts:
                        dist = (pts[("cross", 2)][0][1] - c0[0][1]) / 2.0     # per mm, at the OASIS-1 point
                    slope_rows.append(dict(cond=cname, design=dname, model=m, group=g, d_mm=d, n_points=len(P),
                                           slope_per_year=s, lo=lo, hi=hi, significant_decline=bool(hi < 0),
                                           dist_slope_per_mm=dist,
                                           mm_equiv_of_one_year=(s / dist) if np.isfinite(dist) and dist < 0 else np.nan))
    D = pd.DataFrame(rows_out)
    Sl = pd.DataFrame(slope_rows)
    D.to_csv(out / "time_matched_points.csv", index=False)
    Sl.to_csv(out / "time_matched_slopes.csv", index=False)

    # ---------- figures ----------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    gcol = {"supervised IN-1k": "#4C72B0", "supervised IN-21k": "#55A868", "self-supervised": "#C44E52",
            "weakly supervised": "#8172B2", "vision-language": "#CCB974"}
    for (cname, dname), q in D[D["session"] == "cross"].groupby(["cond", "design"]):
        fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
        for ax, d in zip(axs, (0, 1, 2)):
            qq = q[q["d_mm"] == d]
            for m, g in qq.groupby("model"):
                g = g.sort_values("years")
                grp = g["group"].iloc[0]
                if m == "pixel":
                    ax.errorbar(g["years"], g["mean"], yerr=[g["mean"] - g["lo"], g["hi"] - g["mean"]], fmt="o-",
                                color="red", lw=2, capsize=2, label="pixel", zorder=5)
                elif grp in gcol:
                    ax.plot(g["years"], g["mean"], color=gcol[grp], lw=0.6, alpha=0.3)
            for grp, col in gcol.items():
                h = qq[qq["group"] == grp].groupby("years")["mean"].median()
                if len(h):
                    ax.plot(h.index, h.values, "o-", color=col, lw=2, ms=4, label=f"{grp} (median)")
            ax.set_xlabel("Years between fit scan and eval scan")
            ax.set_title(f"{cname}/{dname}: cross-session, {d} mm from nearest fit slice (S={a.S})", fontsize=9)
        axs[0].set_ylabel("Identifiability (chance-adjusted)")
        axs[-1].legend(fontsize=6)
        fig.tight_layout()
        fig.savefig(out / f"time_matched_{cname}_{dname}.png", dpi=170)
        plt.close(fig)

    # ---------- report ----------
    try:
        import tabulate  # noqa: F401
    except ImportError:
        pd.DataFrame.to_markdown = lambda self, index=False, **kw: "```\n" + self.to_string(index=index) + "\n```"
    L = ["# Time effect at matched pool size", "", f"S = {a.S}, repeats = {a.repeats}, delay sheets: {src}", ""]
    pre = D[~D["group"].isin(["pixel", "random"])]
    for (cname, dname), q in D[D["session"] == "cross"].groupby(["cond", "design"]):
        L += [f"## {cname} / {dname} (cross-session)", ""]
        tab = []
        for (pt, yrs), g in q.groupby(["point", "years"]):
            row = {"point": pt, "years": round(yrs, 2)}
            for d in (0, 1, 2, 3, 4):
                gd = g[g["d_mm"] == d]
                if len(gd):
                    px = gd[gd["model"] == "pixel"]["mean"]
                    pm = gd[~gd["group"].isin(["pixel", "random"])]["mean"].median()
                    row[f"{d}mm pixel"] = round(float(px.iloc[0]), 3) if len(px) else np.nan
                    row[f"{d}mm enc-median"] = round(float(pm), 3)
            tab.append(row)
        L += [pd.DataFrame(tab).sort_values("years").to_markdown(index=False), ""]
        sl = Sl[(Sl["cond"] == cname) & (Sl["design"] == dname)]
        for d in (0, 1, 2):
            s = sl[(sl["d_mm"] == d) & ~sl["group"].isin(["pixel", "random"])]
            px = sl[(sl["d_mm"] == d) & (sl["model"] == "pixel")]
            if len(s):
                L.append(f"- {d} mm: encoders with significant decline over years {int(s['significant_decline'].sum())}"
                         f"/{len(s)}; median slope {s['slope_per_year'].median():+.4f}/yr; pixel slope "
                         f"{(px['slope_per_year'].iloc[0] if len(px) else np.nan):+.4f}/yr "
                         f"[{(px['lo'].iloc[0] if len(px) else np.nan):+.4f},{(px['hi'].iloc[0] if len(px) else np.nan):+.4f}]; "
                         f"median mm-equivalent of one year {s['mm_equiv_of_one_year'].median():.3f} mm")
        L.append("")
    (out / "REPORT_TIME.md").write_text("\n".join(L), encoding="utf-8")
    T.log(f"DONE in {(time.time() - t0) / 60:.1f} min -> {out}")


if __name__ == "__main__":
    main()
