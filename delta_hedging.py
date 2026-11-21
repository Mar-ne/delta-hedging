import numpy as np
import matplotlib.pyplot as plt
from statistics import NormalDist

P = 100             # Initial stock price
K = 100             # Strike price
drift = 0.10        # Annualized physical drift
sigma = 0.20        # Annualized volatility
T = 1               # Simulate one year
step = 365          # Divide one year into 365 simulation steps
r = 0.05            # Annualized risk-free rate, set to 5%
dt = T / step       # Time increment measured in years
rng = np.random.default_rng(42) # Random number generator
prices = [P]        # Stock price sequence
normal = NormalDist()
#call price
d1 = (
    np.log(P / K) + (r + 0.5 * sigma**2) * T
) / (sigma * np.sqrt(T))

d2 = d1 - sigma * np.sqrt(T)

call_price = (
    P * normal.cdf(d1)
    - K * np.exp(-r * T) * normal.cdf(d2)
)

delta = normal.cdf(d1)

# Calculate the replication error for a price path and rebalancing interval
def hedge_error(prices, rebalance_every):
    shares = delta
    cash = call_price - shares * P

    for i in range(1, step):
        cash *= np.exp(r * dt)

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

    cash *= np.exp(r * dt)

    final_value = shares * prices[-1] + cash
    payoff = max(prices[-1] - K, 0)

    return final_value - payoff

#1000 path
rng = np.random.default_rng(42)
errors = {1: [], 7: [], 30: []}
for path_number in range(1000):
    prices = [P]

    # Generate one complete stock price path
    for i in range(step):
        Z = rng.standard_normal()

        P_next = prices[-1] * np.exp(
            (drift - 0.5 * sigma**2) * dt
            + sigma * np.sqrt(dt) * Z
        )

        prices.append(P_next)



    # Compare three rebalancing intervals on the same path
    for interval in errors:
        error = hedge_error(prices, interval)
        errors[interval].append(error)

# Summary statistics    
    for interval, values in errors.items():
        values = np.array(values)
    
        mean_error = np.mean(values)
        rmse = np.sqrt(np.mean(values**2))
        if path_number==999:
            print(
               f"Interval: {interval}, "
               f"Mean error: {mean_error:.4f}, "
               f"RMSE: {rmse:.4f}"
            )


fig, axes = plt.subplots(
    1, 3, figsize=(15, 4), sharex=True, sharey=True
)

# Use common histogram bin edges across the three panels
all_errors = np.concatenate(list(errors.values()))
bins = np.linspace(all_errors.min(), all_errors.max(), 41)

for ax, interval in zip(axes, [1, 7, 30]):
    ax.hist(errors[interval], bins=bins, edgecolor="white")
    ax.axvline(0, color="red", linestyle="--")

    ax.set_title(f"Rebalance every {interval} day(s)")
    ax.set_xlabel("Hedging error")

axes[0].set_ylabel("Number of paths")
fig.suptitle(f"Hedging errors across 1000 paths (drift = {drift:.0%})")

plt.tight_layout()
plt.show()
