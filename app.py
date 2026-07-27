import streamlit as st
import pandas as pd
import requests

# Page setup configuration
st.set_page_config(page_title="NSE F&O EMA Scanner", layout="wide")
st.title("📈 NSE F&O Institutional Strategy Dashboard")
st.write("Scans NSE F&O segments on the **Daily (1D) Timeframe** using TradingView's unblocked bulk technical engine.")

# Standardized high-liquidity F&O Ticker list formatted for TradingView's NSE Exchange routing
FO_TICKERS = [
    "ACC", "AARTIIND", "ABB", "ADANIENT", "ADANIPORTS", "APOLLOHOSP", 
    "ASIANPAINT", "AXISBANK", "BAJAJ_AUTO", "BAJFINANCE", "BAJAJFINSV", 
    "BANKBARODA", "BEL", "BHARATFORG", "BHARTIARTL", "BHEL", "BPCL", 
    "BRITANNIA", "CANBK", "CIPLA", "COALINDIA", "COFORGE", "CONCOR", 
    "DABUR", "DIVISLAB", "DIXON", "DLF", "DRREDDY", "EICHERMOT", 
    "GAIL", "GLENMARK", "GODREJCP", "GODREJPROP", "GRASIM", "HAL", 
    "HAVELLS", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", 
    "HINDALCO", "HINDUNILVR", "ICICIBANK", "ICICIGI", "IDEA", "IGL", 
    "INDHOTEL", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", 
    "IRCTC", "ITC", "JINDALSTEL", "JSWSTEEL", "KOTAKBANK", "LT", 
    "LTIM", "LUPIN", "M_M", "MARICO", "MARUTI", "MCX", "MUTHOOTFIN", 
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
def scan_markets_native_tv():
    scanned_data = []
    try:
        url = "https://tradingview.com"
        payload = {
            "symbols": {"tickers": [f"NSE:{t}" for t in FO_TICKERS], "query": {"types": []}},
            "columns": ["close", "EMA20", "change", "RSI"]
        }
        res = requests.post(url, json=payload, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if res.status_code == 200:
            json_data = res.json().get('data', [])
            for item in json_data:
                ticker = item.get('s', '').split(':')[-1]
                metrics = item.get('d', [])
                
                # Fixed: Properly unpacked columns by accessing specific list array indices safely
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
        pass
    return pd.DataFrame(scanned_data)

def get_supertrend_matrix_native(ticker_clean):
    timeframes = {"Weekly": "W", "Daily": "D", "Hourly": "60", "15 Min": "15"}
    st_row = {"Stock Name": ticker_clean, "Weekly": "⚪ NEUTRAL", "Daily": "⚪ NEUTRAL", "Hourly": "⚪ NEUTRAL", "15 Min": "⚪ NEUTRAL"}
    query_ticker = ticker_clean.replace("&", "_")
    
    url = "https://tradingview.com"
    for label, tf in timeframes.items():
        try:
            payload = {
                "symbols": {"tickers": [f"NSE:{query_ticker}"], "query": {"types": []}},
                "columns": [f"Supertrend.lower|{tf}", f"Supertrend.upper|{tf}", f"close|{tf}"]
            }
            res = requests.post(url, json=payload, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
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

with st.spinner("Executing high-speed institutional data pipelines..."):
    results_df = scan_markets_native_tv()

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
    selected_row = col_master.dataframe(display_master_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

    col_buy.markdown("<div style='background-color: rgba(255, 75, 75, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (&le; -10%)</div>", unsafe_allow_html=True)
    col_buy.markdown("<br>", unsafe_allow_html=True)
    col_buy.dataframe(buy_signals_df, use_container_width=True, hide_index=True) if not buy_signals_df.empty else col_buy.info("No stocks meet strict -10% buy deviation.")

    col_sell.markdown("<div style='background-color: rgba(41, 181, 232, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (&ge; +10%)</div>", unsafe_allow_html=True)
    col_sell.markdown("<br>", unsafe_allow_html=True)
