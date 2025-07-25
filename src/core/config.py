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
    }
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
Y_TOLERANCE = 0.01
X_TOLERANCE = 0.01
SEARCH_RADIUS = 6.0 
TEXT_LOCATION = "above"     # "above", "below", "any"

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
        
        logger.debug(f"Sparsowane dane ({format_name}): {result}")
        return result
        
    except Exception as e:
        logger.debug(f"Błąd parsowania formatu {format_name}: {e}")
        return None

def get_svg_id(parsed: Dict) -> str:
    """Generuje SVG ID z sparsowanych danych zgodnie z aktualnym formatem ID"""
    try:
        # Pobierz aktualny format ID z konfiguracji
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
