@echo off
echo 安装所需包...
echo.
python -m pip install streamlit==1.24.0 --quiet
python -m pip install yfinance --quiet
python -m pip install pandas --quiet
python -m pip install numpy --quiet
python -m pip install matplotlib --quiet
echo.
echo 所有包安装完成！
echo.
echo 启动股票分析应用...
echo 按 Ctrl+C 停止应用
echo.
python -m streamlit run app.py
pause