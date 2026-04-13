import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 1. Initialize the Ticker
ticker = "ASML"
asml = yf.Ticker(ticker)

# 2. Get Current Stock Price
s_0 = asml.history(period="1d")['Close'].iloc[-1]
print(f"Current {ticker} Price (S_0): ${s_0:.2f}")

# 3. Get Expiration Dates
expirations = asml.options
if not expirations:
    print("No options data found.")
    exit()

# Pick an expiration date
target_date_str = expirations[2] 
print(f"\nSelected Expiration Date: {target_date_str}")

# 4. Calculate T (Time to Expiration in Years)
expiration_date = datetime.strptime(target_date_str, '%Y-%m-%d')
today = datetime.now()
days_to_expiry = (expiration_date - today).days
T = days_to_expiry / 365.0 
print(f"Time to Expiration (T): {T:.4f} years ({days_to_expiry} days)")

# 5. Fetch the Option Chain
chain = asml.option_chain(target_date_str)

# Filter out contracts with near-zero premiums to avoid matching worthless, highly illiquid options
calls = chain.calls[chain.calls['lastPrice'] > 1.0].copy()
puts = chain.puts[chain.puts['lastPrice'] > 1.0].copy()

# 6. Search for the Closest Matching Premiums
# We perform a cross join to compare every single Call to every single Put
cross_join = calls.merge(puts, how='cross', suffixes=('_call', '_put'))

# Calculate the absolute difference between the premiums
cross_join['premium_diff'] = (cross_join['lastPrice_call'] - cross_join['lastPrice_put']).abs()

# Find the row where this difference is the absolute minimum
best_match = cross_join.loc[cross_join['premium_diff'].idxmin()]

# Extract the variables for our Strangle
K_c = best_match['strike_call']
K_p = best_match['strike_put']
call_premium = best_match['lastPrice_call']
put_premium = best_match['lastPrice_put']

print(f"\n--- Real-World Matched Contracts ---")
print(f"Call Option: Strike (K_c) = ${K_c:.2f}, Premium = ${call_premium:.2f}")
print(f"Put Option:  Strike (K_p) = ${K_p:.2f}, Premium = ${put_premium:.2f}")
print(f"Difference in Premium: ${abs(call_premium - put_premium):.2f}")

# To satisfy the math evaluation, we will take the average of these two very close premiums
# so they are perfectly identical for plotting purposes.
pi = (call_premium + put_premium) / 2
total_cost = pi * 2

print(f"\nTotal Strategy Cost (2 * pi): ${total_cost:.2f}")

# 7. Evaluate and Plot against hypothetical S_T
# Generate a range of potential stock prices, making sure it covers both strikes widely
min_strike = min(K_c, K_p)
max_strike = max(K_c, K_p)
S_T = np.linspace(min_strike * 0.7, max_strike * 1.3, 200)

# Calculate Individual Profits
call_profit = np.maximum(S_T - K_c, 0) - pi
put_profit = np.maximum(K_p - S_T, 0) - pi

# Calculate Combined Long Strangle Profit
strangle_profit = call_profit + put_profit

# Calculate Breakevens
upper_breakeven = K_c + total_cost
lower_breakeven = K_p - total_cost

# 8. Plotting the evaluation
plt.figure(figsize=(12, 7))

# Plot individual options
plt.plot(S_T, call_profit, label='Call Profit', linestyle='--', color='blue', alpha=0.6)
plt.plot(S_T, put_profit, label='Put Profit', linestyle='--', color='orange', alpha=0.6)

# Plot the main Strangle profit
plt.plot(S_T, strangle_profit, label='Long Strangle Net Profit', color='green', linewidth=2.5)

# Add reference lines
plt.axhline(0, color='black', linewidth=1)
plt.axvline(K_c, color='blue', linestyle=':', label=f'Call Strike (K_c = ${K_c:.2f})')
plt.axvline(K_p, color='orange', linestyle=':', label=f'Put Strike (K_p = ${K_p:.2f})')
plt.axvline(upper_breakeven, color='purple', linestyle=':', label=f'Upper Breakeven (${upper_breakeven:.2f})')
plt.axvline(lower_breakeven, color='purple', linestyle='-.', label=f'Lower Breakeven (${lower_breakeven:.2f})')

# Fill the profit/loss zones
plt.fill_between(S_T, strangle_profit, 0, where=(strangle_profit >= 0), facecolor='green', alpha=0.1)
plt.fill_between(S_T, strangle_profit, 0, where=(strangle_profit < 0), facecolor='red', alpha=0.1)

plt.title(f"{ticker} Long Strangle Evaluation (Expiry: {target_date_str})")
plt.xlabel("Stock Price at Expiration ($S_T$)")
plt.ylabel("Net Profit ($)")
plt.legend()
plt.grid(True)

# 9. Save and Show
filename = f"{ticker}_strangle_evaluation_{target_date_str}.png"
plt.savefig(filename, dpi=300, bbox_inches='tight')
print(f"\nGraphic successfully downloaded and saved as: {filename}")
plt.show()