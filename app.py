import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time

# Page settings
st.set_page_config(
    page_title="Stock 52-Week Drawdown Analysis",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📊 Stock 52-Week Drawdown Analysis")
st.markdown("**Investment Strategy: Buy during significant pullbacks**")

# Initialize session state
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "GOOGL"]
if "selected_stocks" not in st.session_state:
    st.session_state.selected_stocks = []

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Control Panel")
    
    # Add stocks
    st.subheader("Add Stocks")
    new_stocks = st.text_input(
        "Enter stock symbols (comma separated)",
        placeholder="Example: MSFT, AMZN, META"
    )
    
    if st.button("Add to Watchlist", type="primary"):
        if new_stocks:
            stocks = [s.strip().upper() for s in new_stocks.split(",") if s.strip()]
            for stock in stocks:
                if stock not in st.session_state.watchlist:
                    st.session_state.watchlist.append(stock)
            st.success(f"Added! Watchlist now has {len(st.session_state.watchlist)} stocks")
    
    st.divider()
    
    # Watchlist
    st.subheader("📋 Your Watchlist")
    if st.session_state.watchlist:
        selected = st.multiselect(
            "Select stocks to analyze",
            st.session_state.watchlist,
            default=st.session_state.watchlist[:3]
        )
        st.session_state.selected_stocks = selected
        
        if st.button("🚀 Start Analysis", type="primary"):
            st.rerun()
        
        if st.button("Clear Watchlist"):
            st.session_state.watchlist = []
            st.rerun()
    else:
        st.info("Your watchlist is empty. Add stocks above.")
    
    st.divider()
    
    # Strategy info
    st.subheader("📖 Strategy Info")
    st.markdown("""
    **Buy Signals:**
    - ⭐⭐⭐⭐⭐ 30%+ below 52-week high = STRONG BUY
    - ⭐⭐⭐ 20%+ below = BUY
    - ⭐ 10%+ below = WATCH
    """)

# ========== MAIN CONTENT ==========
if st.session_state.selected_stocks:
    st.header(f"📊 Analyzing {len(st.session_state.selected_stocks)} Stocks")
    
    # Progress bar
    progress_bar = st.progress(0)
    
    results = []
    for i, ticker in enumerate(st.session_state.selected_stocks):
        # Update progress
        progress = (i + 1) / len(st.session_state.selected_stocks)
        progress_bar.progress(progress)
        
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                high_52w = hist["Close"].rolling(252).max().iloc[-1]
                drawdown = (high_52w - current_price) / high_52w
                
                # Determine signal
                if drawdown >= 0.30:
                    signal = "⭐⭐⭐⭐⭐ STRONG BUY"
                elif drawdown >= 0.20:
                    signal = "⭐⭐⭐ BUY"
                elif drawdown >= 0.10:
                    signal = "⭐ WATCH"
                else:
                    signal = "HOLD"
                
                results.append({
                    "Ticker": ticker,
                    "Current Price": f"${current_price:.2f}",
                    "52-Week High": f"${high_52w:.2f}",
                    "Drawdown": f"{drawdown:.1%}",
                    "Signal": signal
                })
        except:
            results.append({
                "Ticker": ticker,
                "Current Price": "Error",
                "52-Week High": "Error",
                "Drawdown": "Error",
                "Signal": "ERROR"
            })
    
    # Clear progress bar
    progress_bar.empty()
    
    # Display results
    if results:
        st.subheader("Analysis Results")
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        
        # Show charts
        st.subheader("Price Charts")
        cols = st.columns(2)
        
        for i, ticker in enumerate(st.session_state.selected_stocks[:4]):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="6mo")
                
                with cols[i % 2]:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(hist.index, hist["Close"], linewidth=2)
                    ax.set_title(f"{ticker} - 6 Month Trend")
                    ax.grid(True, alpha=0.3)
                    plt.tight_layout()
                    st.pyplot(fig)
            except:
                pass
        
        # Download button
        st.subheader("💾 Download Results")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"stock_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
else:
    # Welcome screen
    st.markdown("""
    ## 🎯 Welcome to Stock Drawdown Analysis
    
    **How to use:**
    1. **Add stocks** in the sidebar (e.g., AAPL, TSLA, NVDA)
    2. **Select stocks** from your watchlist
    3. **Click "Start Analysis"** to see results
    
    **Example stocks to try:**
    - Technology: AAPL, MSFT, GOOGL, NVDA
    - E-commerce: AMZN, SHOP
    - Electric Vehicles: TSLA, NIO
    - Finance: JPM, V, MA
    """)
    
    st.info("💡 Tip: Start by adding a few stocks in the sidebar, then click 'Start Analysis'")

# Footer
st.divider()
st.caption(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💾 Data: Yahoo Finance | 🛠 Built with Streamlit")
