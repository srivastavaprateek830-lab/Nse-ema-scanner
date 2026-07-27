import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# Fix for Yahoo Finance cache location on Streamlit servers
yf.set_tz_cache_location("/tmp/yf_cache")

# Set up page configuration for an expansive 4-column layout
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

# Sector Mapping Lookup table to calculate performance values natively
TICKER_SECTORS = {
    "AXISBANK": "🏦 BANKING", "BANKBARODA": "🏦 BANKING", "CANBK": "🏦 BANKING", "HDFCBANK": "🏦 BANKING", "ICICIBANK": "🏦 BANKING", "KOTAKBANK": "🏦 BANKING", "PNB": "🏦 BANKING", "SBIN": "🏦 BANKING",
    "COFORGE": "💻 IT SECTOR", "HCLTECH": "💻 IT SECTOR", "INFY": "💻 IT SECTOR", "LTIM": "💻 IT SECTOR", "PERSISTENT": "💻 IT SECTOR", "TCS": "💻 IT SECTOR", "TECHM": "💻 IT SECTOR", "WIPRO": "💻 IT SECTOR",
    "BAJAJ-AUTO": "🚗 AUTO", "EICHERMOT": "🚗 AUTO", "HEROMOTOCO": "🚗 AUTO", "M&M": "🚗 AUTO", "MARUTI": "🚗 AUTO", "TATAMOTORS": "🚗 AUTO", "TVSMOTOR": "🚗 AUTO",
    "CIPLA": "💊 PHARMA", "DIVISLAB": "💊 PHARMA", "DRREDDY": "💊 PHARMA", "GLENMARK": "💊 PHARMA", "LUPIN": "💊 PHARMA", "SUNPHARMA": "💊 PHARMA", "TORNTPHARM": "💊 PHARMA",
    "BRITANNIA": "🛒 FMCG", "DABUR": "🛒 FMCG", "HINDUNILVR": "🛒 FMCG", "ITC": "🛒 FMCG", "NESTLEIND": "🛒 FMCG", "TATACONSUM": "🛒 FMCG",
    "HINDALCO": "🏗️ METALS", "JINDALSTEL": "🏗️ METALS", "JSWSTEEL": "🏗️ METALS", "NATIONALUM": "🏗️ METALS", "SAIL": "🏗️ METALS", "TATASTEEL": "🏗️ METALS", "VEDL": "🏗️ METALS",
    "DLF": "🏢 REALTY", "GODREJPROP": "🏢 REALTY", "OBEROIRLTY": "🏢 REALTY",
    "ADANIPORTS": "⚡ ENERGY", "BPCL": "⚡ ENERGY", "COALINDIA": "⚡ ENERGY", "GAIL": "⚡ ENERGY", "HINDPETRO": "⚡ ENERGY", "IOC": "⚡ ENERGY", "NTPC": "⚡ ENERGY", "ONGC": "⚡ ENERGY", "POWERGRID": "⚡ ENERGY", "TATAPOWER": "⚡ ENERGY"
}

# Renamed core caching function wrapper to 'force_fresh_engine_run' 
# This overrides and flushes the old stuck container errors permanently!
@st.cache_data(ttl=600)  
def force_fresh_engine_run():
    scanned_data = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    tickers_str = " ".join(FO_TICKERS)
    data = yf.download(tickers_str, period="3mo", interval="1d", group_by="ticker", progress=False, session=session)
    
    for ticker in FO_TICKERS:
        try:
            df = data[ticker].dropna() if ticker in data.columns.levels else pd.DataFrame()
            if df.empty or len(df) < 20:
                continue
                
            close_prices = df['Close']
            ema20 = close_prices.ewm(span=20, adjust=False).mean()
            
            current_price = float(close_prices.iloc[-1])
            prev_price = float(close_prices.iloc[-2])
            current_ema20 = float(ema20.iloc[-1])
            
            deviation = ((current_price - current_ema20) / current_ema20) * 100
            day_change = ((current_price - prev_price) / prev_price) * 100
            
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
                "Action": action,
                "Change": day_change
            })
        except Exception:
            continue
            
    return pd.DataFrame(scanned_data)

# One-click manual refresh button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Flushing system lanes and downloading fresh data streams..."):
    results_df = force_fresh_engine_run()

if not results_df.empty:
    # Sort entire master list by absolute largest deviation right away
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Isolate active signal matches cleanly for the side buckets
    buy_signals_df = all_sorted[all_sorted["Deviation (%)"] <= -10][["Ticker", "Price (₹)", "Deviation (%)"]]
    sell_signals_df = all_sorted[all_sorted["Deviation (%)"] >= 10][["Ticker", "Price (₹)", "Deviation (%)"]]

    # Natively calculate the Sectoral Index change using data we already downloaded
    all_sorted["Sector"] = all_sorted["Ticker"].map(TICKER_SECTORS)
    sector_summary = all_sorted.groupby("Sector", as_index=False)["Change"].mean()
    sector_summary = sector_summary.sort_values(by="Change", ascending=False)

    # Clean the primary table display by removing raw change column used for sector calculations
    display_master_df = all_sorted[["Ticker", "Price (₹)", "EMA20 (₹)", "Deviation (%)", "Action"]]

    # --- 📊 FOUR-COLUMN EXTENSIVE DESIGN LAYOUT ---
    # Width distribution proportions: Master table 50%, Buy 16%, Sell 16%, Sectors 18%
    col_master, col_buy, col_sell, col_sectors = st.columns([0.50, 0.16, 0.16, 0.18])

    # Column 1: Master Full F&O Tracker (Left Side)
    with col_master:
        st.subheader("🔍 Complete F&O Watchlist")
        st.dataframe(display_master_df, use_container_width=True, hide_index=True)

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
        
        # Render the natively computed sectors inside the right-hand container box
        for _, row in sector_summary.iterrows():
            name = row["Sector"]
            change = round(row["Change"], 2)
            
            # Apply color templates
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
