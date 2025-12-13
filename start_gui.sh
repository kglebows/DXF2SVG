#!/bin/bash
# -*- coding: utf-8 -*-
# DXF2SVG - Interactive Converter Startup Script dla Linux/macOS

set -e  # Przerwij przy błędzie

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "   DXF2SVG - Interaktywny Konwerter"
echo "========================================"
echo ""

# Sprawdź czy skrypt nie jest uruchamiany jako root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  UWAGA: Nie uruchamiaj tego skryptu z sudo!${NC}"
    echo -e "${YELLOW}   Uruchom jako zwykły użytkownik: ./start_gui.sh${NC}"
    echo ""
    echo -e "${YELLOW}   Pakiety zostaną zainstalowane w trybie użytkownika.${NC}"
    echo ""
fi

# Przejdź do folderu skryptu
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8

# ============================================
# KROK 1: Sprawdź czy Python jest zainstalowany
# ============================================
echo "[1/6] Sprawdzanie Pythona..."

if ! command -v python3 &> /dev/null; then
    echo ""
    echo -e "${RED}❌ BŁĄD: Python 3 nie jest zainstalowany!${NC}"
    echo ""
    echo "📥 Aby zainstalować Pythona:"
    echo ""
    echo "   Ubuntu/Debian:"
    echo "      sudo apt update"
    echo "      sudo apt install python3 python3-pip python3-tk"
    echo ""
    echo "   Fedora/RHEL:"
    echo "      sudo dnf install python3 python3-pip python3-tkinter"
    echo ""
    echo "   macOS (z Homebrew):"
    echo "      brew install python-tk@3.13"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $PYTHON_VERSION jest zainstalowany${NC}"

# Sprawdź wersję Pythona
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]; }; then
    echo -e "${YELLOW}⚠️  OSTRZEŻENIE: Zalecany Python 3.9 lub nowszy${NC}"
fi

# ============================================
# KROK 2: Sprawdź czy pip działa
# ============================================
echo "[2/6] Sprawdzanie pip..."

if ! python3 -m pip --version &> /dev/null; then
    echo ""
    echo -e "${RED}❌ BŁĄD: pip nie działa!${NC}"
    echo ""
    echo "📥 Naprawiam pip..."
    python3 -m ensurepip --upgrade || {
        echo -e "${RED}❌ Nie udało się naprawić pip${NC}"
        echo "   Spróbuj zainstalować pip ręcznie:"
        echo "   sudo apt install python3-pip  # Ubuntu/Debian"
        echo "   sudo dnf install python3-pip  # Fedora/RHEL"
        exit 1
    }
fi

echo -e "${GREEN}✅ pip jest gotowy${NC}"

# ============================================
# KROK 3: Sprawdź tkinter (wymagany dla GUI)
# ============================================
echo "[3/6] Sprawdzanie tkinter..."

if ! python3 -c "import tkinter" &> /dev/null; then
    echo ""
    echo -e "${RED}❌ BŁĄD: tkinter nie jest dostępny!${NC}"
    echo ""
    echo "   tkinter jest wymagany dla GUI."
    echo ""
    echo "📥 Aby zainstalować:"
    echo ""
    echo "   Ubuntu/Debian:"
    echo "      sudo apt install python3-tk"
    echo ""
    echo "   Fedora/RHEL:"
    echo "      sudo dnf install python3-tkinter"
    echo ""
    echo "   Arch Linux:"
    echo "      sudo pacman -S tk"
    echo ""
    echo "   macOS (z Homebrew):"
    echo "      brew install python-tk@3.13"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ tkinter jest dostępny${NC}"

# ============================================
# KROK 3.5: Sprawdź czcionki emoji (tylko Linux)
# ============================================
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "[3.5/5] Sprawdzanie czcionek emoji..."

    # Sprawdź czy Noto Color Emoji jest zainstalowana
    if ! fc-list | grep -qi "Noto Color Emoji"; then
        echo ""
        echo -e "${YELLOW}⚠️  Czcionka emoji nie jest zainstalowana${NC}"
        echo "   Bez niej ikony w GUI mogą być niewidoczne."
        echo ""

        # Sprawdź czy mamy sudo dostęp
        if command -v sudo &> /dev/null; then
            echo "📥 Instaluję czcionkę emoji..."

            # Wykryj dystrybucję
            if command -v apt &> /dev/null; then
                # Ubuntu/Debian
                if sudo apt install -y fonts-noto-color-emoji 2>/dev/null; then
                    echo -e "${GREEN}✅ Czcionka emoji zainstalowana${NC}"
                    # Odśwież cache czcionek
                    fc-cache -f -v >/dev/null 2>&1
                else
                    echo -e "${YELLOW}⚠️  Nie udało się zainstalować czcionki automatycznie${NC}"
                    echo "   Uruchom ręcznie: sudo apt install fonts-noto-color-emoji"
                fi
            elif command -v dnf &> /dev/null; then
                # Fedora/RHEL
                if sudo dnf install -y google-noto-emoji-color-fonts 2>/dev/null; then
                    echo -e "${GREEN}✅ Czcionka emoji zainstalowana${NC}"
                    fc-cache -f -v >/dev/null 2>&1
                else
                    echo -e "${YELLOW}⚠️  Nie udało się zainstalować czcionki automatycznie${NC}"
                    echo "   Uruchom ręcznie: sudo dnf install google-noto-emoji-color-fonts"
                fi
            elif command -v pacman &> /dev/null; then
                # Arch Linux
                if sudo pacman -S --noconfirm noto-fonts-emoji 2>/dev/null; then
                    echo -e "${GREEN}✅ Czcionka emoji zainstalowana${NC}"
                    fc-cache -f -v >/dev/null 2>&1
                else
                    echo -e "${YELLOW}⚠️  Nie udało się zainstalować czcionki automatycznie${NC}"
                    echo "   Uruchom ręcznie: sudo pacman -S noto-fonts-emoji"
                fi
            else
                echo -e "${YELLOW}⚠️  Nie rozpoznano menedżera pakietów${NC}"
                echo "   Zainstaluj ręcznie czcionkę emoji dla swojej dystrybucji"
            fi
        else
            echo -e "${YELLOW}⚠️  sudo nie jest dostępne${NC}"
            echo "   Zainstaluj ręcznie czcionkę emoji:"
            echo "   Ubuntu/Debian: sudo apt install fonts-noto-color-emoji"
            echo "   Fedora/RHEL: sudo dnf install google-noto-emoji-color-fonts"
            echo "   Arch: sudo pacman -S noto-fonts-emoji"
        fi
        echo ""
    else
        echo -e "${GREEN}✅ Czcionka emoji jest zainstalowana${NC}"
    fi
fi

# ============================================
# KROK 4: Zainstaluj wymagane biblioteki
# ============================================
echo "[4/6] Sprawdzanie wymaganych bibliotek..."

# Funkcja do sprawdzania i instalacji pakietu
check_and_install() {
    local package_name=$1
    local import_name=$2
    local version_spec=$3

    if python3 -c "import $import_name" &> /dev/null; then
        echo -e "${GREEN}✅ $package_name już zainstalowane${NC}"
    else
        echo ""
        echo "📦 Instaluję $package_name..."
        # Próbuj z --user, jeśli nie działa, użyj --break-system-packages
        if python3 -m pip install "$package_name$version_spec" --user --quiet 2>/dev/null; then
            echo -e "${GREEN}✅ $package_name zainstalowane${NC}"
        elif python3 -m pip install "$package_name$version_spec" --break-system-packages --quiet 2>/dev/null; then
            echo -e "${GREEN}✅ $package_name zainstalowane (system-wide)${NC}"
        else
            echo -e "${RED}❌ Nie udało się zainstalować $package_name${NC}"
            echo -e "${YELLOW}Próbuję alternatywną metodę...${NC}"
            # Ostatnia szansa - bez --quiet żeby zobaczyć błąd
            if python3 -m pip install "$package_name$version_spec" --user; then
                echo -e "${GREEN}✅ $package_name zainstalowane${NC}"
            else
                echo -e "${RED}❌ Instalacja nie powiodła się${NC}"
                exit 1
            fi
        fi
    fi
}

# Sprawdź i zainstaluj każdą bibliotekę
check_and_install "ezdxf" "ezdxf" ">=1.0.0"
check_and_install "Pillow" "PIL" ">=10.0.0"
check_and_install "svgwrite" "svgwrite" ">=1.4.0"
check_and_install "scipy" "scipy" ">=1.10.0"

# ============================================
# KROK 5: Uruchom aplikację
# ============================================
echo "[6/6] Uruchamianie GUI..."
echo ""
echo "========================================"
echo "   Aplikacja startuje..."
echo "========================================"
echo ""

# Sprawdź czy podano argument konfiguracji
if [ -z "$1" ]; then
    python3 run_interactive_gui.py
else
    echo "Ładuję konfigurację: $1"
    python3 run_interactive_gui.py --config "$1"
fi

# Kod wyjścia
exit_code=$?

# Jeśli aplikacja się zakończyła z błędem
if [ $exit_code -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Aplikacja zakończyła się z błędem (kod: $exit_code)${NC}"
    exit $exit_code
fi
