# 🚀 Instrukcja Instalacji dla Użytkowników Windows

## Krok 1: Zainstaluj Git (jeśli nie masz)

1. Wejdź na stronę: https://git-scm.com/download/win
2. Pobierz instalator (64-bit Git for Windows Setup)
3. Uruchom instalator i klikaj "Next" (domyślne ustawienia są OK)
4. Po instalacji zamknij i otwórz ponownie Command Prompt (CMD)

### Jak sprawdzić czy Git jest zainstalowany?
Otwórz **Command Prompt** (CMD) i wpisz:
```cmd
git --version
```
Jeśli widzisz numer wersji (np. `git version 2.43.0`), Git jest zainstalowany! ✅

---

## Krok 2: Zainstaluj Python (jeśli nie masz)

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
