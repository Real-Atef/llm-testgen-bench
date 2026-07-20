@echo off
REM Run the benchmark and render the leaderboard.
REM Usage:
REM   run.bat                  full default matrix (3 models x 21 tasks)
REM   run.bat --smoke          2 easiest tasks against the smoke model
REM   run.bat <model[,model]>  a specific model or comma-separated list
setlocal

set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo No virtualenv found. Run setup.bat first.
  exit /b 1
)

REM Ollama must be up: every run needs local inference.
curl -sf http://localhost:11434/v1/models >nul 2>&1
if errorlevel 1 (
  echo ERROR: Ollama is not reachable at http://localhost:11434
  echo Start it with 'ollama serve', then pull a model, e.g.:
  echo   ollama pull qwen2.5-coder:7b
  exit /b 1
)

if "%~1"=="--smoke" (
  echo == Smoke run: 2 easiest tasks x smoke model ==
  "%PY%" -m llm_testgen_bench.cli run --smoke
) else if "%~1"=="" (
  echo == Full matrix: qwen2.5-coder:7b, llama3.1:8b, qwen2.5:7b x 21 tasks ==
  echo    ^(CPU-bound; expect roughly an hour^)
  "%PY%" -m llm_testgen_bench.cli run --models qwen2.5-coder:7b,llama3.1:8b,qwen2.5:7b --tasks all --k 1
) else (
  echo == Custom run: %~1 ==
  "%PY%" -m llm_testgen_bench.cli run --models "%~1" --tasks all --k 1
)
if errorlevel 1 exit /b 1

"%PY%" -m llm_testgen_bench.cli report
echo.
echo Done. See results\leaderboard.md and results\kill_rates.png
exit /b 0
