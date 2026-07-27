import streamlit as st
import pandas as pd
from tradingview_ta import get_multiple_analysis, TA_Handler, Interval

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
def scan_markets_bulk_tv():
    scanned_data = []
    try:
        bulk_analysis = get_multiple_analysis(screener="india", symbols=FO_TICKERS, interval=Interval.INTERVAL_1_DAY)
        for full_symbol, analysis in bulk_analysis.items():
            if not analysis:
                continue
            try:
                ticker = full_symbol.split(":")
                indicators = analysis.indicators
                current_price = float(indicators.get("close", 0.0))
                current_ema20 = float(indicators.get("EMA20", 0.0))
                day_change = float(indicators.get("change", 0.0))
                rsi14 = float(indicators.get("RSI", 50.0))
                if current_price == 0.0 or current_ema20 == 0.0:
                    continue
                deviation = ((current_price - current_ema20) / current_ema20) * 100
                if deviation <= -10.0:
                    action = "🔴 BUY"
                elif deviation >= 10.0:
                    action = "🟢 SELL"
                else:
                    action = "⚪ HOLD"
                scanned_data.append({
                    "Ticker": ticker[1].replace("_", "&"),
                    "Price (₹)": round(current_price, 2),
                    "EMA20 (₹)": round(current_ema20, 2),
                    "Deviation (%)": round(deviation, 2),
                    "RSI (14)": round(rsi14, 1),
                    "Action": action,
                    "Change": day_change
                })
            except:
                continue
    except Exception as e:
        st.error(f"Bulk data pipe error: {str(e)}")
    return pd.DataFrame(scanned_data)

def get_supertrend_row(ticker_clean):
    timeframes = {
        "Weekly": Interval.INTERVAL_1_WEEK,
        "Daily": Interval.INTERVAL_1_DAY,
        "Hourly": Interval.INTERVAL_1_HOUR,
        "15 Min": Interval.INTERVAL_15_MINUTES
    }
    st_row = {"Stock Name": ticker_clean}
    query_ticker = ticker_clean.replace("&", "_")
    for label, tf in timeframes.items():
        try:
            handler = TA_Handler(family="standard", symbol=query_ticker, exchange="NSE", screener="india", interval=tf)
            analysis = handler.get_analysis()
            st_lower = analysis.indicators.get("Supertrend.lower")
            st_upper = analysis.indicators.get("Supertrend.upper")
            close_val = analysis.indicators.get("close")
            if st_lower is not None and close_val >= st_lower:
                st_row[label] = "🟢 BULLISH"
            elif st_upper is not None and close_val <= st_upper:
                st_row[label] = "🔴 BEARISH"
            else:
                summary = analysis.summary.get("RECOMMENDATION", "")
                st_row[label] = "🟢 BULLISH" if "BUY" in summary else ("🔴 BEARISH" if "SELL" in summary else "⚪ NEUTRAL")
        except:
            st_row[label] = "⚪ NEUTRAL"
    return pd.DataFrame([st_row])

if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Executing high-speed indicators tracking streams..."):
    results_df = scan_markets_bulk_tv()

if not results_df.empty:
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    buy_signals_df = all_sorted[all_sorted["Deviation (%)"] <= -10.0][["Ticker", "Price (₹)", "Deviation (%)", "RSI (14)"]]
    sell_signals_df = all_sorted[all_sorted["Deviation (%)"] >= 10.0][["Ticker", "Price (₹)", "Deviation (%)", "RSI (14)"]]
    all_sorted["Sector"] = all_sorted["Ticker"].map(TICKER_SECTORS)
    sector_summary = all_sorted.groupby("Sector", as_index=False)["Change"].mean().dropna().sort_values(by="Change", ascending=False)
    display_master_df = all_sorted[["Ticker", "Price (₹)", "EMA20 (₹)", "Deviation (%)", "RSI (14)", "Action"]]

    # --- 📊 MASTER FOUR-COLUMN SPACE BOUNDARIES GRID ---
    # Flat design: Columns are created here and populated directly, avoiding 'with' indentation entirely
    col_master, col_buy, col_sell, col_sectors = st.columns([0.48, 0.17, 0.17, 0.18])

    col_master.subheader("🔍 Complete F&O Watchlist")
    selected_row = col_master.dataframe(
        display_master_df, 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    col_buy.markdown("<div style='background-color: rgba(255, 75, 75, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (&le; -10%)</div>", unsafe_allow_html=True)
    col_buy.markdown("<br>", unsafe_allow_html=True)
    if not buy_signals_df.empty:
        col_buy.dataframe(buy_signals_df, use_container_width=True, hide_index=True)
    else:
        col_buy.info("No stocks meet strict -10% buy deviation.")

    col_sell.markdown("<div style='background-color: rgba(41, 181, 232, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (&ge; +10%)</div>", unsafe_allow_html=True)
    col_sell.markdown("<br>", unsafe_allow_html=True)
    if not sell_signals_df.empty:
