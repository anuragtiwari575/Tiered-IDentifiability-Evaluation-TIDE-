#!/usr/bin/env python3
"""
Step 2b - Run frozen encoders over the cached slices (one model at a time).

33 encoders + the pixel floor. Each model is loaded, run, saved and freed before
the next, so GPU memory never holds more than one model. Finished models are
skipped on re-run (use --overwrite to redo), so the job can be stopped and resumed.

Registry columns (also written to models_meta.csv for the paper's factor analysis):
  name -> (source, id, pretrained, create kwargs, family, pretraining)

Usage:
  python encode_slices.py --cache feats_oasis1_v2                 # all models
  python encode_slices.py --cache feats_oasis1_v2 --models pixel resnet50_in1k
  python encode_slices.py --list
"""
import argparse
import contextlib
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)

REGISTRY = {
    # ---- untrained floors ----
    "resnet18_random":       ("timm", "resnet18", False, {}, "CNN", "random"),
    "vit_small_random":      ("timm", "vit_small_patch16_224", False, {}, "Transformer", "random"),
    # ---- CNNs, supervised ----
    "resnet18_in1k":         ("timm", "resnet18.tv_in1k", True, {}, "CNN", "IN1k"),
    "resnet50_in1k":         ("timm", "resnet50.tv_in1k", True, {}, "CNN", "IN1k"),
    "resnet101_in1k":        ("timm", "resnet101.tv_in1k", True, {}, "CNN", "IN1k"),
    "resnext50_in1k":        ("timm", "resnext50_32x4d.a1h_in1k", True, {}, "CNN", "IN1k"),
    "densenet121_in1k":      ("timm", "densenet121.tv_in1k", True, {}, "CNN", "IN1k"),
    "vgg16bn_in1k":          ("timm", "vgg16_bn.tv_in1k", True, {}, "CNN", "IN1k"),
    "inceptionv3_in1k":      ("timm", "inception_v3.tv_in1k", True, {}, "CNN", "IN1k"),
    "efficientnet_b0_in1k":  ("timm", "efficientnet_b0.ra_in1k", True, {}, "CNN", "IN1k"),
    "efficientnetv2_s_in21k": ("timm", "tf_efficientnetv2_s.in21k_ft_in1k", True, {}, "CNN", "IN21k"),
    "mobilenetv3_l_in1k":    ("timm", "mobilenetv3_large_100.ra_in1k", True, {}, "CNN", "IN1k"),
    "regnety_032_in1k":      ("timm", "regnety_032.ra_in1k", True, {}, "CNN", "IN1k"),
    "convnext_tiny_in1k":    ("timm", "convnext_tiny.fb_in1k", True, {}, "CNN", "IN1k"),
    "convnext_base_in1k":    ("timm", "convnext_base.fb_in1k", True, {}, "CNN", "IN1k"),
    # ---- Transformers, supervised ----
    "vit_small_in21k":       ("timm", "vit_small_patch16_224.augreg_in21k_ft_in1k", True, {}, "Transformer", "IN21k"),
    "vit_base_in21k":        ("timm", "vit_base_patch16_224.augreg_in21k_ft_in1k", True, {}, "Transformer", "IN21k"),
    "deit_small_in1k":       ("timm", "deit_small_patch16_224.fb_in1k", True, {}, "Transformer", "IN1k"),
    "swin_tiny_in1k":        ("timm", "swin_tiny_patch4_window7_224.ms_in1k", True, {}, "Transformer", "IN1k"),
    "swin_base_in22k":       ("timm", "swin_base_patch4_window7_224.ms_in22k_ft_in1k", True, {}, "Transformer", "IN21k"),
    "beit_base_in22k":       ("timm", "beit_base_patch16_224.in22k_ft_in22k_in1k", True, {}, "Transformer", "IN21k"),
    # ---- Hybrid conv-attention ----
    "maxvit_tiny_in1k":      ("timm", "maxvit_tiny_tf_224.in1k", True, {}, "Hybrid", "IN1k"),
    "coatnet0_in1k":         ("timm", "coatnet_0_rw_224.sw_in1k", True, {}, "Hybrid", "IN1k"),
    # ---- MLP / MetaFormer ----
    "mixer_b16_in21k":       ("timm", "mixer_b16_224.goog_in21k_ft_in1k", True, {}, "MLP/MetaFormer", "IN21k"),
    "poolformer_s12_in1k":   ("timm", "poolformer_s12.sail_in1k", True, {}, "MLP/MetaFormer", "IN1k"),
    # ---- Self- / weakly-supervised ----
    "dino_vits16":           ("timm", "vit_small_patch16_224.dino", True, {}, "Transformer", "SSL"),
    "dinov2_vits14":         ("timm", "vit_small_patch14_dinov2.lvd142m", True, {"img_size": 224}, "Transformer", "SSL"),
    "dinov2_vitb14":         ("timm", "vit_base_patch14_dinov2.lvd142m", True, {"img_size": 224}, "Transformer", "SSL"),
    "mae_vitb16":            ("timm", "vit_base_patch16_224.mae", True, {}, "Transformer", "SSL"),
    "resnet50_swsl":         ("timm", "resnet50.fb_swsl_ig1b_ft_in1k", True, {}, "CNN", "weak/semi-sup"),
    # ---- Vision-language ----
    "clip_vitb16_openai":    ("timm", "vit_base_patch16_clip_224.openai", True, {}, "Transformer", "CLIP"),
    # image tower only, loaded straight from the open_clip checkpoint (no transformers / open_clip needed)
    "biomedclip_vitb16":     ("biomedclip", "microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224",
                              True, {}, "Transformer", "medical CLIP"),
}


class BiomedClipVisual(nn.Module):
    """timm ViT-B/16 trunk (CLS token) + BiomedCLIP's linear image projection (768 -> 512)."""
    def __init__(self, trunk, proj_w):
        super().__init__()
        self.trunk = trunk
        if proj_w is not None:
            self.proj = nn.Linear(proj_w.shape[1], proj_w.shape[0], bias=False)
            self.proj.weight.data.copy_(proj_w)
        else:
            self.proj = nn.Identity()

    def forward(self, x):
        return self.proj(self.trunk(x))


def build(name, dev):
    src, mid, pre, kw, _, _ = REGISTRY[name]
    torch.manual_seed(0)
    if src == "timm":
        import timm
        m = timm.create_model(mid, pretrained=pre, num_classes=0, **kw)
        cfg = getattr(m, "pretrained_cfg", None) or {}
        mean, std = cfg.get("mean", IMAGENET_MEAN), cfg.get("std", IMAGENET_STD)
    elif src == "biomedclip":
        import timm
        from huggingface_hub import hf_hub_download
        ckpt = hf_hub_download(mid, "open_clip_pytorch_model.bin")   # already in the HF cache
        sd = torch.load(ckpt, map_location="cpu", weights_only=True)
        trunk = timm.create_model("vit_base_patch16_224", pretrained=False, num_classes=0)
        pre_k = "visual.trunk."
        tsd = {k[len(pre_k):]: v for k, v in sd.items() if k.startswith(pre_k)}
        missing, unexpected = trunk.load_state_dict(tsd, strict=False)
        if missing:
            raise RuntimeError(f"BiomedCLIP trunk: {len(missing)} missing keys, e.g. {missing[:5]}")
        if unexpected:
            print(f"  [note] BiomedCLIP trunk: ignored {len(unexpected)} keys, e.g. {unexpected[:3]}")
        m, mean, std = BiomedClipVisual(trunk, sd.get("visual.head.proj.weight")), CLIP_MEAN, CLIP_STD
    else:
        raise ValueError(f"unknown source {src}")
    m = m.eval().to(dev)
    t = lambda v: torch.tensor(v, device=dev, dtype=torch.float32).view(1, 3, 1, 1)  # noqa: E731
    return m, t(mean), t(std)


def write_feats(path, rows, n, K, O, batches):
    """batches yields (row_indices, np.float16 array b,K,O,D). Writes atomically."""
    tmp = path.with_name(path.name + ".part")
    feats = None
    for rr, f in batches:
        if feats is None:
            feats = np.lib.format.open_memmap(tmp, mode="w+", dtype=np.float16,
                                              shape=(n, K, O, f.shape[-1]))
            feats[:] = np.nan
        feats[rr] = f
    if feats is None:
        return None
    shape = feats.shape
    feats.flush()
    del feats
    os.replace(tmp, path)
    return shape


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", help="folder made by cache_slices.py")
    ap.add_argument("--models", nargs="+", default=None, help="default: pixel + all registry models")
    ap.add_argument("--input-size", type=int, default=224)
    ap.add_argument("--pixel-size", type=int, default=64)
    ap.add_argument("--scans-per-batch", type=int, default=4, help="x K x offsets images per forward pass")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    meta_df = pd.DataFrame([dict(model=k, source=v[0], id=v[1], pretrained=v[2], family=v[4], pretraining=v[5])
                            for k, v in REGISTRY.items()])
    if a.list:
        print(meta_df.to_string(index=False))
        return
    if not a.cache:
        ap.error("--cache is required")

    cache = Path(a.cache)
    meta_df.to_csv(cache / "models_meta.csv", index=False)
    sl = np.load(cache / "slices_uint8.npy", mmap_mode="r")
    n, K, O, H, W = sl.shape
    ok_rows = np.where(pd.read_csv(cache / "scans.csv")["ok"].astype(bool).values)[0]
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp = (torch.autocast(device_type="cuda", dtype=torch.float16)
           if dev.type == "cuda" else contextlib.nullcontext())
    print(f"device: {dev} | cache {sl.shape} | {len(ok_rows)} ok scans")

    names = a.models or (["pixel"] + list(REGISTRY))
    bs = a.scans_per_batch
    for name in names:
        out = cache / f"feats_{name}.npy"
        if out.exists() and not a.overwrite:
            print(f"[skip] {name} (exists)")
            continue
        t0 = time.time()
        if name == "pixel":
            def gen():
                for s in range(0, len(ok_rows), bs):
                    rr = ok_rows[s:s + bs]
                    x = torch.from_numpy(np.asarray(sl[rr])).to(dev).float().div_(255.0)
                    x = x.view(-1, 1, H, W)
                    f = F.adaptive_avg_pool2d(x, a.pixel_size).flatten(1)
                    yield rr, f.view(len(rr), K, O, -1).half().cpu().numpy()
            shape = write_feats(out, ok_rows, n, K, O, gen())
            print(f"[ok]   pixel {shape} ({time.time() - t0:.0f}s)")
            continue
        if name not in REGISTRY:
            print(f"[skip] {name}: not in registry")
            continue
        try:
            m, mean, std = build(name, dev)
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {name}: could not build ({e})")
            continue

        def gen():
            with torch.no_grad():
                for s in range(0, len(ok_rows), bs):
                    rr = ok_rows[s:s + bs]
                    x = torch.from_numpy(np.asarray(sl[rr])).to(dev).float().div_(255.0)
                    x = x.view(-1, 1, H, W)
                    x = F.interpolate(x, size=(a.input_size, a.input_size), mode="bilinear",
                                      align_corners=False).repeat(1, 3, 1, 1)
                    with amp:
                        f = m((x - mean) / std)
                    yield rr, f.float().view(len(rr), K, O, -1).half().cpu().numpy()
        try:
            shape = write_feats(out, ok_rows, n, K, O, gen())
            print(f"[ok]   {name} {shape} ({time.time() - t0:.0f}s)")
        except Exception as e:  # noqa: BLE001
            print(f"[fail] {name}: {e}")
        del m
        if dev.type == "cuda":
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
