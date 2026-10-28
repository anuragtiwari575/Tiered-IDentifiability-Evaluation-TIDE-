#!/usr/bin/env python3
"""
Step 2a - Read every raw scan ONCE and cache its fixed slice positions as uint8.

Same slice selection as extract_features.py (K positions in the central band,
offsets 0/1/6), so results stay comparable. Every encoder is then run on this
cache by encode_slices.py, so the slow volume I/O happens only once.

Output dir (also used as the features dir for run_tiers.py):
  slices_uint8.npy   (n_scans, K, n_offsets, H, W)
  scans.csv          index rows + ok / error / positions
  meta.json          settings

Usage:
  python cache_slices.py --index oasis_raw_index.csv --out feats_oasis1_v2 --workers 4
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from extract_features import ScanSlices, first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--band", type=float, nargs=2, default=(0.25, 0.75))
    ap.add_argument("--offsets", type=int, nargs="+", default=[0, 1, 6])
    ap.add_argument("--axis", type=int, default=-1, help="-1 = shortest axis")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    assert 0 in a.offsets and 1 in a.offsets, "offsets must include 0 and 1"

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    idx = pd.read_csv(a.index)
    n = len(idx)
    ok = np.zeros(n, dtype=bool)
    errs, poss, axes = [""] * n, [""] * n, [-1] * n

    ds = ScanSlices(idx["path"], a.k, a.band, a.offsets, a.axis)
    loader = torch.utils.data.DataLoader(ds, batch_size=1, num_workers=a.workers,
                                         collate_fn=first)
    arr = None
    t0 = time.time()
    for done, (i, sl, pos, ax, err) in enumerate(loader, 1):
        if err:
            errs[i] = err
            print(f"[err] {idx.at[i, 'path']}: {err}")
            continue
        s = (sl.numpy() * 255.0).round().astype(np.uint8)          # K, O, H, W
        if arr is None:
            arr = np.lib.format.open_memmap(out / "slices_uint8.npy", mode="w+",
                                            dtype=np.uint8, shape=(n, *s.shape))
        if s.shape != arr.shape[1:]:
            errs[i] = f"slice shape {s.shape} != {arr.shape[1:]}"
            print(f"[err] {idx.at[i, 'path']}: {errs[i]}")
            continue
        arr[i] = s
        ok[i], poss[i], axes[i] = True, " ".join(map(str, pos)), ax
        if done % 100 == 0:
            print(f"  {done}/{n} scans  ({time.time() - t0:.0f}s)")
    if arr is not None:
        arr.flush()
        print(f"saved slices_uint8.npy {arr.shape}")
        del arr

    idx.assign(ok=ok, error=errs, positions=poss, axis_used=axes).to_csv(out / "scans.csv", index=False)
    meta = dict(k=a.k, band=list(a.band), offsets=a.offsets, axis=a.axis, source="cache_slices.py")
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\n{ok.sum()}/{n} scans cached in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
