@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
  "%LocalAppData%\Programs\Python\Python311\python.exe" -X utf8 "%~dp0apa_bootstrap.py" %*
  if errorlevel 1 pause
  exit /b
)
py -3.11-64 -c "import sys; assert sys.version_info[:2] == (3, 11)" >nul 2>&1
if not errorlevel 1 (
  py -3.11-64 -X utf8 "%~dp0apa_bootstrap.py" %*
  if errorlevel 1 pause
  exit /b
)
echo APA requires Python 3.11 x64. See docs\APA-WINDOWS.md.
pause
exit /b 2
