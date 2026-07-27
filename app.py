import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# Fix for Yahoo Finance cache location on Streamlit servers
yf.set_tz_cache_location("/tmp/yf_cache")

# Set up page configuration for an expansive grid layout
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O EMA20 Deviation Scanner")
st.write("Scans NSE F&O stocks for price deviations (>10% or <-10%) from the 20-period EMA.")

# Curated list of high-liquidity NSE F&O Tickers
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

@st.cache_data(ttl=600)  # Caches results for 10 minutes to maintain stability
def scan_markets():
    scanned_data = []
    
    # Formulate a clean browser session to keep yfinance downloads running smoothly
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Process individual loops to prevent bulk connection dropping blocks
    for ticker in FO_TICKERS:
        try:
            df = yf.download(ticker, period="3mo", interval="1d", progress=False, session=session, show_errors=False)
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

@st.cache_data(ttl=600)
def fetch_sectoral_matrix():
    """Queries open web structures on Google Finance to obtain index performance metrics safely."""
    sectors = {
        "BANKING": "BANKNIFTY", "IT SECTOR": "NIFTYIT", "AUTOMOBILE": "NIFTYAUTO",
        "PHARMA": "NIFTYPHARMA", "FMCG": "NIFTYFMCG", "METALS": "NIFTYMETAL",
        "REALTY": "NIFTYREALTY", "ENERGY": "NIFTYENERGY"
    }
    perf_list = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for label, sym in sectors.items():
        try:
            url = f"https://google.com{sym}:INDEXNSE"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200 and 'data-price-change-percentage="' in res.text:
                raw_pct = res.text.split('data-price-change-percentage="')[1].split('"')[0]
                change = round(float(raw_pct), 2)
                perf_list.append({"Sector": label, "Change (%)": change})
        except:
            continue
            
    if not perf_list:
        return pd.DataFrame([{"Sector": k, "Change (%)": 0.0} for k in sectors.keys()])
    return pd.DataFrame(perf_list).sort_values(by="Change (%)", ascending=False)

# One-click manual refresh button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Streaming safe institutional data tracks... This takes a few seconds."):
    results_df = scan_markets()
    sector_df = fetch_sectoral_matrix()

if not results_df.empty:
    # Sort entire master list by absolute largest deviation right away
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Isolate active signal matches cleanly for the side buckets
    buy_signals_df = all_sorted[all_sorted["Deviation (%)"] <= -10][["Ticker", "Price (₹)", "Deviation (%)"]]
    sell_signals_df = all_sorted[all_sorted["Deviation (%)"] >= 10][["Ticker", "Price (₹)", "Deviation (%)"]]

    # --- 📊 FOUR-COLUMN EXTENSIVE DESIGN LAYOUT ---
    # Width distribution proportions: Master table 50%, Buy 16%, Sell 16%, Sectors 18%
    col_master, col_buy, col_sell, col_sectors = st.columns([0.50, 0.16, 0.16, 0.18])

    # Column 1: Master Full F&O Tracker (Left Side)
    with col_master:
        st.subheader("🔍 Complete F&O Watchlist")
        st.dataframe(all_sorted, use_container_width=True, hide_index=True)

    # Column 2: Buy Side Box Panel (Middle Left)
    with col_buy:
        st.markdown("<div style='background-color: rgba(255, 75, 75, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (&lt; -10%)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not buy_signals_df.empty:
            st.dataframe(buy_signals_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks down past the -10% buy line.")

    # Column 3: Sell Side Box Panel (Middle Right)
    with col_sell:
        st.markdown("<div style='background-color: rgba(41, 181, 232, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (&gt; +10%)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not sell_signals_df.empty:
            st.dataframe(sell_signals_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks pumped past the +10% sell line.")

    # Column 4: Dedicated Sector Performance Panel (Far Right Side)
    with col_sectors:
        st.markdown("<div style='background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 4px; border-left: 4px solid #777777; font-weight: bold;'>⚡ Nifty Sectors Performance</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Format styled list values into individual color-coded rows inside the panel
        for _, row in sector_df.iterrows():
            name = row["Sector"]
            change = row["Change (%)"]
            
            # Dynamic cyan/red indicator font text values based on status
            color = "#29b5e8" if change >= 0 else "#ff4b4b"
            sign = "+" if change >= 0 else ""
            
            st.markdown(
                f"<div style='padding: 8px; margin-bottom: 6px; border: 1px solid rgba(128,128,128,0.15); border-radius: 4px; background-color: rgba(255,255,255,0.01);'>"
                f"<span style='font-size: 13px; font-weight: 500;'>{name}</span>"
                f"<span style='float: right; font-weight: bold; color: {color};'>{sign}{change}%</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
else:
    st.error("Failed to retrieve market data. Try clicking the Refresh button above.")
