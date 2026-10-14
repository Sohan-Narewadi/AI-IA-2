@echo off
cd /d "%~dp0"
if "%OPENROUTER_API_KEY%"=="" set /p OPENROUTER_API_KEY=Paste your OpenRouter key and press Enter:
python run_demo.py
pause
