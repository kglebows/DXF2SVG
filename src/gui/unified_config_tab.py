#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zunifikowana zakładka konfiguracji - łączy pliki, formatowanie i wszystkie parametry
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from typing import Dict, Any, Callable
from src.config.config_manager import ConfigManager


# ============================================================================
# GLOBALNE STAŁE DLA ZAOKRĄGLEŃ I ODSTĘPÓW (zsynchronizowane z interactive_gui_new.py)
# ============================================================================
CORNER_RADIUS = 32          # Promień zaokrągleń dla wszystkich elementów
LAYER_SPACING = 0           # Odstęp między warstwami (0 = bezpośredni kontakt)
CONTENT_PADDING = 0         # Padding wewnętrzny dla contentu (0 = od krawędzi zaokrągleń)
TAB_SPACING = 16            # Odstęp między nazwami zakładek a warstwą 1 (połowa CORNER_RADIUS)
ELEMENT_SPACING = 16        # Odstęp canvas_inner od krawędzi (połowa CORNER_RADIUS)
BORDER_RADIUS = CORNER_RADIUS  # Backwards compatibility
# ============================================================================


def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=None, **kwargs):
    """Rysuje zaokrąglony prostokąt na canvas"""
    if radius is None:
        radius = BORDER_RADIUS
    points = [
        x1+radius, y1,
        x2-radius, y1,
        x2, y1,
        x2, y1+radius,
        x2, y2-radius,
        x2, y2,
        x2-radius, y2,
        x1+radius, y2,
        x1, y2,
        x1, y2-radius,
        x1, y1+radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# Definicje wszystkich parametrów konfiguracji
CONFIG_PARAMETERS = {
    # Sekcja: Warstwy DXF (POŁĄCZONE - nazwy + wymagania)
    'layers': {
        'title': 'Warstwy DXF',
        'collapsible': False,  # NIE rozwijalne
        'params': {
            'LAYER_LINE': {
                'label': 'Warstwa linii',
                'type': 'string',
                'default': '@IDE_KABLE_DC_B',
                'description': 'Nazwa warstwy zawierającej polilinie reprezentujące segmenty stringów. Muszą to być obiekty typu LWPOLYLINE lub POLYLINE.',
                'validation': lambda x: len(x) > 0
            },
            'LAYER_TEXT': {
                'label': 'Warstwa tekstów',
                'type': 'string',
                'default': '@IDE_KABLE_DC_TXT_B',
                'description': 'Nazwa warstwy zawierającej teksty z identyfikatorami. Muszą to być obiekty typu MTEXT lub TEXT.',
                'validation': lambda x: len(x) > 0
            }
        }
    },
    
    # Sekcja: Przetwarzanie segmentów
    'processing': {
        'title': 'Opcje przetwarzania segmentów',
        'collapsible': True,  # Rozwijalne
        'collapsed': True,  # Domyślnie zwinięte
        'params': {
            'POLYLINE_PROCESSING_MODE': {
                'label': 'Tryb przetwarzania polilinii',
                'type': 'choice',
                'choices': ['individual_segments', 'merge_segments'],
                'default': 'individual_segments',
                'description': 'individual_segments: każdy odcinek polilinii jako osobny segment. merge_segments: łączy blisko siebie położone segmenty.',
                'validation': None
            },
            'SEGMENT_MERGE_GAP_TOLERANCE': {
                'label': 'Tolerancja przerw (merge)',
                'type': 'float',
                'default': 1.0,
                'description': 'Maksymalna szerokość przerwy między segmentami do automatycznego połączenia (tryb merge_segments).',
                'validation': lambda x: x >= 0
            },
            'MAX_MERGE_DISTANCE': {
                'label': 'Maks. odległość łączenia',
                'type': 'float',
                'default': 5.0,
                'description': 'Maksymalna odległość między punktami końcowymi segmentów dla łączenia.',
                'validation': lambda x: x >= 0
            }
        }
    },
    
    # Sekcja: Przypisywanie automatyczne
    'assignment': {
        'title': 'Parametry przypisywania automatycznego',
        'collapsible': True,  # Rozwijalne
        'collapsed': True,  # Domyślnie zwinięte
        'params': {
            'TEXT_LOCATION': {
                'label': 'Lokalizacja tekstów',
                'type': 'choice',
                'choices': ['above', 'below', 'any'],
                'default': 'above',
                'description': 'Gdzie szukać tekstów względem segmentów: above (powyżej), below (poniżej), any (dowolnie).',
                'validation': None
            },
            'SEARCH_RADIUS': {
                'label': 'Promień wyszukiwania',
                'type': 'float',
                'default': 6.0,
                'description': 'Promień w jednostkach DXF dla wyszukiwania tekstów wokół segmentów.',
                'validation': lambda x: x > 0
            },
            'MAX_DISTANCE': {
                'label': 'Maksymalna odległość',
                'type': 'float',
                'default': 10.0,
                'description': 'Maksymalna odległość między tekstem a segmentem dla automatycznego przypisania.',
                'validation': lambda x: x > 0
            },
            'X_TOLERANCE': {
                'label': 'Tolerancja X',
                'type': 'float',
                'default': 0.01,
                'description': 'Tolerancja położenia w osi X dla dopasowywania elementów.',
                'validation': lambda x: x >= 0
            },
            'Y_TOLERANCE': {
                'label': 'Tolerancja Y',
                'type': 'float',
                'default': 0.01,
                'description': 'Tolerancja położenia w osi Y dla dopasowywania elementów.',
                'validation': lambda x: x >= 0
            }
        }
    },
    
    # Sekcja: Wizualizacja SVG
    'visualization': {
        'title': 'Parametry wizualizacji',
        'collapsible': True,  # Rozwijalne
        'collapsed': True,  # Domyślnie zwinięte
        'params': {
            'SVG_WIDTH': {
                'label': 'Szerokość SVG (px)',
                'type': 'int',
                'default': 1600,
                'description': 'Szerokość generowanego pliku SVG w pikselach.',
                'validation': lambda x: x > 0
            },
            'SVG_HEIGHT': {
                'label': 'Wysokość SVG (px)',
                'type': 'int',
                'default': 800,
                'description': 'Wysokość generowanego pliku SVG w pikselach.',
                'validation': lambda x: x > 0
            },
            'MARGIN': {
                'label': 'Margines SVG',
                'type': 'float',
                'default': 2.0,
                'description': 'Margines wokół zawartości SVG.',
                'validation': lambda x: x >= 0
            },
            'CLUSTER_DISTANCE_THRESHOLD': {
                'label': 'Próg odległości klastra',
                'type': 'float',
                'default': 300.0,
                'description': 'Odległość dla wykrywania outlierów - elementy dalej niż ta wartość są pomijane.',
                'validation': lambda x: x > 0
            }
        }
    },
    
    # Sekcja: Wygląd elementów
    'appearance': {
        'title': 'Wygląd elementów SVG',
        'collapsible': True,  # Rozwijalne
        'collapsed': True,  # Domyślnie zwinięte
        'params': {
            'MPTT_HEIGHT': {
                'label': 'Grubość linii segmentów',
                'type': 'float',
                'default': 1.0,
                'description': 'Grubość linii reprezentujących segmenty stringów.',
                'validation': lambda x: x > 0
            },
            'SEGMENT_MIN_WIDTH': {
                'label': 'Min. szerokość segmentu',
                'type': 'float',
                'default': 0.0,
                'description': 'Minimalna szerokość segmentu do wyświetlenia.',
                'validation': lambda x: x >= 0
            },
            'DOT_RADIUS': {
                'label': 'Promień kropek',
                'type': 'float',
                'default': 0.25,
                'description': 'Promień kropek oznaczających środki i pozycje tekstów.',
                'validation': lambda x: x > 0
            },
            'TEXT_SIZE': {
                'label': 'Rozmiar tekstu',
                'type': 'float',
                'default': 1.0,
                'description': 'Rozmiar czcionki dla etykiet w SVG.',
                'validation': lambda x: x > 0
            },
            'TEXT_OPACITY': {
                'label': 'Przezroczystość tekstu',
                'type': 'float',
                'default': 0.5,
                'description': 'Przezroczystość etykiet tekstowych (0.0 - 1.0).',
                'validation': lambda x: 0 <= x <= 1
            },
            'STRING_LABEL_OFFSET': {
                'label': 'Offset etykiet',
                'type': 'float',
                'default': 0.0,
                'description': 'Przesunięcie etykiet stringów względem ich pozycji.',
                'validation': None
            }
        }
    },
    
    # Sekcja: Opcje edytora interaktywnego
    'editor_options': {
        'title': 'Opcje edytora przypisań',
        'collapsible': True,  # Rozwijalne
        'collapsed': True,  # Domyślnie zwinięte
        'params': {
            # Toggle wyświetlania
            'SHOW_ELEMENT_POINTS': {
                'label': 'Pokazuj pozycje punktowe elementów',
                'type': 'bool',
                'default': False,
                'description': 'Pokazuj wszystkie kropki (segmenty) i trójkąty (teksty) elementów.',
                'validation': None
            },
            'SHOW_UNASSIGNED_SEGMENT_LABELS': {
                'label': 'Pokazuj numery segmentów nieprzypisanych',
                'type': 'bool',
                'default': True,
                'description': 'Czy pokazywać numery (#1, #2, etc.) przy nieprzypisanych segmentach.',
                'validation': None
            },
            'SHOW_ASSIGNED_SEGMENT_LABELS': {
                'label': 'Pokazuj numery segmentów przypisanych',
                'type': 'bool',
                'default': True,
                'description': 'Czy pokazywać numery (#1, #2, etc.) przy przypisanych segmentach.',
                'validation': None
            },
            
            # Kolory segmentów
            'ASSIGNED_SEGMENT_COLOR': {
                'label': 'Kolor segmentu przypisanego',
                'type': 'color',
                'default': '#00778B',
                'description': 'Kolor linii dla segmentów które mają przypisane teksty.',
                'validation': lambda x: x.startswith('#') and len(x) == 7
            },
            'UNASSIGNED_SEGMENT_COLOR': {
                'label': 'Kolor segmentu nieprzypisanego',
                'type': 'color',
                'default': '#FFC0CB',
                'description': 'Kolor linii dla segmentów bez przypisanych tekstów.',
                'validation': lambda x: x.startswith('#') and len(x) == 7
            },
            'SELECTED_SEGMENT_COLOR': {
                'label': 'Kolor segmentu zaznaczonego',
                'type': 'color',
                'default': '#FFFF00',
                'description': 'Kolor segmentu po kliknięciu/zaznaczeniu.',
                'validation': lambda x: x.startswith('#') and len(x) == 7
            },
            'HOVER_SEGMENT_COLOR': {
                'label': 'Kolor grupy segmentów (hover)',
                'type': 'color',
                'default': '#FFB6C1',
                'description': 'Kolor segmentów grupy przypisanej podczas najechania myszką.',
                'validation': lambda x: x.startswith('#') and len(x) == 7
            },
            
            # Kolory tekstów
            'TEXT_COLOR_ASSIGNED': {
                'label': 'Kolor tekstu przypisanego',
                'type': 'color',
                'default': '#00FF15',
                'description': 'Kolor dla przypisanych tekstów.',
                'validation': lambda x: x.startswith('#') and len(x) == 7
            },
            'TEXT_COLOR_UNASSIGNED': {
                'label': 'Kolor tekstu nieprzypisanego',
                'type': 'color',
                'default': '#FF0000',
                'description': 'Kolor dla nieprzypisanych tekstów.',
                'validation': lambda x: x.startswith('#') and len(x) == 7
            },
            'SELECTED_TEXT_COLOR': {
                'label': 'Kolor tekstu zaznaczonego',
                'type': 'color',
                'default': '#00FFFF',
                'description': 'Kolor tekstu po kliknięciu/zaznaczeniu.',
                'validation': lambda x: x.startswith('#') and len(x) == 7
            },
            'HOVER_TEXT_COLOR': {
                'label': 'Kolor tekstu grupy (hover)',
                'type': 'color',
                'default': '#8B008B',
                'description': 'Kolor tekstów grupy przypisanej podczas najechania myszką.',
                'validation': lambda x: x.startswith('#') and len(x) == 7
            }
        }
    }
}


class UnifiedConfigTab(tk.Frame):
    """Zunifikowana zakładka konfiguracji z wszystkimi parametrami"""
    
    def __init__(self, parent, config_manager: ConfigManager, on_convert_callback: Callable = None, main_app=None):
        # Kolory - MUSI BYĆ PRZED super().__init__
        self.colors = {
            'bg': '#0d0d0d',           # Warstwa 0 - najciemniejsza (tło główne)
            'layer1_bg': '#1a1a1a',    # Warstwa 1 - tło zakładek
            'layer2_bg': '#2d2d2d',    # Warstwa 2 - tło kart/sekcji
            'layer3_bg': '#3a3a3a',    # Warstwa 3 - tło tooltipów
            'card_bg': '#2d2d2d',      # Alias dla kompatybilności
            'card_hover': '#3a3a3a',   # Hover
            'input_bg': '#252525',     # Tło pól tekstowych
            'button_bg': '#3a3a3a',    # Tło przycisków
            'accent': '#4a9eff',       # Kolor akcentu
            'accent_hover': '#6bb3ff', # Hover na akcentach
            'text': '#e0e0e0',         # Główny kolor tekstu
            'text_dim': '#a0a0a0',     # Przyciemniony tekst
            'success': '#4caf50',      # Zielony (sukces)
            'warning': '#ff9800',      # Pomarańczowy (ostrzeżenie)
            'border': '#404040',       # Kolor ramek
        }
        
        super().__init__(parent, bg=self.colors['bg'])  # tk.Frame z czarnym tłem
        
        self.config_manager = config_manager
        self.on_convert_callback = on_convert_callback
        self.main_app = main_app  # Referencja do głównego okna aplikacji (InteractiveGUI)
        
        # Referencja do root window (potrzebna dla option_add)
        self.root = self.winfo_toplevel()
        
        # Słowniki przechowujące zmienne Tkinter dla pól
        self.field_vars: Dict[str, tk.Variable] = {}
        self.advanced_formula_vars: Dict[str, tk.StringVar] = {}
        
        # NOWA STRUKTURA: Lista formatowań (każde z własną konfiguracją)
        self.text_formats = []  # Lista słowników z formatowaniami
        self.format_frames = []  # Lista frame'ów GUI dla każdego formatowania
        self.canvas_draw_functions = []  # Lista funkcji rysujących Canvas (dla odświeżania)
        
        # Zmienne dla plików
        self.dxf_file_var = tk.StringVar()
        self.svg_file_var = tk.StringVar(value="output_interactive.svg")
        
        self.setup_styles()
        self.create_ui()
    
    def setup_styles(self):
        """Konfiguracja stylów dla ciemnego motywu z warstwami (bez ramek)"""
        style = ttk.Style()
        
        # Ustaw ciemny motyw jako bazę
        style.configure('TFrame', background=self.colors['layer1_bg'])
        
        # Styl dla ramek (Bento Box) - BEZ RAMEK
        style.configure('Card.TFrame', 
                       background=self.colors['layer2_bg'],
                       relief=tk.FLAT,
                       borderwidth=0)
        
        # Styl dla labelframe (karty z tytułem) - BEZ RAMEK
        style.configure('Card.TLabelframe',
                       background=self.colors['layer2_bg'],
                       foreground=self.colors['text'],
                       borderwidth=0,
                       relief=tk.FLAT)
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['layer2_bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Styl dla etykiet
        style.configure('Card.TLabel',
                       background=self.colors['layer2_bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9))
        
        style.configure('Dim.TLabel',
                       background=self.colors['layer2_bg'],
                       foreground=self.colors['text_dim'],
                       font=('Segoe UI', 8))
        
        style.configure('Header.TLabel',
                       background=self.colors['layer2_bg'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 11, 'bold'))
        
        # Styl dla przycisków
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9, 'bold'))
        
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent'])],
                 foreground=[('active', 'white')])
        
        # Styl dla combobox - BEZ RAMEK ale z działającym polem
        # NIE używamy pustego layoutu bo ukrywa pole!
        style.configure('Card.TCombobox',
                       fieldbackground=self.colors['input_bg'],
                       background=self.colors['button_bg'],
                       foreground=self.colors['text'],
                       borderwidth=0,
                       relief=tk.FLAT,
                       arrowcolor=self.colors['text'],
                       insertcolor=self.colors['text'],
                       highlightthickness=0)
        style.map('Card.TCombobox',
                 fieldbackground=[('readonly', self.colors['input_bg'])],
                 foreground=[('readonly', self.colors['text'])],
                 selectbackground=[('readonly', self.colors['accent'])],
                 selectforeground=[('readonly', 'white')])
        
        # Poprawka dla Combobox dropdown (lista rozwijana) - BEZ RAMEK
        self.root.option_add('*TCombobox*Listbox.background', self.colors['input_bg'])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors['text'])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors['accent'])
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'white')
        # USUŃ RAMKI Z DROPDOWN LIST - wszystkie możliwe sposoby
        self.root.option_add('*TCombobox*Listbox.borderWidth', '0')
        self.root.option_add('*TCombobox*Listbox.highlightThickness', '0')
        self.root.option_add('*TCombobox*Listbox.relief', 'flat')
        # Dodatkowe opcje dla popupu
        self.root.option_add('*TCombobox*Listbox*borderWidth', '0')
        self.root.option_add('*TCombobox*Listbox*highlightThickness', '0')
        self.root.option_add('*TCombobox.popdownFrame.borderWidth', '0')
        self.root.option_add('*TCombobox.popdownFrame.highlightThickness', '0')
        # Dla samego combobox
        style.configure('Card.TCombobox',
                       highlightthickness=0,
                       borderwidth=0)
        
        # Styl dla checkbutton
        style.configure('Card.TCheckbutton',
                       background=self.colors['layer2_bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9))
        
        # Styl dla scrollbar - MINIMALISTYCZNY, cienki, zaokrąglony, BEZ STRZAŁEK
        style.configure('Vertical.TScrollbar',
                       background=self.colors['layer2_bg'],
                       troughcolor=self.colors['layer1_bg'],
                       borderwidth=0,
                       arrowsize=0,  # Usuń strzałki
                       width=8,  # Cienki
                       relief=tk.FLAT)
        style.map('Vertical.TScrollbar',
                 background=[('active', self.colors['accent']),
                           ('!active', self.colors['layer2_bg'])],
                 arrowcolor=[('active', self.colors['layer1_bg'])])  # Ukryj strzałki
        
        # Layout bez strzałek
        style.layout('Vertical.TScrollbar', [
            ('Vertical.Scrollbar.trough', {
                'children': [
                    ('Vertical.Scrollbar.thumb', {
                        'expand': '1',
                        'sticky': 'nswe'
                    })
                ],
                'sticky': 'ns'
            })
        ])
        
        # Styl dla progressbar - ciemny akcent ZAOKRĄGLONY
        style.configure('TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['layer2_bg'],
                       borderwidth=0,
                       thickness=8,
                       relief=tk.FLAT)
        
    def create_ui(self):
        """Tworzy interfejs użytkownika z ciemnym motywem (warstwa 1)
        Używa globalnych stałych: CORNER_RADIUS, LAYER_SPACING, TAB_SPACING, ELEMENT_SPACING
        """
        # Padding frame - TAB_SPACING jako odstęp od nazw zakładek
        padding_frame = tk.Frame(self, bg=self.colors['bg'])
        padding_frame.pack(fill=tk.BOTH, expand=True, 
                          padx=LAYER_SPACING, pady=(TAB_SPACING, LAYER_SPACING))
        
        # Border canvas dla zaokrąglonego tła
        border_canvas = tk.Canvas(padding_frame, bg=self.colors['bg'],
                                 highlightthickness=0, borderwidth=0)
        border_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Funkcja rysująca zaokrąglony prostokąt
        def round_rectangle(x1, y1, x2, y2, r=25, **kwargs):
            points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1,
                     x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2,
                     x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2,
                     x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
            return border_canvas.create_polygon(points, **kwargs, smooth=True)
        
        # Rysuj zaokrąglone tło używając globalnego CORNER_RADIUS
        def draw_rounded_bg(event=None):
            border_canvas.delete('bg')
            w = border_canvas.winfo_width()
            h = border_canvas.winfo_height()
            if w > 1 and h > 1:
                round_rectangle(0, 0, w, h, r=CORNER_RADIUS,
                              fill=self.colors['layer1_bg'],
                              outline='', tags='bg')
                border_canvas.lower('bg')
        
        border_canvas.bind('<Configure>', draw_rounded_bg)
        
        # Canvas_inner: PRZESUNIĘTY o ELEMENT_SPACING (16px) od każdej strony aby pokazać zaokrąglenia
        canvas_inner = tk.Frame(border_canvas, bg=self.colors['layer1_bg'])
        border_canvas.create_window(ELEMENT_SPACING, ELEMENT_SPACING, 
                                    window=canvas_inner, anchor='nw', tags='inner')
        
        # Content frame bez paddingu
        content_frame = tk.Frame(canvas_inner, bg=self.colors['layer1_bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Aktualizuj rozmiar canvas_inner - mniejszy o 2*ELEMENT_SPACING (z każdej strony)
        def update_size(event=None):
            w = border_canvas.winfo_width()
            h = border_canvas.winfo_height()
            if w > 2*ELEMENT_SPACING and h > 2*ELEMENT_SPACING:
                border_canvas.itemconfig('inner', width=w-2*ELEMENT_SPACING, height=h-2*ELEMENT_SPACING)
        
        border_canvas.bind('<Configure>', lambda e: (draw_rounded_bg(e), update_size(e)))
        
        # Główny scrollable container - CZARNE TŁO dla całej zawartości
        main_canvas = tk.Canvas(content_frame, borderwidth=0, highlightthickness=0, 
                               bg=self.colors['layer1_bg'], 
                               highlightbackground=self.colors['layer1_bg'])
        self.scrollable_frame = tk.Frame(main_canvas, bg=self.colors['layer1_bg'])
        
        # Create window at (0,0) and track changes
        canvas_window = main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def on_frame_configure(event=None):
            # Update scroll region NAJPIERW
            main_canvas.update_idletasks()  # Upewnij się że layout jest gotowy
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            
            # Check if scrollbar is needed
            canvas_height = main_canvas.winfo_height()
            content_height = self.scrollable_frame.winfo_reqheight()
            if content_height > canvas_height:
                # Need scrollbar
                if not hasattr(self, 'scrollbar_visible') or not self.scrollbar_visible:
                    self.scrollbar.pack(side="right", fill="y")
                    self.scrollbar_visible = True
            else:
                # Don't need scrollbar
                if hasattr(self, 'scrollbar_visible') and self.scrollbar_visible:
                    self.scrollbar.pack_forget()
                    self.scrollbar_visible = False
        
        self.scrollable_frame.bind("<Configure>", on_frame_configure)
        
        # Scrollbar - initially hidden, CIEMNY kolor
        self.scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=main_canvas.yview,
                                      style='Vertical.TScrollbar')
        main_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar_visible = False
        
        # Layout - only canvas initially
        main_canvas.pack(side="left", fill="both", expand=True)
        
        # INTELIGENTNE scrollowanie - tylko gdy zawartość jest większa niż widok
        def smart_scroll(event):
            # Sprawdź czy zawartość jest większa niż canvas
            canvas_height = main_canvas.winfo_height()
            content_height = self.scrollable_frame.winfo_reqheight()
            
            if content_height > canvas_height:
                # Scrolluj tylko jeśli zawartość się nie mieści
                main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                
                # Zapobiegaj scrollowaniu poza zakres
                current_view = main_canvas.yview()
                if current_view[0] < 0:
                    main_canvas.yview_moveto(0)
                elif current_view[1] > 1:
                    main_canvas.yview_moveto(1.0 - (current_view[1] - current_view[0]))
        
        self.scrollable_frame.bind_all("<MouseWheel>", smart_scroll)
        
        # Upewnij się że scrollowanie zaczyna się od góry
        main_canvas.yview_moveto(0)
        
        # Przechowaj referencję do canvas dla późniejszego użycia
        self.main_canvas = main_canvas
        
        # Zawartość
        self.create_header()
        self.create_formatting_section()
        self.create_files_section()
        self.create_parameters_sections()
        self.create_action_buttons()
        
        # Zaplanuj dynamiczne dostosowanie szerokości panelu z retry mechanism
        def try_adjust(attempt=0):
            if attempt < 5:  # Maksymalnie 5 prób
                try:
                    self.adjust_panel_width()
                except Exception as e:
                    print(f"⚠️ Próba {attempt+1} dostosowania szerokości nie powiodła się: {e}")
                    self.after(200, lambda: try_adjust(attempt + 1))
            else:
                print("⚠️ Nie udało się dostosować szerokości panelu po 5 próbach")
        
        self.after(500, lambda: try_adjust(0))  # Zwiększone opóźnienie do 500ms
        
    def create_header(self):
        """Nagłówek z wyborem konfiguracji - kompaktowy w jednej linii"""
        card = self.create_bento_card(self.scrollable_frame, None)  # Bez tytułu
        # BEZ dodatkowego paddingu - CORNER_RADIUS już zapewnia odstęp
        # card.master.master.pack_configure(pady=(0, 3))  # Usunięto dodatkowy padding
        
        # Wszystko w jednej linii
        row = tk.Frame(card, bg=self.colors['layer2_bg'])
        row.pack(fill=tk.X)
        
        self.config_combo_var = tk.StringVar(value=self.config_manager.current_config_name)
        
        # Combobox BEZ RAMKI
        combo_frame = tk.Frame(row, bg=self.colors['input_bg'])
        combo_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        self.config_combo = ttk.Combobox(combo_frame, textvariable=self.config_combo_var,
                                        values=self.config_manager.get_available_configs(),
                                        state='readonly',
                                        style='Card.TCombobox')
        self.config_combo.pack(padx=1, pady=1, fill=tk.X)
        self.config_combo.bind('<<ComboboxSelected>>', self.on_config_selected)
        
        # Usuń zaznaczenie po wyborze
        def clear_selection(event):
            self.config_combo.selection_clear()
        self.config_combo.bind('<FocusOut>', clear_selection)
        self.config_combo.bind('<<ComboboxSelected>>', lambda e: [self.on_config_selected(e), self.config_combo.selection_clear()])
        
        # Przyciski jako okrągłe ikony z tooltipami
        self.create_round_button(row, "🔄", self.refresh_config_list, 
                                 "Odśwież listę konfiguracji").pack(side=tk.LEFT, padx=3)
        self.create_round_button(row, "💾", self.save_current_config,
                                 "Zapisz bieżącą konfigurację").pack(side=tk.LEFT, padx=3)
        self.create_round_button(row, "➕", self.create_new_config,
                                 "Utwórz nową konfigurację").pack(side=tk.LEFT, padx=3)
        
    def create_formatting_section(self):
        """Sekcja formatowania Input/Output z możliwością dodawania wielu formatów"""
        # Główna karta Bento Box z przyciskiem "+"
        header_frame = tk.Frame(self.scrollable_frame, bg=self.colors['layer1_bg'])
        header_frame.pack(fill=tk.X, padx=10, pady=3)
        
        # Nagłówek z przyciskiem
        title_row = tk.Frame(header_frame, bg=self.colors['layer1_bg'])
        title_row.pack(fill=tk.X)
        
        title_label = tk.Label(title_row, text="🔤 Formatowania tekstów", 
                              bg=self.colors['layer1_bg'],
                              fg=self.colors['text'],
                              font=('Segoe UI', 11, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Przycisk dodawania nowego formatowania
        add_btn = self.create_round_button(title_row, "➕", self.add_text_format,
                                           "Dodaj nowe formatowanie tekstów", transparent=True)
        add_btn.pack(side=tk.LEFT, padx=10)
        
        # Kontener na formatowania (będzie trzymać wszystkie karty formatowań)
        self.formats_container = tk.Frame(self.scrollable_frame, bg=self.colors['layer1_bg'])
        self.formats_container.pack(fill=tk.X)
        
        # NIE dodawaj domyślnego formatu tutaj - będzie dodany przez load_config_to_fields()
    
    def add_text_format(self, is_initial=False):
        """Dodaje nowe formatowanie tekstów"""
        format_id = len(self.text_formats)
        
        # Utwórz nowy słownik dla tego formatowania
        format_data = {
            'id': format_id,
            'name': tk.StringVar(value=f"Format {format_id + 1}"),
            'station_id': tk.StringVar(value=""),
            'input_format': tk.StringVar(value="{name}/F{inv:2}/STR{str:2}"),
            'output_format': tk.StringVar(value="S{mppt:2}-{str:2}/{inv:2}"),
            'variables': {
                'st': tk.StringVar(value=""),
                'tr': tk.StringVar(value=""),
                'inv': tk.StringVar(value=""),
                'mppt': tk.StringVar(value=""),
                'str': tk.StringVar(value=""),
                'sub': tk.StringVar(value="")
            }
        }
        
        self.text_formats.append(format_data)
        
        # Utwórz GUI dla tego formatowania
        format_frame = self.create_single_format_card(format_data)
        self.format_frames.append(format_frame)
        
        if not is_initial:
            # Scroll do nowo dodanego elementu (jeśli main_canvas istnieje)
            if hasattr(self, 'main_canvas'):
                self.main_canvas.update_idletasks()
                self.main_canvas.yview_moveto(1.0)
    
    def create_single_format_card(self, format_data):
        """Tworzy kartę dla pojedynczego formatowania"""
        format_id = format_data['id']
        
        # Karta Bento Box dla tego formatowania
        card = self.create_bento_card(self.formats_container, title=None)  # Tytuł będzie w środku
        
        # Nagłówek z nazwą i przyciskiem usuwania
        header_row = tk.Frame(card, bg=self.colors['card_bg'])
        header_row.pack(fill=tk.X, pady=(0, 8))
        
        # Pole nazwy formatowania (edytowalne)
        name_label = tk.Label(header_row, text="📝 Nazwa:", 
                             bg=self.colors['card_bg'],
                             fg=self.colors['text_dim'],
                             font=('Segoe UI', 9))
        name_label.pack(side=tk.LEFT, padx=(0, 5))
        
        name_entry = self.create_entry(header_row, format_data['name'], width=20)
        name_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Przycisk usuwania (tylko jeśli nie jest to jedyne formatowanie)
        if len(self.text_formats) > 0:  # Zawsze pokazuj bo można dodać więcej
            def remove_with_cleanup(fid=format_id, btn=None):
                # Usuń tooltip jeśli istnieje
                if hasattr(self, 'tooltip_label') and self.tooltip_label:
                    try:
                        self.tooltip_label.destroy()
                        self.tooltip_label = None
                    except:
                        pass
                self.remove_text_format(fid)
            
            delete_btn = tk.Button(header_row, text="🗑️", 
                                  bg=self.colors['card_bg'],
                                  fg='#ff6b6b',
                                  font=('Segoe UI', 10),
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  command=remove_with_cleanup)
            delete_btn.pack(side=tk.RIGHT)
            self.create_tooltip(delete_btn, "Usuń to formatowanie")
        
        # {name} - STATION_ID
        name_row = tk.Frame(card, bg=self.colors['card_bg'])
        name_row.pack(fill=tk.X, pady=2)
        
        self.create_label(name_row, "{name}:", width=15).pack(side=tk.LEFT)
        
        name_info = self.create_info_icon(name_row, 
            "STATION_ID - ID stacji używany do filtrowania tekstów.\n"
            "To pole definiuje wartość zmiennej {name} w formułach Input/Output.")
        name_info.pack(side=tk.LEFT, padx=(0, 5))
        
        self.create_entry(name_row, format_data['station_id'], width=40).pack(side=tk.LEFT, padx=(0, 5))
        
        # Format Input
        input_row = tk.Frame(card, bg=self.colors['card_bg'])
        input_row.pack(fill=tk.X, pady=2)
        
        self.create_label(input_row, "Format Input:", width=15).pack(side=tk.LEFT)
        
        input_info = self.create_info_icon(input_row,
            "Wzorzec do rozpoznawania tekstów z DXF.\n"
            "Zmienne: {name}, {st}, {tr}, {inv}, {mppt}, {str}, {sub}\n"
            "Formatowanie: {inv:2} = wypełnij zerami do 2 cyfr\n"
            "Przykład: {name}/F{inv:2}/MPPT{mppt:2}/S{str:2}")
        input_info.pack(side=tk.LEFT, padx=(0, 5))
        
        self.create_entry(input_row, format_data['input_format'], width=40).pack(side=tk.LEFT, padx=(0, 5))
        
        # Format Output
        output_row = tk.Frame(card, bg=self.colors['card_bg'])
        output_row.pack(fill=tk.X, pady=2)
        
        self.create_label(output_row, "Format Output:", width=15).pack(side=tk.LEFT)
        
        output_info = self.create_info_icon(output_row,
            "Wzorzec do nazywania stringów w SVG.\n"
            "Zmienne: {name}, {st}, {tr}, {inv}, {mppt}, {str}, {sub}\n"
            "Formatowanie: {inv:2} = wypełnij zerami do 2 cyfr\n"
            "Przykład: S{mppt:2}-{str:2}/{inv:2}")
        output_info.pack(side=tk.LEFT, padx=(0, 5))
        
        self.create_entry(output_row, format_data['output_format'], width=40).pack(side=tk.LEFT, padx=(0, 5))
        
        # Zmienne obliczeniowe - ROZWIJALNE
        self.create_advanced_variables_collapsible_for_format(card, format_data)
        
        return card
    
    def remove_text_format(self, format_id):
        """Usuwa formatowanie o podanym ID"""
        if len(self.text_formats) <= 1:
            messagebox.showwarning("Nie można usunąć", 
                                 "Musi pozostać przynajmniej jedno formatowanie!")
            return
        
        # Znajdź index formatowania
        index = next((i for i, fmt in enumerate(self.text_formats) if fmt['id'] == format_id), None)
        
        if index is not None:
            # Usuń GUI
            self.format_frames[index].master.master.destroy()  # Destroy całej karty (outer frame)
            
            # Usuń z list
            del self.text_formats[index]
            del self.format_frames[index]
            
            # WAŻNE: Wymusz przerysowanie wszystkich Canvas
            self.after(50, self.refresh_all_canvases)
    
    def create_advanced_variables_collapsible_for_format(self, parent, format_data):
        """Tworzy rozwijalną sekcję ze zmiennymi obliczeniowymi dla konkretnego formatowania"""
        # Frame zawierający przycisk rozwijania i zawartość
        collapsible_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        collapsible_frame.pack(fill=tk.X, pady=(8, 0))
        
        # Zmienna do śledzenia stanu (rozwinięte/zwinięte)
        is_expanded = tk.BooleanVar(value=False)
        
        # Przycisk rozwijania
        toggle_btn_frame = tk.Frame(collapsible_frame, bg=self.colors['card_bg'])
        toggle_btn_frame.pack(fill=tk.X)
        
        arrow_label = tk.Label(toggle_btn_frame, text="▶", 
                              bg=self.colors['card_bg'],
                              fg=self.colors['text_dim'],
                              font=('Segoe UI', 9))
        arrow_label.pack(side=tk.LEFT)
        
        toggle_label = tk.Label(toggle_btn_frame, text="Zmienne obliczeniowe (opcjonalne)", 
                               bg=self.colors['card_bg'],
                               fg=self.colors['text_dim'],
                               font=('Segoe UI', 9),
                               cursor='hand2')
        toggle_label.pack(side=tk.LEFT, padx=5)
        
        # Zawartość (początkowo ukryta)
        content_frame = tk.Frame(collapsible_frame, bg=self.colors['card_bg'])
        
        # Funkcja przełączająca
        def toggle_content():
            if is_expanded.get():
                content_frame.pack_forget()
                arrow_label.config(text="▶")
                is_expanded.set(False)
            else:
                content_frame.pack(fill=tk.X, pady=(5, 0))
                arrow_label.config(text="▼")
                is_expanded.set(True)
        
        toggle_btn_frame.bind('<Button-1>', lambda e: toggle_content())
        toggle_label.bind('<Button-1>', lambda e: toggle_content())
        arrow_label.bind('<Button-1>', lambda e: toggle_content())
        
        # Dodaj pola zmiennych
        variables = [
            ('st', 'Station Number'),
            ('tr', 'Tracker'),
            ('inv', 'Inverter'),
            ('mppt', 'MPPT'),
            ('str', 'String'),
            ('sub', 'Substring')
        ]
        
        for var_name, var_label in variables:
            var_row = tk.Frame(content_frame, bg=self.colors['card_bg'])
            var_row.pack(fill=tk.X, pady=1)
            
            self.create_label(var_row, f"{{{var_name}}}:", width=15).pack(side=tk.LEFT)
            
            tooltip = f"Zmienna {{{var_name}}} - {var_label}\nWartość do podstawienia w formułach Input/Output"
            info = self.create_info_icon(var_row, tooltip)
            info.pack(side=tk.LEFT, padx=(0, 5))
            
            self.create_entry(var_row, format_data['variables'][var_name], width=40).pack(side=tk.LEFT, padx=(0, 5))
    
    def create_bento_card(self, parent, title=None):
        """Tworzy kartę z prawdziwymi zaokrąglonymi rogami przez Canvas"""
        # Outer frame dla padding - zmniejszony padding
        outer = tk.Frame(parent, bg=self.colors['layer1_bg'])
        outer.pack(fill=tk.X, padx=10, pady=3)
        
        # Canvas dla zaokrąglonego tła (tło przezroczyste jak outer, rysujemy layer2_bg z zaokrągleniem)
        card_canvas = tk.Canvas(outer, bg=self.colors['layer1_bg'],
                               highlightthickness=0, borderwidth=0)
        card_canvas.pack(fill=tk.X)
        
        # Frame dla zawartości - zmniejszony padding
        # WAŻNE: NIE używamy .pack() tutaj, tylko canvas.create_window()
        content = tk.Frame(card_canvas, bg=self.colors['layer2_bg'])
        
        if title:
            title_label = tk.Label(content, text=title, 
                                  bg=self.colors['layer2_bg'],
                                  fg=self.colors['text'],
                                  font=('Segoe UI', 10, 'bold'))
            title_label.pack(anchor=tk.W, pady=(0, 6))  # Zmniejszony z 8 na 6
        
        # Funkcja do rysowania zaokrąglonego tła po update
        def draw_rounded_bg(event=None):
            content.update_idletasks()
            # Pobierz dokładną wielkość contentu
            req_width = content.winfo_reqwidth()
            req_height = content.winfo_reqheight()
            
            # Jeśli content jest pusty (0x0), nie rysuj nic
            if req_width <= 1 or req_height <= 1:
                card_canvas.configure(width=1, height=1)
                return
            
            # Padding wokół contentu
            padding_x = 12
            padding_y = 8
            width = req_width + (2 * padding_x)
            height = req_height + (2 * padding_y)
            
            card_canvas.configure(width=width, height=height)
            card_canvas.delete('all')
            
            # Rysuj zaokrąglony prostokąt jako tło
            create_rounded_rectangle(card_canvas, 0, 0, width, height,
                                   fill=self.colors['layer2_bg'],
                                   outline='', width=0)
            
            # Umieść content na canvas z paddingiem
            card_canvas.create_window(padding_x, padding_y, window=content, anchor='nw')
        
        # Bind do rysowania po załadowaniu
        content.bind('<Configure>', draw_rounded_bg)
        card_canvas.after(10, draw_rounded_bg)
        
        # Przechowaj funkcję rysującą dla późniejszego odświeżania
        self.canvas_draw_functions.append(draw_rounded_bg)
        
        return content
    
    def create_label(self, parent, text, width=None):
        """Tworzy etykietę w ciemnym stylu"""
        return tk.Label(parent, text=text, 
                       bg=self.colors['layer2_bg'],
                       fg=self.colors['text'],
                       font=('Segoe UI', 9),
                       width=width, anchor='w')
    
    def create_entry(self, parent, textvariable, width=None):
        """Tworzy pole tekstowe w ciemnym stylu"""
        entry = tk.Entry(parent, textvariable=textvariable,
                        bg=self.colors['input_bg'],
                        fg=self.colors['text'],
                        font=('Segoe UI', 9),
                        relief=tk.FLAT,
                        insertbackground=self.colors['text'],
                        width=width,
                        borderwidth=0,
                        highlightthickness=0)
        return entry
    
    def create_button(self, parent, text, command, style='normal'):
        """Tworzy przycisk w ciemnym stylu z zaokrąglonymi rogami"""
        if style == 'accent':
            bg = self.colors['accent']
            fg = 'white'
            font_weight = 'bold'
        else:
            bg = self.colors['button_bg']
            fg = self.colors['text']
            font_weight = 'normal'
        
        btn = tk.Button(parent, text=text, command=command,
                       bg=bg, fg=fg,
                       font=('Segoe UI', 8, font_weight),  # Mniejszy font
                       relief=tk.FLAT,
                       cursor='hand2',
                       padx=10, pady=5,  # Mniejszy padding
                       highlightthickness=0,
                       borderwidth=0)
        
        # Hover effect
        def on_enter(e):
            if style == 'accent':
                btn.config(bg=self.colors['accent_hover'])
            else:
                btn.config(bg=self.colors['card_hover'])
        
        def on_leave(e):
            btn.config(bg=bg)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def create_info_icon(self, parent, tooltip_text):
        """Tworzy ikonkę info z tooltipem"""
        info = tk.Label(parent, text="ℹ️", 
                       bg=self.colors['layer2_bg'],
                       fg=self.colors['accent'],
                       font=('Segoe UI', 10),
                       cursor='hand2')
        self.create_tooltip(info, tooltip_text)
        return info
    
    def create_round_button(self, parent, icon, command, tooltip_text, transparent=False):
        """Tworzy okrągły przycisk z ikoną i tooltipem"""
        # Canvas dla okrągłego tła
        size = 32
        bg_color = self.colors['layer1_bg'] if transparent else self.colors['layer2_bg']
        canvas = tk.Canvas(parent, width=size, height=size,
                          bg=bg_color,
                          highlightthickness=0,
                          borderwidth=0)
        
        # Rysuj okrąg
        circle = canvas.create_oval(2, 2, size-2, size-2,
                                   fill=self.colors['button_bg'],
                                   outline='',
                                   width=0)
        
        # Ikona
        text = canvas.create_text(size//2, size//2,
                                 text=icon,
                                 fill=self.colors['text'],
                                 font=('Segoe UI', 13))
        
        # Hover effect
        def on_enter(e):
            canvas.itemconfig(circle, fill=self.colors['accent'])
            canvas.itemconfig(text, fill='white')
        
        def on_leave(e):
            canvas.itemconfig(circle, fill=self.colors['button_bg'])
            canvas.itemconfig(text, fill=self.colors['text'])
        
        def on_click(e):
            command()
        
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        canvas.bind('<Button-1>', on_click)
        canvas.configure(cursor='hand2')
        
        # Tooltip
        self.create_tooltip(canvas, tooltip_text)
        
        return canvas
    
    def create_advanced_variables_collapsible(self, parent):
        """Sekcja zmiennych zaawansowanych {st}, {tr}, {inv}, etc. - ROZWIJALNA - w tle, dopiero po rozwinięciu tworzy obszar"""
        # Separator
        sep = tk.Frame(parent, height=1, bg=self.colors['border'])
        sep.pack(fill=tk.X, pady=(10, 6))
        
        # Belka rozwijająca - BEZPOŚREDNIO W KARCIE (nie tworzy osobnego obszaru)
        expanded_var = tk.BooleanVar(value=False)
        
        header_frame = tk.Frame(parent, bg=self.colors['card_bg'], cursor='hand2')
        header_frame.pack(fill=tk.X, pady=(0, 0))
        
        arrow_label = tk.Label(header_frame, text="▶", 
                              bg=self.colors['card_bg'],
                              fg=self.colors['accent'],
                              font=('Segoe UI', 8))
        arrow_label.pack(side=tk.LEFT, padx=(0, 6))
        
        title_label = tk.Label(header_frame, text="Zmienne obliczeniowe", 
                              bg=self.colors['card_bg'],
                              fg=self.colors['text_dim'],
                              font=('Segoe UI', 8))
        title_label.pack(side=tk.LEFT)
        
        info_icon = self.create_info_icon(header_frame,
            "FORMUŁY OBLICZENIOWE:\n\n"
            "• Puste pole = wartość z Input\n"
            "• Stała wartość (np. '01') = zawsze ta wartość\n"
            "• Formuła = obliczenia: +, -, *, /, %\n\n"
            "Przykłady:\n"
            "  {str}/2 + {str}%2  → dla str=5: 2+1=3\n"
            "  {inv}*10 + {mppt}  → dla inv=2,mppt=3: 23")
        info_icon.pack(side=tk.LEFT, padx=(8, 0))
        
        # Content frame - separator + pola
        content_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        
        def toggle():
            if expanded_var.get():
                content_frame.pack_forget()
                arrow_label.config(text="▶")
                expanded_var.set(False)
            else:
                content_frame.pack(fill=tk.X, pady=(5, 0))
                arrow_label.config(text="▼")
                expanded_var.set(True)
        
        header_frame.bind('<Button-1>', lambda e: toggle())
        arrow_label.bind('<Button-1>', lambda e: toggle())
        title_label.bind('<Button-1>', lambda e: toggle())
        
        # Zmienne (bez 'name' - to już jest powyżej)
        variables = [
            ('st', "Numer stacji (station number)"),
            ('tr', "Numer transformatora"),
            ('inv', "Numer falownika/invertera"),
            ('mppt', "Numer MPPT (Maximum Power Point Tracker)"),
            ('str', "Numer stringa"),
            ('sub', "Substring - dodatkowa część identyfikatora")
        ]
        
        for var_name, tooltip in variables:
            row = tk.Frame(content_frame, bg=self.colors['card_bg'])
            row.pack(fill=tk.X, pady=4)
            
            self.create_label(row, f"{{{var_name}}}:", width=15).pack(side=tk.LEFT)
            
            # Ikonka info z tooltipem
            info_icon = self.create_info_icon(row, tooltip)
            info_icon.pack(side=tk.LEFT, padx=(0, 5))
            
            var = tk.StringVar()
            self.advanced_formula_vars[var_name] = var
            entry = self.create_entry(row, var, width=40)
            entry.pack(side=tk.LEFT, padx=(0, 5))
            
    def create_files_section(self):
        """Sekcja wyboru plików DXF i SVG - Bento Box"""
        card = self.create_bento_card(self.scrollable_frame, "Pliki wejściowe i wyjściowe")
        
        # Plik DXF
        dxf_row = tk.Frame(card, bg=self.colors['card_bg'])
        dxf_row.pack(fill=tk.X, pady=2)
        
        label_dxf = self.create_label(dxf_row, "Plik DXF:", width=12)
        label_dxf.pack(side=tk.LEFT)
        
        # Info icon z tooltipem
        info_dxf = self.create_info_icon(dxf_row, 
            "Plik wejściowy DXF zawierający warstwy z polilinami (segmenty) i tekstami (identyfikatory).")
        info_dxf.pack(side=tk.LEFT, padx=(0, 5))
        
        self.create_entry(dxf_row, self.dxf_file_var, width=40).pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.create_round_button(dxf_row, "📁", self.browse_dxf, "Przeglądaj pliki DXF").pack(side=tk.LEFT)
        
        # Plik SVG wyjściowy
        svg_row = tk.Frame(card, bg=self.colors['card_bg'])
        svg_row.pack(fill=tk.X, pady=2)
        
        label_svg = self.create_label(svg_row, "Plik SVG:", width=12)
        label_svg.pack(side=tk.LEFT)
        
        # Info icon z tooltipem
        info_svg = self.create_info_icon(svg_row,
            "Plik wyjściowy SVG z interaktywnym podglądem przypisań tekstów do segmentów.")
        info_svg.pack(side=tk.LEFT, padx=(0, 5))
        
        self.create_entry(svg_row, self.svg_file_var, width=40).pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.create_round_button(svg_row, "📁", self.browse_svg, "Zapisz jako SVG").pack(side=tk.LEFT)
        
    def create_parameters_sections(self):
        """Tworzy sekcje dla wszystkich parametrów"""
        for section_key, section_data in CONFIG_PARAMETERS.items():
            self.create_parameter_section(section_key, section_data)
            
    def create_parameter_section(self, section_key: str, section_data: Dict):
        """Tworzy pojedynczą sekcję parametrów - rozwijane sekcje BEZ ramek (tylko w tle)"""
        is_collapsible = section_data.get('collapsible', False)
        is_collapsed = section_data.get('collapsed', True)
        
        if is_collapsible:
            # Rozwijalna sekcja - belka w tle, obszar tylko po rozwinięciu
            outer = tk.Frame(self.scrollable_frame, bg=self.colors['layer1_bg'])
            outer.pack(fill=tk.X, padx=15, pady=4)
            
            # Belka nagłówka - BEZPOŚREDNIO NA TLE (bez ramki)
            expanded_var = tk.BooleanVar(value=not is_collapsed)
            
            header_frame = tk.Frame(outer, bg=self.colors['layer1_bg'], cursor='hand2')
            header_frame.pack(fill=tk.X, pady=2)
            
            arrow_label = tk.Label(header_frame, 
                                  text="▼" if not is_collapsed else "▶",
                                  bg=self.colors['layer1_bg'],
                                  fg=self.colors['accent'],
                                  font=('Segoe UI', 8))
            arrow_label.pack(side=tk.LEFT, padx=(0, 6))
            
            title_label = tk.Label(header_frame, 
                                  text=section_data['title'],
                                  bg=self.colors['layer1_bg'],
                                  fg=self.colors['text_dim'],
                                  font=('Segoe UI', 9))
            title_label.pack(side=tk.LEFT)
            
            # Content frame - POJAWIA SIĘ DOPIERO PO ROZWINIĘCIU jako karta z zaokrągleniami
            content_container = tk.Frame(outer, bg=self.colors['layer1_bg'])
            
            # Canvas container dla zaokrąglonych rogów
            canvas_container = tk.Frame(content_container, bg=self.colors['layer1_bg'])
            canvas_container.pack(fill=tk.X, pady=(2, 0))
            
            # Canvas dla zaokrąglonego tła
            card_canvas = tk.Canvas(canvas_container, bg=self.colors['layer1_bg'],
                                   highlightthickness=0, borderwidth=0)
            card_canvas.pack(fill=tk.BOTH, expand=True)
            
            # Frame dla zawartości
            content_frame = tk.Frame(card_canvas, bg=self.colors['layer2_bg'])
            
            # Funkcja do rysowania zaokrąglonego tła
            def draw_rounded_bg(event=None):
                content_frame.update_idletasks()
                req_width = content_frame.winfo_reqwidth()
                req_height = content_frame.winfo_reqheight()
                
                # Minimalne wymiary jeśli content jest pusty
                width = max(req_width + 24, 100)
                height = max(req_height + 16, 40)
                
                card_canvas.configure(width=width, height=height)
                card_canvas.delete('all')
                
                # Zaokrąglony prostokąt
                create_rounded_rectangle(card_canvas, 0, 0, width, height,
                                       fill=self.colors['layer2_bg'],
                                       outline='', width=0)
                
                # Umieść content na canvas
                card_canvas.create_window(12, 8, window=content_frame, anchor='nw')
            
            content_frame.bind('<Configure>', draw_rounded_bg)
            content_frame.after(50, draw_rounded_bg)
            
            # Przechowuj funkcję rysującą dla późniejszego odświeżania
            self.canvas_draw_functions.append(draw_rounded_bg)
            
            def toggle_section():
                if expanded_var.get():
                    content_container.pack_forget()
                    arrow_label.config(text="▶")
                    expanded_var.set(False)
                else:
                    content_container.pack(fill=tk.X, pady=(2, 0))
                    arrow_label.config(text="▼")
                    expanded_var.set(True)
            
            header_frame.bind('<Button-1>', lambda e: toggle_section())
            arrow_label.bind('<Button-1>', lambda e: toggle_section())
            title_label.bind('<Button-1>', lambda e: toggle_section())
            
            # Dodaj parametry
            for param_name, param_config in section_data['params'].items():
                self.create_parameter_field(content_frame, param_name, param_config)
            
            # Pokaż zawartość jeśli nie zwinięta
            if not is_collapsed:
                content_container.pack(fill=tk.X, pady=(2, 0))
                
        else:
            # Normalna sekcja (nierozwijalna) - Bento Box
            card = self.create_bento_card(self.scrollable_frame, section_data['title'])
            
            for param_name, param_config in section_data['params'].items():
                self.create_parameter_field(card, param_name, param_config)
            
    def create_parameter_field(self, parent, param_name: str, param_config: Dict):
        """Tworzy pojedyncze pole parametru w ciemnym stylu"""
        row = tk.Frame(parent, bg=self.colors['layer2_bg'])
        row.pack(fill=tk.X, pady=1)  # Zmniejszony odstęp z 2 na 1
        
        # Label z jeszcze mniejszą szerokością - maksymalne zagęszczenie
        self.create_label(row, param_config['label'] + ":", width=22).pack(side=tk.LEFT, padx=(0, 4))  # 22 zamiast 25, padx=4 zamiast 5
        
        # Pole w zależności od typu
        param_type = param_config['type']
        default_value = param_config.get('default')
        
        if param_type == 'bool':
            var = tk.BooleanVar(value=default_value)
            widget = tk.Checkbutton(row, variable=var,
                                   bg=self.colors['layer2_bg'],
                                   fg=self.colors['text'],
                                   activebackground=self.colors['layer2_bg'],
                                   activeforeground=self.colors['text'],
                                   selectcolor=self.colors['input_bg'],
                                   relief=tk.FLAT,
                                   highlightthickness=0,
                                   borderwidth=0)
        elif param_type == 'choice':
            var = tk.StringVar(value=default_value)
            # Combobox wrapper BEZ RAMKI
            combo_frame = tk.Frame(row, bg=self.colors['input_bg'])
            combo_frame.pack(side=tk.LEFT, padx=(0, 5))
            widget = ttk.Combobox(combo_frame, textvariable=var, 
                                values=param_config['choices'],
                                state='readonly', width=33,
                                style='Card.TCombobox')
            widget.pack(padx=1, pady=1)
        elif param_type == 'color':
            var = tk.StringVar(value=default_value)
            entry = self.create_entry(row, var, width=15)
            entry.pack(side=tk.LEFT, padx=(0, 5))
            
            # OKRĄGŁY przycisk koloru z tooltipem
            color_btn_canvas = tk.Canvas(row, width=32, height=32, 
                                        bg=self.colors['layer2_bg'],
                                        highlightthickness=0, borderwidth=0)
            color_btn_canvas.pack(side=tk.LEFT, padx=(0, 5))
            
            # Rysuj okrąg (używamy create_oval)
            circle = color_btn_canvas.create_oval(4, 4, 28, 28, 
                                                 fill=self.colors['button_bg'],
                                                 outline='',
                                                 width=0)
            icon = color_btn_canvas.create_text(16, 16, text="🎨", 
                                               font=('Segoe UI', 10))
            
            # Kliknięcie
            def on_color_click(event, v=var):
                self.choose_color(v)
            color_btn_canvas.bind('<Button-1>', on_color_click)
            
            # Hover effect
            def on_color_enter(event):
                color_btn_canvas.itemconfig(circle, fill=self.colors['button_hover'])
                color_btn_canvas.config(cursor='hand2')
            def on_color_leave(event):
                color_btn_canvas.itemconfig(circle, fill=self.colors['button_bg'])
                color_btn_canvas.config(cursor='')
            color_btn_canvas.bind('<Enter>', on_color_enter)
            color_btn_canvas.bind('<Leave>', on_color_leave)
            
            # TOOLTIP
            self.create_tooltip(color_btn_canvas, "Wybierz kolor")
            
            widget = entry
        elif param_type == 'int':
            var = tk.IntVar(value=default_value)
            widget = tk.Spinbox(row, from_=0, to=999999, textvariable=var, width=13,
                              bg=self.colors['input_bg'],
                              fg=self.colors['text'],
                              buttonbackground=self.colors['button_bg'],
                              relief=tk.FLAT,
                              highlightthickness=0,
                              borderwidth=0)
        elif param_type == 'float':
            var = tk.DoubleVar(value=default_value)
            widget = tk.Spinbox(row, from_=0.0, to=999999.0, increment=0.1,
                              textvariable=var, width=13,
                              bg=self.colors['input_bg'],
                              fg=self.colors['text'],
                              buttonbackground=self.colors['button_bg'],
                              relief=tk.FLAT,
                              highlightthickness=0,
                              borderwidth=0)
        else:  # string
            var = tk.StringVar(value=default_value)
            widget = self.create_entry(row, var, width=35)
        
        self.field_vars[param_name] = var
        
        if param_type != 'color' and param_type != 'choice':
            widget.pack(side=tk.LEFT, padx=(0, 5))
        
        # Info icon z tooltipem
        if param_config.get('description'):
            info_icon = self.create_info_icon(row, param_config['description'])
            info_icon.pack(side=tk.LEFT, padx=(2, 0))
                      
    def create_action_buttons(self):
        """Przyciski akcji - Konwertuj i Analizuj - ZAOKRĄGLONE przez Canvas"""
        # Padding na dole
        action_outer = tk.Frame(self.scrollable_frame, bg=self.colors['layer1_bg'])
        action_outer.pack(fill=tk.X, padx=15, pady=(15, 25))
        
        # Canvas dla zaokrąglonego przycisku konwersji
        btn_canvas = tk.Canvas(action_outer, height=48, 
                              bg=self.colors['layer1_bg'],
                              highlightthickness=0, borderwidth=0,
                              cursor='hand2')
        btn_canvas.pack(fill=tk.X)
        
        # Zmienne dla hover efektu
        self.btn_hovered = False
        
        def draw_convert_button(event=None):
            width = btn_canvas.winfo_width()
            if width < 10:
                width = 400
            btn_canvas.configure(width=width)
            btn_canvas.delete('all')
            
            # Kolor zależny od hover
            color = self.colors['accent_hover'] if self.btn_hovered else self.colors['accent']
            
            # Zaokrąglony prostokąt
            self.btn_rect = create_rounded_rectangle(btn_canvas, 0, 0, width, 48,
                                                    fill=color,
                                                    outline='', width=0, tags='button')
            
            # Tekst
            self.btn_text = btn_canvas.create_text(width//2, 24,
                                                  text="▶️  KONWERTUJ I ANALIZUJ",
                                                  fill='white',
                                                  font=('Segoe UI', 10, 'bold'),
                                                  tags='button')
        
        # Hover effects
        def on_enter(e):
            self.btn_hovered = True
            draw_convert_button()
        
        def on_leave(e):
            self.btn_hovered = False
            draw_convert_button()
        
        def on_click(e):
            self.run_conversion()
        
        btn_canvas.bind('<Enter>', on_enter)
        btn_canvas.bind('<Leave>', on_leave)
        btn_canvas.bind('<Button-1>', on_click)
        btn_canvas.bind('<Configure>', draw_convert_button)
        btn_canvas.after(50, draw_convert_button)
        
        # Referencja do canvas zamiast Button
        self.convert_btn = btn_canvas
        
        # Progress bar z zaokrągleniami przez Canvas
        progress_outer = tk.Frame(action_outer, bg=self.colors['layer1_bg'])
        progress_outer.pack(fill=tk.X, pady=(10, 5))
        
        # Canvas dla zaokrąglonego progress bar z animacją
        self.progress_canvas = tk.Canvas(progress_outer, height=8, 
                                   bg=self.colors['layer1_bg'],
                                   highlightthickness=0, borderwidth=0)
        self.progress_canvas.pack(fill=tk.X)
        
        self.progress_bar_rect = None
        self.progress_bar_x = 0
        self.progress_animating = False
        
        # Zaokrąglone tło progress bar
        def draw_progress_bg(event=None):
            width = self.progress_canvas.winfo_width()
            if width < 10:
                width = 400  # fallback
            self.progress_canvas.configure(width=width)
            self.progress_canvas.delete('bg')
            create_rounded_rectangle(self.progress_canvas, 0, 0, width, 8,
                                   radius=8, fill=self.colors['layer2_bg'],
                                   outline='', width=0, tags='bg')
        
        self.progress_canvas.bind('<Configure>', draw_progress_bg)
        self.progress_canvas.after(50, draw_progress_bg)
        
        # Standardowy progressbar (backup, niewidoczny)
        self.progress = ttk.Progressbar(progress_outer, mode='indeterminate',
                                       style='TProgressbar')
        # Ukryty, użyjemy canvas do animacji
        
        # Status
        self.status_label = tk.Label(action_outer, text="Gotowy do konwersji",
                                     bg=self.colors['layer1_bg'],
                                     fg=self.colors['text_dim'],
                                     font=('Segoe UI', 9))
        self.status_label.pack(pady=(5, 0))
        
    def animate_progress(self):
        """Animuj progress bar - ruch w prawo"""
        if not self.progress_animating:
            return
            
        width = self.progress_canvas.winfo_width()
        if width < 10:
            width = 400
        
        bar_width = 80
        
        # Usuń poprzedni prostokąt
        if self.progress_bar_rect:
            self.progress_canvas.delete(self.progress_bar_rect)
        
        # Rysuj nowy prostokąt (zaokrąglony)
        self.progress_bar_rect = create_rounded_rectangle(
            self.progress_canvas,
            self.progress_bar_x, 0,
            self.progress_bar_x + bar_width, 8,
            radius=8,
            fill=self.colors['accent'],
            outline='',
            width=0
        )
        
        # Przesuń pozycję
        self.progress_bar_x += 5
        if self.progress_bar_x > width:
            self.progress_bar_x = -bar_width
        
        # Następna klatka
        if self.progress_animating:
            self.progress_canvas.after(30, self.animate_progress)
    
    def start_progress(self):
        """Rozpocznij animację progress bara"""
        if not self.progress_animating:
            self.progress_animating = True
            self.progress_bar_x = 0
            self.animate_progress()
    
    def stop_progress(self):
        """Zatrzymaj animację progress bara"""
        self.progress_animating = False
        if self.progress_bar_rect:
            self.progress_canvas.delete(self.progress_bar_rect)
            self.progress_bar_rect = None
        
    # === Callback functions ===
    
    def on_config_selected(self, event=None):
        """Załaduj wybraną konfigurację"""
        config_name = self.config_combo_var.get()
        if config_name and config_name != self.config_manager.current_config_name:
            try:
                self.config_manager.load_config(config_name)
                self.load_config_to_fields()
                self.status_label.config(text=f"Załadowano: {config_name}", foreground='green')
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się załadować konfiguracji:\n{e}")
                
    def refresh_config_list(self):
        """Odśwież listę dostępnych konfiguracji"""
        configs = self.config_manager.get_available_configs()
        self.config_combo['values'] = configs
        self.status_label.config(text="Lista konfiguracji odświeżona", foreground='blue')
        
    def save_current_config(self):
        """Zapisz bieżącą konfigurację"""
        try:
            config_name = self.config_combo_var.get()
            if not config_name:
                messagebox.showwarning("Brak konfiguracji", "Wybierz konfigurację do zapisania")
                return
            
            self.save_fields_to_config()
            self.config_manager.save_config(config_name)
            messagebox.showinfo("Sukces", f"Zapisano konfigurację: {config_name}")
            self.status_label.config(text="Konfiguracja zapisana", foreground='green')
                    
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać:\n{e}")
            
    def create_new_config(self):
        """Utwórz nową konfigurację"""
        from tkinter import simpledialog
        name = simpledialog.askstring("Nowa konfiguracja", 
                                     "Podaj nazwę nowej konfiguracji (bez .cfg):")
        if name:
            try:
                # Zapisz obecne wartości
                self.save_fields_to_config()
                # Utwórz nowy plik
                self.config_manager.save_config(name)
                # Odśwież listę i wybierz nowy
                self.refresh_config_list()
                self.config_combo_var.set(name)
                messagebox.showinfo("Sukces", f"Utworzono nową konfigurację: {name}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się utworzyć:\n{e}")
                
    def duplicate_config(self):
        """Zduplikuj bieżącą konfigurację"""
        from tkinter import simpledialog
        current = self.config_manager.current_config_name
        name = simpledialog.askstring("Duplikuj konfigurację", 
                                     f"Duplikujesz: {current}\nNowa nazwa:",
                                     initialvalue=f"{current}_kopia")
        if name:
            try:
                self.save_fields_to_config()
                self.config_manager.save_config(name)
                self.refresh_config_list()
                self.config_combo_var.set(name)
                messagebox.showinfo("Sukces", f"Zduplikowano jako: {name}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się zduplikować:\n{e}")
                
    def create_tooltip(self, widget, text):
        """Tworzy tooltip z zaokrąglonymi rogami - warstwa 3 (najjaśniejsza)"""
        def on_enter(event):
            # Twórz tooltip
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_attributes('-topmost', True)
            
            # Transparent background
            try:
                tooltip.attributes('-alpha', 0.95)
            except:
                pass
            
            # Canvas dla zaokrąglonego tła
            padding = 12
            # Oblicz rozmiar tekstu
            dummy_label = tk.Label(tooltip, text=text, font=('Segoe UI', 9))
            dummy_label.update_idletasks()
            text_width = dummy_label.winfo_reqwidth()
            text_height = dummy_label.winfo_reqheight()
            dummy_label.destroy()
            
            canvas_width = text_width + padding * 2
            canvas_height = text_height + padding * 2
            
            # Canvas z TRANSPARENTNYM tłem (używamy layer3_bg jako tło)
            canvas = tk.Canvas(tooltip, width=canvas_width, height=canvas_height,
                             bg=self.colors['layer3_bg'], highlightthickness=0,
                             borderwidth=0)
            canvas.pack()
            
            # Rysuj zaokrąglony prostokąt - warstwa 3 (ten sam kolor co tło canvas!)
            create_rounded_rectangle(canvas, 0, 0, canvas_width, canvas_height,
                                   fill=self.colors['layer3_bg'],
                                   outline='', width=0)
            
            # Tekst na środku
            canvas.create_text(canvas_width//2, canvas_height//2,
                             text=text, fill=self.colors['text'],
                             font=('Segoe UI', 9), justify=tk.LEFT)
            
            # Pozycjonowanie
            tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
            widget._tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, '_tooltip'):
                try:
                    widget._tooltip.destroy()
                except:
                    pass
                del widget._tooltip
        
        def on_click(event):
            # Usuń tooltip przy kliknięciu
            if hasattr(widget, '_tooltip'):
                try:
                    widget._tooltip.destroy()
                except:
                    pass
                del widget._tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
        widget.bind('<Button-1>', on_click, add='+')  # add='+' żeby nie nadpisać istniejącego handlera
            
    def choose_color(self, var: tk.StringVar):
        """Wybierz kolor z palety"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor=var.get())
        if color[1]:
            var.set(color[1])
            
    def browse_dxf(self):
        """Przeglądaj plik DXF"""
        filename = filedialog.askopenfilename(
            title="Wybierz plik DXF",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )
        if filename:
            self.dxf_file_var.set(filename)
            
    def browse_svg(self):
        """Przeglądaj plik SVG"""
        filename = filedialog.asksaveasfilename(
            title="Zapisz jako SVG",
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
        )
        if filename:
            self.svg_file_var.set(filename)
            
    def load_config_to_fields(self):
        """Załaduj wartości z config_manager do pól"""
        # Wczytaj listę formatowań
        text_formats_data = self.config_manager.get('TEXT_FORMATS_LIST', [])
        
        # Wyczyść obecne formatowania
        for frame in self.format_frames:
            frame.master.master.destroy()
        self.text_formats.clear()
        self.format_frames.clear()
        self.canvas_draw_functions.clear()  # Wyczyść stare funkcje rysujące
        
        # Załaduj formatowania lub dodaj domyślne
        if text_formats_data:
            for fmt_data in text_formats_data:
                format_dict = {
                    'id': len(self.text_formats),
                    'name': tk.StringVar(value=fmt_data.get('name', f"Format {len(self.text_formats) + 1}")),
                    'station_id': tk.StringVar(value=fmt_data.get('station_id', '')),
                    'input_format': tk.StringVar(value=fmt_data.get('input_format', '')),
                    'output_format': tk.StringVar(value=fmt_data.get('output_format', '')),
                    'variables': {
                        var_name: tk.StringVar(value=fmt_data.get('variables', {}).get(var_name, ''))
                        for var_name in ['st', 'tr', 'inv', 'mppt', 'str', 'sub']
                    }
                }
                self.text_formats.append(format_dict)
                format_frame = self.create_single_format_card(format_dict)
                self.format_frames.append(format_frame)
        else:
            # Dodaj jedno domyślne formatowanie jeśli brak w config
            self.add_text_format(is_initial=True)
        
        # WAŻNE: Wymusz przerysowanie wszystkich Canvas
        self.after(100, self.refresh_all_canvases)
            
        # Wszystkie parametry
        for section_data in CONFIG_PARAMETERS.values():
            for param_name in section_data['params'].keys():
                if param_name in self.field_vars:
                    value = self.config_manager.get(param_name)
                    if value is not None:
                        self.field_vars[param_name].set(value)
        
        # Ścieżki plików
        dxf_path = self.config_manager.get('DEFAULT_DXF_FILE', '')
        svg_path = self.config_manager.get('STRUCTURED_SVG_OUTPUT', 'output_interactive.svg')
        self.dxf_file_var.set(dxf_path)
        self.svg_file_var.set(svg_path)
        
    def save_fields_to_config(self):
        """Zapisz wartości z pól do config_manager"""
        # Zapisz listę formatowań
        text_formats_data = []
        for fmt in self.text_formats:
            fmt_dict = {
                'name': fmt['name'].get(),
                'station_id': fmt['station_id'].get(),
                'input_format': fmt['input_format'].get(),
                'output_format': fmt['output_format'].get(),
                'variables': {
                    var_name: fmt['variables'][var_name].get()
                    for var_name in ['st', 'tr', 'inv', 'mppt', 'str', 'sub']
                }
            }
            text_formats_data.append(fmt_dict)
        
        self.config_manager.set('TEXT_FORMATS_LIST', text_formats_data)
        
        # BACKWARD COMPATIBILITY: Zapisz pierwsze formatowanie jako domyślne (dla starego kodu)
        if text_formats_data:
            first_fmt = text_formats_data[0]
            self.config_manager.set('USE_ADVANCED_FORMATTING', True)
            self.config_manager.set('ADVANCED_INPUT_FORMAT', first_fmt['input_format'])
            self.config_manager.set('ADVANCED_OUTPUT_FORMAT', first_fmt['output_format'])
            self.config_manager.set('STATION_ID', first_fmt['station_id'])
            # WAŻNE: Przekonwertuj zmienne z StringVar na dict dla zapisu
            vars_dict = {}
            for var_name in ['st', 'tr', 'inv', 'mppt', 'str', 'sub']:
                var_value = first_fmt['variables'][var_name].get() if hasattr(first_fmt['variables'][var_name], 'get') else first_fmt['variables'][var_name]
                vars_dict[var_name] = var_value
            self.config_manager.set('ADVANCED_ADDITIONAL_VARS', vars_dict)
        
        # Wszystkie parametry
        for param_name, var in self.field_vars.items():
            self.config_manager.set(param_name, var.get())
        
        # Ścieżki plików
        self.config_manager.set('DEFAULT_DXF_FILE', self.dxf_file_var.get())
        self.config_manager.set('STRUCTURED_SVG_OUTPUT', self.svg_file_var.get())
            
        # Zastosuj do modułu config
        self.config_manager.apply_to_config_module()
        
    def run_conversion(self):
        """Uruchom konwersję"""
        if not self.dxf_file_var.get():
            messagebox.showwarning("Brak pliku", "Wybierz plik DXF do konwersji")
            return
            
        # Zapisz konfigurację przed konwersją
        self.save_fields_to_config()
        
        # Wywołaj callback jeśli istnieje
        if self.on_convert_callback:
            # Wyłącz przycisk i pokaż progress
            self.convert_btn.config(state='disabled')
            self.start_progress()  # Użyj nowej animacji
            self.status_label.config(text="🔄 Konwersja w toku...", foreground='blue')
            
            # Uruchom konwersję
            self.on_convert_callback(self.dxf_file_var.get(), self.svg_file_var.get())
        else:
            self.status_label.config(text="Brak callbacku konwersji", foreground='red')
            
    # === Info popups ===
    
    def show_format_info(self):
        """Pokaż info o formatowaniu"""
        info = """FORMATOWANIE TEKSTÓW

Format Input - wzorzec wejściowy do rozpoznawania tekstów z DXF
Format Output - wzorzec wyjściowy do nazywania stringów w SVG

Dostępne zmienne:
{name} - ID stacji (STATION_ID)
{st} - numer stacji  
{tr} - transformator
{inv} - numer falownika/invertera
{mppt} - numer MPPT
{str} - numer stringa
{sub} - substring

Formatowanie liczb:
{inv:2} - wypełnij zerami do 2 cyfr (01, 02, ...)
{mppt:3} - wypełnij zerami do 3 cyfr (001, 002, ...)

Przykłady:
Input: {name}/F{inv:2}/MPPT{mppt:2}/S{str:2}
Rozpozna: ZIEB/F01/MPPT03/S05

Output: S{mppt:2}-{str:2}/{inv:2}  
Wygeneruje: S03-05/01
"""
        messagebox.showinfo("Formatowanie", info)
        
    def show_formula_info(self):
        """Pokaż info o formułach obliczeniowych"""
        info = """FORMUŁY OBLICZENIOWE DLA ZMIENNYCH

Każda zmienna może mieć:
1. Pustą wartość - wtedy używa wartości z Input
2. Stałą wartość - np. "01" - zawsze użyje tej wartości
3. Formułę - obliczenia na podstawie innych zmiennych

Operatory w formułach:
+ - dodawanie
- - odejmowanie  
* - mnożenie
/ - dzielenie całkowite
% - modulo (reszta z dzielenia)

Zmienne w formułach:
{st}, {tr}, {inv}, {mppt}, {str}, {sub}

Przykłady formuł:
{str}/2 + {str}%2  
→ dla str=5: 5/2 + 5%2 = 2 + 1 = 3

{inv}*10 + {mppt}
→ dla inv=2, mppt=3: 2*10 + 3 = 23

Uwaga: {name} zawsze = STATION_ID (nie można obliczyć)
"""
        messagebox.showinfo("Formuły obliczeniowe", info)
        
    def show_layer_requirements(self):
        """Pokaż wymagania dla warstw DXF"""
        info = """WYMAGANIA DLA WARSTW DXF

WARSTWA LINII (np. @IDE_KABLE_DC_B):
✓ Musi zawierać obiekty typu LWPOLYLINE lub POLYLINE
✓ Reprezentują fizyczne położenie stringów
✓ Każdy segment linii = jeden segment stringa
✓ Mogą być ciągłe lub poszatkowane (patrz opcje łączenia)

WARSTWA TEKSTÓW (np. @IDE_KABLE_DC_TXT_B):
✓ Musi zawierać obiekty typu MTEXT lub TEXT  
✓ Teksty muszą pasować do wzorca Input
✓ Muszą być w pobliżu linii (patrz SEARCH_RADIUS)
✓ Lokalizacja względem linii: above/below/any

OPCJE ŁĄCZENIA SEGMENTÓW:
• individual_segments - każdy odcinek osobno
  Używaj gdy: linie są już prawidłowo podzielone
  
• merge_segments - automatyczne łączenie
  Używaj gdy: linie są poszatkowane na małe kawałki
  Parametry: GAP_TOLERANCE, MAX_MERGE_DISTANCE

LOKALIZACJA TEKSTÓW:
• above - teksty powyżej linii (najczęstsze)
• below - teksty poniżej linii  
• any - dowolnie (wolniejsze, mniej precyzyjne)

TOLERANCJE:
• SEARCH_RADIUS - jak daleko szukać tekstów
• X_TOLERANCE, Y_TOLERANCE - dokładność pozycjonowania
• MAX_DISTANCE - max odległość dla auto-przypisania
"""
        messagebox.showinfo("Wymagania warstw DXF", info)
    
    def refresh_all_canvases(self):
        """Wymusza przerysowanie wszystkich Canvas w kartach po zmianach"""
        try:
            # Wymuszenie przerysowania przez pack_forget/pack
            for frame in self.format_frames:
                if frame and frame.winfo_exists():
                    outer = frame.master.master  # outer frame
                    outer.pack_forget()
                    outer.pack(fill=tk.X, padx=10, pady=3)
            
            # Pełna aktualizacja
            self.formats_container.update_idletasks()
            self.scrollable_frame.update_idletasks()
            
            # Wywołaj wszystkie zapisane funkcje rysujące
            for draw_func in self.canvas_draw_functions:
                try:
                    draw_func()
                except Exception as e:
                    pass  # Ignoruj błędy dla usuniętych widgetów
            
            # Aktualizuj scroll region
            if hasattr(self, 'main_canvas'):
                self.main_canvas.update_idletasks()
                self.main_canvas.configure(scrollregion=self.main_canvas.bbox('all'))
        except Exception as e:
            print(f"⚠️ Błąd odświeżania Canvas: {e}")
    
    def adjust_panel_width(self):
        """Dynamicznie dostosowuje szerokość panelu lewego do zawartości"""
        try:
            print("📐 Rozpoczęcie dostosowania szerokości panelu...")
            
            # Znajdź Notebook (bezpośredni parent - już nie ma wrappera)
            notebook = self.master
            print(f"📐 Notebook: {notebook}")
            
            # Znajdź Frame który jest parent Notebook (control_frame)
            control_frame = notebook.master
            print(f"📐 Control Frame: {control_frame}")
            
            # Znajdź PanedWindow który zawiera control_frame
            paned_window = control_frame.master
            print(f"📐 PanedWindow: {paned_window}, typ: {type(paned_window)}")
            
            if not isinstance(paned_window, ttk.PanedWindow):
                print(f"⚠️ Parent nie jest PanedWindow! Typ: {type(paned_window)}")
                return
            
            # Odczekaj aż wszystkie widgety będą gotowe
            self.scrollable_frame.update_idletasks()
            
            # Oblicz wymaganą szerokość na podstawie zawartości
            required_width = self.scrollable_frame.winfo_reqwidth()
            print(f"📐 Wymagana szerokość scrollable_frame: {required_width}px")
            
            # Sprawdź szerokości wszystkich kart
            max_card_width = 0
            for child in self.scrollable_frame.winfo_children():
                child.update_idletasks()
                child_width = child.winfo_reqwidth()
                print(f"📐   - Child: {child.winfo_class()}, width: {child_width}px")
                max_card_width = max(max_card_width, child_width)
            
            print(f"📐 Maksymalna szerokość karty: {max_card_width}px")
            
            # Uwzględnij marginesy używając globalnych stałych:
            # - padding_frame: LAYER_SPACING z każdej strony (obecnie 0)
            # - canvas_inner przesunięty: 2*ELEMENT_SPACING (16px z każdej strony = 32px)
            # - scrollbar gdy widoczny: ~20px
            # Razem: margines = 2*LAYER_SPACING + 2*ELEMENT_SPACING + 20 (scrollbar)
            margin = 2*LAYER_SPACING + 2*ELEMENT_SPACING + 20  # = 0 + 32 + 20 = 52px
            optimal_width = max_card_width + margin
            
            # Ogranicz do rozsądnych wartości (min 400px, max 620px)
            optimal_width = max(400, min(620, optimal_width))
            print(f"📐 Finalna szerokość panelu: {optimal_width}px (karta: {max_card_width}px + {margin}px margines)")
            
            # Wywołaj metodę set_left_panel_width z głównej aplikacji
            if self.main_app and hasattr(self.main_app, 'set_left_panel_width'):
                self.main_app.set_left_panel_width(optimal_width)
            else:
                # Fallback - ustaw bezpośrednio
                try:
                    control_frame.update_idletasks()
                    paned_window.sashpos(0, optimal_width)
                    console.success(f"✅ Dostosowano szerokość panelu (fallback): {optimal_width}px")
                except Exception as e2:
                    print(f"⚠️ Nie udało się ustawić sash: {e2}")
            
            print(f"✅ Obliczono szerokość panelu: {optimal_width}px (max karta: {max_card_width}px)")
            
        except Exception as e:
            import traceback
            print(f"⚠️ Błąd dostosowania szerokości panelu: {e}")
            traceback.print_exc()
        
    def show_param_info(self, label: str, description: str):
        """Pokaż info o parametrze"""
        messagebox.showinfo(label, description)

