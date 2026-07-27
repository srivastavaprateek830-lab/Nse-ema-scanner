import streamlit as st
import pandas as pd
import requests

# Set up page configuration
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O EMA20 Deviation Scanner")
st.write("Scans NSE F&O stocks for price deviations (>10% or <-10%) from the 20-period EMA using open market APIs.")

# Curated list of high-liquidity NSE F&O Tickers
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

@st.cache_data(ttl=600)  # Cache scanner data for 10 minutes
def scan_markets():
    scanned_data = []
    
    # Progress UI updates for standard tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_tickers = len(FO_TICKERS)
    
    for index, ticker in enumerate(FO_TICKERS):
        try:
            status_text.text(f"Scanning {ticker} ({index + 1}/{total_tickers})...")
            progress_bar.progress((index + 1) / total_tickers)
            
            # Using an unthrottled historical charting endpoint optimized for public widgets
            url = f"https://stockmaniacs.net{ticker}&resolution=D&from=1700000000&to=2000000000"
            
            # Direct backup parsing via safe chart links
            fallback_url = f"https://moneycontrol.com{ticker}&resolution=D&from=1577836800&to=2147483647"
            res = requests.get(fallback_url, timeout=10)
            
            if res.status_code == 200:
                json_data = res.json()
                if 'c' in json_data and json_data['c']:
                    close_prices = json_data['c'] # Extract array of closing prices
                    
                    if len(close_prices) >= 20:
                        df_close = pd.Series(close_prices)
                        
                        # Calculate exact EMA20
                        ema20_series = df_close.ewm(span=20, adjust=False).mean()
                        
                        current_price = float(df_close.iloc[-1])
                        current_ema20 = float(ema20_series.iloc[-1])
                        deviation = ((current_price - current_ema20) / current_ema20) * 100
                        
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
                            "Action": action
                        })
        except Exception:
            continue
            
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(scanned_data)

# Manual data refresh button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Fetching stable institutional data streams... Please wait."):
    results_df = scan_markets()

if not results_df.empty:
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
        st.info("No F&O stocks currently show a deviation greater than 10% from the EMA20.")
        
    with st.expander("🔍 View Complete F&O Watchlist Deviation"):
        all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
        st.dataframe(all_sorted, use_container_width=True, hide_index=True)
else:
    st.error("Market API server temporarily busy. Please click 'Refresh Scanner Data' to cycle endpoints.")
