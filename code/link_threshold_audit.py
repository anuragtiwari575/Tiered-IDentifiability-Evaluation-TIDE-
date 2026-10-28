#!/usr/bin/env python3
"""
link_threshold_audit.py - how the cross-release linkage count depends on the threshold rule.

Re-runs part C of tide_extras.py ONLY (reuses the existing feature caches; no registration, no
encoding). For several rules for the decision threshold tau it reports

  * how many OASIS-2 queries are linked,
  * how concordant the linked pairs are in sex and age, against a random-pair baseline,
  * the calibration recall at that tau,

so that the count and the evidence that the links are real can be read side by side.

Background: the published rule is tau = max(q999(calibration impostors), q999(all query-gallery
scores)). The second term is computed on the queries themselves, so the queries help choose the
threshold that is then applied to them. When that term binds, roughly 0.1% of the n_query x
n_gallery scores exceed tau by construction, which fixes the count almost regardless of the data.
This script quantifies that.

Run from the directory holding tide_extras.py and tide_run.py:

    python link_threshold_audit.py --cache-root . --out tide_extras

Writes <out>/link_threshold_audit.csv with counts and concordance only. Subject identifiers are
never written out, in line with the OASIS data-use terms.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import tide_extras as E
import tide_run as T

VARIANTS = (("masked", "feats_oasis1_t88_masked_grid", "feats_oasis2_regmask", "feats_oasis1val_regmask"),
            ("gfc", "feats_oasis1_t88_gfc_grid", "feats_oasis2_reg", "feats_oasis1val_reg"))


def concordance(linked_idx, qsub, gsub, best_pix, qfirst, gfirst, meta):
    """Sex agreement and median |age difference| over the linked pairs (aggregate only)."""
    sx, ad = [], []
    for qi in linked_idx:
        mq = meta.get(qfirst[qsub[qi]][1], {})
        mg = meta.get(gfirst[gsub[best_pix[qi]]][1], {})
        if mq and mg:
            sx.append(mq.get("sex") == mg.get("sex"))
            a1, a2 = mq.get("age", np.nan), mg.get("age", np.nan)
            ad.append(abs(a1 - a2) if np.isfinite(a1) and np.isfinite(a2) else np.nan)
    return (float(np.mean(sx)) if sx else np.nan,
            float(np.nanmedian(ad)) if ad and not np.all(np.isnan(ad)) else np.nan)


def random_baseline(qsub, gsub, qfirst, gfirst, meta, seed, n=5000):
    rng = np.random.default_rng(seed)
    sx, ad = [], []
    for _ in range(n):
        mq = meta.get(qfirst[qsub[rng.integers(len(qsub))]][1], {})
        mg = meta.get(gfirst[gsub[rng.integers(len(gsub))]][1], {})
        if mq and mg:
            sx.append(mq.get("sex") == mg.get("sex"))
            a1, a2 = mq.get("age", np.nan), mg.get("age", np.nan)
            ad.append(abs(a1 - a2) if np.isfinite(a1) and np.isfinite(a2) else np.nan)
    return float(np.mean(sx)), float(np.nanmedian(ad))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-root", default=".")
    ap.add_argument("--sheet-dirs", nargs="+", default=["Datasets", "."])
    ap.add_argument("--out", default="tide_extras")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    T.LOGFILE = out / "link_threshold_audit_log.txt"
    meta, _ = E.load_sheets(a.sheet_dirs)
    T.log(f"[audit] clinical rows {len(meta)}")

    rows = []
    root = Path(a.cache_root)
    for var, off_name, o2_name, cal_name in VARIANTS:
        off_dir, o2_dir, cal_dir = root / off_name, root / o2_name, root / cal_name
        if not all((d / "scans.csv").exists() for d in (off_dir, o2_dir, cal_dir)):
            T.log(f"[audit] {var}: caches missing, skipped")
            continue

        gfirst, _ = E.first_rows(pd.read_csv(off_dir / "scans.csv"))
        gsub = sorted(gfirst)
        g_rows = [gfirst[s][0] for s in gsub]
        qfirst, _ = E.first_rows(pd.read_csv(o2_dir / "scans.csv"))
        qsub = sorted(qfirst)
        q_rows = [qfirst[s][0] for s in qsub]
        cfirst, _ = E.first_rows(pd.read_csv(cal_dir / "scans.csv"))
        csub = sorted(s for s in cfirst if s in gfirst and cfirst[s][1] == gfirst[s][1])
        c_rows = [cfirst[s][0] for s in csub]
        gidx = {s: i for i, s in enumerate(gsub)}

        best, maxsc, gen_s, imp_s, allq = {}, {}, {}, {}, {}
        for model in E.LINK_MODELS:
            if not (off_dir / f"feats_{model}.npy").exists():
                T.log(f"[audit] {var}/{model}: features missing, skipped")
                continue
            G, tf = E.link_feats(off_dir, g_rows, model, seed=a.seed)
            Qn, _ = E.link_feats(o2_dir, q_rows, model, tf)
            Cn, _ = E.link_feats(cal_dir, c_rows, model, tf)
            simQ = np.einsum("ikd,jkd->ij", Qn, G) / G.shape[1]
            simC = np.einsum("ikd,jkd->ij", Cn, G) / G.shape[1]
            mask = np.ones_like(simC, dtype=bool)
            for i, s in enumerate(csub):
                mask[i, gidx[s]] = False
            best[model] = simQ.argmax(axis=1)
            maxsc[model] = simQ.max(axis=1)
            gen_s[model] = np.array([simC[i, gidx[s]] for i, s in enumerate(csub)])
            imp_s[model] = simC[mask]
            allq[model] = simQ.ravel()
            T.log(f"[audit] {var}/{model}: gallery {len(gsub)}, queries {len(qsub)}, calib {len(csub)}")

        if "pixel" not in best:
            continue

        # agreement criterion, unchanged: >= 3 of 4 models choose the gallery subject that pixel chose
        agree = np.array([sum(best[m][qi] == best["pixel"][qi] for m in best) for qi in range(len(qsub))])
        imp, qall = imp_s["pixel"], allq["pixel"]
        base_sx, base_ad = random_baseline(qsub, gsub, qfirst, gfirst, meta, a.seed)

        rules = [
            ("agreement only, no threshold", -np.inf, "none"),
            ("calibration impostors, q99", float(np.quantile(imp, 0.99)), "calibration"),
            ("calibration impostors, q99.9", float(np.quantile(imp, 0.999)), "calibration"),
            ("calibration impostors, maximum", float(imp.max()), "calibration"),
            ("query-gallery scores, q99.9", float(np.quantile(qall, 0.999)), "uses queries"),
            ("max of the two (as published)", float(max(np.quantile(imp, 0.999), np.quantile(qall, 0.999))),
             "uses queries"),
        ]
        for name, tau, kind in rules:
            above = maxsc["pixel"] > tau
            linked = np.where((agree >= 3) & above)[0]
            sx, ad = concordance(linked, qsub, gsub, best["pixel"], qfirst, gfirst, meta)
            rows.append(dict(
                variant=var, rule=name, tau_source=kind, tau=tau,
                n_queries=len(qsub), n_gallery=len(gsub), n_calibration=len(csub),
                queries_above_tau=int(above.sum()),
                pairs_above_tau=int((qall > tau).sum()),
                pairs_total=int(qall.size),
                n_agree_ge3=int((agree >= 3).sum()),
                n_linked=len(linked),
                calibration_recall_at_tau=float((gen_s["pixel"] > tau).mean()),
                sex_agreement=sx, median_abs_age_diff=ad,
                random_sex_agreement=base_sx, random_median_abs_age_diff=base_ad))
            T.log(f"[audit] {var} | {name}: tau={tau:.4f} linked={len(linked)} "
                  f"sex={sx if sx is None else round(sx, 3)} age={ad}")

    R = pd.DataFrame(rows)
    if R.empty:
        T.log("[audit] nothing computed - check --cache-root")
        return
    p = out / "link_threshold_audit.csv"
    R.to_csv(p, index=False)
    T.log(f"[audit] wrote {p}")
    cols = ["variant", "rule", "tau", "n_agree_ge3", "queries_above_tau", "n_linked",
            "calibration_recall_at_tau", "sex_agreement", "median_abs_age_diff"]
    print(R[cols].to_string(index=False))
    print(f"\nrandom-pair baseline: sex agreement {R.random_sex_agreement.iloc[0]:.2f}, "
          f"median |age difference| {R.random_median_abs_age_diff.iloc[0]:.0f} y")


if __name__ == "__main__":
    main()
