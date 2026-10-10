@echo off
title IT Tool LTT - Le The Tuan
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0ITTools"
echo Starting IT Tool LTT...
echo Author: Le The Tuan - Phone/Zalo: 0352 194 195
echo Website: https://lethetuanpc.blogspot.com
echo Telegram: https://t.me/lethetuanpc
echo.

:: -- Auto-detect Python interpreter --
set PYTHON_EXE=

:: 1. Try 'py' launcher
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=py
    goto :check_deps
)

:: 2. Scan known absolute install paths
for %%d in (C D E) do (
    for %%v in (315 314 313 312 311 310 39 38) do (
        if exist "%%d:\Python%%v\python.exe" (
            "%%d:\Python%%v\python.exe" --version >nul 2>&1
            if not errorlevel 1 (
                set PYTHON_EXE=%%d:\Python%%v\python.exe
                goto :check_deps
            )
        )
        if exist "%%d:\Program Files\Python%%v\python.exe" (
            "%%d:\Program Files\Python%%v\python.exe" --version >nul 2>&1
            if not errorlevel 1 (
                set PYTHON_EXE=%%d:\Program Files\Python%%v\python.exe
                goto :check_deps
            )
        )
    )
)

:: 3. Check per-user AppData install
for %%v in (315 314 313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" (
        "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" --version >nul 2>&1
        if not errorlevel 1 (
            set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe
            goto :check_deps
        )
    )
)

:: 4. Try 'python' from PATH but EXCLUDE Windows Store aliases
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    echo %%i | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        "%%i" --version >nul 2>&1
        if not errorlevel 1 (
            set PYTHON_EXE=%%i
            goto :check_deps
        )
    )
)

echo.
echo [LOI] Khong tim thay Python 3.8+ hop le tren may nay!
echo.
echo Vui long cai dat Python 3.8+ tu:
echo   https://www.python.org/downloads/
echo.
echo Luu y: Khi cai, chon "Add Python to PATH" va bo chon Microsoft Store alias.
echo Sau khi cai xong, chay lai IT-Tools.bat
echo.
pause
goto :eof

:: -- Dependency Check and Auto-install --
:check_deps
echo [OK] Dang dung Python: %PYTHON_EXE%
echo.

:: Check if pywebview is installed
"%PYTHON_EXE%" -c "import webview" >nul 2>&1
if not errorlevel 1 goto :run

:: pywebview not found - install requirements
echo [!] Chua cai thu vien. Dang tu dong cai dat...
echo     (Qua trinh nay chi thuc hien 1 lan duy nhat)
echo.
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet
"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet

:: Verify installation
"%PYTHON_EXE%" -c "import webview" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [LOI] Cai dat thu vien that bai!
    echo Kiem tra ket noi mang va thu lai, hoac chay lenh thu cong:
    echo   pip install pywebview pythonnet Pillow psutil
    echo.
    pause
    goto :eof
)

echo.
echo [OK] Cai dat thu vien thanh cong!
echo.

:run
"%PYTHON_EXE%" main.py
if errorlevel 1 (
    echo.
    echo [LOI] Ung dung bi dung hoac xay ra loi khi chay.
    echo Kiem tra lai thu vien: pip install -r requirements.txt
    echo.
    pause
)
