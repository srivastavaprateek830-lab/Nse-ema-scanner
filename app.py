import streamlit as st
import pandas as pd
from tradingview_ta import get_multiple_analysis, TA_Handler, Interval

# Page setup configuration for broad 4-column institutional layout
st.set_page_config(page_title="NSE F&O Dashboard", layout="wide")
st.title("📈 NSE F&O Institutional Strategy Dashboard")
st.write("Scans NSE F&O segments on the Daily (1D) Timeframe using unblocked indicator engines.")

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
# Structural Lookup mapping tickers to their respective indices
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
def scan_markets_bulk_tv():
    scanned_data = []
    try:
        bulk_analysis = get_multiple_analysis(screener="india", symbols=FO_TICKERS, interval=Interval.INTERVAL_1_DAY)
        for full_symbol, analysis in bulk_analysis.items():
            if not analysis: continue
            try:
                ticker = full_symbol.split(":")[-1]
                indicators = analysis.indicators
                current_price = float(indicators.get("close", 0.0))
                current_ema20 = float(indicators.get("EMA20", 0.0))
                day_change = float(indicators.get("change", 0.0))
                rsi14 = float(indicators.get("RSI", 50.0))
                if current_price == 0.0 or current_ema20 == 0.0: continue
                deviation = ((current_price - current_ema20) / current_ema20) * 100
                action = "🔴 BUY" if deviation <= -10.0 else ("🟢 SELL" if deviation >= 10.0 else "⚪ HOLD")
                scanned_data.append({
                    "Ticker": ticker.replace("_", "&"), "Price (₹)": round(current_price, 2),
                    "EMA20 (₹)": round(current_ema20, 2), "Deviation (%)": round(deviation, 2),
                    "RSI (14)": round(rsi14, 1), "Action": action, "Change": day_change
                })
            except: continue
    except Exception as e: st.error(f"Bulk data pipe error: {str(e)}")
    return pd.DataFrame(scanned_data)

def get_supertrend_row(ticker_clean):
    timeframes = {"Weekly": Interval.INTERVAL_1_WEEK, "Daily": Interval.INTERVAL_1_DAY, "Hourly": Interval.INTERVAL_1_HOUR, "15 Min": Interval.INTERVAL_15_MINUTES}
    st_row = {"Stock Name": ticker_clean}
    query_ticker = ticker_clean.replace("&", "_")
    for label, tf in timeframes.items():
        try:
            handler = TA_Handler(family="standard", symbol=query_ticker, exchange="NSE", screener="india", interval=tf)
            analysis = handler.get_analysis()
            st_lower = analysis.indicators.get("Supertrend.lower")
            st_upper = analysis.indicators.get("Supertrend.upper")
            close_val = analysis.indicators.get("close")
            if st_lower is not None and close_val >= st_lower: st_row[label] = "🟢 BULLISH"
            elif st_upper is not None and close_val <= st_upper: st_row[label] = "🔴 BEARISH"
            else:
                summary = analysis.summary.get("RECOMMENDATION", "")
                st_row[label] = "🟢 BULLISH" if "BUY" in summary else ("🔴 BEARISH" if "SELL" in summary else "⚪ NEUTRAL")
        except: st_row[label] = "⚪ NEUTRAL"
    return pd.DataFrame([st_row])
if st.button("🔄 Refresh Scanner Data", type="primary"): st.cache_data.clear()

with st.spinner("Executing high-speed indicator streams..."): results_df = scan_markets_bulk_tv()

if not results_df.empty:
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    buy_df = all_sorted[all_sorted["Deviation (%)"] <= -10.0][["Ticker", "Price (₹)", "Deviation (%)", "RSI (14)"]]
    sell_df = all_sorted[all_sorted["Deviation (%)"] >= 10.0][["Ticker", "Price (₹)", "Deviation (%)", "RSI (14)"]]
    all_sorted["Sector"] = all_sorted["Ticker"].map(TICKER_SECTORS)
    sector_summary = all_sorted.groupby("Sector", as_index=False)["Change"].mean().dropna().sort_values(by="Change", ascending=False)
    display_master_df = all_sorted[["Ticker", "Price (₹)", "EMA20 (₹)", "Deviation (%)", "RSI (14)", "Action"]]

    # --- 📊 MASTER FOUR-COLUMN SPACE BOUNDARIES GRID ---
    # The columns are defined first so we can route the click data to the right column immediately
    col_master, col_buy, col_sell, col_sectors = st.columns([0.46, 0.17, 0.17, 0.20])

    # Column 1: Watchlist (on_select is placed right here)
    col_master.subheader("🔍 Complete F&O Watchlist")
    selected_row = col_master.dataframe(display_master_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

    # Column 2: Buy Side Box
    col_buy.markdown("<div style='background-color: rgba(255, 75, 75, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (&le; -10%)</div><br>", unsafe_allow_html=True)
    if len(buy_df) > 0:
        col_buy.dataframe(buy_df, use_container_width=True, hide_index=True)
    else:
        col_buy.info("No stocks down.")

    # Column 3: Sell Side Box
    col_sell.markdown("<div style='background-color: rgba(41, 181, 232, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (&ge; +10%)</div><br>", unsafe_allow_html=True)
    if len(sell_df) > 0:
        col_sell.dataframe(sell_df, use_container_width=True, hide_index=True)
    else:
        col_sell.info("No stocks pumped.")


    col_sell.markdown("<div style='background-color: rgba(41, 181, 232, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (&ge; +10%)</div><br>", unsafe_allow_html=True)
    if len(sell_df) > 0:
        col_sell.dataframe(sell_df, use_container_width=True, hide_index=True)
    else:
        col_sell.info("No stocks pumped.")


    col_sectors.markdown("<div style='background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 4px; border-left: 4px solid #777777; font-weight: bold;'>⚡ Nifty Sectors Performance</div><br>", unsafe_allow_html=True)
    for _, row in sector_summary.iterrows():
        color = "#29b5e8" if row["Change"] >= 0 else "#ff4b4b"
        sign = "+" if row["Change"] >= 0 else ""
        col_sectors.markdown(f"<div style='padding: 6px; margin-bottom: 4px; border: 1px solid rgba(128,128,128,0.15); border-radius: 4px;'><span style='font-size: 12px;'>{row['Sector']}</span><span style='float: right; font-weight: bold; color: {color};'>{sign}{round(row['Change'],2)}%</span></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🎯 Live Multi-Timeframe SuperTrend Status Matrix")
    st.caption("💡 Pro-Tip: Click on any stock row in the 'Complete F&O Watchlist' table above to instantly load its SuperTrend statuses below.")
    
    sel_rows = selected_row.get('selection', {}).get('rows', [])
    active_ticker = display_master_df.iloc[sel_rows]["Ticker"] if sel_rows else "ACC"

    with st.spinner(f"Updating trend for {active_ticker}..."): 
        st_matrix_df = get_supertrend_row(active_ticker)
        
    def style_cells(v):
        if 'BULLISH' in str(v): return 'background-color: rgba(41, 181, 232, 0.2); color: #29b5e8; font-weight: bold;'
        if 'BEARISH' in str(v): return 'background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; font-weight: bold;'
        return ''
        
    if not st_matrix_df.empty:
        st.dataframe(st_matrix_df.style.map(style_cells, subset=['Weekly', 'Daily', 'Hourly', '15 Min']), use_container_width=True, hide_index=True)
    else:
        st.info("No trend data loaded.")
else:
    st.error("Market API server temporarily busy. Please click 'Refresh Scanner Data' to cycle endpoints.")
