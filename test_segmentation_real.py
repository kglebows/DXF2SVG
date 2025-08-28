from src.config.config_manager import ConfigManager
import src.core.config as config
from src.core.dxf2svg import process_dxf

# Załaduj konfigurację testPrime
cm = ConfigManager()
cm.load_config('testPrime')
cm.apply_to_config_module()

print('=== TEST SEGMENTACJI W PRAKTYCE ===')

# Przygotuj parametry jak w GUI
config_params = {
    'LAYER_TEXT': config.LAYER_TEXT,
    'LAYER_LINE': config.LAYER_LINE,
    'STATION_ID': config.STATION_ID,
    'Y_TOLERANCE': config.Y_TOLERANCE,
    'SEGMENT_MIN_WIDTH': config.SEGMENT_MIN_WIDTH,
    'SEARCH_RADIUS': config.SEARCH_RADIUS,
    'TEXT_LOCATION': config.TEXT_LOCATION,
    'POLYLINE_PROCESSING_MODE': config.POLYLINE_PROCESSING_MODE,
    'SEGMENT_MERGE_GAP_TOLERANCE': config.SEGMENT_MERGE_GAP_TOLERANCE,
    'MAX_MERGE_DISTANCE': config.MAX_MERGE_DISTANCE
}

print(f'Tryb segmentacji: {config_params["POLYLINE_PROCESSING_MODE"]}')
print(f'Gap tolerance: {config_params["SEGMENT_MERGE_GAP_TOLERANCE"]}')
print(f'Max merge distance: {config_params["MAX_MERGE_DISTANCE"]}')

try:
    # Uruchom proces konwersji
    dxf_file = cm.get('DEFAULT_DXF_FILE', 'testPrime.dxf')
    print(f'Przetwarzam plik: {dxf_file}')
    
    assigned_data, station_texts, unassigned_texts, unassigned_segments, unassigned_polylines = process_dxf(dxf_file, config_params)
    
    print(f'\n=== WYNIKI ===')
    print(f'Tekstów stacji: {len(station_texts)}')
    print(f'Nieprzypisanych tekstów: {len(unassigned_texts)}')
    print(f'Nieprzypisanych segmentów: {len(unassigned_segments)}')
    print(f'Nieprzypisanych polilinii: {len(unassigned_polylines)}')
    
    if station_texts:
        print(f'\nPrzykład sparsowanego tekstu: {station_texts[0]}')
        
except Exception as e:
    print(f'Błąd: {e}')
    import traceback
    traceback.print_exc()
