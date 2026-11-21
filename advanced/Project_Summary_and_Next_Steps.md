# Project Summary and Next Steps

## Project focus

**Discrete Delta hedging: transaction costs, rebalancing frequency and volatility differences.**

This Python project builds a self-financing replicating portfolio for a European call. It investigates how to select a rebalancing frequency when trading is costly and how a difference between pricing volatility and actual volatility affects the P&L of a short option with a dynamic hedge.

Repository: [Mar-ne/delta-hedging](https://github.com/Mar-ne/delta-hedging). The A/B extension and its run outputs are in `advanced/`.

## Work completed

### 1. Baseline replication model

- Generate random GBM paths using the exact update between simulation grid points.
- Calculate the initial Black-Scholes call price and Delta.
- Build a stock-and-cash portfolio, including borrowing, lending and interest accrual.
- Rebalance to the new Delta and compare terminal portfolio value with the option payoff.
- Investigate the roles of physical drift, the risk-free rate and cost-free rebalancing frequency.

### 2. A: Transaction costs and rebalancing frequency

Actual and pricing volatility are both 20%. A proportional cost of 0.1% is charged on stock traded at inception, on rebalancing dates and at terminal liquidation. The simulation uses ten steps per day and compares intervals of 0.1, 0.5, 1, 2, 3, 5, 10, 15, 30 and 60 days.

Minimizing net replication RMSE selects **2 days** in both batches of 1,000 paths:

| Seed | 1-day RMSE | 2-day RMSE | 3-day RMSE |
|---|---:|---:|---:|
| 42 | 0.8532 | **0.7620** | 0.8040 |
| 43 | 0.8527 | **0.7825** | 0.7938 |

More frequent rebalancing can reduce discrete replication risk but increases trading costs. The result identifies a trade-off within the chosen grid and parameters, not a universal recommendation to hedge every two days.

### 3. B: Volatility differences and hedged P&L

Separate the volatility used to generate stock paths from the volatility used to price the call and calculate Delta. With pricing volatility fixed at 20%, zero costs and a 0.1-day rebalancing interval:

| Actual volatility | Mean terminal hedged P&L |
|---|---:|
| 15% | +1.8251 |
| 20% | -0.0058 |
| 25% | -1.9162 |

Under these model assumptions, selling the call and hedging it produces positive average P&L when actual volatility is lower than pricing volatility, and negative average P&L when it is higher. Gamma, the stock price and the variance difference explain the path-dependent contribution. The 20% pricing volatility is an assumed model input; it has not been inferred from real option quotes.

### 4. Add costs, select a policy and validate it

With actual volatility 15%, pricing volatility 20% and a 0.1% fee, select the interval with the highest mean net P&L among candidates whose sample loss rate is no greater than 1%. This selects **3 days**.

Fix that policy and evaluate it on 1,000 new paths using seed 44:

| Metric | Selection: seed 43 | Validation: seed 44 |
|---|---:|---:|
| Mean net P&L | 1.3960 | **1.4224** |
| SD | 0.7758 | 0.7532 |
| Sample loss rate | 0.3% | **0.2%** |
| 5th percentile | 0.3115 | 0.3172 |

A's 2-day choice and B's 3-day choice use different objectives and parameters. The validation loss rate is a sample statistic, not a guarantee that the population loss probability is below 1%. P&L is per option on one share, not an equity return.

### 5. Reproducible outputs

The standalone program generated 61 full-precision summaries, 61,000 pathwise P&L records and figures, and saved parameters and random seeds. Strategies reuse price paths, so the record count is not a count of independent stock paths.

Mean, SD, RMSE, loss rate, 5th percentile and average costs were independently recomputed from the exported pathwise data. Gross P&L, net P&L and accumulated costs were also reconciled. Code, notebooks, reports and complete run outputs are included in the project.

## Skills demonstrated

Translate GBM, Black-Scholes, Delta and Gamma into numerical experiments; account for cash flows, financing and costs; distinguish replication and profitability objectives; make controlled comparisons using common paths; validate a selected policy on an independent sample; and document reproducible code, data and figures.

## Current limitations

These are model-based experiments under constant-volatility GBM. They do not use real quotes, volatility forecasts, jumps, stochastic volatility, dividends or actual trading calendars. Future actual volatility is unknown in practice; the assumed 15% is not information known to a real trader in advance. With 1,000 paths per configuration, means, quantiles and loss rates remain subject to sampling uncertainty. Uncertainty in differences between policies has not yet been quantified.

## Proposed research directions

| Order | Direction | Question | Experiment |
|---|---|---|---|
| 1 | Robustness and uncertainty | Do the 2-day and 3-day choices depend on the current parameters or sample? | Vary costs, volatility, maturity and strike; increase paths in batches; use a paired bootstrap of same-path strategy differences to estimate confidence intervals. |
| 2 | Delta-threshold and no-trade-band hedging | Should trading depend on the deviation from the desired stock position? | Compare fixed-time and Delta-threshold policies; record fees, trade counts, turnover and replication risk. |
| 3 | Volatility uncertainty and model mismatch | Does profitability persist when future volatility is unknown or changes over time? | Randomize actual volatility across paths, or introduce stochastic volatility or jumps; restrict the hedger to information available at each time. |
| 4 | Market-data validation | Can a useful volatility difference be identified using real information? | Use historical stock and option quotes, distinguish implied, historical and future realized volatility, validate chronologically out of sample and include bid-ask spreads. |

Historical volatility is not itself a forecast of future volatility; implied volatility is inferred from option prices through a pricing model. The market-data extension must distinguish these concepts. [OIC technical information](https://www.optionseducation.org/referencelibrary/faq/technical-information)

## Recommended next experiment

**Can Delta-threshold hedging improve the trade-off between trading costs and replication risk?**

Start with A's matched-volatility setting: actual and pricing volatility 20%, a 0.1% fee, and a check every 0.1 day. Let q be current stock holdings, Delta the new target, and h the allowed deviation. Trade only when:

$$|\Delta_t-q_t|>h.$$

In the first version, trade back to the new Delta after crossing the threshold. A later version can compare trading only to the band boundary. The threshold h is measured in shares per option, not percentage returns.

1. On identical paths, compare fixed 1-, 2- and 3-day rebalancing with h = 0.01, 0.02, 0.05 and 0.10.
2. Retain A's RMSE objective and also record average costs, trade counts and turnover. Plot the cost-RMSE relationship.
3. Select a threshold on a new sample, for example seed 202, then fix the policy and validate it on another new sample, for example seed 303.
4. Vary transaction costs to assess robustness before applying the policy to B's volatility-difference scenarios.

No-trade bands are an established topic in transaction-cost hedging research. Whalley and Wilmott study bands around the Black-Scholes Delta and how the appropriate post-trade position relates to the boundary under their small-cost, proportional-cost and utility-optimization assumptions. The constant threshold proposed here is a simple experimental policy, not a claim to implement their theoretical optimum. [Original paper](https://users.ox.ac.uk/~ofrcinfo/file_links/mf_papers/1999mf09.pdf)

This extension builds directly on the existing simulator while introducing a state-dependent trading rule.
