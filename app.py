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
CORE_STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'TSM']

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

# Sector classification for concentration warning
STOCK_SECTOR_CLASSIFICATION = {
    'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
    'GOOG': 'Technology', 'AMZN': 'Technology', 'META': 'Technology',
    'NVDA': 'Technology', 'TSLA': 'Technology', 'TSM': 'Technology',
    'AMD': 'Technology', 'INTC': 'Technology', 'NFLX': 'Technology',
    'ADBE': 'Technology', 'CRM': 'Technology', 'QCOM': 'Technology',
    'TXN': 'Technology', 'AVGO': 'Technology',
    'JPM': 'Financials', 'BAC': 'Financials', 'WFC': 'Financials',
    'C': 'Financials', 'GS': 'Financials', 'MS': 'Financials',
    'V': 'Financials', 'MA': 'Financials', 'AXP': 'Financials',
    'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy',
    'SLB': 'Energy', 'EOG': 'Energy',
    'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'MRK': 'Healthcare',
    'ABBV': 'Healthcare', 'UNH': 'Healthcare', 'LLY': 'Healthcare',
    'PG': 'Consumer Staples', 'KO': 'Consumer Staples', 'PEP': 'Consumer Staples',
    'WMT': 'Consumer Staples', 'COST': 'Consumer Staples',
}

STOCK_SECTOR_MAP = {
    'AAPL': '^NDX', 'MSFT': '^NDX', 'GOOGL': '^NDX', 'GOOG': '^NDX',
    'AMZN': '^NDX', 'META': '^NDX', 'NVDA': '^NDX', 'TSLA': '^NDX',
    'TSM': '^NDX', 'AMD': '^NDX', 'INTC': '^NDX', 'NFLX': '^NDX',
    'ADBE': '^NDX', 'CRM': '^NDX',
    'JPM': 'XLF', 'BAC': 'XLF', 'WFC': 'XLF', 'C': 'XLF',
    'GS': 'XLF', 'MS': 'XLF', 'V': 'XLF', 'MA': 'XLF', 'AXP': 'XLF',
    'XOM': 'XLE', 'CVX': 'XLE', 'COP': 'XLE', 'SLB': 'XLE', 'EOG': 'XLE',
    'JNJ': 'XLV', 'PFE': 'XLV', 'MRK': 'XLV', 'ABBV': 'XLV',
    'UNH': 'XLV', 'LLY': 'XLV',
    'PG': 'XLP', 'KO': 'XLP', 'PEP': 'XLP', 'WMT': 'XLP', 'COST': 'XLP',
    'TSM': 'SOXX', 'NVDA': 'SOXX', 'AMD': 'SOXX', 'INTC': 'SOXX',
    'QCOM': 'SOXX', 'TXN': 'SOXX', 'AVGO': 'SOXX',
}

# ========== Sector Concentration Warning ==========
def check_sector_concentration(tickers):
    """
    Warn when >2 stocks from the same sector are selected.
    Returns dict of sector -> list of tickers.
    """
    sector_map = {}
    unknown = []
    for t in tickers:
        sector = STOCK_SECTOR_CLASSIFICATION.get(t)
        if sector:
            sector_map.setdefault(sector, []).append(t)
        else:
            # Try live lookup
            try:
                info = yf.Ticker(t).info
                sector = info.get('sector', 'Unknown')
                sector_map.setdefault(sector, []).append(t)
            except:
                unknown.append(t)

    concentrated = {s: tks for s, tks in sector_map.items() if len(tks) > 2}
    return concentrated, sector_map

# ========== Get Recommended Index ==========
def get_recommended_index(ticker):
    if ticker in STOCK_SECTOR_MAP:
        return STOCK_SECTOR_MAP[ticker]
    try:
        stock = yf.Ticker(ticker)
        sector = stock.info.get('sector', '')
        sector_to_index = {
            'Technology': '^NDX', 'Financial Services': 'XLF',
            'Healthcare': 'XLV', 'Energy': 'XLE',
            'Consumer Defensive': 'XLP', 'Consumer Cyclical': 'XLY',
            'Communication Services': 'XLC', 'Industrials': 'XLI',
            'Basic Materials': 'XLB', 'Real Estate': 'XLRE',
        }
        if sector in sector_to_index:
            return sector_to_index[sector]
    except:
        pass
    return '^GSPC'

def get_index_name(symbol):
    name_map = {
        '^GSPC': 'S&P 500', '^NDX': 'NASDAQ 100', '^DJI': 'Dow Jones',
        '^RUT': 'Russell 2000', 'XLK': 'Technology Sector',
        'SOXX': 'Semiconductor Sector', 'XLF': 'Financial Sector',
        'XLV': 'Healthcare Sector', 'XLP': 'Consumer Staples',
        'XLE': 'Energy Sector', 'XLC': 'Communication Services',
        'XLI': 'Industrial Sector', 'XLB': 'Materials Sector',
        'XLRE': 'Real Estate Sector',
    }
    return name_map.get(symbol, symbol)

# ========== Get Market Data ==========
@st.cache_data(ttl=3600)
def get_market_data(index_symbol):
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
        return {
            'qualified': len(issues) == 0,
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
            'price': 0, 'market_cap': 0, 'volume_value': 0,
            'exchange': '', 'is_core': False
        }

# ========== Price Distribution Analysis ==========
def analyze_price_distribution(hist):
    prices = hist['Close'].values
    current_price = prices[-1]
    mean_price = np.mean(prices)
    std_price = np.std(prices)
    z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
    percentile = stats.percentileofscore(prices, current_price)
    return {
        'z_score': z_score,
        'percentile': percentile,
        'is_extreme_cheap': z_score < -2,
        'is_extreme_expensive': z_score > 2,
        'mean_price': mean_price,
        'std_price': std_price,
        'support_levels': {
            '-2σ': mean_price - 2 * std_price,
            '-1σ': mean_price - 1 * std_price,
            'mean': mean_price,
            '+1σ': mean_price + 1 * std_price,
            '+2σ': mean_price + 2 * std_price
        }
    }

# ========== REVISED: Volatility-Adjusted Drawdown Percentile ==========
@st.cache_data(ttl=86400)
def get_historical_drawdown_distribution(ticker):
    """
    Compute the stock's own historical drawdown distribution over 5 years.
    Returns the list of rolling max-drawdown values so current drawdown
    can be expressed as a percentile of its own history — not a fixed threshold.
    This solves the 'one-size-fits-all threshold' problem.
    """
    try:
        hist = yf.Ticker(ticker).history(period="5y")
        if len(hist) < 252:
            return None
        closes = hist['Close']
        rolling_max = closes.rolling(252, min_periods=20).max()
        drawdowns = (rolling_max - closes) / rolling_max * 100
        return drawdowns.dropna().values
    except:
        return None

def get_drawdown_percentile(ticker, current_drawdown_pct):
    """
    What percentile is today's drawdown in this stock's own 5-year drawdown history?
    Higher percentile = more extreme drawdown = stronger mean-reversion case.
    Returns (percentile, confidence_label)
    """
    dist = get_historical_drawdown_distribution(ticker)
    if dist is None or len(dist) < 50:
        return None, "insufficient history"
    percentile = stats.percentileofscore(dist, current_drawdown_pct)
    if percentile >= 90:
        label = "historically extreme (top 10%)"
    elif percentile >= 75:
        label = "above average drawdown (top 25%)"
    elif percentile >= 50:
        label = "moderate drawdown"
    else:
        label = "below average drawdown"
    return percentile, label

# ========== NEW: Statistical Entry Ladder ==========
def calculate_entry_ladder(ticker, current_price, high_52w, price_dist):
    """
    Compute price levels where this stock's drawdown would become
    statistically significant BY ITS OWN HISTORY.

    NOT a prediction of where price will go — a translation of
    'at what price does my own framework say the odds improve?'

    Levels:
    - 75th pct drawdown: entry-worthy (above-average drawdown for this stock)
    - 90th pct drawdown: strong entry (historically rare for this stock)
    - -1σ / -2σ price levels from past-year distribution
    """
    dist = get_historical_drawdown_distribution(ticker)
    if dist is None or len(dist) < 50:
        return None

    dd_75 = np.percentile(dist, 75)   # drawdown % at 75th percentile
    dd_90 = np.percentile(dist, 90)   # drawdown % at 90th percentile

    price_at_75 = high_52w * (1 - dd_75 / 100)
    price_at_90 = high_52w * (1 - dd_90 / 100)

    ladder = []

    # Sort all candidate levels below current price, most conservative last
    candidates = [
        (price_at_75, f"75th pct drawdown (-{dd_75:.1f}%)", "Above-average drawdown for this stock — initial entry zone"),
        (price_dist['support_levels']['-1σ'], "-1σ price level", "One std dev below past-year mean"),
        (price_at_90, f"90th pct drawdown (-{dd_90:.1f}%)", "Historically rare drawdown — strong entry zone"),
        (price_dist['support_levels']['-2σ'], "-2σ price level", "Two std devs below past-year mean — extreme"),
    ]

    for price, name, desc in candidates:
        status = "✅ Already below" if current_price <= price else f"{(price/current_price - 1)*100:+.1f}% from here"
        ladder.append({
            'price': price,
            'name': name,
            'description': desc,
            'status': status,
            'reached': current_price <= price
        })

    ladder.sort(key=lambda x: x['price'], reverse=True)
    return ladder

# ========== REVISED: Momentum Score (separate from mean-reversion) ==========
def calculate_momentum_score(stock_hist, market_hist):
    """
    Pure momentum overlay — kept SEPARATE from mean-reversion star rating.
    Returns a score and description. Not blended into stars.

    Previous version added this linearly to star level, creating a contradiction:
    strong momentum + deep drawdown = higher buy signal, which conflates
    two opposing strategies. Now returned independently so the user can
    consciously apply whichever lens they prefer.
    """
    combined = pd.DataFrame({
        'stock': stock_hist['Close'],
        'market': market_hist['Close']
    }).dropna()

    if len(combined) < 30:
        return 0, "Insufficient data"

    stock_ret = combined['stock'].pct_change().dropna()
    market_ret = combined['market'].pct_change().dropna()
    excess = stock_ret - market_ret

    mean_excess = np.mean(excess) * 252
    std_excess = np.std(excess) * np.sqrt(252)
    recent_excess = excess[-60:].mean() * 252 if len(excess) >= 60 else mean_excess

    z = recent_excess / std_excess if std_excess > 0 else 0

    if z > 1.5:
        return 2, "🔥 Strong outperformer (momentum favors continuation)"
    elif z > 0.5:
        return 1, "📈 Mild outperformer"
    elif z > -0.5:
        return 0, "➡️ In line with market"
    elif z > -1.5:
        return -1, "📉 Mild underperformer"
    else:
        return -2, "❄️ Strong underperformer (momentum caution)"

# ========== REVISED: Mean-Reversion Signal (volatility-adjusted) ==========
def get_mean_reversion_signal(stock_drawdown_pct, drawdown_percentile, quality_info):
    """
    Pure mean-reversion signal based on:
    1. Raw drawdown %
    2. Drawdown percentile vs stock's own history (volatility-adjusted)
    Quality penalty applied only when drawdown_percentile is available.

    No momentum blending here — that's a separate lens.
    """
    # Base level from raw drawdown
    if stock_drawdown_pct >= 30:
        base = 5
    elif stock_drawdown_pct >= 25:
        base = 4
    elif stock_drawdown_pct >= 20:
        base = 3
    elif stock_drawdown_pct >= 15:
        base = 2
    elif stock_drawdown_pct >= 10:
        base = 1
    elif stock_drawdown_pct >= 5:
        base = 0
    else:
        base = -1

    # Volatility-adjusted boost/penalty using stock's own history
    if drawdown_percentile is not None:
        if drawdown_percentile >= 90:
            adj = +1.0   # This is a genuinely rare drawdown for THIS stock
        elif drawdown_percentile >= 75:
            adj = +0.5
        elif drawdown_percentile >= 50:
            adj = 0
        elif drawdown_percentile >= 25:
            adj = -0.5   # Drawdown is actually mild for this volatile stock
        else:
            adj = -1.0   # Very common drawdown, not a meaningful signal
    else:
        adj = 0

    final = base + adj

    # Quality penalty
    if quality_info and not quality_info['qualified'] and not quality_info['is_core']:
        final -= 0.5

    final = max(-1, min(5, final))

    if final >= 4.5:
        stars, action = "⭐⭐⭐⭐⭐", "STRONG BUY"
    elif final >= 3.5:
        stars, action = "⭐⭐⭐⭐", "BUY"
    elif final >= 2.5:
        stars, action = "⭐⭐⭐", "CONSIDER BUYING"
    elif final >= 1.5:
        stars, action = "⭐⭐", "WATCH"
    elif final >= 0.5:
        stars, action = "⭐", "CAUTIOUS WATCH"
    elif final >= -0.5:
        stars, action = "⚪", "NEUTRAL"
    else:
        stars, action = "⚫", "HOLD"

    return {'stars': stars, 'action': action, 'level': final}

# ========== REVISED: Backtest with Confidence Label ==========
@st.cache_data(ttl=86400)
def calculate_star_performance(ticker, star_level, holding_period=90):
    """
    Historical win rate at this star level for this stock.
    Now explicitly labels confidence based on sample size so users
    don't over-trust statistics from thin data.
    """
    MINIMUM_RELIABLE_SAMPLES = 15  # Below this, treat as illustrative only

    try:
        hist = yf.Ticker(ticker).history(period="5y")
        if len(hist) < 252:
            return None

        results = []

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
                future_prices = hist['Close'].iloc[i+1:i+1+holding_period]
                if len(future_prices) > 20:
                    future_return = (future_prices.iloc[-1] / current_price - 1) * 100
                    results.append(future_return)

        if len(results) < 5:
            return None

        results = np.array(results)
        n = len(results)
        win_rate = np.sum(results > 0) / n
        avg_win = np.mean(results[results > 0]) if np.sum(results > 0) > 0 else 0
        avg_loss = np.mean(results[results < 0]) if np.sum(results < 0) > 0 else 0
        var_95 = np.percentile(results, 5)
        pl_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        # Confidence label based on sample size (check largest threshold first!)
        if n >= 30:
            confidence = "good confidence"
            confidence_color = "🟢"
        elif n >= MINIMUM_RELIABLE_SAMPLES:
            confidence = "moderate confidence"
            confidence_color = "🟡"
        else:
            confidence = f"⚠️ low confidence — treat as illustrative"
            confidence_color = "🔴"

        return {
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'var_95': var_95,
            'profit_loss_ratio': pl_ratio,
            'sample_size': n,
            'confidence': confidence,
            'confidence_color': confidence_color,
            'results': results
        }

    except:
        return None

# ========== Quantitative Report ==========
def generate_quant_report(ticker, current_price, drawdown_pct,
                          price_dist, momentum_score, momentum_desc,
                          signal_info, star_performance,
                          drawdown_percentile, drawdown_percentile_label,
                          entry_ladder=None):
    report = []
    z = price_dist['z_score']
    pct = price_dist['percentile']
    s2 = price_dist['support_levels']['-2σ']
    s1 = price_dist['support_levels']['-1σ']

    if z < -2:
        pos = "historically cheap (below -2σ)"
    elif z < -1:
        pos = "cheap (between -2σ and -1σ)"
    elif z < 0:
        pos = "slightly below average"
    elif z < 1:
        pos = "slightly above average"
    elif z < 2:
        pos = "expensive (between +1σ and +2σ)"
    else:
        pos = "historically expensive (above +2σ)"

    report.append(f"📍 PRICE POSITION")
    report.append(f"{ticker} at ${current_price:.2f} is {pos}.")
    report.append(f"Z-score: {z:.2f} | Cheaper than {pct:.1f}% of past year prices.")

    report.append(f"\n📉 DRAWDOWN CONTEXT")
    report.append(f"Current drawdown: {drawdown_pct:.1f}% from 52W high.")
    if drawdown_percentile is not None:
        report.append(f"Drawdown percentile vs own 5Y history: {drawdown_percentile:.0f}th pct — {drawdown_percentile_label}.")
        report.append(f"(A NVDA -20% is different from a KO -20%. This adjusts for that.)")
    else:
        report.append("5Y drawdown history unavailable — using raw thresholds only.")

    report.append(f"\n📊 MEAN-REVERSION SIGNAL: {signal_info['stars']} {signal_info['action']}")

    report.append(f"\n🏃 MOMENTUM OVERLAY (separate lens)")
    report.append(f"{momentum_desc}")
    if momentum_score > 0 and signal_info['level'] >= 3:
        report.append("Note: Strong momentum + deep drawdown can mean falling knife OR genuine recovery. Verify catalyst.")
    elif momentum_score < 0 and signal_info['level'] >= 3:
        report.append("Note: Weak momentum + deep drawdown is the classic mean-reversion setup. Higher risk, higher potential reward.")

    if star_performance:
        n = star_performance['sample_size']
        conf = star_performance['confidence']
        wr = star_performance['win_rate']
        aw = star_performance['avg_win']
        al = star_performance['avg_loss']
        pl = star_performance['profit_loss_ratio']
        var = star_performance['var_95']

        report.append(f"\n📈 HISTORICAL BACKTEST ({conf}, n={n})")
        report.append(f"Win rate at this signal level: {wr*100:.1f}%")
        report.append(f"Avg win: +{aw:.1f}% | Avg loss: {al:.1f}% | P/L ratio: {pl:.2f}:1")
        report.append(f"95% VaR (historical sim): {var:.1f}% — worst 5% of similar setups.")
        if n < 15:
            report.append("⚠️ Small sample — use for direction only, not precise probability.")

    report.append(f"\n💡 DECISION FRAMEWORK")
    if signal_info['level'] >= 3:
        if drawdown_percentile and drawdown_percentile >= 75:
            report.append(f"This is a historically extreme drawdown for {ticker} specifically.")
            report.append(f"Consider initial position here. Add at ${s2:.2f} (-2σ) if it continues falling.")
        else:
            report.append(f"Drawdown meets threshold but is not extreme vs this stock's own history.")
            report.append(f"Watch for ${s1:.2f} (-1σ) or ${s2:.2f} (-2σ) as better entries.")
    else:
        report.append("Not a compelling mean-reversion entry yet. Continue monitoring.")

    if entry_ladder:
        report.append(f"\n🎯 STATISTICAL ENTRY LADDER")
        report.append(f"Prices where {ticker}'s drawdown becomes significant by its OWN history.")
        report.append(f"These are odds-improvement levels, not predictions:")
        for rung in entry_ladder:
            marker = "►" if rung['reached'] else "○"
            report.append(f"  {marker} ${rung['price']:.2f}  {rung['name']}  [{rung['status']}]")
            report.append(f"      {rung['description']}")
        report.append(f"Ladder logic: scale in gradually as levels are reached — never all at once.")
        report.append(f"If price never gets there, the trade simply doesn't happen. That's discipline, not failure.")

    return "\n".join(report)

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Control Panel")

    st.subheader("👤 User Profile")
    username = st.text_input("Username:", value=st.session_state.username)

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
    new_stocks = st.text_input("Enter stock symbols (comma separated)", placeholder="Example: MSFT, AMZN, META")

    if st.button("Add to Watchlist", type="primary"):
        if new_stocks:
            stocks = [s.strip().upper() for s in new_stocks.split(",") if s.strip()]
            added = 0
            for stock in stocks:
                if stock not in st.session_state.watchlist:
                    st.session_state.watchlist.append(stock)
                    added += 1
            if added > 0:
                user_file = f"watchlist_{st.session_state.username}.json"
                with open(user_file, 'w') as f:
                    json.dump(st.session_state.watchlist, f, indent=2)
                st.success(f"✅ Added {added} stock(s). Total: {len(st.session_state.watchlist)}")
                time.sleep(0.5)
                st.rerun()
            else:
                st.info("Already in watchlist")

    st.divider()
    st.subheader("📋 Your Watchlist")
    if st.session_state.watchlist:
        selected = st.multiselect("Select stocks to analyze", st.session_state.watchlist)
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
    st.subheader("📊 Market Index Selection")
    if st.session_state.selected_stocks:
        current_ticker = st.session_state.selected_stocks[0]
        recommended = get_recommended_index(current_ticker)
        st.info(f"Recommended for {current_ticker}: **{get_index_name(recommended)}**")

    selected_index = st.selectbox(
        "Choose benchmark index:",
        options=list(SECTOR_INDICES.keys()),
        index=0
    )
    index_symbol = SECTOR_INDICES[selected_index]
    market_data = get_market_data(index_symbol)

    if market_data:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Index", market_data['name'])
        with col2:
            st.metric("52W Drawdown", f"{market_data['drawdown']:.1f}%",
                      delta=f"{market_data['current_price']:.0f}")
    else:
        st.info("Index data unavailable")

    st.session_state.selected_index = index_symbol
    st.session_state.market_data = market_data

    st.divider()
    with st.expander("📚 Sector Index Guide", expanded=False):
        st.markdown("""
        **Major Indices:** ^GSPC (S&P 500), ^NDX (NASDAQ 100), ^DJI (Dow Jones)

        **Sector ETFs:** XLK Tech | SOXX Semi | XLF Finance | XLV Health
        XLE Energy | XLP Staples | XLC Comms | XLI Industrial

        **Auto-recommendation:** Tech Giants → NASDAQ 100 | Financials → XLF
        Energy → XLE | Healthcare → XLV | Default → S&P 500
        """)

    st.divider()
    st.subheader("📖 Strategy Mode")
    st.markdown("""
    **Mean-Reversion** (this app's core):
    Buys after significant drawdowns expecting recovery.
    Signal = drawdown % + how extreme vs stock's own history.

    **Momentum** (shown separately):
    Displayed as an independent overlay, NOT blended into stars.
    Use it to ask: *is the stock still falling, or stabilizing?*

    ⚠️ These two strategies can conflict. The app shows both
    so you make the final judgment call.
    """)

# ========== MAIN CONTENT ==========
if st.session_state.selected_stocks:
    st.header(f"📊 Analyzing {len(st.session_state.selected_stocks)} Stocks")

    market_data = st.session_state.get('market_data', None)
    if market_data:
        st.caption(f"📊 Benchmark: **{market_data['name']}** (52W Drawdown: {market_data['drawdown']:.1f}%)")

    # ========== Sector Concentration Warning ==========
    concentrated, sector_breakdown = check_sector_concentration(st.session_state.selected_stocks)
    if concentrated:
        with st.warning("⚠️ **Sector Concentration Risk**"):
            for sector, tickers in concentrated.items():
                st.write(f"**{sector}**: {', '.join(tickers)} ({len(tickers)} stocks)")
            st.write("These stocks are highly correlated. This is NOT 3 independent bets — it's concentrated sector exposure.")

    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    quality_results = []

    for i, ticker in enumerate(st.session_state.selected_stocks):
        progress_bar.progress((i + 1) / len(st.session_state.selected_stocks))
        status_text.text(f"Fetching {ticker}... ({i+1}/{len(st.session_state.selected_stocks)})")

        try:
            hist = yf.Ticker(ticker).history(period="1y")

            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                high_52w = hist["Close"].rolling(252, min_periods=1).max().iloc[-1]
                drawdown_pct = (high_52w - current_price) / high_52w * 100 if high_52w > 0 else 0

                quality_info = check_stock_quality(ticker)
                quality_results.append({
                    'Ticker': ticker,
                    'Qualified': quality_info['qualified'],
                    'Issues': ', '.join(quality_info['issues']) if quality_info['issues'] else 'Pass',
                    'Core': '✓' if quality_info['is_core'] else ''
                })

                price_dist = analyze_price_distribution(hist)

                # Volatility-adjusted drawdown percentile
                dd_percentile, dd_label = get_drawdown_percentile(ticker, drawdown_pct)

                # Mean-reversion signal (no momentum blending)
                signal_info = get_mean_reversion_signal(drawdown_pct, dd_percentile, quality_info)

                # Momentum as separate overlay
                if market_data and market_data['hist'] is not None:
                    momentum_score, momentum_desc = calculate_momentum_score(hist, market_data['hist'])
                else:
                    momentum_score, momentum_desc = 0, "No market data"

                # Backtest with confidence label
                star_performance = calculate_star_performance(ticker, signal_info['level'])

                # Statistical entry ladder
                entry_ladder = calculate_entry_ladder(ticker, current_price, high_52w, price_dist)

                # Next unreached entry level (for summary table)
                next_entry = None
                if entry_ladder:
                    unreached = [r for r in entry_ladder if not r['reached']]
                    if unreached:
                        next_entry = unreached[0]['price']

                # Full report
                quant_report = generate_quant_report(
                    ticker, current_price, drawdown_pct,
                    price_dist, momentum_score, momentum_desc,
                    signal_info, star_performance,
                    dd_percentile, dd_label,
                    entry_ladder
                )
                st.session_state[f"report_{ticker}"] = quant_report
                st.session_state[f"momentum_{ticker}"] = (momentum_score, momentum_desc)
                st.session_state[f"dd_pct_{ticker}"] = (dd_percentile, dd_label)

                results.append({
                    "Ticker": ticker,
                    "Price": f"${current_price:.2f}",
                    "52W High": f"${high_52w:.2f}",
                    "Drawdown": f"{drawdown_pct:.1f}%",
                    "DD Percentile": f"{dd_percentile:.0f}th" if dd_percentile else "N/A",
                    "Next Entry": f"${next_entry:.2f}" if next_entry else "At/below all levels",
                    "Mean-Rev Signal": f"{signal_info['stars']} {signal_info['action']}",
                    "Momentum": momentum_desc.split("(")[0].strip(),
                    "Level": signal_info['level']
                })
            else:
                results.append({
                    "Ticker": ticker, "Price": "No data", "52W High": "No data",
                    "Drawdown": "N/A", "DD Percentile": "N/A", "Next Entry": "N/A",
                    "Mean-Rev Signal": "NO DATA", "Momentum": "N/A", "Level": -2
                })

        except Exception as e:
            results.append({
                "Ticker": ticker, "Price": "Error", "52W High": "Error",
                "Drawdown": "Error", "DD Percentile": "N/A", "Next Entry": "N/A",
                "Mean-Rev Signal": "ERROR", "Momentum": "N/A", "Level": -2
            })

    progress_bar.empty()
    status_text.empty()

    if quality_results:
        with st.expander("🔍 Stock Quality Check", expanded=False):
            quality_df = pd.DataFrame(quality_results)
            def color_qualified(val):
                if val == True: return 'background-color: #90EE90'
                elif val == False: return 'background-color: #FFB6C1'
                return ''
            st.dataframe(quality_df.style.map(color_qualified, subset=['Qualified']),
                        use_container_width=True)

    if results:
        st.subheader("Analysis Results")
        df = pd.DataFrame(results)

        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox("Sort by:", ["Drawdown (Desc)", "DD Percentile (Desc)", "Level (Desc)", "Ticker (Asc)"])

        if sort_by == "Drawdown (Desc)":
            df['_sort'] = df['Drawdown'].apply(lambda v: float(v.rstrip('%')) if v not in ("N/A","Error") else -999)
        elif sort_by == "DD Percentile (Desc)":
            df['_sort'] = df['DD Percentile'].apply(lambda v: float(v.replace('th','')) if v != 'N/A' else -999)
        elif sort_by == "Level (Desc)":
            df['_sort'] = df['Level']
        else:
            df['_sort'] = df['Ticker']

        df = df.sort_values('_sort', ascending=(sort_by == "Ticker (Asc)")).drop('_sort', axis=1)

        display_cols = ["Ticker", "Price", "52W High", "Drawdown", "DD Percentile", "Next Entry", "Mean-Rev Signal", "Momentum"]
        st.dataframe(df[display_cols], use_container_width=True)

        st.caption("""
        **How to read this table:**
        - **DD Percentile**: How extreme is today's drawdown vs this stock's own 5-year history. 90th = rare drawdown for this stock.
        - **Next Entry**: The next price level where this stock's drawdown becomes statistically significant by its own history. A decision rule, NOT a price prediction — see the full report for the complete entry ladder.
        - **Mean-Rev Signal**: Star rating based on drawdown depth, adjusted for the stock's own volatility profile.
        - **Momentum**: Independent overlay. Shown separately — not blended into the star rating.
        """)

        st.subheader("📈 Quantitative Decision Reports")
        for ticker in st.session_state.selected_stocks:
            report_key = f"report_{ticker}"
            if report_key in st.session_state:
                with st.expander(f"📊 {ticker} — Full Analysis", expanded=False):
                    st.text(st.session_state[report_key])

        # Price Charts
        st.subheader("Price Charts")
        num_stocks = min(4, len(st.session_state.selected_stocks))
        cols = st.columns(min(2, num_stocks))

        for i, ticker in enumerate(st.session_state.selected_stocks[:num_stocks]):
            try:
                hist = yf.Ticker(ticker).history(period="6mo")
                if not hist.empty:
                    with cols[i % len(cols)]:
                        fig, ax = plt.subplots(figsize=(10, 4))
                        ax.plot(hist.index, hist["Close"], linewidth=2, color='steelblue')

                        mean_p = np.mean(hist["Close"])
                        std_p = np.std(hist["Close"])
                        ax.axhline(mean_p, color='orange', linestyle='-', alpha=0.6, label=f'Mean ${mean_p:.0f}')
                        ax.axhline(mean_p - std_p, color='gray', linestyle='--', alpha=0.5, label=f'-1σ ${mean_p-std_p:.0f}')
                        ax.axhline(mean_p - 2*std_p, color='red', linestyle='--', alpha=0.5, label=f'-2σ ${mean_p-2*std_p:.0f}')

                        high_52w = hist["Close"].rolling(min(252, len(hist)), min_periods=1).max().iloc[-1]
                        ax.axhline(high_52w, color='green', linestyle=':', alpha=0.5, label=f'52W High ${high_52w:.0f}')

                        ax.set_title(f"{ticker} — 6 Month")
                        ax.set_xlabel("Date")
                        ax.set_ylabel("Price ($)")
                        ax.grid(True, alpha=0.3)
                        ax.legend(loc='best', fontsize=8)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig)
            except:
                pass

        # Download
        st.subheader("💾 Download Results")
        download_df = df[["Ticker", "Price", "52W High", "Drawdown", "DD Percentile", "Next Entry", "Momentum"]].copy()
        csv = download_df.to_csv(index=False).encode("utf-8-sig")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"stock_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

else:
    st.markdown("""
    ## 🎯 Welcome to Quantitative Stock Drawdown Analysis

    **How to use:**
    1. Enter your username in the sidebar
    2. Add stocks (e.g., AAPL, TSLA, NVDA)
    3. Select stocks from your watchlist
    4. Click **Start Analysis**

    **What's improved in this version:**
    - 📊 **Volatility-adjusted signals**: A 20% drawdown on NVDA ≠ a 20% drawdown on KO
    - 🔀 **Momentum shown separately**: No longer blended into the star rating
    - ⚠️ **Sector concentration warning**: Flags when you're piling into one sector
    - 🎯 **Confidence labels**: Backtest stats now show sample size and reliability
    """)

    st.divider()
    st.subheader("📂 Available User Data")
    user_files = [f for f in os.listdir() if f.startswith("watchlist_") and f.endswith(".json")]
    if user_files:
        for file in user_files:
            uname = file.replace("watchlist_", "").replace(".json", "")
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    st.write(f"- **{uname}**: {len(data)} stocks")
            except:
                st.write(f"- **{uname}**: (corrupted)")
    else:
        st.info("No user data found. Start by adding stocks!")

    st.divider()
    if st.button("🚀 Quick Start with Default Stocks"):
        st.session_state.selected_stocks = ["AAPL", "MSFT", "GOOGL"]
        st.rerun()

# Footer
st.divider()
st.caption(f"👤 {st.session_state.username} | 📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💾 Data: Yahoo Finance | Strategy: Mean-Reversion + Momentum Overlay (separate)")
st.sidebar.divider()
st.sidebar.caption(f"Streamlit v{st.__version__}")
