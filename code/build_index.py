#!/usr/bin/env python3
"""
Step 1 - Index every raw T1 acquisition (mpr-N) in OASIS-1 and OASIS-2.

One row per scan:
  dataset  OASIS1 / OASIS2
  subject  OAS1_0001 / OAS2_0001
  session  OAS1_0001_MR1 / OAS2_0001_MR2 ...
  visit    1, 2, ... (MR number)
  scan     N from mpr-N (repeat acquisition inside the same session)
  path     absolute path to the .hdr file
  shape    header shape (expected 256x256x128 for both datasets)

Only files inside a RAW/ folder are used, so OASIS-1 PROCESSED/ files are ignored.

Usage:
  python build_index.py --roots /data/oasis1 /data/oasis2 --out oasis_raw_index.csv
"""
import argparse
import re
import sys
from pathlib import Path

import nibabel as nib
import pandas as pd

SESS_RE = re.compile(r"(OAS([12])_(\d{4})_MR(\d+))")
SCAN_RE = re.compile(r"mpr-(\d+)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True,
                    help="Folders where the OASIS tar.gz files were extracted")
    ap.add_argument("--out", default="oasis_raw_index.csv")
    a = ap.parse_args()

    rows = []
    for root in a.roots:
        for hdr in Path(root).rglob("*.hdr"):
            if "RAW" not in hdr.parts:
                continue
            m = SESS_RE.search(str(hdr))
            s = SCAN_RE.search(hdr.name)
            if not m or not s:
                continue
            img = hdr.with_suffix(".img")
            if not img.exists():
                print(f"[warn] missing .img for {hdr}", file=sys.stderr)
                continue
            try:
                shape = "x".join(str(d) for d in nib.load(str(hdr)).shape)
            except Exception as e:  # noqa: BLE001
                print(f"[warn] unreadable header {hdr}: {e}", file=sys.stderr)
                continue
            rows.append(dict(
                dataset=f"OASIS{m.group(2)}",
                subject=f"OAS{m.group(2)}_{m.group(3)}",
                session=m.group(1),
                visit=int(m.group(4)),
                scan=int(s.group(1)),
                path=str(hdr.resolve()),
                shape=shape,
            ))

    if not rows:
        sys.exit("No raw scans found - check --roots")

    df = (pd.DataFrame(rows)
          .drop_duplicates(subset=["session", "scan"])
          .sort_values(["dataset", "subject", "visit", "scan"])
          .reset_index(drop=True))
    df.to_csv(a.out, index=False)

    # ---- sanity summary ----
    print(f"Wrote {len(df)} scans -> {a.out}\n")
    for ds, g in df.groupby("dataset"):
        n_subj = g.subject.nunique()
        n_sess = g.session.nunique()
        scans_per_sess = g.groupby("session").size().value_counts().sort_index()
        visits_per_subj = g.groupby("subject").visit.nunique().value_counts().sort_index()
        print(f"== {ds}: {n_subj} subjects, {n_sess} sessions, {len(g)} scans")
        print("   scans per session :", dict(scans_per_sess))
        print("   visits per subject:", dict(visits_per_subj))
        print("   header shapes     :", dict(g["shape"].value_counts()))
    print("\nExpected roughly: OASIS1 416 subjects (20 with an MR2 rescan), "
          "OASIS2 150 subjects / 373 sessions.")


if __name__ == "__main__":
    main()
