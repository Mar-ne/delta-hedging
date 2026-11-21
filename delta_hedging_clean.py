# -*- coding: utf-8 -*-
# Save the generated results in the results directory next to this script.
# Rerun the entire script after changing any parameters.

# %% Parameters
import csv
from pathlib import Path
from statistics import NormalDist

import numpy as np
import matplotlib.pyplot as plt

P = 100             # Initial stock price
K = 100             # Strike price
sigma = 0.20        # Annualized volatility
T = 1               # One-year maturity
step = 365          # 365 simulation intervals per year
r = 0.05            # Annualized risk-free rate
path_count = 1000
seed = 42
intervals = [1, 7, 30]
drifts = [0.10, -0.10]
dt = T / step
normal = NormalDist()


result_dir = Path(__file__).resolve().parent / "results"
result_dir.mkdir(exist_ok=True)

# %% Initial pricing
d1 = (np.log(P / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
d2 = d1 - sigma * np.sqrt(T)
call_price = P * normal.cdf(d1) - K * np.exp(-r * T) * normal.cdf(d2)
delta = normal.cdf(d1)
initial_cash = call_price - delta * P

print(f"Initial option price: {call_price:.10f}")
print(f"Initial delta:        {delta:.10f}")
print(f"Initial cash:         {initial_cash:.10f}")


# %% Functions
def generate_path(rng, drift):
    """Generate one GBM path using the exact grid update, including the initial price."""
    prices = [P]
    for i in range(step):
        Z = rng.standard_normal()
        next_price = prices[-1] * np.exp(
            (drift - 0.5 * sigma**2) * dt
            + sigma * np.sqrt(dt) * Z
        )
        prices.append(next_price)
    return np.array(prices)


def hedge_error(prices, rebalance_every):
    """Return the terminal self-financing replication error using the model parameters above."""
    shares = delta
    cash = call_price - shares * P

    for i in range(1, step):
        cash *= np.exp(r * dt)  # Accrue cash interest every day, whether or not a trade occurs
        if i % rebalance_every != 0:
            continue

        current_price = prices[i]
        remaining_time = T - i * dt
        current_d1 = (
            np.log(current_price / K)
            + (r + 0.5 * sigma**2) * remaining_time
        ) / (sigma * np.sqrt(remaining_time))
        new_delta = normal.cdf(current_d1)

        cash -= (new_delta - shares) * current_price
        shares = new_delta

    # Accrue interest over the final interval; do not evaluate Delta at expiry
    cash *= np.exp(r * dt)
    final_value = shares * prices[-1] + cash
    payoff = max(prices[-1] - K, 0)
    return final_value - payoff


# %% Two drift scenarios and summary statistics
all_errors = {}
example_paths = {}

for drift in drifts:
    # Reset the seed for each drift so both scenarios use paired random shocks.
    # Within a scenario, initialize the generator outside the path loop.
    rng = np.random.default_rng(seed)
    errors = {interval: [] for interval in intervals}

    for path_number in range(path_count):
        prices = generate_path(rng, drift)
        if path_number == 0:
            example_paths[drift] = prices.copy()
        for interval in intervals:
            errors[interval].append(hedge_error(prices, interval))

    all_errors[drift] = {
        interval: np.array(values) for interval, values in errors.items()
    }

# Calculate summary statistics after all paths have been simulated.
summary = []
print("Drift   Interval   Mean error     RMSE")
for drift in drifts:
    for interval in intervals:
        values = all_errors[drift][interval]
        mean_error = float(np.mean(values))
        rmse = float(np.sqrt(np.mean(values**2)))
        summary.append({
            "drift": drift, "interval_days": interval,
            "mean_error": mean_error, "rmse": rmse,
        })
        print(f"{drift:+.0%}    {interval:>3}        {mean_error:>8.4f}   {rmse:>8.4f}")


# %% Figures
times = np.linspace(0, T, step + 1)
fig, ax = plt.subplots(figsize=(9, 4.5))
for drift in drifts:
    ax.plot(times, example_paths[drift], label=f"Drift = {drift:+.0%}")
ax.axhline(K, color="gray", linestyle="--", label="Strike = 100")
ax.set(xlabel="Time (years)", ylabel="Stock price",
       title="Example GBM paths with identical random shocks")
ax.legend()
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(result_dir / "example_paths.png", dpi=160)
plt.show()


combined = np.concatenate([
    all_errors[drift][interval] for drift in drifts for interval in intervals
])
bins = np.linspace(combined.min(), combined.max(), 41)
fig, axes = plt.subplots(2, 3, figsize=(14, 7), sharex=True, sharey=True)
for row, drift in enumerate(drifts):
    for col, interval in enumerate(intervals):
        ax = axes[row, col]
        ax.hist(all_errors[drift][interval], bins=bins,
                color="#397ca8", edgecolor="white", linewidth=0.4)
        ax.axvline(0, color="#c33c3c", linestyle="--", linewidth=1)
        ax.set_title(f"Drift {drift:+.0%} | every {interval} day(s)")
        ax.set_xlabel("Hedging error")
        if col == 0:
            ax.set_ylabel("Number of paths")
fig.suptitle(f"Discrete delta hedging: {path_count} paths per drift")
fig.tight_layout()
fig.savefig(result_dir / "error_distributions.png", dpi=160)
plt.show()


fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(intervals))
width = 0.35
for offset, drift in zip([-width / 2, width / 2], drifts):
    values = [row["rmse"] for row in summary if row["drift"] == drift]
    bars = ax.bar(x + offset, values, width, label=f"Drift = {drift:+.0%}")
    ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=9)
ax.set_xticks(x, [f"Every {n} day(s)" for n in intervals])
ax.set(ylabel="RMSE", title="Replication accuracy by rebalancing frequency")
ax.set_ylim(0, max(row["rmse"] for row in summary) * 1.22)
ax.legend()
fig.tight_layout()
fig.savefig(result_dir / "rmse_comparison.png", dpi=160)
plt.show()


# %% Export
with (result_dir / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0]))
    writer.writeheader()
    writer.writerows(summary)

with (result_dir / "path_errors.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["drift", "path_id", "error_1_day", "error_7_days", "error_30_days"])
    for drift in drifts:
        for j in range(path_count):
            writer.writerow([drift, j + 1] + [
                all_errors[drift][interval][j] for interval in intervals
            ])

print("Saved figures and CSV files to:", result_dir.resolve())
