import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import datetime
from streamlit_autorefresh import st_autorefresh

# Auto refresh every 60 seconds
st_autorefresh(interval=60000, key="auto")

st.set_page_config(page_title="AI Crypto Signals Bot", layout="wide")
st.title("🚀 AI Crypto Trading Signals Bot (Supertrend Strategy)")
st.markdown("**Real-time signals • 6 timeframes • Entry + TP + SL • Auto refresh**")

st.sidebar.header("Settings")
symbol = st.sidebar.text_input("Trading Pair", value="BTC/USDT").upper()
rr_ratio = st.sidebar.slider("Risk-Reward Ratio", 1.0, 5.0, 2.0, 0.5)
st.sidebar.caption("Supertrend settings: Period = 10, Multiplier = 3 (best setting for crypto)")

# Disclaimer
st.sidebar.warning("⚠️ Trading crypto is high risk. This is NOT financial advice. Use only money you can afford to lose.")

# Get current price
exchange = ccxt.binance({'enableRateLimit': True})
try:
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    st.success(f"Current {symbol} price: ${current_price:,.2f} ")
except:
    st.error("Invalid pair or Binance rate limit. Try BTC/USDT, ETH/USDT, SOL/USDT etc.")
    st.stop()

timeframes = ['1m', '3m', '5m', '15m', '30m', '1h']

signals = []

for tf in timeframes:
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=300)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calculate Supertrend
        df.ta.supertrend(length=10, multiplier=3, append=True)

        # Find column names dynamically (works with 3 or 3.0)
        supertrend_col = [col for col in df.columns if col.startswith('SUPER_') and 'd' not in col.lower()][0]
        direction_col = [col for col in df.columns if 'SUPERd' in col][0]

        last = df.iloc[-1][supertrend_col]
        direction_now = df.iloc[-1][direction_col]
        direction_prev = df.iloc[-2][direction_col]

        if direction_now == 1:  # Uptrend = BUY
            direction_str = "🟢 BUY (Long)"
            sl = super_t
            tp = current_price + (current_price - sl) * rr_ratio
        else:  # Downtrend = SELL
            direction_str = "🔴 SELL (Short)"
            sl = super_t
            tp = current_price - (sl - current_price) * rr_ratio

        # Check if NEW signal (trend flip on last closed candle)
        if direction_now != direction_prev:
            st.balloons()
            st.success(f"**🔔 NEW SIGNAL on {tf} → {direction_str} at {current_price}$**")

        signals.append({
            "Timeframe": tf,
            "Signal": direction_str,
            "Entry Price": f"${current_price:,.2f}",
            "Stop Loss": f"${sl:,.2f}",
            "Take Profit": f"${tp:,.2f}",
            "Potential Profit": f"{((tp - current_price)/current_price*100 if direction_now == 1 else (current_price - tp)/current_price*100):.1f}%",
            "Last Update": df['timestamp'].iloc[-1].strftime('%H:%M:%S')
        })
    except Exception as e:
        signals.append({"Timeframe": tf, "Signal": "Error/No data", "Entry Price": "-", "Stop Loss": "-", "Take Profit": "-", "Potential Profit": "-", "Last Update": "-"})

# Display table
st.table(pd.DataFrame(signals).set_index("Timeframe"))

st.markdown("---")
st.caption("Signals update every 60 seconds • Supertrend (10,3) is one of the most profitable indicators on crypto in 2024-2025 • You can deploy this app free on Streamlit Cloud")
