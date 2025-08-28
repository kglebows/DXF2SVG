from src.config.config_manager import ConfigManager
import src.core.config as config

# Załaduj konfigurację testPrime
cm = ConfigManager()
cm.load_config('testPrime')
cm.apply_to_config_module()

print('=== TEST PARSOWANIA PO POPRAWCE ===')
print(f'USE_ADVANCED_FORMATTING: {config.USE_ADVANCED_FORMATTING}')
print(f'ADVANCED_INPUT_FORMAT: {config.ADVANCED_INPUT_FORMAT}')

# Test parsowania tekstu
test_text = '1-1-1'
print(f'\nTestujemy text: "{test_text}"')

result = config.parse_text_to_dict(test_text)
print(f'parse_text_to_dict result: {result}')

if result:
    svg_id = config.get_svg_id(result)
    print(f'get_svg_id: {svg_id}')
    
    formatted_id = config.get_advanced_formatted_id(result)
    print(f'get_advanced_formatted_id: {formatted_id}')
else:
    print('Parsowanie zwróciło None - format nie został rozpoznany')
