@echo off
title IT Tool LTT - Internal Build Script
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   IT Tool LTT - Build Script
echo   Dong goi thanh file EXE chay tren moi may tinh
echo ============================================================
echo.

cd /d "%~dp0"

:: ── 1. Tu dong tim kiem Python hop le ──────────────────────────
set "PYTHON_EXE="

py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    goto :found_python
)

for /f "tokens=*" %%i in ('where python 2^>nul') do (
    echo %%i | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        "%%i" --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=%%i"
            goto :found_python
        )
    )
)

for %%v in (315 314 313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" (
        "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
            goto :found_python
        )
    )
)

for %%d in (C D E) do (
    for %%v in (315 314 313 312 311 310 39 38) do (
        if exist "%%d:\Python%%v\python.exe" (
            "%%d:\Python%%v\python.exe" --version >nul 2>&1
            if not errorlevel 1 (
                set "PYTHON_EXE=%%d:\Python%%v\python.exe"
                goto :found_python
            )
        )
    )
)

:found_python
if "%PYTHON_EXE%"=="" (
    echo [LOI] Khong tim thay Python 3.8+ hop le tren he thong!
    pause
    exit /b 1
)

echo [OK] Dang su dung Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version
echo.

:: ── 2. Kiem tra PyInstaller ────────────────────────────────────
"%PYTHON_EXE%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller chua duoc cai dat. Dang cai dat...
    "%PYTHON_EXE%" -m pip install pyinstaller
)

:: ── 3. Don dep thu muc build cu ────────────────────────────────
echo [1/3] Don dep thu muc build cu...
if exist "dist\IT_Tool_LTT.exe" del /f /q "dist\IT_Tool_LTT.exe"
if exist "build" rmdir /s /q "build" 2>nul

:: ── 4. Build EXE ───────────────────────────────────────────────
echo.
echo [2/3] Dang dong goi IT_Tool_LTT.exe (PyInstaller)...
echo      Qua trinh nay co the mat 1 - 2 phut, vui long cho...
"%PYTHON_EXE%" -m PyInstaller IT_Tool_LTT.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo [LOI] Dong goi that bai! Kiem tra log phia tren de biet chi tiet.
    pause
    exit /b 1
)

:: ── 5. Ket qua ─────────────────────────────────────────────────
echo.
echo ============================================================
echo [3/3] HOAN TAT! DONG GOI THANH CONG!
echo.
set "OUT_EXE=%~dp0dist\IT_Tool_LTT.exe"
if exist "%OUT_EXE%" (
    for %%F in ("%OUT_EXE%") do (
        set /a "SIZE_MB=%%~zF / 1048576"
        echo File EXE: %%~fF
        echo Kich thuoc: %%~zF bytes (~!SIZE_MB! MB)
    )
    echo.
    echo HUONG DAN SU DUNG TREN MAY TINH KHAC:
    echo   1. Chi can copy duy nhat file "dist\IT_Tool_LTT.exe" sang may khac.
    echo   2. Khong can cai dat Python, pip, hay bat ky thu vien nao.
    echo   3. File da duoc tich hop san quyen Administrator (UAC).
    echo   4. May tinh chi can Windows 10/11 (da co san WebView2 Runtime).
    explorer.exe /select,"%OUT_EXE%"
)
echo ============================================================
pause
