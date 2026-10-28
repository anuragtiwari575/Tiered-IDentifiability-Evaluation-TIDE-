#!/usr/bin/env python3
"""
tide_run.py - TIDE (Tiered IDentifiability Evaluation): complete OASIS-1 run, one command.

Every stage resumes: finished outputs are reused, so after a crash just re-run the same command.

  1. Index OASIS-1 PROCESSED atlas volumes (T88_111):
       *_t88_gfc.hdr          -> registered (skull present)
       *_t88_masked_gfc.hdr   -> registered + skull-stripped
  2. Cache their slices with the same K positions / offsets as the raw cache
  3. Encode them with all 33 encoders + pixel floor
  4. Probes for every condition (raw / t88_gfc / t88_masked) x pool (all, reliability) x model:
       - TIDE tiers with fixed n_fit (logreg + cosine 1-NN) + permuted-label control (sigma, as in SIA)
       - SIA-mode baseline: SIA Stage-3 protocol (50/50 split of one acquisition's slices), same n_fit
       - near-duplicate injection into the cross-session eval set
       - matched-size subsamples (S=20, 50) of the 'all' pool
       - positive control: identity-supervised PCA+LDA head learned on disjoint subjects (raw only)
  5. Statistics: subject-level paired bootstrap, rank CIs, discriminability (SIA-mode vs TIDE),
     encoder gain over pixel floor, pretraining / family factors, capacity, probe geometry,
     preprocessing ladder (raw -> registered -> skull-stripped), duplicate injection, positive control
  6. Figures + REPORT.md

Usage (from the project folder, next to extract_features.py and encode_slices.py):
  python tide_run.py --raw-cache feats_oasis1_v2 --oasis1-dir Datasets --out tide_oasis1
"""
import argparse
import contextlib
import json
import os
import pickle
import re
import sys
import time
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sklearn.decomposition import PCA  # noqa: E402
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis  # noqa: E402
from sklearn.exceptions import ConvergenceWarning  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

WITHIN = ["same_scan_adjacent", "same_scan_far", "repeat_scan"]
CROSS = ["rescan_90d", "next_visit"]
CROSS_POOLS = {"rescan_90d": "reliability", "next_visit": "longitudinal"}
DUP_FRACS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
PT_GROUP = {"IN1k": "supervised IN-1k", "IN21k": "supervised IN-21k", "SSL": "self-supervised",
            "weak/semi-sup": "weakly supervised", "CLIP": "vision-language",
            "medical CLIP": "vision-language", "random": "random", "pixel": "pixel"}
SESS1 = re.compile(r"(OAS1_(\d{4})_MR(\d+))")
LOGFILE = None


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    if LOGFILE is not None:
        with open(LOGFILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


# =============================================================== stage 1-3: T88 data
def build_t88_index(oasis1_dir):
    rows = []
    for hdr in Path(oasis1_dir).rglob("*_t88_*gfc.hdr"):
        name = hdr.name
        if name.endswith("_t88_masked_gfc.hdr"):
            var = "t88_masked"
        elif name.endswith("_t88_gfc.hdr"):
            var = "t88_gfc"
        else:
            continue
        m = SESS1.search(name)
        if not m:
            continue
        if not hdr.with_suffix(".img").exists():
            log(f"  [warn] missing .img for {hdr}")
            continue
        rows.append(dict(dataset="OASIS1", subject=f"OAS1_{m.group(2)}", session=m.group(1),
                         visit=int(m.group(3)), scan=1, variant=var, path=str(hdr.resolve())))
    if not rows:
        return pd.DataFrame()
    return (pd.DataFrame(rows).drop_duplicates(["variant", "session"])
            .sort_values(["variant", "subject", "visit"]).reset_index(drop=True))


def cache_condition(idx, cdir, k, band, offsets, axis, workers):
    import torch
    from extract_features import ScanSlices, first
    final = cdir / "slices_uint8.npy"
    if final.exists() and (cdir / "scans.csv").exists():
        log(f"[cache] {cdir.name}: exists, reusing")
        return
    cdir.mkdir(parents=True, exist_ok=True)
    idx = idx.reset_index(drop=True)
    n = len(idx)
    ok = np.zeros(n, dtype=bool)
    errs, poss, axes = [""] * n, [""] * n, [-1] * n
    loader = torch.utils.data.DataLoader(ScanSlices(idx["path"], k, band, offsets, axis),
                                         batch_size=1, num_workers=workers, collate_fn=first)
    tmp = cdir / "slices_uint8.npy.part"
    arr, t0 = None, time.time()
    for done, (i, sl, pos, ax, err) in enumerate(loader, 1):
        if err:
            errs[i] = err
            continue
        s = (sl.numpy() * 255.0).round().astype(np.uint8)
        if arr is None:
            arr = np.lib.format.open_memmap(tmp, mode="w+", dtype=np.uint8, shape=(n, *s.shape))
        if s.shape != arr.shape[1:]:
            errs[i] = f"slice shape {s.shape} != {arr.shape[1:]}"
            continue
        arr[i] = s
        ok[i], poss[i], axes[i] = True, " ".join(map(str, pos)), ax
        if done % 100 == 0:
            log(f"  [cache] {cdir.name}: {done}/{n} ({time.time() - t0:.0f}s)")
    if arr is None:
        log(f"[cache] {cdir.name}: nothing readable")
        return
    shape = arr.shape
    arr.flush()
    del arr
    os.replace(tmp, final)
    idx.assign(ok=ok, error=errs, positions=poss, axis_used=axes).to_csv(cdir / "scans.csv", index=False)
    (cdir / "meta.json").write_text(json.dumps(dict(k=k, band=list(band), offsets=list(offsets), axis=axis,
                                                    source="tide_run.py"), indent=2))
    log(f"[cache] {cdir.name}: {ok.sum()}/{n} ok, {shape}, {time.time() - t0:.0f}s")


def encode_condition(cdir, names, input_size, pixel_size, spb):
    import torch
    import torch.nn.functional as F
    from encode_slices import REGISTRY, build, write_feats
    sl = np.load(cdir / "slices_uint8.npy", mmap_mode="r")
    n, K, O, H, W = sl.shape
    ok_rows = np.where(pd.read_csv(cdir / "scans.csv")["ok"].astype(bool).values)[0]
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp = (torch.autocast(device_type="cuda", dtype=torch.float16)
           if dev.type == "cuda" else contextlib.nullcontext())
    for name in names:
        out = cdir / f"feats_{name}.npy"
        if out.exists():
            continue
        t0 = time.time()
        if name == "pixel":
            def gen():
                for s in range(0, len(ok_rows), spb):
                    rr = ok_rows[s:s + spb]
                    x = torch.from_numpy(np.asarray(sl[rr])).to(dev).float().div_(255.0).view(-1, 1, H, W)
                    f = F.adaptive_avg_pool2d(x, pixel_size).flatten(1)
                    yield rr, f.view(len(rr), K, O, -1).half().cpu().numpy()
            write_feats(out, ok_rows, n, K, O, gen())
            log(f"  [enc] {cdir.name}/pixel ({time.time() - t0:.0f}s)")
            continue
        if name not in REGISTRY:
            continue
        try:
            m, mean, std = build(name, dev)
        except Exception as e:  # noqa: BLE001
            log(f"  [enc] {cdir.name}/{name}: build failed ({e})")
            continue

        def gen():
            with torch.no_grad():
                for s in range(0, len(ok_rows), spb):
                    rr = ok_rows[s:s + spb]
                    x = torch.from_numpy(np.asarray(sl[rr])).to(dev).float().div_(255.0).view(-1, 1, H, W)
                    x = F.interpolate(x, size=(input_size, input_size), mode="bilinear",
                                      align_corners=False).repeat(1, 3, 1, 1)
                    with amp:
                        f = m((x - mean) / std)
                    yield rr, f.float().view(len(rr), K, O, -1).half().cpu().numpy()
        try:
            write_feats(out, ok_rows, n, K, O, gen())
            log(f"  [enc] {cdir.name}/{name} ({time.time() - t0:.0f}s)")
        except Exception as e:  # noqa: BLE001
            log(f"  [enc] {cdir.name}/{name}: failed ({e})")
        del m
        if dev.type == "cuda":
            torch.cuda.empty_cache()


def count_params(out):
    p = out / "params.csv"
    if p.exists():
        return dict(pd.read_csv(p).values)
    import timm
    from encode_slices import REGISTRY
    rows = []
    for name, (src, mid, _pre, kw, _fam, _pt) in REGISTRY.items():
        try:
            if src == "timm":
                m = timm.create_model(mid, pretrained=False, num_classes=0, **kw)
                n = sum(x.numel() for x in m.parameters())
            else:
                m = timm.create_model("vit_base_patch16_224", pretrained=False, num_classes=0)
                n = sum(x.numel() for x in m.parameters()) + 768 * 512
            rows.append((name, n / 1e6))
            del m
        except Exception as e:  # noqa: BLE001
            log(f"  [params] {name}: {e}")
    pd.DataFrame(rows, columns=["model", "params_M"]).to_csv(p, index=False)
    return dict(rows)


# =============================================================== stage 4: probes
def subject_records(scans, oi):
    o0, o1, of = oi
    ok = scans[scans["ok"].astype(bool)]
    recs = []
    for subj, g in ok.groupby("subject"):
        sess = sorted(g["session"].unique(), key=lambda s: int(s.split("_MR")[-1]))
        first = g[g["session"] == sess[0]].sort_values("scan")
        a = int(first.index[0])
        tiers = {"same_scan_adjacent": (a, o1), "same_scan_far": (a, of)}
        if len(first) >= 2:
            tiers["repeat_scan"] = (int(first.index[1]), o0)
        if len(sess) >= 2:
            nxt = int(g[g["session"] == sess[1]].sort_values("scan").index[0])
            tiers["rescan_90d" if g["dataset"].iloc[0] == "OASIS1" else "next_visit"] = (nxt, o0)
        recs.append(dict(subject=subj, a=a, fit=(a, o0), tiers=tiers))
    return recs


def make_pools(recs):
    W = [t for t in WITHIN if recs and np.mean([t in r["tiers"] for r in recs]) >= 0.9]
    pools = {}
    allm = [r for r in recs if all(t in r["tiers"] for t in W)]
    if allm:
        pools["all"] = (allm, W)
    for c in CROSS:
        mem = [r for r in allm if c in r["tiers"]]
        if len(mem) >= 5:
            pools[CROSS_POOLS[c]] = (mem, W + [c])
    return pools


def _l2(Z):
    return Z / np.clip(np.linalg.norm(Z, axis=1, keepdims=True), 1e-8, None)


def _per_subj(pred, y, S):
    return np.bincount(y, weights=(pred == y).astype(float), minlength=S) / np.bincount(y, minlength=S)


def _fit_tf(Xf, is_pix, seed):
    sc = StandardScaler().fit(Xf)
    if is_pix:
        pca = PCA(n_components=int(min(256, Xf.shape[0] - 1, Xf.shape[1])), random_state=seed)
        pca.fit(sc.transform(Xf))
        return lambda X: pca.transform(sc.transform(X))
    return sc.transform


def _feats(feat, row, oi):
    return np.asarray(feat[row, :, oi, :], dtype=np.float32)


def _lr():
    return LogisticRegression(C=1.0, max_iter=3000)


def run_full(feat, recs, tiers, is_pix, seed, oi, cross=None, light=False):
    S, K = len(recs), feat.shape[1]
    rng = np.random.default_rng(seed)
    o0, _o1, of = oi
    Xf = np.concatenate([_feats(feat, *r["fit"]) for r in recs])
    yf = np.repeat(np.arange(S), K)
    tf = _fit_tf(Xf, is_pix, seed)
    Zf = tf(Xf)
    clf = _lr().fit(Zf, yf)
    out = {"tide": {}}
    if not light:
        clf_c = _lr().fit(Zf, rng.permutation(yf))
        Zfn = _l2(Zf)
        out["ctrl"] = {}
    evals = {}
    for t in tiers:
        Xe = np.concatenate([_feats(feat, *r["tiers"][t]) for r in recs])
        evals[t] = Xe
        Ze = tf(Xe)
        res = {"logreg": _per_subj(clf.predict(Ze), yf, S)}
        if not light:
            res["1nn"] = _per_subj(yf[np.argmax(_l2(Ze) @ Zfn.T, axis=1)], yf, S)
            out["ctrl"][t] = _per_subj(clf_c.predict(Ze), yf, S)
        out["tide"][t] = res
    if light:
        return out
    if cross in tiers and "same_scan_adjacent" in tiers:
        Xc = evals[cross].reshape(S, K, -1)
        Xa = evals["same_scan_adjacent"].reshape(S, K, -1)
        out["dup"] = {}
        for f in DUP_FRACS:
            nr = int(round(f * K))
            Xd = Xc.copy()
            Xd[:, :nr] = Xa[:, :nr]
            out["dup"][f] = _per_subj(clf.predict(tf(Xd.reshape(S * K, -1))), yf, S)
    # SIA-mode: 50/50 split of the 2K slices (offset 0 + far offset) of ONE acquisition, n_fit = K
    Xsf, Xse = [], []
    for r in recs:
        x = np.concatenate([_feats(feat, r["a"], o0), _feats(feat, r["a"], of)])
        p = rng.permutation(len(x))
        Xsf.append(x[p[:K]])
        Xse.append(x[p[K:2 * K]])
    Xsf, Xse = np.concatenate(Xsf), np.concatenate(Xse)
    tfs = _fit_tf(Xsf, is_pix, seed)
    Zsf, Zse = tfs(Xsf), tfs(Xse)
    cs = _lr().fit(Zsf, yf)
    cs_c = _lr().fit(Zsf, rng.permutation(yf))
    out["sia"] = {"logreg": _per_subj(cs.predict(Zse), yf, S),
                  "1nn": _per_subj(yf[np.argmax(_l2(Zse) @ _l2(Zsf).T, axis=1)], yf, S),
                  "ctrl": _per_subj(cs_c.predict(Zse), yf, S)}
    return out


def job(feat_path, recs, tiers, is_pix, seed, oi, cross, light, sub_size=None):
    feat = np.load(feat_path, mmap_mode="r")
    if sub_size:
        pick = np.random.default_rng(seed).choice(len(recs), sub_size, replace=False)
        recs = [recs[i] for i in pick]
    return run_full(feat, recs, tiers, is_pix, seed, oi, cross, light)


def lda_transform_all(feat, train_recs, ok_rows, seed, ncomp=256):
    """Positive control: identity-supervised PCA(256)+LDA head fit on subjects disjoint from the eval pool."""
    rows, ys = [], []
    for j, r in enumerate(train_recs):
        for row in [r["a"]] + ([r["tiers"]["repeat_scan"][0]] if "repeat_scan" in r["tiers"] else []):
            rows.append(row)
            ys.append(j)
    n, K, O, D = feat.shape
    X = np.asarray(feat[rows], dtype=np.float32).reshape(-1, D)
    y = np.repeat(np.asarray(ys), K * O)
    sc = StandardScaler().fit(X)
    pca = PCA(n_components=int(min(256, D, X.shape[0] - 1)), random_state=seed).fit(sc.transform(X))
    Z = pca.transform(sc.transform(X))
    lda = LinearDiscriminantAnalysis(solver="eigen", shrinkage="auto",
                                     n_components=int(min(ncomp, len(train_recs) - 1, Z.shape[1]))).fit(Z, y)
    d = lda.transform(Z[:2]).shape[1]
    T = np.zeros((n, K, O, d), dtype=np.float32)
    for s in range(0, len(ok_rows), 64):
        rr = ok_rows[s:s + 64]
        x = np.asarray(feat[rr], dtype=np.float32).reshape(-1, D)
        T[rr] = lda.transform(pca.transform(sc.transform(x))).reshape(len(rr), K, O, d)
    return T


def probe_condition(cname, cdir, models, args, out):
    from joblib import Parallel, delayed
    pk = out / f"probes_{cname}.pkl"
    if pk.exists() and not args.redo_probes:
        log(f"[probe] {cname}: reusing {pk.name}")
        with open(pk, "rb") as fh:
            return pickle.load(fh)
    scans = pd.read_csv(cdir / "scans.csv")
    meta = json.loads((cdir / "meta.json").read_text())
    offs = meta["offsets"]
    oi = (offs.index(0), offs.index(1), offs.index(max(offs)))
    recs = subject_records(scans, oi)
    pools = make_pools(recs)
    R = {"pools": {p: {"subjects": [r["subject"] for r in rr], "tiers": tt} for p, (rr, tt) in pools.items()},
         "full": {}, "sub": {}, "posctrl": {}}
    for p, (rr, tt) in pools.items():
        cross = next((t for t in tt if t in CROSS), None)
        t0 = time.time()
        outs = Parallel(n_jobs=args.n_jobs)(
            delayed(job)(str(cdir / f"feats_{m}.npy"), rr, tt, m == "pixel", args.seed, oi, cross, False)
            for m in models)
        R["full"][p] = dict(zip(models, outs))
        log(f"[probe] {cname}/{p}: {len(rr)} subjects, tiers {tt}, {len(models)} models ({time.time() - t0:.0f}s)")
        if p == "all":
            for s in args.pool_sizes:
                if s >= len(rr):
                    continue
                t0 = time.time()
                tasks = [(m, r) for m in models for r in range(args.repeats)]
                outs = Parallel(n_jobs=args.n_jobs)(
                    delayed(job)(str(cdir / f"feats_{m}.npy"), rr, tt, m == "pixel",
                                 args.seed * 1000 + r, oi, None, True, s) for m, r in tasks)
                R["sub"].setdefault(p, {})[s] = {}
                for (m, _r), o in zip(tasks, outs):
                    R["sub"][p][s].setdefault(m, []).append(o)
                log(f"[probe] {cname}/{p}: S={s} x {args.repeats} repeats ({time.time() - t0:.0f}s)")
    if cname == "raw" and "reliability" in pools and "all" in pools:
        rel_ids = set(R["pools"]["reliability"]["subjects"])
        train = [r for r in pools["all"][0] if r["subject"] not in rel_ids]
        ok_rows = np.where(scans["ok"].astype(bool).values)[0]
        rr, tt = pools["reliability"]
        cross = next(t for t in tt if t in CROSS)
        for m in [x for x in args.posctrl_models if x in models]:
            t0 = time.time()
            try:
                T = lda_transform_all(np.load(cdir / f"feats_{m}.npy", mmap_mode="r"), train, ok_rows, args.seed)
                R["posctrl"][m] = run_full(T, rr, tt, False, args.seed, oi, cross, False)
                log(f"[posctrl] {m}+LDA ({time.time() - t0:.0f}s)")
            except Exception as e:  # noqa: BLE001
                log(f"[posctrl] {m}: failed ({e})")
    with open(pk, "wb") as fh:
        pickle.dump(R, fh)
    return R


# =============================================================== stage 5: statistics
def adj(v, S):
    return (np.asarray(v, dtype=np.float64) - 1.0 / S) / (1.0 - 1.0 / S)


def boot_vec(v, B, rng):
    v = np.asarray(v, dtype=np.float64)
    return v[rng.integers(0, len(v), size=(B, len(v)))].mean(axis=1)


def boot_means(A, B, rng):
    A = np.atleast_2d(np.asarray(A, dtype=np.float64))
    idx = rng.integers(0, A.shape[1], size=(B, A.shape[1]))
    return np.stack([A[:, i].mean(axis=1) for i in idx])          # B x M


def ci(x):
    return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))


def pair_stats(A, Mb):
    M = A.shape[0]
    means = A.mean(axis=1)
    d = Mb[:, :, None] - Mb[:, None, :]
    lo, hi = np.percentile(d, 2.5, axis=0), np.percentile(d, 97.5, axis=0)
    iu = np.triu_indices(M, 1)
    sig = ((lo > 0) | (hi < 0))[iu]
    return dict(n_models=M, mean=float(means.mean()), sd=float(means.std(ddof=1)), min=float(means.min()),
                max=float(means.max()), range=float(np.ptp(means)), n_ge_0p95=int((means >= 0.95).sum()),
                frac_pairs_significant=float(sig.mean()))


def summarize(Rs, B, seed, out):
    rng = np.random.default_rng(seed)
    rows, long = [], []
    for cname, R in Rs.items():
        for pool, P in R["full"].items():
            subs = R["pools"][pool]["subjects"]
            S, tiers = len(subs), R["pools"][pool]["tiers"]
            for m, o in P.items():
                mets = {}
                for t in tiers:
                    for pr, v in o["tide"][t].items():
                        mets[("tide", t, pr)] = v
                    mets[("ctrl", t, "logreg")] = o["ctrl"][t]
                for pr, v in o["sia"].items():
                    mets[("sia", "within_50_50", pr)] = v
                for f, v in o.get("dup", {}).items():
                    mets[("dup", f"{f:.1f}", "logreg")] = v
                for (kind, tier, probe), v in mets.items():
                    a = adj(v, S)
                    lo, hi = ci(boot_vec(a, B, rng))
                    rows.append(dict(cond=cname, pool=pool, size=S, model=m, kind=kind, tier=tier, probe=probe,
                                     mean_adj=a.mean(), lo_adj=lo, hi_adj=hi, mean_raw=float(np.mean(v))))
                    long += [dict(cond=cname, pool=pool, model=m, kind=kind, tier=tier, probe=probe,
                                  subject=s, acc=float(x)) for s, x in zip(subs, v)]
        for pool, sizes in R["sub"].items():
            for s, mm in sizes.items():
                for m, lst in mm.items():
                    for t in lst[0]["tide"]:
                        vals = np.array([adj(o["tide"][t]["logreg"].mean(), s) for o in lst])
                        rows.append(dict(cond=cname, pool=f"{pool}_S{s}", size=s, model=m, kind="tide", tier=t,
                                         probe="logreg", mean_adj=vals.mean(), lo_adj=np.percentile(vals, 2.5),
                                         hi_adj=np.percentile(vals, 97.5), mean_raw=np.nan))
        if R["posctrl"]:
            S = len(R["pools"]["reliability"]["subjects"])
            for m, o in R["posctrl"].items():
                for t, d in o["tide"].items():
                    a = adj(d["logreg"], S)
                    lo, hi = ci(boot_vec(a, B, rng))
                    rows.append(dict(cond=cname, pool="reliability", size=S, model=f"{m}+LDA", kind="tide", tier=t,
                                     probe="logreg", mean_adj=a.mean(), lo_adj=lo, hi_adj=hi,
                                     mean_raw=float(np.mean(d["logreg"]))))
    summ = pd.DataFrame(rows)
    summ.to_csv(out / "summary_all.csv", index=False)
    pd.DataFrame(long).to_csv(out / "per_subject_long.csv", index=False)
    return summ


def analyze(Rs, info, params, out, B, seed):
    rng = np.random.default_rng(seed + 1)
    T = {k: [] for k in ["within", "disc", "ranks", "fac", "cap", "geo", "dup", "pos", "ladder"]}
    for cname, R in Rs.items():
        if "all" in R["full"]:
            P = R["full"]["all"]
            S, tiers = len(R["pools"]["all"]["subjects"]), R["pools"]["all"]["tiers"]
            pre = [m for m in P if info[m][1] not in ("pixel", "random")]
            getters = [("SIA-mode (50/50 within acquisition)", lambda o: o["sia"]["logreg"])]
            getters += [(f"TIDE {t}", (lambda tt: lambda o: o["tide"][tt]["logreg"])(t)) for t in tiers]
            for label, g in getters:
                A = np.stack([adj(g(P[m]), S) for m in pre])
                T["within"].append(dict(cond=cname, pool="all", S=S, protocol=label,
                                        **pair_stats(A, boot_means(A, B, rng))))
        for pool in [p for p in R["full"] if p in CROSS_POOLS.values()]:
            P = R["full"][pool]
            S, tiers = len(R["pools"][pool]["subjects"]), R["pools"][pool]["tiers"]
            cross = next(t for t in tiers if t in CROSS)
            models = list(P)
            pre = [m for m in models if info[m][1] not in ("pixel", "random")]
            DI = {m: adj(P[m]["tide"][cross]["logreg"], S) for m in models}
            DI1 = {m: adj(P[m]["tide"][cross]["1nn"], S) for m in models}
            SIA = {m: adj(P[m]["sia"]["logreg"], S) for m in models}
            FAR = {m: adj(P[m]["tide"]["same_scan_far"]["logreg"], S) for m in models}
            CT = {m: adj(P[m]["ctrl"][cross], S) for m in models}
            for label, D in [("SIA-mode (50/50 within acquisition)", SIA), ("TIDE same_scan_far (within)", FAR),
                             (f"TIDE DI logreg ({cross})", DI), (f"TIDE DI 1-NN ({cross})", DI1)]:
                A = np.stack([D[m] for m in pre])
                T["disc"].append(dict(cond=cname, pool=pool, S=S, protocol=label,
                                      **pair_stats(A, boot_means(A, B, rng))))
            A = np.stack([DI[m] for m in pre])
            Mb = boot_means(A, B, rng)
            rk = (-Mb).argsort(axis=1).argsort(axis=1) + 1
            for m in models:
                a, d = DI[m], DI[m] - DI["pixel"]
                lo, hi = ci(boot_vec(a, B, rng))
                slo, shi = ci(boot_vec(SIA[m], B, rng))
                dlo, dhi = ci(boot_vec(d, B, rng))
                row = dict(cond=cname, pool=pool, S=S, model=m, family=info[m][0], pretraining=info[m][1],
                           group=PT_GROUP.get(info[m][1], info[m][1]), params_M=params.get(m, np.nan),
                           DI=a.mean(), DI_lo=lo, DI_hi=hi, DI_1nn=DI1[m].mean(),
                           SIA_mode=SIA[m].mean(), SIA_lo=slo, SIA_hi=shi, within_far=FAR[m].mean(),
                           RG_far=FAR[m].mean() - a.mean(), EG=d.mean(), EG_lo=dlo, EG_hi=dhi,
                           EG_significant=bool(dlo > 0), ctrl_adj=CT[m].mean(), sigma=a.mean() - CT[m].mean(),
                           LG=(DI1[m].mean() / a.mean()) if a.mean() > 0.05 else np.nan)
                if m in pre:
                    j = pre.index(m)
                    row.update(rank=int(np.median(rk[:, j])), rank_lo=int(np.percentile(rk[:, j], 2.5)),
                               rank_hi=int(np.percentile(rk[:, j], 97.5)))
                T["ranks"].append(row)
            for factor, keyfn in [("pretraining", lambda m: PT_GROUP[info[m][1]]), ("family", lambda m: info[m][0])]:
                gn = sorted(set(keyfn(m) for m in pre))
                cols = {g: [pre.index(m) for m in pre if keyfn(m) == g] for g in gn}
                Gb = {g: Mb[:, c].mean(axis=1) for g, c in cols.items()}
                Gm = {g: float(A[c].mean(axis=1).mean()) for g, c in cols.items()}
                for g in gn:
                    lo, hi = ci(Gb[g])
                    T["fac"].append(dict(cond=cname, pool=pool, factor=factor, comparison=g, n_models=len(cols[g]),
                                         mean=Gm[g], lo=lo, hi=hi, significant=np.nan))
                for g1, g2 in combinations(gn, 2):
                    lo, hi = ci(Gb[g1] - Gb[g2])
                    T["fac"].append(dict(cond=cname, pool=pool, factor=factor, comparison=f"{g1} minus {g2}",
                                         n_models=np.nan, mean=Gm[g1] - Gm[g2], lo=lo, hi=hi,
                                         significant=bool(lo > 0 or hi < 0)))
            from scipy.stats import spearmanr
            pm = [m for m in pre if np.isfinite(params.get(m, np.nan))]
            for sub_name, fn in [("all pretrained", lambda m: True), ("CNN", lambda m: info[m][0] == "CNN"),
                                 ("Transformer", lambda m: info[m][0] == "Transformer")]:
                sel = [m for m in pm if fn(m)]
                if len(sel) < 4:
                    continue
                x = np.log10([params[m] for m in sel])
                cols = [pre.index(m) for m in sel]
                rho = spearmanr(x, A[cols].mean(axis=1)).correlation
                lo, hi = ci([spearmanr(x, Mb[b, cols]).correlation for b in range(B)])
                T["cap"].append(dict(cond=cname, pool=pool, subset=sub_name, n_models=len(sel),
                                     spearman_logparams_vs_DI=rho, lo=lo, hi=hi))
            r_geo = spearmanr([DI[m].mean() for m in pre], [DI1[m].mean() for m in pre]).correlation
            T["geo"].append(dict(cond=cname, pool=pool, spearman_logreg_vs_1nn=r_geo,
                                 median_LG=float(np.nanmedian([DI1[m].mean() / max(DI[m].mean(), 1e-6) for m in pre]))))
            for m in models:
                for f, v in P[m].get("dup", {}).items():
                    T["dup"].append(dict(cond=cname, pool=pool, model=m, group=PT_GROUP.get(info[m][1], ""),
                                         frac_near_duplicates=f, mean_adj=adj(v, S).mean()))
            if pool == "reliability":
                for m, o in R["posctrl"].items():
                    a = adj(o["tide"][cross]["logreg"], S)
                    d = a - DI[m]
                    lo, hi = ci(boot_vec(d, B, rng))
                    T["pos"].append(dict(cond=cname, model=m, DI_base=DI[m].mean(), DI_LDA=a.mean(), delta=d.mean(),
                                         lo=lo, hi=hi, significant=bool(lo > 0 or hi < 0),
                                         SIA_LDA=adj(o["sia"]["logreg"], S).mean()))
    # preprocessing ladder (reliability pool, subjects common to all conditions)
    conds = [c for c in ["raw", "t88_gfc", "t88_masked"] if c in Rs and "reliability" in Rs[c]["full"]]
    if len(conds) >= 2:
        common = sorted(set.intersection(*[set(Rs[c]["pools"]["reliability"]["subjects"]) for c in conds]))
        models = [m for m in Rs[conds[0]]["full"]["reliability"]
                  if all(m in Rs[c]["full"]["reliability"] for c in conds)]

        def vec(c, m):
            subs = Rs[c]["pools"]["reliability"]["subjects"]
            v = adj(Rs[c]["full"]["reliability"][m]["tide"]["rescan_90d"]["logreg"], len(subs))
            pos = {s: i for i, s in enumerate(subs)}
            return v[[pos[s] for s in common]]
        for m in models:
            vals = {c: vec(c, m) for c in conds}
            row = dict(model=m, group=PT_GROUP.get(info[m][1], ""), n_subjects=len(common))
            for c in conds:
                row[f"DI_{c}"] = vals[c].mean()
            for c1, c2 in list(zip(conds[:-1], conds[1:])) + ([(conds[0], conds[-1])] if len(conds) > 2 else []):
                d = vals[c2] - vals[c1]
                lo, hi = ci(boot_vec(d, B, rng))
                row[f"delta_{c1}_to_{c2}"] = d.mean()
                row[f"delta_{c1}_to_{c2}_lo"] = lo
                row[f"delta_{c1}_to_{c2}_hi"] = hi
            T["ladder"].append(row)
    frames = {k: pd.DataFrame(v) for k, v in T.items()}
    names = {"within": "within_session_saturation.csv", "disc": "discriminability_sia_vs_tide.csv",
             "ranks": "encoder_table.csv", "fac": "factors.csv", "cap": "capacity.csv", "geo": "probe_geometry.csv",
             "dup": "duplicate_injection.csv", "pos": "positive_control.csv", "ladder": "preprocessing_ladder.csv"}
    for k, f in names.items():
        if not frames[k].empty:
            frames[k].to_csv(out / f, index=False)
    return frames


# =============================================================== stage 6: figures + report
def figures(Rs, summ, F, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fd = out / "figures"
    fd.mkdir(exist_ok=True)
    colors = {"supervised IN-1k": "#4C72B0", "supervised IN-21k": "#55A868", "self-supervised": "#C44E52",
              "weakly supervised": "#8172B2", "vision-language": "#CCB974", "random": "#999999", "pixel": "#000000"}
    # (1) tier heatmaps with the SIA-mode column first
    for (cname, pool), d in summ[summ["probe"] == "logreg"].groupby(["cond", "pool"]):
        if "_S" in pool or pool not in Rs[cname]["pools"]:
            continue
        d = d[d["kind"].isin(["tide", "sia"]) & ~d["model"].str.endswith("+LDA")]
        d = d.assign(col=np.where(d["kind"] == "sia", "SIA-mode\n(50/50)", d["tier"].str.replace("_", "\n")))
        tab = d.pivot_table(index="model", columns="col", values="mean_adj")
        order = ["SIA-mode\n(50/50)"] + [t.replace("_", "\n") for t in Rs[cname]["pools"][pool]["tiers"]]
        tab = tab.reindex(columns=[c for c in order if c in tab.columns])
        tab = tab.sort_values(tab.columns[-1], ascending=False)
        fig, ax = plt.subplots(figsize=(1.5 * tab.shape[1] + 3.5, 0.3 * len(tab) + 1.6))
        im = ax.imshow(tab.values, cmap="viridis", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(tab.shape[1]))
        ax.set_xticklabels(tab.columns, fontsize=8)
        ax.set_yticks(range(len(tab)))
        ax.set_yticklabels(tab.index, fontsize=7)
        for r in range(tab.shape[0]):
            for c in range(tab.shape[1]):
                v = tab.values[r, c]
                if np.isfinite(v):
                    ax.text(c, r, f"{v:.2f}", ha="center", va="center", fontsize=6,
                            color="white" if v < 0.6 else "black")
        ax.set_title(f"{cname} / {pool} (S={len(Rs[cname]['pools'][pool]['subjects'])}), chance-adjusted", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.03)
        fig.tight_layout()
        fig.savefig(fd / f"heatmap_{cname}_{pool}.png", dpi=180)
        plt.close(fig)
    # (2) SIA-mode vs TIDE DI forest (main condition)
    E = F["ranks"]
    for (cname, pool), d in E.groupby(["cond", "pool"]):
        d = d.sort_values("DI")
        y = np.arange(len(d))
        fig, axs = plt.subplots(1, 2, figsize=(10, 0.28 * len(d) + 1.5), sharey=True)
        for ax, (col, lo, hi, title) in zip(axs, [("SIA_mode", "SIA_lo", "SIA_hi", "SIA-mode (within acquisition)"),
                                                  ("DI", "DI_lo", "DI_hi", "TIDE durable identifiability (cross-session)")]):
            c = [colors.get(g, "#333333") for g in d["group"]]
            ax.errorbar(d[col], y, xerr=[d[col] - d[lo], d[hi] - d[col]], fmt="none", ecolor="#bbbbbb", lw=1)
            ax.scatter(d[col], y, c=c, s=18, zorder=3)
            ax.set_xlim(-0.05, 1.05)
            ax.set_title(title, fontsize=9)
            ax.axvline(0, color="k", lw=0.5)
        axs[0].set_yticks(y)
        axs[0].set_yticklabels(d["model"], fontsize=7)
        handles = [plt.Line2D([], [], marker="o", ls="", color=v, label=k) for k, v in colors.items()]
        axs[1].legend(handles=handles, fontsize=6, loc="lower right")
        fig.suptitle(f"{cname} / {pool}: same encoders, two protocols", fontsize=10)
        fig.tight_layout()
        fig.savefig(fd / f"sia_vs_tide_{cname}_{pool}.png", dpi=180)
        plt.close(fig)
        # (3) probe geometry
        fig, ax = plt.subplots(figsize=(4.6, 4.4))
        ax.scatter(d["DI"], d["DI_1nn"], c=[colors.get(g, "#333") for g in d["group"]], s=20)
        ax.plot([0, 1], [0, 1], "k--", lw=0.6)
        ax.set_xlabel("DI, linear probe")
        ax.set_ylabel("DI, cosine 1-NN")
        ax.set_title(f"{cname}/{pool}: detection vs geometry", fontsize=9)
        fig.tight_layout()
        fig.savefig(fd / f"probe_geometry_{cname}_{pool}.png", dpi=180)
        plt.close(fig)
        # (4) capacity
        dd = d[np.isfinite(d["params_M"])]
        if len(dd):
            fig, ax = plt.subplots(figsize=(5.2, 4.2))
            for fam, mk in zip(["CNN", "Transformer", "Hybrid", "MLP/MetaFormer"], ["o", "s", "^", "D"]):
                q = dd[dd["family"] == fam]
                ax.scatter(q["params_M"], q["DI"], marker=mk, label=fam, s=24)
            ax.set_xscale("log")
            ax.set_xlabel("Parameters (M, log)")
            ax.set_ylabel("DI (chance-adjusted)")
            ax.legend(fontsize=7)
            ax.set_title(f"{cname}/{pool}: capacity vs durable identity", fontsize=9)
            fig.tight_layout()
            fig.savefig(fd / f"capacity_{cname}_{pool}.png", dpi=180)
            plt.close(fig)
    # (5) duplicate injection
    D = F["dup"]
    for (cname, pool), d in D.groupby(["cond", "pool"]):
        fig, ax = plt.subplots(figsize=(5, 4))
        for m, q in d.groupby("model"):
            col = "red" if m == "pixel" else ("#999999" if q["group"].iloc[0] == "random" else "#4C72B0")
            ax.plot(q["frac_near_duplicates"], q["mean_adj"], color=col, lw=1.6 if m == "pixel" else 0.6,
                    alpha=1 if m == "pixel" else 0.5)
        ax.set_xlabel("Fraction of cross-session eval slices replaced by same-acquisition neighbours")
        ax.set_ylabel("Identifiability (chance-adjusted)")
        ax.set_title(f"{cname}/{pool}: near-duplicate contamination (red = pixel)", fontsize=9)
        fig.tight_layout()
        fig.savefig(fd / f"duplicate_injection_{cname}_{pool}.png", dpi=180)
        plt.close(fig)
    # (6) preprocessing ladder
    L = F["ladder"]
    if not L.empty:
        cols = [c for c in L.columns if c.startswith("DI_")]
        xs = np.arange(len(cols))
        fig, ax = plt.subplots(figsize=(5.4, 4.2))
        for _, r in L.iterrows():
            if r["model"] == "pixel":
                ax.plot(xs, r[cols].values.astype(float), color="red", lw=2, label="pixel", zorder=4)
            elif r["group"] == "random":
                ax.plot(xs, r[cols].values.astype(float), color="#999999", lw=1, ls="--")
            else:
                ax.plot(xs, r[cols].values.astype(float), color="#4C72B0", lw=0.6, alpha=0.4)
        pre = L[~L["group"].isin(["random", "pixel"])]
        ax.plot(xs, pre[cols].median().values, color="k", lw=2.4, label="median pretrained", zorder=5)
        ax.set_xticks(xs)
        ax.set_xticklabels([c.replace("DI_", "") for c in cols])
        ax.set_ylabel("DI (rescan, chance-adjusted)")
        ax.set_title("Preprocessing ladder: raw -> registered -> skull-stripped", fontsize=9)
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(fd / "preprocessing_ladder.png", dpi=180)
        plt.close(fig)
    # (7) QC slices
    try:
        conds = [c for c in Rs if "reliability" in Rs[c]["pools"]]
        fig, axs = plt.subplots(len(conds), 2, figsize=(5, 2.5 * len(conds)), squeeze=False)
        for i, c in enumerate(conds):
            cdir = Path(Rs[c]["cache_dir"])
            sc = pd.read_csv(cdir / "scans.csv")
            sl = np.load(cdir / "slices_uint8.npy", mmap_mode="r")
            subj = Rs[c]["pools"]["reliability"]["subjects"][0]
            g = sc[(sc["subject"] == subj) & sc["ok"].astype(bool)].sort_values(["visit", "scan"])
            for j, v in enumerate(sorted(g["visit"].unique())[:2]):
                row = g[g["visit"] == v].index[0]
                axs[i, j].imshow(sl[row, sl.shape[1] // 2, 0], cmap="gray")
                axs[i, j].set_title(f"{c} {subj} MR{v}", fontsize=7)
                axs[i, j].axis("off")
        fig.tight_layout()
        fig.savefig(fd / "qc_slices.png", dpi=150)
        plt.close(fig)
    except Exception as e:  # noqa: BLE001
        log(f"[fig] QC figure skipped ({e})")


def report(Rs, F, out, elapsed):
    try:
        import tabulate  # noqa: F401  (needed by DataFrame.to_markdown)
    except ImportError:
        pd.DataFrame.to_markdown = lambda self, index=False, **kw: "```\n" + self.to_string(index=index) + "\n```"
    L = ["# TIDE run report (OASIS-1)", "", f"Total time: {elapsed / 3600:.2f} h", ""]
    E = F["ranks"]
    for (cname, pool), d in E.groupby(["cond", "pool"]):
        pre = d[~d["group"].isin(["random", "pixel"])]
        px = d[d["model"] == "pixel"].iloc[0]
        L += [f"## {cname} / {pool} (S={int(d['S'].iloc[0])})", ""]
        L.append(f"- Pretrained encoders: {len(pre)}. DI range {pre['DI'].min():.3f}-{pre['DI'].max():.3f}; "
                 f"pixel floor {px['DI']:.3f} [{px['DI_lo']:.3f}, {px['DI_hi']:.3f}]; "
                 f"random encoders {', '.join(f'{v:.3f}' for v in d[d['group'] == 'random']['DI'])}.")
        L.append(f"- SIA-mode on the same subjects: range {pre['SIA_mode'].min():.3f}-{pre['SIA_mode'].max():.3f} "
                 f"({int((pre['SIA_mode'] >= 0.95).sum())}/{len(pre)} encoders >= 0.95).")
        L.append(f"- Encoder gain over pixel significant (paired CI > 0): {int(pre['EG_significant'].sum())}/{len(pre)}.")
        L.append(f"- Max permuted-label control (chance-adjusted): {d['ctrl_adj'].max():.3f}.")
        top = pre.sort_values("DI", ascending=False)
        L.append("- Top 5 DI: " + "; ".join(f"{r.model} {r.DI:.3f} [{r.DI_lo:.3f},{r.DI_hi:.3f}]"
                                            for r in top.head(5).itertuples()))
        L.append("- Bottom 5 DI: " + "; ".join(f"{r.model} {r.DI:.3f} [{r.DI_lo:.3f},{r.DI_hi:.3f}]"
                                               for r in top.tail(5).itertuples()))
        L.append("")
    if not F["disc"].empty:
        L += ["## Discriminability: SIA-mode vs TIDE (pretrained encoders)", "",
              F["disc"][["cond", "pool", "S", "protocol", "mean", "sd", "range", "n_ge_0p95",
                         "frac_pairs_significant"]].round(3).to_markdown(index=False), ""]
    if not F["within"].empty:
        L += ["## Within-session saturation ('all' pool)", "",
              F["within"][["cond", "S", "protocol", "min", "max", "n_ge_0p95",
                           "frac_pairs_significant"]].round(3).to_markdown(index=False), ""]
    if not F["fac"].empty:
        sig = F["fac"][F["fac"]["significant"] == True]  # noqa: E712
        L += ["## Factor groups (DI)", "",
              F["fac"][F["fac"]["significant"].isna()][["cond", "pool", "factor", "comparison", "n_models", "mean",
                                                       "lo", "hi"]].round(3).to_markdown(index=False), "",
              "Significant group differences:", ""]
        L += [f"- {r.cond}/{r.pool} {r.factor}: {r.comparison} = {r.mean:+.3f} [{r.lo:+.3f}, {r.hi:+.3f}]"
              for r in sig.itertuples()] or ["- none"]
        L.append("")
    if not F["cap"].empty:
        L += ["## Capacity (Spearman log-params vs DI)", "", F["cap"].round(3).to_markdown(index=False), ""]
    if not F["geo"].empty:
        L += ["## Probe geometry", "", F["geo"].round(3).to_markdown(index=False), ""]
    if not F["ladder"].empty:
        cols = [c for c in F["ladder"].columns if c.startswith("DI_")]
        lad = F["ladder"]
        pre = lad[~lad["group"].isin(["random", "pixel"])]
        L += ["## Preprocessing ladder (rescan DI)", "",
              "- pixel: " + ", ".join(f"{c[3:]} {lad[lad['model'] == 'pixel'][c].iloc[0]:.3f}" for c in cols),
              "- median pretrained: " + ", ".join(f"{c[3:]} {pre[c].median():.3f}" for c in cols)]
        dcols = [c for c in lad.columns if c.startswith("delta_") and not c.endswith(("_lo", "_hi"))]
        for c in dcols:
            n_down = int((pre[c + "_hi"] < 0).sum())
            n_up = int((pre[c + "_lo"] > 0).sum())
            L.append(f"- {c}: significant drop {n_down}/{len(pre)}, significant rise {n_up}/{len(pre)}")
        L.append("")
    if not F["dup"].empty:
        d = F["dup"]
        L += ["## Near-duplicate injection (cross-session eval contaminated)", ""]
        for (c, p), q in d.groupby(["cond", "pool"]):
            pre = q[~q["group"].isin(["random", "pixel"])]
            f0 = pre[pre["frac_near_duplicates"] == 0.0]["mean_adj"].median()
            f1 = pre[pre["frac_near_duplicates"] == 1.0]["mean_adj"].median()
            p0 = q[(q["model"] == "pixel") & (q["frac_near_duplicates"] == 0.0)]["mean_adj"].iloc[0]
            p1 = q[(q["model"] == "pixel") & (q["frac_near_duplicates"] == 1.0)]["mean_adj"].iloc[0]
            L.append(f"- {c}/{p}: median pretrained {f0:.3f} -> {f1:.3f}; pixel {p0:.3f} -> {p1:.3f}")
        L.append("")
    if not F["pos"].empty:
        L += ["## Positive control (identity-supervised PCA+LDA head, disjoint training subjects)", "",
              F["pos"].round(3).to_markdown(index=False), ""]
    (out / "REPORT.md").write_text("\n".join(L), encoding="utf-8")


# =============================================================== main
def main():
    global LOGFILE
    from encode_slices import REGISTRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-cache", default="feats_oasis1_v2")
    ap.add_argument("--oasis1-dir", default="Datasets")
    ap.add_argument("--out", default="tide_oasis1")
    ap.add_argument("--skip-t88", action="store_true")
    ap.add_argument("--t88-axis", type=int, default=-1, help="-1 = shortest axis (sagittal for T88_111)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--pool-sizes", type=int, nargs="+", default=[20, 50])
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--input-size", type=int, default=224)
    ap.add_argument("--pixel-size", type=int, default=64)
    ap.add_argument("--scans-per-batch", type=int, default=4)
    ap.add_argument("--posctrl-models", nargs="+",
                    default=["pixel", "resnet18_in1k", "resnet50_in1k", "convnext_tiny_in1k", "vit_base_in21k",
                             "dino_vits16", "clip_vitb16_openai", "biomedclip_vitb16"])
    ap.add_argument("--redo-probes", action="store_true")
    args = ap.parse_args()

    T0 = time.time()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    LOGFILE = out / "tide_log.txt"
    raw = Path(args.raw_cache)
    meta = json.loads((raw / "meta.json").read_text())
    all_names = ["pixel"] + list(REGISTRY)
    info = {"pixel": ("floor", "pixel"), **{k: (v[4], v[5]) for k, v in REGISTRY.items()}}
    conds = {"raw": raw}
    log(f"TIDE run started | raw cache {raw} | out {out}")

    if not args.skip_t88:
        idx_path = out / "index_t88.csv"
        idx = pd.read_csv(idx_path) if idx_path.exists() else build_t88_index(args.oasis1_dir)
        if idx.empty:
            log("[t88] no PROCESSED T88 volumes found - ladder will be skipped")
        else:
            idx.to_csv(idx_path, index=False)
            for var in ["t88_gfc", "t88_masked"]:
                sub = idx[idx["variant"] == var].reset_index(drop=True)
                log(f"[t88] {var}: {len(sub)} sessions, {sub['subject'].nunique()} subjects")
                if sub.empty:
                    continue
                cdir = raw.parent / f"feats_oasis1_{var}"
                cache_condition(sub, cdir, meta["k"], meta["band"], meta["offsets"], args.t88_axis, args.workers)
                if (cdir / "slices_uint8.npy").exists():
                    encode_condition(cdir, all_names, args.input_size, args.pixel_size, args.scans_per_batch)
                    conds[var] = cdir
    log(f"[stage] data ready ({(time.time() - T0) / 60:.1f} min)")

    params = count_params(out)
    Rs = {}
    for cname, cdir in conds.items():
        models = [m for m in all_names if (cdir / f"feats_{m}.npy").exists()]
        Rs[cname] = probe_condition(cname, cdir, models, args, out)
        Rs[cname]["cache_dir"] = str(cdir)
    log(f"[stage] probes done ({(time.time() - T0) / 60:.1f} min)")

    summ = summarize(Rs, args.boot, args.seed, out)
    F = analyze(Rs, info, params, out, args.boot, args.seed)
    log(f"[stage] statistics done ({(time.time() - T0) / 60:.1f} min)")
    try:
        figures(Rs, summ, F, out)
    except Exception as e:  # noqa: BLE001
        log(f"[fig] figure stage error: {e}")
    try:
        report(Rs, F, out, time.time() - T0)
    except Exception as e:  # noqa: BLE001
        log(f"[report] error: {e}")
    log(f"DONE in {(time.time() - T0) / 3600:.2f} h -> {out}")


if __name__ == "__main__":
    main()
