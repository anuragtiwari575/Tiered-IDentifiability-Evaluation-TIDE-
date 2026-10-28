#!/usr/bin/env python3
"""
Diagnose the TIDE registration step.

1. NCC distribution from registration_qc.csv (unimodal around the threshold = threshold too strict;
   bimodal = some registrations failed).
2. For the 40 OASIS-1 validation sessions: correlate OUR registered slices with the OFFICIAL T88 slices of
   the same session (same atlas space, same slice positions). Correct registration -> high correlation.
   Also reports the correlation with another subject's official slices (baseline) and whether an in-plane
   flip of our slices would match better (orientation error).
3. Montage: ours vs official (3 OASIS-1 sessions), plus OASIS-2 low-NCC and high-NCC examples.

Usage:
  python check_registration.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("tide_full_oasis2")
OFF = {"reg": Path("feats_oasis1_t88_gfc_grid"), "regmask": Path("feats_oasis1_t88_masked_grid")}


def corr(a, b):
    a = a.astype(np.float32).ravel()
    b = b.astype(np.float32).ravel()
    a -= a.mean()
    b -= b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-8))


def main():
    qc = pd.read_csv(OUT / "registration_qc.csv")
    print("== NCC to template (quantiles) ==")
    for g, d in qc.groupby("group"):
        q = d["ncc"].quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).to_dict()
        print(f"  {g}: n={len(d)} passed={int(d['ok'].sum())} quantiles={q}")
    hist, edges = np.histogram(qc["ncc"].dropna(), bins=12)
    print("  histogram:", " ".join(f"{edges[i]:.2f}:{hist[i]}" for i in range(len(hist))))

    val = qc[qc["group"] == "oasis1val"]
    for var, odir in OFF.items():
        if not (odir / "scans.csv").exists():
            print(f"\n[skip] {odir} not found")
            continue
        osc = pd.read_csv(odir / "scans.csv")
        osl = np.load(odir / "slices_uint8.npy", mmap_mode="r")
        row_of = {s: i for i, s in enumerate(osc["session"])}
        rows = []
        sessions = list(val["session"])
        for k, r in enumerate(val.itertuples()):
            if r.session not in row_of or not Path(r.npz).exists():
                continue
            d = np.load(r.npz)
            mine = d[var]
            off = np.asarray(osl[row_of[r.session]])
            other_s = sessions[(k + 3) % len(sessions)]
            other = np.asarray(osl[row_of[other_s]]) if other_s in row_of else None
            flips = {"none": mine, "flipH": mine[..., ::-1, :], "flipW": mine[..., :, ::-1],
                     "flipHW": mine[..., ::-1, ::-1]}
            fc = {k2: corr(v, off) for k2, v in flips.items()}
            pos_same = str(" ".join(map(str, d["pos"]))) == str(osc.at[row_of[r.session], "positions"])
            rows.append(dict(session=r.session, ncc_template=r.ncc, corr_same_session=fc["none"],
                             corr_other_subject=corr(mine, other) if other is not None else np.nan,
                             best_flip=max(fc, key=fc.get), best_flip_corr=max(fc.values()), positions_match=pos_same))
        df = pd.DataFrame(rows)
        df.to_csv(OUT / f"registration_check_{var}.csv", index=False)
        print(f"\n== OASIS-1 validation, {var}: ours vs official T88 ({len(df)} sessions) ==")
        print(f"  median corr same session  : {df['corr_same_session'].median():.3f}")
        print(f"  median corr other subject : {df['corr_other_subject'].median():.3f}")
        print(f"  best in-plane flip counts : {df['best_flip'].value_counts().to_dict()} "
              f"(median best-flip corr {df['best_flip_corr'].median():.3f})")
        print(f"  slice positions identical : {int(df['positions_match'].sum())}/{len(df)}")
        print(f"  corr(same session) vs NCC-to-template Spearman: "
              f"{df[['corr_same_session', 'ncc_template']].corr(method='spearman').iloc[0, 1]:.3f}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        osc = pd.read_csv(OFF["reg"] / "scans.csv")
        osl = np.load(OFF["reg"] / "slices_uint8.npy", mmap_mode="r")
        row_of = {s: i for i, s in enumerate(osc["session"])}
        v3 = [r for r in val.itertuples() if r.session in row_of][:3]
        o2 = qc[qc["group"] == "oasis2"].sort_values("ncc")
        low, high = list(o2.head(3).itertuples()), list(o2.tail(3).itertuples())
        fig, axs = plt.subplots(3, 4, figsize=(12, 9))
        for i, r in enumerate(v3):
            d = np.load(r.npz)
            K = d["reg"].shape[0]
            axs[i, 0].imshow(d["reg"][K // 2, 0], cmap="gray")
            axs[i, 0].set_title(f"OURS {r.session} (NCC {r.ncc:.2f})", fontsize=7)
            axs[i, 1].imshow(osl[row_of[r.session], K // 2, 0], cmap="gray")
            axs[i, 1].set_title(f"OFFICIAL T88 {r.session}", fontsize=7)
        for i, r in enumerate(low):
            d = np.load(r.npz)
            axs[i, 2].imshow(d["reg"][d["reg"].shape[0] // 2, 0], cmap="gray")
            axs[i, 2].set_title(f"OASIS-2 LOW {r.session} (NCC {r.ncc:.2f})", fontsize=7)
        for i, r in enumerate(high):
            d = np.load(r.npz)
            axs[i, 3].imshow(d["reg"][d["reg"].shape[0] // 2, 0], cmap="gray")
            axs[i, 3].set_title(f"OASIS-2 HIGH {r.session} (NCC {r.ncc:.2f})", fontsize=7)
        for ax in axs.ravel():
            ax.axis("off")
        fig.tight_layout()
        fig.savefig(OUT / "registration_check.png", dpi=130)
        print(f"\nmontage -> {OUT / 'registration_check.png'}")
    except Exception as e:  # noqa: BLE001
        print(f"montage skipped: {e}")


if __name__ == "__main__":
    main()
