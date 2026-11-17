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

# -----------------------------------------------------------#
# Imports
# -----------------------------------------------------------#
import os       # walks the two folders
import sys      # the two folder names from the command line

import numpy as np    # numeric comparison (differences, missing values)
import pandas as pd   # reads each CSV as a table

# Tolerance: two numbers whose absolute difference is at most TOL count as
# equal. Floats written to CSV can differ in their last digit between runs
# (rounding of the last operation), which is not a change in the results.
TOL = 1e-9

# -----------------------------------------------------------#
# The two folders to compare
# -----------------------------------------------------------#
# Exactly two arguments: folder A (for example the copy kept before a change)
# and folder B (the results after the change).
if len(sys.argv) != 3:
    sys.exit("Usage: python compare_results.py <folder A> <folder B>")
A, B = sys.argv[1], sys.argv[2]
# Stop with a clear message if either folder does not exist.
for d in (A, B):
    if not os.path.isdir(d):
        sys.exit(f"Folder not found: {d}")


# -----------------------------------------------------------#
# Every CSV of a folder, by its path relative to that folder
# -----------------------------------------------------------#
# Relative paths (for example metrics/tables/Table3_Day1.csv) let the same
# table be matched in the two folders, whatever their names.
def tables(root):
    out = set()
    for base, _, files in os.walk(root):          # every subfolder, recursively
        for f in files:
            if f.lower().endswith(".csv"):        # only tables; figures are skipped
                out.add(os.path.relpath(os.path.join(base, f), root))
    return out


ta, tb = tables(A), tables(B)
rows = []   # one (table, status, largest difference) per table

# -----------------------------------------------------------#
# Compare table by table
# -----------------------------------------------------------#
# ta | tb = every table found in either folder, sorted so the report is in
# the same order every time.
for rel in sorted(ta | tb):
    # 1. Table in only one of the two runs (added or removed by the change).
    if rel not in tb:
        rows.append((rel, "only in " + A, ""))
        continue
    if rel not in ta:
        rows.append((rel, "only in " + B, ""))
        continue
    a = pd.read_csv(os.path.join(A, rel))
    b = pd.read_csv(os.path.join(B, rel))
    # 2. Different columns (names or order) or a different number of rows:
    #    the values cannot be compared cell by cell.
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        rows.append((rel, f"different layout {a.shape} vs {b.shape}", ""))
        continue
    # 3. Text columns (participant IDs, labels): must be exactly equal.
    #    num = numeric columns; other = everything else.
    num = a.select_dtypes("number").columns
    other = [c for c in a.columns if c not in num]
    if not a[other].astype(str).equals(b[other].astype(str)):
        rows.append((rel, "different text values", ""))
        continue
    # A table with only text columns that passed step 3 is identical.
    if len(num) == 0:
        rows.append((rel, "identical", ""))
        continue
    # 4. Numeric columns: compared with the tolerance TOL.
    x, y = a[num].to_numpy(float), b[num].to_numpy(float)
    # The missing values (NaN) must be in the same cells in both tables.
    same_nan = np.array_equal(np.isnan(x), np.isnan(y))
    # Largest absolute difference over the cells where both have a number
    # (nanmax ignores the NaN cells; 0 if no cell has a number in both).
    diff = np.nanmax(np.abs(x - y)) if np.isfinite(x - y).any() else 0.0
    if same_nan and diff <= TOL:
        rows.append((rel, "identical", ""))
    else:
        rows.append((rel, "numeric difference" + ("" if same_nan else " (missing values differ)"),
                     f"{diff:.3g}"))

# -----------------------------------------------------------#
# Report
# -----------------------------------------------------------#
# One line per table, the names aligned in a column of the width of the
# longest name; then how many tables are identical out of all compared.
width = max(len(r[0]) for r in rows) if rows else 10
for rel, status, d in rows:
    print(f"{rel:{width}}  {status}  {d}")
n_same = sum(r[1] == "identical" for r in rows)
print(f"\n{n_same} of {len(rows)} tables identical.")
