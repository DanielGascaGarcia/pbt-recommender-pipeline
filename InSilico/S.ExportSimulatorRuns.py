"""
S.ExportSimulatorRuns.py
One-off migration (InSilico): create simulator_runs/ from the simulations in
InSilico/simulations/, the layout used before simulator_runs/ existed.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each participant, copies to simulator_runs/<id>/Simulation_<id2>/:
        - the basal-only run: simulation_settings_original.json (the
          starting profile, the one simulated) saved as
          simulation_settings.json, and state_results.xlsx;
        - each scenario Day1|Day2/Before|After: simulation_settings.json and
          state_results.xlsx.

Inputs
    globals.sims_root, globals.simulator_runs_root, globals.ROOT

Output
    simulator_runs/<id>/Simulation_<id2>/...

Notes
    - Existing folders in simulator_runs/ are not overwritten.
    - Not part of the pipeline; it was run once to create simulator_runs/.

Usage (from the InSilico folder, with the project root on PYTHONPATH)
    python S.ExportSimulatorRuns.py
"""

import os
import shutil

import globals

# SRC: InSilico/simulations/ (the earlier layout); DEST: simulator_runs/.
SRC, DEST = globals.sims_root(), globals.simulator_runs_root()
for pid in sorted(os.listdir(SRC)):
    for sim in sorted(os.listdir(os.path.join(SRC, pid))):
        s, d = os.path.join(SRC, pid, sim), os.path.join(DEST, pid, sim)
        if not os.path.isdir(s):
            continue
        # Never overwrite what is already in simulator_runs/.
        if os.path.exists(d):
            print(f"{pid}: {os.path.relpath(d, globals.ROOT)} exists; left as it is")
            continue
        # Basal-only run: the _original settings (the profile that was simulated),
        # saved as simulation_settings.json, plus state_results.xlsx.
        start = os.path.join(s, "simulation_settings_original.json")
        if not os.path.isfile(start):
            start = os.path.join(s, "simulation_settings.json")
        os.makedirs(d)
        shutil.copy2(start, os.path.join(d, "simulation_settings.json"))
        if os.path.isfile(os.path.join(s, "state_results.xlsx")):
            shutil.copy2(os.path.join(s, "state_results.xlsx"), d)
        n = 0
        # Each scenario folder, with its settings and results.
        for day in ("Day1", "Day2"):
            for arm in ("Before", "After"):
                a = os.path.join(s, day, arm)
                if os.path.isdir(a):
                    os.makedirs(os.path.join(d, day, arm))
                    for f in ("simulation_settings.json", "state_results.xlsx"):
                        if os.path.isfile(os.path.join(a, f)):
                            shutil.copy2(os.path.join(a, f), os.path.join(d, day, arm))
                    n += 1
        print(f"{pid}: basal-only run and {n} scenarios -> {os.path.relpath(d, globals.ROOT)}")
