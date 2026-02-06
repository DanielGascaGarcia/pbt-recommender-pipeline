#Code: 17.ScriptforTestZenodo.py
#Description: Creating pivot table for merge.
#Created 5th July 2023
#Author: mbaxdg6

import subprocess
import globals


scripts = [
    "0.GeneratorExamplesZenodo.py",
    "3.PivotGeneratorZenodo.py",
    "3.PivotGeneratorBasalZenodo.PY",
    "4.MealBolusDetectionZenodo.py",
    "4.MergeBasalZenodo.py",
    "5.MergeBGCleanZenodo.py",        
    "5.FillGapsBasalZenodo.py",
    "6.SimulationBasalAutomatedZenodo.py",
    "6.SplitHoursZenodo.py",
    "7.InterpolationBGHourlyZenodo.py",
    "8.RelativeChangeZenodo.py",
    "9.BoxplotZenodo.py",
    "10.PivotGeneratorMediansZenodo.py",
    "12.MergeRChBasalNoActZenodo.py",
    "13.InterpolationRChZenodo.py",
    "14.SimulationBolusCHOPy-mgipsimZenodo.py",
    "0.InterpolationBGHourlyDataZenodo.py",
]

for script in scripts:
    try:
        print(f" Current id is: "+ str(globals.id))
        print(f"Running {script}...")
        subprocess.run(["python", script], check=True)
        print(f"{script} completed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running {script}: clear{e}")
        break

