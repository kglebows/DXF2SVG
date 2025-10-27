# DXF2SVG - Interaktywny Konwerter DXF do SVG

![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

---

## 🚀 **Dla Użytkowników Windows - Szybki Start**

> **❓ Nie wiesz co to VSC, Python czy Git? Nie ogarniasz programowania?**  
> **👉 [KLIKNIJ TUTAJ - Prosta Instrukcja Instalacji](INSTALACJA.md) 👈**
>
> Szczegółowa instrukcja krok po kroku jak zainstalować i uruchomić program w kilka minut!  
> Po prostu sklonuj repozytorium, kliknij dwukrotnie `start_gui.bat` i gotowe! 🎉

---

Profesjonalna aplikacja w Pythonie do konwersji plików DXF (AutoCAD) na format SVG z inteligentnym przypisywaniem tekstów do geometrii oraz nowoczesnym interfejsem graficznym.

##  Możliwości

###  **Wiele Formatów Wyjściowych SVG**
- **Podstawowy SVG**: Prosta konwersja tylko z kształtami geometrycznymi
- **Interaktywny SVG**: Interfejs do ręcznej korekty przypisań tekstów (kliknij aby wybrać, prawy przycisk aby przypisać)
- **Strukturalny SVG**: Hierarchicznie zorganizowany wynik pogrupowany według falowników z tooltipami po najechaniu myszką

###  **Nowoczesny Interfejs Graficzny**
- **Zakładka Konfiguracji**: Dynamiczny układ z automatycznym dopasowaniem szerokości panelu
- **Edytor Przypisań**: Wizualna edycja z wyborem lewym przyciskiem i przypisaniem prawym
- **Podgląd na Żywo**: Wbudowana przeglądarka SVG z funkcjami zoom i przesuwania
- **Responsywne Okno Logów**: Wielowątkowe logowanie z automatycznym przewijaniem

###  **Inteligentne Przetwarzanie**
- **Automatyczne Przypisywanie**: Algorytm oparty na odległości automatycznie przypisuje etykiety tekstowe do segmentów geometrycznych
- **Wykrywanie Duplikatów**: Automatycznie identyfikuje i usuwa zduplikowane segmenty
- **Filtrowanie Outlierów**: Usuwa elementy poza znaczącymi granicami dla czystszego wyniku
- **Adaptacyjny ViewBox**: Dynamicznie obliczany viewBox, który obsługuje elementy z ujemnymi współrzędnymi

###  **Zaawansowane Funkcje**
- **Własne Parsowanie Tekstów**: Konfigurowalne wzorce regex do wyodrębniania ID stacji i numerów falowników
- **Przetwarzanie Wsadowe**: Konwertuj wiele plików DXF za pomocą jednej konfiguracji
- **Interaktywne Tooltips**: Najedź na elementy w Strukturalnym SVG aby zobaczyć metadane (ID segmentów, ID strukturalne)
- **Presety Konfiguracji**: Zapisuj i wczytuj pliki `.cfg` dla różnych formatów DXF

##  Szybki Start

### Wymagania

- Python 3.13 lub wyższy
- pip (menedżer pakietów)

### Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/kglebows/DXF2SVG.git
cd DXF2SVG
```

2. Zainstaluj wymagane zależności:
```bash
pip install -r requirements.txt
```

### Uruchomienie

#### Tryb GUI (Zalecany)

Uruchom interfejs graficzny:
```bash
python run_interactive_gui.py
```

Lub użyj skryptu wsadowego na Windows:
```bash
start_gui.bat
```

#### Tryb Linii Poleceń

```python
from src.core.dxf2svg import DXF2SVG

# Wczytaj plik DXF
dxf = DXF2SVG('input.dxf', 'config.cfg')

# Przetwarzaj i generuj SVG
dxf.extract_texts()
dxf.extract_polylines()
dxf.assign_texts_to_strings()
dxf.generate_svg('output.svg')
```

##  Instrukcja Użytkowania

### Krok 1: Uruchom Aplikację
Uruchom `run_interactive_gui.py` aby otworzyć GUI. Główne okno zawiera trzy zakładki:
- **Konfiguracja**: Ustawienia warstw, ID stacji i formatów wyjściowych
- **Edytor Przypisań**: Ręczna korekta przypisań tekstów
- **Przeglądarka SVG**: Podgląd wygenerowanych plików SVG

### Krok 2: Konfiguracja Ustawień DXF
W zakładce **Konfiguracja**:
1. Kliknij **Wybierz Plik DXF** aby wczytać plik AutoCAD
2. Skonfiguruj nazwy warstw:
   - **Warstwa Polilinii**: Warstwa zawierająca segmenty geometryczne (np. `@IDE_STRING_1`)
   - **Warstwa Tekstów**: Warstwa zawierająca etykiety tekstowe (np. `@IDE_STRING_1_TXT`)
3. Ustaw **ID Stacji** (np. `LES1`, `LES2`)

### Krok 3: Konfiguracja Parsowania Tekstów
Zdefiniuj wzorce regex do wyodrębniania metadanych z etykiet tekstowych:
- **Wzorzec ID Stacji**: np. `([A-Z]+\d+)` aby wyodrębnić `LES1` z `LES1-INV01`
- **Wzorzec Falownika**: np. `INV(\d+)` aby wyodrębnić `01` z `LES1-INV01`

### Krok 4: Ustaw Format Wyjściowy
Wybierz tryb generowania SVG:
- **Interaktywny**: Generuje `interactive_assignment.svg` z kontrolkami przypisań
- **Strukturalny**: Tworzy hierarchicznie zorganizowany SVG pogrupowany według falowników z tooltipami

### Krok 5: Przetwórz DXF
Kliknij przycisk **Wczytaj i Przetwórz DXF**:
1. Aplikacja wyodrębni teksty i polilinie
2. Uruchomi się automatyczne przypisywanie (algorytm oparty na odległości)
3. Zostanie wygenerowany interaktywny SVG
4. Pasek postępu pokaże status konwersji

### Krok 6: Popraw Przypisania (Opcjonalnie)
Przejdź do zakładki **Edytor Przypisań**:
1. Zobacz interaktywny SVG z kolorowanymi elementami:
   - **Zielony**: Przypisane segmenty
   - **Czerwony**: Nieprzypisane teksty
   - **Szary**: Nieprzypisane segmenty
2. **Lewy przycisk myszy** - zaznacz tekst lub segment
3. **Prawy przycisk myszy** na docelowym elemencie - przypisz
4. Użyj przycisku **Wyczyść Przypisanie** aby usunąć nieprawidłowe przypisania

### Krok 7: Generuj Finalny SVG
W zakładce **Konfiguracja**, kliknij **Generuj Strukturalny SVG**:
- Wyjściowy SVG będzie zawierał:
  - Hierarchiczne grupowanie według falowników
  - Tooltips po najechaniu pokazujące metadane
  - Czysty viewBox obejmujący wszystkie elementy
  - Geometrię bez duplikatów

##  Format Pliku Konfiguracyjnego

Pliki konfiguracyjne używają formatu `.cfg` ze stylu INI:

```ini
[Layers]
polyline_layer = @IDE_STRING_1
text_layer = @IDE_STRING_1_TXT

[Station]
station_id = LES1

[Format]
delimiter = -
remove_prefix = True

[Search]
search_string_regex = ([A-Z]+\d+)
search_inverter_regex = INV(\d+)
search_segment_regex = (\d+)

[Visual]
segment_height = 20
text_size = 3
spacing = 2

[Files]
output_dir = ./output
save_interactive = True
save_structured = True
```

### Sekcje Konfiguracji

- **[Layers]**: Nazwy warstw DXF dla polilinii i tekstów
- **[Station]**: Identyfikator stacji do filtrowania tekstów
- **[Format]**: Reguły parsowania tekstów (delimiter, obsługa prefiksów)
- **[Search]**: Wzorce regex do wyodrębniania ID
- **[Visual]**: Parametry stylizacji SVG
- **[Files]**: Katalog wyjściowy i flagi generowania

##  Typy Wyjściowych SVG

### Interaktywny SVG
- **Cel**: Interfejs do ręcznej korekty przypisań
- **Funkcje**:
  - Kliknij aby wybrać elementy
  - Prawy przycisk aby przypisać tekst do segmentu
  - Kolorowe statusy (zielony=przypisany, czerwony=nieprzypisany tekst, szary=nieprzypisany segment)
  - Wbudowany JavaScript dla interaktywności
- **Zastosowanie**: Korygowanie błędów automatycznego przypisywania

### Strukturalny SVG
- **Cel**: Finalny produkcyjny wynik
- **Funkcje**:
  - Hierarchiczne grupy `<g>` według ID falownika
  - Niestandardowe atrybuty danych: `data-structural-id`, `data-string-id`, `data-segment-id`
  - Tooltips po najechaniu pokazujące metadane elementu
  - Adaptacyjny viewBox dla pełnej widoczności
  - Czysta, zwalidowana struktura SVG
- **Zastosowanie**: Dokumentacja, integracja webowa, archiwizacja

##  Rozwiązywanie Problemów

### Plik DXF Się Nie Wczytuje
- **Błąd**: "Cannot open DXF file"
- **Rozwiązanie**: Sprawdź ścieżkę do pliku i upewnij się, że DXF nie jest uszkodzony. Sprawdź kompatybilność wersji DXF (obsługiwane R12-R2018).

### Brak Automatycznych Przypisań
- **Błąd**: "0 texts assigned automatically"
- **Rozwiązanie**: 
  - Sprawdź czy ID stacji pasuje do zawartości tekstów
  - Zweryfikuj wzorce regex w zakładce Konfiguracja
  - Upewnij się, że warstwy polilinii i tekstów są prawidłowe

### Tekst Niewidoczny w SVG
- **Błąd**: Brakujące etykiety tekstowe w wyniku
- **Rozwiązanie**: 
  - Zwiększ parametr `text_size` w konfiguracji
  - Sprawdź czy nazwa warstwy tekstowej jest prawidłowa
  - Zweryfikuj czy teksty są na właściwej warstwie w DXF

### Tooltips Nie Działają (Strukturalny SVG)
- **Błąd**: Brak tooltip po najechaniu
- **Rozwiązanie**: 
  - Otwórz SVG w nowoczesnej przeglądarce (Chrome, Firefox, Edge)
  - Upewnij się że JavaScript jest włączony
  - Kursor musi być bezpośrednio nad elementami `rect`

### ViewBox Przycina Elementy
- **Błąd**: Segmenty lub teksty przycięte na krawędziach
- **Rozwiązanie**: Aplikacja automatycznie oblicza adaptacyjny viewBox. Jeśli problem się utrzymuje:
  - Sprawdź czy nie ma ekstremalnie dużych wartości współrzędnych w DXF
  - Zweryfikuj czy filtrowanie outlierów nie jest zbyt agresywne (`outlier_threshold` w konfiguracji)

### Aplikacja Zawiesza się na Dużym DXF
- **Błąd**: Błąd pamięci lub zawieszenie
- **Rozwiązanie**:
  - Zmniejsz rozmiar pliku DXF usuwając niepotrzebne warstwy
  - Zwiększ rozmiar sterty Pythona: `python -X opt -W ignore run_interactive_gui.py`
  - Sprawdź dostępność pamięci RAM w systemie

##  Zaawansowane Użycie

### Własne Parsowanie Tekstów

Nadpisz domyślne wzorce regex dla specjalistycznych formatów DXF:

```python
from src.config.config_manager import ConfigManager

config = ConfigManager('custom.cfg')
config.set('Search', 'search_string_regex', r'CUSTOM-(\d{4})')
config.set('Search', 'search_inverter_regex', r'INV#(\d+)')
config.save()
```

### Przetwarzanie Wsadowe

Przetwarzaj wiele plików DXF z jedną konfiguracją:

```python
import os
from src.core.dxf2svg import DXF2SVG

config_file = 'batch_config.cfg'
input_dir = './input_dxf/'
output_dir = './output_svg/'

for filename in os.listdir(input_dir):
    if filename.endswith('.dxf'):
        dxf_path = os.path.join(input_dir, filename)
        svg_path = os.path.join(output_dir, filename.replace('.dxf', '.svg'))
        
        dxf = DXF2SVG(dxf_path, config_file)
        dxf.process_all()  # Wyodrębnij, przypisz, generuj
        dxf.save_structured_svg(svg_path)
```

### API Programistyczne

Użyj DXF2SVG jako biblioteki w swoich projektach Python:

```python
from src.core.dxf2svg import DXF2SVG

# Inicjalizuj z plikiem DXF i konfiguracją
converter = DXF2SVG('plant_layout.dxf', 'config.cfg')

# Przetwarzanie krok po kroku
texts = converter.extract_texts()
polylines = converter.extract_polylines()
assignments = converter.assign_texts_to_strings()

# Dostęp do surowych danych
for inverter_id, strings in converter.inverter_data.items():
    for string_id, segments in strings.items():
        print(f"Falownik {inverter_id}, String {string_id}: {len(segments)} segmentów")

# Generuj niestandardowe wyjście
converter.generate_interactive_svg('custom_interactive.svg')
converter.generate_structured_svg('custom_structured.svg')
```

##  Struktura Projektu

```
DXF2SVG/
 src/
    core/                # Logika konwersji
       dxf2svg.py       # Główny procesor DXF
       config.py        # Dataclass konfiguracji
       geometry_utils.py # Obliczenia geometryczne
    svg/                 # Generowanie SVG
       svg_generator.py # Generator SVG z adaptacyjnym viewBox
    gui/                 # Interfejs użytkownika
       interactive_gui_new.py # Główne okno aplikacji
       unified_config_tab.py  # Panel konfiguracji
       enhanced_svg_viewer.py # Interaktywna przeglądarka SVG
       simple_svg_viewer.py   # Podstawowy renderer SVG
    interactive/         # Edycja przypisań
       interactive_editor.py  # Zakładka edytora przypisań
       assignment_manager.py  # Logika przypisań
    config/              # Zarządzanie konfiguracją
       config_manager.py # I/O plików konfiguracyjnych
    utils/               # Narzędzia
        console_logger.py # Logowanie wielowątkowe
 configs/                 # Przykładowe pliki konfiguracyjne
    Grabowo3.cfg
    ziec.cfg
 run_interactive_gui.py   # Główny punkt wejścia
 start_gui.bat            # Launcher dla Windows
 requirements.txt         # Zależności Pythona
 LICENSE                  # Licencja MIT
 README.md                # Ten plik
```

##  Wymagania

### Minimalne Wymagania
- Python 3.13+
- 4 GB RAM
- Windows 10/11, macOS 10.14+, lub Linux (Ubuntu 20.04+)

### Zalecane
- Python 3.13.1
- 8 GB RAM
- Rozdzielczość ekranu 1920x1080 dla optymalnego doświadczenia GUI

### Zależności
- `ezdxf>=1.3.0` - Parsowanie plików DXF
- `svgwrite>=1.4.3` - Generowanie plików SVG
- `tkinter` - Framework GUI (dołączony do Pythona)

Zainstaluj wszystkie zależności:
```bash
pip install -r requirements.txt
```

##  Współpraca

Wkład mile widziany! Proszę postępować według tych wytycznych:

1. Zrób fork repozytorium
2. Utwórz gałąź funkcji: `git checkout -b feature/nazwa-funkcji`
3. Zatwierdź zmiany: `git commit -m 'feat: dodaj funkcję'`
4. Wypchnij do gałęzi: `git push origin feature/nazwa-funkcji`
5. Otwórz Pull Request

### Konfiguracja Deweloperska

```bash
git clone https://github.com/kglebows/DXF2SVG.git
cd DXF2SVG
python -m venv venv
source venv/bin/activate  # Na Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Styl Kodu
- Przestrzegaj wytycznych PEP 8
- Używaj type hints dla sygnatur funkcji
- Dokumentuj złożoną logikę komentarzami inline
- Pisz opisowe komunikaty commit (format conventional commits)

##  Licencja

Ten projekt jest licencjonowany na licencji MIT:

```
MIT License

Copyright (c) 2024-2025 Konrad Głębowski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

##  Wsparcie

W razie pytań, zgłoszeń błędów lub próśb o funkcje:
- **Issues**: [GitHub Issues](https://github.com/kglebows/DXF2SVG/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kglebows/DXF2SVG/discussions)

##  Podziękowania

- [ezdxf](https://github.com/mozman/ezdxf) - Doskonała biblioteka do parsowania DXF
- [svgwrite](https://github.com/mozman/svgwrite) - Solidne generowanie SVG
- Społeczność Python Tkinter za najlepsze praktyki GUI

---

**Stworzone przez Konrada Głębowskiego **
