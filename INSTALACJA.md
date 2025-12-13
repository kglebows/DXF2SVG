# 🚀 Instrukcja Instalacji DXF2SVG

> **Szybki wybór:**
>
> - [Instrukcja dla Windows](#instrukcja-instalacji-dla-użytkowników-windows) ⬇️
> - [Instrukcja dla Linux/macOS](#instrukcja-instalacji-dla-linuxmacos) ⬇️

---

## Instrukcja Instalacji dla Użytkowników Windows

### Krok 1: Zainstaluj Git (jeśli nie masz)

1. Wejdź na stronę: https://git-scm.com/download/win
2. Pobierz instalator (64-bit Git for Windows Setup)
3. Uruchom instalator i klikaj "Next" (domyślne ustawienia są OK)
4. Po instalacji zamknij i otwórz ponownie Command Prompt (CMD)

#### Jak sprawdzić czy Git jest zainstalowany?

Otwórz **Command Prompt** (CMD) i wpisz:
```cmd
git --version
```
Jeśli widzisz numer wersji (np. `git version 2.43.0`), Git jest zainstalowany! ✅

---

### Krok 2: Zainstaluj Python (jeśli nie masz)

1. Wejdź na stronę: https://www.python.org/downloads/
2. Pobierz **Python 3.13** lub nowszy
3. Uruchom instalator
4. ⚠️ **WAŻNE**: Zaznacz opcję **"Add Python to PATH"** na pierwszym ekranie!
5. Kliknij "Install Now"
6. Poczekaj na zakończenie instalacji

### Jak sprawdzić czy Python jest zainstalowany?
Otwórz **Command Prompt** (CMD) i wpisz:
```cmd
python --version
```
Jeśli widzisz numer wersji (np. `Python 3.13.0`), Python jest zainstalowany! ✅

---

## Krok 3: Pobierz DXF2SVG

1. Otwórz **Command Prompt** (CMD)
   - Naciśnij `Win + R`
   - Wpisz `cmd` i naciśnij Enter

2. Przejdź do folderu gdzie chcesz pobrać program, np.:
   ```cmd
   cd C:\Users\%USERNAME%\Documents
   ```

3. Sklonuj repozytorium:
   ```cmd
   git clone https://github.com/kglebows/DXF2SVG.git
   ```

4. Wejdź do folderu:
   ```cmd
   cd DXF2SVG
   ```

---

## Krok 4: Uruchom Program

### Metoda 1: Dwuklik (najłatwiejsza)
1. Otwórz folder `DXF2SVG` w Eksploratorze Windows
2. **Kliknij dwukrotnie** na plik `start_gui.bat`
3. Program automatycznie:
   - Sprawdzi czy Python jest zainstalowany
   - Zainstaluje wymagane biblioteki (ezdxf, Pillow)
   - Uruchomi aplikację

### Metoda 2: Z Command Prompt
```cmd
start_gui.bat
```

---

## Co zrobi `start_gui.bat`?

Skrypt automatycznie:
1. ✅ Sprawdzi czy Python jest zainstalowany
2. ✅ Sprawdzi czy pip działa
3. ✅ Zainstaluje brakujące biblioteki (ezdxf, Pillow)
4. ✅ Sprawdzi czy tkinter jest dostępny
5. 🚀 Uruchomi aplikację DXF2SVG

**Nie musisz nic robić ręcznie!** Wszystko dzieje się automatycznie.

---

## 🆘 Rozwiązywanie Problemów

### Problem: "Python nie jest zainstalowany"
**Rozwiązanie:**
1. Zainstaluj Pythona ze strony https://www.python.org/downloads/
2. **Upewnij się że zaznaczyłeś "Add Python to PATH"**
3. Uruchom ponownie `start_gui.bat`

### Problem: "tkinter nie jest dostępny"
**Rozwiązanie:**
1. Odinstaluj Pythona (Panel Sterowania → Programy → Odinstaluj)
2. Zainstaluj ponownie ze strony https://www.python.org/downloads/
3. Podczas instalacji wybierz **"Customize installation"**
4. Upewnij się że opcja **"tcl/tk and IDLE"** jest zaznaczona
5. Dokończ instalację i uruchom ponownie `start_gui.bat`

### Problem: "git clone nie działa"
**Rozwiązanie:**
1. Zainstaluj Git ze strony https://git-scm.com/download/win
2. Zamknij i otwórz ponownie Command Prompt
3. Spróbuj ponownie

### Problem: Aplikacja się nie uruchamia
**Rozwiązanie:**
1. Otwórz Command Prompt w folderze DXF2SVG
2. Uruchom ręcznie:
   ```cmd
   python run_interactive_gui.py
   ```
3. Przeczytaj komunikaty o błędach
4. Jeśli dalej nie działa, skopiuj błędy i zgłoś issue na GitHub

---

## 📁 Struktura Folderów

Po pobraniu, folder `DXF2SVG` będzie wyglądał tak:

```
DXF2SVG/
├── start_gui.bat          ← Kliknij dwukrotnie aby uruchomić
├── run_interactive_gui.py ← Główny skrypt Pythona
├── requirements.txt       ← Lista wymaganych bibliotek
├── README.md             ← Dokumentacja techniczna
├── INSTALACJA.md         ← Ten plik
├── configs/              ← Pliki konfiguracyjne (.cfg)
├── src/                  ← Kod źródłowy
└── ...
```

---

## ✅ Gotowe!

Jeśli wszystko poszło dobrze, powinieneś zobaczyć okno aplikacji DXF2SVG z trzema zakładkami:
- **⚙️ Konfiguracja** - Ustawienia konwersji
- **🔧 Tryb Interaktywny** - Edycja przypisań
- **📊 Status i Logi** - Logi aplikacji

---

## 🔄 Aktualizacja Programu

Aby zaktualizować DXF2SVG do najnowszej wersji:

1. Otwórz Command Prompt w folderze DXF2SVG
2. Wpisz:
   ```cmd
   git pull
   ```
3. Uruchom ponownie `start_gui.bat`

---

## 💡 Wskazówki

- **Pierwszym uruchomieniem może trwać dłużej** - program instaluje biblioteki
- **Kolejne uruchomienia będą natychmiastowe** - biblioteki są już zainstalowane
- **Możesz utworzyć skrót** do `start_gui.bat` na pulpicie dla łatwiejszego dostępu
- **Aplikacja działa offline** - po pierwszym uruchomieniu nie potrzebujesz internetu

---

## 📞 Pomoc

Jeśli masz problemy:
1. Sprawdź sekcję "Rozwiązywanie Problemów" powyżej
2. Przeczytaj pełną dokumentację w pliku `README.md`
3. Zgłoś issue na GitHub: https://github.com/kglebows/DXF2SVG/issues

---

**Powodzenia!** 🎉

---
---

# Linux / macOS

## Instrukcja Instalacji dla Linux/macOS

### Krok 1: Zainstaluj Git (jeśli nie masz)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install git
```

**Fedora/RHEL:**
```bash
sudo dnf install git
```

**macOS (z Homebrew):**
```bash
brew install git
```

#### Jak sprawdzić czy Git jest zainstalowany?

Otwórz **Terminal** i wpisz:
```bash
git --version
```
Jeśli widzisz numer wersji (np. `git version 2.43.0`), Git jest zainstalowany! ✅

---

### Krok 2: Zainstaluj Python 3 i tkinter (jeśli nie masz)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip tk
```

**macOS (z Homebrew):**
```bash
brew install python-tk@3.13
```

#### Jak sprawdzić czy Python jest zainstalowany?

Otwórz **Terminal** i wpisz:
```bash
python3 --version
```
Jeśli widzisz numer wersji (np. `Python 3.11.0`), Python jest zainstalowany! ✅

---

### Krok 3: Pobierz DXF2SVG

1. Otwórz **Terminal**

2. Przejdź do folderu gdzie chcesz pobrać program, np.:
   ```bash
   cd ~/Documents
   ```

3. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/kglebows/DXF2SVG.git
   ```

4. Wejdź do folderu:
   ```bash
   cd DXF2SVG
   ```

---

### Krok 4: Uruchom Program

#### Metoda 1: Skrypt startowy (zalecana)

1. Ustaw uprawnienia wykonywania (tylko raz):
   ```bash
   chmod +x start_gui.sh
   ```

2. Uruchom skrypt:
   ```bash
   ./start_gui.sh
   ```

Program automatycznie:
- Sprawdzi czy Python i tkinter są zainstalowane
- Zainstaluje wymagane biblioteki (ezdxf, Pillow, svgwrite, scipy)
- Uruchomi aplikację

#### Metoda 2: Bezpośrednio przez Python

```bash
python3 run_interactive_gui.py
```

---

## Co zrobi `start_gui.sh`?

Skrypt automatycznie:
1. ✅ Sprawdzi czy Python 3 jest zainstalowany
2. ✅ Sprawdzi czy pip działa
3. ✅ Sprawdzi czy tkinter jest dostępny
4. ✅ Zainstaluje brakujące biblioteki (ezdxf, Pillow, svgwrite, scipy)
5. 🚀 Uruchomi aplikację DXF2SVG

**Nie musisz nic robić ręcznie!** Wszystko dzieje się automatycznie.

---

## 🆘 Rozwiązywanie Problemów (Linux/macOS)

### Problem: "Python 3 nie jest zainstalowany"

**Rozwiązanie:**
Zainstaluj Pythona używając menedżera pakietów twojej dystrybucji (patrz Krok 2 powyżej).

### Problem: "tkinter nie jest dostępny"

**Rozwiązanie:**

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S tk
```

**macOS:**
```bash
brew install python-tk@3.13
```

### Problem: "Permission denied" przy uruchamianiu start_gui.sh

**Rozwiązanie:**
```bash
chmod +x start_gui.sh
./start_gui.sh
```

### Problem: Brak uprawnień pip (user site-packages)

Jeśli pip mówi o braku uprawnień, biblioteki zostaną zainstalowane w trybie użytkownika (`--user`), co jest bezpieczne i nie wymaga sudo.

### Problem: "Naruszenie ochrony pamięci (zrzut pamięci)"

Ten problem powinien być już naprawiony. Jeśli nadal występuje:
1. Upewnij się że masz najnowszą wersję kodu:
   ```bash
   git pull
   ```
2. Sprawdź czy tkinter działa:
   ```bash
   python3 -c "import tkinter; tkinter.Tk()"
   ```
3. Jeśli nadal nie działa, zgłoś issue na GitHub z pełnym komunikatem błędu.

---

## 📁 Struktura Folderów

Po pobraniu, folder `DXF2SVG` będzie wyglądał tak:

```
DXF2SVG/
├── start_gui.sh           ← Uruchom to (Linux/macOS)
├── start_gui.bat          ← Uruchom to (Windows)
├── run_interactive_gui.py ← Główny skrypt Pythona
├── requirements.txt       ← Lista wymaganych bibliotek
├── README.md             ← Dokumentacja techniczna
├── INSTALACJA.md         ← Ten plik
├── configs/              ← Pliki konfiguracyjne (.cfg)
├── src/                  ← Kod źródłowy
└── ...
```

---

## ✅ Gotowe!

Jeśli wszystko poszło dobrze, powinieneś zobaczyć okno aplikacji DXF2SVG z trzema zakładkami:
- **⚙️ Konfiguracja** - Ustawienia konwersji
- **🔧 Tryb Interaktywny** - Edycja przypisań
- **📊 Status i Logi** - Logi aplikacji

---

## 🔄 Aktualizacja Programu

Aby zaktualizować DXF2SVG do najnowszej wersji:

```bash
cd DXF2SVG
git pull
./start_gui.sh  # lub python3 run_interactive_gui.py
```

---

## 💡 Wskazówki (Linux/macOS)

- **Pierwszym uruchomieniem może trwać dłużej** - program instaluje biblioteki
- **Kolejne uruchomienia będą natychmiastowe** - biblioteki są już zainstalowane
- **Aplikacja działa offline** - po pierwszym uruchomieniu nie potrzebujesz internetu
- **Możesz utworzyć alias** w `.bashrc` lub `.zshrc`:
  ```bash
  alias dxf2svg='cd ~/Documents/DXF2SVG && ./start_gui.sh'
  ```

---

## 📞 Pomoc

Jeśli masz problemy:
1. Sprawdź sekcję "Rozwiązywanie Problemów" powyżej
2. Przeczytaj pełną dokumentację w pliku [README.md](README.md)
3. Zgłoś issue na GitHub: https://github.com/kglebows/DXF2SVG/issues

---

**Powodzenia!** 🎉
