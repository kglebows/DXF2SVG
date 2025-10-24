#!/usr/bin/env python3
"""
Nowa wersja Interactive GUI z zakładkami i naprawionym przypisywaniem
Panel sterowania podzielony na zakładki dla lepszej organizacji
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import threading
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
import xml.etree.ElementTree as ET
from src.config.config_manager import ConfigManager, ConfigTab
from tkinter import font
import re

# Dodaj ścieżkę do modułów projektu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modułów projektu
try:
    from src.core.dxf2svg import main as convert_dxf_to_svg, process_dxf
    from src.core.config import *
    from src.utils.console_logger import logger
    from src.interactive.interactive_editor import get_unassigned_texts, get_unassigned_segments
    from src.gui.simple_svg_viewer import SimpleSVGViewer
    from src.gui.enhanced_svg_viewer import EnhancedSVGViewer
    from src.interactive.assignment_manager import AssignmentManager
    from src.gui.unified_config_tab import UnifiedConfigTab
except ImportError as e:
    print(f"Błąd importu: {e}")
    sys.exit(1)


class InteractiveGUI:
    """Główna klasa GUI z zakładkami"""
    
    def __init__(self, config_file=None):
        self.root = tk.Tk()
        self.root.title("DXF2SVG - Interaktywny Edytor")
        
        # Ustaw ciemny motyw dla całego okna
        self.colors = {
            'bg': '#0d0d0d',           # Warstwa 0 - czarne tło
            'layer1_bg': '#1a1a1a',    # Warstwa 1 - zakładki i ich zawartość
            'layer2_bg': '#2d2d2d',    # Warstwa 2 - obszary (karty)
            'layer3_bg': '#3a3a3a',    # Warstwa 3 - tooltips (najjaśniejsza)
            'card_bg': '#2d2d2d',      # Alias dla kompatybilności
            'input_bg': '#252525',
            'button_bg': '#333333',
            'button_hover': '#404040',
            'text': '#e0e0e0',
            'text_dim': '#a0a0a0',
            'accent': '#4a9eff',
            'accent_hover': '#5ab0ff',
            'border': '#404040',
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Ustaw czarny pasek tytułowy (Windows)
        try:
            self.root.tk.call('::tk::unsupported::MacWindowStyle', 'style', self.root, 'dark')
        except:
            pass
        
        # Dla Windows 10/11 - ciemny pasek tytułowy i zaokrąglone rogi
        try:
            import ctypes
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            DWMWA_WINDOW_CORNER_PREFERENCE = 33  # Windows 11
            DWMWCP_ROUND = 2  # Zaokrąglone rogi
            
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            
            # Ciemny pasek tytułowy
            value = ctypes.c_int(1)  # TRUE
            try:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(value), ctypes.sizeof(value))
            except:
                # Fallback dla starszych wersji Windows 10
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                    ctypes.byref(value), ctypes.sizeof(value))
            
            # Zaokrąglone rogi (Windows 11)
            try:
                corner_value = ctypes.c_int(DWMWCP_ROUND)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                    ctypes.byref(corner_value), ctypes.sizeof(corner_value))
            except:
                pass  # Windows 10 nie wspiera zaokrąglonych rogów
                
        except Exception as e:
            print(f"Nie udało się ustawić stylu okna: {e}")
        
        self.setup_styles()
        
        # Always start fullscreen/zoomed
        try:
            if sys.platform.startswith('win'):
                self.root.state('zoomed')
            else:
                self.root.attributes('-fullscreen', True)
        except Exception:
            # Fallback geometry if fullscreen not supported
            self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Inicjalizuj menedżer konfiguracji
        self.config_manager = ConfigManager()
        if config_file:
            self.config_manager.load_config(config_file)
            logger.info(f"Załadowano konfigurację: {config_file}")
        self.config_manager.apply_to_config_module()
        
        # Zmienne
        self.current_dxf_path = tk.StringVar()
        self.current_svg_path = tk.StringVar(value=self.config_manager.get('STRUCTURED_SVG_OUTPUT', 'output_structured.svg'))
        self.processing = False
        self.last_conversion_data = None
        self.current_display_mode = tk.StringVar(value="structured")
        
        # Zmienne dla trybu interaktywnego
        self.all_texts = []  # Wszystkie teksty
        self.all_segments = []  # Wszystkie segmenty
        self.unassigned_texts = []  # Nieprzypisane teksty
        self.unassigned_segments = []  # Nieprzypisane segmenty
        self.assigned_data = {}  # Dane przypisań
        self.assignment_changes = {
            'new_assignments': [],
            'skipped_texts': []
        }
        
        # Centralny menedżer przypisań
        self.assignment_manager = None
        
        # Opcje GUI
        self.auto_refresh_svg = tk.BooleanVar(value=True)  # Domyślnie włączone
        
        # Zmienne dla usuniętej zakładki "Widok SVG" (kompatybilność wsteczna)
        self.current_file_info = tk.StringVar(value="Plik: brak")
        self.zoom_var = tk.StringVar(value="100%")
        self.svg_info = tk.StringVar(value="Brak pliku SVG")
        
        # Kontrola konwersji
        self.conversion_cancelled = False
        self.conversion_thread = None
        
        # Zaznaczone elementy w GUI
        self.selected_text_index = None
        self.selected_segment_index = None
        
        # Zapamiętane wybory
        self.stored_text = None
        self.stored_text_data = None
        self.stored_segment = None
        self.stored_segment_data = None
        
        # Style
        self.setup_styles()
        
        # Interfejs
        self.create_interface()
        
        # Automatyczne ładowanie domyślnych plików
        self.load_default_files()
    
    def setup_styles(self):
        """Konfiguracja stylów - ciemny motyw z warstwami (bez ramek)"""
        style = ttk.Style()
        
        # Ciemny motyw jako bazę
        style.theme_use('clam')
        
        # Główne tło - warstwa 0 (czarna)
        style.configure('.', background=self.colors['bg'], 
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['input_bg'])
        
        # Frame - warstwa 1
        style.configure('TFrame', background=self.colors['layer1_bg'],
                       borderwidth=0, relief=tk.FLAT)
        style.configure('Card.TFrame', background=self.colors['layer2_bg'],
                       borderwidth=0, relief=tk.FLAT)
        
        # Notebook (zakładki) - MAŁE, zaokrąglone, BEZ RAMEK, przezroczyste headery
        style.configure('TNotebook', 
                       background=self.colors['bg'],  # Warstwa 0 - czarna
                       borderwidth=0,
                       tabmargins=0,
                       highlightthickness=0,
                       relief=tk.FLAT)
        
        # KLUCZOWE: PUSTY LAYOUT = BEZ RAMEK (rozwiązanie ze StackOverflow)
        style.layout('TNotebook', [])
        style.configure('TNotebook', tabmargins=0)
        
        # Usuń padding wokół zawartości notebook
        style.configure('TNotebook', padding=0)
        
        # Layout dla zakładek - MINIMALNY, BEZ ramek i focus ring
        style.layout('TNotebook.Tab', [
            ('Notebook.tab', {
                'sticky': 'nswe',
                'children': [
                    ('Notebook.label', {'sticky': ''})
                ]
            })
        ])
        
        style.configure('TNotebook.Tab', 
                       background=self.colors['bg'],  # Niewybrane wtapiają się w tło
                       foreground=self.colors['text_dim'],
                       padding=[28, 12],  # ZWIĘKSZONE odstępy między zakładkami (było 20)
                       font=('Segoe UI', 10),  # WIĘKSZA czcionka (było 9)
                       borderwidth=0,
                       highlightthickness=0,
                       focuscolor='',
                       lightcolor=self.colors['bg'],  # Usuń jasną ramkę
                       darkcolor=self.colors['bg'],  # Usuń ciemną ramkę
                       bordercolor=self.colors['bg'],  # Kolor ramki = tło
                       relief=tk.FLAT)
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['layer1_bg']),  # Wybrana = kolor zawartości
                           ('!selected', self.colors['bg'])],  # Niewybrana = czarne tło
                 foreground=[('selected', self.colors['text']),
                           ('!selected', self.colors['text_dim'])],
                 lightcolor=[('selected', self.colors['layer1_bg']), ('!selected', self.colors['bg'])],
                 darkcolor=[('selected', self.colors['layer1_bg']), ('!selected', self.colors['bg'])],
                 bordercolor=[('selected', self.colors['layer1_bg']), ('!selected', self.colors['bg'])],
                 borderwidth=[('selected', 0), ('!selected', 0)])
        
        # Labels
        style.configure('TLabel', 
                       background=self.colors['layer1_bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9))
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 14, 'bold'),
                       foreground=self.colors['accent'])
        style.configure('Success.TLabel', foreground='#4caf50')
        style.configure('Error.TLabel', foreground='#f44336')
        style.configure('Info.TLabel', foreground=self.colors['accent'])
        
        # Buttons
        style.configure('TButton',
                       background=self.colors['layer2_bg'],
                       foreground=self.colors['text'],
                       borderwidth=0,
                       relief=tk.FLAT,
                       font=('Segoe UI', 9))
        style.map('TButton',
                 background=[('active', self.colors['accent']),
                           ('pressed', self.colors['accent'])],
                 foreground=[('active', 'white')])
        
        # Combobox - ciemny styl BEZ RAMEK ale działający
        # NIE używamy pustego layoutu!
        style.configure('TCombobox',
                       fieldbackground=self.colors['input_bg'],
                       background=self.colors['layer2_bg'],
                       foreground=self.colors['text'],
                       borderwidth=0,
                       arrowcolor=self.colors['text'],
                       insertcolor=self.colors['text'],
                       highlightthickness=0,
                       relief=tk.FLAT)
        style.map('TCombobox',
                 fieldbackground=[('readonly', self.colors['input_bg'])],
                 selectbackground=[('readonly', self.colors['accent'])],
                 selectforeground=[('readonly', 'white')])
        
        # Scrollbar - ciemny styl BEZ RAMEK
        style.configure('Vertical.TScrollbar',
                       background=self.colors['layer2_bg'],
                       troughcolor=self.colors['bg'],
                       borderwidth=0,
                       arrowcolor=self.colors['text'],
                       relief=tk.FLAT)
        style.map('Vertical.TScrollbar',
                 background=[('active', self.colors['accent'])])
        
        # PanedWindow - BEZ RAMEK, minimalistyczny sash
        style.configure('TPanedwindow', 
                       background=self.colors['bg'],
                       borderwidth=0,
                       relief=tk.FLAT)
        
        # Sash (pasek przesuwania) - subtelny, minimalistyczny
        style.configure('Sash',
                       sashthickness=6,  # Cienki pasek
                       background=self.colors['layer2_bg'],
                       borderwidth=0,
                       relief=tk.FLAT)
        style.map('Sash',
                 background=[('active', self.colors['accent'])])  # Podświetlenie przy hover
        
        # Labelframe - BEZ RAMEK (pusty layout dla zawartości)
        style.layout('TLabelframe', [
            ('Labelframe.border', {
                'sticky': 'nswe',
                'children': [
                    ('Labelframe.label', {'side': 'top', 'sticky': 'w'}),
                ]
            })
        ])
        style.configure('TLabelframe', 
                       background=self.colors['layer1_bg'],
                       foreground=self.colors['text'],
                       borderwidth=0,
                       bordercolor=self.colors['layer1_bg'],
                       lightcolor=self.colors['layer1_bg'],
                       darkcolor=self.colors['layer1_bg'],
                       relief=tk.FLAT)
        style.configure('TLabelframe.Label',
                       background=self.colors['layer1_bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Combobox - TRANSPARENT lub DOPASOWANE kolory ramek
        try:
            # Próba 1: transparent
            style.configure('TCombobox',
                           background=self.colors['layer1_bg'],
                           foreground=self.colors['text'],
                           fieldbackground=self.colors['layer1_bg'],
                           selectbackground=self.colors['accent'],
                           selectforeground=self.colors['text'],
                           borderwidth=0,
                           relief=tk.FLAT,
                           lightcolor='',
                           darkcolor='',
                           bordercolor='',
                           arrowcolor=self.colors['text'])
            style.map('TCombobox',
                     fieldbackground=[('readonly', self.colors['layer1_bg'])],
                     selectbackground=[('readonly', self.colors['accent'])],
                     lightcolor=[('focus', ''), ('!focus', '')],
                     darkcolor=[('focus', ''), ('!focus', '')],
                     bordercolor=[('focus', ''), ('!focus', '')])
        except:
            # Fallback: dopasuj do tła
            style.configure('TCombobox',
                           background=self.colors['layer1_bg'],
                           foreground=self.colors['text'],
                           fieldbackground=self.colors['layer1_bg'],
                           selectbackground=self.colors['accent'],
                           selectforeground=self.colors['text'],
                           borderwidth=0,
                           relief=tk.FLAT,
                           lightcolor=self.colors['layer1_bg'],
                           darkcolor=self.colors['layer1_bg'],
                           bordercolor=self.colors['layer1_bg'],
                           arrowcolor=self.colors['text'])
            style.map('TCombobox',
                     fieldbackground=[('readonly', self.colors['layer1_bg'])],
                     selectbackground=[('readonly', self.colors['accent'])],
                     lightcolor=[('focus', self.colors['layer1_bg']), ('!focus', self.colors['layer1_bg'])],
                     darkcolor=[('focus', self.colors['layer1_bg']), ('!focus', self.colors['layer1_bg'])],
                     bordercolor=[('focus', self.colors['layer1_bg']), ('!focus', self.colors['layer1_bg'])])
        
        # Card.TCombobox - specjalny styl dla unified_config_tab (warstwa 2 - ciemniejsza ramka)
        try:
            style.configure('Card.TCombobox',
                           background=self.colors['layer2_bg'],
                           foreground=self.colors['text'],
                           fieldbackground=self.colors['layer2_bg'],
                           selectbackground=self.colors['accent'],
                           selectforeground=self.colors['text'],
                           borderwidth=0,
                           relief=tk.FLAT,
                           lightcolor='',
                           darkcolor='',
                           bordercolor='',
                           arrowcolor=self.colors['text'])
            style.map('Card.TCombobox',
                     fieldbackground=[('readonly', self.colors['layer2_bg'])],
                     selectbackground=[('readonly', self.colors['accent'])],
                     lightcolor=[('focus', ''), ('!focus', '')],
                     darkcolor=[('focus', ''), ('!focus', '')],
                     bordercolor=[('focus', ''), ('!focus', '')])
        except:
            style.configure('Card.TCombobox',
                           background=self.colors['layer2_bg'],
                           foreground=self.colors['text'],
                           fieldbackground=self.colors['layer2_bg'],
                           selectbackground=self.colors['accent'],
                           selectforeground=self.colors['text'],
                           borderwidth=0,
                           relief=tk.FLAT,
                           lightcolor=self.colors['layer2_bg'],
                           darkcolor=self.colors['layer2_bg'],
                           bordercolor=self.colors['layer2_bg'],
                           arrowcolor=self.colors['text'])
            style.map('Card.TCombobox',
                     fieldbackground=[('readonly', self.colors['layer2_bg'])],
                     selectbackground=[('readonly', self.colors['accent'])],
                     lightcolor=[('focus', self.colors['layer2_bg']), ('!focus', self.colors['layer2_bg'])],
                     darkcolor=[('focus', self.colors['layer2_bg']), ('!focus', self.colors['layer2_bg'])],
                     bordercolor=[('focus', self.colors['layer2_bg']), ('!focus', self.colors['layer2_bg'])])
        
        # Entry - WARSTWA 2 dla ramek (ciemniejsza)
        style.configure('TEntry',
                       background=self.colors['layer1_bg'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['layer1_bg'],
                       borderwidth=0,
                       relief=tk.FLAT,
                       lightcolor=self.colors['layer2_bg'],
                       darkcolor=self.colors['layer2_bg'],
                       bordercolor=self.colors['layer2_bg'],
                       insertcolor=self.colors['text'])
        style.map('TEntry',
                 lightcolor=[('focus', self.colors['accent']), ('!focus', self.colors['layer2_bg'])],
                 darkcolor=[('focus', self.colors['accent']), ('!focus', self.colors['layer2_bg'])],
                 bordercolor=[('focus', self.colors['accent']), ('!focus', self.colors['layer2_bg'])])
        
        # Radiobutton - BEZ ramek
        style.configure('TRadiobutton',
                       background=self.colors['layer1_bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10),
                       borderwidth=0,
                       focuscolor='',
                       indicatorcolor=self.colors['accent'],
                       relief=tk.FLAT)
        style.map('TRadiobutton',
                 background=[('active', self.colors['layer1_bg'])],
                 foreground=[('active', self.colors['accent'])])
        
        # Checkbutton - BEZ ramek
        style.configure('TCheckbutton',
                       background=self.colors['layer1_bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10),
                       borderwidth=0,
                       focuscolor='',
                       indicatorcolor=self.colors['accent'],
                       relief=tk.FLAT)
        style.map('TCheckbutton',
                 background=[('active', self.colors['layer1_bg'])],
                 foreground=[('active', self.colors['accent'])])
        
        # KOŃCOWY OVERRIDE - wymuszenie braku ramek na WSZYSTKICH elementach ttk
        self.root.option_add('*borderWidth', 0)
        self.root.option_add('*highlightThickness', 0)
        self.root.option_add('*TNotebook*borderWidth', 0)
        self.root.option_add('*TNotebook*highlightThickness', 0)
        self.root.option_add('*TNotebook*relief', 'flat')
    
    def create_interface(self):
        """Tworzenie interfejsu użytkownika"""
        # Główny kontener z możliwością zmiany szerokości paneli - minimalistyczny sash
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Ustaw cienki, subtelny sash (pasek przesuwania)
        try:
            self.main_paned.configure(sashwidth=6)
        except:
            pass
        
        # Panel lewy z zakładkami (sterowanie) - stała szerokość początkowa 670px (480 + 40%)
        self.control_frame = ttk.Frame(self.main_paned, width=670)
        self.main_paned.add(self.control_frame, weight=0)
        
        # Panel prawy (podgląd SVG)
        self.svg_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.svg_frame, weight=1)
        
        # Ustaw początkową pozycję podziału z większym opóźnieniem i retry
        def set_sash_position(retry=0):
            try:
                self.main_paned.sashpos(0, 670)
                # Sprawdź czy się ustawiło
                if self.main_paned.sashpos(0) < 50 and retry < 3:
                    self.root.after(200, lambda: set_sash_position(retry + 1))
            except:
                if retry < 3:
                    self.root.after(200, lambda: set_sash_position(retry + 1))
        
        self.root.after(250, lambda: set_sash_position(0))
        
        # Utwórz zawartość paneli
        self.create_control_panel_with_tabs(self.control_frame)
        self.create_svg_panel(self.svg_frame)
    
    def create_control_panel_with_tabs(self, parent):
        """Panel sterowania z zakładkami (bez tytułu)"""
        # Notebook dla zakładek - BEZPOŚREDNIO bez tytułu, BEZ RAMEK
        self.notebook = ttk.Notebook(parent, style='TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # AGRESYWNE USUNIĘCIE RAMEK - wszystkie możliwe sposoby
        self.notebook.configure(padding=0)
        
        # Bezpośrednie ustawienia na widget
        try:
            self.notebook['borderwidth'] = 0
            self.notebook['highlightthickness'] = 0
            self.notebook['relief'] = 'flat'
        except:
            pass
        
        # Tkinter wewnętrzne opcje
        try:
            self.notebook.configure(borderwidth=0, highlightthickness=0, relief='flat')
        except:
            pass
        
        # Opcje dla pane (obszaru zawartości)
        self.root.option_add('*TNotebook*borderWidth', '0')
        self.root.option_add('*TNotebook*highlightThickness', '0')
        self.root.option_add('*TNotebook*relief', 'flat')
        self.root.option_add('*TNotebook.client*borderWidth', '0')
        self.root.option_add('*TNotebook.client*highlightThickness', '0')
        
        # Zakładka 1: Konfiguracja (zunifikowana - zastępuje stare zakładki 1 i 4)
        self.create_unified_config_tab()
        
        # Zakładka 2: Tryb Interaktywny
        self.create_interactive_tab()
        
        # Zakładka 3: Status i Logi
        self.create_status_tab()
    
    def create_unified_config_tab(self):
        """Zunifikowana zakładka konfiguracji (zastępuje zakładki 1 i 4)"""
        self.unified_config_tab = UnifiedConfigTab(
            self.notebook, 
            self.config_manager,
            on_convert_callback=self.run_conversion_from_config
        )
        self.notebook.add(self.unified_config_tab, text="⚙️ Konfiguracja")
        
        # Podepnij progress i status z zakładki do głównego GUI
        self.progress = self.unified_config_tab.progress
        self.conversion_status_var = tk.StringVar()
        # Połącz status_var z label
        self.conversion_status_var.trace_add('write', 
            lambda *args: self.unified_config_tab.status_label.config(
                text=self.conversion_status_var.get(),
                foreground='blue' if '🔄' in self.conversion_status_var.get() 
                else 'green' if '✅' in self.conversion_status_var.get()
                else 'orange' if '⚠️' in self.conversion_status_var.get()
                else 'red' if '❌' in self.conversion_status_var.get()
                else 'gray'
            )
        )
        
    def run_conversion_from_config(self, dxf_path: str, svg_path: str):
        """Callback wywoływany z zakładki konfiguracji do uruchomienia konwersji"""
        # Ustaw ścieżki
        self.current_dxf_path.set(dxf_path)
        self.current_svg_path.set(svg_path)
        
        # Uruchom konwersję
        self.convert_and_analyze()
    
    def create_files_tab(self):
        """Zakładka: Pliki i Konwersja z integracją konfiguracji"""
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="📁 Pliki i Konwersja")
        
        # Sekcja aktualnej konfiguracji
        config_section = ttk.LabelFrame(files_frame, text="Aktualna Konfiguracja", padding=10)
        config_section.pack(fill=tk.X, pady=(5, 10))
        
        # Nazwa konfiguracji i przełączanie
        config_header_frame = ttk.Frame(config_section)
        config_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(config_header_frame, text="Konfiguracja:").pack(side=tk.LEFT)
        self.current_config_var = tk.StringVar(value=self.config_manager.current_config_name)
        self.config_combo = ttk.Combobox(config_header_frame, textvariable=self.current_config_var,
                                        values=self.config_manager.get_available_configs(),
                                        state='readonly', width=20)
        self.config_combo.pack(side=tk.LEFT, padx=(5, 10))
        self.config_combo.bind('<<ComboboxSelected>>', self.on_config_change)
        
        ttk.Button(config_header_frame, text="Odśwież listę", 
                  command=self.refresh_config_list).pack(side=tk.LEFT, padx=(5, 0))
        
        # Parametry konfiguracji (read-only)
        config_info_frame = ttk.Frame(config_section)
        config_info_frame.pack(fill=tk.X)
        
        # Lewa kolumna
        left_info = ttk.Frame(config_info_frame)
        left_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.config_station_label = ttk.Label(left_info, text="", font=('Arial', 9))
        self.config_station_label.pack(anchor=tk.W)
        
        self.config_format_label = ttk.Label(left_info, text="", font=('Arial', 9))
        self.config_format_label.pack(anchor=tk.W)
        
        self.config_layers_label = ttk.Label(left_info, text="", font=('Arial', 9))
        self.config_layers_label.pack(anchor=tk.W)
        
        # Prawa kolumna
        right_info = ttk.Frame(config_info_frame)
        right_info.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.config_dxf_label = ttk.Label(right_info, text="", font=('Arial', 9))
        self.config_dxf_label.pack(anchor=tk.W)
        
        self.config_svg_label = ttk.Label(right_info, text="", font=('Arial', 9))
        self.config_svg_label.pack(anchor=tk.W)
        
        self.config_search_label = ttk.Label(right_info, text="", font=('Arial', 9))
        self.config_search_label.pack(anchor=tk.W)
        
        # Sekcja konwersji
        conv_section = ttk.LabelFrame(files_frame, text="Konwersja DXF → SVG", padding=10)
        conv_section.pack(fill=tk.X, pady=(0, 10))
        
        # Informacja o procesie
        info_label = ttk.Label(conv_section, 
                              text="Konwersja rozpocznie analizę pliku DXF z aktualnej konfiguracji\ni wyświetli SVG Assignment do interaktywnej analizy.",
                              font=('Arial', 9), foreground="blue")
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Przycisk konwersji i przerwania
        buttons_frame = ttk.Frame(conv_section)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.convert_button = ttk.Button(buttons_frame, text="🔄 Konwertuj i Analizuj", 
                                       command=self.convert_and_analyze)
        self.convert_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.cancel_button = ttk.Button(buttons_frame, text="⏹️ Przerwij", 
                                      command=self.cancel_conversion, state='disabled')
        self.cancel_button.pack(side=tk.RIGHT)
        
        # Progress bar
        self.progress = ttk.Progressbar(conv_section, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Status konwersji
        self.conversion_status_var = tk.StringVar(value="Gotowy do konwersji")
        status_label = ttk.Label(conv_section, textvariable=self.conversion_status_var, 
                                font=('Arial', 9))
        status_label.pack(anchor=tk.W)
        
        # Załaduj informacje o aktualnej konfiguracji
        self.update_config_info()
    
    def refresh_config_list(self):
        """Odśwież listę dostępnych konfiguracji"""
        configs = self.config_manager.get_available_configs()
        self.config_combo['values'] = configs

    def on_config_change(self, event=None):
        """Obsłuż zmianę konfiguracji"""
        config_name = self.current_config_var.get()
        if config_name and self.config_manager.load_config(config_name):
            self.config_manager.apply_to_config_module()
            self.update_config_info()
            self.log_success(f"Załadowano konfigurację: {config_name}")
            
            # Aktualizuj ścieżki plików
            default_dxf = self.config_manager.get('DEFAULT_DXF_FILE', 'input.dxf')
            if os.path.exists(default_dxf):
                self.current_dxf_path.set(os.path.abspath(default_dxf))
                self.log_success(f"📂 Plik DXF z konfiguracji: {default_dxf}")
            else:
                self.log_warning(f"⚠️ Plik DXF z konfiguracji nie istnieje: {default_dxf}")
            
            structured_svg = self.config_manager.get('STRUCTURED_SVG_OUTPUT', 'output_structured.svg')
            self.current_svg_path.set(structured_svg)
        else:
            self.log_error(f"Nie można załadować konfiguracji: {config_name}")
    
    def update_config_info(self):
        """Aktualizuj wyświetlane informacje o konfiguracji"""
        try:
            # Lewa kolumna
            station_id = self.config_manager.get('STATION_ID', 'N/A')
            text_format = self.config_manager.get('CURRENT_TEXT_FORMAT', 'N/A')
            layer_line = self.config_manager.get('LAYER_LINE', 'N/A')
            layer_text = self.config_manager.get('LAYER_TEXT', 'N/A')
            
            self.config_station_label.config(text=f"🏭 Station ID: {station_id}")
            
            format_desc = ""
            if text_format in self.config_manager.get_text_formats():
                format_desc = self.config_manager.get_text_formats()[text_format]['description']
            self.config_format_label.config(text=f"📝 Format: {text_format}")
            
            self.config_layers_label.config(text=f"📋 Warstwy: {layer_line[:15]}... / {layer_text[:15]}...")
            
            # Prawa kolumna
            dxf_file = self.config_manager.get('DEFAULT_DXF_FILE', 'N/A')
            svg_file = self.config_manager.get('STRUCTURED_SVG_OUTPUT', 'N/A')
            search_radius = self.config_manager.get('SEARCH_RADIUS', 'N/A')
            svg_size = f"{self.config_manager.get('SVG_WIDTH', 'N/A')}x{self.config_manager.get('SVG_HEIGHT', 'N/A')}"
            
            self.config_dxf_label.config(text=f"📄 DXF: {dxf_file}")
            self.config_svg_label.config(text=f"🎨 SVG: {svg_file}")
            self.config_search_label.config(text=f"🔍 Promień: {search_radius}, Rozmiar: {svg_size}")
            
        except Exception as e:
            self.log_error(f"Błąd aktualizacji informacji o konfiguracji: {e}")
    
    def get_dxf_config_params(self):
        """Przygotuj parametry konfiguracji dla process_dxf"""
        return {
            'LAYER_TEXT': self.config_manager.get('LAYER_TEXT', '@IDE_KABLE_DC_TXT_B'),
            'LAYER_LINE': self.config_manager.get('LAYER_LINE', '@IDE_KABLE_DC_B'),
            'STATION_ID': self.config_manager.get('STATION_ID', 'ZIEB'),
            'Y_TOLERANCE': float(self.config_manager.get('Y_TOLERANCE', 0.01)),
            'SEGMENT_MIN_WIDTH': float(self.config_manager.get('SEGMENT_MIN_WIDTH', 0)),
            'SEARCH_RADIUS': float(self.config_manager.get('SEARCH_RADIUS', 6.0)),
            'TEXT_LOCATION': self.config_manager.get('TEXT_LOCATION', 'above'),
            'POLYLINE_PROCESSING_MODE': self.config_manager.get('POLYLINE_PROCESSING_MODE', 'individual_segments'),
            'SEGMENT_MERGE_GAP_TOLERANCE': float(self.config_manager.get('SEGMENT_MERGE_GAP_TOLERANCE', 1.0)),
            'MAX_MERGE_DISTANCE': float(self.config_manager.get('MAX_MERGE_DISTANCE', 5.0))
        }

    def convert_and_analyze(self):
        """Nowa metoda konwersji z analizą według konfiguracji"""
        if self.processing:
            return
            
        try:
            # Pobierz plik DXF z konfiguracji
            dxf_file = self.config_manager.get('DEFAULT_DXF_FILE', 'input.dxf')
            if not os.path.exists(dxf_file):
                self.log_error(f"Plik DXF nie istnieje: {dxf_file}")
                messagebox.showerror("Błąd", f"Plik DXF nie istnieje: {dxf_file}")
                return
                
            self.current_dxf_path.set(os.path.abspath(dxf_file))
            self.log_success(f"📂 Rozpoczynam konwersję pliku DXF: {dxf_file}")
            
            # Rozpocznij konwersję
            self.processing = True
            self.conversion_cancelled = False  # Flaga anulowania
            # Status updates są opcjonalne - mogą nie istnieć w nowym GUI
            if hasattr(self, 'conversion_status_var'):
                self.conversion_status_var.set(f"🔄 Analizowanie pliku: {os.path.basename(dxf_file)}...")
            if hasattr(self, 'progress'):
                self.progress.start()
            
            # Uruchom konwersję w osobnym wątku
            def conversion_thread():
                try:
                    # Import tutaj, żeby uniknąć cyklicznych importów
                    from src.core.dxf2svg import process_dxf
                    
                    # Sprawdź czy proces został anulowany
                    if self.conversion_cancelled:
                        self.root.after(0, self.on_conversion_cancelled)
                        return
                    
                    # Przygotuj parametry konfiguracji
                    config_params = self.get_dxf_config_params()
                    
                    # Konwertuj DXF - używaj bezpośrednio podanego pliku z parametrami konfiguracji
                    self.root.after(0, lambda: self.log_message(f"Przetwarzanie pliku: {dxf_file}"))
                    assigned_data, station_texts, unassigned_texts, unassigned_segments, unassigned_polylines = process_dxf(dxf_file, config_params)
                    
                    # Sprawdź ponownie czy anulowano
                    if self.conversion_cancelled:
                        self.root.after(0, self.on_conversion_cancelled)
                        return
                    
                    # Zachowaj dane dla trybu interaktywnego
                    conversion_data = {
                        'assigned_data': assigned_data,
                        'station_texts': station_texts,
                        'unassigned_texts': unassigned_texts,
                        'unassigned_segments': unassigned_segments,
                        'unassigned_polylines': unassigned_polylines
                    }
                    
                    # Zaktualizuj GUI w głównym wątku
                    self.root.after(0, self.on_conversion_complete, conversion_data)
                    
                except Exception as e:
                    if not self.conversion_cancelled:
                        self.root.after(0, self.on_conversion_error, str(e))
            
            # Uruchom wątek konwersji
            self.conversion_thread = threading.Thread(target=conversion_thread, daemon=True)
            self.conversion_thread.start()
            
        except Exception as e:
            self.log_error(f"Błąd rozpoczęcia konwersji: {e}")
            self.processing = False
            # convert_button i cancel_button są w unified_config_tab
            if hasattr(self, 'progress'):
                self.progress.stop()
    
    def cancel_conversion(self):
        """Anuluj trwającą konwersję"""
        if self.processing:
            self.conversion_cancelled = True
            self.log_warning("⚠️ Anulowanie konwersji...")
            if hasattr(self, 'conversion_status_var'):
                self.conversion_status_var.set("⚠️ Anulowanie...")
    
    def on_conversion_cancelled(self):
        """Obsłuż anulowaną konwersję"""
        self.processing = False
        if hasattr(self, 'progress'):
            self.progress.stop()
        if hasattr(self, 'conversion_status_var'):
            self.conversion_status_var.set("⚠️ Konwersja anulowana")
        if hasattr(self, 'unified_config_tab'):
            self.unified_config_tab.convert_btn.config(state='normal')
        self.log_warning("Konwersja została anulowana przez użytkownika")
    
    def on_conversion_complete(self, conversion_data):
        """Obsłuż zakończenie konwersji"""
        self.processing = False
        if hasattr(self, 'progress'):
            self.progress.stop()
        if hasattr(self, 'unified_config_tab'):
            self.unified_config_tab.convert_btn.config(state='normal')
        
        if conversion_data and not self.conversion_cancelled:
            # Zapisz dane konwersji
            self.last_conversion_data = conversion_data
            
            dxf_file = self.config_manager.get('DEFAULT_DXF_FILE', 'input.dxf')
            if hasattr(self, 'conversion_status_var'):
                self.conversion_status_var.set(f"✅ Konwersja zakończona - {os.path.basename(dxf_file)}")
            self.log_success(f"✅ Konwersja pliku {dxf_file} zakończona pomyślnie")
            
            # Aktualizuj informacje o trybie interaktywnym
            self.update_interactive_info()
            
            # Automatycznie wygeneruj interaktywny SVG po konwersji
            self.log_message("🔄 Automatyczne generowanie interaktywnego SVG...")
            self._auto_generate_interactive_svg()
            
            # Automatycznie uruchom edytor przypisań
            self.log_message("🚀 Automatyczne uruchomienie edytora przypisań...")
            self.start_interactive_mode()
            
            # Przełącz na tryb interactive assignment
            self.current_display_mode.set("interactive")
            self.change_display_mode()
            
        else:
            self.conversion_status_var.set("❌ Błąd konwersji")
            self.log_error("Konwersja DXF nie powiodła się")
    
    def on_conversion_error(self, error_msg):
        """Obsłuż błąd konwersji"""
        self.processing = False
        if hasattr(self, 'progress'):
            self.progress.stop()
        if hasattr(self, 'unified_config_tab'):
            self.unified_config_tab.convert_btn.config(state='normal')
        if hasattr(self, 'conversion_status_var'):
            self.conversion_status_var.set("❌ Błąd konwersji")
        dxf_file = self.config_manager.get('DEFAULT_DXF_FILE', 'input.dxf')
        self.log_error(f"❌ Błąd konwersji pliku {dxf_file}: {error_msg}")
        messagebox.showerror("Błąd konwersji", f"Wystąpił błąd podczas konwersji pliku {os.path.basename(dxf_file)}:\n{error_msg}")
    
    def create_view_tab(self):
        """Zakładka: Widok SVG - tylko strukturalny i assignment"""
        view_frame = ttk.Frame(self.notebook)
        self.notebook.add(view_frame, text="🖼️ Widok SVG")
        
        # Sekcja wyboru widoku SVG
        view_section = ttk.LabelFrame(view_frame, text="Tryb Wyświetlania", padding=10)
        view_section.pack(fill=tk.X, pady=(5, 10))
        
        # Radio buttons dla wyboru widoku (tylko 2 opcje)
        modes = [
            ("structured", "📊 Strukturalny (z grupami I01-I04)"),
            ("interactive", "🔧 Assignment (edytor przypisań)")
        ]
        
        for mode, description in modes:
            ttk.Radiobutton(view_section, text=description, 
                           variable=self.current_display_mode, value=mode,
                           command=self.change_display_mode).pack(anchor=tk.W, pady=2)
        
        # Informacja o aktualnym pliku
        self.current_file_info = tk.StringVar(value="Plik: brak")
        info_label = ttk.Label(view_section, textvariable=self.current_file_info, 
                              style='Info.TLabel', font=('Arial', 9))
        info_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Sekcja kontroli podglądu
        preview_section = ttk.LabelFrame(view_frame, text="Kontrola Podglądu", padding=10)
        preview_section.pack(fill=tk.X, pady=(0, 10))
        
        # Przyciski kontroli widoku
        view_buttons_frame = ttk.Frame(preview_section)
        view_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(view_buttons_frame, text="🔄 Odśwież", command=self.refresh_svg).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(view_buttons_frame, text="🏠 Reset", command=self.reset_view).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(view_buttons_frame, text="🔍 Dopasuj", command=self.fit_to_window).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(view_buttons_frame, text="⚡ Pełny render", command=self.force_full_render).pack(side=tk.LEFT)
        
        # Kontrola zoomu
        zoom_frame = ttk.Frame(preview_section)
        zoom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT)
        
        self.zoom_var = tk.StringVar(value="100%")
        zoom_label = ttk.Label(zoom_frame, textvariable=self.zoom_var)
        zoom_label.pack(side=tk.RIGHT)
        
        # Informacje o pliku SVG
        info_section = ttk.LabelFrame(view_frame, text="Informacje o Pliku", padding=10)
        info_section.pack(fill=tk.X, pady=(0, 10))
        
        self.svg_info = tk.StringVar(value="Brak pliku SVG")
        info_label = ttk.Label(info_section, textvariable=self.svg_info, style='Info.TLabel')
        info_label.pack(anchor=tk.W)
    
    def create_interactive_tab(self):
        """Zakładka: Tryb Interaktywny - uproszczona bez zbędnych nagłówków"""
        interactive_frame = ttk.Frame(self.notebook)
        self.notebook.add(interactive_frame, text="🔧 Tryb Interaktywny")
        
        # BEZ sekcji "Uruchomienie" - od razu lista tekstów
        # Główna ramka (bez tytułu)
        main_frame = tk.Frame(interactive_frame, bg=self.colors['layer1_bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status nieprzypisanych tekstów (na górze)
        self.unassigned_status = tk.StringVar(value="")
        status_label = tk.Label(main_frame, textvariable=self.unassigned_status,
                               bg=self.colors['layer1_bg'],
                               fg=self.colors['accent'],
                               font=('Segoe UI', 10, 'bold'))
        status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Informacje o stanie (jeśli potrzebne)
        self.interactive_info = tk.StringVar(value="")
        info_label = tk.Label(main_frame, textvariable=self.interactive_info,
                             bg=self.colors['layer1_bg'],
                             fg=self.colors['text_dim'],
                             font=('Segoe UI', 9))
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Lista tekstów (BEZ tytułu sekcji)
        self.texts_label = tk.StringVar(value="Wszystkie teksty (🟢 przypisane, 🔴 nieprzypisane):")
        tk.Label(main_frame, textvariable=self.texts_label,
                bg=self.colors['layer1_bg'],
                fg=self.colors['text'],
                font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(0, 5))
        
        # Frame dla listy tekstów i przycisku wyboru
        texts_frame = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        texts_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Frame dla listy tekstów i przycisku wyboru
        texts_frame = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        texts_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.texts_listbox = tk.Listbox(texts_frame, height=5, selectmode=tk.SINGLE,
                                       bg=self.colors['input_bg'],
                                       fg=self.colors['text'],
                                       selectbackground=self.colors['accent'],
                                       selectforeground='white',
                                       relief=tk.FLAT,
                                       borderwidth=0,
                                       highlightthickness=1,
                                       highlightcolor=self.colors['layer2_bg'],
                                       highlightbackground=self.colors['layer2_bg'],
                                       font=('Segoe UI', 9))
        self.texts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.texts_listbox.bind('<<ListboxSelect>>', self.on_text_select)
        self.texts_listbox.bind('<Double-Button-1>', self.on_text_double_click)
        
        # Lista segmentów (BEZ tytułu sekcji)
        self.segments_label = tk.StringVar(value="Wszystkie segmenty (🟢 przypisane, 🔴 nieprzypisane):")
        tk.Label(main_frame, textvariable=self.segments_label,
                bg=self.colors['layer1_bg'],
                fg=self.colors['text'],
                font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(0, 5))
        
        # Frame dla listy segmentów
        segments_frame = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        segments_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame dla listy segmentów
        segments_frame = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        segments_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.segments_listbox = tk.Listbox(segments_frame, height=5, selectmode=tk.SINGLE,
                                          bg=self.colors['input_bg'],
                                          fg=self.colors['text'],
                                          selectbackground=self.colors['accent'],
                                          selectforeground='white',
                                          relief=tk.FLAT,
                                          borderwidth=0,
                                          highlightthickness=1,
                                          highlightcolor=self.colors['layer2_bg'],
                                          highlightbackground=self.colors['layer2_bg'],
                                          font=('Segoe UI', 9))
        self.segments_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.segments_listbox.bind('<<ListboxSelect>>', self.on_segment_select)
        self.segments_listbox.bind('<Double-Button-1>', self.on_segment_double_click)
        
        # NOWE: Prawy przycisk myszy - szybkie przypisanie BEZ potwierdzenia (jak mechanizm SVG)
        self.segments_listbox.bind('<Button-3>', self.quick_assign_right_click)
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Wyświetlanie zapamiętanych wyborów (BEZ LabelFrame)
        tk.Label(main_frame, text="Zapamiętane wybory:",
                bg=self.colors['layer1_bg'],
                fg=self.colors['text'],
                font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        columns_frame = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        columns_frame.pack(fill=tk.X, pady=(0, 10))
        
        columns_frame = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        columns_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Lewa kolumna - Teksty
        text_column = tk.Frame(columns_frame, bg=self.colors['layer1_bg'])
        text_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(text_column, text="📝 Wybrany tekst:",
                bg=self.colors['layer1_bg'],
                fg=self.colors['text'],
                font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        self.stored_text_info = tk.StringVar(value="❌ Brak wybranego tekstu")
        tk.Label(text_column, textvariable=self.stored_text_info,
                bg=self.colors['layer1_bg'],
                fg=self.colors['text_dim'],
                font=('Segoe UI', 8), wraplength=200).pack(anchor=tk.W, pady=(2, 0))
        
        # Prawa kolumna - Segmenty  
        segment_column = tk.Frame(columns_frame, bg=self.colors['layer1_bg'])
        segment_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(segment_column, text="🔗 Wybrany segment:",
                bg=self.colors['layer1_bg'],
                fg=self.colors['text'],
                font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        self.stored_segment_info = tk.StringVar(value="❌ Brak wybranego segmentu")
        tk.Label(segment_column, textvariable=self.stored_segment_info,
                bg=self.colors['layer1_bg'],
                fg=self.colors['text_dim'],
                font=('Segoe UI', 8), wraplength=200).pack(anchor=tk.W, pady=(2, 0))
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Przyciski akcji (BEZ LabelFrame "Akcje")
        tk.Label(main_frame, text="Akcje:",
                bg=self.colors['layer1_bg'],
                fg=self.colors['text'],
                font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Pomocnicza funkcja do tworzenia przycisków z tooltipami
        def create_action_btn(parent, text, command, tooltip, **kwargs):
            btn = ttk.Button(parent, text=text, command=command, **kwargs)
            btn.pack(side=tk.LEFT, padx=(0,5))
            if hasattr(self, 'unified_config_tab') and self.unified_config_tab:
                self.unified_config_tab.create_tooltip(btn, tooltip)
            return btn
        
        # Rząd 1 - Podstawowe operacje
        action_frame1 = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        action_frame1.pack(fill=tk.X, pady=(0, 5))
        
        create_action_btn(action_frame1, "✅ Przypisz Tekst", 
                         self.assign_text_to_segment,
                         "Przypisuje zaznaczony tekst do zaznaczonej linii.\n" +
                         "SKRÓT: Zaznacz tekst i linię, następnie kliknij PRAWYM przyciskiem myszy na liście linii.")
        create_action_btn(action_frame1, "🗑️ Wyczyść Linię", 
                         self.clear_segment_assignments,
                         "Usuwa wszystkie teksty przypisane do zaznaczonej linii.\n" +
                         "Linia zostaje wyczyszczona i może przyjąć nowe przypisania.")
        create_action_btn(action_frame1, "❌ Wyczyść Wybór", 
                         self.clear_selected_text,
                         "Czyści aktualnie zapamiętany wybór tekstu i linii.\n" +
                         "Resetuje formularz do stanu początkowego.")
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # DUŻY PRZYCISK: Generuj Structured SVG (podobny do przycisku Analiza)
        gen_svg_frame = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        gen_svg_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tworzenie dużego przycisku z Canvas (jak przycisk Konwertuj)
        self.generate_svg_canvas = tk.Canvas(gen_svg_frame, height=50,
                                            bg=self.colors['layer1_bg'],
                                            highlightthickness=0, borderwidth=0)
        self.generate_svg_canvas.pack(fill=tk.X)
        
        def draw_generate_btn():
            width = self.generate_svg_canvas.winfo_width() if self.generate_svg_canvas.winfo_width() > 1 else 600
            self.generate_svg_canvas.delete('all')
            from src.gui.unified_config_tab import create_rounded_rectangle
            self.gen_svg_rect = create_rounded_rectangle(
                self.generate_svg_canvas, 0, 0, width, 50, radius=25,
                fill='#4caf50', outline='', width=0)  # Zielony jak sukces
            self.gen_svg_text = self.generate_svg_canvas.create_text(
                width//2, 25, text="📁 Generuj Structured SVG (FINAŁ)",
                fill='white', font=('Segoe UI', 12, 'bold'))
        
        # Hover effects
        def on_gen_enter(e):
            self.generate_svg_canvas.itemconfig(self.gen_svg_rect, fill='#66bb6a')
            self.generate_svg_canvas.config(cursor='hand2')
        def on_gen_leave(e):
            self.generate_svg_canvas.itemconfig(self.gen_svg_rect, fill='#4caf50')
            self.generate_svg_canvas.config(cursor='')
        def on_gen_click(e):
            self.generate_final_structured_svg()
        
        self.generate_svg_canvas.bind('<Configure>', lambda e: draw_generate_btn())
        self.generate_svg_canvas.bind('<Enter>', on_gen_enter)
        self.generate_svg_canvas.bind('<Leave>', on_gen_leave)
        self.generate_svg_canvas.bind('<Button-1>', on_gen_click)
        self.generate_svg_canvas.after(50, draw_generate_btn)
        
        # Tooltip dla dużego przycisku
        if hasattr(self, 'unified_config_tab') and self.unified_config_tab:
            self.unified_config_tab.create_tooltip(
                self.generate_svg_canvas,
                "GENERUJE FINALNY STRUCTURED SVG\n\n" +
                "Tworzy końcowy plik SVG z wszystkimi przypisaniami tekstów do linii.\n" +
                "Ten plik zawiera grupowane elementy (I01-I04) i jest gotowy do użycia.\n\n" +
                "Upewnij się że wszystkie potrzebne przypisania zostały wykonane przed generowaniem.")
        
        # Dodatkowo: przyciski pomocnicze w małym rzędzie
        utils_frame = tk.Frame(main_frame, bg=self.colors['layer1_bg'])
        utils_frame.pack(fill=tk.X, pady=(5, 0))
        
        create_action_btn(utils_frame, "📊 Statystyki", 
                         self.show_assignment_statistics,
                         "Wyświetla szczegółowe statystyki przypisań:\n" +
                         "- Liczba przypisanych tekstów\n" +
                         "- Liczba nieprzypisanych tekstów\n" +
                         "- Liczba linii z przypisaniami")
        create_action_btn(utils_frame, "🗺️ Mapa numerów", 
                         self.show_segment_numbers_map,
                         "Pokazuje mapę wszystkich numerów segmentów/linii.\n" +
                         "Pomaga w identyfikacji linii w pliku DXF.")
    
    def create_config_tab(self):
        """Tworzy zakładkę konfiguracji za pomocą ConfigTab"""
        config_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_tab_frame, text="⚙️ Konfiguracja")
        
        # Utwórz instancję ConfigTab
        self.config_tab = ConfigTab(config_tab_frame, self.config_manager)

    def create_status_tab(self):
        """Zakładka: Status i Logi - ciemny motyw z zaokrągleniami"""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="📊 Status i Logi")
        
        # Status - CANVAS z zaokrąglonym tłem (warstwa 2)
        status_outer = tk.Frame(status_frame, bg=self.colors['layer1_bg'])
        status_outer.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        status_canvas = tk.Canvas(status_outer, height=80,
                                 bg=self.colors['layer1_bg'],
                                 highlightthickness=0, borderwidth=0)
        status_canvas.pack(fill=tk.X)
        
        # Rysuj zaokrąglone tło
        def draw_status_bg(event=None):
            width = status_canvas.winfo_width() if status_canvas.winfo_width() > 1 else 600
            status_canvas.delete('bg')
            from src.gui.unified_config_tab import create_rounded_rectangle
            create_rounded_rectangle(status_canvas, 0, 0, width, 80, radius=16,
                                   fill=self.colors['layer2_bg'], outline='', width=0,
                                   tags='bg')
        
        status_canvas.bind('<Configure>', draw_status_bg)
        status_canvas.after(50, draw_status_bg)
        
        # Zawartość na Canvas
        status_inner = tk.Frame(status_canvas, bg=self.colors['layer2_bg'])
        status_canvas.create_window(15, 10, window=status_inner, anchor='nw')
        
        status_title = tk.Label(status_inner, text="Status", 
                               bg=self.colors['layer2_bg'],
                               fg=self.colors['text'],
                               font=('Segoe UI', 11, 'bold'))
        status_title.pack(anchor=tk.W, pady=(0, 5))
        
        self.status_var = tk.StringVar(value="Gotowy")
        status_label = tk.Label(status_inner, textvariable=self.status_var,
                               bg=self.colors['layer2_bg'],
                               fg=self.colors['accent'],
                               font=('Segoe UI', 10))
        status_label.pack(anchor=tk.W)
        
        # Logi - CANVAS z zaokrąglonym tłem (warstwa 2)
        log_outer = tk.Frame(status_frame, bg=self.colors['layer1_bg'])
        log_outer.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 10))
        
        log_canvas = tk.Canvas(log_outer, 
                              bg=self.colors['layer1_bg'],
                              highlightthickness=0, borderwidth=0)
        log_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Rysuj zaokrąglone tło
        def draw_log_bg(event=None):
            width = log_canvas.winfo_width() if log_canvas.winfo_width() > 1 else 600
            height = log_canvas.winfo_height() if log_canvas.winfo_height() > 1 else 400
            log_canvas.delete('bg')
            from src.gui.unified_config_tab import create_rounded_rectangle
            create_rounded_rectangle(log_canvas, 0, 0, width, height, radius=16,
                                   fill=self.colors['layer2_bg'], outline='', width=0,
                                   tags='bg')
        
        log_canvas.bind('<Configure>', draw_log_bg)
        log_canvas.after(50, draw_log_bg)
        
        # Zawartość na Canvas
        log_inner = tk.Frame(log_canvas, bg=self.colors['layer2_bg'])
        log_canvas.create_window(15, 10, window=log_inner, anchor='nw')
        
        # Dostosuj rozmiar wewnętrznej ramki do canvas
        def resize_log_inner(event=None):
            canvas_width = log_canvas.winfo_width()
            canvas_height = log_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                log_inner.config(width=canvas_width - 30, height=canvas_height - 20)
        log_canvas.bind('<Configure>', lambda e: (draw_log_bg(e), resize_log_inner(e)))
        
        log_title = tk.Label(log_inner, text="Logi", 
                            bg=self.colors['layer2_bg'],
                            fg=self.colors['text'],
                            font=('Segoe UI', 11, 'bold'))
        log_title.pack(anchor=tk.W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(log_inner, wrap=tk.WORD,
                                                  bg=self.colors['input_bg'],
                                                  fg=self.colors['text'],
                                                  insertbackground=self.colors['text'],
                                                  relief=tk.FLAT,
                                                  borderwidth=0,
                                                  highlightthickness=1,
                                                  highlightcolor=self.colors['layer2_bg'],
                                                  highlightbackground=self.colors['layer2_bg'],
                                                  font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
    
    def create_svg_panel(self, parent):
        """Panel podglądu SVG - SVG viewer z własnym wbudowanym toolbarem"""
        # Główny kontener
        main_container = ttk.Frame(parent)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Enhanced SVG Viewer with assignment callback (ma własny toolbar wewnątrz)
        self.svg_viewer = EnhancedSVGViewer(main_container)
        
        # Set assignment callback
        self.svg_viewer.set_assignment_callback(self.on_svg_assignment_made)
        
        # Dodaj przyciski trybu do toolbara SVG viewera
        self.add_mode_buttons_to_svg_viewer()
        
        # Also keep simple viewer as backup
        self.simple_svg_viewer = None
    
    def add_mode_buttons_to_svg_viewer(self):
        """Dodaj przyciski trybu (📊 Strukturalny / 🔧 Assignment) do toolbara SVG viewera"""
        if not hasattr(self.svg_viewer, 'mode_buttons_frame'):
            return
        
        mode_frame = self.svg_viewer.mode_buttons_frame
        
        # Użyj funkcji z SVG viewera
        if not hasattr(self.svg_viewer, 'create_round_icon_button'):
            return
        
        create_btn = self.svg_viewer.create_round_icon_button
        create_tooltip = self.svg_viewer.create_tooltip_func
        colors = self.svg_viewer.toolbar_colors
        
        # Przyciski trybu z tooltipami
        self.btn_structured = create_btn(
            mode_frame, "📊", None,
            "Tryb Strukturalny\nWyświetla SVG z pogrupowanymi\nelementami (I01-I04)",
            is_toggle=True, toggle_value="structured")
        
        self.btn_assignment = create_btn(
            mode_frame, "🔧", None,
            "Tryb Assignment\nEdytor przypisań -\nłącz teksty z liniami",
            is_toggle=True, toggle_value="interactive")
        
        # Dodaj obsługę kliknięć dla przycisków trybu
        def on_structured_click(event):
            self.current_display_mode.set("structured")
            self.change_display_mode()
            update_toggle_buttons()
        
        def on_assignment_click(event):
            self.current_display_mode.set("interactive")
            self.change_display_mode()
            update_toggle_buttons()
        
        # Usuń stare bindingi i dodaj nowe
        self.btn_structured.unbind('<Button-1>')
        self.btn_assignment.unbind('<Button-1>')
        self.btn_structured.bind('<Button-1>', on_structured_click)
        self.btn_assignment.bind('<Button-1>', on_assignment_click)
        
        # Funkcja aktualizacji toggles
        def update_toggle_buttons():
            current = self.current_display_mode.get()
            if current == "structured":
                self.btn_structured.itemconfig(self.btn_structured.circle, fill=colors['accent'])
                self.btn_structured.itemconfig(self.btn_structured.icon_id, fill='white')
                self.btn_assignment.itemconfig(self.btn_assignment.circle, fill=colors['button_bg'])
                self.btn_assignment.itemconfig(self.btn_assignment.icon_id, fill=colors['text'])
            else:
                self.btn_assignment.itemconfig(self.btn_assignment.circle, fill=colors['accent'])
                self.btn_assignment.itemconfig(self.btn_assignment.icon_id, fill='white')
                self.btn_structured.itemconfig(self.btn_structured.circle, fill=colors['button_bg'])
                self.btn_structured.itemconfig(self.btn_structured.icon_id, fill=colors['text'])
        
        # Inicjalna aktualizacja
        mode_frame.after(100, update_toggle_buttons)
    

    # Metody obsługi plików
    def select_dxf_file(self):
        """Wybór pliku DXF"""
        file_path = filedialog.askopenfilename(
            title="Wybierz plik DXF",
            filetypes=[("Pliki DXF", "*.dxf"), ("Wszystkie pliki", "*.*")],
            initialdir=os.getcwd()
        )
        
        if file_path:
            self.current_dxf_path.set(file_path)
            self.log_message(f"Wybrano plik DXF: {os.path.basename(file_path)}")
    
    def save_svg_as(self):
        """Zapisz SVG jako"""
        file_path = filedialog.asksaveasfilename(
            title="Zapisz SVG jako",
            defaultextension=".svg",
            filetypes=[("Pliki SVG", "*.svg"), ("Wszystkie pliki", "*.*")],
            initialdir=os.getcwd()
        )
        
        if file_path:
            self.current_svg_path.set(file_path)
            self.log_message(f"Ustawiono ścieżkę wyjściową: {os.path.basename(file_path)}")
    
    # Metody konwersji
    def convert_file(self):
        """Konwersja pliku DXF do SVG"""
        if self.processing:
            return
        
        dxf_path = self.current_dxf_path.get()
        if not dxf_path or not os.path.exists(dxf_path):
            messagebox.showerror("Błąd", "Wybierz prawidłowy plik DXF")
            return
        
        # Uruchom konwersję w osobnym wątku
        self.processing = True
        self.convert_button.configure(state='disabled')
        self.progress.start()
        self.status_var.set("Konwersja w toku...")
        
        thread = threading.Thread(target=self._convert_worker, args=(dxf_path,))
        thread.daemon = True
        thread.start()
    
    def _convert_worker(self, dxf_path):
        """Worker do konwersji w osobnym wątku"""
        try:
            self.log_message("Rozpoczęcie konwersji...")
            
            # Kopiuj plik DXF do katalogu roboczego jeśli potrzeba
            if os.path.basename(dxf_path) != "input.dxf":
                import shutil
                shutil.copy2(dxf_path, "input.dxf")
                self.log_message("Skopiowano plik DXF do katalogu roboczego")
            
            # Wykonaj konwersję z parametrami konfiguracji i zachowaj dane
            config_params = self.get_dxf_config_params()
            assigned_data, station_texts, unassigned_texts, unassigned_segments, unassigned_polylines = process_dxf("input.dxf", config_params)
            
            # Zachowaj dane dla trybu interaktywnego
            self.last_conversion_data = {
                'assigned_data': assigned_data,
                'station_texts': station_texts,
                'unassigned_texts': unassigned_texts,
                'unassigned_segments': unassigned_segments,
                'unassigned_polylines': unassigned_polylines
            }
            
            # Powrót do głównego wątku
            self.root.after(0, self._conversion_complete, True, "Konwersja zakończona pomyślnie")
            
        except Exception as e:
            error_msg = f"Błąd konwersji: {str(e)}"
            self.root.after(0, self._conversion_complete, False, error_msg)
    
    def _conversion_complete(self, success, message):
        """Zakończenie konwersji"""
        self.processing = False
        if hasattr(self, 'progress'):
            self.progress.stop()
        
        if success:
            if hasattr(self, 'status_var'):
                self.status_var.set("Gotowy")
            self.log_message(message)
            
            # Aktualizuj informacje o trybie interaktywnym
            self.update_interactive_info()
            
            # Automatycznie wygeneruj interaktywny SVG po konwersji
            self.log_message("🔄 Automatyczne generowanie interaktywnego SVG...")
            self._auto_generate_interactive_svg()
            
            # Auto-odświeżanie podglądu
            if self.auto_refresh.get():
                self.refresh_svg()
        else:
            self.status_var.set("Błąd")
            self.log_message(message, "ERROR")
            messagebox.showerror("Błąd konwersji", message)
    
    def _auto_generate_interactive_svg(self):
        """Automatyczne generowanie interaktywnego SVG po konwersji"""
        if not self.last_conversion_data:
            self.log_error("Brak danych konwersji do generowania SVG")
            return
        
        try:
            from src.svg.svg_generator import generate_interactive_svg
            
            # Pobierz dane z konwersji
            assigned_data = self.last_conversion_data.get('assigned_data', {})
            station_texts = self.last_conversion_data.get('station_texts', [])
            unassigned_texts = self.last_conversion_data.get('unassigned_texts', [])
            unassigned_segments = self.last_conversion_data.get('unassigned_segments', [])
            
            # Debug - sprawdź co mamy
            self.log_message(f"🔍 DEBUG: assigned_data keys: {list(assigned_data.keys()) if assigned_data else 'BRAK'}")
            self.log_message(f"🔍 DEBUG: station_texts: {len(station_texts)} elementów")
            self.log_message(f"🔍 DEBUG: unassigned_texts: {len(unassigned_texts)} elementów")
            self.log_message(f"🔍 DEBUG: unassigned_segments: {len(unassigned_segments)} elementów")
            
            # Sprawdź czy są jakieś dane do renderowania
            total_segments = 0
            if assigned_data:
                for inv_segments in assigned_data.values():
                    for segments in inv_segments.values():
                        if isinstance(segments, list):
                            total_segments += len(segments)
            total_segments += len(unassigned_segments)
            
            if total_segments == 0 and len(station_texts) == 0 and len(unassigned_texts) == 0:
                self.log_error("Brak danych do wygenerowania SVG - wszystkie listy są puste!")
                return
            
            # Pobierz konfigurację dla station_id
            config_params = self.get_dxf_config_params()
            station_id = config_params.get('STATION_ID')
            
            self.log_message(f"🔧 Generuję SVG dla stacji: {station_id}")
            self.log_message(f"🔧 Segmenty do renderowania: {total_segments}")
            
            # Usuń stary plik jeśli istnieje
            output_svg = "interactive_assignment.svg"
            if os.path.exists(output_svg):
                os.remove(output_svg)
                self.log_message(f"🗑️ Usunięto stary plik SVG")
            
            # Wygeneruj SVG
            generate_interactive_svg(
                assigned_data,      # przypisane dane
                station_texts,      # wszystkie teksty stacji
                unassigned_texts,   # nieprzypisane teksty
                unassigned_segments, # nieprzypisane segmenty
                output_svg,         # plik wyjściowy
                station_id          # ID stacji
            )
            
            # Walidacja wygenerowanego pliku SVG
            try:
                if not os.path.exists(output_svg):
                    self.log_error(f"❌ Plik SVG nie został utworzony: {output_svg}")
                    return
                    
                file_size = os.path.getsize(output_svg)
                if file_size < 100:  # Zwiększony próg
                    self.log_error(f"❌ Plik SVG jest za mały ({file_size} bajtów): {output_svg}")
                    # Sprawdź zawartość
                    with open(output_svg, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.log_error(f"Zawartość: {content[:200]}...")
                    return
                    
                with open(output_svg, 'rb') as f:
                    head = f.read(4096)
                if b'<svg' not in head.lower():
                    self.log_error(f"❌ Plik nie zawiera <svg> tag: {output_svg}")
                    return
                    
                self.log_success(f"✅ Wygenerowano interaktywny SVG ({file_size} bajtów)")
                
            except Exception as ve:
                self.log_error(f"Błąd walidacji SVG: {ve}")
                return
            
            # Jeśli jesteśmy w trybie interactive, odśwież podgląd
            if self.current_display_mode.get() == "interactive":
                self.refresh_svg()
                
        except Exception as e:
            self.log_error(f"❌ Błąd automatycznego generowania SVG: {e}")
            import traceback
            self.log_error(f"Stack trace: {traceback.format_exc()}")
    
    # Metody widoku SVG
    def change_display_mode(self):
        """Zmiana trybu wyświetlania SVG (tylko structured i interactive)"""
        mode = self.current_display_mode.get()
        
        # Mapowanie trybów na pliki (tylko 2 opcje)
        file_mapping = {
            'structured': self.config_manager.get('STRUCTURED_SVG_OUTPUT', 'output_structured.svg'),
            'interactive': 'interactive_assignment.svg'
        }
        
        new_svg_path = file_mapping.get(mode, 'output_structured.svg')
        self.current_svg_path.set(new_svg_path)
        
        # Aktualizuj informację o pliku
        if os.path.exists(new_svg_path):
            file_size = os.path.getsize(new_svg_path) / 1024
            self.current_file_info.set(f"Plik: {new_svg_path} ({file_size:.1f}KB)")
        else:
            self.current_file_info.set(f"Plik: {new_svg_path} (brak)")
        
        # Odśwież podgląd
        self.refresh_svg()
        self.log_message(f"Przełączono na tryb: {mode}")
    
    def refresh_svg(self):
        """Odświeżenie podglądu SVG"""
        svg_path = self.current_svg_path.get()
        
        if os.path.exists(svg_path):
            try:
                # Validate file size and ensure it contains an <svg ...> element to avoid parse errors
                file_size = os.path.getsize(svg_path)
                if file_size < 20:  # likely header-only or empty
                    self.svg_info.set("Plik SVG jest pusty lub niekompletny")
                    self.log_error(f"SVG parse error: plik pusty lub niekompletny: {svg_path}")
                    return
                with open(svg_path, 'rb') as f:
                    head = f.read(4096)
                if b'<svg' not in head.lower():
                    self.svg_info.set("Nieprawidłowy SVG (brak znacznika <svg>)")
                    self.log_error(f"SVG parse error: brak <svg> w pliku: {svg_path}")
                    return
                self.svg_viewer.load_svg(svg_path)
                self.update_svg_info(svg_path)
                self.update_zoom_display()
                self.log_message(f"Odświeżono podgląd: {os.path.basename(svg_path)}")
            except Exception as e:
                self.svg_info.set("Błąd wczytywania SVG")
                self.log_error(f"SVG parse/load error dla '{svg_path}': {e}")
        else:
            self.svg_info.set("Brak pliku SVG")
            self.log_message(f"Nie znaleziono pliku SVG: {svg_path}", "WARNING")
    
    def reset_view(self):
        """Reset widoku SVG"""
        self.svg_viewer.reset_view()
        self.update_zoom_display()
        self.log_message("Reset widoku")
    
    def fit_to_window(self):
        """Dopasowanie SVG do okna"""
        self.svg_viewer.fit_to_window()
        self.update_zoom_display()
        self.log_message("Dopasowano do okna")
    
    def force_full_render(self):
        """Wymuś pełne renderowanie SVG"""
        self.svg_viewer.force_full_render()
        self.update_zoom_display()
        self.log_message("Wymuszono pełne renderowanie")
    
    def on_svg_assignment_made(self, assignment_data):
        """Callback when assignment is made in SVG viewer - automatyczne przypisanie lub czyszczenie"""
        try:
            action = assignment_data.get('action', 'assign')
            
            if action == 'clear_line':
                # Czyszczenie przypisań dla linii
                segment_id = assignment_data.get('segment_id')
                if segment_id:
                    self.log_message(f"SVG: Czyszczenie przypisań dla segmentu #{segment_id}")
                    
                    if not self.assignment_manager:
                        self.log_error("AssignmentManager nie jest zainicjalizowany!")
                        return
                    
                    # Znajdź wszystkie teksty przypisane do tego segmentu
                    assigned_texts = []
                    for text_id, assigned_segments in self.assigned_data.items():
                        if segment_id in assigned_segments:
                            assigned_texts.append(text_id)
                    
                    if not assigned_texts:
                        self.log_message(f"Segment #{segment_id} nie ma przypisanych tekstów.")
                        return
                    
                    # Wykonaj usunięcie wszystkich przypisań dla tego segmentu bez potwierdzenia
                    try:
                        removed_count = 0
                        for text_id in assigned_texts:
                            result = self.assignment_manager.remove_assignment(text_id, segment_id)
                            if result['success']:
                                removed_count += 1
                                self.log_message(f"✅ Usunięto: {text_id} <- #{segment_id}")
                            else:
                                self.log_error(f"❌ {result['message']}")
                        
                        if removed_count > 0:
                            # Aktualizuj lokalne dane GUI z AssignmentManager
                            self.assigned_data = self.assignment_manager.current_assigned_data
                            self.unassigned_texts = self.assignment_manager.unassigned_texts
                            self.unassigned_segments = self.assignment_manager.unassigned_segments
                            
                            self.log_message(f"✅ Wyczyszczono segment #{segment_id}: usunięto {removed_count} przypisań")
                            
                            # Odśwież listy
                            self.refresh_texts_and_segments_lists()
                            
                            # Zawsze odśwież SVG po czyszczeniu (dla natychmiastowego feedbacku)
                            self.regenerate_and_refresh_svg()
                            
                            # Aktualizuj status
                            self.unassigned_status.set(f"🔴 {len(self.unassigned_texts)} nieprzypisanych tekstów, {len(self.unassigned_segments)} nieprzypisanych segmentów")
                            
                        else:
                            self.log_error("Nie udało się usunąć żadnych przypisań!")
                            
                    except Exception as e:
                        self.log_error(f"❌ Błąd czyszczenia segmentu: {e}")
                
            else:
                # Standardowe przypisanie
                text_id = assignment_data.get('text_id', '').strip()
                line_element = assignment_data.get('line_element')
                
                if text_id and line_element:
                    # Usuń suffix (#XXX) z text_id jeśli istnieje
                    clean_text_id = text_id
                    if ' (#' in clean_text_id:
                        clean_text_id = clean_text_id.split(' (#')[0]
                    
                    self.log_message(f"SVG: Wybrano tekst '{text_id}' (clean: '{clean_text_id}') i linię.")
                    
                    # Znajdź i zaznacz tekst na liście używając oczyszczonego ID
                    self.select_listbox_item_by_id(self.texts_listbox, self.all_texts, 'id', clean_text_id)
                    
                    # Znajdź i zaznacz linię (segment) na liście
                    line_id = line_element.svg_data['attributes'].get('data-segment-id')
                    if line_id:
                        self.select_listbox_item_by_id(self.segments_listbox, self.all_segments, 'id', int(line_id))
                        self.log_message(f"SVG: Znaleziono segment #{line_id} do przypisania.")
                        
                        # Zapamiętaj wybory dla wykonania przypisania
                        sorted_texts = sorted(self.all_texts, key=lambda x: x.get('id', ''))
                        sorted_segments = sorted(self.all_segments, key=lambda x: x.get('id', 0))
                        
                        if (self.selected_text_index is not None and self.selected_text_index < len(sorted_texts) and
                            self.selected_segment_index is not None and self.selected_segment_index < len(sorted_segments)):
                            
                            self.stored_text_data = sorted_texts[self.selected_text_index]
                            self.stored_segment_data = sorted_segments[self.selected_segment_index]
                            
                            # Automatyczne przypisanie (jak było wcześniej)
                            self.assign_text_to_segment()
                    else:
                        self.log_error("Brak 'data-segment-id' w wybranym elemencie linii.")

        except Exception as e:
            self.log_error(f"Błąd podczas operacji SVG: {e}")
    
    def update_zoom_display(self):
        """Aktualizacja wyświetlania zoomu"""
        zoom_percent = int(self.svg_viewer.scale * 100)
        self.zoom_var.set(f"{zoom_percent}%")
    
    def update_svg_info(self, svg_path):
        """Aktualizacja informacji o pliku SVG"""
        try:
            # Rozmiar pliku
            file_size = os.path.getsize(svg_path)
            size_kb = file_size / 1024
            
            # Rozmiary SVG
            width, height = self.svg_viewer.original_size
            
            info = f"Rozmiar: {width}×{height}px, {size_kb:.1f}KB"
            self.svg_info.set(info)
            
        except Exception as e:
            self.svg_info.set(f"Błąd odczytu: {str(e)}")
    
    # Metody trybu interaktywnego
    def update_interactive_info(self):
        """Aktualizacja informacji o trybie interaktywnym"""
        if self.last_conversion_data:
            unassigned_texts_count = len(self.last_conversion_data.get('unassigned_texts', []))
            unassigned_segments_count = len(self.last_conversion_data.get('unassigned_segments', []))
            
            # Zakładka zawsze dostępna
            if unassigned_texts_count > 0 or unassigned_segments_count > 0:
                self.interactive_info.set(f"Edytor przypisań gotowy do pracy")
                status_parts = []
                if unassigned_texts_count > 0:
                    status_parts.append(f"{unassigned_texts_count} nieprzypisanych tekstów")
                if unassigned_segments_count > 0:
                    status_parts.append(f"{unassigned_segments_count} nieprzypisanych segmentów")
                self.unassigned_status.set(f"⚠️ {', '.join(status_parts)}")
            else:
                self.interactive_info.set("Wszystko przypisane - można sprawdzić i poprawić")
                self.unassigned_status.set("✅ Wszystkie elementy przypisane")
        else:
            self.interactive_info.set("Brak danych - wykonaj konwersję DXF")
            self.unassigned_status.set("")
    
    def start_interactive_mode(self):
        """Uruchomienie trybu interaktywnego z pełnymi listami wszystkich tekstów i segmentów"""
        if not self.last_conversion_data:
            messagebox.showerror("Błąd", "Brak danych do edycji. Wykonaj najpierw konwersję DXF.")
            return
        
        try:
            # Pobierz dane z conversion
            assigned_data = self.last_conversion_data.get('assigned_data', {})
            station_texts = self.last_conversion_data.get('station_texts', [])
            unassigned_texts = self.last_conversion_data.get('unassigned_texts', [])
            unassigned_segments = self.last_conversion_data.get('unassigned_segments', [])
            unassigned_polylines = self.last_conversion_data.get('unassigned_polylines', [])
            
            # Utwórz listę wszystkich tekstów (przypisanych + nieprzypisanych)
            self.all_texts = station_texts.copy()  # To już zawiera wszystkie teksty stacji
            self.unassigned_texts = unassigned_texts.copy()
            
            # Aktualizuj listę nieprzypisanych tekstów z poprawnym station_id
            station_id = self.config_manager.get('STATION_ID', 'ZIEB')
            self.unassigned_texts = get_unassigned_texts(self.all_texts, assigned_data, station_id)
            
            # Utwórz listę wszystkich segmentów
            # Zbierz przypisane segmenty z assigned_data
            assigned_segments = []
            for inv_id, strings in assigned_data.items():
                for str_id, segments in strings.items():
                    if segments:  # Tylko stringi z segmentami
                        assigned_segments.extend(segments)
            
            # Połącz przypisane i nieprzypisane segmenty
            self.all_segments = assigned_segments + unassigned_segments
            self.unassigned_segments = unassigned_segments.copy()
            
            # Aktualizuj listę nieprzypisanych segmentów
            self.unassigned_segments = get_unassigned_segments(self.all_segments, assigned_data)
            
            # Aktualizuj dane przypisań
            self.assigned_data = assigned_data
            
            # Inicjalizacja AssignmentManager z aktualnymi danymi
            self.assignment_manager = AssignmentManager()
            self.assignment_manager.initialize_from_data(
                assigned_data=assigned_data,
                all_texts=self.all_texts,
                all_segments=self.all_segments,
                unassigned_texts=unassigned_texts,
                unassigned_segments=unassigned_segments
            )
            self.log_message("✅ AssignmentManager zainicjalizowany z aktualną bazą danych")
            
            if not self.all_texts and not self.all_segments:
                messagebox.showinfo("Info", "Brak danych do wyświetlenia!")
                return
            
            # Wypełnij listy z kolorami
            self.populate_texts_list()
            self.populate_segments_list()
            
            # Zakładka jest zawsze widoczna (bez sekcji assignment_section)
            
            # Przełącz na zakładkę trybu interaktywnego
            self.notebook.select(1)  # Zakładka "Tryb Interaktywny" (była 2, teraz 1 po usunięciu "Widok SVG")
            
            # Przełącz widok na interactive
            self.current_display_mode.set("interactive")
            self.change_display_mode()
            
            # Logowanie informacji
            self.log_message(f"Tryb interaktywny uruchomiony:")
            self.log_message(f"  📝 Wszystkich tekstów: {len(self.all_texts)} (nieprzypisanych: {len(self.unassigned_texts)})")
            self.log_message(f"  📏 Wszystkich segmentów: {len(self.all_segments)} (nieprzypisanych: {len(self.unassigned_segments)})")
            
            # Aktualizuj status
            self.interactive_info.set("✅ Tryb interaktywny aktywny")
            self.unassigned_status.set(f"🔴 {len(self.unassigned_texts)} nieprzypisanych tekstów, {len(self.unassigned_segments)} nieprzypisanych segmentów")
            
        except Exception as e:
            self.log_message(f"Błąd uruchamiania trybu interaktywnego: {e}", "ERROR")
            messagebox.showerror("Błąd", f"Nie można uruchomić trybu interaktywnego:\\n{e}")
    
    def populate_texts_list(self):
        """Wypełnienie listy wszystkich tekstów z zaznaczeniem nieprzypisanych na czerwono"""
        self.texts_listbox.delete(0, tk.END)
        
        # Posortuj wszystkie teksty alfabetycznie
        sorted_texts = sorted(self.all_texts, key=lambda x: x.get('id', ''))
        
        # Utwórz set ID nieprzypisanych tekstów dla szybkiego sprawdzania
        unassigned_ids = {text.get('id') for text in self.unassigned_texts}
        
        assigned_count = 0
        unassigned_count = 0
        
        for i, text in enumerate(sorted_texts):
            try:
                text_id = text.get('id', f'Text_{i}')
                pos = text.get('pos', [0, 0])
                display_text = f"{text_id} @ ({pos[0]:.1f}, {pos[1]:.1f})"
                
                self.texts_listbox.insert(tk.END, display_text)
                
                # Zaznacz nieprzypisane teksty na czerwono
                if text_id in unassigned_ids:
                    self.texts_listbox.itemconfig(i, {'fg': 'red'})
                    unassigned_count += 1
                else:
                    self.texts_listbox.itemconfig(i, {'fg': 'green'})  # Przypisane na zielono
                    assigned_count += 1
                    
            except Exception as e:
                self.log_message(f"Błąd przetwarzania tekstu {i}: {e}", "ERROR")
        
        # Aktualizuj etykietę z liczbami
        self.texts_label.set(f"Wszystkie teksty ({assigned_count} 🟢 przypisanych, {unassigned_count} 🔴 nieprzypisanych):")
    
    def populate_segments_list(self):
        """Wypełnienie listy wszystkich segmentów z numeracją SVG jako główną"""
        self.segments_listbox.delete(0, tk.END)
        
        # Posortuj wszystkie segmenty według ID
        sorted_segments = sorted(self.all_segments, key=lambda x: x.get('id', 0))
        
        # Utwórz set ID nieprzypisanych segmentów dla szybkiego sprawdzania
        unassigned_ids = {segment.get('id') for segment in self.unassigned_segments}
        
        assigned_count = 0
        unassigned_count = 0
        
        # Oblicz globalne numery SVG (jak w svg_generator.py)
        svg_number_map = {}
        svg_counter = 1
        
        # Najpierw przypisane segmenty (w kolejności jak w assigned_data)
        if hasattr(self, 'assigned_data') and self.assigned_data:
            for inverter_id, strings in self.assigned_data.items():
                for string_name, segments in strings.items():
                    if isinstance(segments, list):
                        for segment in segments:
                            seg_id = segment.get('id')
                            if seg_id is not None and seg_id not in svg_number_map:
                                svg_number_map[seg_id] = svg_counter
                                svg_counter += 1
        
        # Potem nieprzypisane segmenty
        for segment in self.unassigned_segments:
            seg_id = segment.get('id')
            if seg_id is not None and seg_id not in svg_number_map:
                svg_number_map[seg_id] = svg_counter
                svg_counter += 1
        
        # Pozostałe segmenty (na wszelki wypadek)
        for segment in sorted_segments:
            seg_id = segment.get('id')
            if seg_id is not None and seg_id not in svg_number_map:
                svg_number_map[seg_id] = svg_counter
                svg_counter += 1
        
        for i, segment in enumerate(sorted_segments):
            try:
                segment_id = segment.get('id', i)
                start = segment.get('start', [0, 0])
                end = segment.get('end', [0, 0])
                
                # Pobierz numer SVG z mapy - to będzie główny numer
                svg_number = svg_number_map.get(segment_id, svg_counter)
                
                # Format: #SVG_numer (DXF:id) (start) → (end)
                display_text = f"#{svg_number} (DXF:{segment_id}) ({start[0]:.1f},{start[1]:.1f}) → ({end[0]:.1f},{end[1]:.1f})"
                
                self.segments_listbox.insert(tk.END, display_text)
                
                # Zaznacz nieprzypisane segmenty na czerwono
                if segment_id in unassigned_ids:
                    self.segments_listbox.itemconfig(i, {'fg': 'red'})
                    unassigned_count += 1
                else:
                    self.segments_listbox.itemconfig(i, {'fg': 'green'})  # Przypisane na zielono
                    assigned_count += 1
                    
            except Exception as e:
                self.log_message(f"Błąd przetwarzania segmentu {i}: {e}", "ERROR")
        
        # Aktualizuj etykietę z liczbami
        self.segments_label.set(f"Wszystkie segmenty ({assigned_count} 🟢 przypisanych, {unassigned_count} 🔴 nieprzypisanych):")
    
    def on_text_select(self, event):
        """Obsługa wyboru tekstu z posortowanej listy wszystkich tekstów"""
        selection = self.texts_listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_text_index = idx
            
            # Pobierz tekst z posortowanej listy wszystkich tekstów
            sorted_texts = sorted(self.all_texts, key=lambda x: x.get('id', ''))
            if idx < len(sorted_texts):
                text_data = sorted_texts[idx]
                text_id = text_data.get('id', 'Unknown')
                
                # Sprawdź czy tekst jest nieprzypisany
                unassigned_ids = {text.get('id') for text in self.unassigned_texts}
                status = "🔴 NIEPRZYPISANY" if text_id in unassigned_ids else "🟢 PRZYPISANY"
                
                # Informacje o tekście są teraz wyświetlane tylko w zapamiętanych wyborach
            else:
                pass  # Błąd indeksu tekstu - nic nie robimy
        else:
            self.selected_text_index = None
    
    def on_segment_select(self, event):
        """Obsługa wyboru segmentu z posortowanej listy wszystkich segmentów"""
        selection = self.segments_listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_segment_index = idx
            
            # Pobierz segment z posortowanej listy wszystkich segmentów
            sorted_segments = sorted(self.all_segments, key=lambda x: x.get('id', 0))
            if idx < len(sorted_segments):
                segment_data = sorted_segments[idx]
                segment_id = segment_data.get('id', 'Unknown')
                
                # Sprawdź czy segment jest nieprzypisany
                unassigned_ids = {segment.get('id') for segment in self.unassigned_segments}
                status = "🔴 NIEPRZYPISANY" if segment_id in unassigned_ids else "🟢 PRZYPISANY"
                
                # Informacje o segmencie są teraz wyświetlane tylko w zapamiętanych wyborach
            else:
                pass  # Błąd indeksu segmentu - nic nie robimy
        else:
            self.selected_segment_index = None
    
    def select_text(self):
        """Zapamiętaj wybrany tekst - UMOŻLIWIA WYBÓR DOWOLNEGO TEKSTU"""
        # Sprawdź czy coś jest zaznaczone w listbox
        selection = self.texts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uwaga", "Najpierw kliknij na tekst w liście")
            return
        
        # Użyj aktualnego zaznaczenia z listbox
        idx = selection[0]
        self.selected_text_index = idx
        
        # Pobierz dane z posortowanej listy wszystkich tekstów
        sorted_texts = sorted(self.all_texts, key=lambda x: x.get('id', ''))
        if idx >= len(sorted_texts):
            messagebox.showerror("Błąd", "Nieprawidłowy indeks tekstu")
            return
        
        selected_text = sorted_texts[idx]
        text_id = selected_text.get('id')
        
        # Sprawdź status tekstu (nieprzypisany / przypisany)
        unassigned_text_ids = {text.get('id') for text in self.unassigned_texts}
        is_unassigned = text_id in unassigned_text_ids
        
        # Zapamiętaj wybór (bez blokowania przypisanych)
        self.stored_text = self.selected_text_index
        self.stored_text_data = selected_text
        
        # Aktualizuj display z właściwym statusem
        status = "🔴 NIEPRZYPISANY" if is_unassigned else "🟢 PRZYPISANY"
        pos = selected_text.get('pos', [0, 0])
        info_text = f"✅ TEKST: {text_id}\nPozycja: ({pos[0]:.2f}, {pos[1]:.2f})\nStatus: {status}"
        
        if not is_unassigned:
            info_text += "\n⚠️ BĘDZIE PRZEPISANY!"
        
        self.stored_text_info.set(info_text)
        
        self.log_message(f"Zapamiętano tekst: {text_id} ({status})")
        
        # Sprawdź czy można już przypisać
        self.check_assignment_ready()
    
    def on_text_double_click(self, event):
        """Obsługa podwójnego kliknięcia na tekście - automatycznie wybierz"""
        self.select_text()
    
    def on_segment_double_click(self, event):
        """Obsługa podwójnego kliknięcia na segmencie - automatycznie wybierz"""
        self.select_segment()
    
    def select_segment(self):
        """Zapamiętaj wybrany segment - UMOŻLIWIA WYBÓR DOWOLNEGO SEGMENTU"""
        # Sprawdź czy coś jest zaznaczone w listbox
        selection = self.segments_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uwaga", "Najpierw kliknij na segment w liście")
            return
        
        # Użyj aktualnego zaznaczenia z listbox
        idx = selection[0]
        self.selected_segment_index = idx
        
        # Pobierz dane z posortowanej listy wszystkich segmentów
        sorted_segments = sorted(self.all_segments, key=lambda x: x.get('id', 0))
        if idx >= len(sorted_segments):
            messagebox.showerror("Błąd", "Nieprawidłowy indeks segmentu")
            return
        
        selected_segment = sorted_segments[idx]
        segment_id = selected_segment.get('id')
        
        # Sprawdź status segmentu (nieprzypisany / przypisany)
        unassigned_segment_ids = {segment.get('id') for segment in self.unassigned_segments}
        is_unassigned = segment_id in unassigned_segment_ids
        
        # Zapamiętaj wybór (bez blokowania przypisanych)
        self.stored_segment = self.selected_segment_index
        self.stored_segment_data = selected_segment
        
        # Aktualizuj display z właściwym statusem
        status = "🔴 NIEPRZYPISANY" if is_unassigned else "🟢 PRZYPISANY"
        start = selected_segment.get('start', [0, 0])
        end = selected_segment.get('end', [0, 0])
        info_text = f"✅ SEGMENT: #{segment_id}\nOd: ({start[0]:.1f}, {start[1]:.1f})\nDo: ({end[0]:.1f}, {end[1]:.1f})\nStatus: {status}"
        
        if not is_unassigned:
            info_text += "\n⚠️ BĘDZIE PRZEPISANY!"
        
        self.stored_segment_info.set(info_text)
        
        self.log_message(f"Zapamiętano segment: #{segment_id} ({status})")
        
        # Sprawdź czy można już przypisać
        self.check_assignment_ready()
    
    def clear_selected_text(self):
        """Wyczyść zapamiętany tekst"""
        self.stored_text = None
        self.stored_text_data = None
        self.stored_text_info.set("❌ Brak wybranego tekstu")
        self.log_message("Wyczyszczono zapamiętany tekst")
    
    def clear_selected_segment(self):
        """Wyczyść zapamiętany segment"""
        self.stored_segment = None
        self.stored_segment_data = None
        self.stored_segment_info.set("❌ Brak wybranego segmentu")
        self.log_message("Wyczyszczono zapamiętany segment")
    
    def clear_selected_segment_assignments(self):
        """Wyczyść wszystkie przypisania dla zapamiętanego segmentu"""
        if not self.stored_segment_data:
            messagebox.showwarning("Brak wyboru", "Najpierw wybierz segment (z listy lub kliknij w SVG)!")
            return
        
        segment_id = self.stored_segment_data.get('id')
        if not segment_id:
            messagebox.showerror("Błąd", "Nie można ustalić ID segmentu!")
            return
        
        if not self.assignment_manager:
            messagebox.showerror("Błąd", "AssignmentManager nie jest zainicjalizowany!")
            return
        
        # Znajdź wszystkie teksty przypisane do tego segmentu
        assigned_texts = []
        for text_id, assigned_segments in self.assigned_data.items():
            if segment_id in assigned_segments:
                assigned_texts.append(text_id)
        
        if not assigned_texts:
            messagebox.showinfo("Informacja", f"Segment #{segment_id} nie ma przypisanych tekstów.")
            return
        
        # Potwierdź usunięcie
        texts_list = "\n".join([f"• {text_id}" for text_id in assigned_texts])
        msg = f"Czy na pewno chcesz wyczyścić wszystkie przypisania dla segmentu #{segment_id}?\n\nUsunięte zostaną przypisania tekstów:\n{texts_list}"
        if not messagebox.askyesno("Potwierdzenie czyszczenia segmentu", msg):
            return
        
        # Wykonaj usunięcie wszystkich przypisań dla tego segmentu
        try:
            removed_count = 0
            for text_id in assigned_texts:
                result = self.assignment_manager.remove_assignment(text_id, segment_id)
                if result['success']:
                    removed_count += 1
                    self.log_message(f"✅ {result['message']}")
                else:
                    self.log_error(f"❌ {result['message']}")
            
            if removed_count > 0:
                # Aktualizuj lokalne dane GUI z AssignmentManager
                self.assigned_data = self.assignment_manager.current_assigned_data
                self.unassigned_texts = self.assignment_manager.unassigned_texts
                self.unassigned_segments = self.assignment_manager.unassigned_segments
                
                self.log_message(f"✅ Wyczyszczono segment #{segment_id}: usunięto {removed_count} przypisań")
                
                # Odśwież listy
                self.refresh_texts_and_segments_lists()
                
                # Zawsze odśwież SVG po czyszczeniu (dla natychmiastowego feedbacku)
                self.regenerate_and_refresh_svg()
                
                # Aktualizuj status w zapamiętanych wyborach - segment nadal zapamiętany ale pokazuje nowy status
                unassigned_segment_ids = {segment.get('id') for segment in self.unassigned_segments}
                is_unassigned = segment_id in unassigned_segment_ids
                status = "🔴 NIEPRZYPISANY" if is_unassigned else "🟢 PRZYPISANY"
                start = self.stored_segment_data.get('start', [0, 0])
                end = self.stored_segment_data.get('end', [0, 0])
                info_text = f"✅ SEGMENT: #{segment_id}\nOd: ({start[0]:.1f}, {start[1]:.1f})\nDo: ({end[0]:.1f}, {end[1]:.1f})\nStatus: {status}"
                self.stored_segment_info.set(info_text)
                
                # Aktualizuj status
                self.unassigned_status.set(f"🔴 {len(self.unassigned_texts)} nieprzypisanych tekstów, {len(self.unassigned_segments)} nieprzypisanych segmentów")
                
            else:
                messagebox.showwarning("Uwaga", "Nie udało się usunąć żadnych przypisań!")
                
        except Exception as e:
            self.log_error(f"❌ Błąd czyszczenia segmentu: {e}")
            messagebox.showerror("Błąd", f"Błąd podczas czyszczenia segmentu: {e}")

    def check_assignment_ready(self):
        """Sprawdź czy można wykonać przypisanie i zaktualizuj przycisk"""
        if self.stored_text_data and self.stored_segment_data:
            # Znajdź przycisk Przypisz i pokoloruj go na zielono
            self.log_message("🎯 Gotowy do przypisania! Naciśnij przycisk 'Przypisz'")
            # Tu można dodać kolorowanie przycisku jeśli potrzeba
    
    def quick_assign_on_right_click(self, event):
        """Szybkie przypisanie prawym przyciskiem myszy - bez okna potwierdzenia - WZOROWANE NA assign_text_to_segment"""
        # Sprawdź czy mamy zaznaczony tekst i segment
        if not self.stored_text_data or not self.stored_segment_data:
            self.log_message("⚠️ Najpierw wybierz tekst i segment używając przycisków 'Wybierz'")
            return  # Nic nie rób jeśli brak wyborów
        
        if not self.assignment_manager:
            self.log_error("❌ AssignmentManager nie jest zainicjalizowany!")
            return
        
        # Pobierz dane z zapamiętanych wyborów (TAK JAK W assign_text_to_segment)
        selected_text = self.stored_text_data
        selected_segment = self.stored_segment_data
        
        text_id = selected_text.get('id')
        segment_id = selected_segment.get('id')
        
        self.log_message(f"🚀 Szybkie przypisanie (PPM): {text_id} -> Segment #{segment_id}")
        
        # Sprawdź statusy elementów (TAK JAK W assign_text_to_segment)
        text_was_unassigned = text_id in {t.get('id') for t in self.assignment_manager.unassigned_texts}
        segment_was_unassigned = segment_id in {s.get('id') for s in self.assignment_manager.unassigned_segments}
        
        self.log_message(f"Status: Tekst {'nieprzypisany' if text_was_unassigned else 'przypisany'}, Segment {'nieprzypisany' if segment_was_unassigned else 'przypisany'}")
        
        # Wykonaj przypisanie BEZ potwierdzenia (to jest główna różnica - brak messagebox.askyesno)
        try:
            result = self.assignment_manager.assign_text_to_segment(text_id, segment_id)
            if result['success']:
                # Aktualizuj lokalne dane GUI z AssignmentManager (TAK JAK W assign_text_to_segment)
                self.assigned_data = self.assignment_manager.current_assigned_data
                self.unassigned_texts = self.assignment_manager.unassigned_texts
                self.unassigned_segments = self.assignment_manager.unassigned_segments
                self.assignment_changes = self.assignment_manager.assignment_changes
                
                action_type = "Przepisano" if result['was_reassignment'] else "Przypisano"
                self.log_success(f"✅ {action_type} (szybkie PPM) {text_id} -> segment #{segment_id}")
                
                # Loguj usunięte przypisania
                for removed in result.get('removed_assignments', []):
                    self.log_message(f"🗑️ Usunięto {removed}")
                
                # Odśwież listy (pokaże zmiany kolorów)
                self.populate_texts_list()
                self.populate_segments_list()
                
                # Wyczyść zapamiętane wybory
                self.clear_selected_text()
                self.clear_selected_segment()
                
                # Wyczyść zaznaczenia w listboxach
                self.texts_listbox.selection_clear(0, tk.END)
                self.segments_listbox.selection_clear(0, tk.END)
                
                # Zawsze odśwież SVG po przypisaniu (dla natychmiastowego feedbacku)
                self.regenerate_and_refresh_svg()
                
                # Aktualizuj status
                self.unassigned_status.set(
                    f"🔴 {len(self.unassigned_texts)} nieprzypisanych tekstów, " +
                    f"{len(self.unassigned_segments)} nieprzypisanych segmentów")
            else:
                self.log_error(f"❌ Szybkie przypisanie nie powiodło się: {result['message']}")
        except Exception as e:
            self.log_error(f"❌ Błąd szybkiego przypisania: {e}")
    
    def quick_assign_right_click(self, event):
        """Szybkie przypisanie PPM - bezpośrednio przez AssignmentManager (jak SVG viewer)"""
        # Sprawdź czy mamy zaznaczony tekst i segment
        if not self.stored_text_data or not self.stored_segment_data:
            self.log_message("⚠️ PPM: Najpierw wybierz tekst i segment")
            return
        
        if not self.assignment_manager:
            self.log_error("❌ PPM: AssignmentManager nie jest zainicjalizowany!")
            return
        
        # Pobierz dane
        text_id = self.stored_text_data.get('id')
        segment_id = self.stored_segment_data.get('id')
        
        self.log_message(f"🖱️ PPM: Przypisanie {text_id} -> Segment #{segment_id}")
        
        try:
            # Wykonaj przypisanie BEZ potwierdzenia (bezpośrednio przez AssignmentManager)
            result = self.assignment_manager.assign_text_to_segment(text_id, segment_id)
            
            if result['success']:
                # Aktualizuj lokalne dane GUI z AssignmentManager
                self.assigned_data = self.assignment_manager.current_assigned_data
                self.unassigned_texts = self.assignment_manager.unassigned_texts
                self.unassigned_segments = self.assignment_manager.unassigned_segments
                self.assignment_changes = self.assignment_manager.assignment_changes
                
                action_type = "Przepisano" if result['was_reassignment'] else "Przypisano"
                self.log_success(f"✅ PPM: {action_type} {text_id} -> segment #{segment_id}")
                
                # Loguj usunięte przypisania
                for removed in result.get('removed_assignments', []):
                    self.log_message(f"🗑️ PPM: Usunięto {removed}")
                
                # Odśwież listy (pokaże zmiany kolorów)
                self.populate_texts_list()
                self.populate_segments_list()
                
                # Wyczyść zapamiętane wybory
                self.clear_selected_text()
                self.clear_selected_segment()
                
                # Wyczyść zaznaczenia w listboxach
                self.texts_listbox.selection_clear(0, tk.END)
                self.segments_listbox.selection_clear(0, tk.END)
                
                # Zawsze odśwież SVG po przypisaniu
                self.regenerate_and_refresh_svg()
                
                # Aktualizuj status
                self.unassigned_status.set(
                    f"🔴 {len(self.unassigned_texts)} nieprzypisanych tekstów, " +
                    f"{len(self.unassigned_segments)} nieprzypisanych segmentów")
                
            else:
                self.log_error(f"❌ PPM: {result['message']}")
                
        except Exception as e:
            self.log_error(f"❌ PPM: Błąd przypisania: {e}")
    
    def assign_text_to_segment(self):
        """Przypisanie tekstu do segmentu używając zapamiętanych wyborów - UMOŻLIWIA PRZEPISYWANIE"""
        if not self.stored_text_data or not self.stored_segment_data:
            messagebox.showwarning("Uwaga", "Najpierw wybierz tekst i segment używając przycisków 'Wybierz'")
            return
        
        if not self.assignment_manager:
            messagebox.showerror("Błąd", "AssignmentManager nie jest zainicjalizowany!")
            return
        
        # Pobierz dane z zapamiętanych wyborów
        selected_text = self.stored_text_data
        selected_segment = self.stored_segment_data
        
        text_id = selected_text.get('id')
        segment_id = selected_segment.get('id')
        
        self.log_message(f"Rozpoczynam przypisanie: {text_id} -> Segment #{segment_id}")
        
        # Sprawdź statusy elementów w AssignmentManager
        text_was_unassigned = text_id in {t.get('id') for t in self.assignment_manager.unassigned_texts}
        segment_was_unassigned = segment_id in {s.get('id') for s in self.assignment_manager.unassigned_segments}
        
        self.log_message(f"Status: Tekst {'nieprzypisany' if text_was_unassigned else 'przypisany'}, Segment {'nieprzypisany' if segment_was_unassigned else 'przypisany'}")
        
        # Potwierdź przepisanie jeśli element był już przypisany (TYLKO dla przycisku, nie dla PPM)
        if not text_was_unassigned or not segment_was_unassigned:
            msg = f"UWAGA: Przepisujesz przypisania!\n\n"
            if not text_was_unassigned:
                msg += f"• Tekst '{text_id}' był już przypisany\n"
            if not segment_was_unassigned:
                msg += f"• Segment #{segment_id} był już przypisany\n"
            msg += f"\nCzy na pewno chcesz przepisać?"
            
            if not messagebox.askyesno("Potwierdzenie przepisania", msg):
                return
        
        # Wykonaj przypisanie przez AssignmentManager
        try:
            result = self.assignment_manager.assign_text_to_segment(text_id, segment_id)
            if result['success']:
                # Aktualizuj lokalne dane GUI z AssignmentManager
                self.assigned_data = self.assignment_manager.current_assigned_data
                self.unassigned_texts = self.assignment_manager.unassigned_texts
                self.unassigned_segments = self.assignment_manager.unassigned_segments
                self.assignment_changes = self.assignment_manager.assignment_changes
                
                action_type = "Przepisano" if result['was_reassignment'] else "Przypisano"
                self.log_success(f"✅ {action_type} {text_id} do segmentu #{segment_id}")
                
                # Loguj usunięte przypisania
                for removed in result.get('removed_assignments', []):
                    self.log_message(f"🗑️ Usunięto {removed}")
                
                # Odśwież listy (pokaże zmiany kolorów)
                self.populate_texts_list()
                self.populate_segments_list()
                
                # Wyczyść zapamiętane wybory
                self.clear_selected_text()
                self.clear_selected_segment()
                
                # Wyczyść zaznaczenia w listboxach
                self.texts_listbox.selection_clear(0, tk.END)
                self.segments_listbox.selection_clear(0, tk.END)
                
                # Zawsze odśwież SVG po przypisaniu (dla natychmiastowego feedbacku)
                self.regenerate_and_refresh_svg()
                
                # Aktualizuj status
                self.unassigned_status.set(f"🔴 {len(self.unassigned_texts)} nieprzypisanych tekstów, {len(self.unassigned_segments)} nieprzypisanych segmentów")
                
            else:
                self.log_error(f"❌ {result['message']}")
                messagebox.showerror("Błąd", f"Nie udało się wykonać przypisania: {result['message']}")
                
        except Exception as e:
            self.log_error(f"❌ Błąd przypisania: {e}")
            messagebox.showerror("Błąd", f"Błąd podczas przypisania: {e}")
        self.selected_text_index = None
        self.selected_segment_index = None
        
        # OPCJONALNE ODŚWIEŻENIE SVG - tylko jeśli użytkownik chce
        if hasattr(self, 'auto_refresh_svg') and self.auto_refresh_svg.get():
            self.log_message("🔄 Rozpoczynam regenerację SVG...")
            self.regenerate_and_refresh_svg()

    def remove_text_segment_assignment(self):
        """Usuń konkretne przypisanie tekstu do segmentu"""
        if not self.assignment_manager:
            messagebox.showerror("Błąd", "AssignmentManager nie jest zainicjalizowany!")
            return
        
        # Pobierz wybrane elementy
        text_id = self.get_selected_text_id()
        segment_id = self.get_selected_segment_id()
        
        if not text_id or not segment_id:
            messagebox.showwarning("Brak wyboru", "Wybierz tekst i segment do usunięcia przypisania!")
            return
        
        # Potwierdź usunięcie
        msg = f"Czy na pewno chcesz usunąć przypisanie?\n\nTekst: {text_id}\nSegment: #{segment_id}"
        if not messagebox.askyesno("Potwierdzenie usunięcia", msg):
            return
        
        # Wykonaj usunięcie przez AssignmentManager
        try:
            result = self.assignment_manager.remove_assignment(text_id, segment_id)
            if result['success']:
                # Aktualizuj lokalne dane GUI z AssignmentManager
                self.assigned_data = self.assignment_manager.current_assigned_data
                self.unassigned_texts = self.assignment_manager.unassigned_texts
                self.unassigned_segments = self.assignment_manager.unassigned_segments
                
                self.log_message(f"✅ {result['message']}")
                
                # Odśwież listy
                self.refresh_texts_and_segments_lists()
                
                # Zawsze odśwież SVG po usunięciu (dla natychmiastowego feedbacku)
                self.regenerate_and_refresh_svg()
                
                # Aktualizuj status
                self.unassigned_status.set(f"🔴 {len(self.unassigned_texts)} nieprzypisanych tekstów, {len(self.unassigned_segments)} nieprzypisanych segmentów")
                
            else:
                self.log_error(f"❌ {result['message']}")
                messagebox.showerror("Błąd", f"Nie udało się usunąć przypisania: {result['message']}")
                
        except Exception as e:
            self.log_error(f"❌ Błąd usuwania: {e}")
            messagebox.showerror("Błąd", f"Błąd podczas usuwania przypisania: {e}")
        
        self.selected_text_index = None
        self.selected_segment_index = None

    def clear_segment_assignments(self):
        """Wyczyść wszystkie przypisania dla zaznaczonego segmentu"""
        if not self.assignment_manager:
            messagebox.showerror("Błąd", "AssignmentManager nie jest zainicjalizowany!")
            return
        
        # Pobierz zaznaczony segment
        segment_id = self.get_selected_segment_id()
        
        if not segment_id:
            messagebox.showwarning("Brak wyboru", "Wybierz segment do wyczyszczenia przypisań!")
            return
        
        # Znajdź wszystkie teksty przypisane do tego segmentu
        assigned_texts = []
        for text_id, assigned_segments in self.assigned_data.items():
            if segment_id in assigned_segments:
                assigned_texts.append(text_id)
        
        if not assigned_texts:
            messagebox.showinfo("Informacja", f"Segment #{segment_id} nie ma przypisanych tekstów.")
            return
        
        # Potwierdź usunięcie
        texts_list = "\n".join([f"• {text_id}" for text_id in assigned_texts])
        msg = f"Czy na pewno chcesz wyczyścić wszystkie przypisania dla segmentu #{segment_id}?\n\nUsunięte zostaną przypisania tekstów:\n{texts_list}"
        if not messagebox.askyesno("Potwierdzenie czyszczenia segmentu", msg):
            return
        
        # Wykonaj usunięcie wszystkich przypisań dla tego segmentu
        try:
            removed_count = 0
            for text_id in assigned_texts:
                result = self.assignment_manager.remove_assignment(text_id, segment_id)
                if result['success']:
                    removed_count += 1
                    self.log_message(f"✅ {result['message']}")
                else:
                    self.log_error(f"❌ {result['message']}")
            
            if removed_count > 0:
                # Aktualizuj lokalne dane GUI z AssignmentManager
                self.assigned_data = self.assignment_manager.current_assigned_data
                self.unassigned_texts = self.assignment_manager.unassigned_texts
                self.unassigned_segments = self.assignment_manager.unassigned_segments
                
                self.log_message(f"✅ Wyczyszczono segment #{segment_id}: usunięto {removed_count} przypisań")
                
                # Odśwież listy
                self.refresh_texts_and_segments_lists()
                
                # Zawsze odśwież SVG po czyszczeniu (dla natychmiastowego feedbacku)
                self.regenerate_and_refresh_svg()
                
                # Aktualizuj status
                self.unassigned_status.set(f"🔴 {len(self.unassigned_texts)} nieprzypisanych tekstów, {len(self.unassigned_segments)} nieprzypisanych segmentów")
                
            else:
                messagebox.showwarning("Uwaga", "Nie udało się usunąć żadnych przypisań!")
                
        except Exception as e:
            self.log_error(f"❌ Błąd czyszczenia segmentu: {e}")
            messagebox.showerror("Błąd", f"Błąd podczas czyszczenia segmentu: {e}")
        
        self.selected_segment_index = None

    
    def regenerate_and_refresh_svg(self):
        """Natychmiastowa regeneracja i odświeżenie SVG po zmianie przypisania"""
        try:
            if not self.assignment_changes['new_assignments']:
                self.log_message("Brak zmian do zastosowania w SVG")
                return
            
            self.log_message("🔄 Regeneruję SVG z nowymi przypisaniami...")
            
            # ZAPISZ AKTUALNĄ POZYCJĘ VIEWPORTU
            viewport_state = None
            if hasattr(self, 'svg_viewer') and self.svg_viewer:
                viewport_state = self.svg_viewer.get_viewport_state()
                self.log_message(f"💾 Zapisano pozycję viewportu: zoom {int(viewport_state['scale']*100)}%")
            
            # Pobierz dane z ostatniej konwersji
            assigned_data = self.last_conversion_data.get('assigned_data', {}).copy()
            station_texts = self.last_conversion_data.get('station_texts', [])
            
            # Zastosuj wszystkie nowe przypisania
            for assignment in self.assignment_changes['new_assignments']:
                text_data = assignment['text']
                segment_data = assignment['segment']
                
                # Znajdź odpowiedni inverter (używamy pierwszego dostępnego)
                inverter_id = list(assigned_data.keys())[0] if assigned_data else "I01"
                if inverter_id not in assigned_data:
                    assigned_data[inverter_id] = {}
                
                # Dodaj segment do stringa tekstowego
                text_id = text_data['id']
                if text_id not in assigned_data[inverter_id]:
                    assigned_data[inverter_id][text_id] = []
                
                # Dodaj segment (unikaj duplikatów)
                segment_ids = [s.get('id') for s in assigned_data[inverter_id][text_id]]
                if segment_data.get('id') not in segment_ids:
                    assigned_data[inverter_id][text_id].append(segment_data)
            
            # Regeneruj SVG z nowymi przypisaniami
            from src.svg.svg_generator import generate_interactive_svg
            
            # Pobierz aktualnie nieprzypisane elementy
            remaining_unassigned_texts = self.unassigned_texts.copy()
            remaining_unassigned_segments = self.unassigned_segments.copy()
            
            self.log_message(f"🔄 Regeneruję SVG: {len(remaining_unassigned_texts)} tekstów, {len(remaining_unassigned_segments)} segmentów")
            
            # Pobierz konfigurację dla station_id
            config_params = self.get_dxf_config_params()
            station_id = config_params.get('STATION_ID')
            
            # Wygeneruj nowy SVG z poprawnymi parametrami
            output_svg = "interactive_assignment.svg"
            generate_interactive_svg(
                assigned_data,           # inverter_data: Dict
                station_texts,          # texts: List (wszystkie teksty stacji)
                remaining_unassigned_texts,  # unassigned_texts: List
                remaining_unassigned_segments,  # unassigned_segments: List
                output_svg,             # output_path: str
                station_id              # station_id: str
            )
            
            # Walidacja wygenerowanego pliku
            try:
                if not os.path.exists(output_svg) or os.path.getsize(output_svg) < 20:
                    self.log_error(f"Interaktywny SVG nie został wygenerowany poprawnie: {output_svg}")
                else:
                    with open(output_svg, 'rb') as f:
                        head = f.read(4096)
                    if b'<svg' not in head.lower():
                        self.log_error(f"Wygenerowany plik nie zawiera <svg>: {output_svg}")
            except Exception as ve:
                self.log_error(f"Walidacja SVG nie powiodła się: {ve}")
            
            # Przełącz widok na interactive i odśwież ZACHOWUJĄC POZYCJĘ
            self.current_display_mode.set("interactive")
            svg_path = "interactive_assignment.svg"
            self.current_svg_path.set(svg_path)
            
            # Aktualizuj informację o pliku
            if os.path.exists(svg_path):
                file_size = os.path.getsize(svg_path) / 1024
                self.current_file_info.set(f"Plik: {svg_path} ({file_size:.1f}KB)")
            else:
                self.current_file_info.set(f"Plik: {svg_path} (brak)")
            
            # Wczytaj SVG ZACHOWUJĄC VIEWPORT
            if viewport_state and hasattr(self, 'svg_viewer') and self.svg_viewer:
                self.svg_viewer.load_svg(svg_path, preserve_viewport=True)
                # Przywróć pozycję natychmiast
                self.svg_viewer.set_viewport_state(viewport_state)
                self.log_message(f"🔄 Przywrócono pozycję viewportu: zoom {int(viewport_state['scale']*100)}%")
                self.update_zoom_display()
            else:
                # Standardowe wczytanie (pierwsze wczytanie)
                self.svg_viewer.load_svg(svg_path)
                self.update_zoom_display()
            
            self.update_svg_info(svg_path)
            self.log_message(f"Odświeżono podgląd: {os.path.basename(svg_path)}")
            
            # Aktualizuj listy po regeneracji
            self.populate_texts_list()
            self.populate_segments_list()
            
            self.log_message("✅ SVG zaktualizowany z nowymi przypisaniami")
            
        except Exception as e:
            self.log_message(f"❌ Błąd regeneracji SVG: {e}", "ERROR")
            # Nie przerywaj operacji - użyj standardowego odświeżania
            self.refresh_svg()

    def _restore_viewport_position(self, viewport_state):
        """Pomocnicza funkcja do przywracania pozycji viewportu"""
        try:
            if hasattr(self, 'svg_viewer') and self.svg_viewer and viewport_state:
                self.svg_viewer.set_viewport_state(viewport_state)
                self.log_message(f"🔄 Przywrócono pozycję viewportu: zoom {int(viewport_state['scale']*100)}%")
                self.update_zoom_display()
            else:
                self.log_message("⚠️ Nie można przywrócić pozycji - brak viewera lub stanu")
        except Exception as e:
            self.log_message(f"⚠️ Nie udało się przywrócić pozycji viewportu: {e}")

    def skip_text(self):
        """Pomiń zapamiętany tekst - UMOŻLIWIA POMIJANIE DOWOLNYCH TEKSTÓW"""
        if not self.stored_text_data:
            messagebox.showwarning("Uwaga", "Najpierw wybierz tekst używając przycisku 'Wybierz Tekst'")
            return
        
        selected_text = self.stored_text_data
        text_id = selected_text.get('id')
        
        # Sprawdź status tekstu
        unassigned_text_ids = {text.get('id') for text in self.unassigned_texts}
        was_unassigned = text_id in unassigned_text_ids
        
        # Potwierdź pomijanie jeśli tekst był już przypisany
        if not was_unassigned:
            if not messagebox.askyesno("Potwierdzenie", f"Tekst '{text_id}' był już przypisany.\nCzy na pewno chcesz go pominąć?"):
                return
        
        # Usuń stare przypisania z assigned_data jeśli istnieją
        if hasattr(self, 'assigned_data') and not was_unassigned:
            for inv_id in list(self.assigned_data.keys()):
                if text_id in self.assigned_data[inv_id]:
                    del self.assigned_data[inv_id][text_id]
                    self.log_message(f"Usunięto przypisanie tekstu {text_id}")
        
        # Dodaj do pominiętych
        self.assignment_changes['skipped_texts'].append(selected_text)
        
        # Usuń z listy nieprzypisanych (jeśli tam był)
        if was_unassigned:
            self.unassigned_texts = [t for t in self.unassigned_texts if t.get('id') != text_id]
        
        action_type = "Usunięto i pominięto" if not was_unassigned else "Pominięto"
        self.log_message(f"{action_type} tekst: {text_id}")
        
        # Odśwież listy (pokaże zmianę kolorów)
        self.populate_texts_list()
        
        # Wyczyść zapamiętany tekst
        self.clear_selected_text()
        
        # Wyczyść zaznaczenie w listbox
        self.selected_text_index = None
        
        # NATYCHMIASTOWE ODŚWIEŻENIE SVG
        self.regenerate_and_refresh_svg()
    
    def show_segment_numbers_map(self):
        """Pokaż mapę numerów segmentów - SVG vs Lista"""
        try:
            if not hasattr(self, 'all_segments') or not self.all_segments:
                messagebox.showinfo("Info", "Brak danych o segmentach")
                return
            
            # Utwórz okno z mapą
            map_window = tk.Toplevel(self.root)
            map_window.title("Mapa numerów segmentów - SVG vs Lista")
            map_window.geometry("800x600")
            
            # Frame z scrollbarem
            main_frame = ttk.Frame(map_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Scrolled text
            scroll_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=('Courier', 10))
            scroll_text.pack(fill=tk.BOTH, expand=True)
            
            # Przygotuj dane
            sorted_segments = sorted(self.all_segments, key=lambda x: x.get('id', 0))
            
            # Nagłówek
            content = "MAPA NUMERÓW SEGMENTÓW\n"
            content += "=" * 80 + "\n\n"
            content += f"{'ID z DXF':<10} {'Nr na SVG':<10} {'Start':<20} {'End':<20} {'Status':<15}\n"
            content += "-" * 80 + "\n"
            
            # Sprawdź nieprzypisane segmenty
            unassigned_ids = {seg.get('id') for seg in self.unassigned_segments}
            
            # Globalna numeracja SVG (jak w svg_generator.py)
            svg_number = 1
            
            # Dane z assigned_data dla obliczenia globalnej numeracji
            if hasattr(self, 'assigned_data'):
                for inverter_id, strings in self.assigned_data.items():
                    for string_name, segments in strings.items():
                        for segment in segments:
                            seg_id = segment.get('id')
                            status = "🟢 PRZYPISANY" if seg_id not in unassigned_ids else "🔴 NIEPRZYPISANY"
                            start = segment.get('start', [0, 0])
                            end = segment.get('end', [0, 0])
                            
                            content += f"{seg_id:<10} #{svg_number:<9} ({start[0]:.1f},{start[1]:.1f}){'':<8} ({end[0]:.1f},{end[1]:.1f}){'':<8} {status}\n"
                            svg_number += 1
            
            # Dodaj nieprzypisane segmenty (będą miały inne numery na SVG)
            for segment in self.unassigned_segments:
                seg_id = segment.get('id')
                start = segment.get('start', [0, 0])  
                end = segment.get('end', [0, 0])
                status = "🔴 NIEPRZYPISANY"
                
                content += f"{seg_id:<10} #{svg_number:<9} ({start[0]:.1f},{start[1]:.1f}){'':<8} ({end[0]:.1f},{end[1]:.1f}){'':<8} {status}\n"
                svg_number += 1
            
            content += "\n" + "=" * 80 + "\n"
            content += f"PODSUMOWANIE:\n"
            content += f"• Całkowita liczba segmentów: {len(self.all_segments)}\n"
            content += f"• Nieprzypisanych: {len(self.unassigned_segments)}\n"
            content += f"• Przypisanych: {len(self.all_segments) - len(self.unassigned_segments)}\n\n"
            content += "UWAGA: Numery 'Nr na SVG' to numeracja wyświetlana na rysunku SVG\n"
            content += "       (rozpoczyna się od #1 i rośnie globalnie)"
            
            scroll_text.insert('1.0', content)
            scroll_text.configure(state='disabled')
            
            # Przycisk zamknij
            ttk.Button(main_frame, text="Zamknij", command=map_window.destroy).pack(pady=5)
            
            self.log_message("Pokazano mapę numerów segmentów")
            
        except Exception as e:
            self.log_message(f"Błąd pokazywania mapy numerów: {e}", "ERROR")
            messagebox.showerror("Błąd", f"Nie można pokazać mapy numerów:\n{e}")
    
    def reload_data_fresh(self):
        """Załaduj dane od nowa (restart assignmentów)"""
        try:
            if not hasattr(self, 'last_conversion_data') or not self.last_conversion_data:
                messagebox.showwarning("Uwaga", "Brak danych do przeładowania. Wykonaj najpierw konwersję DXF.")
                return
            
            # Potwierdź reset
            if not messagebox.askyesno("Potwierdzenie", 
                                      "Czy na pewno chcesz zresetować wszystkie przypisania i zacząć od nowa?\n\nWszystkie niezapisane zmiany zostaną utracone!"):
                return
            
            # Resetuj dane do stanu początkowego
            self.assignment_changes = {'new_assignments': [], 'skipped_texts': []}
            
            # Przywróć oryginalne dane z konwersji
            original_data = self.last_conversion_data
            self.all_texts = original_data.get('station_texts', []).copy()
            self.unassigned_texts = original_data.get('unassigned_texts', []).copy()
            
            # Przypisane segmenty z assigned_data
            assigned_segments = []
            assigned_data = original_data.get('assigned_data', {})
            for inv_id, strings in assigned_data.items():
                for str_id, segments in strings.items():
                    if segments:
                        assigned_segments.extend(segments)
            
            self.all_segments = assigned_segments + original_data.get('unassigned_segments', [])
            self.unassigned_segments = original_data.get('unassigned_segments', []).copy()
            
            # Odśwież listy
            self.populate_texts_list()
            self.populate_segments_list()
            
            # Wyczyść wybory
            self.clear_selected_text()
            self.clear_selected_segment()
            
            # Wygeneruj SVG w stanie początkowym
            self.regenerate_and_refresh_svg()
            
            self.log_message("🔄 Dane przeładowane - wszystkie przypisania zresetowane")
            messagebox.showinfo("Sukces", "Dane zostały przeładowane. Wszystkie przypisania zresetowane.")
            
        except Exception as e:
            self.log_message(f"Błąd przeładowania danych: {e}", "ERROR")
            messagebox.showerror("Błąd", f"Nie można przeładować danych:\n{e}")
    
    def show_assignment_statistics(self):
        """Pokaż statystyki przypisań"""
        try:
            # Oblicz statystyki
            total_texts = len(self.all_texts) if hasattr(self, 'all_texts') else 0
            unassigned_texts = len(self.unassigned_texts) if hasattr(self, 'unassigned_texts') else 0
            assigned_texts = total_texts - unassigned_texts
            
            total_segments = len(self.all_segments) if hasattr(self, 'all_segments') else 0
            unassigned_segments = len(self.unassigned_segments) if hasattr(self, 'unassigned_segments') else 0
            assigned_segments = total_segments - unassigned_segments
            
            new_assignments = len(self.assignment_changes.get('new_assignments', []))
            skipped_texts = len(self.assignment_changes.get('skipped_texts', []))
            
            # Utwórz okno ze statystykami
            stats_window = tk.Toplevel(self.root)
            stats_window.title("Statystyki przypisań")
            stats_window.geometry("500x400")
            
            # Frame główny
            main_frame = ttk.Frame(stats_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Tytuł
            title_label = ttk.Label(main_frame, text="📊 STATYSTYKI PRZYPISAŃ", 
                                   style='Title.TLabel', font=('Arial', 16, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # Teksty
            texts_frame = ttk.LabelFrame(main_frame, text="Teksty", padding=10)
            texts_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(texts_frame, text=f"Wszystkich tekstów: {total_texts}", 
                     font=('Arial', 12)).pack(anchor=tk.W)
            ttk.Label(texts_frame, text=f"🟢 Przypisanych: {assigned_texts}", 
                     font=('Arial', 12), foreground='green').pack(anchor=tk.W)
            ttk.Label(texts_frame, text=f"🔴 Nieprzypisanych: {unassigned_texts}", 
                     font=('Arial', 12), foreground='red').pack(anchor=tk.W)
            
            if total_texts > 0:
                progress_texts = (assigned_texts / total_texts) * 100
                ttk.Label(texts_frame, text=f"Postęp: {progress_texts:.1f}%", 
                         font=('Arial', 12, 'bold')).pack(anchor=tk.W)
            
            # Segmenty
            segments_frame = ttk.LabelFrame(main_frame, text="Segmenty", padding=10)
            segments_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(segments_frame, text=f"Wszystkich segmentów: {total_segments}", 
                     font=('Arial', 12)).pack(anchor=tk.W)
            ttk.Label(segments_frame, text=f"🟢 Przypisanych: {assigned_segments}", 
                     font=('Arial', 12), foreground='green').pack(anchor=tk.W)
            ttk.Label(segments_frame, text=f"🔴 Nieprzypisanych: {unassigned_segments}", 
                     font=('Arial', 12), foreground='red').pack(anchor=tk.W)
            
            if total_segments > 0:
                progress_segments = (assigned_segments / total_segments) * 100
                ttk.Label(segments_frame, text=f"Postęp: {progress_segments:.1f}%", 
                         font=('Arial', 12, 'bold')).pack(anchor=tk.W)
            
            # Sesja
            session_frame = ttk.LabelFrame(main_frame, text="Bieżąca sesja", padding=10)
            session_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(session_frame, text=f"Nowych przypisań: {new_assignments}", 
                     font=('Arial', 12)).pack(anchor=tk.W)
            ttk.Label(session_frame, text=f"Pominiętych tekstów: {skipped_texts}", 
                     font=('Arial', 12)).pack(anchor=tk.W)
            
            # Przycisk zamknij
            ttk.Button(main_frame, text="Zamknij", command=stats_window.destroy).pack(pady=20)
            
            self.log_message("Pokazano statystyki przypisań")
            
        except Exception as e:
            self.log_message(f"Błąd pokazywania statystyk: {e}", "ERROR")
            messagebox.showerror("Błąd", f"Nie można pokazać statystyk:\n{e}")

    def on_auto_refresh_change(self):
        """Obsługa zmiany opcji auto-odświeżania SVG"""
        if self.auto_refresh_svg.get():
            self.log_message("🔄 Auto-odświeżanie SVG włączone - SVG będzie regenerowany po każdym przypisaniu")
        else:
            self.log_message("⚡ Auto-odświeżanie SVG wyłączone - szybsze przypisywanie, odśwież ręcznie")

    def save_assignment_data(self):
        """Automatyczne zapisywanie danych przypisań po każdej zmianie"""
        try:
            if not hasattr(self, 'last_conversion_data') or not self.assignment_changes['new_assignments']:
                return
            
            # Aktualizuj assigned_data z nowymi przypisaniami
            for assignment in self.assignment_changes['new_assignments']:
                text_data = assignment['text']
                segment_data = assignment['segment']
                text_id = text_data['id']
                
                # Znajdź lub utwórz odpowiedni inverter
                inverter_id = list(self.last_conversion_data['assigned_data'].keys())[0] if self.last_conversion_data['assigned_data'] else "I01"
                
                if inverter_id not in self.last_conversion_data['assigned_data']:
                    self.last_conversion_data['assigned_data'][inverter_id] = {}
                
                if text_id not in self.last_conversion_data['assigned_data'][inverter_id]:
                    self.last_conversion_data['assigned_data'][inverter_id][text_id] = []
                
                # Dodaj segment (unikaj duplikatów)
                segment_ids = [s.get('id') for s in self.last_conversion_data['assigned_data'][inverter_id][text_id]]
                if segment_data.get('id') not in segment_ids:
                    self.last_conversion_data['assigned_data'][inverter_id][text_id].append(segment_data)
            
            # Aktualizuj listy nieprzypisanych w danych
            self.last_conversion_data['unassigned_texts'] = self.unassigned_texts.copy()
            self.last_conversion_data['unassigned_segments'] = self.unassigned_segments.copy()
            
            self.log_message("💾 Dane przypisań zapisane automatycznie")
            
        except Exception as e:
            self.log_message(f"⚠️ Błąd automatycznego zapisywania: {e}", "ERROR")

    def generate_final_structured_svg(self):
        """Generuj finalny structured SVG z wszystkimi zmianami"""
        try:
            if not hasattr(self, 'last_conversion_data'):
                messagebox.showerror("Błąd", "Brak danych do generowania. Wykonaj najpierw konwersję DXF.")
                return
            
            # Pokaż dialog potwierdzenia
            structured_filename = self.config_manager.get('STRUCTURED_SVG_OUTPUT', 'output_structured.svg')
            result = messagebox.askyesno(
                "Generowanie Structured SVG", 
                f"Czy wygenerować finalny structured SVG z {len(self.assignment_changes['new_assignments'])} zmianami?\n\n" +
                f"Plik zostanie zapisany jako '{structured_filename}'"
            )
            
            if not result:
                return
            
            self.log_message("🔧 Generowanie finalnego structured SVG...")
            
            # WAŻNE: Upewnij się że config jest aktualny
            self.config_manager.apply_to_config_module()
            import src.core.config as config
            self.log_message(f"🔧 DEBUG: Aktualna wartość config.MPTT_HEIGHT = {config.MPTT_HEIGHT}")
            
            # Użyj aktualnych danych z wszystkimi zmianami (preferuj AssignmentManager)
            from src.svg.svg_generator import generate_structured_svg
            
            if hasattr(self, 'assignment_manager') and self.assignment_manager:
                # Użyj danych z AssignmentManager (najaktualniejsze)
                current_assigned_data = self.assignment_manager.current_assigned_data
                current_unassigned_texts = self.assignment_manager.unassigned_texts
                current_unassigned_segments = self.assignment_manager.unassigned_segments
                self.log_message("📊 Używam danych z AssignmentManager")
            else:
                # Fallback do danych GUI
                current_assigned_data = self.assigned_data if hasattr(self, 'assigned_data') else self.last_conversion_data['assigned_data']
                current_unassigned_texts = self.unassigned_texts
                current_unassigned_segments = self.unassigned_segments
                self.log_message("📊 Używam danych z GUI")
            
            # Pobierz konfigurację dla station_id
            config_params = self.get_dxf_config_params()
            station_id = config_params.get('STATION_ID')
            
            generate_structured_svg(
                current_assigned_data,                        # NAJAKTUALNIEJSZE dane!
                self.last_conversion_data['station_texts'],   # wszystkie teksty stacji
                current_unassigned_texts,                     # aktualne nieprzypisane teksty
                current_unassigned_segments,                  # aktualne nieprzypisane segmenty
                structured_filename,                          # konfigurowalna nazwa pliku
                station_id                                    # ID stacji
            )
            
            self.log_message(f"✅ Finalny structured SVG wygenerowany: {structured_filename}")
            messagebox.showinfo("Sukces", f"Finalny structured SVG został wygenerowany!\n\nPlik: {structured_filename}")
            
            # Zapytaj czy przełączyć widok
            if messagebox.askyesno("Przełączyć widok?", "Czy chcesz przełączyć widok na structured SVG?"):
                self.current_svg_path.set(structured_filename)
                self.current_display_mode.set("structured")
                self.change_display_mode()
            
        except Exception as e:
            self.log_message(f"❌ Błąd generowania structured SVG: {e}", "ERROR")
            messagebox.showerror("Błąd", f"Nie można wygenerować structured SVG:\n{e}")

    def save_assignments(self):
        """Zapisanie zmian przypisań"""
        try:
            if not self.assignment_changes['new_assignments']:
                self.log_message("Brak zmian do zapisania")
                return
            
            # Pokaż podsumowanie zmian
            changes_count = len(self.assignment_changes['new_assignments'])
            confirm_msg = f"Czy zapisać {changes_count} nowych przypisań?\n\n"
            
            for i, assignment in enumerate(self.assignment_changes['new_assignments']):  # Pokaż wszystkie
                text_id = assignment['text']['id']
                segment_id = assignment['segment']['id']
                confirm_msg += f"• {text_id} → Segment #{segment_id}\n"
            
            if changes_count > 5:
                confirm_msg += f"... i {changes_count - 5} więcej"
            
            if not messagebox.askyesno("Potwierdzenie", confirm_msg):
                return
            
            self.log_message(f"Zapisywanie {changes_count} zmian przypisań...")
            
            # Pobierz dane z ostatniej konwersji
            assigned_data = self.last_conversion_data.get('assigned_data', {})
            station_texts = self.last_conversion_data.get('station_texts', [])
            
            # Zastosuj nowe przypisania
            for assignment in self.assignment_changes['new_assignments']:
                text_data = assignment['text']
                segment_data = assignment['segment']
                
                # Znajdź odpowiedni inverter (używamy pierwszego dostępnego)
                inverter_id = list(assigned_data.keys())[0] if assigned_data else "I01"
                if inverter_id not in assigned_data:
                    assigned_data[inverter_id] = {}
                
                # Dodaj segment do stringa tekstowego
                text_id = text_data['id']
                if text_id not in assigned_data[inverter_id]:
                    assigned_data[inverter_id][text_id] = []
                
                assigned_data[inverter_id][text_id].append(segment_data)
                self.log_message(f"Przypisano segment #{segment_data['id']} do {text_id}")
            
            # Regeneruj SVG z nowymi przypisaniami
            from src.svg.svg_generator import generate_interactive_svg
            
            # Pobierz aktualnie nieprzypisane elementy
            remaining_unassigned_texts = []
            for text in self.unassigned_texts:
                # Sprawdź czy nie został przypisany
                is_assigned = any(a['text']['id'] == text['id'] for a in self.assignment_changes['new_assignments'])
                if not is_assigned:
                    remaining_unassigned_texts.append(text)
            
            remaining_unassigned_segments = []
            for segment in self.unassigned_segments:
                # Sprawdź czy nie został przypisany
                is_assigned = any(a['segment']['id'] == segment['id'] for a in self.assignment_changes['new_assignments'])
                if not is_assigned:
                    remaining_unassigned_segments.append(segment)
            
            # Pobierz konfigurację dla station_id
            config_params = self.get_dxf_config_params()
            station_id = config_params.get('STATION_ID')
            
            # Wygeneruj nowy SVG
            output_svg = "interactive_assignment.svg"
            generate_interactive_svg(
                assigned_data, 
                station_texts, 
                remaining_unassigned_texts, 
                remaining_unassigned_segments, 
                output_svg,
                station_id
            )
            
            # Walidacja wygenerowanego pliku
            try:
                if not os.path.exists(output_svg) or os.path.getsize(output_svg) < 20:
                    self.log_error(f"Interaktywny SVG nie został wygenerowany poprawnie: {output_svg}")
                else:
                    with open(output_svg, 'rb') as f:
                        head = f.read(4096)
                    if b'<svg' not in head.lower():
                        self.log_error(f"Wygenerowany plik nie zawiera <svg>: {output_svg}")
            except Exception as ve:
                self.log_error(f"Walidacja SVG nie powiodła się: {ve}")
            
            # Odśwież widok
            self.refresh_svg()
            
            # Wyczyść zmiany po zapisaniu
            self.assignment_changes = {'new_assignments': [], 'skipped_texts': []}
            
            # Zaktualizuj listy nieprzypisanych elementów
            self.unassigned_texts = remaining_unassigned_texts
            self.unassigned_segments = remaining_unassigned_segments
            
            self.log_message(f"✅ Zapisano {changes_count} zmian i zaktualizowano SVG")
            messagebox.showinfo("Sukces", f"Zapisano {changes_count} przypisań")
            
        except Exception as e:
            self.log_message(f"Błąd zapisywania: {e}", "ERROR")
            messagebox.showerror("Błąd", f"Nie można zapisać zmian:\\n{e}")
    
    def get_selected_text_id(self):
        """Get currently selected text ID"""
        if self.stored_text_data:
            return self.stored_text_data.get('id')
        return None
    
    def get_selected_segment_id(self):
        """Get currently selected segment ID"""
        if self.stored_segment_data:
            return self.stored_segment_data.get('id')
        return None
    
    def refresh_texts_and_segments_lists(self):
        """Refresh both text and segment lists"""
        self.populate_texts_list()
        self.populate_segments_list()
    
    def select_listbox_item_by_id(self, listbox, items_list, id_field, search_value):
        """Zaznacz element w listbox na podstawie ID"""
        try:
            # Posortuj liste tak samo jak przy wypelnianiu
            if items_list == self.all_texts:
                sorted_items = sorted(items_list, key=lambda x: x.get(id_field, ''))
            else:  # segments
                sorted_items = sorted(items_list, key=lambda x: x.get(id_field, 0))
            
            # Znajdz index elementu
            for idx, item in enumerate(sorted_items):
                if item.get(id_field) == search_value:
                    # Wyczysc poprzednie zaznaczenie
                    listbox.selection_clear(0, tk.END)
                    # Zaznacz nowy element
                    listbox.selection_set(idx)
                    # Przewin do elementu
                    listbox.see(idx)
                    
                    # Ustaw odpowiedni index
                    if listbox == self.texts_listbox:
                        self.selected_text_index = idx
                    else:
                        self.selected_segment_index = idx
                    
                    return True
            
            self.log_warning(f"Nie znaleziono elementu o ID: {search_value}")
            return False
            
        except Exception as e:
            self.log_error(f"Blad zaznaczania elementu: {e}")
            return False
    
    # Metody pomocnicze
    def log_message(self, message, level="INFO"):
        """Dodanie wiadomości do loga z kolorami i obsługą \\n"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Zamień \\n na prawdziwe znaki nowej linii
        formatted_message = message.replace('\\n', '\n')
        
        # Definiuj kolory dla różnych poziomów
        colors = {
            "INFO": "blue",
            "SUCCESS": "green", 
            "WARNING": "orange",
            "ERROR": "red",
            "DEBUG": "gray"
        }
        
        color = colors.get(level, "black")
        
        # Dodaj timestamp i poziom
        log_entry = f"[{timestamp}] {level}: {formatted_message}\n"
        
        # Dodaj tekst z kolorem
        current_pos = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, log_entry)
        
        # Ustaw kolor tylko dla tej linii
        line_start = current_pos
        line_end = self.log_text.index(tk.END)
        
        # Utwórz tag z kolorem jeśli nie istnieje
        tag_name = f"color_{level}"
        self.log_text.tag_configure(tag_name, foreground=color)
        self.log_text.tag_add(tag_name, line_start, line_end)
        
        self.log_text.see(tk.END)
        
        # Ogranicz liczbę linii w logu
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:  # Zwiększono limit do 1000
            self.log_text.delete("1.0", "50.0")  # Usuń 50 linii na raz
    
    def log_success(self, message):
        """Wiadomość sukcesu"""
        self.log_message(message, "SUCCESS")
    
    def log_warning(self, message):
        """Wiadomość ostrzeżenia"""
        self.log_message(message, "WARNING")
    
    def log_error(self, message):
        """Wiadomość błędu"""
        # Usuń emoji jeśli nie mogą być wyświetlone w konsoli Windows
        try:
            self.log_message(message, "ERROR")
        except UnicodeEncodeError:
            # Usuń wszystkie znaki Unicode które nie są ASCII
            clean_message = message.encode('ascii', 'ignore').decode('ascii')
            self.log_message(clean_message, "ERROR")
    
    def load_default_files(self):
        """Ładowanie domyślnych plików"""
        # Sprawdź domyślny plik DXF z konfiguracji
        default_dxf = self.config_manager.get('DEFAULT_DXF_FILE', 'input.dxf')
        if os.path.exists(default_dxf):
            self.current_dxf_path.set(os.path.abspath(default_dxf))
            self.log_message(f"Załadowano domyślny plik DXF: {default_dxf}")
        
        # Ustaw domyślny plik SVG z konfiguracji
        default_svg = self.config_manager.get('STRUCTURED_SVG_OUTPUT', 'output_structured.svg')
        self.current_svg_path.set(default_svg)
        
        # Sprawdź domyślny plik SVG i ustaw tryb wyświetlania
        self.change_display_mode()
        
        # Sprawdź czy istnieją pliki z poprzednich konwersji
        self.update_interactive_info()
    
    def run(self):
        """Uruchomienie GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\\n⚠️ Przerwano przez użytkownika")
        except Exception as e:
            try:
                print(f"❌ Błąd GUI: {e}")
            except UnicodeEncodeError:
                print(f"[ERROR] Błąd GUI: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    # Obsługa argumentów wiersza poleceń
    parser = argparse.ArgumentParser(description='DXF2SVG Interactive GUI')
    parser.add_argument('--config', '-c', type=str, help='Nazwa pliku konfiguracyjnego (bez rozszerzenia .cfg)')
    args = parser.parse_args()
    
    # Uruchom aplikację z opcjonalną konfiguracją
    app = InteractiveGUI(config_file=args.config)
    app.run()
