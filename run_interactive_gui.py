#!/usr/bin/env python3
"""
Główny plik startowy dla DXF2SVG Interactive GUI
"""
import sys
import os

def main():
    """Główna funkcja startowa"""
    print("Uruchamianie DXF2SVG Interactive GUI...")
    
    # Sprawdź argumenty wiersza poleceń
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("\nDXF2SVG Interactive GUI")
        print("Użycie:")
        print("  python run_interactive_gui.py                    # Domyślna konfiguracja")
        print("  python run_interactive_gui.py --config zieb      # Załaduj konfigurację zieb.cfg")
        print("  python run_interactive_gui.py -c nazwa_obiektu   # Załaduj konfigurację nazwa_obiektu.cfg")
        print("\nDostępne opcje:")
        print("  -h, --help                 Wyświetl tę pomoc")
        print("  -c, --config NAZWA         Załaduj plik konfiguracyjny configs/NAZWA.cfg")
        return
    
    # Sprawdź wymagane biblioteki
    missing_packages = []
    try:
        import ezdxf
    except ImportError:
        missing_packages.append('ezdxf')
    
    try:
        import tkinter
    except ImportError:
        missing_packages.append('tkinter')
    
    try:
        from PIL import Image
    except ImportError:
        missing_packages.append('Pillow')
    
    if missing_packages:
        print("\n❌ BŁĄD: Brakujące wymagane biblioteki!")
        print(f"   Nie znaleziono: {', '.join(missing_packages)}")
        print("\n📦 Aby zainstalować wymagane biblioteki, uruchom:")
        print("   pip install -r requirements.txt")
        print("\nLub zainstaluj ręcznie:")
        for pkg in missing_packages:
            if pkg == 'tkinter':
                print(f"   - {pkg}: zainstaluj Python z obsługą Tkinter (domyślnie w oficjalnej dystrybucji)")
            else:
                print(f"   - pip install {pkg}")
        sys.exit(1)
    
    try:
        from src.gui.interactive_gui_new import InteractiveGUI
        import argparse
        
        # Obsługa argumentów
        parser = argparse.ArgumentParser(description='DXF2SVG Interactive GUI')
        parser.add_argument('--config', '-c', type=str, help='Nazwa pliku konfiguracyjnego (bez rozszerzenia .cfg)')
        args = parser.parse_args()
        
        # Uruchom aplikację
        app = InteractiveGUI(config_file=args.config)
        app.run()
        
    except KeyboardInterrupt:
        print("\n⚠️ Przerwano przez użytkownika")
    except Exception as e:
        print(f"❌ Błąd uruchamiania: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
