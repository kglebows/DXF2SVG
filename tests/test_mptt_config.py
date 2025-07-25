#!/usr/bin/env python3
"""
Test konfiguracji MPTT_HEIGHT - sprawdzenie czy parametr jest obsługiwany w GUI
"""

import sys
sys.path.append('.')

from src.config.config_manager import ConfigManager

def test_mptt_height_config():
    """Test obsługi MPTT_HEIGHT w konfiguracji"""
    print("=== Test konfiguracji MPTT_HEIGHT ===\n")
    
    # Test 1: Domyślna wartość
    config_manager = ConfigManager()
    default_value = config_manager.get('MPTT_HEIGHT', 'BRAK')
    print(f"1. Domyślna wartość MPTT_HEIGHT: {default_value}")
    
    # Test 2: Ustawienie nowej wartości
    config_manager.set('MPTT_HEIGHT', 2.5)
    new_value = config_manager.get('MPTT_HEIGHT')
    print(f"2. Po ustawieniu 2.5: {new_value}")
    
    # Test 3: Zapis i wczytanie z pliku
    print(f"3. Zapisywanie do pliku testowej konfiguracji...")
    if config_manager.save_config('test_mptt'):
        print("   ✅ Zapisano pomyślnie")
        
        # Nowy manager do testu wczytywania
        new_manager = ConfigManager()
        if new_manager.load_config('test_mptt'):
            loaded_value = new_manager.get('MPTT_HEIGHT')
            print(f"   ✅ Wczytano z pliku: {loaded_value}")
            
            if loaded_value == 2.5:
                print("   ✅ Wartości się zgadzają")
            else:
                print(f"   ❌ Błąd: oczekiwano 2.5, otrzymano {loaded_value}")
        else:
            print("   ❌ Nie można wczytać konfiguracji")
    else:
        print("   ❌ Nie można zapisać konfiguracji")
    
    # Test 4: Zastosowanie do modułu config
    import src.core.config as config
    old_value = getattr(config, 'MPTT_HEIGHT', 'BRAK')
    print(f"4. Wartość w config.py przed zastosowaniem: {old_value}")
    
    config_manager.apply_to_config_module()
    new_config_value = getattr(config, 'MPTT_HEIGHT', 'BRAK')
    print(f"   Po zastosowaniu: {new_config_value}")
    
    if new_config_value == 2.5:
        print("   ✅ Pomyślnie zastosowano do modułu config")
    else:
        print(f"   ❌ Błąd zastosowania: oczekiwano 2.5, otrzymano {new_config_value}")
    
    print("\n=== Koniec testu ===")

if __name__ == "__main__":
    test_mptt_height_config()
