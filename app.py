import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# Fix for Yahoo Finance cache location on Streamlit servers
yf.set_tz_cache_location("/tmp/yf_cache")

# Page Layout Configurations
st.set_page_config(
    page_title="NSE F&O Analytics Dashboard", 
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Scanner Configurations")
    st.write("Adjust parameters to customize your trading signals.")
    
    # Dynamic inputs for trading strategies
    ema_period = st.slider("EMA Period", min_value=5, max_value=200, value=20, step=5)
    deviation_threshold = st.slider("Signal Threshold (%)", min_value=1.0, max_value=20.0, value=10.0, step=0.5)
    
    st.markdown("---")
    # Manual data refresh button placed cleanly in sidebar
    if st.button("🔄 Refresh Market Data", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("---")
    st.caption("Data source: Yahoo Finance Feed. Updates cache every 10 minutes.")

# --- MAIN INTERFACE ---
st.title("📊 NSE F&O Strategy Dashboard")
st.markdown("This institutional-grade scanner monitors prominent NSE derivatives and identifies extreme price expansions away from moving average baselines.")

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

@st.cache_data(ttl=600)
def scan_markets(ema_len):
    scanned_data = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Download lookback data based on max possible EMA length
    lookback_period = "6mo" if ema_len > 50 else "3mo"
    tickers_str = " ".join(FO_TICKERS)
    data = yf.download(tickers_str, period=lookback_period, interval="1d", group_by="ticker", progress=False, session=session)
    
    for ticker in FO_TICKERS:
        try:
            df = data[ticker].dropna() if ticker in data.columns.levels else pd.DataFrame()
            if df.empty or len(df) < ema_len:
                continue
                
            close_prices = df['Close']
            ema_series = close_prices.ewm(span=ema_len, adjust=False).mean()
            
            current_price = float(close_prices.iloc[-1])
            current_ema = float(ema_series.iloc[-1])
            deviation = ((current_price - current_ema) / current_ema) * 100
            
            scanned_data.append({
                "Ticker": ticker.replace(".NS", ""),
                "Price (₹)": round(current_price, 2),
                f"EMA{ema_len} (₹)": round(current_ema, 2),
                "Deviation (%)": round(deviation, 2)
            })
        except Exception:
            continue
            
    return pd.DataFrame(scanned_data)

# Run processing engine
with st.spinner("Analyzing F&O market data channels..."):
    results_df = scan_markets(ema_period)

if not results_df.empty:
    # Assign signals dynamically based on sidebar threshold values
    def assign_action(row):
        dev = row["Deviation (%)"]
        if dev <= -deviation_threshold:
            return "🔴 BUY (Undervalued)"
        elif dev >= deviation_threshold:
            return "🟢 SELL (Overvalued)"
        return "白 NEUTRAL"

    results_df["Action"] = results_df.apply(assign_action, axis=1)
    
    # Filter for active alert setups
    filtered_df = results_df[results_df["Action"] != "白 NEUTRAL"].copy()
    filtered_df = filtered_df.reindex(filtered_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Sort entire dataset by highest absolute deviation for the main table view
    all_sorted_df = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)

    # --- METRIC CARDS REGION ---
    buy_count = len(filtered_df[filtered_df["Deviation (%)"] <= -deviation_threshold])
    sell_count = len(filtered_df[filtered_df["Deviation (%)"] >= deviation_threshold])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"<div style='border: 1px solid #ff4b4b; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 5px;'><strong>🔴 BUY Signals (&lt; -{deviation_threshold}%)</strong><br><span style='font-size: 24px; font-weight: bold;'>{buy_count}</span></div>", unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"<div style='border: 1px solid #29b5e8; border-left: 5px solid #29b5e8; padding: 15px; border-radius: 5px;'><strong>🟢 SELL Signals (&gt; +{deviation_threshold}%)</strong><br><span style='font-size: 24px; font-weight: bold;'>{sell_count}</span></div>", unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"<div style='border: 1px solid #777777; border-left: 5px solid #777777; padding: 15px; border-radius: 5px;'><strong>🔍 Active Watchlist Total</strong><br><span style='font-size: 24px; font-weight: bold;'>{len(results_df)} Stocks</span></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- HIGH PRIORITY ALERTS TABLE ---
    st.subheader(f"🎯 Triggered Trading Signals (Threshold: ±{deviation_threshold}%)")
    if not filtered_df.empty:
        st.dataframe(
            filtered_df, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Deviation (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                f"EMA{ema_period} (₹)": st.column_config.NumberColumn(format="₹%.2f")
            }
        )
    else:
        st.info(f"No F&O stocks currently exceed the ±{deviation_threshold}% deviation threshold from the EMA{ema_period}.")
        
    # --- COMPLETE WATCHLIST VIEW & EXPORT ---
    st.markdown("---")
    w_col1, w_col2 = st.columns([3, 1])
    with w_col1:
        st.subheader("🔍 Complete F&O Segment Watchlist")
    with w_col2:
        # Download button directly linked to dataset export
        csv_data = all_sorted_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Tracker to CSV",
            data=csv_data,
            file_name=f"nse_f_o_ema{ema_period}_report.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    # Live Interactive Text Search Bar Filter
    search_query = st.text_input("⚡ Quick Ticker Search", placeholder="Type symbol name (e.g., RELIANCE, SBIN)...").strip().upper()
    if search_query:
        display_all_df = all_sorted_df[all_sorted_df["Ticker"].str.contains(search_query)]
    else:
        display_all_df = all_sorted_df

    st.dataframe(
        display_all_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Deviation (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
            f"EMA{ema_period} (₹)": st.column_config.NumberColumn(format="₹%.2f")
        }
    )
else:
    st.error("Market data processing failed. Please check the network relay or try refreshing data feeds via the sidebar button.")
