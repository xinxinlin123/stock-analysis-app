import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import json
import os
import warnings
from scipy import stats
warnings.filterwarnings('ignore')

# Page settings
st.set_page_config(
    page_title="Stock 52-Week Drawdown Analysis",
    page_icon="📈",
    layout="wide"
)

# ========== Multi-user System ==========
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
st.markdown("**Quantitative Decision Framework: From Rules to Probabilities**")

# ========== Constants ==========
# Core stocks whitelist
CORE_STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'TSM']

# Filter thresholds
FILTER_CONFIG = {
    'MIN_PRICE': 5.0,
    'MIN_MARKET_CAP': 5_000_000_000,
    'MIN_VOLUME_VALUE': 1_000_000,
    'ALLOWED_EXCHANGES': ['NYQ', 'NAS', 'NMS', 'NYSE', 'NASDAQ'],
}

# ========== Sector Index Mapping ==========
SECTOR_INDICES = {
    'S&P 500 (Broad Market)': '^GSPC',
    'NASDAQ 100 (Tech Heavy)': '^NDX',
    'Dow Jones (Blue Chip)': '^DJI',
    'Russell 2000 (Small Cap)': '^RUT',
    
    # Sector ETFs
    'Technology Sector XLK': 'XLK',
    'Semiconductor Sector SOXX': 'SOXX',
    'Financial Sector XLF': 'XLF',
    'Healthcare Sector XLV': 'XLV',
    'Consumer Staples XLP': 'XLP',
    'Energy Sector XLE': 'XLE',
    'Communication Services XLC': 'XLC',
    'Industrial Sector XLI': 'XLI',
    'Materials Sector XLB': 'XLB',
    'Real Estate Sector XLRE': 'XLRE',
}

# Stock to sector mapping rules
STOCK_SECTOR_MAP = {
    # Tech Giants -> NASDAQ 100
    'AAPL': '^NDX',
    'MSFT': '^NDX',
    'GOOGL': '^NDX',
    'GOOG': '^NDX',
    'AMZN': '^NDX',
    'META': '^NDX',
    'NVDA': '^NDX',
    'TSLA': '^NDX',
    'TSM': '^NDX',
    'AMD': '^NDX',
    'INTC': '^NDX',
    'NFLX': '^NDX',
    'ADBE': '^NDX',
    'CRM': '^NDX',
    
    # Financials -> XLF
    'JPM': 'XLF',
    'BAC': 'XLF',
    'WFC': 'XLF',
    'C': 'XLF',
    'GS': 'XLF',
    'MS': 'XLF',
    'V': 'XLF',
    'MA': 'XLF',
    'AXP': 'XLF',
    
    # Energy -> XLE
    'XOM': 'XLE',
    'CVX': 'XLE',
    'COP': 'XLE',
    'SLB': 'XLE',
    'EOG': 'XLE',
    
    # Healthcare -> XLV
    'JNJ': 'XLV',
    'PFE': 'XLV',
    'MRK': 'XLV',
    'ABBV': 'XLV',
    'UNH': 'XLV',
    'LLY': 'XLV',
    
    # Consumer Staples -> XLP
    'PG': 'XLP',
    'KO': 'XLP',
    'PEP': 'XLP',
    'WMT': 'XLP',
    'COST': 'XLP',
    
    # Semiconductors -> SOXX
    'TSM': 'SOXX',
    'NVDA': 'SOXX',
    'AMD': 'SOXX',
    'INTC': 'SOXX',
    'QCOM': 'SOXX',
    'TXN': 'SOXX',
    'AVGO': 'SOXX',
}

# ========== Get Recommended Index ==========
def get_recommended_index(ticker):
    """
    Recommend appropriate benchmark index based on stock ticker
    """
    # Check exact match first
    if ticker in STOCK_SECTOR_MAP:
        return STOCK_SECTOR_MAP[ticker]
    
    # Try to determine by sector
    try:
        stock = yf.Ticker(ticker)
        sector = stock.info.get('sector', '')
        
        sector_to_index = {
            'Technology': '^NDX',
            'Financial Services': 'XLF',
            'Healthcare': 'XLV',
            'Energy': 'XLE',
            'Consumer Defensive': 'XLP',
            'Consumer Cyclical': 'XLY',
            'Communication Services': 'XLC',
            'Industrials': 'XLI',
            'Basic Materials': 'XLB',
            'Real Estate': 'XLRE',
            'Utilities': 'XLU',
        }
        
        if sector in sector_to_index:
            return sector_to_index[sector]
    except:
        pass
    
    # Default to S&P 500
    return '^GSPC'

# ========== Get Index Name ==========
def get_index_name(symbol):
    """
    Return readable name for index symbol
    """
    name_map = {
        '^GSPC': 'S&P 500',
        '^NDX': 'NASDAQ 100',
        '^DJI': 'Dow Jones',
        '^RUT': 'Russell 2000',
        'XLK': 'Technology Sector',
        'SOXX': 'Semiconductor Sector',
        'XLF': 'Financial Sector',
        'XLV': 'Healthcare Sector',
        'XLP': 'Consumer Staples',
        'XLE': 'Energy Sector',
        'XLC': 'Communication Services',
        'XLI': 'Industrial Sector',
        'XLB': 'Materials Sector',
        'XLRE': 'Real Estate Sector',
    }
    return name_map.get(symbol, symbol)

# ========== Get Market Data ==========
@st.cache_data(ttl=3600)
def get_market_data(index_symbol):
    """
    Get 52-week data for specified index
    """
    try:
        market = yf.Ticker(index_symbol)
        hist = market.history(period="1y")
        
        if hist.empty:
            return None
        
        current_price = hist['Close'].iloc[-1]
        high_52w = hist['High'].max()
        drawdown = (high_52w - current_price) / high_52w * 100
        
        return {
            'symbol': index_symbol,
            'name': get_index_name(index_symbol),
            'current_price': current_price,
            'high_52w': high_52w,
            'drawdown': drawdown,
            'hist': hist
        }
    except Exception as e:
        st.sidebar.warning(f"Unable to get {index_symbol} data: {str(e)}")
        return None

# ========== Stock Quality Check ==========
def check_stock_quality(ticker):
    """
    Check if stock meets basic quality requirements
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        market_cap = info.get('marketCap', 0)
        avg_volume = info.get('averageVolume', 0)
        exchange = info.get('exchange', '')
        
        volume_value = avg_volume * price if price > 0 else 0
        issues = []
        
        if price < FILTER_CONFIG['MIN_PRICE']:
            issues.append(f"Price below ${FILTER_CONFIG['MIN_PRICE']} (current: ${price:.2f})")
        
        if market_cap < FILTER_CONFIG['MIN_MARKET_CAP']:
            issues.append(f"Market cap below ${FILTER_CONFIG['MIN_MARKET_CAP']/1e9:.0f}B")
        
        if volume_value < FILTER_CONFIG['MIN_VOLUME_VALUE']:
            issues.append(f"Daily volume below ${FILTER_CONFIG['MIN_VOLUME_VALUE']:,.0f}")
        
        is_qualified = len(issues) == 0
        
        return {
            'qualified': is_qualified,
            'issues': issues,
            'price': price,
            'market_cap': market_cap,
            'volume_value': volume_value,
            'exchange': exchange,
            'is_core': ticker in CORE_STOCKS
        }
        
    except Exception as e:
        return {
            'qualified': False,
            'issues': [f"Data fetch failed: {str(e)[:50]}"],
            'price': 0,
            'market_cap': 0,
            'volume_value': 0,
            'exchange': '',
            'is_core': False
        }

# ========== Price Distribution Analysis ==========
def analyze_price_distribution(hist):
    """
    Analyze current price position in historical distribution
    Returns Z-score, percentile, extreme levels
    """
    prices = hist['Close'].values
    current_price = prices[-1]
    
    mean_price = np.mean(prices)
    std_price = np.std(prices)
    
    z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
    percentile = stats.percentileofscore(prices, current_price)
    
    is_extreme_cheap = z_score < -2
    is_extreme_expensive = z_score > 2
    
    support_levels = {
        '-2σ': mean_price - 2 * std_price,
        '-1σ': mean_price - 1 * std_price,
        'mean': mean_price,
        '+1σ': mean_price + 1 * std_price,
        '+2σ': mean_price + 2 * std_price
    }
    
    return {
        'z_score': z_score,
        'percentile': percentile,
        'is_extreme_cheap': is_extreme_cheap,
        'is_extreme_expensive': is_extreme_expensive,
        'mean_price': mean_price,
        'std_price': std_price,
        'support_levels': support_levels
    }

# ========== Relative Strength Significance Test ==========
def calculate_relative_strength_score(stock_hist, market_hist, lookback_days=252):
    """
    Calculate relative strength and test statistical significance
    """
    combined = pd.DataFrame({
        'stock': stock_hist['Close'],
        'market': market_hist['Close']
    }).dropna()
    
    if len(combined) < 30:
        return 0, "Insufficient data"
    
    stock_returns = combined['stock'].pct_change().dropna()
    market_returns = combined['market'].pct_change().dropna()
    
    excess_returns = stock_returns - market_returns
    
    mean_excess = np.mean(excess_returns) * 252
    std_excess = np.std(excess_returns) * np.sqrt(252)
    
    recent_excess = excess_returns[-60:].mean() * 252 if len(excess_returns) >= 60 else mean_excess
    
    z_score = recent_excess / std_excess if std_excess > 0 else 0
    
    if abs(z_score) < 0.5:
        significance = "Not significant"
        strength_score = 0
    elif z_score > 1:
        significance = "Significantly stronger than market"
        strength_score = 1.0
    elif z_score > 0.5:
        significance = "Slightly stronger than market"
        strength_score = 0.5
    elif z_score < -1:
        significance = "Significantly weaker than market"
        strength_score = -1.0
    elif z_score < -0.5:
        significance = "Slightly weaker than market"
        strength_score = -0.5
    else:
        significance = "In line with market"
        strength_score = 0
    
    return strength_score, significance

# ========== Star Rating Historical Performance ==========
@st.cache_data(ttl=86400)
def calculate_star_performance(ticker, star_level, holding_period=90):
    """
    Calculate historical performance for a given star rating
    Returns win rate, average profit/loss, VaR
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5y")
        
        if len(hist) < 252:
            return None
        
        results = []
        signals_found = 0
        
        for i in range(0, len(hist) - 120, 20):
            window = hist.iloc[:i+1] if i > 0 else hist.iloc[:1]
            
            if len(window) < 50:
                continue
            
            current_price = window['Close'].iloc[-1]
            high_52w = window['Close'].rolling(min(252, len(window)), min_periods=1).max().iloc[-1]
            drawdown_pct = (high_52w - current_price) / high_52w * 100 if high_52w > 0 else 0
            
            if drawdown_pct >= 30:
                signal_level = 5
            elif drawdown_pct >= 25:
                signal_level = 4
            elif drawdown_pct >= 20:
                signal_level = 3
            elif drawdown_pct >= 15:
                signal_level = 2
            elif drawdown_pct >= 10:
                signal_level = 1
            elif drawdown_pct >= 5:
                signal_level = 0
            else:
                signal_level = -1
            
            if abs(signal_level - star_level) < 0.5:
                signals_found += 1
                
                future_prices = hist['Close'].iloc[i+1:i+1+holding_period]
                if len(future_prices) > 20:
                    future_return = (future_prices.iloc[-1] / current_price - 1) * 100
                    results.append(future_return)
        
        if len(results) < 10:
            return None
        
        results = np.array(results)
        win_rate = np.sum(results > 0) / len(results)
        avg_win = np.mean(results[results > 0]) if np.sum(results > 0) > 0 else 0
        avg_loss = np.mean(results[results < 0]) if np.sum(results < 0) > 0 else 0
        
        var_95 = np.percentile(results, 5)
        
        if abs(avg_loss) > 0:
            profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        else:
            profit_loss_ratio = 0
        
        return {
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'var_95': var_95,
            'profit_loss_ratio': profit_loss_ratio,
            'sample_size': len(results),
            'results': results
        }
        
    except Exception as e:
        return None

# ========== Improved Signal System ==========
def get_buy_signal_improved(stock_drawdown, spx_drawdown=None, stock_quality=None, 
                            strength_score=0, strength_desc=""):
    """
    Improved signal system incorporating statistical information
    """
    if stock_drawdown >= 30:
        base_level = 5
    elif stock_drawdown >= 25:
        base_level = 4
    elif stock_drawdown >= 20:
        base_level = 3
    elif stock_drawdown >= 15:
        base_level = 2
    elif stock_drawdown >= 10:
        base_level = 1
    elif stock_drawdown >= 5:
        base_level = 0
    else:
        base_level = -1
    
    final_level = base_level + strength_score
    
    if stock_quality and not stock_quality['qualified'] and not stock_quality['is_core']:
        final_level -= 1
    
    final_level = max(-1, min(5, final_level))
    
    if final_level >= 4.5:
        stars = "⭐⭐⭐⭐⭐"
    elif final_level >= 3.5:
        stars = "⭐⭐⭐⭐"
    elif final_level >= 2.5:
        stars = "⭐⭐⭐"
    elif final_level >= 1.5:
        stars = "⭐⭐"
    elif final_level >= 0.5:
        stars = "⭐"
    elif final_level >= -0.5:
        stars = "⚪"
    else:
        stars = "⚫"
    
    if final_level >= 4:
        action = "STRONG BUY"
    elif final_level >= 3:
        action = "BUY"
    elif final_level >= 2:
        action = "CONSIDER BUYING"
    elif final_level >= 1:
        action = "WATCH"
    elif final_level >= 0:
        action = "CAUTIOUS WATCH"
    else:
        action = "HOLD"
    
    details = []
    if spx_drawdown is not None:
        details.append(f"Market drawdown: {spx_drawdown:.1f}%")
    if strength_desc:
        details.append(strength_desc)
    
    return {
        'stars': stars,
        'action': action,
        'level': final_level,
        'details': details
    }

# ========== Original Signal System ==========
def get_buy_signal_original(drawdown_decimal):
    """Original signal system"""
    if drawdown_decimal >= 0.30:
        return {"stars": "⭐⭐⭐⭐⭐", "action": "STRONG BUY", "level": 5}
    elif drawdown_decimal >= 0.25:
        return {"stars": "⭐⭐⭐⭐", "action": "AGGRESSIVE BUY", "level": 4}
    elif drawdown_decimal >= 0.20:
        return {"stars": "⭐⭐⭐", "action": "BUY", "level": 3}
    elif drawdown_decimal >= 0.15:
        return {"stars": "⭐⭐", "action": "CONSIDER BUYING", "level": 2}
    elif drawdown_decimal >= 0.10:
        return {"stars": "⭐", "action": "WATCH & BUY", "level": 1}
    elif drawdown_decimal >= 0.05:
        return {"stars": "", "action": "CAUTIOUS WATCH", "level": 0}
    else:
        return {"stars": "", "action": "HOLD", "level": -1}

# ========== Generate Quantitative Report ==========
def generate_quant_report(ticker, current_price, drawdown_pct, 
                          price_dist, strength_sig, star_level, 
                          star_performance, quality_info):
    """
    Generate natural language quantitative decision report
    """
    report = []
    
    z_score = price_dist['z_score']
    percentile = price_dist['percentile']
    support_2sigma = price_dist['support_levels']['-2σ']
    support_1sigma = price_dist['support_levels']['-1σ']
    
    if z_score < -2:
        position_desc = "extremely cheap (below -2σ)"
    elif z_score < -1:
        position_desc = "reasonably cheap (between -2σ and -1σ)"
    elif z_score < 0:
        position_desc = "slightly cheap (between -1σ and mean)"
    elif z_score < 1:
        position_desc = "slightly expensive (between mean and +1σ)"
    elif z_score < 2:
        position_desc = "reasonably expensive (between +1σ and +2σ)"
    else:
        position_desc = "extremely expensive (above +2σ)"
    
    report.append(f"{ticker} is currently at ${current_price:.2f}, which is {position_desc}.")
    report.append(f"Statistically, it's {abs(z_score):.2f} standard deviations from the mean, ")
    report.append(f"cheaper than {percentile:.1f}% of historical prices.")
    
    if star_performance:
        var_95 = star_performance['var_95']
        report.append(f"\nRisk Assessment (95% Confidence VaR):")
        report.append(f"If I buy now, there's a 95% probability that the price won't fall below ")
        report.append(f"${current_price * (1 + var_95/100):.2f} in the near term (based on historical patterns).")
        
        win_rate = star_performance['win_rate']
        avg_win = star_performance['avg_win']
        avg_loss = star_performance['avg_loss']
        pl_ratio = star_performance['profit_loss_ratio']
        
        report.append(f"\nProbability Analysis:")
        report.append(f"Historically, stocks at this star level ({star_level:.1f}⭐) have a ")
        report.append(f"{win_rate*100:.1f}% probability of rebounding in the next 3 months.")
        
        if win_rate < 0.4:
            report.append(f"The market is giving only a {win_rate*100:.1f}% chance of rebound, ")
            report.append(f"suggesting we might need more time to bottom.")
        elif win_rate > 0.6:
            report.append(f"The {win_rate*100:.1f}% win rate suggests this is a statistically favorable entry point.")
        
        report.append(f"\nRisk-Reward Ratio:")
        report.append(f"Average win: +{avg_win:.1f}% | Average loss: {avg_loss:.1f}% | ")
        report.append(f"Profit/Loss ratio: {pl_ratio:.2f}:1")
    
    report.append(f"\nTrading Decision:")
    if star_level >= 3:
        if z_score < -1.5:
            report.append(f"I can start with a small position here, and if it really drops to ")
            report.append(f"${support_2sigma:.2f} (the -2σ level), I'll consider adding more. ")
            report.append(f"This way, I follow my 52-week low logic while using VaR to manage risk, ")
            report.append(f"and incorporate market probabilities.")
        else:
            report.append(f"Current price isn't at historical extremes. I'll wait for a better entry point ")
            report.append(f"closer to ${support_1sigma:.2f} or ${support_2sigma:.2f}.")
    else:
        report.append(f"Not a statistically compelling entry point yet. Continue watching.")
    
    return " ".join(report)

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
    
    # ========== Market Index Selection ==========
    st.subheader("📊 Market Index Selection")
    
    if st.session_state.selected_stocks:
        current_ticker = st.session_state.selected_stocks[0]
        recommended = get_recommended_index(current_ticker)
        recommended_name = get_index_name(recommended)
        st.info(f"Based on {current_ticker}, recommended: **{recommended_name}**")
    
    selected_index = st.selectbox(
        "Choose benchmark index:",
        options=list(SECTOR_INDICES.keys()),
        index=0,
        help="Select the index for market comparison. System auto-recommends based on stock, but you can override."
    )
    
    index_symbol = SECTOR_INDICES[selected_index]
    
    market_data = get_market_data(index_symbol)
    if market_data:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Index",
                market_data['name']
            )
        with col2:
            st.metric(
                "52W Drawdown",
                f"{market_data['drawdown']:.1f}%",
                delta=f"{market_data['current_price']:.0f}"
            )
        
        if st.session_state.selected_stocks:
            recommended = get_recommended_index(st.session_state.selected_stocks[0])
            if index_symbol != recommended:
                recommended_name = get_index_name(recommended)
                st.caption(f"⚠️ Current selection differs from system recommendation ({recommended_name})")
    else:
        st.info("Selected index data unavailable")
    
    st.session_state.selected_index = index_symbol
    st.session_state.market_data = market_data
    
    st.divider()
    
    # ========== Index Guide ==========
    with st.expander("📚 Sector Index Guide", expanded=False):
        st.markdown("""
        **Major Indices:**
        - ^GSPC: S&P 500 (Broad Market)
        - ^NDX: NASDAQ 100 (Tech Heavy)
        - ^DJI: Dow Jones (Blue Chip)
        
        **Sector ETFs:**
        - XLK: Technology
        - SOXX: Semiconductors
        - XLF: Financials
        - XLV: Healthcare
        - XLE: Energy
        - XLP: Consumer Staples
        - XLC: Communication
        - XLI: Industrials
        - XLB: Materials
        - XLRE: Real Estate
        
        **Auto-Recommendation Logic:**
        - Tech Giants → NASDAQ 100
        - Financials → XLF
        - Energy → XLE
        - Healthcare → XLV
        - Default → S&P 500
        """)
    
    st.divider()
    
    # ========== Strategy Selection ==========
    st.subheader("📖 Investment Strategy")
    use_improved = st.checkbox("✨ Use Quantitative Decision System", value=True, 
                               help="Enable probability statistics, VaR, and confidence interval analysis")
    
    if use_improved:
        st.markdown("""
        **Quantitative Framework:**
        - 📊 **Price Distribution**: Z-score, percentile
        - 📈 **Win Rate**: Historical probability
        - 🛡️ **Risk Metrics**: 95% VaR
        - ⚖️ **Risk-Reward**: P/L ratio
        """)
    else:
        st.markdown("""
        **Original Signals:**
        - ⭐⭐⭐⭐⭐ 30%+ = STRONG BUY
        - ⭐⭐⭐⭐ 25%+ = AGGRESSIVE BUY  
        - ⭐⭐⭐ 20%+ = BUY
        - ⭐⭐ 15%+ = CONSIDER
        - ⭐ 10%+ = WATCH
        """)
    
    st.session_state.use_improved = use_improved

# ========== MAIN CONTENT ==========
if st.session_state.selected_stocks:
    st.header(f"📊 Analyzing {len(st.session_state.selected_stocks)} Stocks")
    
    market_data = st.session_state.get('market_data', None)
    
    if market_data:
        st.caption(f"📊 Benchmark Index: **{market_data['name']}** (52W Drawdown: {market_data['drawdown']:.1f}%)")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    quality_results = []
    
    for i, ticker in enumerate(st.session_state.selected_stocks):
        progress = (i + 1) / len(st.session_state.selected_stocks)
        progress_bar.progress(progress)
        status_text.text(f"Fetching data for {ticker}... ({i+1}/{len(st.session_state.selected_stocks)})")
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                high_52w = hist["Close"].rolling(252, min_periods=1).max().iloc[-1]
                drawdown_pct = (high_52w - current_price) / high_52w * 100 if high_52w > 0 else 0
                
                quality_info = check_stock_quality(ticker)
                quality_results.append({
                    'Ticker': ticker,
                    'Qualified': quality_info['qualified'],
                    'Issues': ', '.join(quality_info['issues']) if quality_info['issues'] else 'Pass',
                    'IsCore': '✓' if quality_info['is_core'] else ''
                })
                
                if st.session_state.get('use_improved', True):
                    price_dist = analyze_price_distribution(hist)
                    
                    if market_data and market_data['hist'] is not None:
                        strength_score, strength_desc = calculate_relative_strength_score(hist, market_data['hist'])
                    else:
                        strength_score, strength_desc = 0, "No market data"
                    
                    signal_info = get_buy_signal_improved(
                        drawdown_pct, 
                        market_data['drawdown'] if market_data else None,
                        quality_info,
                        strength_score,
                        strength_desc
                    )
                    
                    star_performance = calculate_star_performance(ticker, signal_info['level'])
                    
                    quant_report = generate_quant_report(
                        ticker, current_price, drawdown_pct,
                        price_dist, strength_desc, signal_info['level'],
                        star_performance, quality_info
                    )
                    
                    signal_display = f"{signal_info['stars']} {signal_info['action']}"
                    if signal_info['details']:
                        signal_display += f" ({'; '.join(signal_info['details'])})"
                    
                    st.session_state[f"report_{ticker}"] = quant_report
                    
                else:
                    signal_info = get_buy_signal_original(drawdown_pct / 100)
                    signal_display = f"{signal_info['stars']} {signal_info['action']}"
                
                results.append({
                    "Ticker": ticker,
                    "Current Price": f"${current_price:.2f}",
                    "52-Week High": f"${high_52w:.2f}",
                    "Drawdown": f"{drawdown_pct:.1f}%",
                    "Signal": signal_display,
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
    
    progress_bar.empty()
    status_text.empty()
    
    if st.session_state.get('use_improved', True) and quality_results:
        with st.expander("🔍 Stock Quality Check Details", expanded=False):
            quality_df = pd.DataFrame(quality_results)
            
            def color_qualified(val):
                if val == True:
                    return 'background-color: #90EE90'
                elif val == False:
                    return 'background-color: #FFB6C1'
                return ''
            
            styled_df = quality_df.style.map(color_qualified, subset=['Qualified'])
            st.dataframe(styled_df, use_container_width=True)
    
    if results:
        st.subheader("Analysis Results")
        df = pd.DataFrame(results)
        
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                "Sort by:",
                ["Drawdown (Desc)", "Level (Desc)", "Ticker (Asc)"]
            )
        
        if sort_by == "Drawdown (Desc)":
            def get_drawdown_value(val):
                if val == "N/A" or val == "Error":
                    return -999
                try:
                    return float(val.rstrip('%'))
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
        
        if st.session_state.get('use_improved', True):
            st.subheader("📈 Quantitative Decision Reports")
            
            for ticker in st.session_state.selected_stocks:
                report_key = f"report_{ticker}"
                if report_key in st.session_state:
                    with st.expander(f"📊 {ticker} - Quantitative Analysis", expanded=True):
                        st.markdown(f"```\n{st.session_state[report_key]}\n```")
        
        st.subheader("Price Charts")
        num_stocks = min(4, len(st.session_state.selected_stocks))
        
        if num_stocks > 0:
            if num_stocks == 1:
                for ticker in st.session_state.selected_stocks[:num_stocks]:
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="6mo")
                        if not hist.empty:
                            st.subheader(f"{ticker}")
                            fig, ax = plt.subplots(figsize=(10, 4))
                            ax.plot(hist.index, hist["Close"], linewidth=2, color='blue')
                            
                            mean_price = np.mean(hist["Close"])
                            std_price = np.std(hist["Close"])
                            
                            ax.axhline(y=mean_price, color='orange', linestyle='-', alpha=0.5, label=f'Mean: ${mean_price:.2f}')
                            ax.axhline(y=mean_price - std_price, color='gray', linestyle='--', alpha=0.5, label=f'-1σ: ${mean_price - std_price:.2f}')
                            ax.axhline(y=mean_price - 2*std_price, color='red', linestyle='--', alpha=0.5, label=f'-2σ: ${mean_price - 2*std_price:.2f}')
                            
                            if len(hist) > 20:
                                high_52w = hist["Close"].rolling(min(252, len(hist)), min_periods=1).max().iloc[-1]
                                current_price = hist["Close"].iloc[-1]
                                ax.axhline(y=high_52w, color='red', linestyle='--', alpha=0.5, label=f'52W High: ${high_52w:.2f}')
                            
                            ax.set_title(f"{ticker} - 6 Month Trend with Statistical Bands")
                            ax.set_xlabel("Date")
                            ax.set_ylabel("Price ($)")
                            ax.grid(True, alpha=0.3)
                            ax.legend(loc='upper left')
                            plt.xticks(rotation=45)
                            plt.tight_layout()
                            st.pyplot(fig)
                    except:
                        pass
            
            elif num_stocks == 2:
                cols = st.columns(2)
                for i, ticker in enumerate(st.session_state.selected_stocks[:num_stocks]):
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="6mo")
                        if not hist.empty:
                            with cols[i]:
                                fig, ax = plt.subplots(figsize=(10, 4))
                                ax.plot(hist.index, hist["Close"], linewidth=2, color='blue')
                                
                                mean_price = np.mean(hist["Close"])
                                std_price = np.std(hist["Close"])
                                
                                ax.axhline(y=mean_price, color='orange', linestyle='-', alpha=0.5, label=f'Mean')
                                ax.axhline(y=mean_price - std_price, color='gray', linestyle='--', alpha=0.5, label=f'-1σ')
                                ax.axhline(y=mean_price - 2*std_price, color='red', linestyle='--', alpha=0.5, label=f'-2σ')
                                
                                ax.set_title(f"{ticker}")
                                ax.grid(True, alpha=0.3)
                                ax.legend(loc='upper left')
                                plt.xticks(rotation=45)
                                plt.tight_layout()
                                st.pyplot(fig)
                    except:
                        pass
            
            else:
                cols = st.columns(2)
                for i, ticker in enumerate(st.session_state.selected_stocks[:num_stocks]):
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="6mo")
                        if not hist.empty:
                            with cols[i % 2]:
                                fig, ax = plt.subplots(figsize=(10, 4))
                                ax.plot(hist.index, hist["Close"], linewidth=2, color='blue')
                                
                                mean_price = np.mean(hist["Close"])
                                std_price = np.std(hist["Close"])
                                
                                ax.axhline(y=mean_price, color='orange', linestyle='-', alpha=0.5, label=f'Mean')
                                ax.axhline(y=mean_price - std_price, color='gray', linestyle='--', alpha=0.5, label=f'-1σ')
                                ax.axhline(y=mean_price - 2*std_price, color='red', linestyle='--', alpha=0.5, label=f'-2σ')
                                
                                ax.set_title(f"{ticker}")
                                ax.grid(True, alpha=0.3)
                                ax.legend(loc='upper left')
                                plt.xticks(rotation=45)
                                plt.tight_layout()
                                st.pyplot(fig)
                    except:
                        pass
        
        st.subheader("💾 Download Results")
        display_df = df[["Ticker", "Current Price", "52-Week High", "Drawdown", "Signal"]].copy()
        
        download_df = df[["Ticker", "Current Price", "52-Week High", "Drawdown"]].copy()
        download_df["Signal"] = df["Signal"].str.replace(r'[⭐★⚪⚫]', '', regex=True).str.strip()
        
        csv = download_df.to_csv(index=False).encode("utf-8-sig")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"results_{st.session_state.username}_{timestamp}.csv"
        download_df.to_csv(results_file, index=False, encoding='utf-8-sig')
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"stock_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2:
            st.info(f"Results saved to: `{results_file}`")
        
        st.subheader("Current Analysis")
        st.dataframe(display_df, use_container_width=True)
            
else:
    st.markdown("""
    ## 🎯 Welcome to Quantitative Stock Drawdown Analysis
    
    **How to use:**
    1. **Enter your username** in the sidebar
    2. **Add stocks** (e.g., AAPL, TSLA, NVDA)
    3. **Select stocks** from your watchlist
    4. **Click "Start Analysis"** to see results
    
    **Quantitative Features:**
    - 📊 **Price Distribution**: Z-score, percentile ranking
    - 📈 **Historical Win Rate**: Probability of rebound
    - 🛡️ **Risk Metrics**: 95% VaR, max drawdown
    - ⚖️ **Risk-Reward**: Profit/Loss ratio analysis
    - 📝 **Decision Report**: Natural language trading recommendations
    
    **Example stocks:**
    - AAPL, MSFT, GOOGL, NVDA, TSLA, TSM
    """)
    
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
    
    st.divider()
    if st.button("🚀 Quick Start with Default Stocks"):
        st.session_state.selected_stocks = ["AAPL", "MSFT", "GOOGL"]
        st.rerun()

# Footer
st.divider()
st.caption(f"👤 User: {st.session_state.username} | 📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💾 Data: Yahoo Finance | 🛠 Built with Streamlit")

st.sidebar.divider()
st.sidebar.caption(f"Streamlit v{st.__version__}")