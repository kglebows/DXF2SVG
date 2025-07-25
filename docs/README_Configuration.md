# System Konfiguracji DXF2SVG

System konfiguracji pozwala na łatwe zarządzanie ustawieniami dla różnych obiektów i projektów.

## Struktura plików konfiguracyjnych

Pliki konfiguracyjne znajdują się w folderze `configs/` i mają rozszerzenie `.cfg`. Używają formatu INI z sekcjami:

### Sekcje konfiguracji:

#### `[BASIC]` - Podstawowe ustawienia
- `station_id` - ID stacji (np. ZIEB, WIE4)
- `current_text_format` - Format tekstów (format_1, format_2, format_3)
- `layer_line` - Nazwa warstwy linii DXF
- `layer_text` - Nazwa warstwy tekstów DXF

#### `[SVG]` - Ustawienia SVG
- `svg_width` - Szerokość SVG
- `svg_height` - Wysokość SVG  
- `margin` - Margines SVG

#### `[SEARCH]` - Parametry wyszukiwania
- `search_radius` - Promień wyszukiwania elementów
- `text_location` - Lokalizacja tekstów (above, below, any)
- `y_tolerance` - Tolerancja Y
- `x_tolerance` - Tolerancja X
- `cluster_distance_threshold` - Próg odległości klastrów
- `max_distance` - Maksymalna odległość automatycznego przypisania

#### `[COLORS]` - Kolory elementów
- `assigned_segment_color` - Kolor przypisanych segmentów
- `unassigned_segment_color` - Kolor nieprzypisanych segmentów
- `text_segment_color` - Kolor tekstów segmentów
- `segment_center_color_assigned` - Kolor środków przypisanych segmentów
- `segment_center_color_unassigned` - Kolor środków nieprzypisanych segmentów
- `text_color_assigned` - Kolor przypisanych tekstów
- `text_color_unassigned` - Kolor nieprzypisanych tekstów

#### `[FILES]` - Pliki wejściowe i wyjściowe
- `default_dxf_file` - Domyślny plik DXF do załadowania
- `structured_svg_output` - Nazwa pliku strukturalnego SVG

#### `[VISUALIZATION]` - Parametry wizualizacji
- `show_text_dots` - Pokazuj kropki tekstów (True/False)
- `show_text_labels` - Pokazuj etykiety tekstów (True/False)
- `show_string_labels` - Pokazuj etykiety stringów (True/False)
- `show_segment_centers` - Pokazuj środki segmentów (True/False)
- `show_segment_labels` - Pokazuj etykiety segmentów (True/False)
- `dot_radius` - Promień kropek
- `text_size` - Rozmiar tekstu
- `text_opacity` - Przezroczystość tekstu
- `string_label_offset` - Przesunięcie etykiet stringów
- `mptt_height` - Wysokość MPPT
- `segment_min_width` - Minimalna szerokość segmentu

## Używanie systemu konfiguracji

### W aplikacji GUI

1. **Zakładka Konfiguracja**: Użyj zakładki "⚙️ Konfiguracja" w aplikacji
2. **Wczytywanie**: Wybierz nazwę konfiguracji i kliknij "Wczytaj"
3. **Edytowanie**: Zmień parametry w interfejsie
4. **Zapisywanie**: Wprowadź nową nazwę i kliknij "Zapisz"
5. **Zastosowanie**: Kliknij "Zastosuj zmiany" aby aktywować ustawienia

### Z wiersza poleceń

```bash
# Domyślna konfiguracja
python run_interactive_gui.py

# Konkretna konfiguracja
python run_interactive_gui.py --config zieb
python run_interactive_gui.py -c wie4

# Pomoc
python run_interactive_gui.py --help
```

### Przez plik .bat

```bat
# Domyślna konfiguracja
start_gui.bat

# Z konfiguracją
start_gui.bat zieb
start_gui.bat wie4
```

## Przykładowe konfiguracje

### zieb.cfg - Standardowa konfiguracja dla obiektu ZIEB
- Format tekstów: format_1 (STACJA/FALOWNIK/MPPT/STRING)
- Station ID: ZIEB
- Rozmiar SVG: 1600x800
- Lokalizacja tekstów: above

### wie4.cfg - Konfiguracja dla obiektu WIE4
- Format tekstów: format_2 (STACJA/ST/FALOWNIK/MPPT/STRING)
- Station ID: WIE4
- Rozmiar SVG: 1800x900
- Lokalizacja tekstów: below
- Większy promień wyszukiwania

## Tworzenie nowych konfiguracji

1. **Przez GUI**: 
   - Otwórz zakładkę Konfiguracja
   - Kliknij "Nowy"
   - Ustaw parametry
   - Wprowadź nazwę
   - Kliknij "Zapisz"

2. **Ręcznie**:
   - Skopiuj istniejący plik .cfg
   - Zmień nazwę na `nowa_nazwa.cfg`
   - Edytuj parametry w edytorze tekstu
   - Umieść w folderze `configs/`

## Hierarchia ustawień

1. **Domyślne** - zdefiniowane w `config.py`
2. **Plik konfiguracyjny** - nadpisuje domyślne jeśli istnieje
3. **Interface GUI** - tymczasowe zmiany do zastosowania

Jeśli parametr nie istnieje w pliku .cfg, zostanie użyta wartość domyślna z `config.py`.

## Formaty tekstów

### format_1: STACJA/FALOWNIK/MPPT/STRING
Przykład: `ZIEB/F02/MPPT01/S01`

### format_2: STACJA/ST/FALOWNIK/MPPT/STRING  
Przykład: `WIE4/ST01/F04/MPPT03/S09`

### format_3: PREFIX;STACJA/FALOWNIK/MPPT/STRING
Przykład: `PREFIX;ZIEB/F02/MPPT01/S01`

Wybór formatu wpływa na sposób parsowania i interpretacji tekstów z pliku DXF.
