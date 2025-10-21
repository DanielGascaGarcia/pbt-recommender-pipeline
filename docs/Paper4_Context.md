# Paper 4 Context — Recommending Optimised Basal Insulin Rates (PBT)

This deposit accompanies the manuscript describing Experiment 3, where the PBT algorithm
recommends **redistributed** basal insulin profiles and evaluates them **in silico**. The study
reports composite stability improvements (I > 1 for all 17 participants; strong‑response I > 1.8
in ≈94% of cases) with preserved safety (bias near zero, ISO ±15% compliance) and minimal change
in total basal insulin. The pipeline here captures that flow and the artefacts used to derive figures
and metrics for the manuscript.

## High‑level flow

1. **In vivo analysis** (real data)
   - Parse CGM/pump logs, remove 6‑h post‑meal windows, build composite‑day profiles.
   - Compute hourly **relative change**; estimate basal deficits/excess; summarise medians/outliers.

2. **Basal recommendation**
   - Flatten residual composite deviations using an insulin‑on‑board (IOB) kernel to derive a
     recommendation-based **recommendations** over 24 h (not dose escalation).

3. **In silico evaluation**
   - Map each real participant to the most comparable UVA/Padova virtual subject.
   - Run Py‑mgipsim with meals; test the adjusted basal over 2 days; keep seeds fixed.

4. **Metrics and visualisation**
   - Boxplots by hour → ISO style bias ±15% → composite stability **I**, ΔMAGE, STD, TIR, bias, Δinsulin.

See each subfolder for exact commands and script order.
