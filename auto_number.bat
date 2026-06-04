@echo off
cd /d "%~dp0"

python -c "print('ok')" >nul 2>&1
if %errorlevel% neq 0 (
    echo 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

python python\auto_number_headings.py _posts\
pause
