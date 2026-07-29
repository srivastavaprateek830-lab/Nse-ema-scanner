import streamlit as st
import pandas as pd
import numpy as np
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

# --- Pure Native Mathematics Engine (Replaces pandas_ta) ---
def compute_rsi_native(series, period=14):
    """Calculates Wilder's RSI using pure mathematical calculations"""
    if len(series) <= period:
        return 50.0
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Smooth using Wilder's technique
    for i in range(period, len(series)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

def compute_supertrend_native(df, period=10, multiplier=3.0):
    """Calculates standard SuperTrend without library dependencies"""
    if len(df) < period:
        return 0
        
    high = df['High'].astype(float)
    low = df['Low'].astype(float)
    close = df['Close'].astype(float)
    
    # Calculate True Range (TR)
    hl = high - low
    hc = (high - close.shift(1)).abs()
    lc = (low - close.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    
    # Calculate Average True Range (ATR)
    atr = tr.rolling(window=period).mean()
    for i in range(period, len(df)):
        atr.iloc[i] = (atr.iloc[i-1] * (period - 1) + tr.iloc[i]) / period
        
    hl2 = (high + low) / 2
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)
    
    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    trend = np.ones(len(df)) # 1 = Bullish, -1 = Bearish
    
    for i in range(1, len(df)):
        # Calculate upper band boundaries
        if basic_upper.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i-1]
            
        # Calculate lower band boundaries
        if basic_lower.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i-1]
            
        # Define current trend direction logic
        if close.iloc[i] > final_upper.iloc[i]:
            trend[i] = 1
        elif close.iloc[i] < final_lower.iloc[i]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]
            if trend[i] == 1 and final_lower.iloc[i] < final_lower.iloc[i-1]:
                final_lower.iloc[i] = final_lower.iloc[i-1]
            if trend[i] == -1 and final_upper.iloc[i] > final_upper.iloc[i-1]:
                final_upper.iloc[i] = final_upper.iloc[i-1]
                
    return int(trend[-1])

@st.cache_data(ttl=300)
def fetch_stock_matrix_data(symbol):
    try:
        # Fetch multi-timeframe source histories
        hf_df = yf.download(symbol, period="1mo", interval="15m", progress=False)
        d_df = yf.download(symbol, period="2y", interval="1d", progress=False)
        w_df = yf.download(symbol, period="5y", interval="1wk", progress=False)
        
        if hf_df.empty or d_df.empty or w_df.empty:
            return None

        # Clean yfinance multi-index structural columns
        for df in [hf_df, d_df, w_df]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

        # Resample data streams natively
        st_15m = compute_supertrend_native(hf_df)
        df_1h = hf_df.resample('1H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        st_1h = compute_supertrend_native(df_1h)
        
        st_daily = compute_supertrend_native(d_df)
        st_weekly = compute_supertrend_native(w_df)
        
        price = float(hf_df['Close'].iloc[-1])
        prev_close = float(d_df['Close'].iloc[-2]) if len(d_df) > 1 else price
        pct_change = ((price - prev_close) / prev_close) * 100
        current_rsi = compute_rsi_native(d_df['Close'], length=14)

        return {
            "Price": round(price, 2), "Change": round(pct_change, 2), "RSI": round(current_rsi, 1),
            "W": st_weekly, "D": st_daily, "1H": st_1h, "15m": st_15m
        }
    except:
        return None

# --- Application Engine Operations ---
st.title("🔍 Live Multi-Timeframe SuperTrend Status Matrix")
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

watchlist_data = []
with st.spinner("Processing Market Architectures Natively..."):
    for stock in FO_STOCKS:
        res = fetch_stock_matrix_data(stock)
        if res:
            action_signal = "🟢 BUY" if res["1H"] == 1 else "🔴 SELL"
            watchlist_data.append({
                "Ticker": stock.replace(".NS", ""), "Price (₹)": res["Price"], "Change (%)": res["Change"],
                "RSI (14)": res["RSI"], "Action": action_signal, "W": res["W"], "D": res["D"],
                "1H": res["1H"], "15m": res["15m"]
            })
            
    # Calculate index updates natively
    sector_perf = {}
    for sec_name, sec_ticker in SECTORS.items():
        sec_df = yf.download(sec_ticker, period="5d", interval="1d", progress=False)
        if not sec_df.empty:
            if isinstance(sec_df.columns, pd.MultiIndex): 
                sec_df.columns = sec_df.columns.get_level_values(0)
            chg = ((sec_df['Close'].iloc[-1] - sec_df['Close'].iloc[-2]) / sec_df['Close'].iloc[-2]) * 100
            sector_perf[sec_name] = round(chg, 2)

df_master = pd.DataFrame(watchlist_data)

# --- UI Layout Rendering Layer ---
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

# --- Dynamic Automated Box Routing ---
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
