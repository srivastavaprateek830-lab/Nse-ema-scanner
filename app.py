import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# Fix for Yahoo Finance cache location on Streamlit servers
yf.set_tz_cache_location("/tmp/yf_cache")

# Set up page configuration for an executive layout
st.set_page_config(page_title="NSE F&O Analytics Dashboard", page_icon="📈", layout="wide")
st.title("📊 NSE F&O Strategy Dashboard")
st.markdown("Monitors prominent NSE derivatives and routes extreme price expansions away from moving average baselines.")

# Comprehensive list of liquid F&O Tickers
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

@st.cache_data(ttl=600)  # Maintain standard 10-minute caching layer
def scan_markets():
    scanned_data = []
    
    # Establish persistent header session properties to look like a desktop web browser
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    })
    
    # Bundle into an initialized collection structure to separate individual downloads safely
    tickers_wrapper = yf.Tickers(" ".join(FO_TICKERS), session=session)
    
    for ticker in FO_TICKERS:
        try:
            # Safely fetch individual historical data arrays to bypass cloud blocks
            df = tickers_wrapper.tickers[ticker].history(period="3mo", interval="1d", progress=False)
            
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
        except:
            continue
            
    return pd.DataFrame(scanned_data)

# Manual data refresh button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Streaming stable market vectors... Please wait."):
    results_df = scan_markets()

if not results_df.empty:
    # Sort total values cleanly by extreme deviations
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Filter specific targets for the right-hand action buckets
    buy_box_df = all_sorted[all_sorted["Deviation (%)"] <= -10][["Ticker", "Price (₹)", "Deviation (%)"]]
    sell_box_df = all_sorted[all_sorted["Deviation (%)"] >= 10][["Ticker", "Price (₹)", "Deviation (%)"]]

    # --- 📈 LIVE TREND EXPLORER ---
    st.markdown("### 📈 Live Trend Chart View")
    selected_ticker = st.selectbox("🎯 Select a stock from the dropdown to instantly map its price trend vs EMA20:", sorted(all_sorted["Ticker"].unique()))
    
    if selected_ticker:
        try:
            # Fetch historical pricing array for chart visualization
            chart_df = yf.download(f"{selected_ticker}.NS", period="3mo", interval="1d", progress=False)
            if not chart_df.empty:
                chart_df['EMA20 Line'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
                plot_data = pd.DataFrame({'Close Price': chart_df['Close'], 'EMA20 Baseline': chart_df['EMA20 Line']}, index=chart_df.index)
                st.line_chart(plot_data, y=["Close Price", "EMA20 Baseline"])
        except Exception:
            st.caption("Chart data feed busy. Select another symbol.")

    st.markdown("---")

    # --- 📊 TWO-COLUMN USER INTERFACE LAYOUT ---
    left_col, right_col = st.columns([3, 2]) # 60% Width Left side, 40% Width Right side

    # Left Column Workspace: Master Watchlist Data Grid
    with left_col:
        st.subheader("🔍 Complete F&O Watchlist Deviation")
        st.dataframe(all_sorted, use_container_width=True, hide_index=True)

    # Right Column Workspace: Action Signal Box Targets
    with right_col:
        st.subheader("🛒 Breakout Target Buckets")
        
        # Upper Container Element: Dynamic Buy Routing Panel Box
        st.markdown("<div style='background-color: rgba(255, 75, 75, 0.15); padding: 12px; border-radius: 6px; border-left: 5px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (Deviation &lt; -10%)</div>", unsafe_allow_html=True)
        if not buy_box_df.empty:
            st.dataframe(buy_box_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently meet the -10% buy threshold criteria.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Lower Container Element: Dynamic Sell Routing Panel Box
        st.markdown("<div style='background-color: rgba(41, 181, 232, 0.15); padding: 12px; border-radius: 6px; border-left: 5px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (Deviation &gt; +10%)</div>", unsafe_allow_html=True)
        if not sell_box_df.empty:
            st.dataframe(sell_box_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently meet the +10% sell threshold criteria.")
else:
    st.error("Market data pipeline empty. Click the Refresh button above to retry the server connection.")
