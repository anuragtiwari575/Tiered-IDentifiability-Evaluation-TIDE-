#!/usr/bin/env python3
"""
tide_full_oasis2.py - unattended, resumable full TIDE run on OASIS-2 (+ registration check on OASIS-1).

Stages (each is isolated: a failure is logged and the remaining stages still run; re-running the
same command resumes - finished caches, registrations, features and probe results are reused):

  1  index      all raw scans in --datasets (OASIS-1 + OASIS-2)
  2  raw        OASIS-2 raw cache (first two acquisitions of every session) + all 33 feature sets
  3  clinical   OASIS-2 clinical sheet (oasis_longitudinal*.csv/.xlsx) if present -> MR delay, group, CDR
  4  register   identity-agnostic affine registration of every OASIS-2 session (and the 20 OASIS-1
                reliability subjects, for validation) to a template built from OASIS-1 T88 volumes:
                  reg      = registered (skull present)
                  regmask  = registered x template brain mask
  5  encode     33 feature sets for the registered caches
  6  probes     fixed-n_fit probes (dense / sparse fit), every eval slice binned by distance to the nearest
                fit slice, sessions: within, repeat (raw), each later visit
  7  analysis   decay curves, discriminability, GEN (d >= 2 mm) with encoder gain over pixel, factor groups,
                capacity, TIME analysis (identifiability vs years between visits, distance-equivalent of a
                year), clinical-group analysis, registration validation (own registration vs official T88)
  8  figures + REPORT_FULL.md

Needs, in the same folder: tide_run.py, extract_features.py, encode_slices.py, and the previous outputs
tide_oasis1/index_t88.csv (+ params.csv) and the OASIS-1 grid caches (feats_oasis1_t88_*_grid).

Usage:
  python tide_full_oasis2.py
"""
import argparse
import itertools
import json
import os
import pickle
import re
import subprocess
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

import tide_run as T

SESS_RE = re.compile(r"(OAS([12])_(\d{4})_MR(\d+))")
SCAN_RE = re.compile(r"mpr-(\d+)")
GRID_OFFSETS = [0, 1, 2, 3, 4, 6, 8, 10, 15, 20]
RAW_OFFSETS = [0, 1, 2, 4, 6]
CANDS = [(p, f) for p in itertools.permutations(range(3)) for f in itertools.product([False, True], repeat=3)]
STATUS = {}
OUT = Path("tide_full_oasis2")


# =============================================================== infrastructure
def run_stage(name, fn, *a, **kw):
    t0 = time.time()
    T.log(f"===== stage {name} =====")
    try:
        res = fn(*a, **kw)
        STATUS[name] = f"ok ({(time.time() - t0) / 60:.1f} min)"
        return res
    except Exception as e:  # noqa: BLE001
        STATUS[name] = f"FAILED: {e!r}"
        T.log(f"[{name}] FAILED: {e!r}\n{traceback.format_exc()}")
        return None
    finally:
        (OUT / "STATUS.json").write_text(json.dumps(STATUS, indent=2))


def grp(info, m):
    return T.PT_GROUP.get(info[m][1], info[m][1])


# =============================================================== stage 1: index
def stage_index(datasets):
    p = OUT / "index_raw_all.csv"
    if p.exists():
        df = pd.read_csv(p)
    else:
        rows = []
        for hdr in Path(datasets).rglob("*.hdr"):
            if "RAW" not in hdr.parts:
                continue
            m, s = SESS_RE.search(str(hdr)), SCAN_RE.search(hdr.name)
            if not m or not s or not hdr.with_suffix(".img").exists():
                continue
            rows.append(dict(dataset=f"OASIS{m.group(2)}", subject=f"OAS{m.group(2)}_{m.group(3)}",
                             session=m.group(1), visit=int(m.group(4)), scan=int(s.group(1)),
                             path=str(hdr.resolve())))
        df = (pd.DataFrame(rows).drop_duplicates(["session", "scan"])
              .sort_values(["dataset", "subject", "visit", "scan"]).reset_index(drop=True))
        df.to_csv(p, index=False)
    for ds, g in df.groupby("dataset"):
        T.log(f"[index] {ds}: {g.subject.nunique()} subjects, {g.session.nunique()} sessions, {len(g)} scans; "
              f"visits/subject {dict(g.groupby('subject').visit.nunique().value_counts().sort_index())}")
    return df


# =============================================================== stage 2: raw OASIS-2
def stage_raw(idx, args, names):
    o2 = idx[idx["dataset"] == "OASIS2"].sort_values(["session", "scan"]).groupby("session").head(2)
    o2 = o2.sort_values(["subject", "visit", "scan"]).reset_index(drop=True)
    if o2.empty:
        raise RuntimeError("no OASIS-2 raw scans found")
    cdir = Path(args.cache_root) / "feats_oasis2_raw"
    T.cache_condition(o2, cdir, 10, (0.25, 0.75), RAW_OFFSETS, -1, args.workers)
    T.encode_condition(cdir, names, 224, 64, 2)
    return cdir


# =============================================================== stage 3: clinical sheet
def stage_clinical(dirs):
    files = []
    for d in dirs:
        for pat in ("*longitudinal*.csv", "*longitudinal*.xlsx", "*Longitudinal*.csv", "*Longitudinal*.xlsx"):
            files += list(Path(d).rglob(pat))
    for f in dict.fromkeys(files):
        try:
            df = pd.read_csv(f) if f.suffix.lower() == ".csv" else pd.read_excel(f)
        except Exception as e:  # noqa: BLE001
            T.log(f"[clinical] cannot read {f}: {e}")
            continue
        cols = {c.lower().strip(): c for c in df.columns}
        if "mri id" not in cols or "mr delay" not in cols:
            continue
        out = pd.DataFrame(dict(session=df[cols["mri id"]].astype(str).str.strip(),
                                delay_days=pd.to_numeric(df[cols["mr delay"]], errors="coerce")))
        for k in ("group", "cdr", "mmse", "age"):
            if k in cols:
                out[k] = df[cols[k]].values
        out.to_csv(OUT / "clinical_used.csv", index=False)
        T.log(f"[clinical] using {f} ({len(out)} sessions; groups {out.get('group', pd.Series()).value_counts().to_dict()})")
        return out
    T.log("[clinical] no oasis_longitudinal sheet found - time axis uses visit index, no group analysis")
    return None


# =============================================================== stage 4: registration
def ensure_sitk():
    try:
        import SimpleITK  # noqa: F401
    except ImportError:
        T.log("[register] installing SimpleITK ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "SimpleITK"])


def load_vol(path):
    import nibabel as nib
    img = nib.load(path)
    return np.squeeze(img.get_fdata(dtype=np.float32)), [float(x) for x in img.header.get_zooms()[:3]]


def pnorm(a):
    fg = a[a > 0]
    ref = fg if fg.size > 1000 else a.ravel()
    lo, hi = np.percentile(ref, [1, 99])
    return np.clip((a - lo) / (hi - lo + 1e-6), 0, 1).astype(np.float32)


def orient(arr, zooms, cand):
    perm, flips = cand
    a = np.transpose(arr, perm)
    z = [zooms[p] for p in perm]
    for ax, f in enumerate(flips):
        if f:
            a = np.flip(a, axis=ax)
    return np.ascontiguousarray(a), z


def to_sitk(arr, spacing):
    import SimpleITK as sitk
    im = sitk.GetImageFromArray(np.ascontiguousarray(np.transpose(arr, (2, 1, 0)).astype(np.float32)))
    im.SetSpacing(tuple(float(s) for s in spacing))
    return im


def from_sitk(im):
    import SimpleITK as sitk
    return np.transpose(sitk.GetArrayFromImage(im), (2, 1, 0))


def ncc(a, b):
    a = a.ravel() - a.mean()
    b = b.ravel() - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-8))


def slice_positions(n, k, band, max_off):
    lo, hi = int(round(band[0] * n)), int(round(band[1] * n)) - max_off - 1
    return np.linspace(lo, hi, k).round().astype(int)


def build_template(idx_t88, n):
    p = OUT / "template.npz"
    if p.exists():
        return p
    g = idx_t88[(idx_t88["variant"] == "t88_gfc") & (idx_t88["visit"] == 1)].head(n)
    gm = idx_t88[(idx_t88["variant"] == "t88_masked") & (idx_t88["visit"] == 1)].head(n)
    acc = macc = None
    for path in g["path"]:
        v = pnorm(load_vol(path)[0])
        acc = v if acc is None else acc + v
    for path in gm["path"]:
        v = (load_vol(path)[0] > 0).astype(np.float32)
        macc = v if macc is None else macc + v
    np.savez_compressed(p, tmpl=(acc / len(g)).astype(np.float32), mask=(macc / len(gm)) > 0.5)
    T.log(f"[register] template from {len(g)} OASIS-1 T88 volumes, shape {acc.shape}")
    return p


def calibrate_orientation(idx, idx_t88, n_subj=4):
    p = OUT / "orientation.json"
    if p.exists():
        d = json.loads(p.read_text())
        return (tuple(d["perm"]), tuple(d["flips"]))
    import SimpleITK as sitk
    t88 = idx_t88[(idx_t88["variant"] == "t88_gfc") & (idx_t88["visit"] == 1)]
    raw1 = idx[(idx["dataset"] == "OASIS1") & (idx["visit"] == 1)].sort_values(["subject", "scan"])
    raw1 = raw1.groupby("session").head(1)
    subs = [s for s in t88["subject"] if s in set(raw1["subject"])][:n_subj]
    scores = np.full((len(subs), len(CANDS)), -1.0)
    for i, s in enumerate(subs):
        fx = sitk.Shrink(to_sitk(pnorm(load_vol(t88[t88["subject"] == s]["path"].iloc[0])[0]), [1, 1, 1]), [4, 4, 4])
        fxa = from_sitk(fx)
        arr, z = load_vol(raw1[raw1["subject"] == s]["path"].iloc[0])
        arr = pnorm(arr)
        for c, cand in enumerate(CANDS):
            a, zz = orient(arr, z, cand)
            mv = to_sitk(a, zz)
            try:
                tx = sitk.CenteredTransformInitializer(fx, mv, sitk.Euler3DTransform(),
                                                       sitk.CenteredTransformInitializerFilter.MOMENTS)
                scores[i, c] = ncc(from_sitk(sitk.Resample(mv, fx, tx, sitk.sitkLinear, 0.0, sitk.sitkFloat32)), fxa)
            except Exception:  # noqa: BLE001
                pass
    mean = scores.mean(axis=0)
    order = np.argsort(-mean)
    best = CANDS[int(order[0])]
    T.log("[register] orientation candidates (mean NCC over %d subjects): " % len(subs)
          + "; ".join(f"{CANDS[i]} {mean[i]:.3f}" for i in order[:4]))
    p.write_text(json.dumps(dict(perm=list(best[0]), flips=list(best[1]), ncc=float(mean[order[0]]),
                                 runner_up=float(mean[order[1]]), subjects=subs)))
    return best


def _reg_method(shrink, smooth, iters):
    import SimpleITK as sitk
    R = sitk.ImageRegistrationMethod()
    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
    R.SetMetricSamplingStrategy(R.RANDOM)
    R.SetMetricSamplingPercentage(0.05, 1)
    R.SetInterpolator(sitk.sitkLinear)
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=1.0, minStep=1e-4, numberOfIterations=iters,
                                               relaxationFactor=0.5)
    R.SetOptimizerScalesFromPhysicalShift()
    R.SetShrinkFactorsPerLevel(shrink)
    R.SetSmoothingSigmasPerLevel(smooth)
    R.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    return R


_TMPL = {}


def reg_worker(job):
    key, path, cand, tmpl_path, out_npz, k, band, offsets, threads = job
    try:
        if Path(out_npz).exists():
            return key, float(np.load(out_npz)["ncc"]), "cached"
        import SimpleITK as sitk
        sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(threads)
        if "t" not in _TMPL:
            d = np.load(tmpl_path)
            _TMPL["t"], _TMPL["m"] = d["tmpl"], d["mask"]
        tmpl, mask = _TMPL["t"], _TMPL["m"]
        fixed = to_sitk(tmpl, [1, 1, 1])
        arr, z = load_vol(path)
        a, zz = orient(pnorm(arr), z, cand)
        moving = to_sitk(a, zz)
        rigid = sitk.Euler3DTransform(sitk.CenteredTransformInitializer(
            fixed, moving, sitk.Euler3DTransform(), sitk.CenteredTransformInitializerFilter.MOMENTS))
        R = _reg_method([4, 2], [2, 1], 150)
        R.SetInitialTransform(rigid, inPlace=True)
        R.Execute(fixed, moving)
        aff = sitk.AffineTransform(3)
        aff.SetCenter(rigid.GetCenter())
        aff.SetMatrix(rigid.GetMatrix())
        aff.SetTranslation(rigid.GetTranslation())
        R2 = _reg_method([4, 2, 1], [2, 1, 0], 100)
        R2.SetInitialTransform(aff, inPlace=True)
        R2.Execute(fixed, moving)
        res = from_sitk(sitk.Resample(moving, fixed, aff, sitk.sitkLinear, 0.0, sitk.sitkFloat32))
        head = tmpl > 0.1
        q = ncc(res[head], tmpl[head])
        out = {}
        pos = None
        for name, vol in (("reg", res), ("regmask", res * mask)):
            v = pnorm(vol)
            pos = slice_positions(v.shape[0], k, band, max(offsets))
            sl = np.stack([np.stack([v[p_ + o] for o in offsets]) for p_ in pos])
            out[name] = (sl * 255.0).round().astype(np.uint8)
        np.savez_compressed(out_npz, reg=out["reg"], regmask=out["regmask"], ncc=q, pos=pos,
                            mid=(res[res.shape[0] // 2] * 255).astype(np.uint8))
        return key, q, "ok"
    except Exception as e:  # noqa: BLE001
        return key, np.nan, f"error: {e!r}"


def stage_register(idx, args):
    ensure_sitk()
    idx_t88 = pd.read_csv(Path(args.tide_out) / "index_t88.csv")
    tmpl_path = build_template(idx_t88, args.template_n)
    cand = calibrate_orientation(idx, idx_t88)
    rel = sorted(set(idx_t88[idx_t88["visit"] >= 2]["subject"]))
    first = idx.sort_values(["session", "scan"]).groupby("session").head(1)
    jobs_df = pd.concat([first[(first["dataset"] == "OASIS1") & first["subject"].isin(rel)].assign(group="oasis1val"),
                         first[first["dataset"] == "OASIS2"].assign(group="oasis2")], ignore_index=True)
    vdir = Path(args.cache_root) / "reg_oasis_volumes"
    vdir.mkdir(parents=True, exist_ok=True)
    jobs_df["npz"] = [str(vdir / f"{s}.npz") for s in jobs_df["session"]]
    jobs = [(r.session, r.path, cand, str(tmpl_path), r.npz, 10, (0.25, 0.75), GRID_OFFSETS, args.reg_threads)
            for r in jobs_df.itertuples()]
    T.log(f"[register] {len(jobs)} volumes ({(jobs_df['group'] == 'oasis1val').sum()} OASIS-1 validation, "
          f"{(jobs_df['group'] == 'oasis2').sum()} OASIS-2), {args.reg_procs} processes x {args.reg_threads} threads")
    qc, t0, done = {}, time.time(), 0
    with ProcessPoolExecutor(max_workers=args.reg_procs) as ex:
        futs = [ex.submit(reg_worker, j) for j in jobs]
        for f in as_completed(futs):
            key, q, st = f.result()
            qc[key] = (q, st)
            done += 1
            if done % 25 == 0 or done == len(jobs):
                T.log(f"  [register] {done}/{len(jobs)} ({(time.time() - t0) / 60:.1f} min)")
    jobs_df["ncc"] = [qc[s][0] for s in jobs_df["session"]]
    jobs_df["status"] = [qc[s][1] for s in jobs_df["session"]]
    jobs_df["ok"] = jobs_df["ncc"] >= args.ncc_min
    jobs_df.to_csv(OUT / "registration_qc.csv", index=False)
    T.log(f"[register] NCC median {jobs_df['ncc'].median():.3f}; passed {int(jobs_df['ok'].sum())}/{len(jobs_df)} "
          f"(threshold {args.ncc_min}); errors {int(jobs_df['status'].str.startswith('error').sum())}")
    return jobs_df


def assemble_cache(rows, var, cdir):
    if (cdir / "slices_uint8.npy").exists() and (cdir / "scans.csv").exists():
        return
    cdir.mkdir(parents=True, exist_ok=True)
    rows = rows.reset_index(drop=True)
    first_ok = rows[rows["ok"]].iloc[0]
    shape = np.load(first_ok["npz"])[var].shape
    tmp = cdir / "slices_uint8.npy.part"
    arr = np.lib.format.open_memmap(tmp, mode="w+", dtype=np.uint8, shape=(len(rows), *shape))
    poss = []
    for i, r in rows.iterrows():
        if r["ok"]:
            d = np.load(r["npz"])
            arr[i] = d[var]
            poss.append(" ".join(map(str, d["pos"])))
        else:
            poss.append("")
    arr.flush()
    del arr
    os.replace(tmp, cdir / "slices_uint8.npy")
    rows[["dataset", "subject", "session", "visit", "scan"]].assign(
        path=rows["npz"], ok=rows["ok"], positions=poss).to_csv(cdir / "scans.csv", index=False)
    (cdir / "meta.json").write_text(json.dumps(dict(k=10, band=[0.25, 0.75], offsets=GRID_OFFSETS, axis=0,
                                                    source="tide_full_oasis2 registration")))


def stage_reg_encode(jobs_df, args, names):
    made = {}
    for group in ("oasis1val", "oasis2"):
        rows = jobs_df[jobs_df["group"] == group]
        if rows["ok"].sum() < 10:
            T.log(f"[reg-encode] {group}: too few registered volumes, skipped")
            continue
        for var in ("reg", "regmask"):
            cdir = Path(args.cache_root) / f"feats_{group}_{var}"
            assemble_cache(rows, var, cdir)
            T.encode_condition(cdir, names, 224, 64, 1)
            made[f"{group}_{var}"] = cdir
    return made


# =============================================================== stage 6: probes
def mv_records(scans, use_b, keep=None):
    ok = scans[scans["ok"].astype(bool)]
    recs = []
    for subj, g in ok.groupby("subject"):
        if keep is not None and subj not in keep:
            continue
        sess = sorted(g["session"].unique(), key=lambda s: int(s.split("_MR")[-1]))
        if len(sess) < 2:
            continue
        v1 = g[g["session"] == sess[0]].sort_values("scan")
        r = dict(subject=subj, a=int(v1.index[0]), b=int(v1.index[1]) if use_b and len(v1) >= 2 else None,
                 visits={}, sessions={})
        for s in sess[1:]:
            v = int(s.split("_MR")[-1])
            r["visits"][v] = int(g[g["session"] == s].sort_values("scan").index[0])
            r["sessions"][v] = s
        rows = [r["a"]] + ([r["b"]] if r["b"] is not None else []) + list(r["visits"].values())
        r["pos"] = {row: np.array([int(x) for x in str(scans.at[row, "positions"]).split()]) for row in rows}
        recs.append(r)
    return recs


def mv_job(feat_path, recs, fit_idx, offsets, seed, is_pix, chunk=40):
    feat = np.load(feat_path, mmap_mode="r")
    S, K = len(recs), feat.shape[1]
    o0 = offsets.index(0)
    Xf = np.concatenate([np.asarray(feat[r["a"], fit_idx, o0, :], dtype=np.float32) for r in recs])
    yf = np.repeat(np.arange(S), len(fit_idx))
    tf = T._fit_tf(Xf, is_pix, seed)
    Zf = tf(Xf)
    clf = T._lr().fit(Zf, yf)
    Zfn = T._l2(Zf)
    units = []
    for j, r in enumerate(recs):
        units.append(("within", j, r["a"]))
        if r.get("b") is not None:
            units.append(("repeat", j, r["b"]))
        for v, row in sorted(r["visits"].items()):
            units.append((f"visit{v}", j, row))
    acc = {}
    for u0 in range(0, len(units), chunk):
        X, meta = [], []
        for sess, j, row in units[u0:u0 + chunk]:
            r = recs[j]
            fpos, epos = r["pos"][r["a"]][fit_idx], r["pos"][row]
            x = np.asarray(feat[row], dtype=np.float32)
            for i in range(K):
                for oi, o in enumerate(offsets):
                    d = int(np.min(np.abs(fpos - (epos[i] + o))))
                    if sess == "within" and d == 0:
                        continue
                    X.append(x[i, oi])
                    meta.append((sess, j, d))
        if not X:
            continue
        Z = tf(np.stack(X))
        plr = clf.predict(Z)
        pnn = yf[np.argmax(T._l2(Z) @ Zfn.T, axis=1)]
        for (sess, j, d), a, b in zip(meta, plr, pnn):
            t = acc.setdefault((sess, d, j), [0, 0, 0])
            t[0] += 1
            t[1] += int(a == j)
            t[2] += int(b == j)
    out = {}
    for (sess, d, j), (n, cl, cn) in acc.items():
        o = out.setdefault((sess, d), {"j": [], "n": [], "lr": [], "nn": []})
        o["j"].append(j)
        o["n"].append(n)
        o["lr"].append(cl / n)
        o["nn"].append(cn / n)
    return {k: {kk: np.asarray(vv) for kk, vv in v.items()} for k, v in out.items()}


def probe_cond(cname, cdir, use_b, keep, names, args):
    from joblib import Parallel, delayed
    pk = OUT / f"probes_{cname}.pkl"
    if pk.exists() and not args.redo_probes:
        with open(pk, "rb") as fh:
            return pickle.load(fh)
    scans = pd.read_csv(cdir / "scans.csv")
    offsets = json.loads((cdir / "meta.json").read_text())["offsets"]
    models = [m for m in names if (cdir / f"feats_{m}.npy").exists()]
    recs = mv_records(scans, use_b, keep)
    if len(recs) < 5:
        raise RuntimeError(f"{cname}: only {len(recs)} subjects with >= 2 sessions")
    K = int(np.load(cdir / f"feats_{models[0]}.npy", mmap_mode="r").shape[1])
    R = {"subjects": [r["subject"] for r in recs], "visits": [r["sessions"] for r in recs], "offsets": offsets,
         "res": {}}
    for dname, fidx in {"dense": np.arange(K), "sparse": np.arange(0, K, 2)}.items():
        t0 = time.time()
        res = Parallel(n_jobs=args.n_jobs)(
            delayed(mv_job)(str(cdir / f"feats_{m}.npy"), recs, fidx, offsets, args.seed, m == "pixel")
            for m in models)
        R["res"][dname] = dict(zip(models, res))
        T.log(f"[probe] {cname}/{dname}: {len(recs)} subjects, n_fit={len(fidx)}, {len(models)} models "
              f"({time.time() - t0:.0f}s)")
    with open(pk, "wb") as fh:
        pickle.dump(R, fh)
    return R


# =============================================================== stage 7: analysis
def cell_table(R, design, model, S):
    res = R["res"][design][model]
    out, cross = {}, {}
    for (sess, d), v in res.items():
        if sess.startswith("visit"):
            for j, n, lr, nn in zip(v["j"], v["n"], v["lr"], v["nn"]):
                t = cross.setdefault((d, int(j)), [0.0, 0.0, 0.0, 0])
                t[0] += lr
                t[1] += nn
                t[2] += n
                t[3] += 1
        else:
            out[(sess, d)] = (v["j"].astype(int), T.adj(v["lr"], S), T.adj(v["nn"], S), float(np.median(v["n"])))
    by_d = {}
    for (d, j), (lr, nn, n, c) in cross.items():
        by_d.setdefault(d, []).append((j, lr / c, nn / c, n / c))
    for d, lst in by_d.items():
        lst.sort()
        out[("cross", d)] = (np.array([x[0] for x in lst]), T.adj(np.array([x[1] for x in lst]), S),
                             T.adj(np.array([x[2] for x in lst]), S), float(np.median([x[3] for x in lst])))
    return out


def unit_table(R, design, model, S, mm):
    U = {}
    for (sess, d), v in R["res"][design][model].items():
        if not sess.startswith("visit"):
            continue
        vv = int(sess[5:])
        for j, lr in zip(v["j"], v["lr"]):
            u = U.setdefault((int(j), vv), {"d0": np.nan, "far": []})
            a = float(T.adj(lr, S))
            if d == 0:
                u["d0"] = a
            elif d * mm >= 2.0:
                u["far"].append(a)
    return U


def slope_boot(units, B, rng):
    """units: list of (subject, x, y). Returns slope, lo, hi, spearman."""
    from scipy.stats import spearmanr
    units = [u for u in units if np.isfinite(u[2]) and np.isfinite(u[1])]
    if len(units) < 10 or len(set(u[1] for u in units)) < 2:
        return np.nan, np.nan, np.nan, np.nan
    subj = np.array([u[0] for u in units])
    x = np.array([u[1] for u in units], dtype=float)
    y = np.array([u[2] for u in units], dtype=float)
    s = np.polyfit(x, y, 1)[0]
    us = np.unique(subj)
    idx_by = {k: np.where(subj == k)[0] for k in us}
    bs = []
    for _ in range(B):
        ii = np.concatenate([idx_by[k] for k in rng.choice(us, len(us), replace=True)])
        if len(set(x[ii])) > 1:
            bs.append(np.polyfit(x[ii], y[ii], 1)[0])
    lo, hi = T.ci(bs) if bs else (np.nan, np.nan)
    return float(s), lo, hi, float(spearmanr(x, y).correlation)


def analyze(Rs, MM, info, params, clin, args):
    from scipy.stats import spearmanr
    rng = np.random.default_rng(args.seed + 21)
    B = args.boot
    Tb = {k: [] for k in ["curves", "disc", "gen", "fac", "cap", "time", "time_bins", "clin", "valid"]}
    gens = {}
    delay = {}
    if clin is not None:
        delay = dict(zip(clin["session"], clin["delay_days"] / 365.25))
        group_of = {}
        if "group" in clin:
            for s, g in zip(clin["session"], clin["group"]):
                group_of[s.rsplit("_MR", 1)[0]] = str(g)
    else:
        group_of = {}
    for cname, R in Rs.items():
        mm, S = MM[cname], len(R["subjects"])
        for design in R["res"]:
            try:
                models = list(R["res"][design])
                pre = [m for m in models if info[m][1] not in ("pixel", "random")]
                CT = {m: cell_table(R, design, m, S) for m in models}
                cells = sorted(set.intersection(*[set(CT[m]) for m in models]))
                cells = [c for c in cells if CT[models[0]][c][3] >= args.min_n]
                for c in cells:
                    for m in models:
                        _j, lr, nn, n = CT[m][c]
                        for probe, a in (("logreg", lr), ("1nn", nn)):
                            lo, hi = T.ci(T.boot_vec(a, B, rng))
                            Tb["curves"].append(dict(cond=cname, design=design, session=c[0], d_mm=c[1] * mm, model=m,
                                                     group=grp(info, m), probe=probe, mean=a.mean(), lo=lo, hi=hi,
                                                     n_subj=len(a), n_per_subj=n))
                    A = np.stack([CT[m][c][1] for m in pre])
                    px = CT["pixel"][c][1]
                    above = below = 0
                    for m in pre:
                        lo, hi = T.ci(T.boot_vec(CT[m][c][1] - px, B, rng))
                        above += lo > 0
                        below += hi < 0
                    Tb["disc"].append(dict(cond=cname, design=design, session=c[0], d_mm=c[1] * mm, n_subj=A.shape[1],
                                           pixel=px.mean(), n_above_pixel=int(above), n_below_pixel=int(below),
                                           **T.pair_stats(A, T.boot_means(A, B, rng))))
                gc = [c for c in cells if c[0] == "cross" and c[1] * mm >= 2.0]
                if gc:
                    common = sorted(set.intersection(*[set(CT[models[0]][c][0].tolist()) for c in gc]))

                    def genvec(m):
                        vals = []
                        for c in gc:
                            j, lr, _, _ = CT[m][c]
                            pos = {int(x): i for i, x in enumerate(j)}
                            vals.append(lr[[pos[s] for s in common]])
                        return np.mean(vals, axis=0)
                    G = {m: genvec(m) for m in models}
                    gens[(cname, design)] = G
                    A = np.stack([G[m] for m in pre])
                    Mb = T.boot_means(A, B, rng)
                    Tb["disc"].append(dict(cond=cname, design=design, session="GEN cross (d>=2mm)", d_mm=np.nan,
                                           n_subj=A.shape[1], pixel=G["pixel"].mean(), **T.pair_stats(A, Mb)))
                    rk = (-Mb).argsort(axis=1).argsort(axis=1) + 1
                    for m in models:
                        lo, hi = T.ci(T.boot_vec(G[m], B, rng))
                        dlo, dhi = T.ci(T.boot_vec(G[m] - G["pixel"], B, rng))
                        row = dict(cond=cname, design=design, model=m, family=info[m][0], group=grp(info, m),
                                   params_M=params.get(m, np.nan), GEN=G[m].mean(), lo=lo, hi=hi,
                                   EG=(G[m] - G["pixel"]).mean(), EG_lo=dlo, EG_hi=dhi, n_subj=len(common))
                        if m in pre:
                            jj = pre.index(m)
                            row.update(rank=int(np.median(rk[:, jj])), rank_lo=int(np.percentile(rk[:, jj], 2.5)),
                                       rank_hi=int(np.percentile(rk[:, jj], 97.5)))
                        Tb["gen"].append(row)
                    for factor, keyfn in [("pretraining", lambda m: T.PT_GROUP[info[m][1]]),
                                          ("family", lambda m: info[m][0])]:
                        gn = sorted(set(keyfn(m) for m in pre))
                        cols = {g: [pre.index(m) for m in pre if keyfn(m) == g] for g in gn}
                        Gb = {g: Mb[:, cc].mean(axis=1) for g, cc in cols.items()}
                        for g in gn:
                            lo, hi = T.ci(Gb[g])
                            Tb["fac"].append(dict(cond=cname, design=design, factor=factor, comparison=g,
                                                  mean=float(A[cols[g]].mean()), lo=lo, hi=hi, significant=np.nan))
                        for i, g1 in enumerate(gn):
                            for g2 in gn[i + 1:]:
                                lo, hi = T.ci(Gb[g1] - Gb[g2])
                                Tb["fac"].append(dict(cond=cname, design=design, factor=factor,
                                                      comparison=f"{g1} minus {g2}",
                                                      mean=float(A[cols[g1]].mean() - A[cols[g2]].mean()),
                                                      lo=lo, hi=hi, significant=bool(lo > 0 or hi < 0)))
                    pm = [m for m in pre if np.isfinite(params.get(m, np.nan))]
                    for sub_name, fn in [("all pretrained", lambda m: True), ("CNN", lambda m: info[m][0] == "CNN"),
                                         ("Transformer", lambda m: info[m][0] == "Transformer")]:
                        sel = [m for m in pm if fn(m)]
                        if len(sel) < 4:
                            continue
                        x = np.log10([params[m] for m in sel])
                        cc = [pre.index(m) for m in sel]
                        lo, hi = T.ci([spearmanr(x, Mb[b, cc]).correlation for b in range(B)])
                        Tb["cap"].append(dict(cond=cname, design=design, subset=sub_name, n_models=len(sel),
                                              spearman=spearmanr(x, A[cc].mean(axis=1)).correlation, lo=lo, hi=hi))
                # ---------- time analysis (OASIS-2 conditions) ----------
                if cname.startswith("o2"):
                    U = {m: unit_table(R, design, m, S, mm) for m in models}
                    keys = sorted(set.intersection(*[set(U[m]) for m in models]))

                    def yrs(j, v):
                        sess = R["visits"][j].get(v)
                        if sess in delay and np.isfinite(delay[sess]):
                            return float(delay[sess])
                        return np.nan if delay else float(v - 1)
                    xs = {k: yrs(*k) for k in keys}
                    pseudo = {}
                    for metric in ("d0", "far"):
                        for k in keys:
                            vals = []
                            for m in pre:
                                u = U[m][k]
                                vals.append(u["d0"] if metric == "d0" else (np.mean(u["far"]) if u["far"] else np.nan))
                            pseudo[(metric, k)] = np.nanmean(vals) if np.isfinite(vals).any() else np.nan
                    xd = {}
                    cross_d = sorted({c[1] for c in cells if c[0] == "cross"})
                    for metric in ("d0", "far"):
                        for m in models + ["pretrained_mean"]:
                            units = []
                            for k in keys:
                                if m == "pretrained_mean":
                                    y = pseudo[(metric, k)]
                                else:
                                    u = U[m][k]
                                    y = u["d0"] if metric == "d0" else (np.mean(u["far"]) if u["far"] else np.nan)
                                units.append((k[0], xs[k], y))
                            s, lo, hi, rho = slope_boot(units, args.boot_time, rng)
                            dist_slope = np.nan
                            if m != "pretrained_mean" and metric == "d0" and len(cross_d) >= 2:
                                d2 = min(cross_d[1:], key=lambda d: abs(d * mm - 2.0))
                                a0 = CT[m][("cross", cross_d[0])][1].mean() if ("cross", cross_d[0]) in CT[m] else np.nan
                                a2 = CT[m][("cross", d2)][1].mean() if ("cross", d2) in CT[m] else np.nan
                                dist_slope = (a2 - a0) / (d2 * mm - cross_d[0] * mm)
                            xd[(metric, m)] = s
                            Tb["time"].append(dict(cond=cname, design=design, metric=metric, model=m,
                                                   group="pretrained mean" if m == "pretrained_mean" else grp(info, m),
                                                   n_units=len([u for u in units if np.isfinite(u[2]) and np.isfinite(u[1])]),
                                                   slope_per_year=s, lo=lo, hi=hi, spearman=rho,
                                                   dist_slope_per_mm=dist_slope,
                                                   mm_equivalent_of_one_year=(s / dist_slope) if (
                                                       np.isfinite(dist_slope) and dist_slope < 0) else np.nan,
                                                   time_axis="MR delay (years)" if delay else "visit index"))
                            edges = [0, 1.5, 2.5, 3.5, 99] if delay else [0.5, 1.5, 2.5, 3.5, 99]
                            arr = np.array([(x, y) for _s, x, y in units if np.isfinite(x) and np.isfinite(y)])
                            if len(arr):
                                for lo_e, hi_e in zip(edges[:-1], edges[1:]):
                                    sel = arr[(arr[:, 0] >= lo_e) & (arr[:, 0] < hi_e)]
                                    if len(sel):
                                        Tb["time_bins"].append(dict(cond=cname, design=design, metric=metric, model=m,
                                                                    group="pretrained mean" if m == "pretrained_mean"
                                                                    else grp(info, m),
                                                                    bin=f"{lo_e}-{hi_e}", x_mid=float(sel[:, 0].mean()),
                                                                    mean=float(sel[:, 1].mean()), n=len(sel)))
                    # clinical groups: last visit per subject
                    if group_of:
                        last = {}
                        for (j, v) in keys:
                            if j not in last or v > last[j]:
                                last[j] = v
                        for metric in ("d0", "far"):
                            for m in ("pixel", "pretrained_mean"):
                                per = {}
                                for j, v in last.items():
                                    g = group_of.get(R["subjects"][j], "unknown")
                                    if m == "pretrained_mean":
                                        y = pseudo[(metric, (j, v))]
                                    else:
                                        u = U[m][(j, v)]
                                        y = u["d0"] if metric == "d0" else (np.mean(u["far"]) if u["far"] else np.nan)
                                    if np.isfinite(y):
                                        per.setdefault(g, []).append((y, xs[(j, v)]))
                                for g, lst in per.items():
                                    y = np.array([a for a, _ in lst])
                                    lo, hi = T.ci(T.boot_vec(y, B, rng))
                                    Tb["clin"].append(dict(cond=cname, design=design, metric=metric, model=m, group=g,
                                                           n=len(y), mean=y.mean(), lo=lo, hi=hi,
                                                           mean_years_to_last_visit=float(np.nanmean([b for _, b in lst]))))
            except Exception as e:  # noqa: BLE001
                T.log(f"[analysis] {cname}/{design} failed: {e!r}\n{traceback.format_exc()}")
    # ---------- registration validation ----------
    for mine, off in (("o1val_reg", "o1off_gfc"), ("o1val_regmask", "o1off_masked")):
        for design in ("dense", "sparse"):
            if (mine, design) in gens and (off, design) in gens:
                ga, gb = gens[(mine, design)], gens[(off, design)]
                ms = [m for m in ga if m in gb]
                va = np.array([ga[m].mean() for m in ms])
                vb = np.array([gb[m].mean() for m in ms])
                Tb["valid"].append(dict(own=mine, official=off, design=design, n_models=len(ms),
                                        spearman=spearmanr(va, vb).correlation, mean_abs_diff=float(np.abs(va - vb).mean()),
                                        pixel_own=ga["pixel"].mean(), pixel_official=gb["pixel"].mean(),
                                        median_own=float(np.median(va)), median_official=float(np.median(vb))))
    F = {k: pd.DataFrame(v) for k, v in Tb.items()}
    for k, df in F.items():
        if not df.empty:
            df.to_csv(OUT / f"full_{k}.csv", index=False)
    return F


# =============================================================== stage 8: figures + report
def figures(F, jobs_df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fd = OUT / "figures"
    fd.mkdir(exist_ok=True)
    gcol = {"supervised IN-1k": "#4C72B0", "supervised IN-21k": "#55A868", "self-supervised": "#C44E52",
            "weakly supervised": "#8172B2", "vision-language": "#CCB974"}
    C = F["curves"]
    if not C.empty:
        C = C[C["probe"] == "logreg"]
        for (cname, design), cv in C.groupby(["cond", "design"]):
            sess = [s for s in ("within", "repeat", "cross") if s in cv["session"].unique()]
            fig, axs = plt.subplots(1, len(sess), figsize=(4.6 * len(sess), 4.2), sharey=True, squeeze=False)
            for ax, s in zip(axs[0], sess):
                q = cv[cv["session"] == s]
                for m, g in q.groupby("model"):
                    g = g.sort_values("d_mm")
                    gg = g["group"].iloc[0]
                    if m == "pixel":
                        ax.plot(g["d_mm"], g["mean"], "o-", color="red", lw=2.2, ms=3, label="pixel", zorder=5)
                    elif gg == "random":
                        ax.plot(g["d_mm"], g["mean"], color="#888888", lw=1, ls="--")
                    else:
                        ax.plot(g["d_mm"], g["mean"], color=gcol.get(gg, "#4C72B0"), lw=0.6, alpha=0.3)
                for gname, col in gcol.items():
                    h = q[q["group"] == gname].groupby("d_mm")["mean"].median()
                    if len(h):
                        ax.plot(h.index, h.values, "o-", color=col, lw=2, ms=3, label=f"{gname} (median)")
                ax.axhline(0.5, color="k", lw=0.5, ls=":")
                ax.set_xlabel("Distance to nearest probe-fit slice (mm)")
                ax.set_title(f"{cname}/{design}: {s}", fontsize=9)
            axs[0][0].set_ylabel("Identifiability (chance-adjusted)")
            axs[0][-1].legend(fontsize=6)
            fig.tight_layout()
            fig.savefig(fd / f"decay_{cname}_{design}.png", dpi=170)
            plt.close(fig)
    TBn = F["time_bins"]
    if not TBn.empty:
        for (cname, design), tb in TBn.groupby(["cond", "design"]):
            fig, axs = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
            for ax, metric in zip(axs, ("d0", "far")):
                q = tb[tb["metric"] == metric]
                for m, g in q.groupby("model"):
                    g = g.sort_values("x_mid")
                    if m == "pixel":
                        ax.plot(g["x_mid"], g["mean"], "o-", color="red", lw=2.2, label="pixel")
                    elif m == "pretrained_mean":
                        ax.plot(g["x_mid"], g["mean"], "o-", color="black", lw=2.2, label="pretrained mean")
                    elif g["group"].iloc[0] in gcol:
                        ax.plot(g["x_mid"], g["mean"], color=gcol[g["group"].iloc[0]], lw=0.6, alpha=0.35)
                ax.set_xlabel("years between visits" if "0-1.5" in set(q["bin"]) else "visit index (time proxy)")
                ax.set_title(f"{cname}/{design}: {'same location (0 mm)' if metric == 'd0' else 'd >= 2 mm'}", fontsize=9)
            axs[0].set_ylabel("Identifiability (chance-adjusted)")
            axs[1].legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(fd / f"time_{cname}_{design}.png", dpi=170)
            plt.close(fig)
    G = F["gen"]
    if not G.empty:
        for (cname, design), d in G.groupby(["cond", "design"]):
            d = d.sort_values("GEN")
            y = np.arange(len(d))
            fig, ax = plt.subplots(figsize=(6, 0.27 * len(d) + 1.4))
            cols = ["red" if m == "pixel" else ("#888888" if g == "random" else gcol.get(g, "#333"))
                    for m, g in zip(d["model"], d["group"])]
            ax.errorbar(d["GEN"], y, xerr=[d["GEN"] - d["lo"], d["hi"] - d["GEN"]], fmt="none", ecolor="#bbbbbb")
            ax.scatter(d["GEN"], y, c=cols, s=16, zorder=3)
            ax.set_yticks(y)
            ax.set_yticklabels(d["model"], fontsize=7)
            ax.set_xlim(-0.05, 1.05)
            ax.set_xlabel("GEN: cross-session identifiability, d >= 2 mm (chance-adjusted)")
            ax.set_title(f"{cname}/{design}", fontsize=9)
            fig.tight_layout()
            fig.savefig(fd / f"gen_forest_{cname}_{design}.png", dpi=170)
            plt.close(fig)
    if jobs_df is not None and "ncc" in jobs_df:
        try:
            fig, axs = plt.subplots(1, 4, figsize=(13, 3.4))
            axs[0].hist(jobs_df["ncc"].dropna(), bins=30, color="#4C72B0")
            axs[0].set_title("Registration NCC to template", fontsize=9)
            sample = jobs_df[jobs_df["ok"]].sample(min(3, int(jobs_df["ok"].sum())), random_state=0)
            for ax, r in zip(axs[1:], sample.itertuples()):
                ax.imshow(np.load(r.npz)["mid"].T, cmap="gray", origin="lower")
                ax.set_title(f"{r.session} (NCC {r.ncc:.2f})", fontsize=8)
                ax.axis("off")
            fig.tight_layout()
            fig.savefig(fd / "registration_qc.png", dpi=150)
            plt.close(fig)
        except Exception as e:  # noqa: BLE001
            T.log(f"[fig] registration QC skipped: {e}")
    V = F["valid"]
    if not V.empty:
        V.to_csv(OUT / "registration_validation.csv", index=False)


def report(F, jobs_df, clin, elapsed):
    try:
        import tabulate  # noqa: F401
    except ImportError:
        pd.DataFrame.to_markdown = lambda self, index=False, **kw: "```\n" + self.to_string(index=index) + "\n```"
    L = ["# TIDE full run (OASIS-2 + OASIS-1 registration check)", "", f"Total time: {elapsed / 3600:.2f} h", "",
         "## Stage status", "", "```", json.dumps(STATUS, indent=2), "```", ""]
    if jobs_df is not None and "ncc" in jobs_df:
        L += [f"Registration: {int(jobs_df['ok'].sum())}/{len(jobs_df)} volumes passed; NCC median "
              f"{jobs_df['ncc'].median():.3f} (min {jobs_df['ncc'].min():.3f}).", ""]
    if not F["valid"].empty:
        L += ["## Registration validation (own registration vs official T88, OASIS-1 reliability, GEN)", "",
              F["valid"].round(3).to_markdown(index=False), ""]
    G = F["gen"]
    if not G.empty:
        L += ["## GEN (cross-session, d >= 2 mm) per condition / design", ""]
        for key, g in G.groupby(["cond", "design"]):
            pre = g[~g["group"].isin(["random", "pixel"])].sort_values("GEN", ascending=False)
            px = g[g["model"] == "pixel"].iloc[0]
            L.append(f"- {'/'.join(key)} (S={int(px['n_subj'])}): pixel {px['GEN']:.3f} [{px['lo']:.3f},{px['hi']:.3f}]; "
                     f"pretrained {pre['GEN'].min():.3f}-{pre['GEN'].max():.3f}; above pixel "
                     f"{int((pre['EG_lo'] > 0).sum())}/{len(pre)}, below {int((pre['EG_hi'] < 0).sum())}/{len(pre)}; "
                     "top3 " + ", ".join(f"{r.model} {r.GEN:.3f}" for r in pre.head(3).itertuples())
                     + "; bottom3 " + ", ".join(f"{r.model} {r.GEN:.3f}" for r in pre.tail(3).itertuples()))
        L.append("")
    Tt = F["time"]
    if not Tt.empty:
        L += ["## Time axis: change in identifiability per year between visits", "",
              f"Time axis: {Tt['time_axis'].iloc[0]}", ""]
        keep = Tt[Tt["model"].isin(["pixel", "pretrained_mean", "mae_vitb16", "dino_vits16", "densenet121_in1k",
                                    "resnet50_in1k", "clip_vitb16_openai", "biomedclip_vitb16"])]
        L += [keep[["cond", "design", "metric", "model", "n_units", "slope_per_year", "lo", "hi", "spearman",
                    "dist_slope_per_mm", "mm_equivalent_of_one_year"]].round(4).to_markdown(index=False), ""]
        for (c, d, met), q in Tt.groupby(["cond", "design", "metric"]):
            enc = q[~q["group"].isin(["random", "pixel", "pretrained mean"])]
            L.append(f"- {c}/{d}/{met}: encoders with slope CI < 0: {int((enc['hi'] < 0).sum())}/{len(enc)}; "
                     f"median slope {enc['slope_per_year'].median():+.4f}/yr; median mm-equivalent of one year "
                     f"{enc['mm_equivalent_of_one_year'].median():.3f} mm")
        L.append("")
    Cl = F["clin"]
    if not Cl.empty:
        L += ["## Clinical groups (last visit per subject)", "", Cl.round(3).to_markdown(index=False), ""]
    D = F["disc"]
    if not D.empty:
        L += ["## Per distance bin (pretrained encoders, logreg)", "",
              D[["cond", "design", "session", "d_mm", "n_subj", "pixel", "mean", "min", "max", "n_above_pixel",
                 "n_below_pixel", "frac_pairs_significant"]].round(3).to_markdown(index=False), ""]
    fs = F["fac"]
    if not fs.empty:
        L += ["## Significant factor differences on GEN", ""]
        L += [f"- {r.cond}/{r.design} {r.factor}: {r.comparison} = {r.mean:+.3f} [{r.lo:+.3f},{r.hi:+.3f}]"
              for r in fs[fs["significant"] == True].itertuples()] or ["- none"]  # noqa: E712
        L.append("")
    if not F["cap"].empty:
        L += ["## Capacity (Spearman log-params vs GEN)", "", F["cap"].round(3).to_markdown(index=False), ""]
    if clin is None:
        L += ["Note: no oasis_longitudinal sheet found; the time axis is the visit index, not years.", ""]
    (OUT / "REPORT_FULL.md").write_text("\n".join(L), encoding="utf-8")


# =============================================================== main
def main():
    global OUT
    from encode_slices import REGISTRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="Datasets")
    ap.add_argument("--tide-out", default="tide_oasis1")
    ap.add_argument("--cache-root", default=".")
    ap.add_argument("--out", default="tide_full_oasis2")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--reg-procs", type=int, default=4)
    ap.add_argument("--reg-threads", type=int, default=2)
    ap.add_argument("--template-n", type=int, default=40)
    ap.add_argument("--ncc-min", type=float, default=0.6)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--boot-time", type=int, default=500)
    ap.add_argument("--min-n", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--skip-register", action="store_true")
    ap.add_argument("--redo-probes", action="store_true")
    ap.add_argument("--rebuild-reg", action="store_true",
                    help="drop registered caches + their probe results and rebuild them with the current --ncc-min "
                         "(registered volumes themselves are reused)")
    args = ap.parse_args()

    t_start = time.time()
    OUT = Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)
    T.LOGFILE = OUT / "full_log.txt"
    names = ["pixel"] + list(REGISTRY)
    info = {"pixel": ("floor", "pixel"), **{k: (v[4], v[5]) for k, v in REGISTRY.items()}}
    T.log(f"TIDE full OASIS-2 run started | datasets {args.datasets} | out {OUT}")

    idx = run_stage("1_index", stage_index, args.datasets)
    raw_cdir = run_stage("2_raw_oasis2", stage_raw, idx, args, names) if idx is not None else None
    clin = run_stage("3_clinical", stage_clinical, [args.datasets, "."])
    jobs_df = None
    if not args.skip_register and idx is not None:
        jobs_df = run_stage("4_register", stage_register, idx, args)
    if args.rebuild_reg and jobs_df is not None:
        import shutil
        for g in ("oasis1val", "oasis2"):
            for v in ("reg", "regmask"):
                d = Path(args.cache_root) / f"feats_{g}_{v}"
                if d.exists():
                    shutil.rmtree(d)
                    T.log(f"[rebuild-reg] removed {d}")
        for c in ("o2_reg", "o2_regmask", "o1val_reg", "o1val_regmask"):
            p = OUT / f"probes_{c}.pkl"
            if p.exists():
                p.unlink()
                T.log(f"[rebuild-reg] removed {p}")
    made = run_stage("5_reg_encode", stage_reg_encode, jobs_df, args, names) if jobs_df is not None else None
    made = made or {}
    params = run_stage("params", T.count_params, Path(args.tide_out)) or {}

    conds, MM = {}, {}
    if raw_cdir is not None:
        conds["o2_raw"] = (raw_cdir, True, None)
        MM["o2_raw"] = 1.25
    for key, cname in (("oasis2_reg", "o2_reg"), ("oasis2_regmask", "o2_regmask"),
                       ("oasis1val_reg", "o1val_reg"), ("oasis1val_regmask", "o1val_regmask")):
        if key in made:
            conds[cname] = (made[key], False, None)
            MM[cname] = 1.0
    try:
        idx_t88 = pd.read_csv(Path(args.tide_out) / "index_t88.csv")
        rel = set(idx_t88[idx_t88["visit"] >= 2]["subject"])
        for cname, cd in (("o1off_gfc", "feats_oasis1_t88_gfc_grid"), ("o1off_masked", "feats_oasis1_t88_masked_grid")):
            cdir = Path(args.cache_root) / cd
            if (cdir / "scans.csv").exists():
                conds[cname] = (cdir, False, rel)
                MM[cname] = 1.0
    except Exception as e:  # noqa: BLE001
        T.log(f"[conds] official OASIS-1 caches not added: {e}")

    Rs = {}
    for cname, (cdir, use_b, keep) in conds.items():
        R = run_stage(f"6_probe_{cname}", probe_cond, cname, cdir, use_b, keep, names, args)
        if R is not None:
            Rs[cname] = R
    F = run_stage("7_analysis", analyze, Rs, MM, info, params, clin, args)
    if F is not None:
        run_stage("8_figures", figures, F, jobs_df)
        run_stage("8_report", report, F, jobs_df, clin, time.time() - t_start)
    T.log(f"ALL DONE in {(time.time() - t_start) / 3600:.2f} h -> {OUT}  (see STATUS.json and REPORT_FULL.md)")


if __name__ == "__main__":
    main()
