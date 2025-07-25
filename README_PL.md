# DXF2SVG - Interaktywny Konwerter DXF do SVG

Zaawansowana aplikacja Python do konwersji plików DXF na format SVG z możliwością interaktywnego przypisywania elementów i konfigurowalnymi parametrami.

## Funkcjonalności

- **Konwersja DXF do SVG**: Konwertuj pliki DXF na skalowalny format SVG
- **Interaktywny GUI**: Przyjazny interfejs użytkownika do zarządzania konwersjami i przypisaniami
- **Wiele formatów SVG**:
  - Podstawowy SVG (proste linie)
  - Interaktywny SVG (z klikalny elementami)
  - Strukturalny SVG (z prostokątami i grupowaniem)
- **Automatyczne przypisywanie**: Inteligentne przypisywanie tekst-do-string na podstawie bliskości
- **Ręczne przypisywanie**: Interaktywny edytor do precyzyjnego dostrajania przypisań
- **Konfigurowalne parametry**: Dostosowywalne ustawienia przez pliki konfiguracyjne
- **Podgląd w czasie rzeczywistym**: Wbudowany podgląd SVG dla natychmiastowych rezultatów

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/DXF2SVG.git
cd DXF2SVG
```

2. Zainstaluj wymagane zależności:
```bash
pip install -r requirements.txt
```

## Użytkowanie

### Tryb GUI (Zalecany)
```bash
python start_gui.py
```
lub
```bash
python run_interactive_gui.py
```

### Tryb linii poleceń
```bash
python -m src.core.dxf2svg input.dxf
```

## Struktura projektu

```
DXF2SVG/
├── src/                     # Kod źródłowy
│   ├── core/                # Podstawowa funkcjonalność
│   │   ├── config.py        # Konfiguracja i parsowanie tekstu
│   │   ├── dxf2svg.py       # Główna logika konwersji
│   │   └── geometry_utils.py # Obliczenia geometryczne
│   ├── gui/                 # Interfejs użytkownika
│   │   ├── interactive_gui_new.py # Główna aplikacja GUI
│   │   └── simple_svg_viewer.py   # Komponent podglądu SVG
│   ├── svg/                 # Generowanie SVG
│   │   └── svg_generator.py # Formatowanie wyjścia SVG
│   ├── interactive/         # Interaktywne edytowanie
│   │   ├── interactive_editor.py # Narzędzia ręcznego przypisywania
│   │   └── assignment_manager.py # Zarządzanie przypisaniami
│   ├── config/              # Zarządzanie konfiguracją
│   │   └── config_manager.py # Obsługa plików konfiguracyjnych
│   └── utils/               # Narzędzia pomocnicze
│       └── console_logger.py # Logowanie i wyjście konsoli
├── tests/                   # Pliki testowe
├── docs/                    # Dokumentacja
├── examples/                # Przykładowe pliki
├── logs/                    # Pliki logów
└── temp/                    # Pliki tymczasowe
```

## Konfiguracja

Aplikacja używa plików konfiguracyjnych (`.cfg`) do dostosowania zachowania:

- **MPTT_HEIGHT**: Grubość linii w generowanym SVG
- **STATION_ID**: Identyfikator stacji do filtrowania tekstu
- **TEXT_FORMATS**: Obsługiwane wzorce formatów tekstu
- **Kolory i stylizacja**: Dostosowywany wygląd

Konfigurację można modyfikować przez zakładkę Config w GUI lub bezpośrednio edytując pliki `.cfg`.

## Obsługiwane formaty plików

- **Wejście**: DXF (Drawing Exchange Format)
- **Wyjście**: SVG (Scalable Vector Graphics)
- **Konfiguracja**: CFG (pliki konfiguracyjne)

## Kluczowe komponenty

### Silnik główny (`src/core/`)
- **dxf2svg.py**: Główna logika konwersji i orkiestracja przepływu pracy
- **config.py**: Zarządzanie konfiguracją i narzędzia parsowania tekstu
- **geometry_utils.py**: Obliczenia geometryczne i analiza przestrzenna

### Interfejs użytkownika (`src/gui/`)
- **interactive_gui_new.py**: Główna aplikacja GUI z interfejsem zakładkowym
- **simple_svg_viewer.py**: Wbudowany komponent podglądu SVG

### Generowanie SVG (`src/svg/`)
- **svg_generator.py**: Generowanie wielu formatów SVG z konfigurowalnymi stylami

### Narzędzia interaktywne (`src/interactive/`)
- **interactive_editor.py**: Narzędzia ręcznego przypisywania i edycji
- **assignment_manager.py**: Zarządzanie stanem przypisań

## Współpraca

1. Zrób fork repozytorium
2. Utwórz branch funkcjonalności (`git checkout -b feature/amazing-feature`)
3. Zatwierdź swoje zmiany (`git commit -m 'Dodaj niesamowitą funkcjonalność'`)
4. Wypchnij do brancha (`git push origin feature/amazing-feature`)
5. Otwórz Pull Request

## Licencja

Ten projekt jest licencjonowany na licencji MIT - zobacz plik [LICENSE](LICENSE) dla szczegółów.

## Wymagania

- Python 3.7+
- tkinter (zwykle dołączony do Pythona)
- ezdxf (do przetwarzania plików DXF)
- Inne zależności wymienione w `requirements.txt`

## Rozwiązywanie problemów

### Częste problemy

1. **Błędy importu**: Upewnij się, że wszystkie zależności są zainstalowane przez `pip install -r requirements.txt`
2. **Problemy z ładowaniem DXF**: Sprawdź czy plik DXF jest prawidłowy i nie uszkodzony
3. **GUI się nie uruchamia**: Sprawdź wersję Pythona (wymagany 3.7+) i dostępność tkinter

### Tryb debugowania

Włącz logowanie debug ustawiając poziom logowania w konfiguracji lub uruchamiając z szczegółowym wyjściem.

## Rozwój

### Uruchamianie testów
```bash
python -m pytest tests/
```

### Styl kodu
Projekt przestrzega wytycznych PEP 8. Używaj narzędzi takich jak `flake8` lub `black` do formatowania kodu.

## Historia zmian

Zobacz [CHANGELOG.md](CHANGELOG.md) dla historii wersji i aktualizacji.

## Zrzuty ekranu

*Zrzuty ekranu będą dodane wkrótce...*

## Uwagi dla deweloperów

### Kluczowe funkcjonalności
- **Konfigurowalny MPTT_HEIGHT**: Parametr wpływa na grubość linii w SVG
- **Inteligentne przypisywanie**: Automatyczne łączenie tekstów z segmentami na podstawie odległości
- **Format strukturalny**: Generowanie prostokątów zamiast linii dla lepszej wizualizacji
- **Manager przypisań**: Obsługa cofania/ponowienia z historią zmian

### Architektura
Aplikacja została zaprojektowana z modularną architekturą umożliwiającą łatwe rozszerzanie i utrzymanie.
