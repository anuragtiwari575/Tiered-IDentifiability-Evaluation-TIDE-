# OASIS redundancy-tier pilot (RC-SIS)

Goal: with the probe budget fixed (n_fit = 10 slices/subject), check how much
"identity" survives as the eval data moves away from the fit data:
adjacent slice → far slice (same scan) → repeat scan (same session) → rescan (≤90 d, OASIS-1) → next visit (OASIS-2).

## 0. Setup (DGX / Ant-PC)
```bash
pip install nibabel timm scikit-learn pandas matplotlib joblib
```
Disk: archives ~34 GB; keep ~80 GB free for a full extract.
Model weights download from the Hugging Face hub on first run (needs internet).

## 1. Extract
```bash
mkdir -p /data/oasis1 /data/oasis2
for f in oasis_cross-sectional_disc*.tar.gz; do tar -xzf "$f" -C /data/oasis1; done
for f in OAS2_RAW_PART*.tar.gz;            do tar -xzf "$f" -C /data/oasis2; done
```
OASIS-1 RAW only (saves space; but keep PROCESSED if you want the skull-stripped T88 variant later):
```bash
for f in oasis_cross-sectional_disc*.tar.gz; do tar -xzf "$f" -C /data/oasis1 --wildcards '*/RAW/*'; done
```

## 2. Index
```bash
python build_index.py --roots /data/oasis1 /data/oasis2 --out oasis_raw_index.csv
```
Check the printed counts (≈ OASIS1 416 subjects with 20 MR2 rescans; OASIS2 150 subjects / 373 sessions; shapes 256x256x128).

## 3. Features (GPU)
```bash
python extract_features.py --index oasis_raw_index.csv --out feats/ --workers 8
```
Defaults: K=10 positions in the central 25–75% of the 128-slice (sagittal) axis, offsets 0/1/6.
Feature sets: pixel, resnet18_random, resnet18_in1k, resnet50_in1k, convnext_tiny_in1k, vit_small_in21k, dinov2_vits14.

## 4. Tier probes (CPU)
```bash
python run_tiers.py --feats feats/ --out results/ --n-jobs 8
```
Outputs: `summary.csv`, `results_runs.csv`, `per_subject_full_pool.csv`, `tiers_<pool>.png`.

## What to send back
- console output of step 2 (counts)
- `results/summary.csv` and the `tiers_*.png` plots

## Reading the result
- Pixel ≈ deep encoders at adjacent/repeat tiers → that tier is benchmark redundancy, not learned identity.
- The drop from repeat_scan → next_visit = how much is acquisition redundancy vs durable identity.
- Caveat: these are RAW volumes (face removed, skull present, no registration). A high next_visit score
  for the pixel probe would mean skull/head shape or positioning carries identity → the next step is a
  skull-stripped (SynthStrip/HD-BET) + rigidly aligned variant before any "anatomical identity" claim.
