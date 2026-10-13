@echo off
setlocal EnableExtensions
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0\..\.." || (
  echo ERROR: Cannot access the APA repository.
  exit /b 1
)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  py -3.11 -c "import sys; print(sys.version)" >nul 2>&1
  if %ERRORLEVEL% EQU 0 (
    py -3.11 tools\apa_knowledge_graph\bootstrap.py --repo-root .
    goto :done
  )
)
python tools\apa_knowledge_graph\bootstrap.py --repo-root .
:done
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Python 3.11 or source files unavailable.
  echo This script cannot install the required Archicad or MCP host.
  exit /b 1
)
echo.
echo APA Knowledge index is ready in the local user cache.
echo To use GPT integration, add the optional MCP stdio command printed above
echo to a compatible MCP client. No source projects or PLN files were changed.
exit /b 0
