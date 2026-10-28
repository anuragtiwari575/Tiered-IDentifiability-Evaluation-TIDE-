#!/usr/bin/env python3
"""
tide_grid.py - TIDE spatial-offset x session grid on registered OASIS-1 (T88 gfc / masked).

Question: after atlas registration, how fast does identifiability decay as the eval slice moves
away (in mm) from the probe-fit slice, within the same acquisition vs. in a rescan session?

Grid (fit always = MR1, K reference slices at offset 0, fixed n_fit):
  within(d)  : same MR1 volume, slice +d          d in offsets[1:]
  rescan(d)  : MR2 volume (<= 90 days later), slice +d   d in offsets
T88_111 is 1 mm isotropic, so d is in mm.

Per encoder it reports decay curves, the d50 (offset where identifiability drops below 0.5),
SIG = Spatial Identity Generalisation (mean rescan identifiability over d >= 2 mm),
encoder gain over the pixel floor on SIG, and a discriminability map showing in which cell
encoders differ most. Factor-group and capacity analyses are repeated on SIG.

Needs tide_run.py (and its index_t88.csv) in the same folder. Resumable.

Usage:
  python tide_grid.py --tide-out tide_oasis1 --out tide_grid_oasis1
"""
import argparse
import json
import pickle
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

import tide_run as T

DEFAULT_OFFSETS = [0, 1, 2, 3, 4, 6, 8, 10, 15, 20]


def grid_records(scans):
    ok = scans[scans["ok"].astype(bool)]
    recs = []
    for subj, g in ok.groupby("subject"):
        g = g.sort_values("visit")
        recs.append(dict(subject=subj, a=int(g.index[0]), b=int(g.index[1]) if g["visit"].nunique() >= 2 else None))
    return recs


def grid_job(feat_path, recs, offsets, seed, is_pix, light=False, sub=None):
    feat = np.load(feat_path, mmap_mode="r")
    if sub:
        pick = np.random.default_rng(seed).choice(len(recs), sub, replace=False)
        recs = [recs[i] for i in pick]
    S, K = len(recs), feat.shape[1]
    Xf = np.concatenate([T._feats(feat, r["a"], 0) for r in recs])
    yf = np.repeat(np.arange(S), K)
    tf = T._fit_tf(Xf, is_pix, seed)
    Zf = tf(Xf)
    clf = T._lr().fit(Zf, yf)
    Zfn = T._l2(Zf)
    out = {}
    sessions = ["within"] + (["rescan"] if all(r["b"] is not None for r in recs) and not light else [])
    for sess in sessions:
        for j, d in enumerate(offsets):
            if sess == "within" and d == 0:
                continue
            Xe = np.concatenate([T._feats(feat, r["a"] if sess == "within" else r["b"], j) for r in recs])
            Ze = tf(Xe)
            res = {"logreg": T._per_subj(clf.predict(Ze), yf, S)}
            if not light:
                res["1nn"] = T._per_subj(yf[np.argmax(T._l2(Ze) @ Zfn.T, axis=1)], yf, S)
            out[(sess, d)] = res
    return out


def d50(offs, vals):
    if vals[0] < 0.5:
        return float(offs[0])
    for i in range(1, len(offs)):
        if vals[i] < 0.5:
            x0, x1, y0, y1 = offs[i - 1], offs[i], vals[i - 1], vals[i]
            return float(x0 + (0.5 - y0) * (x1 - x0) / (y1 - y0)) if y1 != y0 else float(x1)
    return np.inf


def run_variant(var, cdir, models, offsets, args, out):
    from joblib import Parallel, delayed
    pk = out / f"grid_{var}.pkl"
    if pk.exists() and not args.redo_probes:
        T.log(f"[grid] {var}: reusing {pk.name}")
        with open(pk, "rb") as fh:
            return pickle.load(fh)
    scans = pd.read_csv(cdir / "scans.csv")
    recs = grid_records(scans)
    rel = [r for r in recs if r["b"] is not None]
    R = {"subjects": {"all": [r["subject"] for r in recs], "reliability": [r["subject"] for r in rel]},
         "full": {}, "sub": {}}
    for pool, rr in [("all", recs), ("reliability", rel)]:
        t0 = time.time()
        res = Parallel(n_jobs=args.n_jobs)(
            delayed(grid_job)(str(cdir / f"feats_{m}.npy"), rr, offsets, args.seed, m == "pixel") for m in models)
        R["full"][pool] = dict(zip(models, res))
        T.log(f"[grid] {var}/{pool}: {len(rr)} subjects x {len(models)} models ({time.time() - t0:.0f}s)")
    if len(recs) > args.sub_size:
        t0 = time.time()
        tasks = [(m, r) for m in models for r in range(args.repeats)]
        res = Parallel(n_jobs=args.n_jobs)(
            delayed(grid_job)(str(cdir / f"feats_{m}.npy"), recs, offsets, args.seed * 1000 + r, m == "pixel",
                              True, args.sub_size) for m, r in tasks)
        for (m, _r), o in zip(tasks, res):
            R["sub"].setdefault(m, []).append(o)
        T.log(f"[grid] {var}/all S={args.sub_size} x {args.repeats} repeats ({time.time() - t0:.0f}s)")
    with open(pk, "wb") as fh:
        pickle.dump(R, fh)
    return R


def analyze(Rs, offsets, info, params, out, B, seed):
    from scipy.stats import spearmanr
    rng = np.random.default_rng(seed + 7)
    curves, disc, sig_rows, fac, cap = [], [], [], [], []
    for var, R in Rs.items():
        # ---- curves with CIs (full pools) ----
        for pool, P in R["full"].items():
            S = len(R["subjects"][pool])
            for m, o in P.items():
                for (sess, d), res in o.items():
                    for probe, v in res.items():
                        a = T.adj(v, S)
                        lo, hi = T.ci(T.boot_vec(a, B, rng))
                        curves.append(dict(variant=var, pool=pool, S=S, model=m, group=T.PT_GROUP.get(info[m][1], ""),
                                           session=sess, offset_mm=d, probe=probe, mean=a.mean(), lo=lo, hi=hi))
        # within-session decay at matched S (subsamples of the 'all' pool)
        for m, lst in R["sub"].items():
            s = args_sub_size(lst)
            for key in lst[0]:
                vals = np.array([T.adj(o[key]["logreg"].mean(), s) for o in lst])
                curves.append(dict(variant=var, pool=f"all_S{s}", S=s, model=m, group=T.PT_GROUP.get(info[m][1], ""),
                                   session=key[0], offset_mm=key[1], probe="logreg", mean=vals.mean(),
                                   lo=np.percentile(vals, 2.5), hi=np.percentile(vals, 97.5)))
        # ---- discriminability map + SIG on the reliability pool ----
        P = R["full"]["reliability"]
        S = len(R["subjects"]["reliability"])
        models = list(P)
        pre = [m for m in models if info[m][1] not in ("pixel", "random")]
        cells = [c for c in P[models[0]].keys()]
        for pool_name, PP, SS in [("reliability", P, S), ("all", R["full"]["all"], len(R["subjects"]["all"]))]:
            for c in [c for c in PP[models[0]].keys()]:
                A = np.stack([T.adj(PP[m][c]["logreg"], SS) for m in pre])
                disc.append(dict(variant=var, pool=pool_name, S=SS, session=c[0], offset_mm=c[1],
                                 **T.pair_stats(A, T.boot_means(A, B, rng))))
        sig_cells = [c for c in cells if c[0] == "rescan" and c[1] >= 2]
        SIGv = {m: np.mean([T.adj(P[m][c]["logreg"], S) for c in sig_cells], axis=0) for m in models}
        A = np.stack([SIGv[m] for m in pre])
        Mb = T.boot_means(A, B, rng)
        disc.append(dict(variant=var, pool="reliability", S=S, session="SIG (rescan, d>=2)", offset_mm=np.nan,
                         **T.pair_stats(A, Mb)))
        resc = sorted([c for c in cells if c[0] == "rescan"], key=lambda c: c[1])
        wit = sorted([c for c in cells if c[0] == "within"], key=lambda c: c[1])
        rk = (-Mb).argsort(axis=1).argsort(axis=1) + 1
        for m in models:
            v = SIGv[m]
            lo, hi = T.ci(T.boot_vec(v, B, rng))
            dv = v - SIGv["pixel"]
            dlo, dhi = T.ci(T.boot_vec(dv, B, rng))
            rc = [T.adj(P[m][c]["logreg"], S).mean() for c in resc]
            wc = [T.adj(P[m][c]["logreg"], S).mean() for c in wit]
            row = dict(variant=var, model=m, family=info[m][0], group=T.PT_GROUP.get(info[m][1], ""),
                       params_M=params.get(m, np.nan), DI_rescan_0mm=rc[0], SIG=v.mean(), SIG_lo=lo, SIG_hi=hi,
                       EG_SIG=dv.mean(), EG_lo=dlo, EG_hi=dhi, EG_significant=bool(dlo > 0),
                       EG_negative=bool(dhi < 0), d50_rescan_mm=d50([c[1] for c in resc], rc),
                       d50_within_mm=d50([0] + [c[1] for c in wit], [1.0] + wc),
                       session_penalty=float(np.mean([w - r for (cw, w) in zip(wit, wc)
                                                      for (cr, r) in zip(resc, rc) if cw[1] == cr[1]])))
            if m in pre:
                j = pre.index(m)
                row.update(rank=int(np.median(rk[:, j])), rank_lo=int(np.percentile(rk[:, j], 2.5)),
                           rank_hi=int(np.percentile(rk[:, j], 97.5)))
            sig_rows.append(row)
        for factor, keyfn in [("pretraining", lambda m: T.PT_GROUP[info[m][1]]), ("family", lambda m: info[m][0])]:
            gn = sorted(set(keyfn(m) for m in pre))
            cols = {g: [pre.index(m) for m in pre if keyfn(m) == g] for g in gn}
            Gb = {g: Mb[:, c].mean(axis=1) for g, c in cols.items()}
            Gm = {g: float(A[c].mean(axis=1).mean()) for g, c in cols.items()}
            for g in gn:
                lo, hi = T.ci(Gb[g])
                fac.append(dict(variant=var, factor=factor, comparison=g, n_models=len(cols[g]), mean=Gm[g],
                                lo=lo, hi=hi, significant=np.nan))
            for g1, g2 in combinations(gn, 2):
                lo, hi = T.ci(Gb[g1] - Gb[g2])
                fac.append(dict(variant=var, factor=factor, comparison=f"{g1} minus {g2}", n_models=np.nan,
                                mean=Gm[g1] - Gm[g2], lo=lo, hi=hi, significant=bool(lo > 0 or hi < 0)))
        pm = [m for m in pre if np.isfinite(params.get(m, np.nan))]
        for sub_name, fn in [("all pretrained", lambda m: True), ("CNN", lambda m: info[m][0] == "CNN"),
                             ("Transformer", lambda m: info[m][0] == "Transformer")]:
            sel = [m for m in pm if fn(m)]
            if len(sel) < 4:
                continue
            x = np.log10([params[m] for m in sel])
            cols = [pre.index(m) for m in sel]
            rho = spearmanr(x, A[cols].mean(axis=1)).correlation
            lo, hi = T.ci([spearmanr(x, Mb[b, cols]).correlation for b in range(B)])
            cap.append(dict(variant=var, subset=sub_name, n_models=len(sel), spearman_logparams_vs_SIG=rho, lo=lo, hi=hi))
    F = {"curves": pd.DataFrame(curves), "disc": pd.DataFrame(disc), "sig": pd.DataFrame(sig_rows),
         "fac": pd.DataFrame(fac), "cap": pd.DataFrame(cap)}
    for k, df in F.items():
        if not df.empty:
            df.to_csv(out / f"grid_{k}.csv", index=False)
    return F


def args_sub_size(lst):
    k = next(iter(lst[0]))
    return len(lst[0][k]["logreg"])


def figures(F, offsets, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fd = out / "figures"
    fd.mkdir(exist_ok=True)
    gcol = {"supervised IN-1k": "#4C72B0", "supervised IN-21k": "#55A868", "self-supervised": "#C44E52",
            "weakly supervised": "#8172B2", "vision-language": "#CCB974"}
    C = F["curves"]
    for var, cv in C.groupby("variant"):
        cv = cv[(cv["pool"] == "reliability") & (cv["probe"] == "logreg")]
        fig, axs = plt.subplots(1, 2, figsize=(11, 4.3), sharey=True)
        for ax, sess in zip(axs, ["within", "rescan"]):
            q = cv[cv["session"] == sess]
            for m, g in q.groupby("model"):
                g = g.sort_values("offset_mm")
                grp = g["group"].iloc[0]
                if m == "pixel":
                    ax.plot(g["offset_mm"], g["mean"], color="red", lw=2.2, label="pixel", zorder=5)
                elif grp == "random":
                    ax.plot(g["offset_mm"], g["mean"], color="#888888", lw=1, ls="--")
                else:
                    ax.plot(g["offset_mm"], g["mean"], color=gcol.get(grp, "#4C72B0"), lw=0.6, alpha=0.35)
            for grp, col in gcol.items():
                h = q[q["group"] == grp].groupby("offset_mm")["mean"].median()
                if len(h):
                    ax.plot(h.index, h.values, color=col, lw=2.2, label=f"{grp} (median)")
            ax.axhline(0.5, color="k", lw=0.5, ls=":")
            ax.set_xlabel("Offset from probe-fit slice (mm, atlas space)")
            ax.set_title(f"{var}: {'same acquisition (MR1)' if sess == 'within' else 'rescan session (MR2)'}", fontsize=9)
        axs[0].set_ylabel("Identifiability (chance-adjusted, S=20)")
        axs[1].legend(fontsize=6, loc="upper right")
        fig.tight_layout()
        fig.savefig(fd / f"decay_{var}.png", dpi=180)
        plt.close(fig)
    D = F["disc"]
    for (var, pool), d in D[D["offset_mm"].notna()].groupby(["variant", "pool"]):
        sess = [s for s in ["within", "rescan"] if s in d["session"].unique()]
        M = np.full((len(sess), len(offsets)), np.nan)
        Mm = np.full_like(M, np.nan)
        for i, s in enumerate(sess):
            for j, o in enumerate(offsets):
                q = d[(d["session"] == s) & (d["offset_mm"] == o)]
                if len(q):
                    M[i, j] = q["frac_pairs_significant"].iloc[0]
                    Mm[i, j] = q["mean"].iloc[0]
        fig, ax = plt.subplots(figsize=(1.0 * len(offsets) + 2, 1.3 * len(sess) + 1.4))
        im = ax.imshow(M, cmap="magma", vmin=0, vmax=1, aspect="auto")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                if np.isfinite(M[i, j]):
                    ax.text(j, i, f"{M[i, j]:.2f}\n(mean {Mm[i, j]:.2f})", ha="center", va="center", fontsize=6,
                            color="white" if M[i, j] < 0.6 else "black")
        ax.set_xticks(range(len(offsets)))
        ax.set_xticklabels([f"{o}" for o in offsets])
        ax.set_yticks(range(len(sess)))
        ax.set_yticklabels(sess)
        ax.set_xlabel("Offset (mm)")
        ax.set_title(f"{var}/{pool}: fraction of encoder pairs significantly different", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.03)
        fig.tight_layout()
        fig.savefig(fd / f"discriminability_{var}_{pool}.png", dpi=180)
        plt.close(fig)
    Sg = F["sig"]
    for var, d in Sg.groupby("variant"):
        d = d.sort_values("SIG")
        y = np.arange(len(d))
        fig, ax = plt.subplots(figsize=(6, 0.28 * len(d) + 1.4))
        cols = ["red" if m == "pixel" else ("#888888" if g == "random" else gcol.get(g, "#333"))
                for m, g in zip(d["model"], d["group"])]
        ax.errorbar(d["SIG"], y, xerr=[d["SIG"] - d["SIG_lo"], d["SIG_hi"] - d["SIG"]], fmt="none",
                    ecolor="#bbbbbb", lw=1)
        ax.scatter(d["SIG"], y, c=cols, s=18, zorder=3)
        ax.set_yticks(y)
        ax.set_yticklabels(d["model"], fontsize=7)
        ax.set_xlim(-0.05, 1.05)
        ax.set_xlabel("SIG: rescan identifiability averaged over 2-20 mm offsets")
        ax.set_title(f"{var}: spatial identity generalisation", fontsize=9)
        fig.tight_layout()
        fig.savefig(fd / f"sig_forest_{var}.png", dpi=180)
        plt.close(fig)


def report(F, out, elapsed):
    try:
        import tabulate  # noqa: F401
    except ImportError:
        pd.DataFrame.to_markdown = lambda self, index=False, **kw: "```\n" + self.to_string(index=index) + "\n```"
    L = ["# TIDE spatial-offset x session grid (OASIS-1, registered)", "", f"Total time: {elapsed / 3600:.2f} h", ""]
    Sg = F["sig"]
    for var, d in Sg.groupby("variant"):
        pre = d[~d["group"].isin(["random", "pixel"])]
        px = d[d["model"] == "pixel"].iloc[0]
        L += [f"## {var}", "",
              f"- Rescan at 0 mm: pixel {px['DI_rescan_0mm']:.3f}; pretrained "
              f"{pre['DI_rescan_0mm'].min():.3f}-{pre['DI_rescan_0mm'].max():.3f}",
              f"- SIG (rescan, 2-20 mm): pixel {px['SIG']:.3f} [{px['SIG_lo']:.3f},{px['SIG_hi']:.3f}]; pretrained "
              f"{pre['SIG'].min():.3f}-{pre['SIG'].max():.3f}; random "
              + ", ".join(f"{v:.3f}" for v in d[d['group'] == 'random']['SIG']),
              f"- Encoder gain over pixel on SIG: significantly positive {int(pre['EG_significant'].sum())}/{len(pre)}, "
              f"significantly negative {int(pre['EG_negative'].sum())}/{len(pre)}",
              f"- d50 rescan (mm): pixel {px['d50_rescan_mm']:.1f}; pretrained median {pre['d50_rescan_mm'].median():.1f}",
              f"- d50 within (mm): pixel {px['d50_within_mm']:.1f}; pretrained median {pre['d50_within_mm'].median():.1f}",
              f"- Mean session penalty (within minus rescan, same offset): pretrained median "
              f"{pre['session_penalty'].median():+.3f}, pixel {px['session_penalty']:+.3f}", ""]
        top = pre.sort_values("SIG", ascending=False)
        L.append("- Top 5 SIG: " + "; ".join(f"{r.model} {r.SIG:.3f}" for r in top.head(5).itertuples()))
        L.append("- Bottom 5 SIG: " + "; ".join(f"{r.model} {r.SIG:.3f}" for r in top.tail(5).itertuples()))
        L.append("")
    D = F["disc"]
    L += ["## Discriminability per cell (pretrained encoders)", "",
          D[["variant", "pool", "S", "session", "offset_mm", "mean", "sd", "n_ge_0p95",
             "frac_pairs_significant"]].round(3).to_markdown(index=False), ""]
    if not F["fac"].empty:
        fs = F["fac"]
        L += ["## Factor groups on SIG", "",
              fs[fs["significant"].isna()][["variant", "factor", "comparison", "n_models", "mean", "lo", "hi"]]
              .round(3).to_markdown(index=False), "", "Significant differences:", ""]
        L += [f"- {r.variant} {r.factor}: {r.comparison} = {r.mean:+.3f} [{r.lo:+.3f},{r.hi:+.3f}]"
              for r in fs[fs["significant"] == True].itertuples()] or ["- none"]  # noqa: E712
        L.append("")
    if not F["cap"].empty:
        L += ["## Capacity (Spearman log-params vs SIG)", "", F["cap"].round(3).to_markdown(index=False), ""]
    (out / "REPORT_grid.md").write_text("\n".join(L), encoding="utf-8")


def main():
    from encode_slices import REGISTRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--tide-out", default="tide_oasis1", help="folder of the previous tide_run.py (index_t88.csv)")
    ap.add_argument("--out", default="tide_grid_oasis1")
    ap.add_argument("--cache-root", default=".", help="where the grid slice caches are written")
    ap.add_argument("--offsets", type=int, nargs="+", default=DEFAULT_OFFSETS)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--band", type=float, nargs=2, default=(0.25, 0.75))
    ap.add_argument("--variants", nargs="+", default=["t88_masked", "t88_gfc"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--sub-size", type=int, default=20)
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--input-size", type=int, default=224)
    ap.add_argument("--pixel-size", type=int, default=64)
    ap.add_argument("--scans-per-batch", type=int, default=1, help="1 scan = K x offsets = 100 images per forward")
    ap.add_argument("--redo-probes", action="store_true")
    a = ap.parse_args()
    assert a.offsets[0] == 0, "first offset must be 0"

    t_start = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    T.LOGFILE = out / "grid_log.txt"
    idx = pd.read_csv(Path(a.tide_out) / "index_t88.csv")
    names = ["pixel"] + list(REGISTRY)
    info = {"pixel": ("floor", "pixel"), **{k: (v[4], v[5]) for k, v in REGISTRY.items()}}
    params = T.count_params(Path(a.tide_out))
    T.log(f"TIDE grid started | offsets {a.offsets} mm | variants {a.variants}")
    Rs = {}
    for var in a.variants:
        sub = idx[idx["variant"] == var].reset_index(drop=True)
        if sub.empty:
            T.log(f"[grid] {var}: not in index, skipped")
            continue
        cdir = Path(a.cache_root) / f"feats_oasis1_{var}_grid"
        T.cache_condition(sub, cdir, a.k, a.band, a.offsets, -1, a.workers)
        meta = json.loads((cdir / "meta.json").read_text())
        if meta["offsets"] != a.offsets:
            raise SystemExit(f"{cdir} was cached with offsets {meta['offsets']}; delete it or use the same offsets")
        T.encode_condition(cdir, names, a.input_size, a.pixel_size, a.scans_per_batch)
        models = [m for m in names if (cdir / f"feats_{m}.npy").exists()]
        Rs[var] = run_variant(var, cdir, models, a.offsets, a, out)
    T.log(f"[stage] probes done ({(time.time() - t_start) / 60:.1f} min)")
    F = analyze(Rs, a.offsets, info, params, out, a.boot, a.seed)
    try:
        figures(F, a.offsets, out)
    except Exception as e:  # noqa: BLE001
        T.log(f"[fig] error: {e}")
    try:
        report(F, out, time.time() - t_start)
    except Exception as e:  # noqa: BLE001
        T.log(f"[report] error: {e}")
    T.log(f"DONE in {(time.time() - t_start) / 3600:.2f} h -> {out}")


if __name__ == "__main__":
    main()
