@echo off
REM Launch calculator.py from this folder
setlocal
pushd "%~dp0"

REM Activate virtualenv if present
if exist venv\Scripts\activate.bat (
  call venv\Scripts\activate.bat
)

REM Install required packages
echo Installing dependencies...
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -m pip install -q -r requirements.txt
  goto :python_check
)
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python -m pip install -q -r requirements.txt
)

:python_check
REM Prefer the Python launcher, fall back to python on PATH
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 calculator.py %*
  pause
  goto :EOF
)
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python calculator.py %*
  pause
  goto :EOF
)

echo Python not found. Install Python or add it to PATH.
pause
popd
endlocal
exit /b 1