#Code: 17.ScriptforTestSimglucose.py
#Description: Creating pivot table for merge.
#Created 5th July 2023
#Author: mbaxdg6

import subprocess
import globals


scripts = [
    "0.GeneratorExamplesPy-mgipsimForEGPtest.py",
    "3.PivotGeneratorZenodo.py",
    "5.MergeBGCompletePy-mgipsimTest.py",        
    "5.FillGapsBasalTest.py",
    "6.SimulationBasalAutomatedTest.py",
    "6.SplitHoursTest.py",
    "7.InterpolationBGHourlyTest.py",
    "8.RelativeChangeTest.py",
    "9.BoxplotTest.py",
    "10.PivotGeneratormediansTest.py",
    "12.MergeRChBasalNoActTest.py",
    "13.InterpolationRChTest.py",
    "14.SimulationBolusCHOPy-mgipsimTest.py",
    "15.GeneratorFileToPy-mgipsimTest.py",
    # "0.GeneratorBolusExamplesPy-mgipsimForEGPMealTest.py",
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

