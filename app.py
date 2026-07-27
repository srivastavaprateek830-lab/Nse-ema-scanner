import streamlit as st
import pandas as pd
import requests

# Page setup configuration
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O Institutional Strategy Dashboard")
st.write("Scans NSE F&O segments on the **Daily (1D) Timeframe** using TradingView's bulk technical engine.")

# Standardized high-liquidity F&O Ticker list formatted for TradingView's NSE Exchange routing
FO_TICKERS = [
    "NSE:ACC", "NSE:AARTIIND", "NSE:ABB", "NSE:ADANIENT", "NSE:ADANIPORTS", "NSE:APOLLOHOSP", 
    "NSE:ASIANPAINT", "NSE:AXISBANK", "NSE:BAJAJ_AUTO", "NSE:BAJFINANCE", "NSE:BAJAJFINSV", 
    "NSE:BANKBARODA", "NSE:BEL", "NSE:BHARATFORG", "NSE:BHARTIARTL", "NSE:BHEL", "NSE:BPCL", 
    "NSE:BRITANNIA", "NSE:CANBK", "NSE:CIPLA", "NSE:COALINDIA", "NSE:COFORGE", "NSE:CONCOR", 
    "NSE:DABUR", "NSE:DIVISLAB", "NSE:DIXON", "NSE:DLF", "NSE:DRREDDY", "NSE:EICHERMOT", 
    "NSE:GAIL", "NSE:GLENMARK", "NSE:GODREJCP", "NSE:GODREJPROP", "NSE:GRASIM", "NSE:HAL", 
    "NSE:HAVELLS", "NSE:HCLTECH", "NSE:HDFCBANK", "NSE:HDFCLIFE", "NSE:HEROMOTOCO", 
    "NSE:HINDALCO", "NSE:HINDUNILVR", "NSE:ICICIBANK", "NSE:ICICIGI", "NSE:IDEA", "NSE:IGL", 
    "NSE:INDHOTEL", "NSE:INDIGO", "NSE:INDUSINDBK", "NSE:INDUSTOWER", "NSE:INFY", "NSE:IOC", 
    "NSE:IRCTC", "NSE:ITC", "NSE:JINDALSTEL", "NSE:JSWSTEEL", "NSE:KOTAKBANK", "NSE:LT", 
    "NSE:LTIM", "NSE:LUPIN", "NSE:M_M", "NSE:MARICO", "NSE:MARUTI", "NSE:MCX", "NSE:MUTHOOTFIN", 
    "NSE:NATIONALUM", "NSE:NAUKRI", "NSE:NESTLEIND", "NSE:NMDC", "NSE:NTPC", "NSE:ONGC", 
    "NSE:PERSISTENT", "NSE:PFC", "NSE:PIDILITIND", "NSE:PNB", "NSE:POLYCAB", "NSE:POWERGRID", 
    "NSE:REC", "NSE:RELIANCE", "NSE:SAIL", "NSE:SBICARD", "NSE:SBILIFE", "NSE:SBIN", 
    "NSE:SHRIRAMFIN", "NSE:SIEMENS", "NSE:SRF", "NSE:SUNPHARMA", "NSE:TATACHEMICAL", 
    "NSE:TATACOMM", "NSE:TATACONSUM", "NSE:TATAMOTORS", "NSE:TATAPOWER", "NSE:TATASTEEL", 
    "NSE:TCS", "NSE:TECHM", "NSE:TITAN", "NSE:TORNTPHARM", "NSE:TRENT", "NSE:TVSMOTOR", 
    "NSE:ULTRACEMCO", "NSE:UPL", "NSE:VEDL", "NSE:VOLTAS", "NSE:WIPRO", "NSE:ZEEL"
]

# Sector Mapping Lookup table to calculate performance values natively
TICKER_SECTORS = {
    "ACC": "🏗️ MATERIALS", "AARTIIND": "💊 PHARMA", "ABB": "🏗️ MATERIALS", "ADANIENT": "⚡ ENERGY", "ADANIPORTS": "⚡ ENERGY", "APOLLOHOSP": "💊 PHARMA",
    "ASIANPAINT": "🛒 FMCG", "AXISBANK": "🏦 BANKING", "BAJAJ_AUTO": "🚗 AUTO", "BAJFINANCE": "🏦 BANKING", "BAJAJFINSV": "🏦 BANKING",
    "BANKBARODA": "🏦 BANKING", "BEL": "💻 IT SECTOR", "BHARATFORG": "🚗 AUTO", "BHARTIARTL": "💻 IT SECTOR", "BHEL": "⚡ ENERGY", "BPCL": "⚡ ENERGY",
    "BRITANNIA": "🛒 FMCG", "CANBK": "🏦 BANKING", "CIPLA": "💊 PHARMA", "COALINDIA": "⚡ ENERGY", "COFORGE": "💻 IT SECTOR", "CONCOR": "⚡ ENERGY",
    "DABUR": "🛒 FMCG", "DIVISLAB": "💊 PHARMA", "DIXON": "💻 IT SECTOR", "DLF": "🏢 REALTY", "DRREDDY": "💊 PHARMA", "EICHERMOT": "🚗 AUTO",
    "GAIL": "⚡ ENERGY", "GLENMARK": "💊 PHARMA", "GODREJCP": "🛒 FMCG", "GODREJPROP": "🏢 REALTY", "GRASIM": "🏗️ MATERIALS", "HAL": "🏗️ MATERIALS",
    "HAVELLS": "🏗️ MATERIALS", "HCLTECH": "💻 IT SECTOR", "HDFCBANK": "🏦 BANKING", "HDFCLIFE": "🏦 BANKING", "HEROMOTOCO": "🚗 AUTO",
    "HINDALCO": "🏗️ METALS", "HINDUNILVR": "🛒 FMCG", "ICICIBANK": "🏦 BANKING", "ICICIGI": "🏦 BANKING", "IDEA": "💻 IT SECTOR", "IGL": "⚡ ENERGY",
    "INDHOTEL": "🛒 FMCG", "INDIGO": "🚗 AUTO", "INDUSINDBK": "🏦 BANKING", "INDUSTOWER": "💻 IT SECTOR", "INFY": "💻 IT SECTOR", "IOC": "⚡ ENERGY",
    "IRCTC": "🛒 FMCG", "ITC": "🛒 FMCG", "JINDALSTEL": "🏗️ METALS", "JSWSTEEL": "🏗️ METALS", "KOTAKBANK": "🏦 BANKING", "LT": "🏗️ MATERIALS",
    "LTIM": "💻 IT SECTOR", "LUPIN": "💊 PHARMA", "M_M": "🚗 AUTO", "MARICO": "🛒 FMCG", "MARUTI": "🚗 AUTO", "MCX": "🏦 BANKING", "MUTHOOTFIN": "🏦 BANKING",
    "NATIONALUM": "🏗️ METALS", "NAUKRI": "💻 IT SECTOR", "NESTLEIND": "🛒 FMCG", "NMDC": "🏗️ METALS", "NTPC": "⚡ ENERGY", "ONGC": "⚡ ENERGY",
    "PERSISTENT": "💻 IT SECTOR", "PFC": "🏦 BANKING", "PIDILITIND": "🛒 FMCG", "PNB": "🏦 BANKING", "POLYCAB": "🏗️ MATERIALS", "POWERGRID": "⚡ ENERGY",
    "REC": "🏦 BANKING", "RELIANCE": "⚡ ENERGY", "SAIL": "🏗️ METALS", "SBICARD": "🏦 BANKING", "SBILIFE": "🏦 BANKING", "SBIN": "🏦 BANKING",
    "SHRIRAMFIN": "🏦 BANKING", "SIEMENS": "🏗️ MATERIALS", "SRF": "🏗️ MATERIALS", "SUNPHARMA": "💊 PHARMA", "TATACHEMICAL": "🏗️ MATERIALS",
    "TATACOMM": "💻 IT SECTOR", "TATACONSUM": "🛒 FMCG", "TATAMOTORS": "🚗 AUTO", "TATAPOWER": "⚡ ENERGY", "TATASTEEL": "🏗️ METALS",
    "TCS": "💻 IT SECTOR", "TECHM": "💻 IT SECTOR", "TITAN": "🛒 FMCG", "TORNTPHARM": "💊 PHARMA", "TRENT": "🛒 FMCG", "TVSMOTOR": "🚗 AUTO",
    "ULTRACEMCO": "🏗️ MATERIALS", "UPL": "🏗️ MATERIALS", "VEDL": "🏗️ METALS", "VOLTAS": "🏗️ MATERIALS", "WIPRO": "💻 IT SECTOR", "ZEEL": "🛒 FMCG"
}

@st.cache_data(ttl=300)
def scan_markets_bulk_tv_native():
    scanned_data = []
    try:
        url = "https://tradingview.com"
        
        # Fixed: Added the compulsory 'range' dimensions payload array structure to satisfy TV servers
        payload = {
            "symbols": {"tickers": FO_TICKERS, "query": {"types": []}},
            "columns": ["close", "EMA20", "change", "RSI"],
            "range": [0, 150]
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            json_data = res.json().get('data', [])
            for item in json_data:
                ticker = item.get('s', '').split(':')[-1]
                metrics = item.get('d', [])
                
                if len(metrics) >= 4:
                    current_price = float(metrics[0]) if metrics[0] is not None else 0.0
                    current_ema20 = float(metrics[1]) if metrics[1] is not None else 0.0
                    day_change = float(metrics[2]) if metrics[2] is not None else 0.0
                    rsi14 = float(metrics[3]) if metrics[3] is not None else 50.0
                    
                    if current_price == 0.0 or current_ema20 == 0.0:
                        continue
                        
                    deviation = ((current_price - current_ema20) / current_ema20) * 100
                    action = "🔴 BUY" if deviation <= -10.0 else ("🟢 SELL" if deviation >= 10.0 else "⚪ HOLD")
                    
                    scanned_data.append({
                        "Ticker": ticker.replace("_", "&"),
                        "Price (₹)": round(current_price, 2),
                        "EMA20 (₹)": round(current_ema20, 2),
                        "Deviation (%)": round(deviation, 2),
                        "RSI (14)": round(rsi14, 1),
                        "Action": action,
                        "Change": day_change
                    })
    except Exception as e:
        st.error(f"Bulk data pipe error: {str(e)}")
    return pd.DataFrame(scanned_data)

def get_supertrend_matrix_native(ticker_clean):
    timeframes = {"Weekly": "W", "Daily": "D", "Hourly": "60", "15 Min": "15"}
    st_row = {"Stock Name": ticker_clean, "Weekly": "⚪ NEUTRAL", "Daily": "⚪ NEUTRAL", "Hourly": "⚪ NEUTRAL", "15 Min": "⚪ NEUTRAL"}
    query_ticker = ticker_clean.replace("&", "_")
    
    url = "https://tradingview.com"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    tickers_list = [f"NSE:{query_ticker}"]
    for label, tf in timeframes.items():
        try:
            payload = {
                "symbols": {"tickers": tickers_list, "query": {"types": []}},
                "columns": [f"Supertrend.lower|{tf}", f"Supertrend.upper|{tf}", f"close|{tf}"],
                "range": [0, 1]
            }
            res = requests.post(url, json=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                data_block = res.json().get('data', [])
                if data_block:
                    metrics = data_block[0].get('d', [])
                    if len(metrics) >= 3:
                        st_lower = metrics[0]
                        st_upper = metrics[1]
                        close_val = float(metrics[2]) if metrics[2] is not None else 0.0
                        
                        if st_lower is not None and close_val >= float(st_lower):
                            st_row[label] = "🟢 BULLISH"
                        elif st_upper is not None and close_val <= float(st_upper):
                            st_row[label] = "🔴 BEARISH"
        except:
            continue
    return pd.DataFrame([st_row])

if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Executing high-speed institutional indicators tracking streams..."):
    results_df = scan_markets_bulk_tv_native()

if not results_df.empty:
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    buy_signals_df = all_sorted[all_sorted["Deviation (%)"] <= -10.0][["Ticker", "Price (₹)", "Deviation (%)", "RSI (14)"]]
    sell_signals_df = all_sorted[all_sorted["Deviation (%)"] >= 10.0][["Ticker", "Price (₹)", "Deviation (%)", "RSI (14)"]]
    all_sorted["Sector"] = all_sorted["Ticker"].map(TICKER_SECTORS)
    sector_summary = all_sorted.groupby("Sector", as_index=False)["Change"].mean().dropna().sort_values(by="Change", ascending=False)
    display_master_df = all_sorted[["Ticker", "Price (₹)", "EMA20 (₹)", "Deviation (%)", "RSI (14)", "Action"]]

    # --- 📊 MASTER FOUR-COLUMN SPACE BOUNDARIES GRID ---
    col_master, col_buy, col_sell, col_sectors = st.columns([0.48, 0.17, 0.17, 0.18])

    col_master.subheader("🔍 Complete F&O Watchlist")
    selected_row = col_master.dataframe(
        display_master_df, 
        use_container_width=True, 
        hide_index=True, 
        on_select="rerun", 
        selection_mode="single-row"
    )

