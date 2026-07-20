@echo off
REM One-shot setup: virtualenv, pinned dependencies, and a verification run.
REM Usage:  setup.bat
setlocal

echo == 1/4  Creating virtual environment ==
python -m venv .venv
if errorlevel 1 goto error

set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo ERROR: could not find the venv interpreter.
  goto error
)

echo == 2/4  Installing pinned dependencies ^(requirements.lock^) ==
"%PY%" -m pip install --upgrade pip -q
if errorlevel 1 goto error
"%PY%" -m pip install -r requirements.lock -q
if errorlevel 1 goto error

echo == 3/4  Installing this package ==
"%PY%" -m pip install -e . --no-deps -q
if errorlevel 1 goto error

echo == 4/4  Verifying: harness tests ^(no model calls^) ==
"%PY%" -m pytest -q -m "not smoke"
if errorlevel 1 goto error

echo.
echo SETUP COMPLETE.
echo Next:
echo   run.bat --smoke     quick check against a tiny model ^(needs Ollama^)
echo   run.bat             full 3-model matrix
exit /b 0

:error
echo.
echo SETUP FAILED.
exit /b 1
