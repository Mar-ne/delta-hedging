# Optimal Hedging and Volatility Trading

This directory contains the complete data and figures from the executed A/B simulation. All results were generated from random GBM paths, without reading transcribed terminal results.

- [Hedging_AB.ipynb](Hedging_AB.ipynb): result tables, figures, explanations and optional rerun code.
- [Report.md](Report.md): the full report, covering all 61 configurations and independent validation.
- [experiments_ab.py](experiments_ab.py): a standalone program that generates data and plots from scratch.
- [Project_Summary_and_Next_Steps.md](Project_Summary_and_Next_Steps.md): project overview and proposed extensions.
- [results/rerun/fresh_summary.csv](results/rerun/fresh_summary.csv): 61 full-precision summary rows.
- [results/rerun/fresh_path_pnl.csv](results/rerun/fresh_path_pnl.csv): 61,000 pathwise net/gross P&L and cost records; strategies reuse paths.
- [results/rerun/fresh_metadata.json](results/rerun/fresh_metadata.json): run parameters, seeds and NumPy version.
- [results/audit.json](results/audit.json): independent checks of the pathwise summaries and file hashes.

## Run the experiments

```bash
python -m pip install -r requirements.txt
python experiments_ab.py
```

Rerunning updates files with the same names in this directory. A selects a 2-day interval by minimum candidate RMSE. B selects 3 days under its sample loss constraint; the independent validation mean net P&L is 1.4224 and the sample loss rate is 0.2%. See the report for assumptions and limitations.
