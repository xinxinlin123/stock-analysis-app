# 📈 Stock 52-Week Drawdown Analysis

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stock-analysis-app-52weekspricelimit.streamlit.app/)

A stock analysis tool based on 52-week drawdown to identify buying opportunities. When a stock price falls from its 52-week high to specific thresholds, the system generates corresponding buy signals.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 👥 **Multi-User System** | Each user has an independent watchlist with auto-save |
| 📊 **6-Level Signal System** | From ⭐⭐⭐⭐⭐ to ⭐, precisely identify buying opportunities |
| 📈 **Real-time Data** | Get latest stock data from Yahoo Finance |
| 📉 **Visual Charts** | 6-month price trends with 52-week high markers |
| 💾 **Auto Save** | Analysis results automatically saved as CSV files |
| 🎯 **Smart Sorting** | Sort by drawdown, signal level, or stock ticker |

---

## 📊 Investment Signal Guide

| Drawdown | Signal | Stars | Action |
|---------|--------|-------|--------|
| 30%+ | STRONG BUY | ⭐⭐⭐⭐⭐ | Strong Buy |
| 25%+ | AGGRESSIVE BUY | ⭐⭐⭐⭐ | Aggressive Buy |
| 20%+ | BUY | ⭐⭐⭐ | Buy |
| 15%+ | CONSIDER BUYING | ⭐⭐ | Consider Buying |
| 10%+ | WATCH & BUY | ⭐ | Watch & Buy |
| 5%+ | CAUTIOUS WATCH | - | Cautious Watch |

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.8 or higher
- pip package manager

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/StockApp.git
cd StockApp

# Install dependencies
pip install -r requirements.txt

# Launch the application
streamlit run app.py
```

---

## 📖 Usage Guide

### **Step 1: Set Up User**
- Enter username in the left sidebar
- Click "Switch User" to change accounts
- Each user's watchlist is saved independently

### **Step 2: Add Stocks**
- Enter stock symbols (e.g., AAPL, TSLA, MSFT)
- Supports batch addition, comma-separated
- Click "Add to Watchlist"

### **Step 3: Analyze Stocks**
- Select stocks from your watchlist
- Click "Start Analysis"
- View analysis results and charts

### **Step 4: Export Data**
- Click "Download as CSV"
- Results are automatically saved locally

---

## 📁 Project Structure

```
StockApp/
├── app.py                 # Main application file
├── requirements.txt       # Dependencies list
├── .gitignore            # Git ignore file
├── README.md             # Project documentation
├── run_app.bat           # Windows one-click launch script
├── watchlist_*.json      # User watchlists (auto-generated)
└── results_*.csv         # Analysis results (auto-generated)
```

---

## 📦 Dependencies

```txt
streamlit==1.24.0        # Web application framework
yfinance==0.2.28         # Yahoo Finance data
pandas==2.0.0            # Data analysis
numpy==1.24.0            # Numerical computing
matplotlib==3.7.0        # Data visualization
```

---

## 🔧 Troubleshooting

### Q: The application won't start?
A: Ensure Python version ≥ 3.8, run `python --version` to check.

### Q: Failed to fetch stock data?
A: Yahoo Finance occasionally times out, just retry.

### Q: How to clear user data?
A: Delete `watchlist_*.json` files.

### Q: Charts not displaying?
A: Reinstall matplotlib: `pip install matplotlib==3.7.0`

---

## 🤝 Contributing

Welcome to submit Issues and Pull Requests!

1. Fork the project
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request


## 📄 License

MIT License © 2024 [Your Name]


## 🌟 Support

If this project helps you, please give it a Star ⭐


**Last Updated:** February 11, 2026
