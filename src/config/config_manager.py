"""
Menedżer konfiguracji - obsługa plików .cfg i domyślnych ustawień
"""
import os
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Optional
from src.utils.console_logger import console, logger
import src.core.config as config


class ConfigManager:
    """Menedżer konfiguracji obsługujący pliki .cfg"""
    
    def __init__(self):
        self.config_dir = "configs"
        self.current_config_name = "default"
        self.config_data = {}
        self.ensure_config_dir()
        self.load_defaults()
    
    def ensure_config_dir(self):
        """Upewnij się, że folder configs istnieje"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            logger.info(f"Utworzono folder konfiguracji: {self.config_dir}")
    
    def load_defaults(self):
        """Załaduj domyślne ustawienia z config.py"""
        self.config_data = {
            # Podstawowe ustawienia
            'STATION_ID': config.STATION_ID,
            'STATION_NUMBER': config.STATION_NUMBER,
            'ID_FORMAT': config.ID_FORMAT,
            'CURRENT_TEXT_FORMAT': config.CURRENT_TEXT_FORMAT,
            'LAYER_LINE': config.LAYER_LINE,
            'LAYER_TEXT': config.LAYER_TEXT,
            
            # Wymiary SVG
            'SVG_WIDTH': config.SVG_WIDTH,
            'SVG_HEIGHT': config.SVG_HEIGHT,
            
            # Parametry wyszukiwania i tolerancji
            'SEARCH_RADIUS': config.SEARCH_RADIUS,
            'TEXT_LOCATION': config.TEXT_LOCATION,
            'Y_TOLERANCE': config.Y_TOLERANCE,
            'X_TOLERANCE': config.X_TOLERANCE,
            'MARGIN': config.MARGIN,
            'CLUSTER_DISTANCE_THRESHOLD': config.CLUSTER_DISTANCE_THRESHOLD,
            'MAX_DISTANCE': config.MAX_DISTANCE,
            
            # Kolory
            'ASSIGNED_SEGMENT_COLOR': config.ASSIGNED_SEGMENT_COLOR,
            'UNASSIGNED_SEGMENT_COLOR': config.UNASSIGNED_SEGMENT_COLOR,
            'TEXT_SEGMENT_COLOR': config.TEXT_SEGMENT_COLOR,
            'SEGMENT_CENTER_COLOR_ASSIGNED': config.SEGMENT_CENTER_COLOR_ASSIGNED,
            'SEGMENT_CENTER_COLOR_UNASSIGNED': config.SEGMENT_CENTER_COLOR_UNASSIGNED,
            'TEXT_COLOR_ASSIGNED': config.TEXT_COLOR_ASSIGNED,
            'TEXT_COLOR_UNASSIGNED': config.TEXT_COLOR_UNASSIGNED,
            
            # Parametry wizualizacji
            'SHOW_TEXT_DOTS': config.SHOW_TEXT_DOTS,
            'SHOW_TEXT_LABELS': config.SHOW_TEXT_LABELS,
            'SHOW_STRING_LABELS': config.SHOW_STRING_LABELS,
            'SHOW_SEGMENT_CENTERS': config.SHOW_SEGMENT_CENTERS,
            'SHOW_SEGMENT_LABELS': config.SHOW_SEGMENT_LABELS,
            'DOT_RADIUS': config.DOT_RADIUS,
            'TEXT_SIZE': config.TEXT_SIZE,
            'TEXT_OPACITY': config.TEXT_OPACITY,
            'STRING_LABEL_OFFSET': config.STRING_LABEL_OFFSET,
            
            # Inne parametry
            'MPTT_HEIGHT': config.MPTT_HEIGHT,
            'SEGMENT_MIN_WIDTH': config.SEGMENT_MIN_WIDTH,
            
            # Pliki
            'DEFAULT_DXF_FILE': 'input.dxf',
            'STRUCTURED_SVG_OUTPUT': 'output_structured.svg',
            
            # Zaawansowane formatowanie
            'ADVANCED_INPUT_FORMAT': '{name}/F{inv:2}/STR{str:2}',
            'ADVANCED_OUTPUT_FORMAT': 'S{mppt:2}-{str:2}/{inv:2}',
            'ADVANCED_ADDITIONAL_VARS': {'mppt': '{str}/2 + {str}%2'},
            'USE_ADVANCED_FORMATTING': False
        }
        logger.debug(f"Załadowano domyślne ustawienia: {len(self.config_data)} parametrów")
    
    def get_available_configs(self) -> list:
        """Pobierz listę dostępnych plików konfiguracyjnych"""
        configs = []
        if os.path.exists(self.config_dir):
            for file in os.listdir(self.config_dir):
                if file.endswith('.cfg'):
                    configs.append(file[:-4])  # Usuń rozszerzenie .cfg
        return sorted(configs)
    
    def load_config(self, config_name: str) -> bool:
        """Załaduj konfigurację z pliku"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_name}.cfg")
            if not os.path.exists(config_path):
                logger.warning(f"Plik konfiguracyjny nie istnieje: {config_path}")
                return False
            
            # Zacznij od domyślnych ustawień
            self.load_defaults()
            
            # Załaduj i nadpisz ustawieniami z pliku
            parser = configparser.ConfigParser()
            parser.read(config_path, encoding='utf-8')
            
            for section_name in parser.sections():
                for key, value in parser[section_name].items():
                    # Konwertuj wartości na odpowiednie typy
                    converted_value = self._convert_value(value)
                    self.config_data[key.upper()] = converted_value
                    logger.debug(f"Załadowano: {key.upper()} = {converted_value}")
            
            # AKTUALIZUJ GLOBALNE ZMIENNE W src.core.config
            import src.core.config as cfg
            for key, value in self.config_data.items():
                if hasattr(cfg, key):
                    setattr(cfg, key, value)
                    logger.debug(f"Zaktualizowano globalną zmienną cfg.{key} = {value}")
            
            self.current_config_name = config_name
            logger.info(f"Załadowano konfigurację: {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd ładowania konfiguracji '{config_name}': {e}")
            return False
    
    def save_config(self, config_name: str) -> bool:
        """Zapisz aktualną konfigurację do pliku"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_name}.cfg")
            
            parser = configparser.ConfigParser()
            
            # Sekcja podstawowa
            parser['BASIC'] = {
                'station_id': str(self.config_data.get('STATION_ID', '')),
                'current_text_format': str(self.config_data.get('CURRENT_TEXT_FORMAT', '')),
                'layer_line': str(self.config_data.get('LAYER_LINE', '')),
                'layer_text': str(self.config_data.get('LAYER_TEXT', '')),
            }
            
            # Sekcja SVG
            parser['SVG'] = {
                'svg_width': str(self.config_data.get('SVG_WIDTH', 1600)),
                'svg_height': str(self.config_data.get('SVG_HEIGHT', 800)),
                'margin': str(self.config_data.get('MARGIN', 2.0)),
            }
            
            # Sekcja parametrów wyszukiwania
            parser['SEARCH'] = {
                'search_radius': str(self.config_data.get('SEARCH_RADIUS', 6.0)),
                'text_location': str(self.config_data.get('TEXT_LOCATION', 'above')),
                'y_tolerance': str(self.config_data.get('Y_TOLERANCE', 0.01)),
                'x_tolerance': str(self.config_data.get('X_TOLERANCE', 0.01)),
                'cluster_distance_threshold': str(self.config_data.get('CLUSTER_DISTANCE_THRESHOLD', 300.0)),
                'max_distance': str(self.config_data.get('MAX_DISTANCE', 10.0)),
            }
            
            # Sekcja parametrów segmentacji
            parser['SEGMENTATION'] = {
                'polyline_processing_mode': str(self.config_data.get('POLYLINE_PROCESSING_MODE', 'individual_segments')),
                'segment_merge_gap_tolerance': str(self.config_data.get('SEGMENT_MERGE_GAP_TOLERANCE', 1.0)),
                'max_merge_distance': str(self.config_data.get('MAX_MERGE_DISTANCE', 5.0)),
            }
            
            # Sekcja kolorów
            parser['COLORS'] = {
                'assigned_segment_color': str(self.config_data.get('ASSIGNED_SEGMENT_COLOR', '#00778B')),
                'unassigned_segment_color': str(self.config_data.get('UNASSIGNED_SEGMENT_COLOR', '#FFC0CB')),
                'text_segment_color': str(self.config_data.get('TEXT_SEGMENT_COLOR', '#000000')),
                'segment_center_color_assigned': str(self.config_data.get('SEGMENT_CENTER_COLOR_ASSIGNED', '#FFFB00')),
                'segment_center_color_unassigned': str(self.config_data.get('SEGMENT_CENTER_COLOR_UNASSIGNED', '#FF7B00')),
                'text_color_assigned': str(self.config_data.get('TEXT_COLOR_ASSIGNED', '#00FF15')),
                'text_color_unassigned': str(self.config_data.get('TEXT_COLOR_UNASSIGNED', '#FF0000')),
            }
            
            # Sekcja plików
            parser['FILES'] = {
                'default_dxf_file': str(self.config_data.get('DEFAULT_DXF_FILE', 'input.dxf')),
                'structured_svg_output': str(self.config_data.get('STRUCTURED_SVG_OUTPUT', 'output_structured.svg')),
            }
            
            # Sekcja wizualizacji
            parser['VISUALIZATION'] = {
                'show_text_dots': str(self.config_data.get('SHOW_TEXT_DOTS', True)),
                'show_text_labels': str(self.config_data.get('SHOW_TEXT_LABELS', True)),
                'show_string_labels': str(self.config_data.get('SHOW_STRING_LABELS', True)),
                'show_segment_centers': str(self.config_data.get('SHOW_SEGMENT_CENTERS', True)),
                'show_segment_labels': str(self.config_data.get('SHOW_SEGMENT_LABELS', True)),
                'dot_radius': str(self.config_data.get('DOT_RADIUS', 0.25)),
                'text_size': str(self.config_data.get('TEXT_SIZE', 1)),
                'text_opacity': str(self.config_data.get('TEXT_OPACITY', 0.5)),
                'string_label_offset': str(self.config_data.get('STRING_LABEL_OFFSET', 0)),
                'mptt_height': str(self.config_data.get('MPTT_HEIGHT', 1)),
                'segment_min_width': str(self.config_data.get('SEGMENT_MIN_WIDTH', 0)),
            }
            
            # Sekcja zaawansowanego formatowania
            import json
            # Escape % dla ConfigParser (% -> %%)
            additional_vars_json = json.dumps(self.config_data.get('ADVANCED_ADDITIONAL_VARS', {}))
            additional_vars_json = additional_vars_json.replace('%', '%%')
            
            parser['ADVANCED_FORMATTING'] = {
                'use_advanced_formatting': str(self.config_data.get('USE_ADVANCED_FORMATTING', False)),
                'advanced_input_format': str(self.config_data.get('ADVANCED_INPUT_FORMAT', '')),
                'advanced_output_format': str(self.config_data.get('ADVANCED_OUTPUT_FORMAT', '')),
                'advanced_additional_vars': additional_vars_json,
            }
            
            # Zapisz do pliku
            with open(config_path, 'w', encoding='utf-8') as configfile:
                parser.write(configfile)
            
            self.current_config_name = config_name
            logger.info(f"Zapisano konfigurację: {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd zapisywania konfiguracji '{config_name}': {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _convert_value(self, value: str) -> Any:
        """Konwertuj wartość tekstową na odpowiedni typ"""
        # JSON dla zaawansowanych zmiennych (unescape %% -> %)
        if value.startswith('{') and value.endswith('}'):
            try:
                import json
                # Przywróć oryginalny format % z %%
                unescaped_value = value.replace('%%', '%')
                return json.loads(unescaped_value)
            except json.JSONDecodeError:
                pass
        
        # Boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Float
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # String (pozostaw bez zmian)
        return value
    
    def get(self, key: str, default=None):
        """Pobierz wartość z konfiguracji"""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Ustaw wartość w konfiguracji"""
        self.config_data[key] = value
        logger.debug(f"Ustawiono: {key} = {value}")
    
    def get_text_formats(self) -> Dict:
        """Pobierz dostępne formaty tekstów"""
        return config.TEXT_FORMATS
    
    def get_text_locations(self) -> list:
        """Pobierz dostępne lokalizacje tekstów"""
        return ["above", "below", "any"]
    
    def apply_to_config_module(self):
        """Zastosuj aktualną konfigurację do modułu config"""
        for key, value in self.config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
                logger.debug(f"Zastosowano do config.{key} = {value}")


class ConfigTab:
    """Zakładka konfiguracji w GUI"""
    
    def __init__(self, parent, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        """Utwórz interfejs zakładki konfiguracji"""
        # Główny frame z przewijaniem
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sekcja zarządzania konfiguracją
        config_mgmt_frame = ttk.LabelFrame(main_frame, text="Zarządzanie konfiguracją")
        config_mgmt_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Nazwa konfiguracji
        ttk.Label(config_mgmt_frame, text="Nazwa konfiguracji:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_name_var = tk.StringVar(value=self.config_manager.current_config_name)
        self.config_name_entry = ttk.Entry(config_mgmt_frame, textvariable=self.config_name_var, width=30)
        self.config_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Przyciski zarządzania
        buttons_frame = ttk.Frame(config_mgmt_frame)
        buttons_frame.grid(row=0, column=2, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Wczytaj", command=self.load_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Zapisz", command=self.save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Nowy", command=self.new_config).pack(side=tk.LEFT, padx=2)
        
        # Lista dostępnych konfiguracji
        ttk.Label(config_mgmt_frame, text="Dostępne konfiguracje:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_listbox = tk.Listbox(config_mgmt_frame, height=3)
        self.config_listbox.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        self.config_listbox.bind('<Double-1>', self.on_config_select)
        
        # Sekcja podstawowych ustawień
        basic_frame = ttk.LabelFrame(main_frame, text="Podstawowe ustawienia")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        row = 0
        
        # Station ID
        ttk.Label(basic_frame, text="ID Stacji:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.station_id_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.station_id_var, width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Station Number
        ttk.Label(basic_frame, text="Numer Stacji:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.station_number_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.station_number_var, width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # ID Format
        ttk.Label(basic_frame, text="Format ID:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.id_format_var = tk.StringVar()
        self.id_format_combo = ttk.Combobox(basic_frame, textvariable=self.id_format_var,
                                           values=["01-02/03", "05-06/07"],
                                           state='readonly', width=18)
        self.id_format_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        self.id_format_combo.bind('<<ComboboxSelected>>', self.on_id_format_change)
        row += 1
        
        # Opis formatu ID
        self.id_format_description_label = ttk.Label(basic_frame, text="", foreground="green", wraplength=400)
        self.id_format_description_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # ===== SEKCJA ZAAWANSOWANEGO FORMATOWANIA =====
        format_frame = ttk.LabelFrame(main_frame, text="🔧 Zaawansowane Formatowanie Tekstów")
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        format_row = 0
        
        # Checkbox - użyj zaawansowanego formatowania
        self.use_advanced_formatting_var = tk.BooleanVar()
        ttk.Checkbutton(format_frame, text="🚀 Użyj zaawansowanego formatowania tekstów", 
                       variable=self.use_advanced_formatting_var,
                       command=self.on_advanced_formatting_toggle).grid(row=format_row, column=0, columnspan=3, 
                                                                        sticky=tk.W, padx=5, pady=5)
        format_row += 1
        
        # Frame dla ustawień zaawansowanych (początkowo ukryty)
        self.advanced_format_controls = ttk.Frame(format_frame)
        self.advanced_format_controls.grid(row=format_row, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=5)
        format_row += 1
        
        # Input format
        ttk.Label(self.advanced_format_controls, text="Format Input:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.advanced_input_format_var = tk.StringVar()
        input_entry = ttk.Entry(self.advanced_format_controls, textvariable=self.advanced_input_format_var, width=40)
        input_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        
        # Output format
        ttk.Label(self.advanced_format_controls, text="Format Output:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.advanced_output_format_var = tk.StringVar()
        output_entry = ttk.Entry(self.advanced_format_controls, textvariable=self.advanced_output_format_var, width=40)
        output_entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        
        # Przycisk konfiguracji zaawansowanej
        config_btn = ttk.Button(self.advanced_format_controls, text="⚙️ Konfiguracja Zaawansowana", 
                               command=self.open_advanced_formatter)
        config_btn.grid(row=2, column=0, columnspan=3, pady=10)
        
        # ===== LEGACY FORMAT (dla kompatybilności wstecznej) =====
        legacy_frame = ttk.LabelFrame(main_frame, text="📝 Legacy Format Tekstów (stary system)")
        legacy_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Format tekstów (stary system)
        ttk.Label(legacy_frame, text="Format tekstów:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.text_format_var = tk.StringVar()
        self.text_format_combo = ttk.Combobox(legacy_frame, textvariable=self.text_format_var, 
                                             values=list(self.config_manager.get_text_formats().keys()),
                                             state='readonly', width=18)
        self.text_format_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.text_format_combo.bind('<<ComboboxSelected>>', self.on_text_format_change)
        
        # Opis formatu tekstów
        self.format_description_label = ttk.Label(legacy_frame, text="", foreground="blue", wraplength=400)
        self.format_description_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        # ===== WARSTWY I LOKALIZACJA =====
        layers_frame = ttk.LabelFrame(main_frame, text="🗂️ Warstwy i Lokalizacja")
        layers_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Warstwy
        ttk.Label(layers_frame, text="Warstwa linii:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.layer_line_var = tk.StringVar()
        ttk.Entry(layers_frame, textvariable=self.layer_line_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(layers_frame, text="Warstwa tekstów:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.layer_text_var = tk.StringVar()
        ttk.Entry(layers_frame, textvariable=self.layer_text_var, width=30).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Lokalizacja tekstów
        ttk.Label(layers_frame, text="Lokalizacja tekstów:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.text_location_var = tk.StringVar()
        text_location_combo = ttk.Combobox(layers_frame, textvariable=self.text_location_var,
                                          values=self.config_manager.get_text_locations(),
                                          state='readonly', width=18)
        text_location_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Sekcja parametrów
        params_frame = ttk.LabelFrame(main_frame, text="Parametry wyszukiwania")
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        row = 0
        
        # Search radius
        ttk.Label(params_frame, text="Promień wyszukiwania:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.search_radius_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.search_radius_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Margin
        ttk.Label(params_frame, text="Margines:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.margin_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.margin_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Cluster distance threshold
        ttk.Label(params_frame, text="Próg odległości klastrów:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.cluster_distance_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.cluster_distance_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Max distance
        ttk.Label(params_frame, text="Maks. odległość:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_distance_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.max_distance_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # MPTT Height
        ttk.Label(params_frame, text="Szerokość MPTT:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.mptt_height_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.mptt_height_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Sekcja wymiarów SVG
        svg_frame = ttk.LabelFrame(main_frame, text="Wymiary SVG")
        svg_frame.pack(fill=tk.X, pady=(0, 10))
        
        row = 0
        
        # SVG width
        ttk.Label(svg_frame, text="Szerokość SVG:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.svg_width_var = tk.StringVar()
        ttk.Entry(svg_frame, textvariable=self.svg_width_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # SVG height
        ttk.Label(svg_frame, text="Wysokość SVG:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.svg_height_var = tk.StringVar()
        ttk.Entry(svg_frame, textvariable=self.svg_height_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Sekcja plików
        files_frame = ttk.LabelFrame(main_frame, text="Pliki")
        files_frame.pack(fill=tk.X, pady=(0, 10))
        
        row = 0
        
        # Domyślny plik DXF
        ttk.Label(files_frame, text="Domyślny plik DXF:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.default_dxf_var = tk.StringVar()
        ttk.Entry(files_frame, textvariable=self.default_dxf_var, width=30).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Strukturalny SVG
        ttk.Label(files_frame, text="Strukturalny SVG:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.structured_svg_var = tk.StringVar()
        ttk.Entry(files_frame, textvariable=self.structured_svg_var, width=30).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Przyciski akcji
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Zastosuj zmiany", command=self.apply_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Przywróć domyślne", command=self.reset_to_defaults).pack(side=tk.LEFT, padx=5)
        
        self.refresh_config_list()
    
    def refresh_config_list(self):
        """Odśwież listę dostępnych konfiguracji"""
        self.config_listbox.delete(0, tk.END)
        configs = self.config_manager.get_available_configs()
        for config_name in configs:
            self.config_listbox.insert(tk.END, config_name)
    
    def load_current_config(self):
        """Załaduj aktualną konfigurację do interfejsu"""
        self.station_id_var.set(self.config_manager.get('STATION_ID', ''))
        self.station_number_var.set(self.config_manager.get('STATION_NUMBER', '01'))
        self.id_format_var.set(self.config_manager.get('ID_FORMAT', '01-02/03'))
        self.text_format_var.set(self.config_manager.get('CURRENT_TEXT_FORMAT', ''))
        self.layer_line_var.set(self.config_manager.get('LAYER_LINE', ''))
        self.layer_text_var.set(self.config_manager.get('LAYER_TEXT', ''))
        self.text_location_var.set(self.config_manager.get('TEXT_LOCATION', 'above'))
        self.search_radius_var.set(str(self.config_manager.get('SEARCH_RADIUS', 6.0)))
        self.margin_var.set(str(self.config_manager.get('MARGIN', 2.0)))
        self.cluster_distance_var.set(str(self.config_manager.get('CLUSTER_DISTANCE_THRESHOLD', 300.0)))
        self.max_distance_var.set(str(self.config_manager.get('MAX_DISTANCE', 10.0)))
        self.mptt_height_var.set(str(self.config_manager.get('MPTT_HEIGHT', 1)))
        self.svg_width_var.set(str(self.config_manager.get('SVG_WIDTH', 1600)))
        self.svg_height_var.set(str(self.config_manager.get('SVG_HEIGHT', 800)))
        self.default_dxf_var.set(self.config_manager.get('DEFAULT_DXF_FILE', 'input.dxf'))
        self.structured_svg_var.set(self.config_manager.get('STRUCTURED_SVG_OUTPUT', 'output_structured.svg'))
        
        # Zaawansowane formatowanie
        self.use_advanced_formatting_var.set(self.config_manager.get('USE_ADVANCED_FORMATTING', False))
        self.advanced_input_format_var.set(self.config_manager.get('ADVANCED_INPUT_FORMAT', ''))
        self.advanced_output_format_var.set(self.config_manager.get('ADVANCED_OUTPUT_FORMAT', ''))
        
        # Trigger toggle dla pokazania/ukrycia kontrolek
        self.on_advanced_formatting_toggle()
        
        # Aktualizuj opisy formatów
        self.on_text_format_change()
        self.on_id_format_change()
    
    def on_text_format_change(self, event=None):
        """Aktualizuj opis formatu tekstów"""
        format_key = self.text_format_var.get()
        formats = self.config_manager.get_text_formats()
        if format_key in formats:
            description = formats[format_key]['description']
            self.format_description_label.config(text=f"Opis: {description}")
    
    def on_id_format_change(self, event=None):
        """Aktualizuj opis formatu ID"""
        format_id = self.id_format_var.get()
        if format_id == "01-02/03":
            description = "Format: 01-MPPT, 02-String, 03-Inverter (np. 01-01/02)"
        elif format_id == "05-06/07":
            description = "Format: 05-Station, 06-MPPT, 07-Inverter (np. 01-01/02)"
        else:
            description = ""
        self.id_format_description_label.config(text=description)
    
    def on_config_select(self, event):
        """Obsłuż wybór konfiguracji z listy"""
        selection = self.config_listbox.curselection()
        if selection:
            config_name = self.config_listbox.get(selection[0])
            self.config_name_var.set(config_name)
    
    def load_config(self):
        """Wczytaj wybraną konfigurację"""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            messagebox.showwarning("Ostrzeżenie", "Wprowadź nazwę konfiguracji")
            return
        
        if self.config_manager.load_config(config_name):
            self.load_current_config()
            messagebox.showinfo("Sukces", f"Wczytano konfigurację: {config_name}")
        else:
            messagebox.showerror("Błąd", f"Nie można wczytać konfiguracji: {config_name}")
    
    def save_config(self):
        """Zapisz aktualną konfigurację"""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            messagebox.showwarning("Ostrzeżenie", "Wprowadź nazwę konfiguracji")
            return
        
        # Zapisz aktualne wartości do config_manager
        self.save_current_values()
        
        if self.config_manager.save_config(config_name):
            self.refresh_config_list()
            messagebox.showinfo("Sukces", f"Zapisano konfigurację: {config_name}")
        else:
            messagebox.showerror("Błąd", f"Nie można zapisać konfiguracji: {config_name}")
    
    def new_config(self):
        """Utwórz nową konfigurację"""
        self.config_name_var.set("nowa_konfiguracja")
        self.reset_to_defaults()
    
    def save_current_values(self):
        """Zapisz aktualne wartości z interfejsu do config_manager"""
        try:
            self.config_manager.set('STATION_ID', self.station_id_var.get())
            self.config_manager.set('STATION_NUMBER', self.station_number_var.get())
            self.config_manager.set('ID_FORMAT', self.id_format_var.get())
            self.config_manager.set('CURRENT_TEXT_FORMAT', self.text_format_var.get())
            self.config_manager.set('LAYER_LINE', self.layer_line_var.get())
            self.config_manager.set('LAYER_TEXT', self.layer_text_var.get())
            self.config_manager.set('TEXT_LOCATION', self.text_location_var.get())
            self.config_manager.set('SEARCH_RADIUS', float(self.search_radius_var.get()))
            self.config_manager.set('MARGIN', float(self.margin_var.get()))
            self.config_manager.set('CLUSTER_DISTANCE_THRESHOLD', float(self.cluster_distance_var.get()))
            self.config_manager.set('MAX_DISTANCE', float(self.max_distance_var.get()))
            self.config_manager.set('MPTT_HEIGHT', float(self.mptt_height_var.get()))
            self.config_manager.set('SVG_WIDTH', int(self.svg_width_var.get()))
            self.config_manager.set('SVG_HEIGHT', int(self.svg_height_var.get()))
            self.config_manager.set('DEFAULT_DXF_FILE', self.default_dxf_var.get())
            self.config_manager.set('STRUCTURED_SVG_OUTPUT', self.structured_svg_var.get())
            
            # Zaawansowane formatowanie
            self.config_manager.set('USE_ADVANCED_FORMATTING', self.use_advanced_formatting_var.get())
            self.config_manager.set('ADVANCED_INPUT_FORMAT', self.advanced_input_format_var.get())
            self.config_manager.set('ADVANCED_OUTPUT_FORMAT', self.advanced_output_format_var.get())
            # Additional vars będą ustawione przez advanced formatter
            
        except ValueError as e:
            raise ValueError(f"Nieprawidłowa wartość liczbowa: {e}")
    
    def on_advanced_formatting_toggle(self):
        """Pokaż/ukryj kontrolki zaawansowanego formatowania"""
        if self.use_advanced_formatting_var.get():
            self.advanced_format_controls.grid()
        else:
            self.advanced_format_controls.grid_remove()
    
    def open_advanced_formatter(self):
        """Otwórz okno zaawansowanego formatera"""
        try:
            from src.gui.advanced_formatter_gui import show_advanced_formatter_window
            
            # Otwórz okno formatera
            formatter_gui = show_advanced_formatter_window()
            
            # Załaduj aktualne ustawienia
            formatter_gui.input_format_var.set(self.advanced_input_format_var.get())
            formatter_gui.output_format_var.set(self.advanced_output_format_var.get())
            
            # Załaduj dodatkowe zmienne z config_manager
            additional_vars = self.config_manager.get('ADVANCED_ADDITIONAL_VARS', {})
            formatter_gui.additional_vars = additional_vars.copy()
            formatter_gui.update_vars_list()
            
            def on_formatter_save():
                """Callback po zapisaniu w formaterze"""
                # Pobierz zaktualizowane wartości z formatera
                self.advanced_input_format_var.set(formatter_gui.input_format_var.get())
                self.advanced_output_format_var.set(formatter_gui.output_format_var.get())
                self.config_manager.set('ADVANCED_ADDITIONAL_VARS', formatter_gui.additional_vars.copy())
                
            # Dodaj callback (jeśli formatter obsługuje)
            if hasattr(formatter_gui, 'set_save_callback'):
                formatter_gui.set_save_callback(on_formatter_save)
                
        except ImportError as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć zaawansowanego formatera: {e}")
    
    def apply_changes(self):
        """Zastosuj zmiany w konfiguracji"""
        try:
            self.save_current_values()
            self.config_manager.apply_to_config_module()
            messagebox.showinfo("Sukces", "Zastosowano zmiany w konfiguracji")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zastosować zmian: {e}")
    
    def reset_to_defaults(self):
        """Przywróć domyślne ustawienia"""
        self.config_manager.load_defaults()
        self.load_current_config()
        messagebox.showinfo("Sukces", "Przywrócono domyślne ustawienia")
