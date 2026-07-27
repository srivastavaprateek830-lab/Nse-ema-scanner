import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
    ema_period = st.slider("EMA Period", min_value=5, max_value=200, value=20, step=5)
    deviation_threshold = st.slider("Signal Threshold (%)", min_value=1.0, max_value=20.0, value=10.0, step=0.5)
    
    st.markdown("---")
    if st.button("🔄 Refresh Market Data", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.keyboard_sliders = {} 
        st.rerun()
        
    st.markdown("---")
    st.caption("Data source: Individual Ticker Streams via Yahoo Finance.")

# --- MAIN INTERFACE ---
st.title("📊 NSE F&O Strategy Dashboard")
st.markdown("This scanner monitors prominent NSE derivatives and identifies extreme price expansions away from moving average baselines.")

# List of prominent liquid NSE F&O Tickers
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

def fetch_single_ticker(ticker, lookback, ema_len, session):
    """Worker function to fetch data for one ticker to bypass network blocks."""
    try:
        # Request individual history stream safely
        df = yf.download(ticker, period=lookback, interval="1d", progress=False, session=session, show_errors=False)
        if df.empty or len(df) < ema_len:
            return None
            
        close_prices = df['Close']
        ema_series = close_prices.ewm(span=ema_len, adjust=False).mean()
        
        current_price = float(close_prices.iloc[-1])
        current_ema = float(ema_series.iloc[-1])
        deviation = ((current_price - current_ema) / current_ema) * 100
        
        return {
            "Ticker": ticker.replace(".NS", ""),
            "Price (₹)": round(current_price, 2),
            f"EMA{ema_len} (₹)": round(current_ema, 2),
            "Deviation (%)": round(deviation, 2)
        }
    except:
        return None

@st.cache_data(ttl=600)
def scan_markets(ema_len):
    scanned_data = []
    lookback_period = "6mo" if ema_len > 50 else "3mo"
    
    # Configure a persistent user session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    })
    
    # Streamlit visual tracking bars
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Process tickers in parallel using multi-threading
    total_tickers = len(FO_TICKERS)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_single_ticker, ticker, lookback_period, ema_len, session): ticker for ticker in FO_TICKERS}
        
        for future in as_completed(futures):
            completed += 1
            ticker_name = futures[future].replace(".NS", "")
            status_text.text(f"Scanning data lane: {ticker_name} ({completed}/{total_tickers})...")
            progress_bar.progress(completed / total_tickers)
            
            result = future.result()
            if result:
                scanned_data.append(result)
                
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(scanned_data)

# Run processing engine
results_df = scan_markets(ema_period)

if not results_df.empty:
    # Assign signals dynamically based on slider values
    def assign_action(row):
        dev = row["Deviation (%)"]
        if dev <= -deviation_threshold:
            return "🔴 BUY (Undervalued)"
        elif dev >= deviation_threshold:
            return "🟢 SELL (Overvalued)"
        return "⚪ NEUTRAL"

    results_df["Action"] = results_df.apply(assign_action, axis=1)
    
    # Filter for active alert setups
    filtered_df = results_df[results_df["Action"] != "⚪ NEUTRAL"].copy()
    if not filtered_df.empty:
        filtered_df = filtered_df.reindex(filtered_df["Deviation (%)"].abs().sort_values(ascending=False).index)
    
    # Sort entire dataset by highest absolute deviation for the main table view
    all_sorted_df = results_df.reindex(results_df["Deviation (%)"].abs().sort_values(ascending=False).index)

    # --- METRIC CARDS REGION ---
    buy_count = len(filtered_df[filtered_df["Deviation (%)"] <= -deviation_threshold]) if not filtered_df.empty else 0
    sell_count = len(filtered_df[filtered_df["Deviation (%)"] >= deviation_threshold]) if not filtered_df.empty else 0
    
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
        csv_data = all_sorted_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Tracker to CSV",
            data=csv_data,
            file_name=f"nse_f_o_ema{ema_period}_report.csv",
            mime="text/csv",
            use_container_width=True
        )
        
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
