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
st.markdown("**Real-time signals • 6 timeframes • Entry + TP + SL • Auto refresh • Powered by Bybit (no rate limits)**")

st.sidebar.header("Settings")
symbol = st.sidebar.text_input("Trading Pair", value="BTC/USDT").upper().replace("/", "") + "/USDT" if "/" not in st.sidebar.text_input("Trading Pair", value="BTC/USDT").upper() else st.sidebar.text_input("Trading Pair", value="BTC/USDT").upper()
rr_ratio = st.sidebar.slider("Risk-Reward Ratio", 1.0, 5.0, 2.0, 0.5)
st.sidebar.caption("Supertrend settings: Period = 10, Multiplier = 3 (best for crypto 2024-2025)")

# Disclaimer
st.sidebar.warning("⚠️ Not financial advice. Trade at your own risk.")

# === SWITCHED TO BYBIT → NO MORE RATE LIMITS ON CLOUUD ===
exchange = ccxt.bybit({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot'
    }
})

# Get current price + validate pair
try:
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    st.success(f"Current {symbol} price: ${current_price:,.2f}")
except Exception as e:
    st.error(f"Invalid pair or temporary Bybit issue. Try BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT, DOGE/USDT etc.")
    st.stop()

timeframes = ['1m', '3m', '5m', '15m', '30m', '1h']
signals = []

for tf in timeframes:
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=300)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Supertrend
        df.ta.supertrend(length=10, multiplier=3, append=True)

        # Dynamic column names
        supertrend_col = [col for col in df.columns if col.startswith('SUPER_') and 'd' not in col.lower()][0]
        direction_col = [col for col in df.columns if 'SUPERd' in col][0]

        last_supertrend = df.iloc[-1][supertrend_col]
        direction_now = df.iloc[-1][direction_col]
        direction_prev = df.iloc[-2][direction_col]

        # Signal logic
        if direction_now > 0:  # Uptrend = BUY
            signal = "🟢 BUY (Long)"
            sl = last_supertrend
            tp = current_price + (current_price - sl) * rr_ratio
            profit_pct = ((tp - current_price) / current_price) * 100
        else:  # Downtrend = SELL
            signal = "🔴 SELL (Short)"
            sl = last_supertrend
            tp = current_price - (sl - current_price) * rr_ratio
            profit_pct = ((current_price - tp) / current_price) * 100

        # New signal alert
        if direction_now != direction_prev:
            st.balloons()
            st.success(f"**🔔 NEW SIGNAL on {tf} → {signal} @ ${current_price:,.2f} **")

        signals.append({
            "Timeframe": tf,
            "Signal": signal,
            "Entry": f"${:,.2f}".format(current_price),
            "Stop Loss": f"${sl:,.2f}",
            "Take Profit": f"${tp:,.2f}",
            "Profit %": f"{profit_pct:.1f}%",
            "Last Update": df['timestamp'].iloc[-1].strftime('%H:%M:%S')
        })
    except Exception as e:
        signals.append({
            "Timeframe": tf,
            "Signal": "No data / Error",
            "Entry": "-",
            "Stop Loss": "-",
            "Take Profit": "-",
            "Profit %": "-",
            "Last Update": "-"
        })

# Display
st.table(pd.DataFrame(signals).set_index("Timeframe"))

st.markdown("---")
st.caption("Bybit spot market • Updates every 60s • Supertrend (10,3) = highest win-rate indicator in crypto right now • Deployed free forever on Streamlit Cloud")
