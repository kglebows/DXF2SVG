# DXF2SVG - Interaktywny GUI

## Opis

Interaktywny graficzny interfejs użytkownika (GUI) dla systemu konwersji DXF do SVG. Aplikacja oferuje intuicyjny sposób pracy z plikami DXF i podgląd generowanych plików SVG w czasie rzeczywistym.

## Funkcje

### Panel Sterowania (Lewa strona)
- **Zarządzanie plikami**: Wybór pliku DXF wejściowego i określenie ścieżki wyjściowej SVG
- **Konwersja**: Przycisk konwersji DXF → SVG z paskiem postępu
- **Opcje**: Auto-odświeżanie podglądu, grupowanie strukturalne
- **Kontrola podglądu**: Przyciski odświeżania, reset i dopasowania widoku
- **Status i logi**: Bieżący status operacji i historia działań

### Panel Podglądu (Prawa strona)
- **Podgląd SVG**: Wyświetlanie wygenerowanego pliku SVG
- **Zoom**: Przybliżanie i oddalanie za pomocą kółka myszy
- **Panoramowanie**: Przesuwanie obrazu poprzez przeciąganie
- **Auto-odświeżanie**: Automatyczna aktualizacja po konwersji

## Uruchomienie

### Metoda 1: Bezpośrednio
```bash
python interactive_gui.py
```

### Metoda 2: Przez launcher
```bash
python run_interactive_gui.py
```

## Wymagania

### Biblioteki Python
- `tkinter` (wbudowany w Python)
- `pillow` - obsługa obrazów
- `ezdxf` - parsowanie plików DXF
- `svgwrite` - generowanie SVG
- `scipy` - obliczenia matematyczne

### Instalacja wymaganych pakietów
```bash
pip install pillow ezdxf svgwrite scipy
```

## Struktura Interfejsu

```
┌─────────────────────────────────────────────────────────────┐
│                DXF2SVG - Interaktywny Edytor               │
├──────────────────────┬──────────────────────────────────────┤
│   Panel Sterowania   │         Panel Podglądu SVG          │
│                      │                                      │
│ ┌─ Pliki ──────────┐ │ ┌─ Podgląd SVG ─────────────────────┐ │
│ │ • Plik DXF       │ │ │                                   │ │
│ │ • Plik SVG       │ │ │        [Wyświetlanie SVG]        │ │
│ └──────────────────┘ │ │                                   │ │
│                      │ │      • Zoom kółkiem myszy         │ │
│ ┌─ Konwersja ──────┐ │ │      • Przeciąganie do            │ │
│ │ • Konwertuj      │ │ │        przesuwania                │ │
│ │ • Auto-odśw.     │ │ │                                   │ │
│ │ • Grupowanie     │ │ │                                   │ │
│ └──────────────────┘ │ └───────────────────────────────────┘ │
│                      │                                      │
│ ┌─ Kontrola ───────┐ │                                      │
│ │ • Odśwież        │ │                                      │
│ │ • Reset          │ │                                      │
│ │ • Dopasuj        │ │                                      │
│ └──────────────────┘ │                                      │
│                      │                                      │
│ ┌─ Status ─────────┐ │                                      │
│ │ • Status         │ │                                      │
│ │ • Progress       │ │                                      │
│ │ • Logi           │ │                                      │
│ └──────────────────┘ │                                      │
└──────────────────────┴──────────────────────────────────────┘
```

## Obsługa

### Podstawowy workflow
1. **Wybór pliku DXF**: Kliknij "Wybierz" przy polu "Plik DXF"
2. **Ustawienie wyjścia**: Opcjonalnie zmień nazwę pliku SVG
3. **Konwersja**: Kliknij "Konwertuj DXF → SVG"
4. **Podgląd**: Automatycznie zostanie wyświetlony wygenerowany SVG

### Kontrola podglądu
- **Zoom in/out**: Kółko myszy nad obszarem podglądu
- **Przesuwanie**: Przeciągnij obraz lewym przyciskiem myszy
- **Reset widoku**: Przycisk "Reset" przywraca domyślny widok
- **Dopasuj do okna**: Przycisk "Dopasuj" automatycznie skaluje SVG

### Opcje zaawansowane
- **Auto-odświeżanie**: Automatyczna aktualizacja podglądu po konwersji
- **Grupowanie strukturalne**: Tworzenie grup SVG według struktury inverterów

## Pliki wyjściowe

Aplikacja generuje następujące pliki:
- `output_initial.svg` - podstawowy podgląd SVG
- `output_structured.svg` - SVG z grupowaniem strukturalnym
- `debug.log` - szczegółowe logi procesu konwersji

## Rozwiązywanie problemów

### GUI nie uruchamia się
- Sprawdź czy zainstalowano wszystkie wymagane biblioteki
- Upewnij się, że używasz Python 3.7+

### Błąd renderowania SVG
- GUI używa uproszczonego renderera SVG
- Kompleksowe pliki SVG mogą być wyświetlane jako informacja tekstowa

### Konwersja nie działa
- Sprawdź czy plik DXF jest prawidłowy
- Sprawdź logi w dolnej części panelu sterowania

## Architektura

### Komponenty główne
- `InteractiveGUI` - główna klasa aplikacji
- `SVGViewer` - komponent podglądu SVG
- `dxf2svg.main()` - silnik konwersji (uruchamiany w osobnym wątku)

### Przepływ danych
1. Wybór pliku DXF przez użytkownika
2. Uruchomienie konwersji w tle
3. Generowanie plików SVG
4. Automatyczne odświeżenie podglądu
5. Aktualizacja informacji o pliku

## Integracja z istniejącym systemem

GUI korzysta z istniejących modułów:
- `dxf2svg.py` - główny silnik konwersji
- `config.py` - konfiguracja i parsowanie tekstów
- `svg_generator.py` - generowanie plików SVG
- `console_logger.py` - system logowania

Nie modyfikuje istniejącego kodu - jest całkowicie addytywny.

## Przyszłe rozszerzenia

Planowane funkcje:
- Edycja parametrów konwersji przez GUI
- Podgląd z wyróżnieniem grup inverterów
- Eksport do różnych formatów
- Batch processing wielu plików
- Integracja z interaktywnym editorem przypisań
