#!/usr/bin/env python3
"""
Test końcowy - porównanie SVG z różnymi wartościami MPTT_HEIGHT
"""

import sys
sys.path.append('.')

from src.config.config_manager import ConfigManager
import src.core.config as config
from src.svg.svg_generator import generate_structured_svg

def create_comparison_svgs():
    """Utwórz porównawcze SVG z różnymi wartościami MPTT_HEIGHT"""
    print("=== Test porównawczy różnych wartości MPTT_HEIGHT ===\n")
    
    # Przykładowe dane testowe
    test_data = {
        'I01': {
            'S01': [
                {'start': (100, 100), 'end': (200, 100), 'polyline_idx': 0},
                {'start': (200, 100), 'end': (300, 100), 'polyline_idx': 0}
            ]
        }
    }
    
    test_texts = [
        {'id': 'S01', 'pos': (150, 80), 'station': 'TEST'}
    ]
    
    # Test różnych wartości
    test_values = [(1, 'default'), (2, 'medium'), (4, 'thick'), (8, 'very_thick')]
    
    config_manager = ConfigManager()
    
    for value, name in test_values:
        print(f"🔧 Test MPTT_HEIGHT = {value} ({name})")
        
        # Ustaw wartość
        config_manager.set('MPTT_HEIGHT', value)
        config_manager.apply_to_config_module()
        
        # Sprawdź czy została zastosowana
        actual_value = config.MPTT_HEIGHT
        print(f"   config.MPTT_HEIGHT = {actual_value}")
        
        # Wygeneruj SVG
        output_file = f'test_mptt_{name}_{value}.svg'
        try:
            generate_structured_svg(
                test_data,
                test_texts,
                [],  # unassigned_texts
                [],  # unassigned_segments
                output_file,
                'TEST'
            )
            print(f"   ✅ Utworzono {output_file}")
        except Exception as e:
            print(f"   ❌ Błąd: {e}")
    
    print(f"\n📊 Porównaj pliki:")
    for value, name in test_values:
        print(f"   - test_mptt_{name}_{value}.svg (grubość linii: {value})")
    
    print(f"\n💡 Jeśli widzisz różnice w grubości linii między plikami,")
    print(f"   to MPTT_HEIGHT działa poprawnie!")

if __name__ == "__main__":
    create_comparison_svgs()
