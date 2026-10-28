#!/usr/bin/env python3
"""
Step 2 - Frozen-encoder features at fixed slice positions of every raw scan.

For each scan we take K slice positions spread over the central band of the
slice axis (default: the shortest axis = 128-slice sagittal axis of the raw
OASIS acquisitions). For every position we keep the slices at a few offsets:

  offset 0  reference slice           (probe fit + repeat-scan / visit tiers)
  offset 1  adjacent slice            (near-duplicate tier)
  offset 6  farther slice, same scan  (same acquisition, different anatomy)

Feature sets written:
  pixel               adaptive-avg-pooled 64x64 intensities (redundancy floor)
  resnet18_random     random-init ResNet-18 (untrained floor)
  resnet18_in1k, resnet50_in1k, convnext_tiny_in1k, vit_small_in21k, dinov2_vits14

Outputs in --out:
  scans.csv            index rows + ok flag / error / slice positions used
  meta.json            settings
  feats_<name>.npy     float16, shape (n_scans, K, n_offsets, D)

Usage:
  python extract_features.py --index oasis_raw_index.csv --out feats/
"""
import argparse
import contextlib
import json
import time
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import timm
import torch
import torch.nn.functional as F

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# name -> (timm id, pretrained, extra create_model kwargs)
BACKBONES = {
    "resnet18_random": ("resnet18", False, {}),
    "resnet18_in1k": ("resnet18.tv_in1k", True, {}),
    "resnet50_in1k": ("resnet50.tv_in1k", True, {}),
    "convnext_tiny_in1k": ("convnext_tiny.fb_in1k", True, {}),
    "vit_small_in21k": ("vit_small_patch16_224.augreg_in21k_ft_in1k", True, {}),
    "dinov2_vits14": ("vit_small_patch14_dinov2.lvd142m", True, {"img_size": 224}),
}


def slice_positions(n, k, band, max_off):
    lo = int(round(band[0] * n))
    hi = int(round(band[1] * n)) - max_off - 1
    if hi <= lo:
        raise ValueError(f"band too narrow for axis length {n}")
    return np.linspace(lo, hi, k).round().astype(int)


class ScanSlices(torch.utils.data.Dataset):
    def __init__(self, paths, k, band, offsets, axis):
        self.paths, self.k, self.band = list(paths), k, band
        self.offsets, self.axis = list(offsets), axis

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        try:
            vol = np.squeeze(nib.load(self.paths[i]).get_fdata(dtype=np.float32))
            if vol.ndim != 3:
                raise ValueError(f"unexpected shape {vol.shape}")
            ax = int(np.argmin(vol.shape)) if self.axis < 0 else self.axis
            fg = vol[vol > 0]
            ref = fg if fg.size > 1000 else vol.ravel()
            lo, hi = np.percentile(ref, [1, 99])
            vol = np.clip((vol - lo) / (hi - lo + 1e-6), 0.0, 1.0)
            pos = slice_positions(vol.shape[ax], self.k, self.band, max(self.offsets))
            sl = np.stack([np.stack([np.take(vol, p + o, axis=ax) for o in self.offsets])
                           for p in pos]).astype(np.float32)          # K, O, H, W
            return i, torch.from_numpy(sl), pos, ax, None
        except Exception as e:  # noqa: BLE001
            return i, None, None, None, repr(e)


def first(batch):
    return batch[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=10, help="slice positions per scan (= n_fit per subject)")
    ap.add_argument("--band", type=float, nargs=2, default=(0.25, 0.75))
    ap.add_argument("--offsets", type=int, nargs="+", default=[0, 1, 6])
    ap.add_argument("--axis", type=int, default=-1, help="-1 = shortest axis")
    ap.add_argument("--models", nargs="+", default=list(BACKBONES))
    ap.add_argument("--pixel-size", type=int, default=64)
    ap.add_argument("--input-size", type=int, default=224)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    assert 0 in a.offsets and 1 in a.offsets, "offsets must include 0 and 1"

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    idx = pd.read_csv(a.index)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp = (torch.autocast(device_type="cuda", dtype=torch.float16)
           if dev.type == "cuda" else contextlib.nullcontext())

    models = {}
    for name in a.models:
        tid, pre, kw = BACKBONES[name]
        try:
            torch.manual_seed(0)
            m = timm.create_model(tid, pretrained=pre, num_classes=0, **kw).eval().to(dev)
            cfg = getattr(m, "pretrained_cfg", None) or {}
            mean = torch.tensor(cfg.get("mean", IMAGENET_MEAN), device=dev).view(1, 3, 1, 1)
            std = torch.tensor(cfg.get("std", IMAGENET_STD), device=dev).view(1, 3, 1, 1)
            models[name] = (m, mean, std)
            print(f"[ok]   {name} <- {tid}")
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {name} ({tid}): {e}")

    n = len(idx)
    feats = {name: [None] * n for name in ["pixel", *models]}
    ok = np.zeros(n, dtype=bool)
    errs, poss, axes = [""] * n, [""] * n, [-1] * n

    ds = ScanSlices(idx["path"], a.k, a.band, a.offsets, a.axis)
    loader = torch.utils.data.DataLoader(ds, batch_size=1, num_workers=a.workers,
                                         collate_fn=first)
    t0 = time.time()
    with torch.no_grad():
        for done, (i, sl, pos, ax, err) in enumerate(loader, 1):
            if err:
                errs[i] = err
                print(f"[err] {idx.at[i, 'path']}: {err}")
                continue
            K, O, H, W = sl.shape
            x = sl.view(K * O, 1, H, W).to(dev, non_blocking=True)
            pix = F.adaptive_avg_pool2d(x, a.pixel_size).flatten(1)
            feats["pixel"][i] = pix.view(K, O, -1).half().cpu().numpy()
            x3 = F.interpolate(x, size=(a.input_size, a.input_size), mode="bilinear",
                               align_corners=False).repeat(1, 3, 1, 1)
            for name, (m, mean, std) in models.items():
                parts = []
                for s in range(0, x3.shape[0], a.batch):
                    with amp:
                        f = m((x3[s:s + a.batch] - mean) / std)
                    parts.append(f.float())
                feats[name][i] = torch.cat(parts).view(K, O, -1).half().cpu().numpy()
            ok[i], poss[i], axes[i] = True, " ".join(map(str, pos)), ax
            if done % 100 == 0:
                print(f"  {done}/{n} scans  ({time.time() - t0:.0f}s)")

    for name, lst in feats.items():
        ref = next((v for v in lst if v is not None), None)
        if ref is None:
            continue
        arr = np.full((n, *ref.shape), np.nan, dtype=np.float16)
        for j, v in enumerate(lst):
            if v is not None:
                arr[j] = v
        np.save(out / f"feats_{name}.npy", arr)
        print(f"saved feats_{name}.npy {arr.shape}")

    idx = idx.assign(ok=ok, error=errs, positions=poss, axis_used=axes)
    idx.to_csv(out / "scans.csv", index=False)
    meta = dict(k=a.k, band=list(a.band), offsets=a.offsets, axis=a.axis,
                pixel_size=a.pixel_size, input_size=a.input_size,
                models={k: BACKBONES[k][0] for k in models})
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\n{ok.sum()}/{n} scans ok in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
