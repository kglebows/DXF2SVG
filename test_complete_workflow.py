from src.config.config_manager import ConfigManager
import src.core.config as config

# Załaduj konfigurację testPrime
cm = ConfigManager()
cm.load_config('testPrime')
cm.apply_to_config_module()

print('=== TEST KOMPLETNEGO WORKFLOW Z CUSTOM FORMAT ===')
print(f'Config załadowany: USE_ADVANCED_FORMATTING: {config.USE_ADVANCED_FORMATTING}')
print(f'Format wejściowy: {config.ADVANCED_INPUT_FORMAT}')
print(f'Format wyjściowy: {config.ADVANCED_OUTPUT_FORMAT}')

# Test różnych tekstów
test_texts = ['1-1-1', '2-3-4', '10-19-6']

for test_text in test_texts:
    print(f'\n--- Test tekstu: "{test_text}" ---')
    
    # Parsowanie
    result = config.parse_text_to_dict(test_text)
    print(f'Wynik parsowania: {result}')
    
    if result:
        # Sprawdź zmienne
        variables = result.get('variables', {})
        print(f'Zmienne: {variables}')
        
        # SVG ID
        svg_id = config.get_svg_id(result)
        print(f'SVG ID: {svg_id}')
        
        # Advanced formatted ID  
        formatted_id = config.get_advanced_formatted_id(result)
        print(f'Advanced formatted ID: {formatted_id}')
        
        # Check if it matches expected format
        if 'st' in variables and 'inv' in variables and 'mppt' in variables:
            st = variables['st']
            inv = variables['inv'] 
            mppt = variables['mppt']
            expected = f'S{st:02d}-{inv:02d}/{mppt:02d}'
            print(f'Expected format: {expected}')
            print(f'Match: {formatted_id == expected}')
    else:
        print('Tekst nie został rozpoznany')
