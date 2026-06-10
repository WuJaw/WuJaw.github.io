@echo off

:: ============================================================
::  一键部署：标题自动编号 → 添加 Front Matter → 图片转 Web 路径 → Git 提交推送
:: ============================================================

:: 切换到 bat 所在目录（项目根目录）
cd /d "%~dp0"

:: --- 步骤 0：检测 Python ---
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 未找到 Python，请先安装 Python 并添加到 PATH。
    echo.
    pause
    exit /b 1
)

echo ==================================================
echo  Python 已找到，开始执行...
echo ==================================================
echo.

:: --- 步骤 1：标题自动编号 ---
echo [1/4] 标题自动编号...
python python\auto_number_headings.py _posts\
if %errorlevel% neq 0 (
    echo.
    echo [错误] 标题自动编号失败，已中止。
    echo.
    pause
    exit /b 1
)
echo.

:: --- 步骤 2：添加 Front Matter ---
echo [2/4] 添加 Front Matter...
python python\add_front_matter.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] 添加 Front Matter 失败，已中止。
    echo.
    pause
    exit /b 1
)
echo.

:: --- 步骤 3：图片路径转 Web 格式 ---
echo [3/4] 图片路径转 Web 格式...
python python\fix_img_path.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] 图片路径转换失败，已中止。
    echo.
    pause
    exit /b 1
)
echo.

:: --- 步骤 4：Git 自动提交推送 ---
echo [4/4] Git 自动提交推送...
python python\autocommit.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] Git 提交推送失败，已中止。
    echo.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo  全部完成！
echo ==================================================
pause
