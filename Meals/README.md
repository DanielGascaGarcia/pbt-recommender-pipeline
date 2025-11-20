Meal Scenarios

**Purpose:**  
Generate meal and bolus event patterns for py-mgipsim simulations, allowing you to compare a baseline run (before) with a perturbed run (after) that includes carbohydrate disturbances.

**Script:**  
`0.GeneratorBolusExamplesPy-mgipsimForEGPMealTest.py`

**What it does:**  
- Renames the latest `Simulation*` folder to `Simulation_{id}`  
- Loads the patient’s ICR from `{path}/{id}.json`  
- Updates the simulation duration (`end_time`)  
- Injects meal events (magnitudes, timings, duration)  
- Computes and injects corresponding bolus insulin doses based on ICR  
- Saves all changes back to `simulation_settings.json`

**Usage:**  
1. Run the simulator once with the original folder → *baseline (“before”) scenario*  
2. Run this script to modify meals/boluses → *perturbed (“after”) scenario*  
3. Compare the two runs for effect testing
