#!/usr/bin/env python3
"""
Test skrypt sprawdzający obsługę różnych formatów tekstów
"""

from src.core.config import parse_text_to_dict, get_svg_id, STATION_ID

def test_formats():
    """Test różnych formatów tekstów"""
    print("=== TEST OBSŁUGI RÓŻNYCH FORMATÓW TEKSTÓW ===")
    print(f"Aktualne STATION_ID: {STATION_ID}")
    print()
    
    test_cases = [
        # Format 1: STACJA/FALOWNIK/MPPT/STRING
        "ZIEB/F01/MPPT1/S01",
        "ZIEB/F02/MPPT3/S05",
        
        # Format 4: INV01-02 (nowy format)
        "INV01-02",
        "INV03-05", 
        "INV10-12",
        
        # Format 2: STACJA/ST/FALOWNIK/MPPT/STRING (gdyby był)
        "WIE4/ST01/F04/MPPT03/S09",
        
        # Niepoprawne formaty
        "BŁĘDNY_FORMAT",
        "123-456",
    ]
    
    print(f"{'Tekst wejściowy':<20} {'Format':<10} {'Station':<8} {'Inverter':<8} {'MPPT':<8} {'String':<8} {'SVG ID':<10}")
    print("=" * 80)
    
    for text in test_cases:
        result = parse_text_to_dict(text, STATION_ID)
        if result:
            svg_id = get_svg_id(result)
            # Określ format na podstawie wzorca
            format_type = "?"
            if "/" in text and "F" in text:
                if "/ST" in text:
                    format_type = "format_2"
                else:
                    format_type = "format_1"
            elif text.startswith("INV"):
                format_type = "format_4"
            
            print(f"{text:<20} {format_type:<10} {result['station']:<8} {result['inverter']:<8} {result['mppt']:<8} {result['substring']:<8} {svg_id:<10}")
        else:
            print(f"{text:<20} {'BŁĄD':<10} {'---':<8} {'---':<8} {'---':<8} {'---':<8} {'---':<10}")

if __name__ == "__main__":
    test_formats()
