import os
import csv
import math
from datetime import datetime
import matplotlib.pyplot as plt

filename = 'ASML.csv'
ticker = 'ASML'

# --- NEW SECTION: Check for file and download if missing ---
if not os.path.exists(filename):
    print(f"'{filename}' not found. Downloading 5 years of data using yfinance...")
    import yfinance as yf
    
    # Download using Ticker to avoid MultiIndex issues
    stock = yf.Ticker(ticker)
    data = stock.history(period='5y')
    
    # Save the data to a CSV file
    data.to_csv(filename)
    print(f"Data successfully saved to '{filename}'.\n")
else:
    print(f"'{filename}' found locally. Skipping download.\n")
# -----------------------------------------------------------

# 1. Read Data from the Local CSV File
prices = []
dates = []

print(f"Reading data from {filename}...")
with open(filename, 'r') as file:
    reader = csv.reader(file)
    header = next(reader)  # Grab the header row to find column positions
    
    # yfinance sometimes names the index 'Date' or 'Datetime' depending on the interval
    date_col_name = 'Date' if 'Date' in header else 'Datetime'
    
    date_idx = header.index(date_col_name)
    close_idx = header.index('Close')  # We use standard Close 
    
    for row in reader:
        try:
            # We slice [:10] to only grab 'YYYY-MM-DD' and ignore timezone/time data
            dt = datetime.strptime(row[date_idx][:10], '%Y-%m-%d')
            price = float(row[close_idx])
            
            dates.append(dt)
            prices.append(price)
        except ValueError:
            # Skip empty or unparseable rows
            continue

print(f"Successfully loaded {len(prices)} days of data.\n")

# 2. Hardcoded Returns Calculation
arithmetic_returns = []
geometric_returns = []
return_dates = dates[1:] 

for i in range(1, len(prices)):
    p_t = prices[i]
    p_t_1 = prices[i-1]
    
    r_a = (p_t - p_t_1) / p_t_1
    arithmetic_returns.append(r_a)
    
    r_g = math.log(p_t / p_t_1)
    geometric_returns.append(r_g)

# 3. Hardcoded Standard Deviation Function
def calculate_sample_std(data_list):
    n = len(data_list)
    if n <= 1:
        return 0.0
    
    mean_val = sum(data_list) / n
    sum_squared_diffs = sum((x - mean_val) ** 2 for x in data_list)
    variance = sum_squared_diffs / (n - 1)
    return math.sqrt(variance)

# --- Grouping by Year and Half-Year ---
yearly_returns_a = {}
yearly_returns_g = {}
h1_returns_a = {} # Jan - Jun
h2_returns_a = {} # Jul - Dec
h1_returns_g = {}
h2_returns_g = {}

for i in range(len(return_dates)):
    dt = return_dates[i]
    y = dt.year
    m = dt.month
    
    if y not in yearly_returns_a:
        yearly_returns_a[y] = []
        yearly_returns_g[y] = []
        h1_returns_a[y] = []
        h2_returns_a[y] = []
        h1_returns_g[y] = []
        h2_returns_g[y] = []
        
    yearly_returns_a[y].append(arithmetic_returns[i])
    yearly_returns_g[y].append(geometric_returns[i])
    
    if m <= 6:
        h1_returns_a[y].append(arithmetic_returns[i])
        h1_returns_g[y].append(geometric_returns[i])
    else:
        h2_returns_a[y].append(arithmetic_returns[i])
        h2_returns_g[y].append(geometric_returns[i])

print("=== ASML VOLATILITY BREAKDOWN PER YEAR ===")
for y in sorted(yearly_returns_a.keys()):
    # Calculate Yearly Volatility (Annualized)
    vol_y_a = calculate_sample_std(yearly_returns_a[y]) * math.sqrt(252)
    vol_y_g = calculate_sample_std(yearly_returns_g[y]) * math.sqrt(252)
    
    # Calculate Half-Year Volatility (Scaled by 126 days)
    vol_h1_a = calculate_sample_std(h1_returns_a[y]) * math.sqrt(126) if len(h1_returns_a[y]) > 1 else 0.0
    vol_h1_g = calculate_sample_std(h1_returns_g[y]) * math.sqrt(126) if len(h1_returns_g[y]) > 1 else 0.0
    
    vol_h2_a = calculate_sample_std(h2_returns_a[y]) * math.sqrt(126) if len(h2_returns_a[y]) > 1 else 0.0
    vol_h2_g = calculate_sample_std(h2_returns_g[y]) * math.sqrt(126) if len(h2_returns_g[y]) > 1 else 0.0

    print(f"\nYear: {y}")
    print(f"  Yearly Volatility    -> Arithmetic: {vol_y_a:.4f} | Geometric: {vol_y_g:.4f}")
    if vol_h1_a > 0:
        print(f"  First Half (H1) Vol  -> Arithmetic: {vol_h1_a:.4f} | Geometric: {vol_h1_g:.4f}")
    if vol_h2_a > 0:
        print(f"  Second Half (H2) Vol -> Arithmetic: {vol_h2_a:.4f} | Geometric: {vol_h2_g:.4f}")
print("==========================================\n")

# 4. Hardcoded Rolling Volatility Calculation
window_size = 30
rolling_arithmetic_vol = []
rolling_geometric_vol = []

rolling_dates = return_dates[window_size - 1:]

for i in range(len(arithmetic_returns) - window_size + 1):
    window_arith = arithmetic_returns[i : i + window_size]
    window_geom = geometric_returns[i : i + window_size]
    
    daily_vol_arith = calculate_sample_std(window_arith)
    daily_vol_geom = calculate_sample_std(window_geom)
    
    annualized_arith = daily_vol_arith * math.sqrt(252)
    annualized_geom = daily_vol_geom * math.sqrt(252)
    
    rolling_arithmetic_vol.append(annualized_arith)
    rolling_geometric_vol.append(annualized_geom)

# 5. Plot the Results
plt.figure(figsize=(12, 6))
plt.plot(rolling_dates, rolling_arithmetic_vol, label='Arithmetic Volatility', color='blue', alpha=0.7, linewidth=2)
plt.plot(rolling_dates, rolling_geometric_vol, label='Geometric Volatility', color='red', alpha=0.7, linestyle='--', linewidth=2)

plt.title('ASML 30-Day Rolling Annualized Volatility (From CSV Data)')
plt.xlabel('Date')
plt.ylabel('Annualized Volatility')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.show()