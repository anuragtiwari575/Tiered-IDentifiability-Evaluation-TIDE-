#!/usr/bin/env python3
"""Build the V9 summary figures (F3, F4, F5, F7) from the analysis reports and CSVs."""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

PIX = "#C8323C"      # pixel floor
ENC = "#2E5EAA"      # pretrained encoders
GREY = "#6B6B6B"
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "legend.fontsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#E3E3E3", "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "lines.linewidth": 1.8, "savefig.bbox": "tight", "pdf.fonttype": 42})


def md_table(text, first_col):
    rows = [l for l in text.splitlines() if l.startswith(f"| {first_col}") or re.match(r"^\| (o1|o2)", l)]
    return rows


# ---------------- F3: distance decay ----------------
full = (SRC / "REPORT_FULL.md").read_text(encoding="utf-8")
sec = full.split("## Per distance bin")[1].split("## Significant")[0]
recs = []
for l in sec.splitlines():
    p = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(p) == 12 and p[0] and not p[0].startswith(("cond", ":")):
        try:
            recs.append(dict(cond=p[0], design=p[1], session=p[2], d=float(p[3]), S=int(p[4]), pixel=float(p[5]),
                             mean=float(p[6]), lo=float(p[7]), hi=float(p[8])))
        except ValueError:
            pass
D = pd.DataFrame(recs)
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
for ax, cond, title in ((axs[0], "o1off_masked", "OASIS-1, official T88, skull-stripped\n20 subjects, rescan within 90 days"),
                        (axs[1], "o2_regmask", "OASIS-2, own registration, skull-stripped\n118 subjects, visits 1-5 years apart")):
    for sess, ls, mk, lab in (("cross", "-", "o", "across sessions"), ("within", "--", "s", "same acquisition")):
        q = D[(D.cond == cond) & (D.design == "sparse") & (D.session == sess)].sort_values("d")
        if sess == "cross":
            ax.fill_between(q.d, q.lo, q.hi, color=ENC, alpha=0.13, lw=0)
        ax.plot(q.d, q["mean"], ls=ls, marker=mk, ms=3.5, color=ENC, label=f"encoders, mean ({lab})")
        ax.plot(q.d, q.pixel, ls=ls, marker=mk, ms=3.5, color=PIX, label=f"pixel floor ({lab})")
    ax.set_title(title)
    ax.set_xlabel("Distance to nearest probe-fit slice (mm)")
    ax.set_ylim(0, 1.03)
    ax.set_xticks(range(0, 8))
axs[0].set_ylabel("Identifiability (chance-adjusted)")
h, l = axs[1].get_legend_handles_labels()
fig.tight_layout(rect=(0, 0.11, 1, 1))
fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.savefig(OUT / "fig3_decay.pdf")
plt.close(fig)

# ---------------- F4: verification ----------------
ex = (SRC / "REPORT_EXTRAS.md").read_text(encoding="utf-8")
pat = re.compile(r"- (\w+) @ ([\d.]+) mm \(S=(\d+)\): pixel AUC ([\d.]+) EER [\d.]+ TAR@1%FAR [\d.]+ rank-1\(subject\) [\d.]+; "
                 r"encoders AUC median ([\d.]+) \(range ([\d.]+)-([\d.]+)\)")
V = pd.DataFrame([dict(cond=m[0], d=float(m[1]), S=int(m[2]), pixel=float(m[3]), med=float(m[4]), lo=float(m[5]),
                       hi=float(m[6])) for m in pat.findall(ex)])
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
for ax, cond, title in ((axs[0], "o2_raw", "OASIS-2 raw (150 subjects)"),
                        (axs[1], "o2_reg", "OASIS-2 registered (118)"),
                        (axs[2], "o2_regmask", "OASIS-2 registered, skull-stripped (118)")):
    q = V[V.cond == cond].sort_values("d")
    ax.fill_between(q.d, q.lo, q.hi, color=ENC, alpha=0.13, lw=0, label="encoders, range")
    ax.plot(q.d, q.med, "o-", ms=3.5, color=ENC, label="encoders, median")
    ax.plot(q.d, q.pixel, "s-", ms=3.5, color=PIX, label="pixel floor")
    ax.set_title(title)
    ax.set_xlabel("Offset from first-visit slice (mm)")
    ax.set_ylim(0.65, 1.01)
axs[0].set_ylabel("Verification AUC")
h, l = axs[0].get_legend_handles_labels()
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.savefig(OUT / "fig4_verification.pdf")
plt.close(fig)

# ---------------- F5: time at matched S ----------------
P = pd.read_csv(SRC / "time_matched_points.csv")
P = P[(P.design == "sparse") & (P.session == "cross")]
fig, axs = plt.subplots(2, 3, figsize=(7.2, 4.0), sharex=True, sharey=True)
for r, (cond, lab) in enumerate((("regmask", "skull-stripped"), ("reg", "skull present"))):
    for c, d in enumerate((0, 1, 2)):
        ax = axs[r, c]
        q = P[(P.cond == cond) & (P.d_mm == d)]
        px = q[q.model == "pixel"].sort_values("years")
        enc = q[~q.group.isin(["pixel", "random"])]
        g = enc.groupby("years")["mean"]
        yrs = np.array(sorted(enc.years.unique()))
        ax.fill_between(yrs, g.quantile(0.25).reindex(yrs), g.quantile(0.75).reindex(yrs), color=ENC, alpha=0.15,
                        lw=0, label="encoders, IQR")
        ax.plot(yrs, g.median().reindex(yrs), "o-", ms=3.5, color=ENC, label="encoders, median")
        ax.errorbar(px.years, px["mean"], yerr=[px["mean"] - px.lo, px.hi - px["mean"]], fmt="s-", ms=3.5, capsize=2,
                    color=PIX, label="pixel floor (95% interval)")
        ax.set_title(f"{lab}, {d} mm")
        ax.set_ylim(0.35, 1.03)
axs[1, 1].set_xlabel("Years between probe-fit scan and evaluation scan")
fig.supylabel("Identifiability (chance-adjusted, S = 16)", fontsize=8, x=0.02)
h, l = axs[0, 0].get_legend_handles_labels()
fig.tight_layout(rect=(0.02, 0.05, 1, 1))
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.savefig(OUT / "fig5_time.pdf")
plt.close(fig)

# ---------------- F7: privacy-utility summary ----------------
secA = ex.split("## A.")[1].split("Top-5")[0]
U = []
for l in secA.splitlines():
    p = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(p) >= 9 and re.match(r"o[12]_", p[0]):
        U.append(dict(cond=p[0], rho=float(p[2]), lo=float(p[3]), hi=float(p[4]), best=float(p[6]), pixel=float(p[7]),
                      age=float(p[8])))
U = pd.DataFrame(U)
names = {"o1_raw": "OASIS-1 raw", "o1_gfc": "OASIS-1 registered", "o1_masked": "OASIS-1 skull-stripped",
         "o2_raw": "OASIS-2 raw", "o2_reg": "OASIS-2 registered", "o2_regmask": "OASIS-2 skull-stripped"}
order = ["o1_raw", "o1_gfc", "o1_masked", "o2_raw", "o2_reg", "o2_regmask"]
U = U.set_index("cond").loc[order]
y = np.arange(len(U))[::-1]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.5), sharey=True)
axs[0].axvline(0, color=GREY, lw=0.8)
axs[0].errorbar(U.rho, y, xerr=[U.rho - U.lo, U.hi - U.rho], fmt="o", ms=4, capsize=2, color=ENC)
axs[0].set_xlabel("Spearman rho, identity (GEN) vs diagnosis AUC\nacross 30 encoders (95% interval)")
axs[0].set_xlim(-1, 1)
axs[1].plot(U.best, y, "o", ms=5, color=ENC, label="best encoder")
axs[1].plot(U.pixel, y, "s", ms=5, color=PIX, label="pixel floor")
axs[1].plot(U.age, y, "D", ms=4.5, color=GREY, label="age only")
axs[1].set_xlabel("Diagnosis AUC (CDR>0, subject-level CV)")
axs[1].set_xlim(0.4, 0.9)
axs[1].legend(loc="lower right", frameon=False)
axs[0].set_yticks(y)
axs[0].set_yticklabels([names[c] for c in U.index])
fig.savefig(OUT / "fig7_privacy_utility.pdf")
plt.close(fig)


# ---------------- shared parser for markdown tables ----------------
def md_rows(text, ncol):
    out = []
    for l in text.splitlines():
        if not l.startswith("|"):
            continue
        p = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(p) == ncol and not p[0].startswith((":", "cond", "variant")):
            out.append(p)
    return out


# ---------------- F2: protocol diagnostics ----------------
grid = (SRC / "REPORT_grid_nominal_offsets.md").read_text(encoding="utf-8")
nom = [(float(p[4]), float(p[5])) for p in md_rows(grid, 9)
       if p[0] == "t88_masked" and p[1] == "reliability" and p[3] == "rescan" and p[4] != "nan"]
nom = pd.DataFrame(nom, columns=["off", "mean"]).sort_values("off")
full_rows = md_rows(full, 12)
F = pd.DataFrame([dict(cond=p[0], design=p[1], session=p[2], d=float(p[3]), pixel=float(p[5]), mean=float(p[6]),
                       mn=float(p[7]), mx=float(p[8]), frac=float(p[11])) for p in full_rows if p[3] != "nan"])
reg = (SRC / "REPORT_regrid.md").read_text(encoding="utf-8")
R = pd.DataFrame([dict(cond=p[0], pool=p[1], design=p[2], session=p[4], d=float(p[5]), mean=float(p[8]),
                       mn=float(p[9]), mx=float(p[10]), frac=float(p[13])) for p in md_rows(reg, 14) if p[5] != "nan"])
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.5))
ax = axs[0]
ax.plot(nom.off, nom["mean"], "o--", ms=3.5, color=GREY, label="binned by nominal offset")
for des, mk, lab in (("dense", "o", "binned by distance, dense"), ("sparse", "s", "binned by distance, sparse")):
    q = F[(F.cond == "o1off_masked") & (F.design == des) & (F.session == "cross")].sort_values("d")
    ax.plot(q.d, q["mean"], marker=mk, ms=3.5, color=ENC, alpha=1 if des == "dense" else 0.55, label=lab)
ax.set_xlabel("Offset or distance (mm)")
ax.set_ylabel("Mean encoder identifiability")
ax.set_title("(a) Nominal-offset artefact")
ax.set_ylim(0.2, 1.32); ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.legend(frameon=False, loc="upper right", fontsize=6)
curves = [("OASIS-1 rescan, S=20", F[(F.cond == "o1off_masked") & (F.design == "sparse") & (F.session == "cross")], "-", "o"),
          ("OASIS-1 within, S=416", R[(R.cond == "t88_masked") & (R.pool == "all") & (R.design == "sparse") & (R.session == "within")], "--", "s"),
          ("OASIS-2 later visits, S=118", F[(F.cond == "o2_regmask") & (F.design == "sparse") & (F.session == "cross")], ":", "D")]
for name, q, ls, mk in curves:
    q = q.sort_values("d")
    axs[1].plot(q.d, q.mx - q.mn, ls=ls, marker=mk, ms=3.2, color=ENC, label=name)
    axs[2].plot(q.d, q.frac, ls=ls, marker=mk, ms=3.2, color=ENC, label=name)
axs[1].set_title("(b) Spread across 30 encoders")
axs[1].set_ylabel("Max $-$ min identifiability")
axs[2].set_title("(c) Encoder pairs separated")
axs[2].set_ylabel("Share of pairs, 95% CI excludes 0")
for ax in axs[1:]:
    ax.set_xlabel("Distance to nearest fit slice (mm)")
    ax.set_ylim(0, 1)
h, l = axs[1].get_legend_handles_labels()
fig.tight_layout(rect=(0, 0.08, 1, 1), w_pad=1.2)
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.savefig(OUT / "fig2_protocol_diagnostics.pdf")
plt.close(fig)

# ---------------- F6: per-encoder identifiability (matched S = 16) ----------------
P2 = pd.read_csv(SRC / "time_matched_points.csv")
P2 = P2[(P2.cond == "regmask") & (P2.design == "sparse") & (P2.session == "cross") & (P2.d_mm >= 2)]
o1 = P2[P2.point == "OASIS-1 rescan"].groupby("model")["mean"].mean()
o2 = P2[P2.point != "OASIS-1 rescan"].groupby("model")["mean"].mean()
grp = P2.drop_duplicates("model").set_index("model").group
order_m = o2.sort_values().index
GC = {"pixel": PIX, "random": "#9A9A9A", "self-supervised": "#1B7F5B", "supervised IN-21k": "#2E5EAA",
      "supervised IN-1k": "#7FA6D9", "weakly supervised": "#C77C1E", "vision-language": "#7A3E9D"}
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
fig, ax = plt.subplots(figsize=(5.2, 6.0))
y = np.arange(len(order_m))
for i, m in enumerate(order_m):
    c = GC[grp[m]]
    ax.plot([o1[m], o2[m]], [i, i], color=c, lw=0.8, alpha=0.5)
    ax.plot(o2[m], i, "o", ms=4.5, color=c)
    ax.plot(o1[m], i, "o", ms=4.5, mfc="white", mec=c, mew=1.1)
ax.set_yticks(y)
ax.set_yticklabels([NICE[m] for m in order_m], fontsize=7)
ax.set_xlabel("Cross-session identifiability at $d\\geq2$ mm (chance-adjusted, $S=16$)")
ax.set_xlim(0, 1)
from matplotlib.lines import Line2D
hs = [Line2D([], [], marker="o", ls="", color=GC[k], label=k) for k in
      ("pixel", "self-supervised", "supervised IN-21k", "supervised IN-1k", "weakly supervised", "vision-language", "random")]
hs += [Line2D([], [], marker="o", ls="", color="k", label="OASIS-2, 1-5 years (filled)"),
       Line2D([], [], marker="o", ls="", mfc="white", mec="k", label="OASIS-1, 90 days (open)")]
ax.legend(handles=hs, loc="lower right", frameon=False, fontsize=6)
fig.savefig(OUT / "fig6_encoders.pdf")
plt.close(fig)

# ---------------- F8: preprocessing conditions (QC slices) ----------------
from PIL import Image
qc_path = Path(__file__).parent / "raw" / "qc_slices.png"
if qc_path.exists():
    im = np.array(Image.open(qc_path).convert("L"))
    boxes = {0: [(35, 356), (394, 715)], 1: [(60, 332), (419, 691)], 2: [(60, 332), (419, 691)]}
    ys = [(47, 367), (414, 735), (782, 1102)]
    fig, axs = plt.subplots(2, 3, figsize=(6.2, 4.4))
    titles = ["Raw (released)", "Registered (official T88)", "Registered, skull-stripped"]
    for r in range(3):
        for c in range(2):
            (x0, x1), (y0, y1) = boxes[r][c], ys[r]
            ax = axs[c, r]
            ax.imshow(im[y0:y1, x0:x1], cmap="gray", vmin=0, vmax=255)
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            if c == 0:
                ax.set_title(titles[r])
    axs[0, 0].set_ylabel("First session")
    axs[1, 0].set_ylabel("Rescan within 90 days")
    fig.tight_layout()
    fig.savefig(OUT / "fig8_conditions.pdf", dpi=200)
    plt.close(fig)
print("figures written:", sorted(p.name for p in OUT.glob("fig*.pdf")))
