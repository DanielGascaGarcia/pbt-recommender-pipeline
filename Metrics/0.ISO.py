#Code: 0.ISO.py
#Description: Box plots of BG per hour.
#Created 11th Oct 2025
#Author: mbaxdg6
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import os
import globals



folder_path = globals.folder_path;
file_name = "hourly_mean_and_std.xlsx"
file_path = os.path.join(folder_path, file_name)

# 1) Load data
df = pd.read_excel(file_path)


rename_map = {
    'BG_1_mean': 'BG_Before_mean',
    'BG_2_mean': 'BG_After_mean',
    'BG_1_std':  'BG_Before_std',
    'BG_2_std':  'BG_After_std'
}
df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})


if 'hour' not in df.columns:
    if 'Key' in df.columns:
        df['hour'] = pd.to_datetime(df['Key'], format='%H:%M:%S', errors='coerce').dt.hour
        if df['hour'].isna().any():  # fallback to generic parsing if needed
            df['hour'] = pd.to_datetime(df['Key'], errors='coerce').dt.hour
        if df['hour'].isna().any():
            raise ValueError("Could not derive 'hour' from 'Key'.")
    else:
        raise KeyError("Missing 'hour' column and no 'Key' column to derive it from.")


denom = df['BG_Before_mean'].replace(0, pd.NA)
df['relative_bias'] = ((df['BG_After_mean'] - df['BG_Before_mean']) / denom) * 100
df['relative_bias'] = df['relative_bias'].fillna(0)  # avoid inf/NaN when Before==0
df['within_10_percent'] = df['relative_bias'].abs() <= 15
df['std_improved'] = df['BG_After_std'] < df['BG_Before_std']
bias_mean = df['relative_bias'].mean()

before_std_mmol = df['BG_Before_std']
after_std_mmol  = df['BG_After_std']

# -----------------------------------------------------------#
#                      Plot
# -----------------------------------------------------------#
fig, axes = plt.subplots(1, 3, figsize=(18, 5))


axes[0].bar(df['hour'], df['relative_bias'], color='skyblue')
axes[0].axhline(15, color='red', linestyle='--', label='±15% threshold')
axes[0].axhline(-15, color='red', linestyle='--')
axes[0].set_title('Relative Bias (After vs Before)')
axes[0].set_xlabel('Hour')
axes[0].set_ylabel('Relative Bias (%)')
axes[0].set_xticks(range(0, 24, 1))
axes[0].grid(True, axis='y')
axes[0].legend()

axes[1].plot(df['hour'], before_std_mmol, marker='o', label='Before SD', color='orange')
axes[1].plot(df['hour'], after_std_mmol,  marker='o', label='After SD',  color='green')
axes[1].set_title('Standard Deviation by Hour')
axes[1].set_xlabel('Hour')
axes[1].set_ylabel('SD Deviation (mmol/L)')
axes[1].set_xticks(range(0, 24, 1))
axes[1].legend()
axes[1].grid(True)


ax2 = axes[1].twinx()
y1min, y1max = axes[1].get_ylim()
ax2.set_ylim(y1min * 18, y1max * 18)  # same scale converted
ax2.set_ylabel('Std Deviation (mg/dL)')

y1ticks = axes[1].get_yticks()
ax2.set_yticks(y1ticks * 18)
ax2.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))


within_10 = df['within_10_percent'].sum()
std_better = df['std_improved'].sum()
total = len(df)

labels = ['Within ±15%', 'Lower Std After']
values = [within_10 / total * 100, std_better / total * 100]
bars = axes[2].bar(labels, values, color=['cornflowerblue', 'mediumseagreen'])

# Add percentage labels on bars
for bar in bars:
    height = bar.get_height()
    axes[2].text(bar.get_x() + bar.get_width() / 2, height + 2, f'{height:.1f}%',
                 ha='center', fontsize=10)

axes[2].set_ylim(0, 110)
axes[2].set_title('Compliance Summary (%)')
axes[2].set_ylabel('% of Hours')
axes[2].grid(axis='y')


axes[2].text(0.5, 95, f'Mean Bias: {bias_mean:.2f}%',
             ha='center', fontsize=10, bbox=dict(facecolor='white', edgecolor='black'))


plt.suptitle('Evaluation of Basal Insulin Adjustment (Before vs After)', fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()
