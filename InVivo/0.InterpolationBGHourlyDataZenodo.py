
#Code: 0.InterpolationBGHourlyDataZenodo.py 
#Description: interpolate values.
#Created 19th April 2023
#Author: mbaxdg6

import warnings
import datetime 
import pandas as pd
import os
from datetime import datetime,timedelta
import datetime 
from matplotlib import pyplot as plt
import numpy as np
import csv
import globals
from scipy.stats import zscore
id=globals.id;

# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#

path2 = globals.fileToSave
fileToRead = "BGwNMLeftJoined" + str(id)
fileToSave = "BGwNMLeftJoinedHourlyInterpolated" + str(id)
warnings.simplefilter(action='ignore', category=FutureWarning)

# Load data
data = pd.read_csv(f"{path2}{fileToRead}.csv")
data = data.interpolate(limit=5, limit_direction='both')
data["MedianBGValue"] = data.median(axis='columns', numeric_only=True)

# Convert Key to datetime (with dummy date for proper resampling)
data['Key'] = pd.to_datetime(data['Key'], format='%H:%M:%S')
data['Key'] = data['Key'].apply(lambda dt: dt.replace(year=2023, month=1, day=1))
data.set_index('Key', inplace=True)

# Get hourly median values
hourly_median = data['MedianBGValue'].resample('H').median()


# Get hourly median values
hourly_median = data['MedianBGValue'].resample('H').median()

# Replace clearly wrong values with 0 (e.g., values < 3 or > 30)
hourly_median_clean = hourly_median.copy()
hourly_median_clean[(hourly_median_clean < 3) | (hourly_median_clean > 30)] = 0


# Step 3: Temporarily replace 0s with NaN for interpolation
hourly_median_interp = hourly_median_clean.replace(0, np.nan)

# Step 4: Interpolate over NaNs using time-based interpolation
hourly_median_interp = hourly_median_interp.interpolate(method='time', limit_direction='both')

# Step 5 (Optional): Clip final result to medically safe range
hourly_median_interp = hourly_median_interp.clip(lower=3, upper=12)

# Print result to verify
hourly_median=hourly_median_interp



# Manually set 24:00:00 = 00:00:00
value_0000 = hourly_median.loc[hourly_median.index.time == pd.to_datetime('00:00:00').time()].iloc[0]
hourly_median.loc[pd.to_datetime('2023-01-02 00:00:00')] = value_0000

# Create full 1-minute time index from 00:00 to 24:00
full_index = pd.date_range(start='2023-01-01 00:00:00', end='2023-01-02 00:00:00', freq='T')
interp_df = pd.DataFrame(index=full_index)
interp_df['MedianBGValue'] = hourly_median.reindex(full_index)
interp_df['MedianBGValue'] = interp_df['MedianBGValue'].interpolate(method='polynomial', order=3, limit_direction='both')



# Format output
interp_df = interp_df.reset_index()
interp_df.columns = ['Key', 'MedianBGValue']
interp_df['Key'] = interp_df['Key'].dt.strftime('%H:%M:%S')
interp_df.loc[interp_df['Key'] == '00:00:00', 'Key'] = '24:00:00'

# Save
interp_df.to_csv(f"{path2}{fileToSave}.csv", index=False)