# Multi-Format Text Formatting - Implementation Summary

## Przegląd zmian

Dodano funkcjonalność obsługi wielu formatowań tekstów w jednej konfiguracji. Użytkownik może teraz dodawać wiele formatów za pomocą przycisku "+", a parser automatycznie próbuje wszystkie formaty po kolei, aż znajdzie pasujący. Każdy format ma własny output_format, który jest używany przy generowaniu końcowego SVG.

## Zmodyfikowane pliki

### 1. `src/gui/unified_config_tab.py`
**Zmiany w strukturze danych:**
- Zmieniono z pojedynczego formatu na listę formatów: `self.text_formats = []`
- Każdy format to dict z kluczami: `id`, `name`, `station_id`, `input_format`, `output_format`, `variables`
- Każde pole to `StringVar` dla automatycznej synchronizacji z GUI

**Nowe funkcje:**
- `add_text_format()` - Dodaje nowy format do listy (przycisk "+")
- `create_single_format_card()` - Tworzy GUI card dla pojedynczego formatu
- `remove_text_format()` - Usuwa format (minimum 1 musi zostać)
- `create_advanced_variables_collapsible_for_format()` - Rozwijalna sekcja zmiennych dla formatu

**Zmodyfikowane funkcje:**
- `create_formatting_section()` - Całkowita przebudowa: nagłówek z "+", kontener na karty formatów
- `save_fields_to_config()` - Zapisuje `TEXT_FORMATS_LIST` (lista dicts), backward compatibility
- `load_config_to_fields()` - Odtwarza GUI z `TEXT_FORMATS_LIST`, tworzy karty dynamicznie

**Format danych TEXT_FORMATS_LIST:**
```python
[
    {
        'id': 1,
        'name': 'Format 1',
        'station_id': 'Grabowo3',
        'input_format': '{name}/F{inv:2}/STR{str:2}',
        'output_format': 'S{mppt:2}-{str:2}/{inv:2}',
        'variables': {
            'st': '0', 'tr': '0', 'inv': '0',
            'mppt': '(inv - 1) * 2 + (1 if str <= 10 else 2)',
            'str': 'str if str <= 10 else str - 10',
            'sub': '0'
        }
    },
    # ... więcej formatów
]
```

### 2. `src/core/config.py`
**Funkcja `parse_text_to_dict()`:**
- Dodano sekcję próbującą wszystkie formaty z `TEXT_FORMATS_LIST`
- Pętla przez `text_formats_list` próbuje każdy format po kolei
- Pierwsze dopasowanie zwraca dict z dodatkowymi kluczami:
  - `format_index`: index formatu który pasował (0-based)
  - `format_name`: nazwa formatu (np. "Format 1")
  - `output_format`: output_format z tego konkretnego formatu
  - `variables`: sparsowane zmienne z AdvancedFormatter
  - `parsed_with`: zawsze 'advanced_formatting'

**Backward compatibility:**
- Jeśli `TEXT_FORMATS_LIST` pusta, używa starego `ADVANCED_INPUT_FORMAT`/`ADVANCED_OUTPUT_FORMAT`
- Jeśli zaawansowane formatowanie wyłączone, używa legacy parsera

**Funkcja `get_advanced_formatted_id()`:**
- **KRYTYCZNA ZMIANA**: Używa `parsed.get('output_format')` zamiast globalnego `ADVANCED_OUTPUT_FORMAT`
- Sprawdza czy `parsed` już zawiera `variables` (unika re-parsowania)
- Jeśli zmienne są, używa ich bezpośrednio
- Jeśli nie ma, parsuje tekst (legacy path)
- Debug log: `"DEBUG: final SVG ID result = ... (from output_format: ...)"`

### 3. `src/config/config_manager.py`
**Funkcja `apply_to_config_module()`:**
- Dodano eksplicytne ustawienie `config.TEXT_FORMATS_LIST = data.get('TEXT_FORMATS_LIST', [])`
- Zapewnia że lista formatów jest dostępna przez `globals().get('TEXT_FORMATS_LIST')`
- Konieczne żeby parser miał dostęp do formatów

## Przepływ danych

### 1. Konfiguracja formatów (GUI → Config)
```
unified_config_tab.py:
  add_text_format() -> self.text_formats.append({...})
  save_fields_to_config() -> config_data['TEXT_FORMATS_LIST'] = [...]
  
config_manager.py:
  apply_to_config_module() -> config.TEXT_FORMATS_LIST = [...]
```

### 2. Parsowanie tekstu (Parser)
```
config.py:parse_text_to_dict():
  text_formats_list = globals().get('TEXT_FORMATS_LIST', [])
  for fmt in text_formats_list:
    formatter.parse_input_format(text, fmt['input_format'])
    if matches:
      return {
        'output_format': fmt['output_format'],
        'variables': parsed_vars,
        'format_index': i,
        'format_name': fmt['name'],
        ...
      }
```

### 3. Generowanie SVG ID (SVG Generator)
```
svg_generator.py:
  parsed_text = config.parse_text_to_dict(text_id, station_id)
  structural_id = config.get_svg_id(parsed_text)
  
config.py:get_svg_id():
  return get_advanced_formatted_id(parsed)
  
config.py:get_advanced_formatted_id():
  output_format = parsed.get('output_format', global_fallback)  # NOWE!
  variables = parsed.get('variables', None)  # NOWE!
  if variables:
    formatter.variables = variables  # Użyj gotowych zmiennych
  result = formatter.format_output(output_format)  # Użyj format-specific output
  return result
```

## Backward Compatibility

### Stare konfiguracje (bez TEXT_FORMATS_LIST)
- Parser używa `ADVANCED_INPUT_FORMAT` i `ADVANCED_OUTPUT_FORMAT` z globals
- `get_advanced_formatted_id()` używa globalnego output_format
- GUI może załadować starą konfigurację i przekonwertować na nowy format

### Stare SVG generation
- Jeśli `parsed` nie ma `output_format`, używa globalnego
- Jeśli `parsed` nie ma `variables`, parsuje tekst normalnie

## Testy manualne

### Test 1: Dodawanie formatów
1. Otwórz GUI
2. Kliknij "+" w sekcji Formatowanie tekstów
3. Sprawdź czy pojawił się nowy format card
4. Edytuj pola name, input_format, output_format
5. Kliknij "Zapisz konfigurację"
6. Zamknij i otwórz ponownie - sprawdź czy formaty zostały zachowane

### Test 2: Parsowanie z wieloma formatami
1. Skonfiguruj 2 formaty:
   - Format 1: input=`{name}/F{inv:2}/STR{str:2}`, output=`S{mppt:2}-{str:2}/{inv:2}`
   - Format 2: input=`{name}-I{inv:2}-S{str:2}`, output=`I{inv:2}/S{str:2}`
2. Wczytaj DXF z tekstami w formacie 1
3. Sprawdź `debug.log`:
   - Powinno być: `Format 'Format 1' rozpoznał: {...}`
   - NIE powinno być: `Format 'Format 2' rozpoznał`
4. Wygeneruj SVG i sprawdź ID - powinny być w formacie `S01-01/01`

### Test 3: Backward compatibility
1. Wczytaj starą konfigurację (np. `gostynin2-st1.cfg`)
2. Sprawdź czy działa mimo braku TEXT_FORMATS_LIST
3. Zmodyfikuj i zapisz - sprawdź czy tworzy TEXT_FORMATS_LIST

## Potencjalne problemy

### Problem: Parser nie rozpoznaje tekstów
**Diagnoza:** Sprawdź debug.log dla "Format 'X' nie rozpoznał tekstu"
**Rozwiązanie:** 
- Sprawdź czy input_format pasuje do tekstów w DXF
- Sprawdź czy TEXT_FORMATS_LIST jest ustawione w config module

### Problem: SVG ma złe ID
**Diagnoza:** Sprawdź debug.log dla "DEBUG: final SVG ID result = ..."
**Rozwiązanie:**
- Sprawdź czy parsed dict zawiera 'output_format'
- Sprawdź czy get_advanced_formatted_id() używa właściwego output_format

### Problem: GUI nie zapisuje formatów
**Diagnoza:** Sprawdź czy config file ma sekcję [TEXT_FORMATS_LIST]
**Rozwiązanie:**
- Sprawdź save_fields_to_config() w unified_config_tab.py
- Sprawdź czy self.text_formats nie jest puste

## Logi diagnostyczne

### Parsowanie tekstu
```
DEBUG: Próbuję zaawansowane formatowanie...
DEBUG: Format 'Format Grabowo' rozpoznał: {'name': 'Grabowo3', 'inv': 1, 'str': 1}
DEBUG: Zwracam standardowy format z 'Format Grabowo': {...}
```

### Generowanie SVG ID
```
DEBUG: original_text = Grabowo3/F01/STR01
DEBUG: formatter variables = {'name': 'Grabowo3', 'inv': 1, 'str': 1}
DEBUG: final SVG ID result = S01-01/01 (from output_format: S{mppt:2}-{str:2}/{inv:2})
```

## Przyszłe ulepszenia

1. **Validation:** Sprawdzanie czy input_format i output_format są poprawne
2. **Preview:** Pokazanie przykładowego output dla każdego formatu
3. **Reorder:** Możliwość zmiany kolejności formatów (priorytet)
4. **Import/Export:** Eksport/import formatów między konfiguracjami
5. **Templates:** Gotowe szablony formatów dla popularnych przypadków
