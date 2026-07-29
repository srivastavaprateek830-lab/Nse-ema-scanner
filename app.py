import streamlit as st
import pandas as pd
import numpy as np

# --- STREAMLIT COMPATIBILITY PATCH FOR PANDAS_TA ---
# This explicitly re-injects the missing append method to stop pandas_ta from crashing
def patch_pandas_append():
    if not hasattr(pd.Series, 'append'):
        def legacy_append(self, other, ignore_index=False, verify_integrity=False, sort=False):
            return pd.concat([self, other], ignore_index=ignore_index)
        pd.Series.append = legacy_append
patch_pandas_append()

# Now it is completely safe to import pandas_ta
import pandas_ta as ta
import yfinance as yf


# --- Page Layout Setup ---
st.set_page_config(layout="wide", page_title="F&O SuperTrend Scanner")
st.markdown("<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True)

# --- F&O Watchlist Universe ---
FO_STOCKS = [
    "COFORGE.NS", "HCLTECH.NS", "TCS.NS", "TVSMOTOR.NS", "DIVISLAB.NS",
    "NAUKRI.NS", "CONCOR.NS", "PERSISTENT.NS", "TECHM.NS", "INFY.NS",
    "BAJAJ-AUTO.NS", "DRREDDY.NS", "DIXON.NS", "GODREJPROP.NS", "TITAN.NS", "SBICARD.NS"
]

SECTORS = {
    "IT SECTOR": "^CNXIT",
    "BANKING": "^NSEBANK",
    "ENERGY": "^CNXENERGY"
}

# --- Core SuperTrend Engine ---
def get_supertrend_signal(df, length=10, multiplier=3.0):
    """Returns 1 for Bullish (🟢), -1 for Bearish (🔴), 0 for No Data"""
    if len(df) < length:
        return 0
    st_df = ta.supertrend(df['High'], df['Low'], df['Close'], length=length, multiplier=multiplier)
    if st_df is None or st_df.empty:
        return 0
    direction_col = f"SUPERTd_{length}_{multiplier}"
    if direction_col in st_df.columns:
        return int(st_df[direction_col].iloc[-1])
    return 0

@st.cache_data(ttl=300) # 5-Minute Cache to safeguard API rate limits
def fetch_stock_matrix_data(symbol):
    try:
        # Pull required historical data resolution bundles
        hf_df = yf.download(symbol, period="1mo", interval="15m", progress=False)
        d_df = yf.download(symbol, period="2y", interval="1d", progress=False)
        w_df = yf.download(symbol, period="5y", interval="1wk", progress=False)
        
        if hf_df.empty or d_df.empty or w_df.empty:
            return None

        # Standardize column structure (strips multi-index levels if present)
        for df in [hf_df, d_df, w_df]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

        # 15M and 1H Resampling Calculations
        st_15m = get_supertrend_signal(hf_df)
        df_1h = hf_df.resample('1H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        st_1h = get_supertrend_signal(df_1h)
        
        # Daily and Weekly Calculations
        st_daily = get_supertrend_signal(d_df)
        st_weekly = get_supertrend_signal(w_df)
        
        # Core Watchlist Data Features
        price = float(hf_df['Close'].iloc[-1])
        prev_close = float(d_df['Close'].iloc[-2]) if len(d_df) > 1 else price
        pct_change = ((price - prev_close) / prev_close) * 100
        
        rsi_series = ta.rsi(d_df['Close'], length=14)
        current_rsi = float(rsi_series.iloc[-1]) if rsi_series is not None else 50.0

        return {
            "Price": round(price, 2), "Change": round(pct_change, 2), "RSI": round(current_rsi, 1),
            "W": st_weekly, "D": st_daily, "1H": st_1h, "15m": st_15m
        }
    except:
        return None

# --- Application Main Executive Process ---
st.title("🔍 Live Multi-Timeframe SuperTrend Status Matrix")
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

# Process Raw Universe Metrics
watchlist_data = []
with st.spinner("Syncing Live Exchange Data Feeds..."):
    for stock in FO_STOCKS:
        res = fetch_stock_matrix_data(stock)
        if res:
            # Map action logic based on the 1-Hour SuperTrend Frame
            action_signal = "🟢 BUY" if res["1H"] == 1 else "🔴 SELL"
            
            watchlist_data.append({
                "Ticker": stock.replace(".NS", ""), "Price (₹)": res["Price"], "Change (%)": res["Change"],
                "RSI (14)": res["RSI"], "Action": action_signal, "W": res["W"], "D": res["D"],
                "1H": res["1H"], "15m": res["15m"]
            })
            
    # Fetch Sector Changes
    sector_perf = {}
    for sec_name, sec_ticker in SECTORS.items():
        sec_df = yf.download(sec_ticker, period="5d", interval="1d", progress=False)
        if not sec_df.empty:
            if isinstance(sec_df.columns, pd.MultiIndex): sec_df.columns = sec_df.columns.get_level_values(0)
            chg = ((sec_df['Close'].iloc[-1] - sec_df['Close'].iloc[-2]) / sec_df['Close'].iloc[-2]) * 100
            sector_perf[sec_name] = round(chg, 2)

df_master = pd.DataFrame(watchlist_data)

# --- UI Presentation Grid Layer ---
left_col, right_col = st.columns([1.1, 0.9])

with left_col:
    st.subheader("📋 Complete F&O Watchlist")
    if not df_master.empty:
        st.dataframe(
            df_master[["Ticker", "Price (₹)", "Change (%)", "RSI (14)", "Action"]],
            use_container_width=True, hide_index=True
        )

with right_col:
    st.subheader("🎯 Live Multi-Timeframe SuperTrend Status Matrix")
    if not df_master.empty:
        matrix_df = df_master.copy()
        def format_emoji(val): return "🟩" if val == 1 else "🟥"
        for tf in ["W", "D", "1H", "15m"]:
            matrix_df[tf] = matrix_df[tf].apply(format_emoji)
            
        st.dataframe(
            matrix_df[["Ticker", "W", "D", "1H", "15m"]].rename(columns={"W": "Weekly", "D": "Daily", "1H": "Hourly", "15m": "15 Min"}),
            use_container_width=True, hide_index=True
        )

st.divider()

# --- Bottom Dynamic Routing System Layers ---
b_col1, b_col2, b_col3 = st.columns(3)

with b_col1:
    st.markdown("### 📥 Buy Stocks (1H SuperTrend = 🟢)")
    if not df_master.empty:
        buys = df_master[df_master["1H"] == 1][["Ticker", "Price (₹)", "Change (%)", "RSI (14)"]]
        if not buys.empty:
            st.dataframe(buys, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently meet Bullish 1H setups.")

with b_col2:
    st.markdown("### 📤 Sell Stocks (1H SuperTrend = 🔴)")
    if not df_master.empty:
        sells = df_master[df_master["1H"] == -1][["Ticker", "Price (₹)", "Change (%)", "RSI (14)"]]
        if not sells.empty:
            st.dataframe(sells, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently meet Bearish 1H setups.")

with b_col3:
    st.markdown("### ⚡ Nifty Sectors Performance")
    for sec, perf in sector_perf.items():
        color_flag = "🟢" if perf >= 0 else "🔴"
        st.markdown(f"**{sec}** : {color_flag} `{perf:+.2f}%`")
