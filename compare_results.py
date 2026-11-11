"""
compare_results.py
Compare every table (CSV) of two runs, to check that a change leaves the
results unchanged.

Created: November 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Finds every .csv under the two folders (matched by relative path) and
    reports, for each one: identical, numeric difference (with the largest
    absolute difference), different layout, or present in only one run.

Notes
    - Numbers are compared with a tolerance of TOL (1e-9), so differences
      in the last digit of a float are not reported as changes.
    - Figures (.png) are not compared.

Usage (from the project root)
    python compare_results.py results_before results
"""

import os
import sys

import numpy as np
import pandas as pd

TOL = 1e-9

if len(sys.argv) != 3:
    sys.exit("Usage: python compare_results.py <folder A> <folder B>")
A, B = sys.argv[1], sys.argv[2]
for d in (A, B):
    if not os.path.isdir(d):
        sys.exit(f"Folder not found: {d}")


def tables(root):
    out = set()
    for base, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(".csv"):
                out.add(os.path.relpath(os.path.join(base, f), root))
    return out


ta, tb = tables(A), tables(B)
rows = []
for rel in sorted(ta | tb):
    if rel not in tb:
        rows.append((rel, "only in " + A, ""))
        continue
    if rel not in ta:
        rows.append((rel, "only in " + B, ""))
        continue
    a = pd.read_csv(os.path.join(A, rel))
    b = pd.read_csv(os.path.join(B, rel))
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        rows.append((rel, f"different layout {a.shape} vs {b.shape}", ""))
        continue
    num = a.select_dtypes("number").columns
    other = [c for c in a.columns if c not in num]
    if not a[other].astype(str).equals(b[other].astype(str)):
        rows.append((rel, "different text values", ""))
        continue
    if len(num) == 0:
        rows.append((rel, "identical", ""))
        continue
    x, y = a[num].to_numpy(float), b[num].to_numpy(float)
    same_nan = np.array_equal(np.isnan(x), np.isnan(y))
    diff = np.nanmax(np.abs(x - y)) if np.isfinite(x - y).any() else 0.0
    if same_nan and diff <= TOL:
        rows.append((rel, "identical", ""))
    else:
        rows.append((rel, "numeric difference" + ("" if same_nan else " (missing values differ)"),
                     f"{diff:.3g}"))

width = max(len(r[0]) for r in rows) if rows else 10
for rel, status, d in rows:
    print(f"{rel:{width}}  {status}  {d}")
n_same = sum(r[1] == "identical" for r in rows)
print(f"\n{n_same} of {len(rows)} tables identical.")
