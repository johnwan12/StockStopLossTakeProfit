from polygon import RESTClient
from datetime import date, timedelta
import numpy as np

# Initialize Polygon client (assumes API key is configured)
client = RESTClient()

# Input: Stock symbol and your average price
ticker = 'TSLA'  # Enter your stock symbol here
average_price = 250  # Enter your average price here

# Fetch recent daily data (last 30 days for ATR calculation)
today = date.today()
from_ = today - timedelta(days=30)
aggs = client.get_aggs(ticker, 1, 'day', from_.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

# Calculate true ranges
tr = []
for i in range(1, len(aggs)):
    high = aggs[i].high
    low = aggs[i].low
    prev_close = aggs[i-1].close
    tr.append(max(high - low, high - prev_close, prev_close - low))

# Calculate 14-day ATR
atr = np.mean(tr[-14:])

# Current price and stock name
current_price = aggs[-1].close
stock_name = client.get_ticker_details(ticker).name

# Calculate R using golden ratio multiplier (1.618 * ATR / current_price)
R = 1.618 * atr / current_price

# Calculate stop loss and take profit
stop_loss = average_price * (1 - R)
take_profit = average_price * (1 + 2 * R)

# Output report
print(f'Stock Name: {stock_name}')
print(f'Current Date: {today}')
print(f'Short Golden Stop Loss Percentage (R): {R * 100:.2f}%')
print(f'Stop Loss Price: {stop_loss:.2f}')
print(f'Take Profit Price: {take_profit:.2f}')
