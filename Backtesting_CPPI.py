# Author: Davide Marangiello - DavideM-quant

#  This script analyzes the CPPI (Constant Proportion Portfolio Insurance) strategy, using the S&P 500 as the risky
#  asset and 3-month U.S. Treasury Bills as the risk-free asset. A comparative backtest against a Buy & Hold strategy
#  is performed to evaluates performance and risk.


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis

############### 1. Setting Dataset ###############

sp_daily = pd.read_excel("data_daily.xlsx", sheet_name="SP500 daily")
rf_annual = pd.read_excel("data_daily.xlsx", sheet_name="3M T-bills")


# Taking common dates
data = pd.merge(sp_daily, rf_annual, on='Date')
data = data.ffill()

# DISCRETIONAL PARAMETER: can be changed to analyse different periods
# Very good period: 2010-2015
# Bad period: 2018-2023
# Very bad period: 2006-2011
start_date = pd.to_datetime("2010-01-01")
end_date   = pd.to_datetime("2015-01-01")

data['Date'] = pd.to_datetime(data['Date'])
data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]

dates = data['Date'].iloc[1:].values

# Risky asset returns
sp_prices = data['Prices'].values
r_risky_asset = np.diff(sp_prices) / sp_prices[:-1]

# Risk free asset daily returns
r_rf_asset = data['Rate'].values[1:]
r_rf_asset = r_rf_asset / 100
r_rf_asset = (1 + r_rf_asset)**(1/252) - 1


# Check for data integrity

# Normalizing prices to 100
risky_index = sp_prices / sp_prices[0] * 100

rf_index = np.zeros(len(r_rf_asset) + 1)
rf_index[0] = 100

for i in range(1, len(rf_index)):
    rf_index[i] = rf_index[i-1] * (1 + r_rf_asset[i-1])

# Plot of normalized prices

plt.figure()

plt.plot(data['Date'], risky_index, 'k', linewidth=1.5)
plt.plot(data['Date'], rf_index, 'b', linewidth=1.5)

plt.title('Risky Asset and Risk-Free Asset', fontsize=16)
plt.xlabel('Date')
plt.ylabel('Index (Base = 100)')
plt.legend(['Risky Asset (S&P500)', 'Risk-Free Asset (3M T-bills)'], loc='upper left', fontsize=12)
plt.grid(True)

############### 2. Setting parameters and initial values of CPPI and Buy & Hold strategies ###############

# number of days in the selected period
T = len(dates)

###### CPPI ######

# DISCRETIONARY PARAMETERS

p = np.zeros(T)
p[0] = 100     # Portfolio initial value

Floor_T = 70    # Estimated floor at maturity

ml = 2         # max leverage allowed
m = 3          # cushion multiplier

# Transaction costs: trading fee + bid-ask spread
# for simplicity i don't consider splippage and leverage costs
cost_pct = 0.001   # 0.1% per trade
spread_pct = 0.0005 # 0.05% bid-ask spread

# rebalancing frequency (trading month)
rebalance_days = 21

# tolerance threshold for exceeding the maximum leverage
# (to avoid too many rebalancing operations and thus excessive transaction costs)
th = 0.10

# INITIAL VALUES

# Floor: there are different methods to calculate it.
# - it can be assumed that the discount rate remain constant over the period
# - I can use the yield curve but we need further data.
# For the sake of simplicity i assume that the discount rate is constant.

f = np.zeros(T)
f[0] = Floor_T / (1 + r_rf_asset[0])**(T-1)

# Cushion
c = np.zeros(T)
c[0] = p[0] - f[0]

# Investment in the risky asset - meets max leverage condition
s = np.zeros(T)
s[0] = min(ml * p[0], m * c[0])

# Invesment in risk-free asset
b = np.zeros(T)
b[0] = p[0] - s[0]


###### Buy & Hold ######

# Allocation should be the same of the initial CPPI allocation for a
# correct comparison

# relative weights
w_rf = f[0] / p[0]
w_risky = 1 - w_rf

bh_risky = np.zeros(T)
bh_rf = np.zeros(T)

bh_risky[0] = 100
bh_rf[0] = 100

# Allocation
BH = np.zeros(T)
BH[0] = w_risky * bh_risky[0] + w_rf * bh_rf[0]

############### 3. Backtesting CPPI and Buy & Hold strategies ###############

# initializing lock-in variable
lock_in = False

for i in range(1, T):

    ###### CPPI ######

    # Computing portfolio value
    p[i] = s[i - 1] * (1 + r_risky_asset[i - 1]) + b[i - 1] * (1 + r_rf_asset[i - 1])

    # Computing floor
    f[i] = Floor_T / (1 + r_rf_asset[i]) ** (T - i - 1)

    # Computing cushion
    c[i] = p[i] - f[i]

    # Non lock-in scenario
    if lock_in == False:

        # 2 rebalancing conditions: every 21 days or if the actual levarage exceed
        # the max leverage plus a tolerance threshold
        if ((i % rebalance_days) == 0) or (s[i - 1] * (1 + r_risky_asset[i - 1]) / p[i] > ml * (1 + th)):

            # New allocation
            s_new = max(0, min(ml * p[i], m * c[i]))
            b_new = p[i] - s_new

            # Accounting for transaction costs
            trade = abs(s_new - (s[i - 1] * (1 + r_risky_asset[i - 1])))

            # New portfolio value
            p[i] = p[i] - trade * (cost_pct + spread_pct)

            # Update allocation
            s[i] = s_new
            b[i] = b_new

        else:
            # No trade
            s[i] = s[i - 1] * (1 + r_risky_asset[i - 1])
            b[i] = b[i - 1] * (1 + r_rf_asset[i - 1])

        # Lock-in scenario activation
        if p[i] <= f[i]:
            lock_in = True

            # Sell the total amount of risky asset
            trade = abs(s[i - 1] * (1 + r_risky_asset[i - 1]))

            # Accounting for transaction costs
            p[i] = p[i] - trade * (cost_pct + spread_pct)

            s[i] = 0
            b[i] = p[i]

    else:
        # Lock-in scenario
        s[i] = 0
        b[i] = b[i - 1] * (1 + r_rf_asset[i - 1])
        p[i] = b[i]

    ###### Buy & Hold ######

    bh_risky[i] = bh_risky[i - 1] * (1 + r_risky_asset[i - 1])
    bh_rf[i] = bh_rf[i - 1] * (1 + r_rf_asset[i - 1])
    BH[i] = w_risky * bh_risky[i] + w_rf * bh_rf[i]

############### 4. Charts ###############

x_axis = dates

plt.figure(figsize=(12,10))

# 4.1 CPPI vs Buy & Hold portfolio value
plt.subplot(2,2,1)
plt.plot(x_axis, p, 'r', linewidth=1.5)
plt.plot(x_axis, BH, 'k', linewidth=1.5)
plt.title('CPPI vs Buy & Hold - S&P500')

# if CPPI goes in lock in plot a black dot
lock_in_idx = np.where(p <= f)[0]
if len(lock_in_idx) > 0:
    idx = lock_in_idx[0]
    plt.scatter(dates[idx], p[idx], color='k', s=80)

plt.ylabel('Portfolio Value')
plt.legend(['CPPI','Buy & Hold','Lock-in'])
plt.grid(True)


# 4.2 CPPI vs floor (the difference is equal to the cushion)

plt.subplot(2,2,2)
plt.plot(dates, p, 'r', linewidth=1.5)
plt.plot(dates, f, 'b', linewidth=1.5)

lock_in_idx = np.where(p <= f)[0]
if len(lock_in_idx) > 0:
    idx = lock_in_idx[0]
    plt.scatter(dates[idx], p[idx], color='k', s=80)

plt.title('CPPI vs Floor')
plt.ylabel('Value')
plt.legend(['CPPI','Floor','Lock-in'])
plt.grid(True)


# 4.3 Proportion invested in the risky asset

plt.subplot(2,2,3)
plt.plot(x_axis, s/p, 'r', linewidth=1.5)

plt.axhline(ml)              # max leverage
plt.axhline(1)               # 100% of portfolio invested in the risky asset
plt.axhline(ml*(1+th), linestyle='--')  # threshold

plt.title('Proportion of Portfolio Invested in the Risky Asset')
plt.ylabel('Proportion')

plt.legend(['CPPI Risky allocation',
            'Max leverage (ml)',
            'Full portfolio (100%)',
            'Tolerance threshold'])
plt.grid(True)


# 4.4 Lock-in risk: portfolio distance to floor (%)

distance_pct = (p - f) / f

# Lock-in day
lock_in_idx = np.where(p <= f)[0]

plt.subplot(2,2,4)
plt.plot(dates, distance_pct, 'k', linewidth=1.5)

if len(lock_in_idx) > 0:
    idx = lock_in_idx[0]
    plt.scatter(dates[idx], distance_pct[idx], color='k', s=80)

plt.title('CPPI Safety Buffer - Lock-in risk')
plt.ylabel('Distance to Floor')
plt.grid(True)

plt.tight_layout()

############### 5. Computing descriptive statistics ###############

# Strategies returns
r_CPPI = np.diff(p) / p[:-1]
r_BH = np.diff(BH) / BH[:-1]

# Simple mean
r_mean_CPPI = np.mean(r_CPPI)
r_mean_BH = np.mean(r_BH)

# Annualised simple mean
r_mean_CPPI_1Y = r_mean_CPPI * 252
r_mean_BH_1Y = r_mean_BH * 252

# Geometric average
r_geom_CPPI = np.exp(np.mean(np.log(1 + r_CPPI))) - 1
r_geom_BH = np.exp(np.mean(np.log(1 + r_BH))) - 1

# Annualised Geometric average
r_geom_CPPI_1Y = (1 + r_geom_CPPI)**252 - 1
r_geom_BH_1Y = (1 + r_geom_BH)**252 - 1

# Min and Max Return
r_min_CPPI = np.min(r_CPPI)
r_max_CPPI = np.max(r_CPPI)

r_min_BH = np.min(r_BH)
r_max_BH = np.max(r_BH)

# Standard Deviation
r_std_CPPI = np.std(r_CPPI)
r_std_BH = np.std(r_BH)

# Annualised Standard Deviation
r_std_CPPI_1Y = r_std_CPPI * np.sqrt(252)
r_std_BH_1Y = r_std_BH * np.sqrt(252)

# Skewness
skew_CPPI = skew(r_CPPI)
skew_BH   = skew(r_BH)

# Kurtosis
kurt_CPPI = kurtosis(r_CPPI)
kurt_BH   = kurtosis(r_BH)

# Max drawdown
cummax_p = np.maximum.accumulate(p)
cummax_BH = np.maximum.accumulate(BH)

DD_CPPI = (p - cummax_p) / cummax_p
DD_BH   = (BH - cummax_BH) / cummax_BH

maxDD_CPPI = np.min(DD_CPPI)
maxDD_BH   = np.min(DD_BH)

# Annualised Sharpe ratio
Sharpe_CPPI_1Y = (np.mean(r_CPPI) / np.std(r_CPPI)) * np.sqrt(252)
Sharpe_BH_1Y   = (np.mean(r_BH) / np.std(r_BH)) * np.sqrt(252)

# Value at Risk (1% and 5%)

VaR1_CPPI = np.quantile(r_CPPI, 0.01)
VaR1_BH   = np.quantile(r_BH, 0.01)

VaR5_CPPI = np.quantile(r_CPPI, 0.05)
VaR5_BH   = np.quantile(r_BH, 0.05)

# Tail Conditional Expectation (Expected Shortfall) (1% and 5%)

TCE1_CPPI = np.mean(r_CPPI[r_CPPI <= VaR1_CPPI])
TCE1_BH   = np.mean(r_BH[r_BH <= VaR1_BH])

TCE5_CPPI = np.mean(r_CPPI[r_CPPI <= VaR5_CPPI])
TCE5_BH   = np.mean(r_BH[r_BH <= VaR5_BH])


# Summary table

Stats_matrix = np.array([
    [r_geom_CPPI_1Y, r_geom_BH_1Y],
    [r_mean_CPPI_1Y, r_mean_BH_1Y],
    [r_min_CPPI, r_min_BH],
    [r_max_CPPI, r_max_BH],
    [r_std_CPPI_1Y, r_std_BH_1Y],
    [skew_CPPI, skew_BH],
    [kurt_CPPI, kurt_BH],
    [maxDD_CPPI, maxDD_BH],
    [Sharpe_CPPI_1Y, Sharpe_BH_1Y],
    [VaR1_CPPI, VaR1_BH],
    [VaR5_CPPI, VaR5_BH],
    [TCE1_CPPI, TCE1_BH],
    [TCE5_CPPI, TCE5_BH]
])

Stats = pd.DataFrame(
    Stats_matrix,
    columns=['CPPI','BuyHold'],
    index=[
        'GeomMean_1Y','Mean_1Y','Min','Max','StdDev_1Y','Skewness','Kurtosis','MaxDrawdown',
        'Sharpe_1Y','VaR_1pct','VaR_5pct','TCE_1pct','TCE_5pct'
    ]
)

print(Stats)

############### 6. Performance and Risk assessment ###############

plt.figure(figsize=(12,10))

# 6.1 Relative Price

plt.subplot(2,2,1)
plt.plot(dates, p/BH, linewidth=1.5)
plt.axhline(1, linestyle='--')
plt.title('Relative Price (CPPI / Buy & Hold)')
plt.ylabel('Relative Price')
plt.grid(True)


window = 252 # 1 trading year

# 6.2 Rolling 1Y differential returns

roll_CPPI = p[window:] / p[:-window] - 1
roll_BH   = BH[window:] / BH[:-window] - 1

roll_diff = roll_CPPI - roll_BH

plt.subplot(2,2,2)
plt.plot(dates[window:], roll_diff, linewidth=1.5)
plt.axhline(0, linestyle='--')
plt.title('Rolling 1Y Differential Return (CPPI - Buy & Hold)')
plt.ylabel('Outperformance')
plt.grid(True)


# 6.3 Rolling Sharpe ratio (Stop if it goes into lock-in)

sharpe_roll_CPPI = np.full(len(r_CPPI), np.nan)
sharpe_roll_BH   = np.full(len(r_BH), np.nan)

lock_in_idx = np.where(p <= f)[0]
lock_in_idx = lock_in_idx[0] if len(lock_in_idx) > 0 else None

for i in range(window, len(r_CPPI)):

    if lock_in_idx is not None and i >= lock_in_idx:
        sharpe_roll_CPPI[i] = np.nan
        continue

    mu_CPPI = np.mean(r_CPPI[i-window+1:i+1])
    sigma_CPPI = np.std(r_CPPI[i-window+1:i+1])

    mu_BH = np.mean(r_BH[i-window+1:i+1])
    sigma_BH = np.std(r_BH[i-window+1:i+1])

    sharpe_roll_CPPI[i] = (mu_CPPI*252) / (sigma_CPPI*np.sqrt(252))
    sharpe_roll_BH[i]   = (mu_BH*252) / (sigma_BH*np.sqrt(252))


plt.subplot(2,2,3)
plt.plot(dates[window:-1], sharpe_roll_CPPI[window:], 'r', linewidth=1.5)
plt.plot(dates[window:-1], sharpe_roll_BH[window:], 'k', linewidth=1.5)

if lock_in_idx is not None:
    plt.scatter(dates[lock_in_idx-1], sharpe_roll_CPPI[lock_in_idx-1], color='k', s=80)

plt.legend(['CPPI','Buy & Hold','Lock-in'])
plt.title('Rolling Sharpe Ratio (1Y)')
plt.ylabel('Sharpe')
plt.grid(True)


# 6.4 Max Drawdown

plt.subplot(2,2,4)
plt.plot(dates, DD_CPPI, 'r', linewidth=1.5)
plt.plot(dates, DD_BH, 'k', linewidth=1.5)
plt.gca().invert_yaxis()
plt.title('Dynamic Drawdown')
plt.legend(['CPPI','Buy & Hold'])
plt.ylabel('Drawdown')
plt.grid(True)

plt.tight_layout()

# %%%%%%%%%% Distributions %%%%%%%%%

plt.figure(figsize=(12,10))

# 6.5 Daily Returns Distribution
plt.subplot(2,2,1)
plt.hist(r_CPPI, bins=50, density=True, alpha=0.5)
plt.hist(r_BH, bins=50, density=True, alpha=0.5)
plt.title('Daily Returns Distribution')
plt.xlabel('Return')
plt.ylabel('Density')
plt.legend(['CPPI','Buy & Hold'])
plt.grid(True)

# 6.6 Rolling 1Y Returns Distribution
plt.subplot(2,2,2)
plt.hist(roll_CPPI, bins=50, density=True, alpha=0.5)
plt.hist(roll_BH, bins=50, density=True, alpha=0.5)
plt.title('Rolling 1Y Returns Distribution')
plt.xlabel('Return')
plt.ylabel('Density')
plt.legend(['CPPI','Buy & Hold'])
plt.grid(True)

# 6.7 Rolling 1Y Differential Return (CPPI - BH) Distribution
plt.subplot(2,2,3)
plt.hist(roll_diff, bins=50, density=True, alpha=0.5)
plt.axvline(0, linestyle='--')
plt.title('Rolling 1Y Differential Return (CPPI - B&H) Distribution')
plt.xlabel('Differencial Return')
plt.ylabel('Density')
plt.grid(True)

# 6.8 Percentage Floor Distance Distribution
plt.subplot(2,2,4)
plt.hist(distance_pct, bins=50, density=True, alpha=0.5)
plt.title('CPPI Percentage Distance to Floor Distribution')
plt.xlabel('Portfolio - Floor (%)')
plt.ylabel('Density')
plt.grid(True)

plt.tight_layout()
plt.show()