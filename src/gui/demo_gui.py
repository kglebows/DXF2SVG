#!/usr/bin/env python3
"""
Demo i test dla interaktywnego GUI
"""

import os
import sys

def demo_gui():
    """Demonstracja możliwości GUI"""
    print("=== DXF2SVG Interactive GUI - Demo ===\n")
    
    # Sprawdź czy pliki istnieją
    files_check = [
        ("interactive_gui.py", "Główny plik GUI"),
        ("run_interactive_gui.py", "Launcher GUI"),
        ("input.dxf", "Przykładowy plik DXF"),
        ("output_structured.svg", "Wygenerowany SVG"),
        ("dxf2svg.py", "Silnik konwersji")
    ]
    
    print("Sprawdzanie plików:")
    for filename, description in files_check:
        exists = "✅" if os.path.exists(filename) else "❌"
        print(f"{exists} {filename:<25} - {description}")
    
    print("\n=== Funkcje GUI ===")
    features = [
        "📁 Wybór pliku DXF przez dialog",
        "⚙️  Konwersja DXF → SVG w tle",
        "🖼️  Podgląd SVG z zoomem i panoramowaniem", 
        "🔄 Auto-odświeżanie po konwersji",
        "📊 Panel statusu i logów",
        "🎛️  Kontrola opcji renderowania",
        "📏 Informacje o pliku i zoomie",
        "🖱️  Intuicyjna obsługa myszą"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n=== Instrukcja uruchomienia ===")
    print("1. python interactive_gui.py")
    print("2. Wybierz plik DXF przyciskiem 'Wybierz'")
    print("3. Kliknij 'Konwertuj DXF → SVG'")
    print("4. Podgląd SVG pojawi się automatycznie")
    print("5. Użyj kółka myszy do zoomowania")
    print("6. Przeciągnij myszą aby przesunąć widok")
    
    print("\n=== Kontrola podglądu ===")
    controls = [
        "Kółko myszy ↕️  - Zoom in/out",
        "Przeciąganie 🖱️ - Panoramowanie", 
        "Przycisk 'Reset' - Przywrócenie domyślnego widoku",
        "Przycisk 'Dopasuj' - Automatyczne skalowanie",
        "Przycisk 'Odśwież' - Ponowne załadowanie SVG"
    ]
    
    for control in controls:
        print(f"  • {control}")
    
    print(f"\n=== Status systemu ===")
    print(f"📂 Katalog roboczy: {os.getcwd()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"💻 System: {os.name}")
    
    # Sprawdź importy
    print(f"\n=== Sprawdzanie zależności ===")
    dependencies = [
        ("tkinter", "GUI framework"),
        ("PIL", "Pillow - obsługa obrazów"), 
        ("xml.etree.ElementTree", "Parsowanie XML/SVG"),
        ("threading", "Wielowątkowość"),
        ("ezdxf", "Parsowanie DXF"),
        ("svgwrite", "Generowanie SVG")
    ]
    
    for module, desc in dependencies:
        try:
            __import__(module)
            print(f"✅ {module:<20} - {desc}")
        except ImportError:
            print(f"❌ {module:<20} - {desc} (BRAK!)")
    
    print(f"\n{'='*50}")
    print("GUI gotowe do uruchomienia!")
    print("Użyj: python interactive_gui.py")
    print(f"{'='*50}")

if __name__ == "__main__":
    demo_gui()
