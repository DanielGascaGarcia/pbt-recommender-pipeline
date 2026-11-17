"""
S.SyncSimulatorResults.py
Metrics, step 1: bring the results of the before/after scenarios from
simulator_runs/ into the working copy InSilico/simulations/ that InSilico has
just rebuilt.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For every participant and scenario (Day1|Day2 / Before|After), copies
    simulator_runs/<id>/Simulation_<id2>/<day>/<arm>/state_results.xlsx into
    InSilico/simulations/<id>/Simulation_<id2>/<day>/<arm>/ only if the
    simulation_settings.json stored next to it (the one it was simulated
    with) is identical, as JSON, to the one InSilico has just written.

Inputs
    globals.simulator_runs_root, globals.sims_root, globals.ROOT

Outputs
    InSilico/simulations/<id>/.../state_results.xlsx   (copies)
    printed: one line per scenario not ready and a summary

Notes
    - The whole settings file is compared (basal, meals, boluses and every
      other input), so a result simulated with an earlier recommendation or
      other meals is never used.
    - The check cannot tell whether a state_results.xlsx was really produced
      with the settings stored next to it; keep the two files of each
      Py-mgipsim run together.
    - Writes nothing else; the metrics scripts that follow skip scenarios
      without a result.

Usage (normally through 17.ScriptforTestExperiment3.py metrics)
    python S.SyncSimulatorResults.py
"""

import json
import os
import shutil

import globals

# RUNS: simulator_runs/ (archive, never modified); WORK: InSilico/simulations/
# (working copy). Four scenarios per participant.
RUNS, WORK = globals.simulator_runs_root(), globals.sims_root()
SCENARIOS = [(d, a) for d in ("Day1", "Day2") for a in ("Before", "After")]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


ok, problems = 0, []
# insilico must have run first: it rebuilds the working copy and writes the
# scenario settings.
if not os.path.isdir(WORK):
    raise SystemExit(f"No working simulations in {WORK}: run insilico first.")
for pid in sorted(os.listdir(WORK)):
    for sim in sorted(os.listdir(os.path.join(WORK, pid))):
        for day, arm in SCENARIOS:
            # work: where InSilico wrote the settings; kept: where the simulated result
            # is archived.
            work = os.path.join(WORK, pid, sim, day, arm)
            kept = os.path.join(RUNS, pid, sim, day, arm)
            new_json = os.path.join(work, "simulation_settings.json")
            if not os.path.isfile(new_json):
                problems.append(f"{pid} {day} {arm}: no settings written by insilico")
                continue
            res, used_json = os.path.join(kept, "state_results.xlsx"), os.path.join(kept, "simulation_settings.json")
            # Not simulated yet.
            if not os.path.isfile(res):
                problems.append(f"{pid} {day} {arm}: not simulated yet -> simulate "
                                f"{os.path.relpath(new_json, globals.ROOT)} and keep its "
                                f"settings and state_results.xlsx in {os.path.relpath(kept, globals.ROOT)}")
                continue
            # A result without the settings it was simulated with cannot be checked.
            if not os.path.isfile(used_json):
                problems.append(f"{pid} {day} {arm}: result kept without its simulation_settings.json; "
                                f"add the settings it was simulated with")
                continue
            # Compared as JSON: same content, whatever the spacing or the key order.
            if load(used_json) != load(new_json):
                problems.append(f"{pid} {day} {arm}: simulated with other settings -> simulate again")
                continue
            # Settings match: copy the result into the working copy.
            shutil.copy2(res, work)
            ok += 1

for p in problems:
    print(p)
print(f"\n{ok} scenario results in place; {len(problems)} not ready.")
