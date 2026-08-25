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
echo Cortex Hub  http://127.0.0.1:3848/
py -3 hub\server.py
if errorlevel 1 python hub\server.py
