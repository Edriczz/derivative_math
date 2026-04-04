import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 1. Initialize the Ticker
ticker = "ASML"
asml = yf.Ticker(ticker)

# 2. Get S_0 (Current Stock Price)
# Using history to get the most reliable recent close price
s_0 = asml.history(period="1d")['Close'].iloc[-1]
print(f"Current {ticker} Price (S_0): ${s_0:.2f}")

# 3. Get Expiration Dates
expirations = asml.options
if not expirations:
    print("No options data found.")
    exit()

# Let's pick an expiration date a bit further out for a better example (e.g., the 3rd available date)
target_date_str = expirations[2] 
print(f"\nSelected Expiration Date: {target_date_str}")

# 4. Calculate T (Time to Expiration in Years)
# Convert string to datetime, assume expiry at 4:00 PM EST
expiration_date = datetime.strptime(target_date_str, '%Y-%m-%d')
today = datetime.now()
days_to_expiry = (expiration_date - today).days

# Annualize the time to expiration
T = days_to_expiry / 365.0 
print(f"Time to Expiration (T): {T:.4f} years ({days_to_expiry} days)")

# 5. Fetch the Option Chain
chain = asml.option_chain(target_date_str)
calls = chain.calls
puts = chain.puts

# 6. Select a specific Strike Price (K) close to the current price (At-The-Money)
# We find the strike price in the calls dataframe that has the minimum absolute difference from S_0
atm_call = calls.iloc[(calls['strike'] - s_0).abs().argsort()[:1]]
K = atm_call['strike'].values[0]
call_premium = atm_call['lastPrice'].values[0]

print(f"\nEvaluating At-The-Money Call Option:")
print(f"Strike Price (K): ${K:.2f}")
print(f"Option Premium (Cost to buy): ${call_premium:.2f}")

# 7. Evaluate and Plot against hypothetical S_T
# Generate a range of potential stock prices at expiration (S_T) +/- 20% from K
S_T = np.linspace(K * 0.8, K * 1.2, 100)

# Calculate Intrinsic Value (Payoff) and Total Profit
# Payoff = max(S_T - K, 0)
intrinsic_value = np.maximum(S_T - K, 0)
# Profit accounts for the premium paid to buy the contract
profit = intrinsic_value - call_premium

# Plotting the evaluation
plt.figure(figsize=(10, 6))
plt.plot(S_T, intrinsic_value, label='Intrinsic Value (Payoff)', linestyle='--', color='blue')
plt.plot(S_T, profit, label='Net Profit', color='green')
plt.axhline(0, color='black', linewidth=1)
plt.axvline(K, color='red', linestyle=':', label=f'Strike Price (K = {K})')
plt.axvline(K + call_premium, color='purple', linestyle=':', label=f'Breakeven (S_T = {K + call_premium:.2f})')

plt.title(f"{ticker} Call Option Evaluation (Expiry: {target_date_str})")
plt.xlabel("Stock Price at Expiration ($S_T$)")
plt.ylabel("Value / Profit ($)")
plt.legend()
plt.grid(True)

# 1. Create a dynamic filename so it doesn't overwrite older files
filename = f"{ticker}_call_evaluation_{target_date_str}.png"

# 2. Save the figure. 
# dpi=300 makes it high-resolution (great for documents)
# bbox_inches='tight' ensures the labels don't get cut off
plt.savefig(filename, dpi=300, bbox_inches='tight')

print(f"\nGraphic successfully downloaded and saved as: {filename}")

# 3. Optional: You can keep plt.show() if you still want the window to pop up, 
# or you can delete plt.show() if you ONLY want it to save in the background.
plt.show()