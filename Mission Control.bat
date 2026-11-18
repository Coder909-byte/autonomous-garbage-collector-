@echo off
rem Double-click to start Mission Control and share it with phones on the ROVER-CTRL Wi-Fi.
cd /d "%~dp0"
echo Building Mission Control...
call npm run build || goto failed
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8787"
call npm run share
goto end
:failed
echo Build failed. If this is the first run after git pull, connect to the internet and run: npm install
:end
pause
