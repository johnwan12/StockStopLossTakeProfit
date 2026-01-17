import streamlit as st
from polygon import RESTClient
from datetime import date, timedelta
import numpy as np
import os

# ────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────
st.set_page_config(page_title="Golden Stop Loss & Take Profit", layout="centered")

st.title("Short Golden Stop Loss & Take Profit Calculator")
st.markdown("Enter a stock symbol and your average price. Uses 14-day ATR × φ (golden ratio ≈ 1.618) for dynamic R.")

# ────────────────────────────────────────────────
# Get API key from Streamlit secrets
# ────────────────────────────────────────────────
try:
    api_key = st.secrets["POLYGON_API_KEY"]
    if not api_key or len(api_key.strip()) < 10:
        st.error("Invalid or missing POLYGON_API_KEY in Streamlit secrets. Please add it in App Settings → Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Could not read POLYGON_API_KEY from secrets: {str(e)}\n\nGo to Manage app → Settings → Secrets and add:\n```\nPOLYGON_API_KEY = \"your_key_here\"\n```")
    st.stop()

client = RESTClient(api_key=api_key)

# ────────────────────────────────────────────────
# User inputs
# ────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    ticker = st.text_input("Stock Symbol (e.g. TSLA, AAPL)", value="TSLA").strip().upper()

with col2:
    try:
        avg_price = st.number_input("Your Average Price ($)", min_value=0.01, value=250.0, step=0.01)
    except:
        avg_price = None

if not ticker:
    st.info("Please enter a stock symbol.")
    st.stop()

if not avg_price or avg_price <= 0:
    st.info("Please enter a valid average price > 0.")
    st.stop()

# ────────────────────────────────────────────────
# Fetch data
# ────────────────────────────────────────────────
with st.spinner(f"Fetching data for {ticker}..."):
    try:
        today = date.today()
        from_date = today - timedelta(days=40)  # buffer for weekends/holidays

        # Get ticker details (name)
        details = client.get_ticker_details(ticker)
        stock_name = details.name if details else ticker

        # Get aggregates (daily bars)
        aggs = client.get_aggs(
            ticker,
            multiplier=1,
            timespan="day",
            from_=from_date.strftime("%Y-%m-%d"),
            to=today.strftime("%Y-%m-%d"),
            limit=120
        )

        if len(aggs) < 15:
            st.error(f"Not enough data for {ticker} (need at least 14 days). Try another symbol or check market status.")
            st.stop()

        # Current price & name
        current_price = aggs[-1].close

        # Calculate True Range for last 14+ periods
        tr_list = []
        for i in range(1, len(aggs)):
            h = aggs[i].high
            l = aggs[i].low
            pc = aggs[i-1].close
            tr = max(h - l, abs(h - pc), abs(l - pc))
            tr_list.append(tr)

        atr = np.mean(tr_list[-14:])   # 14-day ATR

        golden_ratio = 1.618
        R = (golden_ratio * atr) / current_price

        stop_loss   = avg_price * (1 - R)
        take_profit = avg_price * (1 + 2 * R)

        # ────────────────────────────────────────────────
        # Display results
        # ────────────────────────────────────────────────
        st.success("Calculation complete!")
        st.subheader(stock_name or ticker)

        st.markdown(f"**Current Date**: {today.strftime('%B %d, %Y')}")
        st.markdown(f"**Current Price**: ${current_price:,.2f}")
        st.markdown(f"**Short Golden Stop Loss % (R)**: {R*100:.2f}%  (based on 14-day ATR × 1.618)")

        col_sl, col_tp = st.columns(2)
        with col_sl:
            st.metric("Stop Loss Price", f"${stop_loss:,.2f}", delta=f"-{R*100:.2f}%")
        with col_tp:
            st.metric("Take Profit Price (2R)", f"${take_profit:,.2f}", delta=f"+{2*R*100:.2f}%")

    except Exception as e:
        error_msg = str(e).lower()
        if "auth" in error_msg or "api_key" in error_msg:
            st.error("Authentication failed. Double-check your POLYGON_API_KEY in Streamlit secrets.")
        elif "not found" in error_msg or "invalid" in error_msg:
            st.error(f"Ticker '{ticker}' not found or no data available. Try e.g. AAPL, MSFT, NVDA.")
        else:
            st.error(f"Error fetching data: {str(e)}\n\nTry again later or check your internet connection.")
