# Delta Hedging: Replication, Optimal Rebalancing and Volatility Trading

A Python mathematical finance project examining discrete replication errors, trading costs and volatility differences using simulated GBM paths and self-financing stock-and-cash portfolios.

## Start here

| Part | Notebook | Scope |
|---|---|---|
| Baseline | [Delta_Hedging.ipynb](Delta_Hedging.ipynb) | Cost-free replication, rebalancing frequency and physical drift |
| A/B extension | [advanced/Hedging_AB.ipynb](advanced/Hedging_AB.ipynb) | Cost-aware rebalancing, volatility trading and independent validation |

Read the [baseline report](Report.md), the [A/B report](advanced/Report.md), or the [project summary and next steps](advanced/Project_Summary_and_Next_Steps.md). The standalone A/B implementation is [experiments_ab.py](advanced/experiments_ab.py).

## A: How often should the hedge be rebalanced?

The initial stock price and strike are 100, maturity is one year, the risk-free rate is 5%, and physical drift is 10%. Actual and pricing volatility are both 20%. Stock trades incur a 0.1% proportional cost, including initial positioning, rebalancing and terminal liquidation. Each batch contains 1,000 paths on a 3,650-step grid.

Candidate intervals are 0.1, 0.5, 1, 2, 3, 5, 10, 15, 30 and 60 days. Minimizing net replication RMSE selects **2 days** in both batches:

| Seed | 1-day RMSE | 2-day RMSE | 3-day RMSE |
|---|---:|---:|---:|
| 42 | 0.8532 | **0.7620** | 0.8040 |
| 43 | 0.8527 | **0.7825** | 0.7938 |

![A: replication RMSE, costs and P&L variability](advanced/results/rerun/A_optimal_hedging.png)

## B: Where does hedged P&L come from?

Hold pricing volatility at 20%, remove transaction costs, and rebalance every 0.1 day:

| Actual volatility | Mean terminal hedged P&L |
|---|---:|
| 15% | +1.8251 |
| 20% | -0.0058 |
| 25% | -1.9162 |

Selling the call and hedging it generates positive average gross P&L when actual volatility is lower than pricing volatility, and negative average P&L when actual volatility is higher. The report relates this to the Gamma-weighted variance difference.

With actual volatility 15%, pricing volatility 20% and a 0.1% fee, maximizing mean net P&L subject to a sample loss rate of at most 1% selects **3 days**. The policy is then fixed and evaluated on independent seed 44:

| Sample | Mean net P&L | SD | Sample loss rate | 5th percentile |
|---|---:|---:|---:|---:|
| Selection: seed 43 | 1.3960 | 0.7758 | 0.3% | 0.3115 |
| Validation: seed 44 | **1.4224** | 0.7532 | **0.2%** | 0.3172 |

![B: rebalancing frequency, net P&L and loss rates](advanced/results/rerun/B_volatility_trading.png)

A and B use different parameters and objectives. Their selected intervals are not interchangeable. All P&L amounts are per option on one share, not returns on equity.

## Data and reproducibility

The extension generates its data from simulated stock price paths.

- [61 full-precision summaries](advanced/results/rerun/fresh_summary.csv).
- [61,000 pathwise P&L records](advanced/results/rerun/fresh_path_pnl.csv). Strategies reuse price paths; this is not a count of independent stock paths.
- [Parameters, seeds and NumPy version](advanced/results/rerun/fresh_metadata.json).
- [Independent numerical checks and hashes](advanced/results/audit.json).

```bash
cd advanced
python -m pip install -r requirements.txt
python experiments_ab.py
```

The script runs all A/B experiments and writes CSV and PNG files to `advanced/results/rerun/`. Alternatively, run the optional code cells in the A/B notebook. The baseline can be run with `python delta_hedging_clean.py`; its output goes to the root `results/` directory. `delta_hedging.py` is the original learning implementation.

## Limitations

Constant-volatility GBM, no dividends, fractional shares and idealized financing are model assumptions. No real market quotes are used, and future actual volatility is unknown in practice. The selected intervals apply to the stated parameters, candidate grid and finite samples. A sample loss rate below 1% does not guarantee a population loss probability below 1% or profitable real-market trading.
