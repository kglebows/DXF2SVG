from src.config.config_manager import ConfigManager
import src.core.config as config

# Test z mniejszym search_radius żeby zobaczyć czy to problem  
cm = ConfigManager()
cm.load_config('testPrime')

# Zmień search_radius na mniejszy na test
print('=== TEST Z RÓŻNYMI SEARCH_RADIUS ===')

# Domyślne 120.0 nie działa, spróbujmy różne wartości
test_values = [120.0, 200.0, 300.0, 500.0]

for radius in test_values:
    print(f'\nTest z search_radius = {radius}')
    
    # Ustaw nową wartość
    cm.config_data['SEARCH_RADIUS'] = radius
    cm.apply_to_config_module()
    
    print(f'  SEARCH_RADIUS w config: {config.SEARCH_RADIUS}')
    
    # Sprawdź kilka innych parametrów
    print(f'  Y_TOLERANCE: {config.Y_TOLERANCE}')
    print(f'  TEXT_LOCATION: {config.TEXT_LOCATION}')
    print(f'  POLYLINE_PROCESSING_MODE: {config.POLYLINE_PROCESSING_MODE}')

print(f'\n=== ANALIZA PARAMETRÓW ===')
print('Możliwe przyczyny braku przypisań:')
print('1. search_radius za mały dla rozmiarów DXF')
print('2. TEXT_LOCATION nie pasuje do rzeczywistego położenia tekstów') 
print('3. Problem z algorytmem automatycznego przypisywania po segmentacji')
print('4. Teksty i segmenty są w różnych skalach/jednostkach')

print(f'\nAktualnie:')
print(f'- 172 tekstów znalezionych i sparsowanych')
print(f'- 126 stringów po segmentacji (z ~3000 oryginalnych segmentów)')
print(f'- 0 automatycznych przypisań z search_radius=120')
print(f'- TEXT_LOCATION={config.TEXT_LOCATION} (any powinna łapać wszystkie)')
