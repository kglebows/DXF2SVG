#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher dla Interactive GUI z poprawnym kodowaniem"""

import os
import sys

# Ustaw kodowanie
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Zmień katalog na katalog skryptu
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Dodaj ścieżkę do sys.path
sys.path.insert(0, script_dir)

try:
    print("🚀 Uruchamianie DXF2SVG Interactive GUI...")
    print(f"📁 Katalog roboczy: {os.getcwd()}")
    
    # Import i uruchomienie nowej wersji GUI
    from src.gui.interactive_gui_new import InteractiveGUI
    
    app = InteractiveGUI()
    print("✅ GUI zainicjalizowany, uruchamianie...")
    app.run()
    
except KeyboardInterrupt:
    print("\n⚠️ Przerwano przez użytkownika")
except Exception as e:
    print(f"❌ Błąd uruchomienia GUI: {e}")
    import traceback
    traceback.print_exc()
    input("Naciśnij Enter aby zamknąć...")
