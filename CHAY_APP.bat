@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Dang mo app cham bai Toan...
python -m streamlit run app.py
pause
