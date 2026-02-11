# 📈 Stock 52-Week Drawdown Analysis

基于52周跌幅的股票分析工具，帮助识别买入机会。当股票价格从52周高点下跌达到特定阈值时，系统会给出相应的买入信号。

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.24.0-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 👥 **多用户系统** | 每个用户独立的观察列表，自动保存 |
| 📊 **6级信号系统** | 从⭐⭐⭐⭐⭐到⭐，精确识别买入时机 |
| 📈 **实时数据** | 从Yahoo Finance获取最新股票数据 |
| 📉 **可视化图表** | 6个月价格趋势，52周高点标记 |
| 💾 **自动保存** | 分析结果自动保存为CSV文件 |
| 🎯 **智能排序** | 按跌幅、信号级别、股票代码排序 |

---

## 📊 投资信号说明

| 跌幅 | 信号 | 星级 | 建议 |
|------|------|------|------|
| 30%+ | STRONG BUY | ⭐⭐⭐⭐⭐ | 强烈买入 |
| 25%+ | AGGRESSIVE BUY | ⭐⭐⭐⭐ | 积极买入 |
| 20%+ | BUY | ⭐⭐⭐ | 买入 |
| 15%+ | CONSIDER BUYING | ⭐⭐ | 考虑买入 |
| 10%+ | WATCH & BUY | ⭐ | 观察并买入 |
| 5%+ | CAUTIOUS WATCH | - | 谨慎观察 |

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.8 或更高版本
- pip包管理器

### 2. 安装步骤

```bash
# 克隆项目
git clone https://github.com/你的用户名/StockApp.git
cd StockApp

# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py