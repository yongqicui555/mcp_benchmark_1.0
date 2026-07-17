@echo off
echo ============================================
echo   CHANGELOGAI - One-Click Publish
echo ============================================
echo.
echo This script publishes changelogai to all channels:
echo   1. npm registry (global install)
echo   2. Gumroad ($9 product)
echo.
echo ============================================
echo   STEP 1: npm
echo ============================================
echo.
call npm whoami 2>nul
if errorlevel 1 (
    echo [!] Not logged in to npm.
    echo     Run: npm adduser
    echo.
    call npm adduser
)
echo.
echo [npm] Publishing to npm registry...
call npm publish
echo.
if not errorlevel 1 (
    echo [OK] Published to npm!
    echo     Users can install with: npm install -g changelogai
) else (
    echo [!] npm publish failed. Check errors above.
)
echo.
echo ============================================
echo   STEP 2: Pack tarball
echo ============================================
echo.
call npm pack
echo [OK] Tarball created.
echo.
echo ============================================
echo   STEP 3: Gumroad
echo ============================================
echo.
echo Open Gumroad in your browser and create the product manually:
echo   URL: https://app.gumroad.com/products/new
echo.
echo   Name: changelogai — AI Changelog Generator CLI
echo   Price: $9
echo   File: Upload the .tgz tarball from this folder
echo.
echo Or run the Playwright upload script:
echo   node "%~dp0..\Documents\GumroadProducts\upload_changelogai.js"
echo.
echo ============================================
echo   DONE
echo ============================================
echo.
echo Distribution channels:
echo   npm: npm install -g changelogai
echo   URL: npm install -g https://files.catbox.moe/eiv7q2.tgz
echo   Gumroad: (check browser)
echo.
pause
