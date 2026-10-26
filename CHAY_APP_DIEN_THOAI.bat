@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Dang mo app cham bai Toan cho dien thoai trong cung Wi-Fi.
echo Dia chi may tinh:
ipconfig | findstr /i "IPv4"
echo.
echo Tren iPhone mo Safari, go: http://<dia chi IPv4>:8501
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
pause
