# Paper 4 — Recommending Optimised Basal Insulin Rates (PBT)

This deposit accompanies the manuscript for **Experiment 3**, where the Personalised Basal Tuner (PBT) generates **24-hour basal adjustments** from real-world data and evaluates them **in silico** with Py-mgipsim. Across two simulated days per participant, the study shows **composite stability improvements** for almost all cases (**I > 1 in 16/17 participants** on both days), with **one participant with I < 1**. Safety is preserved (low bias; ISO ±15% style checks), and total basal insulin changes remain small.

## High-level flow

1. **In-vivo analysis (real data)**
   - Parse CGM/pump logs, exclude post-meal windows, and build composite-day profiles.
   - Compute hourly **relative change** and identify residual deviations (deficit/excess).

2. **Basal recommendation**
   - Convert residual deviations into **conservative 24-h basal adjustments** using an insulin-on-board (IOB) kernel (no blanket dose escalation).

3. **In-silico evaluation**
   - Map each participant to a comparable virtual subject.
   - Run **Py-mgipsim** with meals enabled; evaluate the adjusted profile over **2 days** with fixed seeds.

4. **Metrics & figures**
   - Variability (STD), excursion change (ΔMAGE-like), **Composite Stability Index (I)**, TIR, bias, and Δ basal insulin.
   - Boxplots by hour; ISO-style bias ±15% view; per-subject tables and day-1/day-2 reproducibility.

> See each subfolder for exact script order and commands that reproduce manuscript figures and tables.
