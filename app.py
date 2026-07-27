import streamlit as st
import pandas as pd
import requests

# Set up page configuration for an expansive 4-column layout
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O EMA20 Deviation Scanner")
st.write("Scans NSE F&O stocks for price deviations (>10% or <-10%) from the 20-period EMA.")

# List of prominent NSE F&O Tickers
FO_TICKERS = [
    "ACC", "AARTIIND", "ABB", "ADANIENT", "ADANIPORTS", "APOLLOHOSP", 
    "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", 
    "BANKBARODA", "BEL", "BHARATFORG", "BHARTIARTL", "BHEL", "BPCL", 
    "BRITANNIA", "CANBK", "CIPLA", "COALINDIA", "COFORGE", "CONCOR", 
    "DABUR", "DIVISLAB", "DIXON", "DLF", "DRREDDY", "EICHERMOT", 
    "GAIL", "GLENMARK", "GODREJCP", "GODREJPROP", "GRASIM", "HAL", 
    "HAVELLS", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", 
    "HINDALCO", "HINDUNILVR", "ICICIBANK", "ICICIGI", "IDEA", "IGL", 
    "INDHOTEL", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", 
    "IRCTC", "ITC", "JINDALSTEL", "JSWSTEEL", "KOTAKBANK", "LT", 
    "LTIM", "LUPIN", "M&M", "MARICO", "MARUTI", "MCX", "MUTHOOTFIN", 
    "NATIONALUM", "NAUKRI", "NESTLEIND", "NMDC", "NTPC", "ONGC", 
    "PERSISTENT", "PFC", "PIDILITIND", "PNB", "POLYCAB", "POWERGRID", 
    "REC", "RELIANCE", "SAIL", "SBICARD", "SBILIFE", "SBIN", 
    "SHRIRAMFIN", "SIEMENS", "SRF", "SUNPHARMA", "TATACHEMICAL", 
    "TATACOMM", "TATACONSUM", "TATAMOTORS", "TATAPOWER", "TATASTEEL", 
    "TCS", "TECHM", "TITAN", "TORNTPHARM", "TRENT", "TVSMOTOR", 
    "ULTRACEMCO", "UPL", "VEDL", "VOLTAS", "WIPRO", "ZEEL"
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

@st.cache_data(ttl=600)  # Caches results for 10 minutes to protect api traffic lanes
def scan_markets_unblocked():
    scanned_data = []
    
    # Establish persistent header session
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    
    # Visual loading bar directly inside the Streamlit user interface
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_tickers = len(FO_TICKERS)
    
    for index, ticker in enumerate(FO_TICKERS):
        try:
            status_text.text(f"Scanning data feed: {ticker} ({index + 1}/{total_tickers})...")
            progress_bar.progress((index + 1) / total_tickers)
            
            # Request historical data from the highly reliable unthrottled public charting API
            api_url = f"https://moneycontrol.com{ticker}&resolution=D&from=1577836800&to=2147483647"
            res = session.get(api_url, timeout=10)
            
            if res.status_code == 200:
                json_data = res.json()
                if 'c' in json_data and json_data['c']:
                    close_prices = json_data['c']  # Extract array of daily closing prices
                    
                    if len(close_prices) >= 20:
                        df_close = pd.Series(close_prices)
                        
                        # Calculate exact 20-period Exponential Moving Average (EMA20)
                        ema20_series = df_close.ewm(span=20, adjust=False).mean()
                        
                        current_price = float(df_close.iloc[-1])
                        prev_price = float(df_close.iloc[-2])
                        current_ema20 = float(ema20_series.iloc[-1])
                        
                        deviation = ((current_price - current_ema20) / current_ema20) * 100
                        day_change = ((current_price - prev_price) / prev_price) * 100
                        
                        if deviation <= -10:
                            action = "🔴 BUY (Undervalued)"
                        elif deviation >= 10:
                            action = "🟢 SELL (Overvalued)"
                        else:
                            action = "⚪ HOLD / NEUTRAL"
                            
                        scanned_data.append({
                            "Ticker": ticker,
                            "Price (₹)": round(current_price, 2),
                            "EMA20 (₹)": round(current_ema20, 2),
                            "Deviation (%)": round(deviation, 2),
                            "Action": action,
                            "Change": day_change
                        })
        except:
            continue
            
    # Clear visual status updates upon completion
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(scanned_data)

# Manual data refresh button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Connecting to public market API streams..."):
    results_df = scan_markets_unblocked()

if not results_df.empty:
    # Sort entire master list by absolute largest deviation right away
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Isolate active buy and sell signal matches cleanly for the side buckets
    buy_signals_df = all_sorted[all_sorted["Deviation (%)"] <= -10][["Ticker", "Price (₹)", "Deviation (%)"]]
    sell_signals_df = all_sorted[all_sorted["Deviation (%)"] >= 10][["Ticker", "Price (₹)", "Deviation (%)"]]

    # Calculate the Sectoral Index change using data we already downloaded natively
    all_sorted["Sector"] = all_sorted["Ticker"].map(TICKER_SECTORS)
    sector_summary = all_sorted.groupby("Sector", as_index=False)["Change"].mean()
    sector_summary = sector_summary.dropna().sort_values(by="Change", ascending=False)

    # Prepare master list table view
    display_master_df = all_sorted[["Ticker", "Price (₹)", "EMA20 (₹)", "Deviation (%)", "Action"]]

    # --- 📊 FOUR-COLUMN EXTENSIVE DESIGN LAYOUT ---
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
    st.error("Market API server temporarily busy. Please click 'Refresh Scanner Data' to cycle endpoints.")
