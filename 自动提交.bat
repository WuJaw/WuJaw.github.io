@echo off
cd /d "%~dp0"
git add .
for /f "delims=" %%a in ('git status --porcelain 2^>nul') do (
  set "files=!files! [%%a]"
)
if "!files!"=="" (
  echo 无变更，跳过提交。
  exit /b
)
set "msg=Auto-commit: !files!"
git commit -m "!msg!" && git push
if errorlevel 1 (
  echo 推送失败。
) else (
  echo 推送成功: !msg!
)
pause
