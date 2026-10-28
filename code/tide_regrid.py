#!/usr/bin/env python3
"""
tide_regrid.py - TIDE re-analysis binned by distance to the NEAREST probe-fit slice.

Fixes the confound in tide_grid.py / the raw 'same_scan_far' tier: probe-fit positions are ~6-9 slices
apart, so a nominal offset d can land next to a *different* fit position. Here every eval slice is
assigned its true distance to the nearest fit slice of the same subject (in mm), and accuracy is
binned by that distance. Within the probe-fit acquisition, slices identical to a fit slice (distance 0)
are excluded.

Re-uses the existing slice/feature caches - no new encoding.

Fit designs (fixed n_fit per design):
  dense  : all K positions, offset 0           (n_fit = K)     -> distances 0 .. ~half spacing
  sparse : every second position, offset 0     (n_fit = K/2)   -> distances 0 .. ~one spacing
Sessions:
  within : same acquisition as the fit slices (MR1, first scan)
  repeat : second acquisition of the same session (raw only)
  rescan : next session (MR2, <= 90 days)

Usage:
  python tide_regrid.py --out tide_regrid_oasis1
  (defaults: raw=feats_oasis1_v2 @1.25 mm, t88_gfc=feats_oasis1_t88_gfc_grid @1 mm,
             t88_masked=feats_oasis1_t88_masked_grid @1 mm)
"""
import argparse
import json
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd

import tide_run as T

DEFAULT_CONDS = ["raw=feats_oasis1_v2:1.25", "t88_gfc=feats_oasis1_t88_gfc_grid:1.0",
                 "t88_masked=feats_oasis1_t88_masked_grid:1.0"]
SESS_KEY = {"within": "a", "repeat": "b", "rescan": "c"}


def records(scans):
    ok = scans[scans["ok"].astype(bool)]
    out = []
    for subj, g in ok.groupby("subject"):
        sess = sorted(g["session"].unique(), key=lambda s: int(s.split("_MR")[-1]))
        first = g[g["session"] == sess[0]].sort_values("scan")
        r = dict(subject=subj, a=int(first.index[0]),
                 b=int(first.index[1]) if len(first) >= 2 else None,
                 c=int(g[g["session"] == sess[1]].sort_values("scan").index[0]) if len(sess) >= 2 else None)
        for k in ("a", "b", "c"):
            r[f"pos_{k}"] = (np.array([int(x) for x in str(scans.at[r[k], "positions"]).split()])
                             if r[k] is not None else None)
        out.append(r)
    return out


def regrid_job(feat_path, recs, sessions, fit_idx, offsets, seed, is_pix, chunk=40):
    feat = np.load(feat_path, mmap_mode="r")
    S, K = len(recs), feat.shape[1]
    o0 = offsets.index(0)
    Xf = np.concatenate([np.asarray(feat[r["a"], fit_idx, o0, :], dtype=np.float32) for r in recs])
    yf = np.repeat(np.arange(S), len(fit_idx))
    tf = T._fit_tf(Xf, is_pix, seed)
    Zf = tf(Xf)
    clf = T._lr().fit(Zf, yf)
    Zfn = T._l2(Zf)
    out = {}
    for sess in sessions:
        key = SESS_KEY[sess]
        subj_all, d_all, lr_all, nn_all = [], [], [], []
        for s0 in range(0, S, chunk):
            X, meta = [], []
            for j in range(s0, min(S, s0 + chunk)):
                r = recs[j]
                fpos = r["pos_a"][fit_idx]
                epos = r[f"pos_{key}"]
                x = np.asarray(feat[r[key]], dtype=np.float32)          # K, O, D
                for i in range(K):
                    for oi, o in enumerate(offsets):
                        d = int(np.min(np.abs(fpos - (epos[i] + o))))
                        if sess == "within" and d == 0:
                            continue
                        X.append(x[i, oi])
                        meta.append((j, d))
            if not X:
                continue
            meta = np.asarray(meta)
            Z = tf(np.stack(X))
            subj_all.append(meta[:, 0])
            d_all.append(meta[:, 1])
            lr_all.append(clf.predict(Z) == meta[:, 0])
            nn_all.append(yf[np.argmax(T._l2(Z) @ Zfn.T, axis=1)] == meta[:, 0])
        subj, dd = np.concatenate(subj_all), np.concatenate(d_all)
        lr, nn = np.concatenate(lr_all), np.concatenate(nn_all)
        for d in np.unique(dd):
            m = dd == d
            cnt = np.bincount(subj[m], minlength=S)
            if cnt.min() == 0:
                continue                      # keep only bins every subject has
            out[(sess, int(d))] = dict(n=int(np.median(cnt)),
                                       lr=np.bincount(subj[m], weights=lr[m].astype(float), minlength=S) / cnt,
                                       nn=np.bincount(subj[m], weights=nn[m].astype(float), minlength=S) / cnt)
    return out


def run_cond(cname, cdir, models, args, out):
    from joblib import Parallel, delayed
    pk = out / f"regrid_{cname}.pkl"
    if pk.exists() and not args.redo_probes:
        T.log(f"[regrid] {cname}: reusing {pk.name}")
        with open(pk, "rb") as fh:
            return pickle.load(fh)
    scans = pd.read_csv(cdir / "scans.csv")
    offsets = json.loads((cdir / "meta.json").read_text())["offsets"]
    recs = records(scans)
    K = int(np.load(cdir / f"feats_{models[0]}.npy", mmap_mode="r").shape[1])
    has_b = np.mean([r["b"] is not None for r in recs]) >= 0.9
    pools = {}
    base = ["within"] + (["repeat"] if has_b else [])
    pools["all"] = ([r for r in recs if all(r[SESS_KEY[s]] is not None for s in base)], base)
    rel = [r for r in pools["all"][0] if r["c"] is not None]
    if len(rel) >= 5:
        pools["reliability"] = (rel, base + ["rescan"])
    designs = {"dense": np.arange(K), "sparse": np.arange(0, K, 2)}
    R = {"offsets": offsets, "pools": {p: {"subjects": [r["subject"] for r in rr], "sessions": ss}
                                       for p, (rr, ss) in pools.items()}, "res": {}}
    for p, (rr, ss) in pools.items():
        for dname, fidx in designs.items():
            t0 = time.time()
            res = Parallel(n_jobs=args.n_jobs)(
                delayed(regrid_job)(str(cdir / f"feats_{m}.npy"), rr, ss, fidx, offsets, args.seed, m == "pixel")
                for m in models)
            R["res"][(p, dname)] = dict(zip(models, res))
            T.log(f"[regrid] {cname}/{p}/{dname}: {len(rr)} subj, n_fit={len(fidx)}, sessions {ss} "
                  f"({time.time() - t0:.0f}s)")
    with open(pk, "wb") as fh:
        pickle.dump(R, fh)
    return R


def analyze(Rs, mm, info, params, out, B, seed, min_n):
    from scipy.stats import spearmanr
    rng = np.random.default_rng(seed + 11)
    curves, disc, gen_rows, cap, fac = [], [], [], [], []
    for cname, R in Rs.items():
        for (pool, design), P in R["res"].items():
            S = len(R["pools"][pool]["subjects"])
            models = list(P)
            pre = [m for m in models if info[m][1] not in ("pixel", "random")]
            cells = sorted(set.intersection(*[set(P[m].keys()) for m in models]))
            cells = [c for c in cells if P[models[0]][c]["n"] >= min_n]
            for c in cells:
                for m in models:
                    for probe in ("lr", "nn"):
                        a = T.adj(P[m][c][probe], S)
                        lo, hi = T.ci(T.boot_vec(a, B, rng))
                        curves.append(dict(cond=cname, pool=pool, design=design, S=S, model=m,
                                           group=T.PT_GROUP.get(info[m][1], ""), session=c[0], d_slices=c[1],
                                           d_mm=c[1] * mm[cname], n_per_subject=P[m][c]["n"],
                                           probe="logreg" if probe == "lr" else "1nn", mean=a.mean(), lo=lo, hi=hi))
                A = np.stack([T.adj(P[m][c]["lr"], S) for m in pre])
                px = T.adj(P["pixel"][c]["lr"], S)
                above = below = 0
                for m in pre:
                    lo, hi = T.ci(T.boot_vec(T.adj(P[m][c]["lr"], S) - px, B, rng))
                    above += lo > 0
                    below += hi < 0
                disc.append(dict(cond=cname, pool=pool, design=design, S=S, session=c[0], d_mm=c[1] * mm[cname],
                                 n_per_subject=P[models[0]][c]["n"], pixel=px.mean(), n_above_pixel=int(above),
                                 n_below_pixel=int(below), **T.pair_stats(A, T.boot_means(A, B, rng))))
            # generalisation score per cross-acquisition session: mean over bins with d >= 2 mm
            for sess in [s for s in ("repeat", "rescan") if s in R["pools"][pool]["sessions"]]:
                gc = [c for c in cells if c[0] == sess and c[1] * mm[cname] >= 2.0]
                if not gc:
                    continue
                G = {m: np.mean([T.adj(P[m][c]["lr"], S) for c in gc], axis=0) for m in models}
                A = np.stack([G[m] for m in pre])
                Mb = T.boot_means(A, B, rng)
                disc.append(dict(cond=cname, pool=pool, design=design, S=S, session=f"GEN {sess} (d>=2mm)",
                                 d_mm=np.nan, n_per_subject=np.nan, pixel=G["pixel"].mean(),
                                 **T.pair_stats(A, Mb)))
                for m in models:
                    lo, hi = T.ci(T.boot_vec(G[m], B, rng))
                    dlo, dhi = T.ci(T.boot_vec(G[m] - G["pixel"], B, rng))
                    gen_rows.append(dict(cond=cname, pool=pool, design=design, session=sess, model=m,
                                         family=info[m][0], group=T.PT_GROUP.get(info[m][1], ""),
                                         params_M=params.get(m, np.nan), GEN=G[m].mean(), lo=lo, hi=hi,
                                         EG=(G[m] - G["pixel"]).mean(), EG_lo=dlo, EG_hi=dhi,
                                         bins_mm=",".join(f"{c[1] * mm[cname]:g}" for c in gc)))
                for factor, keyfn in [("pretraining", lambda m: T.PT_GROUP[info[m][1]]),
                                      ("family", lambda m: info[m][0])]:
                    gn = sorted(set(keyfn(m) for m in pre))
                    cols = {g: [pre.index(m) for m in pre if keyfn(m) == g] for g in gn}
                    Gb = {g: Mb[:, cc].mean(axis=1) for g, cc in cols.items()}
                    for g in gn:
                        lo, hi = T.ci(Gb[g])
                        fac.append(dict(cond=cname, pool=pool, design=design, session=sess, factor=factor,
                                        comparison=g, mean=float(A[cols[g]].mean()), lo=lo, hi=hi, significant=np.nan))
                    for i, g1 in enumerate(gn):
                        for g2 in gn[i + 1:]:
                            lo, hi = T.ci(Gb[g1] - Gb[g2])
                            fac.append(dict(cond=cname, pool=pool, design=design, session=sess, factor=factor,
                                            comparison=f"{g1} minus {g2}",
                                            mean=float(A[cols[g1]].mean() - A[cols[g2]].mean()), lo=lo, hi=hi,
                                            significant=bool(lo > 0 or hi < 0)))
                pm = [m for m in pre if np.isfinite(params.get(m, np.nan))]
                for sub_name, fn in [("all pretrained", lambda m: True), ("CNN", lambda m: info[m][0] == "CNN"),
                                     ("Transformer", lambda m: info[m][0] == "Transformer")]:
                    sel = [m for m in pm if fn(m)]
                    if len(sel) < 4:
                        continue
                    x = np.log10([params[m] for m in sel])
                    cc = [pre.index(m) for m in sel]
                    lo, hi = T.ci([spearmanr(x, Mb[b, cc]).correlation for b in range(B)])
                    cap.append(dict(cond=cname, pool=pool, design=design, session=sess, subset=sub_name,
                                    n_models=len(sel), spearman=spearmanr(x, A[cc].mean(axis=1)).correlation,
                                    lo=lo, hi=hi))
    F = {"curves": pd.DataFrame(curves), "disc": pd.DataFrame(disc), "gen": pd.DataFrame(gen_rows),
         "fac": pd.DataFrame(fac), "cap": pd.DataFrame(cap)}
    for k, df in F.items():
        if not df.empty:
            df.to_csv(out / f"regrid_{k}.csv", index=False)
    return F


def figures(F, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fd = out / "figures"
    fd.mkdir(exist_ok=True)
    gcol = {"supervised IN-1k": "#4C72B0", "supervised IN-21k": "#55A868", "self-supervised": "#C44E52",
            "weakly supervised": "#8172B2", "vision-language": "#CCB974"}
    C = F["curves"]
    C = C[C["probe"] == "logreg"]
    for (cname, pool, design), cv in C.groupby(["cond", "pool", "design"]):
        sess = [s for s in ("within", "repeat", "rescan") if s in cv["session"].unique()]
        fig, axs = plt.subplots(1, len(sess), figsize=(4.6 * len(sess), 4.2), sharey=True, squeeze=False)
        for ax, s in zip(axs[0], sess):
            q = cv[cv["session"] == s]
            for m, g in q.groupby("model"):
                g = g.sort_values("d_mm")
                grp = g["group"].iloc[0]
                if m == "pixel":
                    ax.plot(g["d_mm"], g["mean"], "o-", color="red", lw=2.2, ms=3, label="pixel", zorder=5)
                elif grp == "random":
                    ax.plot(g["d_mm"], g["mean"], color="#888888", lw=1, ls="--")
                else:
                    ax.plot(g["d_mm"], g["mean"], color=gcol.get(grp, "#4C72B0"), lw=0.6, alpha=0.3)
            for grp, col in gcol.items():
                h = q[q["group"] == grp].groupby("d_mm")["mean"].median()
                if len(h):
                    ax.plot(h.index, h.values, "o-", color=col, lw=2, ms=3, label=f"{grp} (median)")
            ax.set_xlabel("Distance to nearest probe-fit slice (mm)")
            ax.set_title(f"{cname} / {pool} / {design}: {s}", fontsize=9)
            ax.axhline(0.5, color="k", lw=0.5, ls=":")
        axs[0][0].set_ylabel("Identifiability (chance-adjusted)")
        axs[0][-1].legend(fontsize=6)
        fig.tight_layout()
        fig.savefig(fd / f"decay_{cname}_{pool}_{design}.png", dpi=180)
        plt.close(fig)


def report(F, out, elapsed):
    try:
        import tabulate  # noqa: F401
    except ImportError:
        pd.DataFrame.to_markdown = lambda self, index=False, **kw: "```\n" + self.to_string(index=index) + "\n```"
    L = ["# TIDE re-analysis: identifiability vs distance to nearest probe-fit slice", "",
         f"Total time: {elapsed / 3600:.2f} h", ""]
    D = F["disc"]
    L += ["## Per distance bin (pretrained encoders; pixel = pixel floor; logreg, chance-adjusted)", "",
          D[["cond", "pool", "design", "S", "session", "d_mm", "n_per_subject", "pixel", "mean", "min", "max",
             "n_above_pixel", "n_below_pixel", "frac_pairs_significant"]].round(3).to_markdown(index=False), ""]
    G = F["gen"]
    if not G.empty:
        L += ["## Generalisation score (mean over d >= 2 mm), per condition / design / session", ""]
        for key, g in G.groupby(["cond", "pool", "design", "session"]):
            pre = g[~g["group"].isin(["random", "pixel"])].sort_values("GEN", ascending=False)
            px = g[g["model"] == "pixel"].iloc[0]
            L.append(f"- {'/'.join(key)}: pixel {px['GEN']:.3f}; pretrained {pre['GEN'].min():.3f}-"
                     f"{pre['GEN'].max():.3f}; above pixel {int((pre['EG_lo'] > 0).sum())}/{len(pre)}, "
                     f"below pixel {int((pre['EG_hi'] < 0).sum())}/{len(pre)}; top3 "
                     + ", ".join(f"{r.model} {r.GEN:.3f}" for r in pre.head(3).itertuples())
                     + "; bottom3 " + ", ".join(f"{r.model} {r.GEN:.3f}" for r in pre.tail(3).itertuples()))
        L.append("")
    fs = F["fac"]
    if not fs.empty:
        L += ["## Significant factor differences on GEN", ""]
        L += [f"- {r.cond}/{r.pool}/{r.design}/{r.session} {r.factor}: {r.comparison} = {r.mean:+.3f} "
              f"[{r.lo:+.3f},{r.hi:+.3f}]" for r in fs[fs["significant"] == True].itertuples()] or ["- none"]  # noqa: E712
        L.append("")
    if not F["cap"].empty:
        L += ["## Capacity (Spearman log-params vs GEN)", "", F["cap"].round(3).to_markdown(index=False), ""]
    (out / "REPORT_regrid.md").write_text("\n".join(L), encoding="utf-8")


def main():
    from encode_slices import REGISTRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--conds", nargs="+", default=DEFAULT_CONDS, help="name=cache_dir:mm_per_slice")
    ap.add_argument("--out", default="tide_regrid_oasis1")
    ap.add_argument("--params-from", default="tide_oasis1", help="folder holding params.csv")
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--min-n", type=int, default=3, help="min eval slices per subject per distance bin")
    ap.add_argument("--redo-probes", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    T.LOGFILE = out / "regrid_log.txt"
    names = ["pixel"] + list(REGISTRY)
    info = {"pixel": ("floor", "pixel"), **{k: (v[4], v[5]) for k, v in REGISTRY.items()}}
    params = T.count_params(Path(a.params_from))
    Rs, mm = {}, {}
    for spec in a.conds:
        cname, rest = spec.split("=", 1)
        cdir, mmv = rest.rsplit(":", 1)
        cdir = Path(cdir)
        if not (cdir / "scans.csv").exists():
            T.log(f"[regrid] {cname}: {cdir} not found, skipped")
            continue
        mm[cname] = float(mmv)
        models = [m for m in names if (cdir / f"feats_{m}.npy").exists()]
        Rs[cname] = run_cond(cname, cdir, models, a, out)
    T.log(f"[stage] probes done ({(time.time() - t0) / 60:.1f} min)")
    F = analyze(Rs, mm, info, params, out, a.boot, a.seed, a.min_n)
    try:
        figures(F, out)
    except Exception as e:  # noqa: BLE001
        T.log(f"[fig] error: {e}")
    try:
        report(F, out, time.time() - t0)
    except Exception as e:  # noqa: BLE001
        T.log(f"[report] error: {e}")
    T.log(f"DONE in {(time.time() - t0) / 3600:.2f} h -> {out}")


if __name__ == "__main__":
    main()
