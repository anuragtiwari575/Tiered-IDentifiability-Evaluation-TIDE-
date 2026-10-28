#!/usr/bin/env python3
"""
tide_extras.py - four add-on analyses on the existing TIDE feature caches (no new registration/encoding).

  A  Privacy-utility   : CDR>0 vs CDR=0 from frozen subject embeddings (subject-level repeated stratified CV,
                         AUC), per encoder and condition, against the identity score GEN from earlier runs.
                         Age-only baseline reported.
  B  Verification      : attack-style metrics, MR1 vs a later session at the same atlas position + offset d:
                         verification AUC (pool-size free), EER, TAR@FAR 1% / 0.1%, rank-1 (slice and subject).
  C  Cross-dataset     : OASIS-2 (own registration) queried against all 416 OASIS-1 subjects (official T88).
     linkage audit       Thresholds calibrated on 20 OASIS-1 reliability sessions processed by BOTH pipelines
                         (genuine = same session, other pipeline). Candidates need agreement of >= 3 of 4 models;
                         sex/age consistency reported against random pairs. Only counts go in the paper.
  D  Correlation length: fit acc(d) = a * exp(-d / lambda) to every encoder's distance curve -> lambda in mm.

Usage:
  python tide_extras.py
"""
import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler

import tide_run as T

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

UTIL_CONDS = {"o1_masked": "feats_oasis1_t88_masked_grid", "o1_gfc": "feats_oasis1_t88_gfc_grid",
              "o1_raw": "feats_oasis1_v2", "o2_regmask": "feats_oasis2_regmask", "o2_reg": "feats_oasis2_reg",
              "o2_raw": "feats_oasis2_raw"}
ID_SRC = {"o1_masked": ("regrid", dict(cond="t88_masked", pool="reliability", design="sparse", session="rescan")),
          "o1_gfc": ("regrid", dict(cond="t88_gfc", pool="reliability", design="sparse", session="rescan")),
          "o1_raw": ("regrid", dict(cond="raw", pool="reliability", design="sparse", session="rescan")),
          "o2_regmask": ("full", dict(cond="o2_regmask", design="sparse")),
          "o2_reg": ("full", dict(cond="o2_reg", design="sparse")),
          "o2_raw": ("full", dict(cond="o2_raw", design="sparse"))}
LINK_MODELS = ["pixel", "dino_vits16", "mae_vitb16", "densenet121_in1k"]
GCOL = {"supervised IN-1k": "#4C72B0", "supervised IN-21k": "#55A868", "self-supervised": "#C44E52",
        "weakly supervised": "#8172B2", "vision-language": "#CCB974", "random": "#999999", "pixel": "red"}


# ------------------------------------------------------------------ helpers
def find_sheet(dirs, key):
    for d in dirs:
        for ext in ("xlsx", "csv"):
            for f in Path(d).rglob(f"*{key}*.{ext}"):
                if f.is_file():
                    return f
    return None


def load_sheets(dirs):
    meta = {}
    f1, f2 = find_sheet(dirs, "cross-sectional"), find_sheet(dirs, "longitudinal")
    for f, idcol in ((f1, "id"), (f2, "mri id")):
        if f is None:
            continue
        df = pd.read_csv(f) if f.suffix == ".csv" else pd.read_excel(f)
        cols = {c.lower().strip(): c for c in df.columns}
        for _, r in df.iterrows():
            meta[str(r[cols[idcol]]).strip()] = dict(
                cdr=pd.to_numeric(r.get(cols.get("cdr", ""), np.nan), errors="coerce"),
                age=pd.to_numeric(r.get(cols.get("age", ""), np.nan), errors="coerce"),
                sex=str(r.get(cols.get("m/f", ""), "")).strip())
    return meta, [str(f1), str(f2)]


def first_rows(scans):
    ok = scans[scans["ok"].astype(bool)]
    first, later = {}, {}
    for subj, g in ok.groupby("subject"):
        sess = sorted(g["session"].unique(), key=lambda s: int(s.split("_MR")[-1]))
        a = g[g["session"] == sess[0]].sort_values("scan")
        first[subj] = (int(a.index[0]), sess[0])
        if len(sess) >= 2:
            c = g[g["session"] == sess[1]].sort_values("scan")
            later[subj] = (int(c.index[0]), sess[1])
    return first, later


def make_tf(X, is_pix, seed=0):
    sc = StandardScaler().fit(X)
    if is_pix:
        pca = PCA(n_components=int(min(256, X.shape[0] - 1, X.shape[1])), random_state=seed).fit(sc.transform(X))
        return lambda Z: pca.transform(sc.transform(Z))
    return sc.transform


def l2(Z):
    return Z / np.clip(np.linalg.norm(Z, axis=-1, keepdims=True), 1e-8, None)


def offsets_of(cdir):
    return json.loads((cdir / "meta.json").read_text())["offsets"]


# ------------------------------------------------------------------ A: privacy-utility
def utility_job(feat_path, rows, y, is_pix, splits, repeats, seed):
    from sklearn.model_selection import RepeatedStratifiedKFold
    from sklearn.pipeline import make_pipeline
    feat = np.load(feat_path, mmap_mode="r")
    X = np.stack([np.asarray(feat[r, :, 0, :], dtype=np.float32).mean(axis=0) for r in rows])
    aucs = []
    for tr, te in RepeatedStratifiedKFold(n_splits=splits, n_repeats=repeats, random_state=seed).split(X, y):
        steps = [StandardScaler()]
        if is_pix:
            steps.append(PCA(n_components=int(min(128, len(tr) - 1, X.shape[1])), random_state=seed))
        steps.append(LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced"))
        clf = make_pipeline(*steps).fit(X[tr], y[tr])
        aucs.append(roc_auc_score(y[te], clf.predict_proba(X[te])[:, 1]))
    return float(np.mean(aucs)), float(np.std(aucs)), float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


def part_utility(args, names, info, meta):
    from joblib import Parallel, delayed
    from scipy.stats import spearmanr
    rows_out, corr_rows = [], []
    gen_tables = {}
    for src, path in (("regrid", Path(args.regrid_dir) / "regrid_gen.csv"), ("full", Path(args.full_dir) / "full_gen.csv")):
        if path.exists():
            gen_tables[src] = pd.read_csv(path)
    for cname, cd in UTIL_CONDS.items():
        cdir = Path(args.cache_root) / cd
        if not (cdir / "scans.csv").exists():
            T.log(f"[A] {cname}: cache missing")
            continue
        first, _ = first_rows(pd.read_csv(cdir / "scans.csv"))
        rows, y, age = [], [], []
        for subj, (row, sess) in first.items():
            if not sess.endswith("_MR1"):
                continue
            m = meta.get(sess)
            if m is None or not np.isfinite(m["cdr"]):
                continue
            rows.append(row)
            y.append(int(m["cdr"] > 0))
            age.append(m["age"])
        y = np.asarray(y)
        if len(y) < 30 or y.min() == y.max():
            T.log(f"[A] {cname}: not enough labelled subjects ({len(y)})")
            continue
        models = [m for m in names if (cdir / f"feats_{m}.npy").exists()]
        t0 = time.time()
        res = Parallel(n_jobs=args.n_jobs)(delayed(utility_job)(str(cdir / f"feats_{m}.npy"), rows, y, m == "pixel",
                                                                5, args.cv_repeats, args.seed) for m in models)
        # age-only baseline
        from sklearn.model_selection import RepeatedStratifiedKFold
        A = np.asarray(age, dtype=float).reshape(-1, 1)
        okA = np.isfinite(A[:, 0])
        aa = []
        for tr, te in RepeatedStratifiedKFold(n_splits=5, n_repeats=args.cv_repeats, random_state=args.seed).split(A[okA], y[okA]):
            c = LogisticRegression(class_weight="balanced").fit(A[okA][tr], y[okA][tr])
            aa.append(roc_auc_score(y[okA][te], c.predict_proba(A[okA][te])[:, 1]))
        T.log(f"[A] {cname}: {len(y)} subjects ({int(y.sum())} CDR>0), {len(models)} models ({time.time() - t0:.0f}s); "
              f"age-only AUC {np.mean(aa):.3f}")
        gsrc = ID_SRC[cname]
        gt = gen_tables.get(gsrc[0])
        gen = {}
        if gt is not None:
            q = gt.copy()
            for k, v in gsrc[1].items():
                q = q[q[k] == v]
            gen = dict(zip(q["model"], q["GEN"]))
        for m, (mu, sd, lo, hi) in zip(models, res):
            rows_out.append(dict(cond=cname, model=m, group=T.PT_GROUP.get(info[m][1], info[m][1]), family=info[m][0],
                                 n_subjects=len(y), n_pos=int(y.sum()), AUC=mu, AUC_sd=sd, AUC_lo=lo, AUC_hi=hi,
                                 GEN=gen.get(m, np.nan), age_only_AUC=float(np.mean(aa))))
        d = pd.DataFrame([r for r in rows_out if r["cond"] == cname])
        pre = d[~d["group"].isin(["pixel", "random"]) & d["GEN"].notna()]
        if len(pre) >= 6:
            rng = np.random.default_rng(args.seed)
            rho = spearmanr(pre["GEN"], pre["AUC"]).correlation
            bs = []
            for _ in range(args.boot):
                ii = rng.integers(0, len(pre), len(pre))
                bs.append(spearmanr(pre["GEN"].values[ii], pre["AUC"].values[ii]).correlation)
            lo, hi = T.ci(np.nan_to_num(bs))
            pareto = [r.model for r in pre.itertuples()
                      if not ((pre["AUC"] >= r.AUC) & (pre["GEN"] <= r.GEN) &
                              ((pre["AUC"] > r.AUC) | (pre["GEN"] < r.GEN))).any()]
            corr_rows.append(dict(cond=cname, n_encoders=len(pre), spearman_GEN_vs_AUC=rho, lo=lo, hi=hi,
                                  best_AUC_model=pre.loc[pre["AUC"].idxmax(), "model"], best_AUC=pre["AUC"].max(),
                                  pixel_AUC=d[d["model"] == "pixel"]["AUC"].iloc[0] if (d["model"] == "pixel").any() else np.nan,
                                  age_only_AUC=float(np.mean(aa)), pareto_low_identity_high_utility=", ".join(pareto)))
    return pd.DataFrame(rows_out), pd.DataFrame(corr_rows)


# ------------------------------------------------------------------ B: verification metrics
def fast_auc(g, i):
    from scipy.stats import rankdata
    r = rankdata(np.concatenate([g, i]))
    return float((r[:len(g)].sum() - len(g) * (len(g) + 1) / 2) / (len(g) * len(i)))


def verif_metrics(sims, rng, B, cap=50000):
    K, S, _ = sims.shape
    eye = np.eye(S, dtype=bool)
    gen = sims[:, eye].ravel()
    imp = sims[:, ~eye].ravel()
    y = np.r_[np.ones(len(gen)), np.zeros(len(imp))]
    sc = np.r_[gen, imp]
    auc = roc_auc_score(y, sc)
    fpr, tpr, _ = roc_curve(y, sc)
    eer = float(fpr[np.nanargmin(np.abs(fpr - (1 - tpr)))])
    tar = {f: float(np.interp(f, fpr, tpr)) for f in (1e-2, 1e-3)}
    r1 = float((sims.argmax(axis=2) == np.arange(S)[None, :]).mean())
    r1s = float((sims.mean(axis=0).argmax(axis=1) == np.arange(S)).mean())
    bs = []
    for _ in range(B):
        ii = rng.integers(0, S, S)
        sub = sims[:, ii][:, :, ii]
        same = ii[:, None] == ii[None, :]
        g = sub[:, np.eye(S, dtype=bool)].ravel()
        im = sub[:, ~same].ravel()
        if len(im) > cap:
            im = rng.choice(im, cap, replace=False)
        bs.append(fast_auc(g, im))
    lo, hi = T.ci(bs)
    return dict(AUC=auc, AUC_lo=lo, AUC_hi=hi, EER=eer, TAR_at_FAR1e2=tar[1e-2], TAR_at_FAR1e3=tar[1e-3],
                rank1_slice=r1, rank1_subject=r1s, S=S)


def verif_job(feat_path, pairs, offsets, dlist, is_pix, B, seed):
    feat = np.load(feat_path, mmap_mode="r")
    o0 = offsets.index(0)
    A = np.stack([np.asarray(feat[a, :, o0, :], dtype=np.float32) for a, _ in pairs])
    S, K, D = A.shape
    tf = make_tf(A.reshape(-1, D), is_pix, seed)
    GA = l2(tf(A.reshape(-1, D))).reshape(S, K, -1)
    rng = np.random.default_rng(seed)
    out = {}
    for d in dlist:
        if d not in offsets:
            continue
        Q = np.stack([np.asarray(feat[c, :, offsets.index(d), :], dtype=np.float32) for _, c in pairs])
        Q = l2(tf(Q.reshape(-1, D))).reshape(S, K, -1)
        out[d] = verif_metrics(np.einsum("ikd,jkd->kij", Q, GA), rng, B)
    return out


def part_verification(args, names, info):
    from joblib import Parallel, delayed
    rows = []
    rel = None
    try:
        it = pd.read_csv(Path(args.tide_out) / "index_t88.csv")
        rel = set(it[it["visit"] >= 2]["subject"])
    except Exception:  # noqa: BLE001
        pass
    for cname, cd in UTIL_CONDS.items():
        cdir = Path(args.cache_root) / cd
        if not (cdir / "scans.csv").exists():
            continue
        first, later = first_rows(pd.read_csv(cdir / "scans.csv"))
        subs = [s for s in later if s in first and (not cname.startswith("o1") or rel is None or s in rel)]
        if len(subs) < 5:
            continue
        pairs = [(first[s][0], later[s][0]) for s in subs]
        offs = offsets_of(cdir)
        mm = 1.25 if cname.endswith("raw") else 1.0
        dlist = [d for d in (0, 1, 2, 4) if d in offs]
        models = [m for m in names if (cdir / f"feats_{m}.npy").exists()]
        t0 = time.time()
        res = Parallel(n_jobs=args.n_jobs)(delayed(verif_job)(str(cdir / f"feats_{m}.npy"), pairs, offs, dlist,
                                                              m == "pixel", args.boot_verif, args.seed) for m in models)
        for m, r in zip(models, res):
            for d, mt in r.items():
                rows.append(dict(cond=cname, model=m, group=T.PT_GROUP.get(info[m][1], info[m][1]),
                                 offset_mm=d * mm, **mt))
        T.log(f"[B] {cname}: {len(pairs)} subjects, offsets {dlist} ({time.time() - t0:.0f}s)")
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ C: cross-dataset linkage
def link_feats(cdir, rows, model, tf=None, seed=0):
    feat = np.load(cdir / f"feats_{model}.npy", mmap_mode="r")
    X = np.stack([np.asarray(feat[r, :, 0, :], dtype=np.float32) for r in rows])
    N, K, D = X.shape
    if tf is None:
        tf = make_tf(X.reshape(-1, D), model == "pixel", seed)
    return l2(tf(X.reshape(-1, D))).reshape(N, K, -1), tf


def part_linkage(args, meta):
    out_rows, cand_rows, summary = [], [], []
    root = Path(args.cache_root)
    for var, off_dir, o2_dir, cal_dir in (("masked", "feats_oasis1_t88_masked_grid", "feats_oasis2_regmask",
                                           "feats_oasis1val_regmask"),
                                          ("gfc", "feats_oasis1_t88_gfc_grid", "feats_oasis2_reg", "feats_oasis1val_reg")):
        off_dir, o2_dir, cal_dir = root / off_dir, root / o2_dir, root / cal_dir
        if not all((d / "scans.csv").exists() for d in (off_dir, o2_dir, cal_dir)):
            T.log(f"[C] {var}: caches missing")
            continue
        gfirst, _ = first_rows(pd.read_csv(off_dir / "scans.csv"))
        gsub = sorted(gfirst)
        g_rows = [gfirst[s][0] for s in gsub]
        qfirst, _ = first_rows(pd.read_csv(o2_dir / "scans.csv"))
        qsub = sorted(qfirst)
        q_rows = [qfirst[s][0] for s in qsub]
        cfirst, _ = first_rows(pd.read_csv(cal_dir / "scans.csv"))
        csub = sorted(s for s in cfirst if s in gfirst and cfirst[s][1] == gfirst[s][1])
        c_rows = [cfirst[s][0] for s in csub]
        gidx = {s: i for i, s in enumerate(gsub)}
        top = {}
        for model in LINK_MODELS:
            if not (off_dir / f"feats_{model}.npy").exists():
                continue
            G, tf = link_feats(off_dir, g_rows, model, seed=args.seed)
            Qn, _ = link_feats(o2_dir, q_rows, model, tf)
            Cn, _ = link_feats(cal_dir, c_rows, model, tf)
            simQ = np.einsum("ikd,jkd->ij", Qn, G) / G.shape[1]
            simC = np.einsum("ikd,jkd->ij", Cn, G) / G.shape[1]
            gen = np.array([simC[i, gidx[s]] for i, s in enumerate(csub)])
            mask = np.ones_like(simC, dtype=bool)
            for i, s in enumerate(csub):
                mask[i, gidx[s]] = False
            imp = simC[mask]
            tau = float(max(np.quantile(imp, 0.999), np.quantile(simQ, 0.999)))
            recall = float((gen > tau).mean())
            best = simQ.argmax(axis=1)
            srt = np.sort(simQ, axis=1)
            margin = srt[:, -1] - srt[:, -2]
            top[model] = (best, simQ.max(axis=1), margin, tau)
            summary.append(dict(variant=var, model=model, n_gallery=len(gsub), n_queries=len(qsub),
                                n_calibration=len(csub), genuine_median=float(np.median(gen)),
                                impostor_q999=float(np.quantile(imp, 0.999)), tau=tau,
                                calibration_recall_at_tau=recall,
                                queries_above_tau=int((simQ.max(axis=1) > tau).sum())))
            out_rows += [dict(variant=var, model=model, kind="calibration genuine", score=float(v)) for v in gen]
            out_rows += [dict(variant=var, model=model, kind="calibration impostor", score=float(v))
                         for v in np.random.default_rng(0).choice(imp, min(5000, len(imp)), replace=False)]
            out_rows += [dict(variant=var, model=model, kind="OASIS-2 best match", score=float(v)) for v in simQ.max(axis=1)]
        if "pixel" not in top:
            continue
        for qi, qs in enumerate(qsub):
            votes = [gsub[top[m][0][qi]] for m in top]
            cand = gsub[top["pixel"][0][qi]]
            agree = sum(v == cand for v in votes)
            above = top["pixel"][1][qi] > top["pixel"][3]
            if agree >= 3 and above:
                mq, mg = meta.get(qfirst[qs][1], {}), meta.get(gfirst[cand][1], {})
                cand_rows.append(dict(variant=var, oasis2_subject=qs, oasis1_subject=cand, models_agreeing=agree,
                                      pixel_score=float(top["pixel"][1][qi]), pixel_margin=float(top["pixel"][2][qi]),
                                      sex_match=(mq.get("sex") == mg.get("sex")) if mq and mg else np.nan,
                                      age_oasis2_mr1=mq.get("age", np.nan), age_oasis1=mg.get("age", np.nan)))
        # random-pair baseline for sex agreement / age difference
        rng = np.random.default_rng(args.seed)
        sx, ad = [], []
        for _ in range(2000):
            mq = meta.get(qfirst[qsub[rng.integers(len(qsub))]][1], {})
            mg = meta.get(gfirst[gsub[rng.integers(len(gsub))]][1], {})
            if mq and mg:
                sx.append(mq.get("sex") == mg.get("sex"))
                ad.append(abs((mq.get("age") or np.nan) - (mg.get("age") or np.nan)))
        summary.append(dict(variant=var, model="random pairs", sex_agreement=float(np.mean(sx)),
                            median_abs_age_diff=float(np.nanmedian(ad))))
    C = pd.DataFrame(cand_rows)
    if not C.empty:
        C["abs_age_diff"] = (C["age_oasis2_mr1"] - C["age_oasis1"]).abs()
    return pd.DataFrame(summary), C, pd.DataFrame(out_rows)


# ------------------------------------------------------------------ D: correlation length
def part_lambda(args, params):
    from scipy.optimize import curve_fit
    from scipy.stats import spearmanr
    sets = []
    p1, p2 = Path(args.regrid_dir) / "regrid_curves.csv", Path(args.full_dir) / "full_curves.csv"
    if p1.exists():
        c = pd.read_csv(p1)
        c = c[c["probe"] == "logreg"]
        for cond, pool, sess in (("t88_masked", "all", "within"), ("t88_masked", "reliability", "rescan"),
                                 ("t88_gfc", "all", "within"), ("t88_gfc", "reliability", "rescan")):
            q = c[(c["cond"] == cond) & (c["pool"] == pool) & (c["design"] == "sparse") & (c["session"] == sess)]
            sets.append((f"OASIS-1 {cond} {pool} {sess}", q))
    if p2.exists():
        c = pd.read_csv(p2)
        c = c[c["probe"] == "logreg"]
        for cond, sess in (("o2_regmask", "cross"), ("o2_regmask", "within"), ("o2_reg", "cross")):
            q = c[(c["cond"] == cond) & (c["design"] == "sparse") & (c["session"] == sess)]
            sets.append((f"OASIS-2 {cond} {sess}", q))
    rows, corr = [], []
    f = lambda d, a, lam: a * np.exp(-d / lam)  # noqa: E731
    for name, q in sets:
        if q.empty:
            continue
        for m, g in q.groupby("model"):
            g = g.sort_values("d_mm")
            x, y = g["d_mm"].values.astype(float), g["mean"].values.astype(float)
            try:
                (a, lam), _ = curve_fit(f, x, y, p0=(1.0, 3.0), bounds=([0, 0.05], [1.5, 500]), maxfev=20000)
                r2 = 1 - np.sum((y - f(x, a, lam)) ** 2) / max(np.sum((y - y.mean()) ** 2), 1e-12)
            except Exception:  # noqa: BLE001
                a = lam = r2 = np.nan
            rows.append(dict(curve=name, model=m, group=g["group"].iloc[0], a=a, lambda_mm=lam, R2=r2,
                             params_M=params.get(m, np.nan)))
        d = pd.DataFrame([r for r in rows if r["curve"] == name])
        for fam_name, fam in (("all pretrained", None),):
            pre = d[~d["group"].isin(["pixel", "random"]) & d["lambda_mm"].notna() & d["params_M"].notna()]
            if len(pre) >= 6:
                corr.append(dict(curve=name, subset=fam_name, spearman_logparams_vs_lambda=spearmanr(
                    np.log10(pre["params_M"]), pre["lambda_mm"]).correlation,
                    pixel_lambda=d[d["model"] == "pixel"]["lambda_mm"].iloc[0] if (d["model"] == "pixel").any() else np.nan,
                    median_lambda=pre["lambda_mm"].median()))
    return pd.DataFrame(rows), pd.DataFrame(corr)


# ------------------------------------------------------------------ figures + report
def figures(U, V, Lsum, Ldist, LAM, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fd = out / "figures"
    fd.mkdir(exist_ok=True)
    if not U.empty:
        for cname, d in U.groupby("cond"):
            d = d[d["GEN"].notna()]
            if d.empty:
                continue
            fig, ax = plt.subplots(figsize=(5.2, 4.4))
            for gname, g in d.groupby("group"):
                ax.scatter(g["GEN"], g["AUC"], color=GCOL.get(gname, "#333"), s=26 if gname != "pixel" else 60,
                           label=gname, marker="*" if gname == "pixel" else "o", zorder=3)
            for r in d.itertuples():
                if r.model in ("pixel", "mae_vitb16", "dino_vits16", "clip_vitb16_openai", "biomedclip_vitb16"):
                    ax.annotate(r.model, (r.GEN, r.AUC), fontsize=6)
            ax.axhline(d["age_only_AUC"].iloc[0], color="k", ls=":", lw=0.8, label="age-only AUC")
            ax.set_xlabel("Identity (GEN, chance-adjusted)")
            ax.set_ylabel("Diagnosis AUC (CDR>0, subject-level CV)")
            ax.set_title(f"{cname}: privacy-utility", fontsize=9)
            ax.legend(fontsize=6)
            fig.tight_layout()
            fig.savefig(fd / f"privacy_utility_{cname}.png", dpi=170)
            plt.close(fig)
    if not V.empty:
        for cname, d in V.groupby("cond"):
            fig, ax = plt.subplots(figsize=(5.2, 4.2))
            for m, g in d.groupby("model"):
                g = g.sort_values("offset_mm")
                gname = g["group"].iloc[0]
                if m == "pixel":
                    ax.plot(g["offset_mm"], g["AUC"], "o-", color="red", lw=2.2, label="pixel", zorder=5)
                else:
                    ax.plot(g["offset_mm"], g["AUC"], color=GCOL.get(gname, "#4C72B0"), lw=0.7, alpha=0.5)
            ax.set_xlabel("Offset from MR1 slice (mm)")
            ax.set_ylabel("Verification AUC (same vs different person)")
            ax.set_title(f"{cname}: verification (pool-size free)", fontsize=9)
            ax.legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(fd / f"verification_{cname}.png", dpi=170)
            plt.close(fig)
    if not Ldist.empty:
        for var, d in Ldist.groupby("variant"):
            q = d[d["model"] == "pixel"]
            if q.empty:
                continue
            fig, ax = plt.subplots(figsize=(6, 4))
            for kind, col in (("calibration impostor", "#999999"), ("calibration genuine", "green"),
                              ("OASIS-2 best match", "#4C72B0")):
                v = q[q["kind"] == kind]["score"]
                if len(v):
                    ax.hist(v, bins=60, alpha=0.55, density=True, color=col, label=kind)
            t = Lsum[(Lsum["variant"] == var) & (Lsum["model"] == "pixel")]
            if len(t):
                ax.axvline(t["tau"].iloc[0], color="k", ls="--", lw=1, label="threshold")
            ax.set_xlabel("Mean slice cosine similarity (pixel)")
            ax.set_title(f"Cross-dataset linkage audit ({var})", fontsize=9)
            ax.legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(fd / f"linkage_{var}.png", dpi=170)
            plt.close(fig)
    if not LAM.empty:
        for name, d in LAM.groupby("curve"):
            d = d.sort_values("lambda_mm")
            y = np.arange(len(d))
            fig, ax = plt.subplots(figsize=(5.5, 0.27 * len(d) + 1.3))
            ax.barh(y, d["lambda_mm"], color=[GCOL.get(g, "#4C72B0") for g in d["group"]])
            ax.set_yticks(y)
            ax.set_yticklabels(d["model"], fontsize=7)
            ax.set_xlabel("Identity correlation length lambda (mm)")
            ax.set_title(name, fontsize=9)
            fig.tight_layout()
            fig.savefig(fd / f"lambda_{name.replace(' ', '_')}.png", dpi=170)
            plt.close(fig)


def report(U, Ucorr, V, Lsum, Lcand, LAM, LAMc, out, elapsed, sheets):
    try:
        import tabulate  # noqa: F401
    except ImportError:
        pd.DataFrame.to_markdown = lambda self, index=False, **kw: "```\n" + self.to_string(index=index) + "\n```"
    L = ["# TIDE extras", "", f"Total time: {elapsed / 60:.1f} min; sheets: {sheets}", ""]
    if not Ucorr.empty:
        L += ["## A. Privacy-utility (identity GEN vs diagnosis AUC across pretrained encoders)", "",
              Ucorr.round(3).to_markdown(index=False), ""]
        top = U.sort_values(["cond", "AUC"], ascending=[True, False]).groupby("cond").head(5)
        L += ["Top-5 AUC per condition:", "", top[["cond", "model", "AUC", "AUC_lo", "AUC_hi", "GEN"]].round(3)
              .to_markdown(index=False), ""]
    if not V.empty:
        L += ["## B. Verification (attack-style)", ""]
        for (cname, off), d in V.groupby(["cond", "offset_mm"]):
            pre = d[~d["group"].isin(["pixel", "random"])]
            px = d[d["model"] == "pixel"]
            L.append(f"- {cname} @ {off:g} mm (S={int(d['S'].iloc[0])}): pixel AUC "
                     f"{px['AUC'].iloc[0]:.3f} EER {px['EER'].iloc[0]:.3f} TAR@1%FAR {px['TAR_at_FAR1e2'].iloc[0]:.3f} "
                     f"rank-1(subject) {px['rank1_subject'].iloc[0]:.3f}; encoders AUC median {pre['AUC'].median():.3f} "
                     f"(range {pre['AUC'].min():.3f}-{pre['AUC'].max():.3f}), best {pre.loc[pre['AUC'].idxmax(), 'model']}")
        L.append("")
    if not Lsum.empty:
        L += ["## C. Cross-dataset linkage audit (OASIS-2 queries vs 416 OASIS-1 subjects)", "",
              Lsum.round(3).to_markdown(index=False), ""]
        if Lcand.empty:
            L.append("No query passed the threshold with >= 3 of 4 models agreeing.")
        else:
            for var, c in Lcand.groupby("variant"):
                L.append(f"- {var}: {len(c)} candidate cross-dataset matches; sex agreement {c['sex_match'].mean():.2f}; "
                         f"median |age difference| {c['abs_age_diff'].median():.1f} y (compare with random pairs above)")
            L.append("(Candidate IDs are in linkage_candidates.csv for internal verification only - report counts, "
                     "not identities.)")
        L.append("")
    if not LAMc.empty:
        L += ["## D. Identity correlation length (lambda, mm)", "", LAMc.round(3).to_markdown(index=False), ""]
        for name, d in LAM.groupby("curve"):
            pre = d[~d["group"].isin(["pixel", "random"])].sort_values("lambda_mm", ascending=False)
            L.append(f"- {name}: top3 " + ", ".join(f"{r.model} {r.lambda_mm:.2f}" for r in pre.head(3).itertuples())
                     + "; bottom3 " + ", ".join(f"{r.model} {r.lambda_mm:.2f}" for r in pre.tail(3).itertuples())
                     + f"; median R2 {d['R2'].median():.2f}")
        L.append("")
    (out / "REPORT_EXTRAS.md").write_text("\n".join(L), encoding="utf-8")


def main():
    from encode_slices import REGISTRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-root", default=".")
    ap.add_argument("--regrid-dir", default="tide_regrid_oasis1")
    ap.add_argument("--full-dir", default="tide_full_oasis2")
    ap.add_argument("--tide-out", default="tide_oasis1")
    ap.add_argument("--sheet-dirs", nargs="+", default=["Datasets", "."])
    ap.add_argument("--out", default="tide_extras")
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--cv-repeats", type=int, default=5)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--boot-verif", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--parts", nargs="+", default=["A", "B", "C", "D"])
    a = ap.parse_args()
    t0 = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    T.LOGFILE = out / "extras_log.txt"
    names = ["pixel"] + list(REGISTRY)
    info = {"pixel": ("floor", "pixel"), **{k: (v[4], v[5]) for k, v in REGISTRY.items()}}
    meta, sheets = load_sheets(a.sheet_dirs)
    params = T.count_params(Path(a.tide_out))
    T.log(f"TIDE extras started | clinical rows {len(meta)} | parts {a.parts}")
    U = Uc = V = Ls = Lc = Ld = LAM = LAMc = pd.DataFrame()
    for part, fn in (("A", lambda: part_utility(a, names, info, meta)), ("B", lambda: part_verification(a, names, info)),
                     ("C", lambda: part_linkage(a, meta)), ("D", lambda: part_lambda(a, params))):
        if part not in a.parts:
            continue
        t1 = time.time()
        try:
            res = fn()
            if part == "A":
                U, Uc = res
                U.to_csv(out / "privacy_utility.csv", index=False)
                Uc.to_csv(out / "privacy_utility_summary.csv", index=False)
            elif part == "B":
                V = res
                V.to_csv(out / "verification.csv", index=False)
            elif part == "C":
                Ls, Lc, Ld = res
                Ls.to_csv(out / "linkage_summary.csv", index=False)
                Lc.to_csv(out / "linkage_candidates.csv", index=False)
            else:
                LAM, LAMc = res
                LAM.to_csv(out / "correlation_length.csv", index=False)
                LAMc.to_csv(out / "correlation_length_summary.csv", index=False)
            T.log(f"[part {part}] done ({(time.time() - t1) / 60:.1f} min)")
        except Exception as e:  # noqa: BLE001
            import traceback
            T.log(f"[part {part}] FAILED: {e!r}\n{traceback.format_exc()}")
    try:
        figures(U, V, Ls, Ld, LAM, out)
    except Exception as e:  # noqa: BLE001
        T.log(f"[fig] {e!r}")
    report(U, Uc, V, Ls, Lc, LAM, LAMc, out, time.time() - t0, sheets)
    T.log(f"DONE in {(time.time() - t0) / 60:.1f} min -> {out}")


if __name__ == "__main__":
    main()
