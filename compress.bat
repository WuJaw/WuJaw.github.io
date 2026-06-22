@echo off
chcp 65001 >nul
echo 正在压缩 assets/ 目录图片...
C:\Users\wuergou\.workbuddy\binaries\python\envs\default\Scripts\python.exe "%~dp0python\compress_images.py"
echo.
pause
