@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   DXF2SVG - Interaktywny Konwerter
echo ========================================
echo.

REM Przejdź do folderu skryptu
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

REM ============================================
REM KROK 1: Sprawdź czy Python jest zainstalowany
REM ============================================
echo [1/4] Sprawdzanie Pythona...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ BŁĄD: Python nie jest zainstalowany!
    echo.
    echo 📥 Aby zainstalować Pythona:
    echo    1. Odwiedź: https://www.python.org/downloads/
    echo    2. Pobierz Python 3.13 lub nowszy
    echo    3. WAŻNE: Podczas instalacji zaznacz "Add Python to PATH"
    echo    4. Po instalacji uruchom ponownie ten skrypt
    echo.
    pause
    exit /b 1
)

REM Pobierz wersję Pythona
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% jest zainstalowany

REM ============================================
REM KROK 2: Sprawdź czy pip działa
REM ============================================
echo [2/4] Sprawdzanie pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ BŁĄD: pip nie działa!
    echo.
    echo 📥 Naprawiam pip...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo ❌ Nie udało się naprawić pip. Zainstaluj Pythona ponownie.
        pause
        exit /b 1
    )
)
echo ✅ pip jest gotowy

REM ============================================
REM KROK 3: Zainstaluj wymagane biblioteki
REM ============================================
echo [3/4] Sprawdzanie wymaganych bibliotek...

REM Sprawdź czy ezdxf jest zainstalowane
python -c "import ezdxf" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 📦 Instaluję ezdxf...
    python -m pip install ezdxf>=1.0.0 --quiet
    if %errorlevel% neq 0 (
        echo ❌ Nie udało się zainstalować ezdxf
        pause
        exit /b 1
    )
    echo ✅ ezdxf zainstalowane
) else (
    echo ✅ ezdxf już zainstalowane
)

REM Sprawdź czy Pillow jest zainstalowane
python -c "from PIL import Image" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 📦 Instaluję Pillow...
    python -m pip install Pillow>=10.0.0 --quiet
    if %errorlevel% neq 0 (
        echo ❌ Nie udało się zainstalować Pillow
        pause
        exit /b 1
    )
    echo ✅ Pillow zainstalowane
) else (
    echo ✅ Pillow już zainstalowane
)

REM Sprawdź czy svgwrite jest zainstalowane
python -c "import svgwrite" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 📦 Instaluję svgwrite...
    python -m pip install svgwrite>=1.4.0
    if %errorlevel% neq 0 (
        echo ❌ Nie udało się zainstalować svgwrite
        pause
        exit /b 1
    )
    echo ✅ svgwrite zainstalowane
) else (
    echo ✅ svgwrite już zainstalowane
)

REM Sprawdź czy scipy jest zainstalowane
python -c "import scipy" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 📦 Instaluję scipy...
    python -m pip install scipy>=1.10.0
    if %errorlevel% neq 0 (
        echo ❌ Nie udało się zainstalować scipy
        pause
        exit /b 1
    )
    echo ✅ scipy zainstalowane
) else (
    echo ✅ scipy już zainstalowane
)

REM Sprawdź tkinter
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ BŁĄD: tkinter nie jest dostępny!
    echo.
    echo    tkinter jest częścią standardowej biblioteki Pythona.
    echo    Być może Python został zainstalowany bez opcji "tcl/tk and IDLE".
    echo.
    echo 📥 Aby naprawić:
    echo    1. Odinstaluj obecną wersję Pythona
    echo    2. Zainstaluj ponownie z: https://www.python.org/downloads/
    echo    3. Podczas instalacji upewnij się że "tcl/tk and IDLE" jest zaznaczone
    echo.
    pause
    exit /b 1
)
echo ✅ tkinter jest dostępny

REM ============================================
REM KROK 4: Uruchom aplikację
REM ============================================
echo [4/4] Uruchamianie GUI...
echo.
echo ========================================
echo   Aplikacja startuje...
echo ========================================
echo.

REM Sprawdź czy podano argument konfiguracji
if "%1"=="" (
    python run_interactive_gui.py
) else (
    echo Ładuję konfigurację: %1
    python run_interactive_gui.py --config %1
)

REM Jeśli aplikacja się zakończyła z błędem, wstrzymaj okno
if %errorlevel% neq 0 (
    echo.
    echo ❌ Aplikacja zakończyła się z błędem (kod: %errorlevel%)
    pause
)

