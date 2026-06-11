@echo off
echo Installing required packages from requirements.txt...
echo.
python -m pip install -r requirements.txt --quiet
echo.
echo All packages installed!
echo.
echo Starting stock analysis app...
echo Press Ctrl+C to stop
echo.
python -m streamlit run app.py
pause
