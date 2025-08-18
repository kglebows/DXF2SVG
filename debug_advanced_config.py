#!/usr/bin/env python3
"""
Debug script to test advanced formatting step by step
"""

from src.config.config_manager import ConfigManager
import src.core.config as config
from src.core.advanced_formatter import AdvancedFormatter

def debug_advanced_formatting():
    # Załaduj konfigurację
    cm = ConfigManager()
    cm.load_config('configs/ziec.cfg')
    
    # Włącz zaawansowane formatowanie
    cm.config_data['USE_ADVANCED_FORMATTING'] = True
    cm.config_data['ADVANCED_INPUT_FORMAT'] = '{name}/F{inv:02d}/STR{str}'
    cm.config_data['ADVANCED_OUTPUT_FORMAT'] = 'S{mppt:02d}-{str:02d}/{inv:02d}'
    cm.config_data['ADVANCED_ADDITIONAL_VARS'] = {'mppt': '{str}/2 + {str}%2'}
    
    # Zastosuj konfigurację do config.py
    cm.apply_to_config_module()
    
    print("=== CONFIG LOADED ===")
    print(f'USE_ADVANCED_FORMATTING: {config.USE_ADVANCED_FORMATTING}')
    print(f'INPUT_FORMAT: {getattr(config, "ADVANCED_INPUT_FORMAT", "NOT SET")}')
    print(f'OUTPUT_FORMAT: {getattr(config, "ADVANCED_OUTPUT_FORMAT", "NOT SET")}')
    
    # Test direct formatter
    print("\n=== DIRECT FORMATTER TEST ===")
    formatter = AdvancedFormatter()
    test_text = 'STM2/F06/STR19'
    input_format = '{name}/F{inv:02d}/STR{str}'
    output_format = 'S{mppt:02d}-{str:02d}/{inv:02d}'
    
    variables = formatter.parse_input_format(test_text, input_format)
    print(f'parse_input_format("{test_text}", "{input_format}") = {variables}')
    
    if variables:
        formatter.variables = variables
        formatter.set_additional_variable('mppt', '{str}/2 + {str}%2')
        result = formatter.format_output(output_format)
        print(f'format_output("{output_format}") = {result}')
    
    # Test config functions in isolation
    print("\n=== CONFIG FUNCTIONS TEST ===")
    
    print("Testing get_advanced_formatted_id directly...")
    test_parsed = {'original_text': 'STM2/F06/STR19'}
    
    try:
        result = config.get_advanced_formatted_id(test_parsed)
        print(f'get_advanced_formatted_id({test_parsed}) = {result}')
    except Exception as e:
        print(f'ERROR in get_advanced_formatted_id: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_advanced_formatting()
