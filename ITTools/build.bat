@echo off
chcp 65001 >nul
echo ============================================================
echo   IT Tool LTT - Build Script
echo   Dong goi thanh file EXE chay tren moi may tinh
echo ============================================================
echo.

cd /d "%~dp0"

:: Auto-detect Python
set PYTHON=
where python >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
) else (
    py --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON=py
    ) else if exist "C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
        set PYTHON=C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe
    )
)

if "%PYTHON%"=="" (
    echo [LOI] Khong tim thay Python! Vui long cai dat Python 3.8+ va them vao PATH.
    pause
    exit /b 1
)

echo [OK] Dang dung Python: %PYTHON%
"%PYTHON%" --version

:: Kiem tra PyInstaller
"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller chua duoc cai dat. Dang cai dat...
    "%PYTHON%" -m pip install pyinstaller
)

:: Xoa thu muc build cu
echo.
echo [1/3] Don dep thu muc build cu...
if exist "dist\IT_Tool_LTT.exe" del /f /q "dist\IT_Tool_LTT.exe"
if exist "build" rmdir /s /q "build"

:: Build EXE
echo.
echo [2/3] Dang dong goi IT_Tool_LTT.exe (PyInstaller)...
echo      Qua trinh nay co the mat 1 - 2 phut, vui long cho...
"%PYTHON%" -m PyInstaller IT_Tool_LTT.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo [LOI] Dong goi that bai! Kiem tra log phia tren de biet chi tiet.
    pause
    exit /b 1
)

:: Ket qua
echo.
echo ============================================================
echo [3/3] HOAN TAT! DONG GOI THANH CONG!
echo.
echo File EXE: dist\IT_Tool_LTT.exe
for %%F in ("dist\IT_Tool_LTT.exe") do (
    echo Kich thuoc: %%~zF bytes (~%%~zF / 1048576 MB)
)
echo.
echo HUONG DAN SU DUNG TREN MAY TINH KHAC:
echo   1. Chi can copy duy nhat file "dist\IT_Tool_LTT.exe" sang may khac.
echo   2. Khong can cai dat Python, pip, hay bat ky thu vien nao.
echo   3. File da duoc tich hop san quyen Administrator (UAC).
echo   4. May tinh chi can Windows 10/11 (da co san WebView2 Runtime).
echo ============================================================
pause
