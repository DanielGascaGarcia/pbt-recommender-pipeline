"""
S.PowerAnalysisTest.py
Metrics: the test planned in the power analysis, applied to the results:
one-tailed paired t test on the SD of the simulated glucose before and after
the recommended basal, one test per evaluation day.

Created: October 2026
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Power analysis: one-tailed paired t test, alpha = 0.05, power = 0.80,
       dz = 0.70. Reports the sample size it requires and the power reached
       with the participants included (noncentral t, as G*Power).
    2. Per day: n; mean and SD of the SD before and after (mmol/L); mean
       reduction with its 95% CI; t, df and one-tailed P (H1: SD before > SD
       after); observed dz; participants with a lower SD after; Shapiro-Wilk
       P on the reductions; Wilcoxon signed-rank one-tailed P; whether P stays
       below alpha after Bonferroni adjustment for the two days.

Inputs
    globals.path4
    results/metrics/tables/metrics_by_participant.csv   (S.CollectScenarioResults.py)

Output
    results/metrics/tables/PowerAnalysisTest.csv

Outputs (also)
    results/metrics/tables/PowerTestDescriptives.csv and
    PowerTestDescriptives_table.tex: mean (SD), median (Q1-Q3) and range of
    the SD before, the SD after and the reduction, per day, for the data
    appendix of the thesis.

Notes
    - With fewer than MIN_N (3) participants, as in the demo (n = 1), the
      test cannot be computed: only the SDs before and after are reported.
    - dz = 0.70 requires n = 15; with n = 17 the power is 0.868, and the
      smallest effect detectable at 80% power (sensitivity analysis) is
      dz = 0.63.
    - The observed dz is large partly by design: before and after share the
      same virtual subject, meals and boluses and have no noise, so the
      reductions vary little between participants.
    - The Wilcoxon test is a check that does not assume normality; the t
      test is the planned one.
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

import globals

ALPHA, POWER, DZ = 0.05, 0.80, 0.70
MIN_N = 3          # fewer participants (e.g. the demo, n = 1): the test is not run
TABLES = globals.path4


def power_one_tailed(n, dz, alpha=ALPHA):
    """Power of a one-tailed paired t test (noncentral t), as in G*Power."""
    df = n - 1
    tcrit = stats.t.ppf(1 - alpha, df)
    return 1 - stats.nct.cdf(tcrit, df, dz * np.sqrt(n))


def required_n(dz, alpha=ALPHA, power=POWER):
    n = 2
    while power_one_tailed(n, dz, alpha) < power:
        n += 1
    return n


m = pd.read_csv(os.path.join(TABLES, "metrics_by_participant.csv"), dtype={"ID": str})
days = sorted(m["Day"].unique())
rows = []
for day in days:
    d = m[m["Day"] == day]
    before, after = d["STD_1_mmolL"].to_numpy(float), d["STD_2_mmolL"].to_numpy(float)
    red = before - after
    n = len(red)
    if n < MIN_N:
        # The test needs several participants (the demo has one): report the SDs only.
        rows.append({"Day": day, "n": n,
                     "SD_before_mean": before.mean(), "SD_after_mean": after.mean(),
                     "reduction_mean": red.mean(),
                     "participants_lower_SD": int((red > 0).sum())})
        continue
    t = stats.ttest_rel(before, after, alternative="greater")
    se = red.std(ddof=1) / np.sqrt(n)
    lo, hi = stats.t.interval(0.95, n - 1, loc=red.mean(), scale=se)
    rows.append({
        "Day": day, "n": n,
        "SD_before_mean": before.mean(), "SD_before_sd": before.std(ddof=1),
        "SD_after_mean": after.mean(), "SD_after_sd": after.std(ddof=1),
        "reduction_mean": red.mean(), "reduction_sd": red.std(ddof=1),
        "reduction_CI95_low": lo, "reduction_CI95_high": hi,
        "t": t.statistic, "df": n - 1, "p_one_tailed": t.pvalue,
        "dz_observed": red.mean() / red.std(ddof=1),
        "participants_lower_SD": int((red > 0).sum()),
        "shapiro_p": stats.shapiro(red).pvalue if n >= 3 else np.nan,
        "wilcoxon_p_one_tailed": stats.wilcoxon(before, after, alternative="greater").pvalue,
        "significant_bonferroni": bool(t.pvalue < ALPHA / len(days)),
    })

r = pd.DataFrame(rows)
r.to_csv(os.path.join(TABLES, "PowerAnalysisTest.csv"), index=False)

# -----------------------------------------------------------#
# Descriptive statistics of the variables entering the test,
# for the data appendix of the thesis (same layout as the
# Bland-Altman descriptives of the chapter of paper 2)
# -----------------------------------------------------------#
drows = []
for day in days:
    d = m[m["Day"] == day]
    for name, v in [("SD before", d["STD_1_mmolL"]), ("SD after", d["STD_2_mmolL"]),
                    ("reduction (before - after)", d["STD_1_mmolL"] - d["STD_2_mmolL"])]:
        v = v.dropna()
        drows.append({"Day": day, "Variable": name, "n": len(v), "mean": v.mean(),
                      "sd": v.std(ddof=1) if len(v) > 1 else float("nan"),
                      "median": v.median(), "q1": v.quantile(0.25), "q3": v.quantile(0.75),
                      "min": v.min(), "max": v.max()})
desc = pd.DataFrame(drows)
desc.to_csv(os.path.join(TABLES, "PowerTestDescriptives.csv"), index=False)


def num(x):
    return f"{x:.2f}".replace("-", "$-$")


tex = [r"""% Data appendix of the chapter of paper 3: variables of the planned test.
% Written by metrics/S.PowerAnalysisTest.py.
\begin{table}[htbp]
\centering
\small
\caption{Variables entering the planned paired test, Chapter~\ref{Chap:Paper3} (n=""" + str(int(desc["n"].max()) if len(desc) else 0) + r"""; standard deviation of simulated glucose, mmol/L). Reduction = before $-$ after (positive = lower variability after the adjustment). SD: standard deviation; Q1--Q3: first to third quartile.}
% Source: PowerTestDescriptives.csv
\label{tab:app_powertest_ch6}
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Variable} & \textbf{Mean (SD)} & \textbf{Median (Q1--Q3)} & \textbf{Range} \\
\hline"""]
for _, x in desc.iterrows():
    sd = f"{x['sd']:.2f}" if x["sd"] == x["sd"] else "--"
    label = f"{x.Day[:3]} {x.Day[3:]}: {x.Variable}".replace("before - after", "before $-$ after")
    tex.append(f"{label} & {num(x['mean'])} ({sd}) & {num(x['median'])} ({num(x.q1)} to {num(x.q3)}) & "
               f"{num(x['min'])} to {num(x['max'])} \\\\")
tex.append(r"""\hline
\end{tabular}
\end{table}
""")
with open(os.path.join(TABLES, "PowerTestDescriptives_table.tex"), "w", encoding="utf-8") as f:
    f.write("\n".join(tex))
print("Saved:", os.path.join(TABLES, "PowerTestDescriptives.csv"))
print("Saved:", os.path.join(TABLES, "PowerTestDescriptives_table.tex"))

n_req = required_n(DZ)
n_used = int(r["n"].max()) if len(r) else 0
print(f"Power analysis: one-tailed paired t test, alpha={ALPHA}, power={POWER}, dz={DZ}")
if n_used >= MIN_N:
    print(f"  required n = {n_req}; with n = {n_used}, power = {power_one_tailed(n_used, DZ):.3f}\n")
else:
    print(f"  required n = {n_req}; only {n_used} participant(s) here (demo?), so the test is not run.\n")
for _, x in r.iterrows():
    if int(x.n) < MIN_N:
        print(f"{x.Day}: SD {x.SD_before_mean:.2f} -> {x.SD_after_mean:.2f} mmol/L; "
              f"reduction {x.reduction_mean:.2f}; lower SD in {int(x.participants_lower_SD)}/{int(x.n)} "
              f"(test needs at least {MIN_N} participants)")
        continue
    print(f"{x.Day}: SD {x.SD_before_mean:.2f} +/- {x.SD_before_sd:.2f} -> {x.SD_after_mean:.2f} +/- {x.SD_after_sd:.2f} mmol/L; "
          f"reduction {x.reduction_mean:.2f} (95% CI {x.reduction_CI95_low:.2f} to {x.reduction_CI95_high:.2f}); "
          f"t({int(x.df)}) = {x.t:.2f}, one-tailed P = {x.p_one_tailed:.2g}; dz = {x.dz_observed:.2f}; "
          f"lower SD in {int(x.participants_lower_SD)}/{int(x.n)}; Shapiro P = {x.shapiro_p:.2f}; "
          f"Wilcoxon P = {x.wilcoxon_p_one_tailed:.2g}; Bonferroni ({len(days)} days): "
          f"{'significant' if x.significant_bonferroni else 'not significant'}")
print(f"\nSaved: {os.path.join(TABLES, 'PowerAnalysisTest.csv')}")
