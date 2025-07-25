#!/usr/bin/env python3
"""
Debug test dla sprawdzenia ładowania konfiguracji
"""

import sys
import os
sys.path.append('.')
sys.path.append('..')

from src.config.config_manager import ConfigManager

def debug_config_loading():
    """Debug test ładowania konfiguracji"""
    print("=== DEBUG TEST ŁADOWANIA KONFIGURACJI ===")
    
    # Sprawdź czy pliki istnieją
    print("\n1. Sprawdzenie istnienia plików:")
    zieb_path = 'configs/zieb.cfg'
    ziec_path = 'configs/ziec.cfg'
    
    print(f"   {zieb_path}: {'✅' if os.path.exists(zieb_path) else '❌'}")
    print(f"   {ziec_path}: {'✅' if os.path.exists(ziec_path) else '❌'}")
    
    # Test ładowania ZIEC z debugiem
    print("\n2. Debug ładowania ZIEC:")
    config_ziec = ConfigManager()
    
    # Włącz logowanie debug
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    result = config_ziec.load_config('ziec')
    print(f"   Wynik ładowania: {result}")
    
    # Sprawdź wszystkie klucze
    print(f"   Wszystkich kluczy w config_data: {len(config_ziec.config_data)}")
    
    # Sprawdź konkretne klucze
    print("\n3. Klucze związane z warstwami:")
    relevant_keys = ['STATION_ID', 'LAYER_LINE', 'LAYER_TEXT', 'TEXT_LOCATION']
    for key in relevant_keys:
        value = config_ziec.config_data.get(key, 'NOT_FOUND')
        print(f"   {key}: {value}")
    
    # Sprawdź wszystkie klucze zawierające 'LAYER'
    print("\n4. Wszystkie klucze zawierające 'LAYER':")
    for key, value in config_ziec.config_data.items():
        if 'LAYER' in key:
            print(f"   {key}: {value}")

if __name__ == "__main__":
    debug_config_loading()
