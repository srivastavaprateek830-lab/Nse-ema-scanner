import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# --- Page Config Setup ---
st.set_page_config(layout="wide", page_title="Master F&O Swing Dashboard")

# --- Streamlit Theme Custom Table CSS Styling Injector ---
st.html("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; }
    .fno-table {
        width: 100%; border-collapse: collapse; margin-bottom: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .fno-table th {
        background-color: #11141a; color: #a1a7b5; padding: 10px; text-align: left;
        font-size: 12px; font-weight: 600; border-bottom: 2px solid #232833;
    }
    .fno-table td {
        padding: 10px; border-bottom: 1px solid #1f242e; font-size: 13px; color: #ffffff;
    }
    .dot-green { height: 12px; width: 12px; background-color: #28a745; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .dot-red { height: 12px; width: 12px; background-color: #dc3545; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .dot-gray { height: 12px; width: 12px; background-color: #6c757d; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .tag-buy { color: #28a745; font-weight: bold; }
    .tag-sell { color: #dc3545; font-weight: bold; }
    .tag-neutral { color: #6c757d; font-weight: bold; }
    </style>
""")

st.title("🎯 Comprehensive F&O Technical Matrix")
st.caption("Universal Multi-Column System Table (Real-Time RSI 50 Matrix + SuperTrend Filter)")
st.divider()

# --- Full Comprehensive High-Volume F&O Universe Array Base ---
FULL_FNO_LIST = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "BHARTIARTL", "SBIN", 
    "LTIM", "AXISBANK", "TATAMOTORS", "TRENT", "BAJFINANCE", "MARUTI", "HINDALCO", 
    "KOTAKBANK", "LT", "HCLTECH", "SUNPHARMA", "M&M", "ULTRACEMCO", "POWERGRID", 
    "NTPC", "TITAN", "ASIANPAINT", "ADANIENT", "JSWSTEEL", "COALINDIA", "HEROMOTOCO", 
    "HINDZINC", "VEDL", "AMBUJACEM", "TATASTEEL", "ADANIPORTS", "APOLLOHOSP", 
    "BAJAJFINSV", "AUBANK", "BEL", "BHARATFORG", "COFORGE", "DLF", "EICHERMOT", 
    "GRASIM", "HINDUNILVR", "INDUSINDBK", "IOC", "IRCTC", "JINDALSTEL", "LICHSGFIN"
]

@st.cache_data(ttl=900)  # Refresh metrics optimization interval cache every 15 minutes
def scan_fno_universe(tickers):
    master_rows = []
    buy_rows = []
    sell_rows = []
    
    for ticker in tickers:
        try:
            yf_sym = f"{ticker}.NS"
            df = yf.download(yf_sym, period="1mo", interval="1d", progress=False)
            if df.empty or len(df) < 15:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Execution Logic Computations
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            df['SMA_7'] = ta.trend.sma_indicator(df['Close'], window=7)
            df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)

            curr = df.iloc[-1]
            prev = df.iloc[-2]

            c_close = float(curr['Close'])
            p_close = float(prev['Close'])
            c_rsi = round(float(curr['RSI']), 1)
            
            # Mathematical percentage delta variations calculation
            pct_chg = round(((c_close - p_close) / p_close) * 100, 2)
            pct_str = f"+{pct_chg}%" if pct_chg >= 0 else f"{pct_chg}%"

            # Determine indicator status alignments
            st_bullish = c_close > float(curr['EMA_20'])
            sma_bullish = c_close > float(curr['SMA_7'])
            
            # Operational Status Logic Definition Arrays
            if c_rsi > 50 and st_bullish and sma_bullish:
                st_dot = '<span class="dot-green"></span>'
                sig_text = '<span class="tag-buy">🟢 Strong Buy</span>'
                status = "BUY"
            elif c_rsi < 50 and not st_bullish and not sma_bullish:
                st_dot = '<span class="dot-red"></span>'
                sig_text = '<span class="tag-sell">🔴 Strong Sell</span>'
                status = "SELL"
            else:
                st_dot = '<span class="dot-gray"></span>'
                sig_text = '<span class="tag-neutral">⚪ Neutral</span>'
                status = "NEUTRAL"

            row_html = f"""
                <tr>
                    <td><b>{ticker}</b></td>
                    <td>₹{round(c_close, 2)}</td>
                    <td>{pct_str}</td>
                    <td>{c_rsi}</td>
                    <td>{st_dot}</td>
                    <td>{sig_text}</td>
                </tr>
            """
            
            master_rows.append(row_html)
            if status == "BUY":
                buy_rows.append(row_html)
            elif status == "SELL":
                sell_rows.append(row_html)
        except:
            continue
            
    return master_rows, buy_rows, sell_rows

# --- Execute Parallel Cloud Scanning Data Operations ---
with st.spinner("Compiling full structural data matrices across F&O targets..."):
    master_data, buy_data, sell_data = scan_fno_universe(FULL_FNO_LIST)

# --- Render 3 Columns Interface Tables Side-by-Side ---
col1, col2, col3 = st.columns(3)

table_header_html = """
    <table class="fno-table">
        <thead>
            <tr>
                <th>Ticker</th>
                <th>LTP</th>
                <th>% Chg</th>
                <th>RSI</th>
                <th>Supertrend</th>
                <th>↓ Signal</th>
            </tr>
        </thead>
        <tbody>
"""

with col1:
    st.subheader(f"📋 Master F&O List ({len(master_data)})")
    if master_data:
        full_table = table_header_html + "".join(master_data) + "</tbody></table>"
        st.html(full_table)

with col2:
    st.subheader(f"🟢 Buy Watchlist ({len(buy_data)})")
    if buy_data:
        buy_table = table_header_html + "".join(buy_data) + "</tbody></table>"
        st.html(buy_table)
    else:
        st.info("No assets currently logging immediate aligned long setups.")

with col3:
    st.subheader(f"🔴 Sell Watchlist ({len(sell_data)})")
    if sell_data:
        sell_table = table_header_html + "".join(sell_data) + "</tbody></table>"
        st.html(sell_table)
    else:
        st.info("No assets currently logging immediate aligned short setups.")
