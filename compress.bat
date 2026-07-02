@echo off
chcp 65001 >nul
echo Compressing images in assets/ ...
C:\Users\wuergou\.workbuddy\binaries\python\envs\default\Scripts\python.exe "%~dp0python\compress_images.py"
echo.
pause
