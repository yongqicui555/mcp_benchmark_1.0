@echo off
echo ============================================
echo   CHANGELOGAI - Publish to npm
echo ============================================
echo.
echo Se non hai un account npm, creane uno su https://www.npmjs.com/signup
echo.
echo [1] Login npm...
call npm adduser
echo.
echo [2] Publishing changelogai to npm...
call npm publish
echo.
echo [DONE] Pacchetto pubblicato!
echo Installa ovunque con: npm install -g changelogai
pause
