#!/usr/bin/env python3
"""
Test zaawansowanego formatowania dla testPrime.cfg
"""

from src.config.config_manager import ConfigManager
import src.core.config as config

def test_testprime_advanced_formatting():
    print("=== TEST ZAAWANSOWANEGO FORMATOWANIA testPrime.cfg ===")
    
    # Załaduj konfigurację
    cm = ConfigManager()
    result = cm.load_config('testPrime')
    print(f"load_config('testPrime'): {result}")
    
    if not result:
        print("❌ Nie udało się załadować konfiguracji testPrime.cfg")
        return
    
    # Sprawdź co zostało załadowane
    print(f"\n=== CONFIG_DATA ===")
    for key, value in cm.config_data.items():
        if 'ADVANCED' in key or 'FORMAT' in key:
            print(f"{key}: {value} (type: {type(value)})")
    
    # Zastosuj do config.py
    cm.apply_to_config_module()
    
    print(f"\n=== CONFIG.PY PO ZASTOSOWANIU ===")
    print(f"USE_ADVANCED_FORMATTING: {getattr(config, 'USE_ADVANCED_FORMATTING', 'NOT SET')}")
    print(f"ADVANCED_INPUT_FORMAT: {getattr(config, 'ADVANCED_INPUT_FORMAT', 'NOT SET')}")
    print(f"ADVANCED_OUTPUT_FORMAT: {getattr(config, 'ADVANCED_OUTPUT_FORMAT', 'NOT SET')}")
    print(f"ADVANCED_ADDITIONAL_VARS: {getattr(config, 'ADVANCED_ADDITIONAL_VARS', 'NOT SET')}")
    
    # Test parsowania tekstu
    test_text = "1-1-1"
    print(f"\n=== TEST PARSOWANIA ===")
    print(f"Tekst testowy: '{test_text}'")
    
    if getattr(config, 'USE_ADVANCED_FORMATTING', False):
        print("Używam zaawansowanego formatowania...")
        from src.core.advanced_formatter import AdvancedFormatter
        
        formatter = AdvancedFormatter()
        input_format = getattr(config, 'ADVANCED_INPUT_FORMAT', '')
        output_format = getattr(config, 'ADVANCED_OUTPUT_FORMAT', '')
        
        print(f"Input format: '{input_format}'")
        print(f"Output format: '{output_format}'")
        
        variables = formatter.parse_input_format(test_text, input_format)
        print(f"Parsed variables: {variables}")
        
        if variables:
            formatter.variables = variables
            result = formatter.format_output(output_format)
            print(f"Formatted output: '{result}'")
        else:
            print("❌ Nie udało się sparsować tekstu!")
    else:
        print("❌ Zaawansowane formatowanie jest wyłączone!")
        
        # Sprawdź czy legacy parser rozpoznaje tekst
        parsed = config.parse_text_to_dict(test_text)
        print(f"Legacy parsed: {parsed}")

if __name__ == "__main__":
    test_testprime_advanced_formatting()
