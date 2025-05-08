@echo off
echo Web Monitor starting...
cd /d %~dp0
python -m src.monitor
if %ERRORLEVEL% NEQ 0 (
  echo Error: Web Monitor execution failed with code %ERRORLEVEL%
  pause
) else (
  echo Web Monitor completed successfully.
) 
