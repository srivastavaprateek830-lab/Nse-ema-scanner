import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# --- Page Config Setup ---
st.set_page_config(layout="wide", page_title="F&O Swing Dashboard")

# --- Optimized CSS Styles for 3 Columns ---
st.html("""
    <style>
    .status-card {
        padding: 12px; border-radius: 6px; margin-bottom: 10px; color: #ffffff; font-family: monospace;
    }
    .bg-neutral { background-color: #1e1e24; border-left: 4px solid #6c757d; }
    .bg-buy { background-color: #0e2f1d; border-left: 4px solid #198754; }
    .bg-sell { background-color: #3b141a; border-left: 4px solid #dc3545; }
    .text-green { color: #28a745; font-weight: bold; }
    .text-red { color: #dc3545; font-weight: bold; }
    </style>
""")

st.title("🎯 High-Conviction F&O Multi-Column Dashboard")
st.caption("Complete Market Regime Matrix (RSI 50 Filter + Trend Line Proxy + 7 SMA)")
st.divider()

# --- Full F&O Master Watchlist Asset Base (Expanded) ---
FNO_TICKERS = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "BHARTIARTL",
    "SBIN", "LTIM", "AXISBANK", "TATAMOTORS", "TRENT", "BAJFINANCE", "MARUTI",
    "HINDALCO", "KOTAKBANK", "LT", "HCLTECH", "SUNPHARMA", "M&M", "ULTRACEMCO",
    "POWERGRID", "NTPC", "TITAN", "ASIANPAINT", "ADANIENT", "JSWSTEEL", "COALINDIA"
]

# --- Background Technical Calculation Processing Engine ---
@st.cache_data(ttl=1800)
def process_full_market(tickers):
    all_stocks = []
    buy_stocks = []
    sell_stocks = []
    
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
            
            # Use safe background indicator proxies for momentum regime matching
            df['above_st'] = df['Close'] > ta.trend.ema_indicator(df['Close'], window=20)
            df['above_sma'] = df['Close'] > df['SMA_7']
            df['below_st'] = df['Close'] < ta.trend.ema_indicator(df['Close'], window=20)
            df['below_sma'] = df['Close'] < df['SMA_7']

            curr = df.iloc[-1]
            c_price = float(curr['Close'])
            c_rsi = float(curr['RSI'])
            
            stock_data = {
                "name": ticker,
                "rsi": round(c_rsi, 2),
                "close": round(c_price, 2),
                "above_st": bool(curr['above_st']),
                "above_sma": bool(curr['above_sma']),
                "below_st": bool(curr['below_st']),
                "below_sma": bool(curr['below_sma'])
            }
            
            all_stocks.append(stock_data)
            
            # Continuous Structural Regime Rules (Not limited to exact crossover candle)
            if c_rsi > 50 and stock_data["above_st"] and stock_data["above_sma"]:
                buy_stocks.append(stock_data)
            elif c_rsi < 50 and stock_data["below_st"] and stock_data["below_sma"]:
                sell_stocks.append(stock_data)
        except:
            continue
            
    return all_stocks, buy_stocks, sell_stocks

# --- Run Screening Operations ---
with st.spinner("Processing full F&O technical analysis matrix..."):
    full_list, buy_list, sell_list = process_full_market(FNO_TICKERS)

# --- 3-Column Visual Layout Workspace ---
col1, col2, col3 = st.columns(3)

with col1:
    st.header(f"📋 Full Watchlist ({len(full_list)})")
    st.markdown("---")
    for stock in full_list:
        # Determine quick status tags for master summary list view
        tag = "🟢 BULL" if stock in buy_list else "🔴 BEAR" if stock in sell_list else "⚪ NEUTRAL"
        st.html(f"""
            <div class="status-card bg-neutral">
                <h4><b>{stock['name']}</b> ({tag})</h4>
                <p>Price: ₹{stock['close']} | RSI: {stock['rsi']}</p>
            </div>
        """)

with col2:
    st.header(f"🟢 Active BUY Market Regimes ({len(buy_list)})")
    st.markdown("---")
    if not buy_list:
        st.info("No stocks currently holding fully aligned bullish configurations.")
    else:
        for stock in buy_list:
            st.html(f"""
                <div class="status-card bg-buy">
                    <h3>📈 {stock['name']}</h3>
                    <p><b>Close:</b> ₹{stock['close']}</p>
                    <p><b>RSI:</b> {stock['rsi']} (<span class="text-green">Above 50</span>)</p>
                    <p>SuperTrend Proxy: <span class="text-green">▲ Above</span></p>
                    <p>7 SMA Line: <span class="text-green">▲ Above</span></p>
                </div>
            """)

with col3:
    st.header(f"🔴 Active SELL Market Regimes ({len(sell_list)})")
    st.markdown("---")
    if not sell_list:
        st.info("No stocks currently holding fully aligned bearish configurations.")
    else:
        for stock in sell_list:
            st.html(f"""
                <div class="status-card bg-sell">
                    <h3>📉 {stock['name']}</h3>
                    <p><b>Close:</b> ₹{stock['close']}</p>
                    <p><b>RSI:</b> {stock['rsi']} (<span class="text-red">Below 50</span>)</p>
                    <p>SuperTrend Proxy: <span class="text-red">▼ Below</span></p>
                    <p>7 SMA Line: <span class="text-red">▼ Below</span></p>
                </div>
            """)
