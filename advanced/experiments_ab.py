# -*- coding: utf-8 -*-
"""Run all A/B experiments from simulated stock price paths.

This module uses the same GBM, Delta and transaction-cost rules as the
learning implementation. It updates prices in time order, processes 1,000
paths in parallel and compounds cash over each interval between trades.
"""
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist
import csv
import json

import numpy as np
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Model:
    P: float = 100.0
    K: float = 100.0
    T: float = 1.0
    r: float = 0.05
    drift: float = 0.10
    sigma_hedge: float = 0.20
    steps_per_day: int = 10
    paths: int = 1000


INTERVALS = [0.1, 0.5, 1, 2, 3, 5, 10, 15, 30, 60]
NORMAL = NormalDist()


def initial_price_delta(model):
    d1 = (np.log(model.P / model.K)
          + (model.r + 0.5 * model.sigma_hedge**2) * model.T
          ) / (model.sigma_hedge * np.sqrt(model.T))
    d2 = d1 - model.sigma_hedge * np.sqrt(model.T)
    price = (model.P * NORMAL.cdf(d1)
             - model.K * np.exp(-model.r * model.T) * NORMAL.cdf(d2))
    return float(price), NORMAL.cdf(d1)


def generate_paths(model, sigma_actual, seed):
    if sigma_actual <= 0 or model.sigma_hedge <= 0:
        raise ValueError('Volatilities must be positive.')
    exact_steps = 365 * model.T * model.steps_per_day
    steps = round(exact_steps)
    if not np.isclose(exact_steps, steps) or steps < 1:
        raise ValueError('The maturity must align with the simulation time grid.')
    dt = model.T / steps
    rng = np.random.default_rng(seed)
    # Rows are paths and columns are time points; preserve the learning implementation's random-number order.
    shocks = rng.standard_normal((model.paths, steps))
    prices = np.empty((model.paths, steps + 1))
    prices[:, 0] = model.P
    for i in range(steps):
        prices[:, i + 1] = prices[:, i] * np.exp(
            (model.drift - 0.5 * sigma_actual**2) * dt
            + sigma_actual * np.sqrt(dt) * shocks[:, i]
        )
    return prices


def hedge_paths(prices, interval_days, fee_rate, model):
    """Return net P&L, gross P&L and trading costs accumulated to maturity. One option is on one share."""
    interval_steps_float = interval_days * model.steps_per_day
    interval_steps = round(interval_steps_float)
    if interval_steps < 1 or not np.isclose(interval_steps, interval_steps_float):
        raise ValueError('The rebalancing interval must be a positive integer multiple of the 0.1-day base step.')
    if fee_rate < 0:
        raise ValueError('The transaction-cost rate cannot be negative.')
    steps = prices.shape[1] - 1
    dt = model.T / steps
    initial_price, initial_delta = initial_price_delta(model)
    count = prices.shape[0]
    shares = np.full(count, initial_delta)
    initial_fee = fee_rate * abs(initial_delta) * model.P
    cash = np.full(count, initial_price - initial_delta * model.P - initial_fee)
    costs_at_T = np.full(count, initial_fee)
    previous_i = 0

    for i in range(interval_steps, steps, interval_steps):
        growth = np.exp(model.r * (i - previous_i) * dt)
        cash *= growth
        costs_at_T *= growth
        current_price = prices[:, i]
        remaining_time = model.T - i * dt
        d1 = (np.log(current_price / model.K)
              + (model.r + 0.5 * model.sigma_hedge**2) * remaining_time
              ) / (model.sigma_hedge * np.sqrt(remaining_time))
        new_delta = np.fromiter((NORMAL.cdf(float(x)) for x in d1),
                                dtype=float, count=count)
        trade = new_delta - shares
        fee = fee_rate * np.abs(trade) * current_price
        cash -= trade * current_price + fee
        costs_at_T += fee
        shares = new_delta
        previous_i = i

    growth = np.exp(model.r * (steps - previous_i) * dt)
    cash *= growth
    costs_at_T *= growth
    closing_fee = fee_rate * np.abs(shares) * prices[:, -1]
    costs_at_T += closing_fee
    payoff = np.maximum(prices[:, -1] - model.K, 0)
    net_pnl = shares * prices[:, -1] + cash - closing_fee - payoff
    gross_pnl = net_pnl + costs_at_T
    return net_pnl, gross_pnl, costs_at_T


def metrics(values):
    return {
        'mean': float(np.mean(values)),
        'std': float(np.std(values, ddof=1)),
        'rmse': float(np.sqrt(np.mean(values**2))),
        'loss_probability': float(np.mean(values < 0)),
        'q05': float(np.quantile(values, 0.05)),
    }


def run_all(output_dir, model=None):
    model = Model() if model is None else model
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, pnl_rows = [], []
    bundles = {}

    def collect(case, seed, actual, fee, intervals, prices):
        bundle = {}
        for interval in intervals:
            net, gross, cost = hedge_paths(prices, interval, fee, model)
            # Accounting identity: costs do not change Delta; net P&L + accumulated costs = gross P&L.
            if fee:
                independent_gross, _, _ = hedge_paths(prices, interval, 0.0, model)
                if not np.allclose(net + cost, independent_gross, atol=1e-8, rtol=1e-9):
                    raise AssertionError('The self-financing and transaction-cost check failed.')
            elif not np.all(cost == 0):
                raise AssertionError('Trading costs must be zero when the fee rate is zero.')
            row = {
                'experiment': case, 'seed': seed, 'paths': model.paths,
                'steps_per_day': model.steps_per_day, 'interval_days': interval,
                'sigma_actual': actual, 'sigma_hedge': model.sigma_hedge,
                'fee_rate': fee, 'drift': model.drift, **metrics(net),
                'mean_cost_at_T': float(np.mean(cost)),
                'provenance': 'fresh_run',
            }
            rows.append(row)
            bundle[interval] = (net, gross, cost)
            for j in range(model.paths):
                pnl_rows.append([case, seed, interval, j + 1,
                                 net[j], gross[j], cost[j]])
            print(f'{case}, seed={seed}, interval={interval}: '
                  f'mean={row["mean"]:.4f}, std={row["std"]:.4f}, '
                  f'RMSE={row["rmse"]:.4f}, loss={row["loss_probability"]:.1%}', flush=True)
        bundles[(case, seed)] = bundle

    # A: compare replication RMSE under identical parameters in two independent batches.
    for seed in [42, 43]:
        prices = generate_paths(model, 0.20, seed)
        collect('A', seed, 0.20, 0.001, INTERVALS, prices)
        if seed == 43:
            collect('B_equal_vol_no_cost', seed, 0.20, 0.0, INTERVALS, prices)

    # B: reset seed 43 for each volatility to use paired random shocks.
    prices = generate_paths(model, 0.15, 43)
    collect('B_low_vol_no_cost', 43, 0.15, 0.0, INTERVALS, prices)
    collect('B_low_vol_with_cost', 43, 0.15, 0.001, INTERVALS, prices)
    prices = generate_paths(model, 0.25, 43)
    collect('B_high_vol_no_cost', 43, 0.25, 0.0, INTERVALS, prices)

    candidates = [row for row in rows
                  if row['experiment'] == 'B_low_vol_with_cost'
                  and row['loss_probability'] <= 0.01]
    selected = max(candidates, key=lambda row: row['mean']) if candidates else None

    # The original selection fixed a 3-day policy; evaluate it on an independent sample without reselection.
    prices = generate_paths(model, 0.15, 44)
    collect('B_validation_fixed_3_days', 44, 0.15, 0.001, [3], prices)

    with (output_dir / 'fresh_summary.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (output_dir / 'fresh_path_pnl.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['experiment', 'seed', 'interval_days', 'path_id',
                         'net_pnl', 'gross_pnl', 'cost_at_T'])
        writer.writerows(pnl_rows)
    metadata = {
        'model': model.__dict__, 'intervals_days': INTERVALS,
        'A_seeds': [42, 43], 'B_selection_seed': 43, 'B_validation_seed': 44,
        'selection_loss_limit': 0.01,
        'selected_interval_fresh': None if selected is None else selected['interval_days'],
        'validation_interval_fixed_from_history': 3,
        'numpy_version': np.__version__,
    }
    (output_dir / 'fresh_metadata.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    plot_results(rows, output_dir)
    print('Fresh run saved to:', output_dir.resolve(), flush=True)
    return rows


def plot_results(rows, output_dir):
    def select(case, seed):
        return [row for row in rows if row['experiment'] == case and row['seed'] == seed]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for seed in [42, 43]:
        group = select('A', seed)
        axes[0].plot([v['interval_days'] for v in group], [v['rmse'] for v in group],
                     'o-', label=f'Seed {seed}')
    group = select('A', 43)
    axes[1].plot(INTERVALS, [v['mean_cost_at_T'] for v in group], 'o-', label='Cost at T')
    axes[1].plot(INTERVALS, [v['std'] for v in group], 'o-', label='Net P&L SD')
    axes[0].set_ylabel('Net replication RMSE')
    axes[1].set_ylabel('Amount per option')
    for ax in axes:
        ax.set_xscale('log')
        ax.set_xlabel('Rebalancing interval (days)')
        ax.grid(alpha=0.3)
        ax.legend()
    fig.suptitle('A: matched volatility, 0.1% fee')
    fig.tight_layout()
    fig.savefig(output_dir / 'A_optimal_hedging.png', dpi=160)
    plt.close(fig)

    group = select('B_low_vol_with_cost', 43)
    x = [v['interval_days'] for v in group]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(x, [v['mean'] for v in group], 'o-', label='Mean net P&L')
    axes[0].plot(x, [v['q05'] for v in group], 'o--', label='5th percentile')
    axes[0].axhline(0, color='gray', linestyle=':')
    axes[0].set_ylabel('Terminal P&L')
    axes[0].legend()
    axes[1].plot(x, [100*v['loss_probability'] for v in group], 'o-', color='darkred')
    axes[1].axhline(1, color='gray', linestyle=':', label='1% sample constraint')
    axes[1].legend()
    axes[1].set_ylabel('Loss probability (%)')
    for ax in axes:
        ax.set_xscale('log')
        ax.set_xlabel('Rebalancing interval (days)')
        ax.grid(alpha=0.3)
    fig.suptitle('B: actual 15%, pricing 20%, fee 0.1%, seed 43')
    fig.tight_layout()
    fig.savefig(output_dir / 'B_volatility_trading.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    run_all(Path(__file__).resolve().parent / 'results' / 'rerun')
