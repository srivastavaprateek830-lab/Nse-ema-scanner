import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# --- Page Config Setup ---
st.set_page_config(layout="wide", page_title="F&O Swing Dashboard")

# --- Use st.html to apply the custom CSS styles directly without markdown errors ---
st.html("""
    <style>
    .metric-box-buy {
        background-color: #0e2f1d; padding: 15px; border-radius: 8px;
        border-left: 6px solid #198754; margin-bottom: 12px; color: #e0f2e9;
    }
    .metric-box-sell {
        background-color: #3b141a; padding: 15px; border-radius: 8px;
        border-left: 6px solid #dc3545; margin-bottom: 12px; color: #fde8eb;
    }
    .arrow-green { color: #28a745; font-weight: bold; }
    .arrow-red { color: #dc3545; font-weight: bold; }
    </style>
""")

st.title("🎯 High-Conviction F&O Daily Swing Dashboard")
st.caption("Daily Trend Systems Engine (RSI 50 Reversals + SuperTrend + 7 SMA Check)")
st.divider()

# --- Core Liquid F&O Watchlist ---
FNO_TICKERS = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "BHARTIARTL",
    "SBIN", "LTIM", "AXISBANK", "TATAMOTORS", "TRENT", "BAJFINANCE", "MARUTI",
    "HINDALCO", "KOTAKBANK", "LT", "HCLTECH", "SUNPHARMA", "M&M"
]

# --- Sidebar Layout: Watchlist View Panel ---
with st.sidebar:
    st.header("📋 F&O Master Watchlist")
    st.write(f"Total Liquid Counters Monitored: **{len(FNO_TICKERS)}**")
    selected_stock = st.selectbox("Quick-Inspect Underlying Data:", FNO_TICKERS)

# --- Background Technical Calculation Processing Engine ---
@st.cache_data(ttl=1800)
def compute_market_signals(tickers):
    buy_signals = []
    sell_signals = []
    
    for ticker in tickers:
        try:
            yf_sym = f"{ticker}.NS"
            df = yf.download(yf_sym, period="1y", interval="1d", progress=False)
            if df.empty or len(df) < 30:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            df['SMA_7'] = ta.trend.sma_indicator(df['Close'], window=7)
            
            df['above_st'] = df['Close'] > ta.trend.ema_indicator(df['Close'], window=20)
            df['above_sma'] = df['Close'] > df['SMA_7']
            df['below_st'] = df['Close'] < ta.trend.ema_indicator(df['Close'], window=20)
            df['below_sma'] = df['Close'] < df['SMA_7']

            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            stock_data = {
                "name": ticker,
                "rsi": round(float(curr['RSI']), 2),
                "close": round(float(curr['Close']), 2),
                "above_st": bool(curr['above_st']),
                "above_sma": bool(curr['above_sma']),
                "below_st": bool(curr['below_st']),
                "below_sma": bool(curr['below_sma'])
            }
            
            if float(prev['RSI']) <= 50 and float(curr['RSI']) > 50 and stock_data["above_st"] and stock_data["above_sma"]:
                buy_signals.append(stock_data)
            elif float(prev['RSI']) >= 50 and float(curr['RSI']) < 50 and stock_data["below_st"] and stock_data["below_sma"]:
                sell_signals.append(stock_data)
        except:
            continue
    return buy_signals, sell_signals

# --- Run Screening Operations ---
with st.spinner("Processing real-time equity technical data models..."):
    buys, sells = compute_market_signals(FNO_TICKERS)

# --- Dashboard Layout Panels ---
col_buy, col_sell = st.columns(2)

with col_buy:
    st.subheader("🟢 High-Conviction BUY Triggers")
    if not buys:
        st.info("No F&O counters currently crossing above structural RSI 50 criteria today.")
    else:
        for stock in buys:
            st.html(f"""
                <div class="metric-box-buy">
                    <h3>📈 {stock['name']}</h3>
                    <p><b>Current Price:</b> ₹{stock['close']}</p>
                    <p><b>Daily RSI:</b> <b>{stock['rsi']}</b> (Crossed &gt; 50)</p>
                    <p>Price vs SuperTrend: <span class="arrow-green">▲ Above</span></p>
                    <p>Price vs 7-Period SMA: <span class="arrow-green">▲ Above</span></p>
                </div>
            """)

with col_sell:
    st.subheader("🔴 High-Conviction SELL Triggers")
    if not sells:
        st.info("No F&O counters currently breaking down beneath macro boundaries today.")
    else:
        for stock in sells:
            st.html(f"""
                <div class="metric-box-sell">
                    <h3>📉 {stock['name']}</h3>
                    <p><b>Current Price:</b> ₹{stock['close']}</p>
                    <p><b>Daily RSI:</b> <b>{stock['rsi']}</b> (Crossed &lt; 50)</p>
                    <p>Price vs SuperTrend: <span class="arrow-red">▼ Below</span></p>
                    <p>Price vs 7-Period SMA: <span class="arrow-red">▼ Below</span></p>
                </div>
            """)
