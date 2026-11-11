"""
0.InterpolationBGHourlyDataZenodo.py
Reference curve (InVivo): median glucose level of the participant over the
day, used as the reference for the simulator input (G.CurveCheck.py,
S.CurveAgreement.py). It does not enter the basal recommendation.

Created: 19 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Median glucose across analysis days, minute by minute, after filling
       gaps of up to 5 minutes in each day.
    2. Median of each hour (labelled at the start of the hour).
    3. Hourly values below 3 or above 30 mmol/L are taken as missing and
       interpolated in time; the result is clipped to 3-12 mmol/L.
    4. Cubic polynomial interpolation between the 25 hourly anchors (the
       00:00 value is repeated at 24:00) to a 1-minute curve.

Inputs
    globals.id, globals.fileToSave
    processed/<id>/BGwNMLeftJoined<id>.csv   (5.MergeBGCleanZenodo.py)

Output
    processed/<id>/BGwNMLeftJoinedHourlyInterpolated<id>.csv   Key, MedianBGValue (mmol/L)

Notes
    - Only the BGValue* columns enter the median. The joined file also
      carries its saved index ("Unnamed: 0"); before this was fixed, the
      index entered the median, and hours with 0-1 days of data were
      discarded and filled by interpolation.
    - Hours with a single day of data reflect that day only.
    - The cubic interpolation can overshoot between anchors (values above
      the 12 mmol/L clip, or outside the range of the anchors).
    - The clip to 3-12 mmol/L flattens hours above 12 into plateaus.
"""

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


path2 = globals.fileToSave
fileToRead = "BGwNMLeftJoined" + str(id)
fileToSave = "BGwNMLeftJoinedHourlyInterpolated" + str(id)
warnings.simplefilter(action='ignore', category=FutureWarning)

# Load data
data = pd.read_csv(f"{path2}{fileToRead}.csv")
# Keep only the time key and the day columns (BGValue*). The CSV also carries the
# saved row index ('Unnamed: 0'), which would otherwise enter the across-day median
# as if it were one more day: in hours with 0-1 days of data it pushed the hourly
# median above 30, so the hour was discarded and filled by interpolation.
data = data[["Key"] + [c for c in data.columns if c.startswith("BGValue")]]
data = data.interpolate(limit=5, limit_direction='both')
data["MedianBGValue"] = data.median(axis='columns', numeric_only=True)

# Convert Key to datetime (with dummy date for proper resampling)
data['Key'] = pd.to_datetime(data['Key'], format='%H:%M:%S')
data['Key'] = data['Key'].apply(lambda dt: dt.replace(year=2023, month=1, day=1))
data.set_index('Key', inplace=True)

# Get hourly median values (each labelled at the start of its hour)
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
# The last row (midnight of the next day) closes the day as 24:00:00; the first
# row stays 00:00:00, so each label appears once.
interp_df.loc[interp_df.index[-1], 'Key'] = '24:00:00'

# Save
interp_df.to_csv(f"{path2}{fileToSave}.csv", index=False)
