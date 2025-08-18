#!/usr/bin/env python3
"""
Debug parse_input_format specifically
"""

from src.core.advanced_formatter import AdvancedFormatter

def debug_parse_input_format():
    formatter = AdvancedFormatter()
    
    test_text = 'STM2/F06/STR19'
    
    # Test różnych formatów input
    test_formats = [
        '{name}/F{inv:02d}/STR{str}',
        '{name}/F{inv:2}/STR{str}',
        '{name}/F{inv}/STR{str}',
        '{name}/F{inv:d}/STR{str}',
        r'{name}/F(\d+)/STR{str}',
    ]
    
    print(f"Testing text: '{test_text}'")
    print("=" * 50)
    
    for fmt in test_formats:
        print(f"\nFormat: '{fmt}'")
        try:
            result = formatter.parse_input_format(test_text, fmt)
            print(f"Result: {result}")
            
            # Także sprawdźmy wygenerowany regex
            pattern = formatter._generate_regex_pattern(fmt)
            print(f"Generated regex: {pattern}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_parse_input_format()
