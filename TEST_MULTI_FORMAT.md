# Test Multi-Format Text Formatting

## Cel testu
Sprawdzenie czy system multi-format działa poprawnie:
1. Czy można dodawać wiele formatowań tekstów przyciskiem "+"
2. Czy parser próbuje wszystkie formaty po kolei
3. Czy SVG generuje ID używając output_format z właściwego formatu

## Scenariusz testowy

### Krok 1: Uruchom aplikację
```powershell
.\start_gui.bat
```

### Krok 2: Konfiguracja formatów
1. Przejdź do zakładki konfiguracji
2. Znajdź sekcję "Formatowanie tekstów"
3. Kliknij przycisk "+" aby dodać drugi format

### Krok 3: Skonfiguruj Format 1
- **Nazwa**: "Format Grabowo"
- **{name}**: Grabowo3
- **Input format**: `{name}/F{inv:2}/STR{str:2}`
- **Output format**: `S{mppt:2}-{str:2}/{inv:2}`
- **Zmienne**:
  - mppt: `(inv - 1) * 2 + (1 if str <= 10 else 2)`
  - inv: `inv`
  - str: `str if str <= 10 else str - 10`

### Krok 4: Skonfiguruj Format 2  
- **Nazwa**: "Format Alternatywny"
- **{name}**: TestStation
- **Input format**: `{name}-I{inv:2}-M{mppt:2}-S{str:2}`
- **Output format**: `I{inv:2}/M{mppt:2}/S{str:2}`
- **Zmienne**: (domyślne wartości)

### Krok 5: Wczytaj plik DXF z tekstami
- Użyj `Grabowo3.dxf` (powinien mieć teksty w formacie "Grabowo3/F01/STR01")
- Parser powinien spróbować Format 1, potem Format 2
- Format 1 powinien rozpoznać teksty

### Krok 6: Wygeneruj SVG
- Sprawdź w logach którym formatem zostały rozpoznane teksty
- Powinno być: `Format 'Format Grabowo' rozpoznał: {...}`
- SVG powinien zawierać ID w formacie `S01-01/01` (z output_format Format 1)

### Krok 7: Sprawdź logi
Szukaj w `debug.log`:
```
Format 'Format Grabowo' rozpoznał: {'name': 'Grabowo3', 'inv': 1, 'str': 1}
DEBUG: final SVG ID result = S01-01/01 (from output_format: S{mppt:2}-{str:2}/{inv:2})
```

## Oczekiwane rezultaty

✅ **Sukces** jeśli:
- Można dodać wiele formatów przyciskiem "+"
- Każdy format ma własne pola: name, station_id, input_format, output_format, zmienne
- Parser próbuje formaty po kolei i znajduje pasujący
- SVG ID używa output_format z formatu który rozpoznał tekst
- Logi pokazują nazwę formatu i wygenerowany ID

❌ **Błąd** jeśli:
- Nie można dodać nowego formatu
- Parser używa tylko jednego formatu
- SVG ID nie odpowiada output_format z właściwego formatu
- Błędy w logach dotyczące TEXT_FORMATS_LIST

## Backward Compatibility Test

### Test starej konfiguracji (single format)
1. Wczytaj starą konfigurację (bez TEXT_FORMATS_LIST)
2. Powinien działać stary ADVANCED_INPUT_FORMAT i ADVANCED_OUTPUT_FORMAT
3. Parser powinien użyć fallback do pojedynczego formatu
4. SVG powinien nadal być generowany poprawnie

## Debug Tips

### Jeśli parser nie rozpoznaje tekstów:
- Sprawdź czy TEXT_FORMATS_LIST jest ustawione w config module
- Zobacz config_manager.py -> apply_to_config_module()
- Sprawdź debug.log dla komunikatów "Format 'X' nie rozpoznał tekstu"

### Jeśli SVG ma złe ID:
- Sprawdź czy parsed dict zawiera 'output_format' i 'variables'
- Zobacz config.py -> get_advanced_formatted_id()
- Sprawdź logi "DEBUG: final SVG ID result = ..."

### Jeśli GUI nie działa:
- Sprawdź unified_config_tab.py -> create_formatting_section()
- Czy self.text_formats jest listą?
- Czy add_text_format() tworzy nowe dictionaries?
