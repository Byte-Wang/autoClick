@echo off
chcp 65001 > nul

cd /d "%~dp0"

python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)

pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Error: PyInstaller installation failed
        pause
        exit /b 1
    )
)

echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Warning: Some dependencies failed to install
)

echo Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo Starting packaging...
pyinstaller auto_tool.spec --clean --noconfirm

if errorlevel 1 (
    echo Error: Packaging process failed
    echo Trying fallback solution...
    
    pyinstaller --onedir --windowed --icon=icon.png --name auto_tool --add-data "icon.png;." --add-data "config.json;." --add-data "git-download.html;." --hidden-import=cv2 --hidden-import=numpy --hidden-import=pyautogui --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageGrab --clean --noconfirm main.py
    
    if errorlevel 1 (
        echo Error: Fallback packaging solution also failed
        pause
        exit /b 1
    )
)

echo.
echo ===============================================
echo Packaging completed!
echo ===============================================
echo.
echo Generated exe file location: dist\auto_tool\auto_tool.exe
echo.
echo Important notes:
echo 1. Copy the entire dist\auto_tool directory to target computer
echo 2. Ensure target computer has necessary Visual C++ runtime libraries installed
echo 3. Administrator privileges may be required for first run
echo.

echo Checking generated files...
if exist "dist\auto_tool\auto_tool.exe" (
    echo ✓ Main program file generated
    dir "dist\auto_tool\*.dll" /b > nul 2>&1
    if not errorlevel 1 (
        echo ✓ DLL files included
    ) else (
        echo ⚠ Warning: No DLL files detected
    )
    
    echo.
    echo File list:
    dir "dist\auto_tool" /b
) else (
    echo ❌ Error: Main program file not generated
)

echo.
pause