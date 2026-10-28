#!/usr/bin/env python3
"""Write the data-heavy LaTeX tables of the TIDE manuscript from the analysis reports.

Usage: python tables/source/make_tables.py results tables
Every number in the generated tables is read from results/; nothing is typed by hand.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

NICE = {"pixel": "Pixel floor", "resnet18_random": "ResNet-18 (random)", "vit_small_random": "ViT-S/16 (random)",
        "resnet18_in1k": "ResNet-18", "resnet50_in1k": "ResNet-50", "resnet101_in1k": "ResNet-101",
        "resnext50_in1k": "ResNeXt-50", "densenet121_in1k": "DenseNet-121", "vgg16bn_in1k": "VGG16-BN",
        "inceptionv3_in1k": "Inception-v3", "efficientnet_b0_in1k": "EfficientNet-B0",
        "efficientnetv2_s_in21k": "EfficientNetV2-S", "mobilenetv3_l_in1k": "MobileNetV3-L",
        "regnety_032_in1k": "RegNetY-032", "convnext_tiny_in1k": "ConvNeXt-T", "convnext_base_in1k": "ConvNeXt-B",
        "vit_small_in21k": "ViT-S/16", "vit_base_in21k": "ViT-B/16", "deit_small_in1k": "DeiT-S",
        "swin_tiny_in1k": "Swin-T", "swin_base_in22k": "Swin-B", "beit_base_in22k": "BEiT-B",
        "maxvit_tiny_in1k": "MaxViT-T", "coatnet0_in1k": "CoAtNet-0", "mixer_b16_in21k": "MLP-Mixer-B/16",
        "poolformer_s12_in1k": "PoolFormer-S12", "dino_vits16": "DINO ViT-S/16", "dinov2_vits14": "DINOv2 ViT-S/14",
        "dinov2_vitb14": "DINOv2 ViT-B/14", "mae_vitb16": "MAE ViT-B/16", "resnet50_swsl": "ResNet-50 SWSL",
        "clip_vitb16_openai": "CLIP ViT-B/16", "biomedclip_vitb16": "BiomedCLIP ViT-B/16"}
FAMILY = {"resnet18_random": "CNN", "vit_small_random": "Transf.", "resnet18_in1k": "CNN", "resnet50_in1k": "CNN",
          "resnet101_in1k": "CNN", "resnext50_in1k": "CNN", "densenet121_in1k": "CNN", "vgg16bn_in1k": "CNN",
          "inceptionv3_in1k": "CNN", "efficientnet_b0_in1k": "CNN", "efficientnetv2_s_in21k": "CNN",
          "mobilenetv3_l_in1k": "CNN", "regnety_032_in1k": "CNN", "convnext_tiny_in1k": "CNN",
          "convnext_base_in1k": "CNN", "vit_small_in21k": "Transf.", "vit_base_in21k": "Transf.",
          "deit_small_in1k": "Transf.", "swin_tiny_in1k": "Transf.", "swin_base_in22k": "Transf.",
          "beit_base_in22k": "Transf.", "maxvit_tiny_in1k": "Hybrid", "coatnet0_in1k": "Hybrid",
          "mixer_b16_in21k": "MLP", "poolformer_s12_in1k": "MLP", "dino_vits16": "Transf.",
          "dinov2_vits14": "Transf.", "dinov2_vitb14": "Transf.", "mae_vitb16": "Transf.", "resnet50_swsl": "CNN",
          "clip_vitb16_openai": "Transf.", "biomedclip_vitb16": "Transf.", "pixel": "--"}
GROUP = {"pixel": "--", "random": "random", "self-supervised": "SSL", "supervised IN-21k": "IN-21k",
         "supervised IN-1k": "IN-1k", "weakly supervised": "weak", "vision-language": "VL"}
COND = {"o1off_gfc": "OASIS-1 registered", "o1off_masked": "OASIS-1 skull-stripped",
        "o1val_reg": "OASIS-1 own reg.", "o1val_regmask": "OASIS-1 own reg., skull-str.",
        "o2_raw": "OASIS-2 raw", "o2_reg": "OASIS-2 registered", "o2_regmask": "OASIS-2 skull-stripped",
        "o1_raw": "OASIS-1 raw", "o1_gfc": "OASIS-1 registered", "o1_masked": "OASIS-1 skull-stripped"}


def f2(x):
    return "--" if pd.isna(x) else f"{x:.2f}"


def f3(x):
    return "--" if pd.isna(x) else f"{x:.3f}"


def ci(v, lo, hi, d=2, sign=False):
    s = "+" if sign else ""
    return f"${v:{s}.{d}f}$ $[{lo:.{d}f}, {hi:.{d}f}]$"


def md_rows(text, ncol):
    out = []
    for l in text.splitlines():
        if not l.startswith("|"):
            continue
        p = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(p) == ncol and not p[0].startswith((":", "cond", "variant", "own", "curve", "point")):
            out.append(p)
    return out


def write(name, body):
    (OUT / f"{name}.tex").write_text(body, encoding="utf-8")


full = (SRC / "REPORT_FULL.md").read_text(encoding="utf-8")
regrid = (SRC / "REPORT_regrid.md").read_text(encoding="utf-8")
extras = (SRC / "REPORT_EXTRAS.md").read_text(encoding="utf-8")
timer = (SRC / "REPORT_TIME.md").read_text(encoding="utf-8")

# ------------------------------------------------------------------ per-bin table (REPORT_FULL)
binsec = full.split("## Per distance bin")[1].split("## Significant")[0]
B = pd.DataFrame([dict(cond=p[0], design=p[1], session=p[2], d=p[3], S=int(p[4]), pixel=float(p[5]),
                       mean=float(p[6]), mn=float(p[7]), mx=float(p[8]), above=p[9], below=p[10], frac=float(p[11]))
                  for p in md_rows(binsec, 12)])
Bd = B[B.d != "nan"].copy()
Bd["d"] = Bd.d.astype(float)

# ---- Table: identifiability by distance (registered data, sparse)
rows = []
for cond in ("o1off_gfc", "o1off_masked", "o2_reg", "o2_regmask"):
    for sess, slab in (("cross", "across sessions"), ("within", "same acquisition")):
        q = Bd[(Bd.cond == cond) & (Bd.design == "sparse") & (Bd.session == sess)].set_index("d")
        S = int(q.S.iloc[0])
        pix = [f2(q.pixel.get(float(d), np.nan)) for d in range(8)]
        enc = [f2(q["mean"].get(float(d), np.nan)) for d in range(8)]
        lab = f"{COND[cond]} ($S={S}$)" if sess == "cross" else ""
        rows.append(f"{lab} & {slab} & pixel & " + " & ".join(pix) + r" \\")
        rows.append(f" & & encoders & " + " & ".join(enc) + r" \\")
    rows.append(r"\addlinespace")
write("tab_decay", "\n".join(rows[:-1]) + "\n")

# ---- Table: raw OASIS-2 by distance
rows = []
for sess, slab in (("cross", "later visit"), ("repeat", "repeat acquisition"), ("within", "same acquisition")):
    q = Bd[(Bd.cond == "o2_raw") & (Bd.design == "sparse") & (Bd.session == sess)].set_index("d")
    ds = [0.0, 1.25, 2.5, 5.0, 6.25, 7.5]
    rows.append(f"{slab} & pixel & " + " & ".join(f2(q.pixel.get(d, np.nan)) for d in ds) + r" \\")
    rows.append(f" & encoders & " + " & ".join(f2(q["mean"].get(d, np.nan)) for d in ds) + r" \\")
    rows.append(f" & encoders above / below pixel & " + " & ".join(
        (f"{q.above.get(d)}/{q.below.get(d)}" if d in q.index else "--") for d in ds) + r" \\")
write("tab_raw", "\n".join(rows) + "\n")

# ---- Table: GEN per condition and design
gen = B[B.d == "nan"]
lines = full.split("## GEN (cross-session")[1].split("## Time axis")[0].splitlines()
pat = re.compile(r"- (\w+)/(\w+) \(S=(\d+)\): pixel ([\d.]+) \[([\d.]+),([\d.]+)\]; pretrained ([\d.]+)-([\d.]+); "
                 r"above pixel (\d+)/30, below (\d+)/30")
rows = []
order = ["o1off_gfc", "o1off_masked", "o1val_reg", "o1val_regmask", "o2_raw", "o2_reg", "o2_regmask"]
recs = {(m[0], m[1]): m for m in (pat.match(l).groups() for l in lines if pat.match(l))}
for cond in order:
    for des in ("dense", "sparse"):
        m = recs[(cond, des)]
        g = gen[(gen.cond == cond) & (gen.design == des)].iloc[0]
        lab = COND[cond] if des == "dense" else ""
        rows.append(f"{lab} & {des} & {m[2]} & ${float(m[3]):.2f}$ $[{float(m[4]):.2f}, {float(m[5]):.2f}]$ & "
                    f"{g['mean']:.2f} & {float(m[6]):.2f}--{float(m[7]):.2f} & {m[8]} / {m[9]} & {g.frac:.2f}" + r" \\")
# raw OASIS-1 from the regrid report (nominal sampling of raw volumes)
rr = [l for l in regrid.splitlines() if l.startswith("- raw/reliability/sparse/rescan")]
m = re.search(r"pixel ([\d.]+); pretrained ([\d.]+)-([\d.]+); above pixel (\d+)/30, below pixel (\d+)/30", rr[0])
rg = [p for p in md_rows(regrid, 14) if p[0] == "raw" and p[1] == "reliability" and p[4] == "GEN rescan (d>=2mm)"][0]
rows.append(f"OASIS-1 raw & sparse & 20 & ${float(m[1]):.2f}$ & {float(rg[8]):.2f} & {float(m[2]):.2f}--{float(m[3]):.2f} & "
            f"{m[4]} / {m[5]} & {float(rg[13]):.2f}" + r" \\")
write("tab_gen", "\n".join(rows) + "\n")

# ---- Table: within-acquisition and near-duplicate saturation
RG = pd.DataFrame([dict(cond=p[0], pool=p[1], design=p[2], S=p[3], session=p[4], d=p[5], pixel=float(p[7]),
                        mean=float(p[8]), mn=float(p[9]), mx=float(p[10]), frac=float(p[13]))
                   for p in md_rows(regrid, 14)])
sat = [("OASIS-1 raw", RG, dict(cond="raw", pool="all", design="sparse", session="repeat", d="0"), "repeat acq.", "0"),
       ("OASIS-1 raw", RG, dict(cond="raw", pool="all", design="sparse", session="within", d="1.25"), "same acq.", "1.25"),
       ("OASIS-1 registered", RG, dict(cond="t88_gfc", pool="all", design="sparse", session="within", d="1"), "same acq.", "1"),
       ("OASIS-1 skull-stripped", RG, dict(cond="t88_masked", pool="all", design="sparse", session="within", d="1"), "same acq.", "1"),
       ("OASIS-2 raw", None, dict(cond="o2_raw", design="sparse", session="repeat", d=0.0), "repeat acq.", "0"),
       ("OASIS-2 raw", None, dict(cond="o2_raw", design="sparse", session="within", d=1.25), "same acq.", "1.25"),
       ("OASIS-2 registered", None, dict(cond="o2_reg", design="sparse", session="within", d=1.0), "same acq.", "1"),
       ("OASIS-2 skull-stripped", None, dict(cond="o2_regmask", design="sparse", session="within", d=1.0), "same acq.", "1"),
       ("OASIS-1 raw", RG, dict(cond="raw", pool="reliability", design="sparse", session="repeat", d="0"), "repeat acq.", "0"),
       ("OASIS-1 registered", RG, dict(cond="t88_gfc", pool="reliability", design="sparse", session="rescan", d="0"), "rescan", "0"),
       ("OASIS-1 skull-stripped", RG, dict(cond="t88_masked", pool="reliability", design="sparse", session="rescan", d="0"), "rescan", "0")]
rows = []
for lab, src, key, slab, dlab in sat:
    if src is None:
        q = Bd
        for k, v in key.items():
            q = q[q[k] == v]
        S = int(q.S.iloc[0])
    else:
        q = src
        for k, v in key.items():
            q = q[q[k] == v]
        S = int(q.S.iloc[0])
    r = q.iloc[0]
    rows.append(f"{lab} & {S} & {slab} & {dlab} & {r.pixel:.3f} & {r['mean']:.3f} & {r.mn:.2f}--{r.mx:.2f} & {r.frac:.2f}" + r" \\")
    if lab == "OASIS-2 skull-stripped":
        rows.append(r"\addlinespace")
write("tab_saturation", "\n".join(rows) + "\n")

# ---- Table: discriminability by protocol cell
rows = []
cells = [("OASIS-1 registered", RG, dict(cond="t88_gfc", pool="reliability", design="sparse"), ("within", "rescan"), [0, 1, 2, 3, 4]),
         ("OASIS-1 skull-stripped", RG, dict(cond="t88_masked", pool="reliability", design="sparse"), ("within", "rescan"), [0, 1, 2, 3, 4]),
         ("OASIS-1 registered", RG, dict(cond="t88_gfc", pool="all", design="sparse"), ("within",), [0, 1, 2, 3, 4]),
         ("OASIS-1 skull-stripped", RG, dict(cond="t88_masked", pool="all", design="sparse"), ("within",), [0, 1, 2, 3, 4]),
         ("OASIS-2 registered", None, dict(cond="o2_reg", design="sparse"), ("within", "cross"), [0, 1, 2, 3, 4]),
         ("OASIS-2 skull-stripped", None, dict(cond="o2_regmask", design="sparse"), ("within", "cross"), [0, 1, 2, 3, 4])]
for lab, src, key, sessions, ds in cells:
    for j, sess in enumerate(sessions):
        if src is None:
            q = Bd[(Bd.cond == key["cond"]) & (Bd.design == key["design"]) & (Bd.session == sess)]
            S = int(q.S.iloc[0])
            vals = {float(d): f for d, f in zip(q.d, q.frac)}
        else:
            q = src[(src.cond == key["cond"]) & (src.pool == key["pool"]) & (src.design == key["design"]) &
                    (src.session == sess)]
            S = int(q.S.iloc[0])
            vals = {float(d): f for d, f in zip(q.d, q.frac) if d != "nan"}
        name = {"cross": "later visit", "rescan": "rescan", "within": "same acquisition"}[sess]
        l0 = f"{lab} ($S={S}$)" if j == 0 else ""
        rows.append(f"{l0} & {name} & " + " & ".join(f2(vals.get(float(d), np.nan)) for d in ds) + r" \\")
write("tab_disc", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ verification (REPORT_EXTRAS B)
pat = re.compile(r"- (\w+) @ ([\d.]+) mm \(S=(\d+)\): pixel AUC ([\d.]+) EER ([\d.]+) TAR@1%FAR ([\d.]+) "
                 r"rank-1\(subject\) ([\d.]+); encoders AUC median ([\d.]+) \(range ([\d.]+)-([\d.]+)\), best (\w+)")
rows = []
prev = None
for m in pat.findall(extras):
    c = m[0]
    lab = f"{COND[c]} & {m[2]}" if c != prev else " & "
    if prev is not None and c != prev:
        rows.append(r"\addlinespace")
    prev = c
    rows.append(f"{lab} & {float(m[1]):g} & {m[3]} & {m[4]} & {m[5]} & {m[6]} & {m[7]} & {m[8]}--{m[9]} & {NICE[m[10]]}" + r" \\")
write("tab_verif", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ time at matched S (REPORT_TIME)
def time_block(cond, design):
    sec = timer.split(f"## {cond} / {design}")[1].split("##")[0]
    out = []
    for p in md_rows(sec, 12):
        cells = " & ".join(f"{float(p[i]):.2f} / {float(p[i + 1]):.2f}" for i in range(2, 12, 2))
        out.append(f"{re.sub(r'(\d)-(\d)', r'\1--\2', p[0]).replace('OASIS-2 ', 'OASIS-2, ')} & {float(p[1]):.2f} & {cells}" + r" \\")
    return out


rows = [r"\multicolumn{7}{l}{\emph{Registered, skull-stripped}} \\"] + time_block("regmask", "sparse") + \
       [r"\addlinespace", r"\multicolumn{7}{l}{\emph{Registered, skull present}} \\"] + time_block("reg", "sparse")
write("tab_time", "\n".join(rows) + "\n")

pat = re.compile(r"- (\d) mm: encoders with significant decline over years (\d+)/30; median slope ([+-][\d.]+)/yr; "
                 r"pixel slope ([+-][\d.]+)/yr \[([+-][\d.]+),([+-][\d.]+)\]; median mm-equivalent of one year ([+-]?[\d.]+) mm")
rows = []
for cond, clab in (("regmask", "skull-stripped"), ("reg", "skull present")):
    for design in ("sparse", "dense"):
        sec = timer.split(f"## {cond} / {design}")[1].split("##")[0]
        for j, m in enumerate(pat.findall(sec)):
            lab = f"{clab} & {design}" if j == 0 else " & "
            rows.append(f"{lab} & {m[0]} & {m[1]}/30 & ${float(m[2]):+.3f}$ & ${float(m[3]):+.3f}$ $[{float(m[4]):+.3f}, {float(m[5]):+.3f}]$ & ${float(m[6]):+.2f}$" + r" \\")
        rows.append(r"\addlinespace")
write("tab_slopes", "\n".join(rows[:-1]) + "\n")

# ------------------------------------------------------------------ per-encoder table (matched S = 16)
P = pd.read_csv(SRC / "time_matched_points.csv")
Sl = pd.read_csv(SRC / "time_matched_slopes.csv")
P = P[(P.design == "sparse") & (P.session == "cross")]


def summ(cond):
    q = P[P.cond == cond]
    o1 = q[q.point == "OASIS-1 rescan"]
    o2 = q[q.point != "OASIS-1 rescan"]
    return pd.DataFrame({"o1_0": o1[o1.d_mm == 0].set_index("model")["mean"],
                         "o1_gen": o1[o1.d_mm >= 2].groupby("model")["mean"].mean(),
                         "o2_0": o2[o2.d_mm == 0].groupby("model")["mean"].mean(),
                         "o2_gen": o2[o2.d_mm >= 2].groupby("model")["mean"].mean()})


A = summ("regmask")
Bk = summ("reg")
s = Sl[(Sl.design == "sparse") & (Sl.d_mm == 0)]
sm = s[s.cond == "regmask"].set_index("model")
sr = s[s.cond == "reg"].set_index("model")
grp = P.drop_duplicates("model").set_index("model").group
rows = []
for mdl in A.sort_values("o2_gen", ascending=False).index:
    a = A.loc[mdl]
    sig_m = r"$^{*}$" if sm.loc[mdl, "significant_decline"] else ""
    sig_r = r"$^{*}$" if sr.loc[mdl, "significant_decline"] else ""
    rows.append(f"{NICE[mdl]} & {GROUP[grp[mdl]]} & {a.o1_0:.2f} & {a.o1_gen:.2f} & {a.o2_0:.2f} & "
                f"{a.o2_gen:.2f} & {Bk.loc[mdl, 'o2_gen']:.2f} & "
                f"${sm.loc[mdl, 'slope_per_year']:+.3f}$ $[{sm.loc[mdl, 'lo']:+.3f}, {sm.loc[mdl, 'hi']:+.3f}]${sig_m} & "
                f"${sr.loc[mdl, 'slope_per_year']:+.3f}${sig_r}" + r" \\")
write("tab_encoders_full", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ factor differences (REPORT_FULL)
fac = {}
for m in re.finditer(r"- (\w+)/(\w+) (pretraining|family): (.+?) minus (.+?) = ([+-][\d.]+) \[([+-][\d.]+),([+-][\d.]+)\]", full):
    fac[(m[1], m[2], m[4], m[5])] = (float(m[6]), float(m[7]), float(m[8]))
COMP = [("self-supervised", "supervised IN-1k", "SSL $-$ IN-1k"),
        ("self-supervised", "supervised IN-21k", "SSL $-$ IN-21k"),
        ("self-supervised", "vision-language", "SSL $-$ VL"),
        ("self-supervised", "weakly supervised", "SSL $-$ weak"),
        ("supervised IN-21k", "supervised IN-1k", "IN-21k $-$ IN-1k"),
        ("supervised IN-1k", "vision-language", "IN-1k $-$ VL"),
        ("supervised IN-21k", "vision-language", "IN-21k $-$ VL"),
        ("weakly supervised", "vision-language", "weak $-$ VL"),
        ("CNN", "Transformer", "CNN $-$ Transformer"),
        ("CNN", "Hybrid", "CNN $-$ Hybrid"),
        ("Hybrid", "Transformer", "Hybrid $-$ Transformer"),
        ("MLP/MetaFormer", "Transformer", "MLP $-$ Transformer")]
CONDS = ["o1off_gfc", "o1off_masked", "o2_raw", "o2_reg", "o2_regmask"]
rows = []
for a_, b_, lab in COMP:
    cells = []
    for c in CONDS:
        if (c, "sparse", a_, b_) in fac:
            v, lo, hi = fac[(c, "sparse", a_, b_)]
        elif (c, "sparse", b_, a_) in fac:
            v, lo, hi = fac[(c, "sparse", b_, a_)]
            v, lo, hi = -v, -hi, -lo
        else:
            cells.append(r"\makecell{n.s.}")
            continue
        cells.append(rf"\makecell{{${v:+.3f}$\\$[{lo:+.3f}, {hi:+.3f}]$}}")
    rows.append(f"{lab} & " + " & ".join(cells) + r" \\")
    if lab.startswith("weak $-$ VL"):
        rows.append(r"\midrule")
write("tab_factors_full", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ capacity (REPORT_FULL)
capsec = full.split("## Capacity")[1]
C = pd.DataFrame([dict(cond=p[0], design=p[1], subset=p[2], rho=float(p[4]), lo=float(p[5]), hi=float(p[6]))
                  for p in md_rows(capsec, 7)])
rows = []
for cond in ["o1off_gfc", "o1off_masked", "o1val_reg", "o1val_regmask", "o2_raw", "o2_reg", "o2_regmask"]:
    for des in ("dense", "sparse"):
        q = C[(C.cond == cond) & (C.design == des)].set_index("subset")
        lab = COND[cond] if des == "dense" else ""
        cells = []
        for sub in ("all pretrained", "CNN", "Transformer"):
            r = q.loc[sub]
            star = r"$^{*}$" if (r.hi < 0 or r.lo > 0) else ""
            cells.append(f"${r.rho:+.2f}$ $[{r.lo:+.2f}, {r.hi:+.2f}]${star}")
        rows.append(f"{lab} & {des} & " + " & ".join(cells) + r" \\")
write("tab_capacity", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ correlation length (REPORT_EXTRAS D)
dsec = extras.split("## D.")[1]
Lt = md_rows(dsec, 5)
top = {}
for m in re.finditer(r"- (.+?): top3 (\w+) ([\d.]+), \w+ [\d.]+, \w+ [\d.]+; bottom3 \w+ [\d.]+, \w+ [\d.]+, (\w+) ([\d.]+); median R2 ([\d.]+)", dsec):
    top[m[1]] = (m[2], float(m[3]), m[4], float(m[5]), float(m[6]))
CURVE = {"OASIS-1 t88_masked reliability rescan": ("OASIS-1 skull-stripped", "rescan", 20),
         "OASIS-1 t88_masked all within": ("OASIS-1 skull-stripped", "same acq.", 416),
         "OASIS-1 t88_gfc reliability rescan": ("OASIS-1 registered", "rescan", 20),
         "OASIS-1 t88_gfc all within": ("OASIS-1 registered", "same acq.", 416),
         "OASIS-2 o2_regmask cross": ("OASIS-2 skull-stripped", "later visit", 118),
         "OASIS-2 o2_regmask within": ("OASIS-2 skull-stripped", "same acq.", 118),
         "OASIS-2 o2_reg cross": ("OASIS-2 registered", "later visit", 118)}


def lam(x):
    return "$>20$" if x > 20 else f"{x:.1f}"


rows = []
for key in ["OASIS-1 t88_masked reliability rescan", "OASIS-1 t88_masked all within", "OASIS-2 o2_regmask cross",
            "OASIS-2 o2_regmask within", "OASIS-1 t88_gfc reliability rescan", "OASIS-1 t88_gfc all within",
            "OASIS-2 o2_reg cross"]:
    p = [r for r in Lt if r[0] == key][0]
    t = top[key]
    c = CURVE[key]
    rows.append(f"{c[0]} & {c[1]} & {c[2]} & {lam(float(p[3]))} & {lam(float(p[4]))} & "
                f"{NICE[t[0]]} ({lam(t[1])}) & {NICE[t[2]]} ({lam(t[3])}) & ${float(p[2]):+.2f}$ & {t[4]:.2f}" + r" \\")
write("tab_lambda", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ privacy-utility (REPORT_EXTRAS A)
asec = extras.split("## A.")[1].split("Top-5")[0]
rows = []
for p in md_rows(asec, 10):
    par = ", ".join(NICE[x.strip()] for x in p[9].split(","))
    rows.append(f"{COND[p[0]]} & ${float(p[2]):+.2f}$ $[{float(p[3]):+.2f}, {float(p[4]):+.2f}]$ & "
                f"{NICE[p[5]]} ({float(p[6]):.2f}) & {float(p[7]):.2f} & {float(p[8]):.2f} & {par}" + r" \\")
write("tab_utility", "\n".join(rows) + "\n")

tsec = extras.split("Top-5 AUC per condition:")[1].split("## B.")[0]
rows = []
prev = None
for p in md_rows(tsec, 6):
    if p[1] == "model":
        continue
    lab = COND[p[0]] if p[0] != prev else ""
    if prev is not None and p[0] != prev:
        rows.append(r"\addlinespace")
    prev = p[0]
    rows.append(f"{lab} & {NICE[p[1]]} & ${float(p[2]):.3f}$ $[{float(p[3]):.2f}, {float(p[4]):.2f}]$ & {float(p[5]):.2f}" + r" \\")
write("tab_top5", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ linkage calibration (REPORT_EXTRAS C), counts only
# Only the calibration distributions are taken from here; the threshold, its recall and the linked
# counts come from the threshold audit below, because the tau reported in REPORT_EXTRAS was not
# independent of the queries.
csec = extras.split("## C.")[1].split("## D.")[0]
rows = []
prev = None
for p in md_rows(csec, 12):
    if p[1] == "random pairs":
        continue
    var = {"masked": "skull-stripped", "gfc": "with skull"}[p[0]]
    lab = var if p[0] != prev else ""
    if prev is not None and p[0] != prev:
        rows.append(r"\addlinespace")
    prev = p[0]
    rows.append(f"{lab} & {NICE[p[1]]} & {int(float(p[4]))} & {float(p[5]):.3f} & {float(p[6]):.3f}" + r" \\")
write("tab_linkage", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ linkage threshold sensitivity
RULES = {"agreement only, no threshold": ("Agreement only, no threshold", ""),
         "calibration impostors, q99": ("Calibration impostors, 99th pct", ""),
         "calibration impostors, q99.9": ("Calibration impostors, 99.9th pct", r"$^{\ast}$"),
         "calibration impostors, maximum": ("Calibration impostors, maximum", ""),
         "query-gallery scores, q99.9": (r"Query--gallery scores, 99.9th pct", r"$^{\dagger}$")}
thr = (SRC / "REPORT_LINK_THRESHOLD.md").read_text(encoding="utf-8")
rows = []
prev = None
for line in thr.splitlines():
    tok = line.split()
    if len(tok) < 9 or tok[0] not in ("masked", "gfc"):
        continue
    var, tail, rule = tok[0], tok[-7:], " ".join(tok[1:-7])
    if rule not in RULES:
        continue
    name, mark = RULES[rule]
    tau, nagree, _above, linked, recall, sx, ad = tail
    lab = {"masked": "Skull-stripped", "gfc": "With skull"}[var] if var != prev else ""
    if prev is not None and var != prev:
        rows.append(r"\addlinespace")
    prev = var
    f_tau = "--" if tau == "-inf" else f"{float(tau):.3f}"
    f_sx = "--" if sx.lower() == "nan" else f"{float(sx):.2f}"
    f_ad = "--" if ad.lower() == "nan" else f"{float(ad):.1f}"
    rows.append(f"{lab} & {name}{mark} & {f_tau} & {float(recall):.3f} & {int(nagree)} & {int(linked)} & "
                f"{f_sx} & {f_ad}" + r" \\")
write("tab_linksens", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ clustered time bootstrap
clu = (SRC / "REPORT_TIME_CLUSTER.md").read_text(encoding="utf-8")
CLU_COND = {"reg": "Skull present", "regmask": "Skull-stripped"}
rows, prev = [], None
for m in re.finditer(r"## (reg|regmask) .*?\n(.*?)(?=\n## |\nPer-encoder)", clu, re.S):
    cond, blk = m[1], m[2]
    for ln in re.finditer(r"- (\d) mm: pixel slope ([+-][\d.]+)/yr \[([+-][\d.]+), ([+-][\d.]+)\]; "
                          r"encoders median ([+-][\d.]+)/yr, (\d+)/(\d+) with interval below zero", blk):
        lab = CLU_COND[cond] if cond != prev else ""
        if prev is not None and cond != prev:
            rows.append(r"\addlinespace")
        prev = cond
        rows.append(f"{lab} & {ln[1]} & ${float(ln[2]):+.4f}$ $[{float(ln[3]):+.4f}, {float(ln[4]):+.4f}]$ & "
                    f"${float(ln[5]):+.4f}$ & {ln[6]}/{ln[7]}" + r" \\")
write("tab_timecluster", "\n".join(rows) + "\n")

# ------------------------------------------------------------------ registration validation
V = pd.read_csv(SRC / "registration_validation.csv")
rows = []
for _, r in V.iterrows():
    lab = {"o1val_reg": "registered", "o1val_regmask": "registered, skull-stripped"}[r.own]
    rows.append(f"{lab} & {r.design} & {int(r.n_models)} & {r.spearman:.2f} & {r.mean_abs_diff:.3f} & "
                f"{r.pixel_own:.2f} / {r.pixel_official:.2f} & {r.median_own:.2f} / {r.median_official:.2f}" + r" \\")
write("tab_regval", "\n".join(rows) + "\n")
print("tables written:", sorted(p.name for p in OUT.glob("tab_*.tex")))
