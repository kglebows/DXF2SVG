# Szybki Start - System Konfiguracji

## Uruchamianie z konfiguracją

### Metoda 1: Przez GUI
1. Uruchom aplikację: `python run_interactive_gui.py`
2. Przejdź do zakładki "⚙️ Konfiguracja"
3. Wybierz konfigurację z listy i kliknij "Wczytaj"

### Metoda 2: Z wiersza poleceń
```bash
# Uruchom z konfiguracją ZIEB
python run_interactive_gui.py --config zieb

# Uruchom z konfiguracją WIE4  
python run_interactive_gui.py --config wie4

# Domyślne ustawienia
python run_interactive_gui.py
```

### Metoda 3: Przez plik .bat
```bat
# Domyślne ustawienia
start_gui.bat

# Z konfiguracją
start_gui.bat zieb
start_gui.bat wie4
```

## Dostępne konfiguracje

- **zieb.cfg** - Obiekt ZIEB, format_1, teksty powyżej
- **wie4.cfg** - Obiekt WIE4, format_2, teksty poniżej

## Tworzenie nowej konfiguracji

1. W zakładce Konfiguracja kliknij "Nowy"
2. Ustaw parametry (Station ID, format tekstów, pliki itp.)
3. Wprowadź nazwę konfiguracji
4. Kliknij "Zapisz"

## Najważniejsze parametry

- **Station ID**: Identyfikator stacji (ZIEB, WIE4, itp.)
- **Format tekstów**: Sposób interpretacji tekstów DXF
- **Domyślny DXF**: Plik automatycznie ładowany przy starcie
- **Strukturalny SVG**: Nazwa pliku wyjściowego

Szczegółowa dokumentacja: `README_Configuration.md`
