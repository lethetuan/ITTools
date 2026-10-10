@echo off
title IT Tool LTT - Dong goi EXE Standalone
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ============================================================
echo   IT Tool LTT - Dong goi thanh file EXE Standalone
echo   Tac gia: Le The Tuan - Zalo: 0352 194 195
echo ============================================================
echo.

cd /d "%~dp0"

:: -- 1. Auto-detect Python interpreter --
set PYTHON_EXE=

:: 1. Try 'py' launcher
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=py
    goto :check_pyinstaller
)

:: 2. Scan known absolute install paths
for %%d in (C D E) do (
    for %%v in (315 314 313 312 311 310 39 38) do (
        if exist "%%d:\Python%%v\python.exe" (
            "%%d:\Python%%v\python.exe" --version >nul 2>&1
            if not errorlevel 1 (
                set PYTHON_EXE=%%d:\Python%%v\python.exe
                goto :check_pyinstaller
            )
        )
        if exist "%%d:\Program Files\Python%%v\python.exe" (
            "%%d:\Program Files\Python%%v\python.exe" --version >nul 2>&1
            if not errorlevel 1 (
                set PYTHON_EXE=%%d:\Program Files\Python%%v\python.exe
                goto :check_pyinstaller
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
            goto :check_pyinstaller
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
            goto :check_pyinstaller
        )
    )
)

echo.
echo [LOI] Khong tim thay Python 3.8+ hop le tren may nay!
echo Vui long cai dat Python 3.8+ tu: https://www.python.org/downloads/
echo.
pause
goto :eof

:: -- 2. Check & Install PyInstaller --
:check_pyinstaller
echo [OK] Dang dung Python: %PYTHON_EXE%
echo.

"%PYTHON_EXE%" -m PyInstaller --version >nul 2>&1
if not errorlevel 1 goto :clean_and_build

echo [!] PyInstaller chua duoc cai dat. Dang tu dong cai dat...
"%PYTHON_EXE%" -m pip install pyinstaller
if errorlevel 1 (
    echo [LOI] Cai dat PyInstaller that bai!
    pause
    goto :eof
)

:clean_and_build
echo [1/3] Don dep thu muc build cu...
if exist "dist\IT_Tool_LTT.exe" del /f /q "dist\IT_Tool_LTT.exe"
if exist "build\IT-Tools" rmdir /s /q "build\IT-Tools" 2>nul
echo [OK] Da don dep xong.
echo.

echo [2/3] Dang dong goi IT_Tool_LTT.exe (PyInstaller)...
echo      Qua trinh nay co the mat 1 - 2 phut, vui long cho...
echo.

"%PYTHON_EXE%" -m PyInstaller IT-Tools.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo ============================================================
    echo [LOI] Dong goi that bai! Kiem tra log phia tren de biet chi tiet.
    echo ============================================================
    pause
    goto :eof
)

echo.
echo ============================================================
echo [3/3] HOAN TAT! DONG GOI THANH CONG!
echo ============================================================
echo.

if not exist "dist\IT_Tool_LTT.exe" goto :exe_not_found

echo File EXE da tao tai:
for %%F in ("dist\IT_Tool_LTT.exe") do (
    echo   %%~fF
    echo   Kich thuoc: %%~zF bytes
)
echo.
echo HUONG DAN SU DUNG TREN MAY TINH KHAC:
echo   1. Chi can copy file dist\IT_Tool_LTT.exe sang may khac la chay duoc ngay.
echo   2. Khong can cai dat Python, pip, hay bat ky thu vien nao.
echo   3. File da duoc tich hop san quyen Administrator (UAC).
echo   4. May tinh chi can Windows 10/11 (da co san WebView2 Runtime).
echo ============================================================
echo.
echo Dang mo thu muc chua file EXE...
explorer.exe /select,"%~dp0dist\IT_Tool_LTT.exe"
goto :done

:exe_not_found
echo [CANH BAO] Khong tim thay file dist\IT_Tool_LTT.exe!

:done
echo.
pause

