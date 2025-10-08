@echo off
REM ================================
REM اجرای برنامه مدیریت دامنه و هاست
REM ================================

cd /d "%~dp0"

echo -------------------------------------------------
echo 🚀 Starting Domain ^& Hosting Management App
echo -------------------------------------------------

REM فعال‌سازی محیط مجازی (اختیاری)
REM call venv\Scripts\activate

REM خواندن متغیرهای فایل .env و تنظیم آن‌ها در محیط ویندوز
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    set "%%a=%%b"
)

REM بررسی اینکه فایل app.py وجود دارد
if not exist app.py (
    echo ❌ فایل app.py پیدا نشد!
    pause
    exit /b
)

REM اجرای برنامه
python app.py

echo -------------------------------------------------
echo ✅ Flask app is now running on http://127.0.0.1:5000
echo -------------------------------------------------
pause
