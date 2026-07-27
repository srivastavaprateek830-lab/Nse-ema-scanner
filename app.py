import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# Fix for Yahoo Finance cache location on Streamlit servers
yf.set_tz_cache_location("/tmp/yf_cache")

# Set up page configuration
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O EMA20 Deviation Scanner")
st.write("Scans NSE F&O stocks for price deviations (>10% or <-10%) from the 20-period EMA.")

# List of 100+ prominent NSE F&O Tickers (Appended with .NS for Yahoo Finance)
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

# One-click manual refresh button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Scanning NSE F&O segment... This takes a few seconds."):
    results_df = scan_markets()

if not results_df.empty:
    # Sort entire master list by absolute largest deviation right away
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Isolate active signal matches cleanly for the side buckets
    buy_signals_df = all_sorted[all_sorted["Deviation (%)"] <= -10][["Ticker", "Price (₹)", "Deviation (%)"]]
    sell_signals_df = all_sorted[all_sorted["Deviation (%)"] >= 10][["Ticker", "Price (₹)", "Deviation (%)"]]

    # --- 📈 DYNAMIC TREND VIEWER PANEL ---
    st.markdown("### 📈 Interactive Trend Visualizer")
    selected_ticker = st.selectbox("🎯 Click below to select any stock ticker and view its price vs EMA20 chart line:", sorted(all_sorted["Ticker"].unique()))
    
    if selected_ticker:
        try:
            # Create the exact same proxy session to fetch single stock chart safely
            chart_session = requests.Session()
            chart_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            ticker_ns = f"{selected_ticker}.NS"
            chart_df = yf.download(ticker_ns, period="3mo", interval="1d", progress=False, session=chart_session)
            if not chart_df.empty:
                chart_df['EMA20 Line'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
                
                # Bundle series for line rendering
                plot_data = pd.DataFrame({
                    'Market Price': chart_df['Close'],
                    'EMA20 Baseline': chart_df['EMA20 Line']
                }, index=chart_df.index)
                
                st.line_chart(plot_data, y=["Market Price", "EMA20 Baseline"])
        except Exception:
            st.caption("Unable to draw live preview chart for this token right now.")

    st.markdown("---")

    # --- 📊 THREE-COLUMN DISPLAY LAYOUT ---
    # Layout splits view screen room dynamically: 50% Master List, 25% Buy box, 25% Sell box
    left_col, mid_col, right_col = st.columns([0.5, 0.25, 0.25])

    # Column Workspace A: Master Watchlist
    with left_col:
        st.subheader("🔍 Complete F&O Watchlist Deviation")
        st.dataframe(all_sorted, use_container_width=True, hide_index=True)

    # Column Workspace B: Dedicated Buy Box Container
    with mid_col:
        st.markdown("<div style='background-color: rgba(255, 75, 75, 0.15); padding: 12px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (Deviation &lt; -10%)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not buy_signals_df.empty:
            st.dataframe(buy_signals_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks down past the -10% buy line.")

    # Column Workspace C: Dedicated Sell Box Container
    with right_col:
        st.markdown("<div style='background-color: rgba(41, 181, 232, 0.15); padding: 12px; border-radius: 6px; border-left: 5px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (Deviation &gt; +10%)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not sell_signals_df.empty:
            st.dataframe(sell_signals_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks pumped past the +10% sell line.")
else:
    st.error("Failed to retrieve market data. Try clicking the Refresh button above.")
