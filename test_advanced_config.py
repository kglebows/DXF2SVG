#!/usr/bin/env python3
"""
Test script to manually set advanced formatting config
"""

from src.config.config_manager import ConfigManager
import src.core.config as config

def test_advanced_formatting():
    # Załaduj konfigurację
    cm = ConfigManager()
    cm.load_config('configs/ziec.cfg')
    
    # Włącz zaawansowane formatowanie
    cm.config_data['USE_ADVANCED_FORMATTING'] = True
    cm.config_data['ADVANCED_INPUT_FORMAT'] = '{name}/F{inv:02d}/STR{str}'
    cm.config_data['ADVANCED_OUTPUT_FORMAT'] = 'S{mppt:02d}-{str:02d}/{inv:02d}'
    cm.config_data['ADVANCED_ADDITIONAL_VARS'] = {'mppt': '{str}/2 + {str}%2'}
    
    print("=== PRZED ZASTOSOWANIEM ===")
    print(f'config.USE_ADVANCED_FORMATTING: {config.USE_ADVANCED_FORMATTING}')
    
    # Zastosuj konfigurację do config.py
    cm.apply_to_config_module()
    
    print("\n=== PO ZASTOSOWANIU ===")
    print(f'config.USE_ADVANCED_FORMATTING: {config.USE_ADVANCED_FORMATTING}')
    print(f'config.ADVANCED_INPUT_FORMAT: {getattr(config, "ADVANCED_INPUT_FORMAT", "NOT SET")}')
    print(f'config.ADVANCED_OUTPUT_FORMAT: {getattr(config, "ADVANCED_OUTPUT_FORMAT", "NOT SET")}')
    print(f'config.ADVANCED_ADDITIONAL_VARS: {getattr(config, "ADVANCED_ADDITIONAL_VARS", "NOT SET")}')
    
    # Test get_svg_id
    print("\n=== TEST GET_SVG_ID ===")
    test_parsed = {'original_text': 'STM2/F06/STR19'}
    result = config.get_svg_id(test_parsed)
    print(f'get_svg_id({{original_text: "STM2/F06/STR19"}}): {result}')
    
    # Test z różnymi formatami
    test_cases = [
        'STM2/F06/STR19',
        'STM2/F01/STR1', 
        'STM2/F12/STR35'
    ]
    
    for test_text in test_cases:
        test_parsed = {'original_text': test_text}
        result = config.get_svg_id(test_parsed)
        print(f'"{test_text}" -> "{result}"')

if __name__ == "__main__":
    test_advanced_formatting()
