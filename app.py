import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

# Fix for Yahoo Finance cache location on Streamlit servers
yf.set_tz_cache_location("/tmp/yf_cache")

# Set up page configuration
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O EMA20 Deviation Scanner")
st.write("Scans NSE F&O stocks for price deviations (>10% or <-10%) from the 20-period EMA.")

# Curated list of prominent NSE F&O Tickers
FO_TICKERS = [
    "ACC.NS", "AARTIIND.NS", "ABB.NS", "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", 
    "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", 
    "BANKBARODA.NS", "BEL.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BPCL.NS", 
    "BRITANNIA.NS", "CANBK.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "CONCOR.NS", 
    "DABUR.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", 
    "GAIL.NS", "GLENMARK.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRASIM.NS", "HAL.NS", 
    "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", 
    "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "IDEA.NS", "IGL.NS", 
    "INDHOTEL.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", 
    "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", 
    "LTIM.NS", "LUPIN.NS", "M&M.NS", "MARICO.NS", "MARUTI.NS", "MCX.NS", "MUTHOOTFIN.NS", 
    "NATIONALUM.NS", "NAUKRI.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "ONGC.NS", 
    "PERSISTENT.NS", "PFC.NS", "PIDILITIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", 
    "REC.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", 
    "SHRIRAMFIN.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "TATACHEMICAL.NS", 
    "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", 
    "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", 
    "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS"
]

@st.cache_data(ttl=600)  # Caches results for 10 minutes to maintain speed
def scan_markets():
    scanned_data = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    tickers_str = " ".join(FO_TICKERS)
    
    # Anti-Throttling Strategy: Try downloading up to 3 times to get past cloud IP drops
    data = pd.DataFrame()
    for attempt in range(3):
        try:
            data = yf.download(tickers_str, period="3mo", interval="1d", group_by="ticker", progress=False, session=session)
            if not data.empty:
                break
        except Exception:
            time.sleep(1) # Soft pause before retrying
            
    if data.empty:
        return pd.DataFrame()
    
    for ticker in FO_TICKERS:
        try:
            df = data[ticker].dropna() if ticker in data.columns.levels else pd.DataFrame()
            if df.empty or len(df) < 20:
                continue
                
            close_prices = df['Close']
            ema20 = close_prices.ewm(span=20, adjust=False).mean()
            
            current_price = float(close_prices.iloc[-1])
            current_ema20 = float(ema20.iloc[-1])
            deviation = ((current_price - current_ema20) / current_ema20) * 100
            
            if deviation <= -10:
                action = "🔴 BUY"
            elif deviation >= 10:
                action = "🟢 SELL"
            else:
                action = "⚪ HOLD / NEUTRAL"
                
            scanned_data.append({
                "Ticker": ticker.replace(".NS", ""),
                "Price (₹)": round(current_price, 2),
                "EMA20 (₹)": round(current_ema20, 2),
                "Deviation (%)": round(deviation, 2),
                "Action": action
            })
        except Exception:
            continue
            
    return pd.DataFrame(scanned_data)

# Manual data refresh button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Scanning NSE F&O segment..."):
    results_df = scan_markets()

if not results_df.empty:
    # Sort data by largest deviation
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Extract clean buy and sell tables
    buy_box_df = all_sorted[all_sorted["Deviation (%)"] <= -10][["Ticker", "Price (₹)", "Deviation (%)"]]
    sell_box_df = all_sorted[all_sorted["Deviation (%)"] >= 10][["Ticker", "Price (₹)", "Deviation (%)"]]

    # --- 📈 INTERACTIVE TREND PREVIEW WINDOW ---
    st.markdown("### 📈 Historical Trend Explorer")
    selected_ticker = st.selectbox("🎯 Choose any stock to instantly plot its price vs EMA20 line graph:", sorted(all_sorted["Ticker"].unique()))
    
    if selected_ticker:
        try:
            # Safely fetch historical pricing array for chart visualization
            chart_df = yf.download(f"{selected_ticker}.NS", period="3mo", interval="1d", progress=False)
            if not chart_df.empty:
                chart_df['EMA20 Line'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
                plot_data = pd.DataFrame({'Close Price': chart_df['Close'], 'EMA20 Baseline': chart_df['EMA20 Line']}, index=chart_df.index)
                st.line_chart(plot_data, y=["Close Price", "EMA20 Baseline"])
        except Exception:
            st.caption("Chart pipeline briefly occupied. Select another ticker or try again.")

    st.markdown("---")

    # --- 📊 MULTI-COLUMN DESIGN LAYOUT ---
    left_col, right_col = st.columns([3, 2]) # Split workspace: 60% Left, 40% Right

    # Left Column Workspace: Master Watchlist Frame
    with left_col:
        st.subheader("🔍 Complete F&O Watchlist Deviation")
        st.dataframe(all_sorted, use_container_width=True, hide_index=True)

    # Right Column Workspace: Action Target Containers
    with right_col:
        st.subheader("🛒 Breakout Target Buckets")
        
        # Top Box Layer: Dynamic Buy Routing Panel
        st.markdown("<div style='background-color: rgba(255, 75, 75, 0.15); padding: 12px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (Deviation &lt; -10%)</div>", unsafe_allow_html=True)
        if not buy_box_df.empty:
            st.dataframe(buy_box_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks are currently showing a buy signal below -10%.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bottom Box Layer: Dynamic Sell Routing Panel
        st.markdown("<div style='background-color: rgba(41, 181, 232, 0.15); padding: 12px; border-radius: 6px; border-left: 5px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (Deviation &gt; +10%)</div>", unsafe_allow_html=True)
        if not sell_box_df.empty:
            st.dataframe(sell_box_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks are currently showing a sell signal above +10%.")
else:
    st.error("Yahoo's API network gate closed. Click 'Refresh Scanner Data' to cycle your cloud connection pipeline.")
