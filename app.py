import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

# Set up page configuration
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O EMA20 Deviation Scanner")
st.write("Scans NSE F&O stocks for price deviations (>10% or <-10%) from the 20-period EMA.")

# Curated list of major liquid NSE F&O Tickers
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

@st.cache_data(ttl=600)  # Cache scanner data for 10 minutes
def scan_markets():
    scanned_data = []
    
    # Establish persistent header session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    })
    
    # Visual loading bar directly inside the Streamlit user interface
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_tickers = len(FO_TICKERS)
    
    for index, ticker in enumerate(FO_TICKERS):
        try:
            status_text.text(f"Processing {ticker} ({index + 1}/{total_tickers})...")
            progress_bar.progress((index + 1) / total_tickers)
            
            # Request ticker data with an attached browser agent session
            stock = yf.Ticker(ticker, session=session)
            df = stock.history(period="3m", interval="1d")
            
            if df.empty or len(df) < 20:
                continue
                
            # Calculate 20-period Exponential Moving Average (EMA20)
            close_prices = df['Close']
            ema20 = close_prices.ewm(span=20, adjust=False).mean()
            
            current_price = float(close_prices.iloc[-1])
            current_ema20 = float(ema20.iloc[-1])
            
            # Calculate percentage deviation
            deviation = ((current_price - current_ema20) / current_ema20) * 100
            
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
            
            # Minute anti-throttling safety pause
            time.sleep(0.05)
            
        except Exception:
            continue
            
    # Clear visual status updates upon completion
    status_text.empty()
    progress_bar.empty()
    
    return pd.DataFrame(scanned_data)

# Manual data refresh button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

results_df = scan_markets()

if not results_df.empty:
    # Filter targets displaying high deviations
    filtered_df = results_df[results_df["Deviation (%)"].abs() >= 10]
    filtered_df = filtered_df.reindex(filtered_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    buy_count = len(filtered_df[filtered_df["Deviation (%)"] <= -10])
    sell_count = len(filtered_df[filtered_df["Deviation (%)"] >= 10])
    
    col1, col2 = st.columns(2)
    col1.metric("Total BUY Signals (< -10%)", buy_count)
    col2.metric("Total SELL Signals (> +10%)", sell_count)
    
    st.subheader("🎯 Triggered Trading Signals")
    if not filtered_df.empty:
        st.dataframe(
            filtered_df.style.map(
                lambda val: 'background-color: #ffcccc; color: black;' if 'BUY' in str(val) 
                else ('background-color: #ccffcc; color: black;' if 'SELL' in str(val) else ''),
                subset=['Action']
            ), 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No stocks currently show a deviation greater than 10% from the EMA20.")
        
    with st.expander("🔍 View Complete F&O Watchlist Deviation"):
        all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
        st.dataframe(all_sorted, use_container_width=True, hide_index=True)
else:
    st.error("No market data recovered. Try clicking 'Refresh Scanner Data' to clear the cloud connection cache.")
