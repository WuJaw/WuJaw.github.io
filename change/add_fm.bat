@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
python change\add_front_matter.py
pause