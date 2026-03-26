# CPPI_strategy

## Description
This repository implements and analyzes the CPPI (Constant Proportion Portfolio Insurance) strategy. It aims to evaluate in which market conditions is it best to adopt it and its effectiveness in balancing risk and return through dynamic allocation between risky (S&P 500) and risk-free (3-month U.S. Treasury Bills) assets, compared to a passive Buy & Hold approach.

## Data
- S&P 500 daily prices are obtained via Yahoo Finance API.  
- 3-month U.S. Treasury Bills returns are sourced from the FRED (Federal Reserve Economic Data) database.

## Default parameters
CPPI strategy is implemented using the following baseline parameters:

- Start date: 2010-01-01 
- End date: 2015-01-01 
- Initial portfolio value: 100 
- Floor value: 70 
- Maximum leverage: 2 (with a tolerance threshold of 10%) 
- Cushion multiplier: 3 
- Transaction costs: 
- Trading commission: 0.1% 
- Bid-ask spread: 0.05% 
- Rebalancing frequency: every 21 days

They can be changed to perform different backtests.

## Buy-and-Hold Benchmark
To ensure a fair comparison, the Buy & Hold portfolio is constructed with weights that replicate the CPPI initial allocation:

- The weight of the risk-free asset is set equal to the floor value at time 0  
- The remaining capital is invested in the risky asset  

## Results
The analysis highlights the performance and risk characteristics of the CPPI strategy compared to the Buy & Hold. Key metrics such as rolling differential returns, Sharpe ratio and dynamic drawdown and distributions are used to assess the trade-off between downside protection and upside participation and compare with Buy & Hold strategy.

For a detailed analysis with full graphs and explanations, see my Medium article: https://medium.com/datadriveninvestor/is-cppi-a-good-strategy-backtesting-performance-and-risk-vs-buy-hold-across-market-scenarios-c8628306129b


## How to run the code
1. Clone the repository  
2. Install the required packages imported in the script
3. Set discretional parameters (start_date, end_date, Floor_T, m, ml, cost_pct, spread_pct, rebalance_days, th)
4. Run Backtesting_CPPI script to backtest the strategy
5. Review generated outputs and figures
