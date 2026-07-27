import streamlit as st
import pandas as pd
from tradingview_ta import get_multiple_analysis, Interval

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
    "AXISBANK": "🏦 BANKING", "BANKBARODA": "🏦 BANKING", "CANBK": "🏦 BANKING", "HDFCBANK": "🏦 BANKING", "ICICIBANK": "🏦 BANKING", "KOTAKBANK": "🏦 BANKING", "PNB": "🏦 BANKING", "SBIN": "🏦 BANKING",
    "COFORGE": "💻 IT SECTOR", "HCLTECH": "💻 IT SECTOR", "INFY": "💻 IT SECTOR", "LTIM": "💻 IT SECTOR", "PERSISTENT": "💻 IT SECTOR", "TCS": "💻 IT SECTOR", "TECHM": "💻 IT SECTOR", "WIPRO": "💻 IT SECTOR",
    "BAJAJ_AUTO": "🚗 AUTO", "EICHERMOT": "🚗 AUTO", "HEROMOTOCO": "🚗 AUTO", "M_M": "🚗 AUTO", "MARUTI": "🚗 AUTO", "TATAMOTORS": "🚗 AUTO", "TVSMOTOR": "🚗 AUTO",
    "CIPLA": "💊 PHARMA", "DIVISLAB": "💊 PHARMA", "DRREDDY": "💊 PHARMA", "GLENMARK": "💊 PHARMA", "LUPIN": "💊 PHARMA", "SUNPHARMA": "💊 PHARMA", "TORNTPHARM": "💊 PHARMA",
    "BRITANNIA": "🛒 FMCG", "DABUR": "🛒 FMCG", "HINDUNILVR": "🛒 FMCG", "ITC": "🛒 FMCG", "NESTLEIND": "🛒 FMCG", "TATACONSUM": "🛒 FMCG",
    "HINDALCO": "🏗️ METALS", "JINDALSTEL": "🏗️ METALS", "JSWSTEEL": "🏗️ METALS", "NATIONALUM": "🏗️ METALS", "SAIL": "🏗️ METALS", "TATASTEEL": "🏗️ METALS", "VEDL": "🏗️ METALS",
    "DLF": "🏢 REALTY", "GODREJPROP": "🏢 REALTY", "OBEROIRLTY": "🏢 REALTY",
    "ADANIPORTS": "⚡ ENERGY", "BPCL": "⚡ ENERGY", "COALINDIA": "⚡ ENERGY", "GAIL": "⚡ ENERGY", "HINDPETRO": "⚡ ENERGY", "IOC定位": "⚡ ENERGY", "NTPC": "⚡ ENERGY", "ONGC": "⚡ ENERGY", "POWERGRID": "⚡ ENERGY", "TATAPOWER": "⚡ ENERGY"
}

@st.cache_data(ttl=300) # Fast 5-minute tracking cache refresh layer
def scan_markets_bulk_tv():
    scanned_data = []
    try:
        # One single high-speed bulk call fetching all technical metrics simultaneously
        bulk_analysis = get_multiple_analysis(screener="india", exchange="NSE", symbols=FO_TICKERS, interval=Interval.INTERVAL_1_DAY)
        
        for full_symbol, analysis in bulk_analysis.items():
            if not analysis:
                continue
            try:
                ticker = full_symbol.split(":")[1]
                indicators = analysis.indicators
                
                current_price = float(indicators.get("close", 0.0))
                current_ema20 = float(indicators.get("EMA20", 0.0))
                day_change = float(indicators.get("change", 0.0))
                rsi14 = float(indicators.get("RSI", 50.0)) # Pull native 14-period RSI
                
                if current_price == 0.0 or current_ema20 == 0.0:
                    continue
                    
                # Strict 10% core mathematical equation logic restored
                deviation = ((current_price - current_ema20) / current_ema20) * 100
                
                # Enhanced Logic: Flag if strict 10% criteria matches RSI momentum safety
                if deviation <= -10.0:
                    action = "🔴 BUY" if rsi14 < 35 else "🔴 BUY (Weak RSI)"
                elif deviation >= 10.0:
                    action = "🟢 SELL" if rsi14 > 65 else "🟢 SELL (Weak RSI)"
                else:
                    action = "⚪ HOLD"
                    
                scanned_data.append({
                    "Ticker": ticker.replace("_", "&"),
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

# Refresh framework initialization panel button
if st.button("🔄 Refresh Scanner Data", type="primary"):
    st.cache_data.clear()

with st.spinner("Executing high-speed institutional indicators tracking streams..."):
    results_df = scan_markets_bulk_tv()

if not results_df.empty:
    # Sort absolute deviations largest to smallest
    all_sorted = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Isolate targets that fulfill the exact strict 10% boundary requirements
    buy_signals_df = all_sorted[all_sorted["Deviation (%)"] <= -10.0][["Ticker", "Price (₹)", "Deviation (%)", "RSI (14)"]]
    sell_signals_df = all_sorted[all_sorted["Deviation (%)"] >= 10.0][["Ticker", "Price (₹)", "Deviation (%)", "RSI (14)"]]

    # Natively summarize the Sector Index values
    all_sorted["Sector"] = all_sorted["Ticker"].map(TICKER_SECTORS)
    sector_summary = all_sorted.groupby("Sector", as_index=False)["Change"].mean()
    sector_summary = sector_summary.dropna().sort_values(by="Change", ascending=False)

    # Master frame view configuration data
    display_master_df = all_sorted[["Ticker", "Price (₹)", "EMA20 (₹)", "Deviation (%)", "RSI (14)", "Action"]]

    # --- 📊 MASTER FOUR-COLUMN SPACE BOUNDARIES GRID ---
    col_master, col_buy, col_sell, col_sectors = st.columns([0.48, 0.17, 0.17, 0.18])

    with col_master:
        st.subheader("🔍 Complete F&O Watchlist")
        st.dataframe(display_master_df, use_container_width=True, hide_index=True)

    with col_buy:
        st.markdown("<div style='background-color: rgba(255, 75, 75, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #ff4b4b; font-weight: bold;'>🚨 Buy Stocks (&le; -10%)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not buy_signals_df.empty:
            st.dataframe(buy_signals_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks meet strict -10% buy deviation.")

    with col_sell:
        st.markdown("<div style='background-color: rgba(41, 181, 232, 0.12); padding: 10px; border-radius: 4px; border-left: 4px solid #29b5e8; font-weight: bold;'>🚨 Sell Stocks (&ge; +10%)</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if not sell_signals_df.empty:
            st.dataframe(sell_signals_df, use_container_width=True, hide_index=True)
        else:
            st.info("No stocks meet strict +10% sell deviation.")

    with col_sectors:
        st.markdown("<div style='background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 4px; border-left: 4px solid #777777; font-weight: bold;'>⚡ Nifty Sectors Performance</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for _, row in sector_summary.iterrows():
            name = row["Sector"]
            change = round(row["Change"], 2)
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
