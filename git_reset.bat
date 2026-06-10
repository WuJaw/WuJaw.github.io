@echo off
cd /d "%~dp0"

echo === git reset ===
echo.

"C:\Program Files\Git\bin\git.exe" checkout -f main
"C:\Program Files\Git\bin\git.exe" clean -fd

if %errorlevel% equ 0 (
    echo.
    echo OK - reset to main
) else (
    echo.
    echo FAILED - check network or git status
)

echo.
pause
