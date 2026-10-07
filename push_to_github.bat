@echo off
cd /d "%~dp0"
echo =================================================================
echo   Pushing SIH2026146 to GitHub (origin main)
echo =================================================================
git push -u origin main
echo.
pause
