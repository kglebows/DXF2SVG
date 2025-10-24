"""
Test filtrowania tekstów według station_id dla projektu lesniewice
"""
import sys
sys.path.insert(0, 'c:\\Users\\konra\\VSC\\DXF2SVG')

from src.config.config_manager import ConfigManager
from src.core.dxf2svg import process_dxf
from src.utils.console_logger import console

def test_lesniewice():
    """Test z plikiem lesniewice.dxf i lesniewice.cfg"""
    
    print("\n=== TEST FILTROWANIA TEKSTOW DLA LESNIEWICE ===\n")
    
    # Załaduj konfigurację
    config_name = "lesniewice"  # Bez .cfg i ścieżki
    dxf_path = "lesniewice.dxf"
    
    print(f"Ladowanie konfiguracji: {config_name}")
    config_manager = ConfigManager()
    config_manager.load_config(config_name)
    
    # Pobierz parametry jak w GUI
    config_params = {
        'LAYER_TEXT': config_manager.get('LAYER_TEXT', '@IDE_KABLE_DC_TXT_B'),
        'LAYER_LINE': config_manager.get('LAYER_LINE', '@IDE_KABLE_DC_B'),
        'STATION_ID': config_manager.get('STATION_ID', 'ZIEB'),
        'Y_TOLERANCE': float(config_manager.get('Y_TOLERANCE', 0.01)),
        'SEGMENT_MIN_WIDTH': float(config_manager.get('SEGMENT_MIN_WIDTH', 0)),
        'SEARCH_RADIUS': float(config_manager.get('SEARCH_RADIUS', 6.0)),
        'TEXT_LOCATION': config_manager.get('TEXT_LOCATION', 'above'),
        'POLYLINE_PROCESSING_MODE': config_manager.get('POLYLINE_PROCESSING_MODE', 'individual_segments'),
        'SEGMENT_MERGE_GAP_TOLERANCE': float(config_manager.get('SEGMENT_MERGE_GAP_TOLERANCE', 1.0)),
        'MAX_MERGE_DISTANCE': float(config_manager.get('MAX_MERGE_DISTANCE', 5.0)),
        'USE_ADVANCED_FORMATTING': config_manager.get('USE_ADVANCED_FORMATTING', False),
        'ADVANCED_INPUT_FORMAT': config_manager.get('ADVANCED_INPUT_FORMAT', ''),
        'ADVANCED_OUTPUT_FORMAT': config_manager.get('ADVANCED_OUTPUT_FORMAT', ''),
    }
    
    print(f"Station ID z konfiguracji: {config_params['STATION_ID']}")
    print(f"Use Advanced Formatting: {config_params.get('USE_ADVANCED_FORMATTING', False)}")
    print(f"Advanced Input Format: {config_params.get('ADVANCED_INPUT_FORMAT', 'N/A')}")
    
    # Sprawdź globalne zmienne
    import src.core.config as cfg
    print(f"\nGlobalne zmienne w src.core.config:")
    print(f"  cfg.USE_ADVANCED_FORMATTING = {cfg.USE_ADVANCED_FORMATTING}")
    print(f"  cfg.ADVANCED_INPUT_FORMAT = {getattr(cfg, 'ADVANCED_INPUT_FORMAT', 'BRAK')}")
    print(f"  cfg.STATION_ID = {cfg.STATION_ID}")
    
    # Przetwórz DXF
    print(f"\nPrzetwarzam plik: {dxf_path}")
    
    try:
        # Bezpośrednia ekstrakcja bez console_logger
        import ezdxf
        from src.core.config import parse_text_to_dict
        
        doc = ezdxf.readfile(dxf_path)
        
        # Ekstraktuj teksty
        from src.core.dxf2svg import extract_texts_from_dxf
        all_texts = extract_texts_from_dxf(doc, config_params['LAYER_TEXT'])
        print(f"Wszystkich tekstow w DXF: {len(all_texts)}")
        
        # Przykładowe teksty
        print(f"\nPrzykladowe teksty z DXF:")
        for i, text in enumerate(all_texts[:3]):
            print(f"  {i+1}. {text['id']}")
        
        # Test parsowania pojedynczego tekstu
        if all_texts:
            test_text = all_texts[0]['id']
            print(f"\nTest parsowania tekstu: '{test_text}'")
            parsed = parse_text_to_dict(test_text, config_params['STATION_ID'])
            print(f"Wynik parsowania: {parsed}")
        
        # Parsuj teksty i filtruj po station_id
        station_texts = []
        use_advanced_formatting = config_params.get('USE_ADVANCED_FORMATTING', False)
        
        for text in all_texts:
            parsed = parse_text_to_dict(text['id'], config_params['STATION_ID'])
            if parsed:
                if use_advanced_formatting:
                    # Filtruj po 'name' ze zmiennych zaawansowanego formatowania
                    if parsed.get('variables', {}).get('name') == config_params['STATION_ID']:
                        text.update(parsed)
                        station_texts.append(text)
                else:
                    # W legacy formatowaniu filtrujemy po station
                    if parsed.get('station') == config_params['STATION_ID']:
                        text.update(parsed)
                        station_texts.append(text)
        
        print("\n=== WYNIKI ===")
        print(f"Tekstow dla stacji {config_params['STATION_ID']}: {len(station_texts)}")
        
        if station_texts:
            print(f"\nPrzyklad sparsowanego tekstu: {station_texts[0]}")
            print(f"\nPierwsze 5 tekstow:")
            for i, text in enumerate(station_texts[:5]):
                print(f"  {i+1}. {text['id']} -> variables: {text.get('variables', {})}")
        
        # Sprawdź wszystkie stacje
        print("\n=== SPRAWDZENIE WSZYSTKICH STACJI ===")
        
        stations_found = {}
        for text in all_texts:
            parsed = parse_text_to_dict(text['id'], config_params['STATION_ID'])
            if parsed and 'variables' in parsed:
                name = parsed['variables'].get('name')
                if name:
                    if name not in stations_found:
                        stations_found[name] = []
                    stations_found[name].append(text['id'])
        
        print(f"Znalezione stacje: {sorted(stations_found.keys())}")
        
        # Policz teksty dla każdej stacji
        for station in sorted(stations_found.keys()):
            count = len(stations_found[station])
            print(f"  {station}: {count} tekstow (przyklad: {stations_found[station][0] if stations_found[station] else 'brak'})")
        
    except FileNotFoundError:
        print(f"BLAD: Plik {dxf_path} nie istnieje!")
        print(f"\nUpewnij sie ze plik lesniewice.dxf znajduje sie w glownym katalogu projektu.")
    except Exception as e:
        print(f"BLAD: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lesniewice()
