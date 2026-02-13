import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Page settings
st.set_page_config(
    page_title="Stock 52-Week Drawdown Analysis",
    page_icon="📈",
    layout="wide"
)

# ========== 添加多用户系统 ==========
if "username" not in st.session_state:
    st.session_state.username = "default_user"

if "watchlist" not in st.session_state:
    user_file = f"watchlist_{st.session_state.username}.json"
    if os.path.exists(user_file):
        try:
            with open(user_file, 'r') as f:
                st.session_state.watchlist = json.load(f)
        except:
            st.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "GOOGL"]
    else:
        st.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "GOOGL"]

if "selected_stocks" not in st.session_state:
    st.session_state.selected_stocks = []

# Title
st.title("📊 Stock 52-Week Drawdown Analysis")
st.markdown("**Investment Strategy: Buy during significant pullbacks**")

# ========== 改进的信号分级系统 ==========
def get_buy_signal(drawdown):
    """改进的信号分级系统"""
    if drawdown >= 0.30:
        return {"stars": "⭐⭐⭐⭐⭐", "action": "STRONG BUY", "level": 5}
    elif drawdown >= 0.25:
        return {"stars": "⭐⭐⭐⭐", "action": "AGGRESSIVE BUY", "level": 4}
    elif drawdown >= 0.20:
        return {"stars": "⭐⭐⭐", "action": "BUY", "level": 3}
    elif drawdown >= 0.15:
        return {"stars": "⭐⭐", "action": "CONSIDER BUYING", "level": 2}
    elif drawdown >= 0.10:
        return {"stars": "⭐", "action": "WATCH & BUY", "level": 1}
    elif drawdown >= 0.05:
        return {"stars": "", "action": "CAUTIOUS WATCH", "level": 0}
    else:
        return {"stars": "", "action": "HOLD", "level": -1}

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Control Panel")
    
    st.subheader("👤 User Profile")
    username = st.text_input(
        "Username:",
        value=st.session_state.username,
        key="username_input"
    )
    
    if st.button("Switch User", type="secondary"):
        st.session_state.username = username
        user_file = f"watchlist_{username}.json"
        if os.path.exists(user_file):
            try:
                with open(user_file, 'r') as f:
                    st.session_state.watchlist = json.load(f)
            except:
                st.session_state.watchlist = []
        else:
            st.session_state.watchlist = []
        st.session_state.selected_stocks = []
       
        st.rerun()
    
    st.divider()
    
    st.subheader("Add Stocks")
    new_stocks = st.text_input(
        "Enter stock symbols (comma separated)",
        placeholder="Example: MSFT, AMZN, META"
    )
    
    if st.button("Add to Watchlist", type="primary"):
        if new_stocks:
            stocks = [s.strip().upper() for s in new_stocks.split(",") if s.strip()]
            added_count = 0
            for stock in stocks:
                if stock not in st.session_state.watchlist:
                    st.session_state.watchlist.append(stock)
                    added_count += 1
            
            if added_count > 0:
                user_file = f"watchlist_{st.session_state.username}.json"
                with open(user_file, 'w') as f:
                    json.dump(st.session_state.watchlist, f, indent=2)
                
                st.success(f"✅ Successfully added {added_count} stock(s)! Total: {len(st.session_state.watchlist)} stocks")
                time.sleep(0.5)
                st.rerun()
            else:
                st.info("These stocks are already in your watchlist")
    
    st.divider()
    
    st.subheader("📋 Your Watchlist")
    if st.session_state.watchlist:
        # 修复：移除default参数，显示全部股票
        selected = st.multiselect(
            "Select stocks to analyze",
            st.session_state.watchlist
        )
        st.session_state.selected_stocks = selected
        
        if st.button("🚀 Start Analysis", type="primary"):
            st.rerun()
        
        if st.button("Clear Watchlist"):
            st.session_state.watchlist = []
            user_file = f"watchlist_{st.session_state.username}.json"
            if os.path.exists(user_file):
                os.remove(user_file)
            st.success("Watchlist cleared!")
            time.sleep(0.5)
            st.rerun()
    else:
        st.info("Your watchlist is empty. Add stocks above.")
    
    st.divider()
    
    st.subheader("📖 Investment Strategy")
    st.markdown("""
    **Buy Signals:**
    - ⭐⭐⭐⭐⭐ 30%+ below 52-week high = STRONG BUY
    - ⭐⭐⭐⭐ 25%+ below = AGGRESSIVE BUY  
    - ⭐⭐⭐ 20%+ below = BUY
    - ⭐⭐ 15%+ below = CONSIDER BUYING
    - ⭐ 10%+ below = WATCH & BUY
    - 5%+ below = CAUTIOUS WATCH
    """)

# ========== MAIN CONTENT ==========
if st.session_state.selected_stocks:
    st.header(f"📊 Analyzing {len(st.session_state.selected_stocks)} Stocks")
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    for i, ticker in enumerate(st.session_state.selected_stocks):
        # Update progress
        progress = (i + 1) / len(st.session_state.selected_stocks)
        progress_bar.progress(progress)
        status_text.text(f"Fetching data for {ticker}... ({i+1}/{len(st.session_state.selected_stocks)})")
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                high_52w = hist["Close"].rolling(252, min_periods=1).max().iloc[-1]
                drawdown = (high_52w - current_price) / high_52w if high_52w > 0 else 0
                
                signal_info = get_buy_signal(drawdown)
                
                results.append({
                    "Ticker": ticker,
                    "Current Price": f"${current_price:.2f}",
                    "52-Week High": f"${high_52w:.2f}",
                    "Drawdown": f"{drawdown:.1%}",
                    "Signal": f"{signal_info['stars']} {signal_info['action']}",
                    "Level": signal_info['level']
                })
            else:
                results.append({
                    "Ticker": ticker,
                    "Current Price": "No data",
                    "52-Week High": "No data",
                    "Drawdown": "N/A",
                    "Signal": "NO DATA",
                    "Level": -2
                })
                
        except Exception as e:
            results.append({
                "Ticker": ticker,
                "Current Price": "Error",
                "52-Week High": "Error",
                "Drawdown": "Error",
                "Signal": f"ERROR",
                "Level": -2
            })
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display results with sorting
    if results:
        st.subheader("Analysis Results")
        df = pd.DataFrame(results)
        
        # 添加排序选项
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                "Sort by:",
                ["Drawdown (Desc)", "Level (Desc)", "Ticker (Asc)"]
            )
        
        # 排序逻辑
        if sort_by == "Drawdown (Desc)":
            # 创建一个临时列用于排序
            def get_drawdown_value(val):
                if val == "N/A" or val == "Error":
                    return -999
                try:
                    return float(val.rstrip('%')) / 100
                except:
                    return -999
            
            df['drawdown_num'] = df['Drawdown'].apply(get_drawdown_value)
            df = df.sort_values('drawdown_num', ascending=False)
            df = df.drop('drawdown_num', axis=1)
        elif sort_by == "Level (Desc)":
            df = df.sort_values('Level', ascending=False)
        else:
            df = df.sort_values('Ticker')
        
        st.dataframe(df[["Ticker", "Current Price", "52-Week High", "Drawdown", "Signal"]], 
                    use_container_width=True)
        
                # Show charts
        st.subheader("Price Charts")
        
        # 获取要显示的股票数量（最多4个）
        num_stocks = min(4, len(st.session_state.selected_stocks))
        
        if num_stocks == 0:
            st.info("No stocks selected for charts")
        else:
            # 根据股票数量创建列
            if num_stocks == 1:
                # 只有1个股票，用单列
                for i, ticker in enumerate(st.session_state.selected_stocks[:num_stocks]):
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="6mo")
                        
                        if not hist.empty:
                            st.subheader(f"{ticker}")
                            fig, ax = plt.subplots(figsize=(10, 4))
                            ax.plot(hist.index, hist["Close"], linewidth=2, color='blue')
                            
                            if len(hist) > 20:
                                high_52w = hist["Close"].rolling(min(252, len(hist)), min_periods=1).max().iloc[-1]
                                current_price = hist["Close"].iloc[-1]
                                
                                ax.axhline(y=high_52w, color='red', linestyle='--', alpha=0.5, label=f'52W High: ${high_52w:.2f}')
                                ax.axhline(y=current_price, color='green', linestyle='--', alpha=0.5, label=f'Current: ${current_price:.2f}')
                            
                            ax.set_title(f"{ticker} - 6 Month Trend")
                            ax.set_xlabel("Date")
                            ax.set_ylabel("Price ($)")
                            ax.grid(True, alpha=0.3)
                            ax.legend(loc='upper left')
                            plt.xticks(rotation=45)
                            plt.tight_layout()
                            st.pyplot(fig)
                    except Exception as e:
                        st.error(f"Could not load chart for {ticker}: {str(e)}")
            
            elif num_stocks == 2:
                # 2个股票，用2列
                cols = st.columns(2)
                for i, ticker in enumerate(st.session_state.selected_stocks[:num_stocks]):
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="6mo")
                        
                        if not hist.empty:
                            with cols[i]:
                                fig, ax = plt.subplots(figsize=(10, 4))
                                ax.plot(hist.index, hist["Close"], linewidth=2, color='blue')
                                
                                if len(hist) > 20:
                                    high_52w = hist["Close"].rolling(min(252, len(hist)), min_periods=1).max().iloc[-1]
                                    current_price = hist["Close"].iloc[-1]
                                    
                                    ax.axhline(y=high_52w, color='red', linestyle='--', alpha=0.5, label=f'52W High: ${high_52w:.2f}')
                                    ax.axhline(y=current_price, color='green', linestyle='--', alpha=0.5, label=f'Current: ${current_price:.2f}')
                                
                                ax.set_title(f"{ticker} - 6 Month Trend")
                                ax.set_xlabel("Date")
                                ax.set_ylabel("Price ($)")
                                ax.grid(True, alpha=0.3)
                                ax.legend(loc='upper left')
                                plt.xticks(rotation=45)
                                plt.tight_layout()
                                st.pyplot(fig)
                    except Exception as e:
                        with cols[i]:
                            st.error(f"Could not load chart for {ticker}")
            
            elif num_stocks >= 3:
                # 3-4个股票，用2列，每列显示1-2个
                cols = st.columns(2)
                for i, ticker in enumerate(st.session_state.selected_stocks[:num_stocks]):
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="6mo")
                        
                        if not hist.empty:
                            with cols[i % 2]:
                                fig, ax = plt.subplots(figsize=(10, 4))
                                ax.plot(hist.index, hist["Close"], linewidth=2, color='blue')
                                
                                if len(hist) > 20:
                                    high_52w = hist["Close"].rolling(min(252, len(hist)), min_periods=1).max().iloc[-1]
                                    current_price = hist["Close"].iloc[-1]
                                    
                                    ax.axhline(y=high_52w, color='red', linestyle='--', alpha=0.5, label=f'52W High: ${high_52w:.2f}')
                                    ax.axhline(y=current_price, color='green', linestyle='--', alpha=0.5, label=f'Current: ${current_price:.2f}')
                                
                                ax.set_title(f"{ticker} - 6 Month Trend")
                                ax.set_xlabel("Date")
                                ax.set_ylabel("Price ($)")
                                ax.grid(True, alpha=0.3)
                                ax.legend(loc='upper left')
                                plt.xticks(rotation=45)
                                plt.tight_layout()
                                st.pyplot(fig)
                    except Exception as e:
                        with cols[i % 2]:
                            st.error(f"Could not load chart for {ticker}")
        
                # Download button
        st.subheader("💾 Download Results")
        
        # 创建两个版本的数据：一个用于显示，一个用于下载
        display_df = df[["Ticker", "Current Price", "52-Week High", "Drawdown", "Signal"]].copy()
        
        # 为下载创建干净版本（移除星星符号，只保留文字）
        download_df = df[["Ticker", "Current Price", "52-Week High", "Drawdown"]].copy()
        download_df["Signal"] = df["Signal"].str.replace(r'[⭐★]', '', regex=True).str.strip()
        
        # CSV下载（用UTF-8 with BOM，Excel能识别）
        csv = download_df.to_csv(index=False).encode("utf-8-sig")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"results_{st.session_state.username}_{timestamp}.csv"
        download_df.to_csv(results_file, index=False, encoding='utf-8-sig')
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download CSV (Excel兼容)",
                data=csv,
                file_name=f"stock_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2:
            st.info(f"Results also saved to: `{results_file}`")
            
        # 显示带星星的表格
        st.subheader("Current Analysis")
        st.dataframe(display_df, use_container_width=True)              
            
else:
    # Welcome screen
    st.markdown("""
    ## 🎯 Welcome to Stock Drawdown Analysis
    
    **How to use:**
    1. **Enter your username** in the sidebar (or use default)
    2. **Add stocks** (e.g., AAPL, TSLA, NVDA)
    3. **Select stocks** from your watchlist
    4. **Click "Start Analysis"** to see results
    
    **Features:**
    - 📁 **Multi-user support**: Each user has their own watchlist
    - 📊 **Detailed analysis**: 6-level buy signal system
    - 📈 **Interactive charts**: Visualize price trends
    - 📥 **Export data**: Download results as CSV
    
    **Example stocks to try:**
    - Technology: AAPL, MSFT, GOOGL, NVDA
    - E-commerce: AMZN, SHOP
    - Electric Vehicles: TSLA, NIO
    - Finance: JPM, V, MA
    """)
    
    # 显示可用的用户文件
    st.divider()
    st.subheader("📂 Available User Data")
    user_files = [f for f in os.listdir() if f.startswith("watchlist_") and f.endswith(".json")]
    if user_files:
        st.write("Found watchlists for:")
        for file in user_files:
            username = file.replace("watchlist_", "").replace(".json", "")
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    st.write(f"- **{username}**: {len(data)} stocks")
            except:
                st.write(f"- **{username}**: (corrupted)")
    else:
        st.info("No user data found. Start by adding stocks!")
    
    # 添加快速启动按钮
    st.divider()
    if st.button("🚀 Quick Start with Default Stocks"):
        st.session_state.selected_stocks = ["AAPL", "MSFT", "GOOGL"][:min(3, len(st.session_state.watchlist))]
        st.rerun()

# Footer
st.divider()
st.caption(f"👤 User: {st.session_state.username} | 📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💾 Data: Yahoo Finance | 🛠 Built with Streamlit | 📈 Multi-user Support")

# 添加版本兼容性提示
st.sidebar.divider()
st.sidebar.caption(f"Streamlit v{st.__version__}")