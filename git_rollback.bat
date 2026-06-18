@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo   Git Rollback Tool - revert HEAD
echo ========================================
echo.

echo Last 10 commits:
echo.
"C:\Program Files\Git\bin\git.exe" log --oneline -10
echo.

echo Will revert HEAD - safe rollback, creates a new undo commit
echo.
set /p confirm=Confirm? Input y to continue, other to cancel: 

if /i not "!confirm!"=="y" (
    echo.
    echo Cancelled.
    pause
    exit /b
)

echo.
echo Reverting...
"C:\Program Files\Git\bin\git.exe" revert HEAD --no-edit

if %errorlevel% equ 0 (
    echo.
    echo Success! Revert commit created.
    echo.
    echo Latest commits:
    "C:\Program Files\Git\bin\git.exe" log --oneline -3
    echo.
    set /p push=Push to GitHub now? Input y to push, other to skip: 
    if /i "!push!"=="y" (
        "C:\Program Files\Git\bin\git.exe" push
        echo Push done.
    )
) else (
    echo.
    echo Revert failed. Please check git status.
)

echo.
pause
