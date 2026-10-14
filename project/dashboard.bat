@echo off
cd /d "%~dp0"
if "%OPENROUTER_API_KEY%"=="" set /p OPENROUTER_API_KEY=Paste your OpenRouter key (or just press Enter for offline Replay mode):
python dashboard\server.py
pause
