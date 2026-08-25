@echo off
setlocal
cd /d "%~dp0.."
if exist "cortex.env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("cortex.env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
)
if exist "%USERPROFILE%\.config\opencode\cortex.env" if not defined CORTEX_API_KEY (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%USERPROFILE%\.config\opencode\cortex.env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
)
set PYTHONIOENCODING=utf-8
py -3 mcp\server.py
if errorlevel 1 python mcp\server.py
