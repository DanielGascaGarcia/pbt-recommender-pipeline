"""
S.PrepareDemo.py
Demo mode, data stage (DEMO=1): place the py-mgipsim runs shipped in
sample_data/simulations/ where InSilico and metrics read them, so the demo
runs without the simulator.

Created: November 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Copies sample_data/simulations/ to demo_output/simulator_runs/
    (globals.simulator_runs_root() in demo mode). The input files of the demo
    participant are already in sample_data/<id>/, in the format the pipeline
    reads, so they need no download, conversion or cleaning.

Inputs
    globals.DEMO, globals.ROOT, globals.simulator_runs_root
    <ROOT>/sample_data/simulations/<id>/

Output
    demo_output/simulator_runs/<id>/

Notes
    - Stops if DEMO is not set, so it cannot overwrite the simulator runs of
      the full analysis.
    - demo_output/simulator_runs/ is deleted and copied again on every run.

Usage: DEMO=1, then python 17.ScriptforTestExperiment3.py data (or the menu).
"""

import os
import shutil
import sys

import globals

# Demo mode only: in the full run simulator_runs_root() is the real archive.
if not globals.DEMO:
    sys.exit("S.PrepareDemo.py is for demo mode only (set DEMO=1).")

# The simulator runs shipped with the demo (written by S.GenerateSampleData.py).
src = os.path.join(globals.ROOT, "sample_data", "simulations")
if not os.path.isdir(src):
    sys.exit(f"Not found: {src}")
# In demo mode: demo_output/simulator_runs/.
dest = globals.simulator_runs_root()
shutil.rmtree(dest, ignore_errors=True)          # start from the shipped files
shutil.copytree(src, dest)
for pid in sorted(os.listdir(dest)):
    print(f"{pid}: simulations -> {os.path.join(dest, pid)}")
print("\nDemo ready: run invivo, insilico and metrics with DEMO=1.")
