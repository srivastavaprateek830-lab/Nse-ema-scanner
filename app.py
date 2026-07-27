import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# Fix for Yahoo Finance cache location on Streamlit servers
yf.set_tz_cache_location("/tmp/yf_cache")

# Professional dashboard display options
st.set_page_config(page_title="NSE F&O Analytics Dashboard", page_icon="📈", layout="wide")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Scanner Options")
    st.write("Click below to manual flush the cache window and fetch raw market updates.")
    # Manual data refresh button isolated to the side panel
    if st.button("🔄 Refresh Scanner Data", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- MAIN DASHBOARD INTERFACE ---
st.title("📊 NSE F&O Strategy Dashboard")
st.markdown("This tracker highlights extreme price expansion signals away from daily moving average baselines.")

# Comprehensive list of active liquid NSE F&O Tickers
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
    
    # Formulate a clean browser session to keep yfinance downloads running smooth
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Download data in bulk using the corrected '3mo' duration value
    tickers_str = " ".join(FO_TICKERS)
    data = yf.download(tickers_str, period="3mo", interval="1d", group_by="ticker", progress=False, session=session)
    
    for ticker in FO_TICKERS:
        try:
            # Extract ticker specific dataframe safely
            df = data[ticker].dropna() if ticker in data.columns.levels else pd.DataFrame()
            if df.empty or len(df) < 20:
                continue
                
            # Calculate EMA20
            close_prices = df['Close']
            ema20 = close_prices.ewm(span=20, adjust=False).mean()
            
            # Get latest values
            current_price = float(close_prices.iloc[-1])
            current_ema20 = float(ema20.iloc[-1])
            
            # Calculate percentage deviation
            deviation = ((current_price - current_ema20) / current_ema20) * 100
            
            # Determine Action Signal
            if deviation <= -10:
                action = "🔴 BUY (Undervalued)"
            elif deviation >= 10:
                action = "🟢 SELL (Overvalued)"
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

with st.spinner("Streaming security metrics from market channels... Please wait."):
    results_df = scan_markets()

if not results_df.empty:
    # Sort absolute deviations largest to smallest
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Route matching entries cleanly to target action buckets
    buy_box_df = all_sorted[all_sorted["Deviation (%)"] <= -10][["Ticker", "Price (₹)", "Deviation (%)"]]
    sell_box_df = all_sorted[all_sorted["Deviation (%)"] >= 10][["Ticker", "Price (₹)", "Deviation (%)"]]

    # --- 📈 INTEGRATED TREND CHART ENGINE ---
    st.markdown("### 📈 Historical Trend Visualizer")
    selected_ticker = st.selectbox("🎯 Select any active symbol from the dropdown to instantly view its close trend against the EMA20:", sorted(all_sorted["Ticker"].unique()))
    
    if selected_ticker:
        try:
            chart_df = yf.download(f"{selected_ticker}.NS", period="3mo", interval="1d", progress=False)
            if not chart_df.empty:
                chart_df['EMA20 Line'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
                plot_data = pd.DataFrame({'Close Price': chart_df['Close'], 'EMA20 Baseline': chart_df['EMA20 Line']}, index=chart_df.index)
                st.line_chart(plot_data, y=["Close Price", "EMA20 Baseline"])
        except Exception:
            st.caption("Data lines for this symbol are busy right now. Try selecting a different asset.")

    st.markdown("---")

    # --- 📊 MULTI-COLUMN DESIGN WORKSPACE ---
    left_col, mid_col, right_col = st.columns([0.6, 0.2, 0.2]) # Splits viewport: 60% Master table, 20% Buy panel, 20% Sell panel

    # 1. Column Frame: Full Master Table (60% Width)
    with left_col:
        st.subheader("🔍 Complete F&O Watchlist Deviation")
        st.dataframe(all_sorted, use_container_width=True, hide_index=True)

    # 2. Column Frame: Dedicated Buy Alerts Box (20% Width)
    with mid_col:
        st.markdown("<div style='background-color: rgba(255, 75, 75, 0.15); padding: 12px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (&lt; -10%)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not buy_box_df.empty:
            st.dataframe(buy_box_df, use_container_width=True, hide_index=True)
        else:
            st.info("Empty panel. No entities match criteria.")

    # 3. Column Frame: Dedicated Sell Alerts Box (20% Width)
    with right_col:
        st.markdown("<div style='background-color: rgba(41, 181, 232, 0.15); padding: 12px; border-radius: 6px; border-left: 5px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (&gt; +10%)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not sell_box_df.empty:
            st.dataframe(sell_box_df, use_container_width=True, hide_index=True)
        else:
            st.info("Empty panel. No entities match criteria.")
else:
    st.error("Market data pipeline empty. Yahoo blocked the connection request. Click the Refresh button on the left sidebar to try again.")
