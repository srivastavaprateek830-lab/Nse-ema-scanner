import streamlit as st
import yfinance as yf
import pandas as pd

# Set up page configuration
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O EMA20 Deviation Scanner")
st.write("Scans NSE F&O stocks for price deviations (>10% or <-10%) from the 20-period EMA.")

# List of 180+ current NSE F&O Tickers (Appended with .NS for Yahoo Finance)
FO_TICKERS = [
    "ACC.NS", "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", 
    "ADANIENT.NS", "ADANIPORTS.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", 
    "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", 
    "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", 
    "BAJAJFINSV.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", 
    "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", 
    "BIOCON.NS", "BOSCHLTD.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANFINHOME.NS", 
    "CANBK.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", 
    "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS", "CROMPTON.NS", 
    "CUB.NS", "CUMMINSIND.NS", "CYIENT.NS", "DABUR.NS", "DALBHARAT", "DEEPAKNTR.NS", 
    "DELHIVERY.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", 
    "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", 
    "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", 
    "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", 
    "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HCOPPER.NS", "HINDPETRO.NS", 
    "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDEA.NS", 
    "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", 
    "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", 
    "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", 
    "JUBLFOOD.NS", "KALYANKJIL.NS", "KOTAKBANK.NS", "L&TFH.NS", "LT.NS", "LTIM.NS", 
    "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", 
    "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", 
    "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", 
    "NAVINFLUOR.NS", "NAUKRI.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", 
    "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", 
    "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", 
    "RAMCOCEM.NS", "RBLBANK.NS", "REC.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", 
    "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SHRIRAMFIN.NS", "SIEMENS.NS", "SRF.NS", 
    "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACHEMICAL.NS", "TATACOMM.NS", 
    "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", 
    "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TORNTPOWER.NS", "TRENT.NS", "TVSMOTOR.NS", 
    "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS"
]

@st.cache_data(ttl=600)  # Caches results for 10 minutes to maintain speed
def scan_markets():
    scanned_data = []
    
    # Download data in bulk for efficiency
    tickers_str = " ".join(FO_TICKERS)
    data = yf.download(tickers_str, period="3m", interval="1d", group_by="ticker", progress=False)
    
    for ticker in FO_TICKERS:
        try:
            # Extract ticker specific dataframe
            df = data[ticker].dropna() if ticker in data.columns.levels[0] else pd.DataFrame()
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
    # Filter for signals matching your criteria
    filtered_df = results_df[results_df["Deviation (%)"].abs() >= 10]
    
    # Sort by the absolute largest deviation
    filtered_df = filtered_df.reindex(filtered_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Display Key Statistics Cards
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
        
    # Section to look at all stocks anyway
    with st.expander("🔍 View Complete F&O Watchlist Deviation"):
        all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
        st.dataframe(all_sorted, use_container_width=True, hide_index=True)
else:
    st.error("Failed to retrieve market data. Please verify your internet connection.")
