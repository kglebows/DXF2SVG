"""
Konfiguracja formatów tekstów i parametrów systemu
"""
import re
from typing import Dict
from src.utils.console_logger import console, logger

# ============================================================================
# KONFIGURACJA FORMATÓW TEKSTÓW
# ============================================================================
TEXT_FORMATS = {
    # Format 1: STACJA/FALOWNIK/MPPT/STRING (stary format)
    'format_1': {
        'pattern': r'^([^/]+)/F(\d+)/(MPPT\d+)/(.+)$',
        'description': 'Format: STACJA/FALOWNIK/MPPT/STRING (np. WIE2/F02/MPPT01/S01)',
        'groups': {
            'station': 1,      # Grupa 1: STACJA
            'inverter': 2,     # Grupa 2: FALOWNIK (numer)
            'mppt': 3,         # Grupa 3: MPPT
            'substring': 4     # Grupa 4: STRING
        },
        'station_format': lambda station: station,  # Bez zmian
        'inverter_format': lambda inv: f"I{inv.zfill(2)}"  # Dodaj I i wypełnij zerami
    },
    
    # Format 2: STACJA/ST/FALOWNIK/MPPT/STRING (nowy format)
    'format_2': {
        'pattern': r'^([^/]+)/ST(\d+)/F(\d+)/(MPPT\d+)/(.+)$',
        'description': 'Format: STACJA/ST/FALOWNIK/MPPT/STRING (np. WIE4/ST01/F04/MPPT03/S09)',
        'groups': {
            'station': 1,      # Grupa 1: STACJA
            'station_num': 2,  # Grupa 2: Numer stacji (po ST)
            'inverter': 3,     # Grupa 3: FALOWNIK (po F)
            'mppt': 4,         # Grupa 4: MPPT
            'substring': 5     # Grupa 5: STRING
        },
        'station_format': lambda station, st_num: f"{station}/ST{st_num.zfill(2)}",  # Połącz stację i numer
        'inverter_format': lambda inv: f"I{inv.zfill(2)}"  # Dodaj I i wypełnij zerami
    },
    
    # Format 3: STACJA/FALOWNIK/MPPT/STRING z ; (format z separatorem)
    'format_3': {
        'pattern': r'^[^;]*;([^/]+)/(\d+)/(MPPT\d+)/(.+)$',
        'description': 'Format z separatorem: PREFIX;STACJA/FALOWNIK/MPPT/STRING',
        'groups': {
            'station': 1,      # Grupa 1: STACJA (po ;)
            'inverter': 2,     # Grupa 2: FALOWNIK
            'mppt': 3,         # Grupa 3: MPPT
            'substring': 4     # Grupa 4: STRING
        },
        'station_format': lambda station: station,
        'inverter_format': lambda inv: f"I{inv.zfill(2)}"
    },
    
    # Format 4: INV01-02 (INVERTER-MPPT) - zawsze string 0
    'format_4': {
        'pattern': r'^INV(\d+)-(\d+)$',
        'description': 'Format: INV<INVERTER>-<MPPT> (np. INV01-02) - automatycznie string 0',
        'groups': {
            'inverter': 1,     # Grupa 1: INVERTER (po INV)
            'mppt': 2,         # Grupa 2: MPPT (po -)
        },
        'inverter_format': lambda inv: f"I{inv.zfill(2)}",  # I01, I02, etc.
        'mppt_format': lambda mppt: f"MPPT{mppt.zfill(2)}",  # MPPT01, MPPT02, etc.
        'substring_format': lambda: "S00"  # Zawsze string 0
    },
    # Format 5: STACJA/FALOWNIK/STR (Upale - nowy format)
    'format_5': {
        'pattern': r'^([^/]+)/F(\d+)/(STR\d+)$',
        'description': 'Format: STACJA/FALOWNIK/STR (np. STM2/F06/STR19)',
        'groups': {
            'station': 1,      # Grupa 1: STACJA
            'inverter': 2,     # Grupa 2: FALOWNIK (numer)
            'mppt': 3         # Grupa 3: STR (string jako MPPT)
        },
        'station_format': lambda station: station,  # Bez zmian
        'inverter_format': lambda inv: f"I{inv.zfill(2)}",  # Dodaj I i wypełnij zerami
        'mppt_format': lambda str_num: f"MPPT{str_num.replace('STR', '').zfill(2)}",  # STR19 -> MPPT19
        'substring_format': lambda: "S00"  # Zawsze string 0
    },
}

# WYBIERZ FORMAT DLA TEGO OBIEKTU
CURRENT_TEXT_FORMAT = 'format_1'  # Ustaw na 'format_1', 'format_2', lub 'format_3'

# ============================================================================
# KONFIGURACJA PODSTAWOWA
# ============================================================================
STATION_ID = "ZIEB"
STATION_NUMBER = "01"  # Numer stacji dla formatu structured SVG
ID_FORMAT = "01-02/03"  # Format ID: 01-MPPT, 02-String, 03-Inverter ALBO 05-06/07 gdzie 05-Station, 06-MPPT, 07-Inverter
LAYER_LINE = "@IDE_KABLE_DC_B"
LAYER_TEXT = "@IDE_KABLE_DC_TXT_B"
SVG_WIDTH = 1600
SVG_HEIGHT = 800
MPTT_HEIGHT = 1
SEGMENT_MIN_WIDTH = 0
ASSIGNED_SEGMENT_COLOR = "#00778B"  # Kolor przypisanych segmentów
UNASSIGNED_SEGMENT_COLOR = "#FFC0CB"  # Różowy dla nieprzypisanych segmentów
TEXT_SEGMENT_COLOR = "#000000"  # Czarny dla tekstów segmentów

# ============================================================================
# ZAAWANSOWANE FORMATOWANIE
# ============================================================================
USE_ADVANCED_FORMATTING = False
ADVANCED_INPUT_FORMAT = "{name}/F{inv:2}/STR{str:2}"
ADVANCED_OUTPUT_FORMAT = "S{mppt:2}-{str:2}/{inv:2}"
ADVANCED_ADDITIONAL_VARS = {"mppt": "{str}/2 + {str}%2"}
Y_TOLERANCE = 0.01
X_TOLERANCE = 0.01
SEARCH_RADIUS = 6.0 
TEXT_LOCATION = "above"     # "above", "below", "any"

# Parametry segmentacji polilinii
POLYLINE_PROCESSING_MODE = "individual_segments"  # "individual_segments", "merge_segments" 
SEGMENT_MERGE_GAP_TOLERANCE = 1.0  # Tolerancja przerw między segmentami do łączenia
MAX_MERGE_DISTANCE = 5.0  # Maksymalna odległość między punktami końcowymi do łączenia

# Parametry wizualizacji
SHOW_TEXT_DOTS = True
SHOW_TEXT_LABELS = True
SHOW_STRING_LABELS = True
SHOW_SEGMENT_CENTERS = True  # Nowy parametr - pokazuj środki segmentów
SHOW_SEGMENT_LABELS = True   # Nowy parametr - pokazuj etykiety segmentów
DOT_RADIUS = 0.25
TEXT_SIZE = 1
TEXT_OPACITY = 0.5  # Przezroczystość tekstu
SEGMENT_CENTER_COLOR_ASSIGNED = "#FFFB00"    # Pomarańczowy dla przypisanych
SEGMENT_CENTER_COLOR_UNASSIGNED = "#FF7B00"  # Żółty dla nieprzypisanych
TEXT_COLOR_ASSIGNED = "#00FF15"  # Czarny dla przypisanych tekstów
TEXT_COLOR_UNASSIGNED = "#FF0000"  # Czerwony dla niepr
STRING_LABEL_OFFSET = 0
CLUSTER_DISTANCE_THRESHOLD = 300.0
MARGIN = 2.0  # Margines dla SVG
MAX_DISTANCE = 10.0  # Maksymalna odległość dla automatycznego przypisania

# Nowe parametry edytora interaktywnego
SHOW_ELEMENT_POINTS = False  # Pokazuj wszystkie kropki i trójkąty
SHOW_ASSIGNED_SEGMENT_LABELS = True  # Pokazuj numery segmentów przypisanych
SHOW_UNASSIGNED_SEGMENT_LABELS = True  # Pokazuj numery segmentów nieprzypisanych
SELECTED_SEGMENT_COLOR = "#FFFF00"  # Żółty dla zaznaczonego segmentu
SELECTED_TEXT_COLOR = "#00FFFF"  # Cyan dla zaznaczonego tekstu
HOVER_SEGMENT_COLOR = "#FFB6C1"  # Jasny różowy dla segmentów w grupie (hover)
HOVER_TEXT_COLOR = "#8B008B"  # Ciemny fioletowy dla tekstów w grupie (hover)

def print_format_info():
    """Wyświetl informacje o dostępnych formatach tekstu"""
    logger.info("Wyświetlanie informacji o formatach tekstów")
    
    console.header("KONFIGURACJA FORMATÓW TEKSTÓW")
    
    for format_key, format_config in TEXT_FORMATS.items():
        is_current = format_key == CURRENT_TEXT_FORMAT
        status = "<<< AKTUALNY" if is_current else ""
        
        if is_current:
            console.success(f"{format_key}: {format_config['description']} {status}")
        else:
            console.info(f"{format_key}: {format_config['description']}", "📝")
            
        logger.debug(f"Format {format_key}: pattern='{format_config['pattern']}', groups={format_config['groups']}")
    
    console.separator()
    from src.utils.console_logger import Colors
    console.result("AKTUALNY FORMAT", CURRENT_TEXT_FORMAT, Colors.BRIGHT_GREEN)
    console.result("OCZEKIWANE ID STACJI", STATION_ID, Colors.BRIGHT_YELLOW)
    console.separator()

def clean_dxf_text(text: str) -> str:
    """Czyszczenie tekstu z formatowania DXF"""
    text = re.sub(r'\\\{.*?\}', '', text)
    text = re.sub(r'\\[A-Za-z0-9]+\b', '', text)
    text = re.sub(r'[\\{}]', '', text)
    text = re.sub(r'^[^a-zA-Z0-9]+', '', text)
    text = text.replace(" ", "").strip()
    return text

def parse_string_name(text: str):
    """Uniwersalna funkcja parsowania tekstów wspierająca różne formaty - zwraca stację"""
    try:
        parsed = parse_text_to_dict(text)
        if parsed:
            return parsed.get('station')
        return None
    except Exception as e:
        logger.error(f"Błąd parsowania tekstu '{text}': {e}")
        return None

def parse_text_to_dict(text: str, station_id: str = None) -> Dict:
    """Uniwersalna funkcja parsowania tekstów wspierająca różne formaty - zwraca pełne dane"""
    try:
        cleaned = clean_dxf_text(text)
        logger.debug(f"Tekst oryginalny: '{text}' -> po czyszczeniu: '{cleaned}'")
        
        # SPRAWDŹ NAJPIERW ZAAWANSOWANE FORMATOWANIE (WIELE FORMATÓW)
        # WAŻNE: Użyj zmiennej modułowej, nie globals()
        if USE_ADVANCED_FORMATTING:
            logger.debug("Próbuję zaawansowane formatowanie...")
            
            from src.core.advanced_formatter import AdvancedFormatter
            
            # Pobierz listę formatowań
            text_formats_list = TEXT_FORMATS_LIST
            
            if text_formats_list:
                # Próbuj każde formatowanie po kolei
                for fmt_index, fmt_data in enumerate(text_formats_list):
                    input_format = fmt_data.get('input_format', '')
                    output_format = fmt_data.get('output_format', '')
                    station_id_fmt = fmt_data.get('station_id', '')
                    additional_vars = fmt_data.get('variables', {})
                    format_name = fmt_data.get('name', f'Format {fmt_index + 1}')
                    
                    if input_format and output_format:
                        formatter = AdvancedFormatter()
                        variables = formatter.parse_input_format(cleaned, input_format)
                        
                        if variables:
                            # Sprawdź czy name pasuje do station_id formatu
                            if station_id_fmt and variables.get('name') != station_id_fmt:
                                logger.debug(f"{format_name} odrzucił: name={variables.get('name')} != station_id={station_id_fmt}")
                                continue  # Odrzuć ten format, próbuj następny
                            
                            logger.debug(f"Format '{format_name}' rozpoznał: {variables}")
                            
                            # Zastosuj dodatkowe zmienne obliczeniowe (jeśli są)
                            if additional_vars:
                                formatter.variables = variables
                                for var_name, expression in additional_vars.items():
                                    if expression and expression.strip():  # Tylko jeśli expression nie jest puste
                                        # Oblicz wartość wyrazyżenia i zaktualizuj variables
                                        result_value = formatter._evaluate_expression(expression, variables)
                                        variables[var_name] = result_value
                                        logger.debug(f"Obliczono {var_name} = {result_value} (z {expression})")
                            
                            # Utwórz standardowy dict format dla kompatybilności z resztą systemu
                            result = {
                                'station': variables.get('name', variables.get('st', station_id_fmt or station_id or STATION_ID)),
                                'station_id': variables.get('name', variables.get('st', station_id_fmt or station_id or STATION_ID)),
                                'inverter': f"I{variables.get('inv', 0):02d}",
                                'mppt': f"MPPT{variables.get('mppt', 0)}",
                                'substring': f"STR{variables.get('str', variables.get('tr', 0))}",
                                'original_text': text,
                                'parsed_with': 'advanced_formatting',
                                'format_index': fmt_index,  # Zapisz index formatowania
                                'format_name': format_name,  # Zapisz nazwę formatowania
                                'output_format': output_format,  # Zapisz output format dla tego tekstuszczegółowe
                                'variables': variables  # Zachowaj oryginalne zmienne
                            }
                            
                            logger.debug(f"Zwracam standardowy format z '{format_name}': {result}")
                            return result
                        else:
                            logger.debug(f"Format '{format_name}' nie rozpoznał tekstu '{cleaned}'")
            else:
                # BACKWARD COMPATIBILITY: Stary sposób (pojedyncze formatowanie)
                input_format = ADVANCED_INPUT_FORMAT
                output_format = ADVANCED_OUTPUT_FORMAT
                additional_vars = ADVANCED_ADDITIONAL_VARS
                
                if input_format and output_format:
                    formatter = AdvancedFormatter()
                    variables = formatter.parse_input_format(cleaned, input_format)
                    
                    if variables:
                        logger.debug(f"Zaawansowane formatowanie rozpoznało: {variables}")
                        
                        result = {
                            'station': variables.get('name', variables.get('st', station_id or STATION_ID)),
                            'station_id': variables.get('name', variables.get('st', station_id or STATION_ID)),
                            'inverter': f"I{variables.get('inv', 0):02d}",
                            'mppt': f"MPPT{variables.get('mppt', 0)}",
                            'substring': f"STR{variables.get('str', variables.get('tr', 0))}",
                            'original_text': text,
                            'parsed_with': 'advanced_formatting',
                            'format_index': 0,
                            'output_format': output_format,
                            'variables': variables
                        }
                        
                        logger.debug(f"Zwracam standardowy format: {result}")
                        return result
        
        # LEGACY FORMATOWANIE (jeśli zaawansowane nie zadziałało)
        logger.debug("Próbuję legacy formatowanie...")
        
        # Użyj przekazanego station_id lub domyślnego z config
        if station_id is None:
            station_id = STATION_ID
        
        # Próbuj najpierw aktualny format
        if CURRENT_TEXT_FORMAT in TEXT_FORMATS:
            result = try_parse_format(cleaned, CURRENT_TEXT_FORMAT, text, station_id)
            if result:
                return result
        
        # Jeśli aktualny format nie zadziałał, próbuj wszystkie inne
        for format_name in TEXT_FORMATS:
            if format_name != CURRENT_TEXT_FORMAT:
                result = try_parse_format(cleaned, format_name, text, station_id)
                if result:
                    logger.info(f"Tekst '{text}' rozpoznany jako format {format_name}")
                    return result
        
        # Jeśli żaden format nie pasuje
        logger.warning(f"Tekst '{text}' nie pasuje do żadnego znanego formatu")
        return None
        
    except Exception as e:
        logger.error(f"Błąd parsowania tekstu '{text}': {e}")
        return None

def try_parse_format(cleaned_text: str, format_name: str, original_text: str, station_id: str) -> Dict:
    """Próbuje sparsować tekst używając określonego formatu"""
    try:
        format_config = TEXT_FORMATS[format_name]
        pattern = format_config['pattern']
        groups = format_config['groups']
        
        logger.debug(f"Próbuję format {format_name} z wzorcem: {pattern}")
        
        # Dopasuj wzorzec
        match = re.match(pattern, cleaned_text)
        if not match:
            return None
        
        logger.debug(f"Dopasowane grupy dla {format_name}: {match.groups()}")
        
        # Wyciągnij dane według formatu
        result = {}
        
        if format_name == 'format_1':
            # Format: STACJA/FALOWNIK/MPPT/STRING
            station = match.group(groups['station'])
            inverter_num = match.group(groups['inverter'])
            mppt = match.group(groups['mppt'])
            substring = match.group(groups['substring'])
            
            result = {
                'station': format_config['station_format'](station),
                'inverter': format_config['inverter_format'](inverter_num),
                'mppt': mppt,
                'substring': substring
            }
            logger.debug(f"Format 1 - Station: {station}, Inverter: {inverter_num}, MPPT: {mppt}, String: {substring}")
            
        elif format_name == 'format_2':
            # Format: STACJA/ST/FALOWNIK/MPPT/STRING
            station = match.group(groups['station'])
            station_num = match.group(groups['station_num'])
            inverter_num = match.group(groups['inverter'])
            mppt = match.group(groups['mppt'])
            substring = match.group(groups['substring'])
            
            result = {
                'station': format_config['station_format'](station, station_num),
                'inverter': format_config['inverter_format'](inverter_num),
                'mppt': mppt,
                'substring': substring
            }
            logger.debug(f"Format 2 - Station: {station}, ST: {station_num}, Inverter: {inverter_num}, MPPT: {mppt}, String: {substring}")
            
        elif format_name == 'format_3':
            # Format z separatorem: PREFIX;STACJA/FALOWNIK/MPPT/STRING
            station = match.group(groups['station'])
            inverter_num = match.group(groups['inverter'])
            mppt = match.group(groups['mppt'])
            substring = match.group(groups['substring'])
            
            result = {
                'station': format_config['station_format'](station),
                'inverter': format_config['inverter_format'](inverter_num),
                'mppt': mppt,
                'substring': substring
            }
            logger.debug(f"Format 3 - Station: {station}, Inverter: {inverter_num}, MPPT: {mppt}, String: {substring}")
            
        elif format_name == 'format_4':
            # Format INV01-02: INVERTER-MPPT (zawsze string 0)
            inverter_num = match.group(groups['inverter'])
            mppt_num = match.group(groups['mppt'])
            
            result = {
                'station': station_id,  # Używaj przekazanego station_id
                'inverter': format_config['inverter_format'](inverter_num),
                'mppt': format_config['mppt_format'](mppt_num),
                'substring': format_config['substring_format']()
            }
            logger.debug(f"Format 4 - Inverter: {inverter_num}, MPPT: {mppt_num}, String: 00 (auto), Station: {station_id}")
            
        elif format_name == 'format_5':
            # Format: STACJA/F<INVERTER>/STR<MPPT> (zawsze string 0)
            station = match.group(groups['station'])
            inverter_num = match.group(groups['inverter'])
            str_mppt = match.group(groups['mppt'])  # STR19
            
            result = {
                'station': format_config['station_format'](station),
                'inverter': format_config['inverter_format'](inverter_num),
                'mppt': format_config['mppt_format'](str_mppt),  # STR19 -> MPPT19
                'substring': format_config['substring_format']()  # S00
            }
            logger.debug(f"Format 5 - Station: {station}, Inverter: {inverter_num}, STR-MPPT: {str_mppt}, String: 00 (auto)")
        
        logger.debug(f"Sparsowane dane ({format_name}): {result}")
        return result
        
    except Exception as e:
        logger.debug(f"Błąd parsowania formatu {format_name}: {e}")
        return None

def get_svg_id(parsed: Dict) -> str:
    """Generuje SVG ID z sparsowanych danych zgodnie z aktualnym formatem ID"""
    try:
        # Sprawdź czy używamy zaawansowanego formatowania
        if USE_ADVANCED_FORMATTING:
            return get_advanced_formatted_id(parsed)
        
        # Pobierz aktualny format ID z konfiguracji (legacy system)
        current_format = ID_FORMAT
        
        # Wyciągnij numer MPPT
        mppt = parsed['mppt'].replace("MPPT", "").zfill(2)
        
        # Wyciągnij numer stringa
        sub = re.sub(r'[^0-9]', '', parsed['substring'])
        
        # Wyciągnij numer falownika (usuń prefiks I)
        inverter = parsed['inverter'].replace("I", "").zfill(2)
        
        if current_format == "01-02/03":
            # Format: 01-MPPT, 02-String, 03-Inverter
            return f"{mppt}-{sub.zfill(2)}/{inverter}"
        elif current_format == "05-06/07":
            # Format: 05-Station, 06-MPPT, 07-Inverter
            station_num = STATION_NUMBER.zfill(2)
            return f"{station_num}-{mppt}/{inverter}"
        else:
            # Fallback do starego formatu
            return f"{mppt}-{sub}/{inverter}"
            
    except Exception as e:
        logger.error(f"Błąd generowania SVG ID: {e}")
        return "unknown"


def get_advanced_formatted_id(parsed: Dict) -> str:
    """Generuje SVG ID używając zaawansowanego formatowania"""
    try:
        from src.core.advanced_formatter import AdvancedFormatter
        
        # NOWE: Jeśli parsed zawiera output_format (z multi-format parsing), użyj go
        # W przeciwnym razie użyj globalnego ADVANCED_OUTPUT_FORMAT (backward compatibility)
        output_format = parsed.get('output_format', ADVANCED_OUTPUT_FORMAT)
        
        # Pobierz konfigurację zaawansowanego formatowania
        input_format = ADVANCED_INPUT_FORMAT
        additional_vars = ADVANCED_ADDITIONAL_VARS
        
        if not output_format:
            logger.warning("Brak skonfigurowanego output_format, używam legacy")
            return get_legacy_formatted_id(parsed)
        
        # NOWE: Sprawdź czy parsed już zawiera zmienne (z parse_text_to_dict multi-format)
        # To pozwala uniknąć ponownego parsowania
        if 'variables' in parsed and parsed.get('variables'):
            logger.debug(f"Używam już sparsowanych zmiennych: {parsed['variables']}")
            variables = parsed['variables'].copy()  # Kopia aby nie modyfikować oryginalu
            
            # WAŻNE: Sprawdź czy trzeba zastosować dodatkowe zmienne obliczeniowe
            # Jeśli parsed pochodzi z TEXT_FORMATS_LIST, additional_vars już zostały zastosowane w parse_text_to_dict
            # Ale jeśli pochodzi z legacy path lub backward compatibility, zastosuj globalne additional_vars
            if 'format_index' not in parsed and additional_vars:  # Legacy parsing - zastosuj globalne additional_vars
                formatter = AdvancedFormatter()
                formatter.variables = variables
                for var_name, expression in additional_vars.items():
                    if expression and expression.strip():
                        result_value = formatter._evaluate_expression(expression, variables)
                        variables[var_name] = result_value
                        logger.debug(f"Zastosowano dodatkową zmienną {var_name} = {result_value}")
        else:
            # Musimy sparsować tekst - legacy path lub brak zmiennych
            # Jeśli parsed zawiera klucz 'original_text', użyj go do parsowania
            original_text = parsed.get('original_text')
            if not original_text:
                # Fallback: spróbuj zrekonstruować original_text z parsed data
                # To będzie działać dla przypadków gdzie legacy parser zadziałał
                station = parsed.get('station', parsed.get('station_id', ''))
                inverter_num = parsed.get('inverter', '').replace('I', '').lstrip('0')
                
                # Sprawdź czy mamy wszystkie potrzebne części do rekonstrukcji
                if station and inverter_num:
                    # Spróbuj różnych formatów
                    possible_formats = [
                        f"{station}/F{inverter_num.zfill(2)}/STR{parsed.get('substring', '').replace('S', '').replace('STR', '')}",
                        f"{station}/F{inverter_num}/STR{parsed.get('substring', '').replace('S', '').replace('STR', '')}",
                    ]
                    
                    for possible_text in possible_formats:
                        if possible_text.count('/') >= 2:  # Minimum format check
                            original_text = possible_text
                            break
            
            if not original_text:
                logger.warning(f"Nie można ustalić original_text z parsed: {parsed}")
                return get_legacy_formatted_id(parsed)
            
            logger.debug(f"DEBUG: original_text = {original_text}")
            logger.debug(f"DEBUG: input_format = {input_format}")
            
            # Użyj zaawansowanego formatera do parsowania
            formatter = AdvancedFormatter()
            variables = formatter.parse_input_format(original_text, input_format)
            
            if not variables:
                logger.warning(f"Zaawansowany formatter nie może sparsować '{original_text}' z formatem '{input_format}'")
                return get_legacy_formatted_id(parsed)
            
            logger.debug(f"DEBUG: formatter variables = {variables}")
        
        # Ustaw zmienne w formaterze
        formatter = AdvancedFormatter()
        formatter.variables = variables
        
        # Wygeneruj output używając format-specific output_format
        result = formatter.format_output(output_format)
        logger.debug(f"DEBUG: final SVG ID result = {result} (from output_format: {output_format})")
        
        return result
        
    except Exception as e:
        logger.error(f"Błąd zaawansowanego formatowania: {e}")
        import traceback
        traceback.print_exc()
        return get_legacy_formatted_id(parsed)


def get_legacy_formatted_id(parsed: Dict) -> str:
    """Generuje SVG ID używając starego systemu (fallback)"""
    try:
        current_format = ID_FORMAT
        
        # Wyciągnij numer MPPT
        mppt = parsed['mppt'].replace("MPPT", "").zfill(2)
        
        # Wyciągnij numer stringa
        sub = re.sub(r'[^0-9]', '', parsed['substring'])
        
        # Wyciągnij numer falownika (usuń prefiks I)
        inverter = parsed['inverter'].replace("I", "").zfill(2)
        
        if current_format == "01-02/03":
            return f"{mppt}-{sub.zfill(2)}/{inverter}"
        elif current_format == "05-06/07":
            station_num = STATION_NUMBER.zfill(2)
            return f"{station_num}-{mppt}/{inverter}"
        else:
            return f"{mppt}-{sub}/{inverter}"
            
    except Exception as e:
        logger.error(f"Błąd legacy formatowania: {e}")
        return f"error-{parsed.get('substring', 'unknown')}"
