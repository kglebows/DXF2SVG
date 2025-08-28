from src.config.config_manager import ConfigManager
import src.core.config as config

# Test ładowania konfiguracji testPrime z nowymi parametrami segmentacji
cm = ConfigManager()
cm.load_config('testPrime')
cm.apply_to_config_module()

print('=== TEST PARAMETRÓW SEGMENTACJI ===')
print(f'POLYLINE_PROCESSING_MODE: {config.POLYLINE_PROCESSING_MODE}')
print(f'SEGMENT_MERGE_GAP_TOLERANCE: {config.SEGMENT_MERGE_GAP_TOLERANCE}')
print(f'MAX_MERGE_DISTANCE: {config.MAX_MERGE_DISTANCE}')

print('\n=== TEST ZAAWANSOWANEGO FORMATOWANIA ===')
print(f'USE_ADVANCED_FORMATTING: {config.USE_ADVANCED_FORMATTING}')
print(f'ADVANCED_INPUT_FORMAT: {config.ADVANCED_INPUT_FORMAT}')

# Test parsowania
test_text = '2-1-7'
result = config.parse_text_to_dict(test_text)
print(f'\nTest parsowania "{test_text}": {result}')
