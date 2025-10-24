#!/usr/bin/env python3
"""
Enhanced SVG Viewer with improved performance and interactive capabilities
Features:
- Smooth zooming and panning
- Efficient viewport-based rendering
- Interactive element selection (text and lines)
- Better initial fit-to-window
- Performance optimizations
"""
import tkinter as tk
from tkinter import ttk
import os
import xml.etree.ElementTree as ET
import math
from typing import Optional, Tuple, List, Callable, Dict, Any


class InteractiveElement:
    """Represents an interactive SVG element"""
    def __init__(self, element_id: str, element_type: str, bounds: Tuple[float, float, float, float], 
                 canvas_id: int, svg_data: Dict[str, Any]):
        self.element_id = element_id
        self.element_type = element_type  # 'text', 'line', 'rect', etc.
        self.bounds = bounds  # (x1, y1, x2, y2) in SVG coordinates
        self.canvas_id = canvas_id
        self.svg_data = svg_data
        self.selected = False
        self.assigned_group = None  # For tracking assigned elements (text + segments)


class EnhancedSVGViewer:
    """Enhanced SVG viewer with performance optimizations and interactivity"""
    
    def __init__(self, parent, on_element_select: Optional[Callable] = None):
        self.parent = parent
        self.on_element_select = on_element_select  # Callback for element selection
        
        # Viewport parameters
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.svg_content = None
        self.original_size = (800, 600)
        self.svg_bounds = (0, 0, 800, 600)  # Actual content bounds
        
        # Performance optimizations
        self.viewport_buffer = 100  # Zwiększony buffer dla lepszego renderowania
        self.max_elements_per_frame = 999999  # Renderuj wszystkie elementy bez limitu
        self.render_cache = {}
        self.last_render_params = None
        self.needs_full_render = True
        
        # Interactive elements
        self.interactive_elements: Dict[int, InteractiveElement] = {}
        self.selected_elements: List[InteractiveElement] = []
        self.hover_element: Optional[InteractiveElement] = None
        
        # Colors and styles
        self.colors = {
            'selected': '#FF6B6B',
            'hover': '#4ECDC4',
            'text': '#2C3E50',
            'line': '#34495E',
            'background': '#FFFFFF',
            'hover_segment': '#FFB6C1',  # Jasny różowy dla segmentów
            'hover_text': '#8B008B'       # Ciemny fioletowy dla tekstów
        }
        
        # Hover state for assigned groups
        self.hovered_group_elements: List[InteractiveElement] = []
        
        # Mouse interaction
        self.last_click_pos = (0, 0)
        self.is_dragging = False
        self.drag_threshold = 5  # pixels
        
        # Multi-selection support
        self.selection_start_pos = None
        self.selection_rect = None
        self.is_box_selecting = False
        self.current_selection_mode = 'single'  # 'single' or 'multi'
        
        # Assignment state
        self.selected_text_element = None
        self.selected_line_element = None
        self.assignment_mode = True  # Start in assignment mode
        
        # Assignment callback
        self.on_assignment_made = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        self.create_toolbar()
        
        # Canvas with scrollbars
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.colors['background'])
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.setup_event_bindings()
        
    def create_toolbar(self):
        """Create toolbar with controls - NOWY PASEK Z IKONAMI I TOOLTIPAMI"""
        # Ciemny motyw kolorów (zgodny z interactive_gui_new.py)
        colors = {
            'layer1_bg': '#1a1a1a',
            'layer2_bg': '#2d2d2d',
            'layer3_bg': '#3a3a3a',
            'button_bg': '#333333',
            'button_hover': '#404040',
            'button_disabled': '#262626',
            'text_disabled': '#666666',
            'accent': '#4a9eff',
            'accent_hover': '#5ab0ff',
            'text': '#e0e0e0',
            'border': '#404040'
        }
        
        # Toolbar z zaokrąglonym tłem (warstwa 1)
        toolbar_container = tk.Frame(self.main_frame, bg=colors['layer1_bg'])
        toolbar_container.pack(fill=tk.X, padx=5, pady=(5, 5))
        
        # Canvas dla zaokrąglonego tła
        toolbar_canvas = tk.Canvas(toolbar_container, height=60,
                                   bg=colors['layer1_bg'],
                                   highlightthickness=0, borderwidth=0)
        toolbar_canvas.pack(fill=tk.X)
        
        # Rysuj zaokrąglone tło toolbara
        def draw_toolbar_bg(event=None):
            toolbar_canvas.delete('toolbar_bg')
            width = toolbar_canvas.winfo_width()
            height = 60
            if width > 1:
                from src.gui.unified_config_tab import create_rounded_rectangle
                create_rounded_rectangle(toolbar_canvas, 0, 0, width, height,
                                       radius=16,
                                       fill=colors['layer1_bg'],
                                       outline='', width=0,
                                       tags='toolbar_bg')
        
        toolbar_canvas.bind('<Configure>', draw_toolbar_bg)
        toolbar_canvas.after(50, draw_toolbar_bg)
        
        # Frame wewnętrzny na przyciskach (na Canvas)
        toolbar = tk.Frame(toolbar_canvas, bg=colors['layer1_bg'], height=50)
        toolbar_canvas.create_window(5, 5, window=toolbar, anchor='nw', width=990)
        
        # Kontener wewnętrzny
        toolbar_inner = tk.Frame(toolbar, bg=colors['layer1_bg'])
        toolbar_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Pomocnicza funkcja do prostego tooltipu
        def create_tooltip(widget, text):
            """Tworzy prosty tooltip dla widgetu"""
            tooltip = None
            timeout_id = None
            
            def show_tooltip(event):
                nonlocal tooltip
                if tooltip:
                    return
                
                # Użyj pozycji kursora z eventu dla Canvas
                x = event.x_root + 10
                y = event.y_root + 10
                
                tooltip = tk.Toplevel(widget)
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{x}+{y}")
                
                label = tk.Label(tooltip, text=text, 
                               bg=colors['layer3_bg'], 
                               fg=colors['text'],
                               relief=tk.SOLID, 
                               borderwidth=1,
                               font=('Segoe UI', 9),
                               padx=5, pady=3)
                label.pack()
            
            def schedule_tooltip(event):
                nonlocal timeout_id
                timeout_id = widget.after(500, lambda: show_tooltip(event))
            
            def hide_tooltip(event):
                nonlocal tooltip, timeout_id
                if timeout_id:
                    widget.after_cancel(timeout_id)
                    timeout_id = None
                if tooltip:
                    tooltip.destroy()
                    tooltip = None
            
            widget.bind('<Enter>', schedule_tooltip)
            widget.bind('<Leave>', hide_tooltip)
        
        # Pomocnicza funkcja do tworzenia okrągłych przycisków z ikonami
        def create_round_icon_button(parent, icon, command, tooltip_text, is_toggle=False, toggle_value=None):
            """Tworzy okrągły przycisk tylko z ikoną"""
            btn_canvas = tk.Canvas(parent, width=40, height=40,
                                  bg=colors['layer1_bg'],
                                  highlightthickness=0, borderwidth=0)
            btn_canvas.pack(side=tk.LEFT, padx=3)
            
            # Rysuj okrąg
            circle = btn_canvas.create_oval(2, 2, 38, 38,
                                           fill=colors['button_bg'],
                                           outline='', width=0)
            # Ikona - dla emoji używaj anchor='center' zamiast pozycji tekstowej
            icon_id = btn_canvas.create_text(20, 20, text=icon,
                                            fill=colors['text'],
                                            font=('Segoe UI', 16),
                                            anchor='center')
            
            # Przechowuj elementy dla update
            btn_canvas.circle = circle
            btn_canvas.icon_id = icon_id
            btn_canvas.toggle_value = toggle_value
            btn_canvas.is_toggle = is_toggle
            
            # Kliknięcie
            if command:
                btn_canvas.bind('<Button-1>', lambda e: command())
            
            # Hover
            def on_enter(event):
                btn_canvas.itemconfig(circle, fill=colors['button_hover'])
                btn_canvas.config(cursor='hand2')
            
            def on_leave(event):
                btn_canvas.itemconfig(circle, fill=colors['button_bg'])
                btn_canvas.config(cursor='')
            
            btn_canvas.bind('<Enter>', on_enter)
            btn_canvas.bind('<Leave>', on_leave)
            
            # Tooltip
            if tooltip_text:
                create_tooltip(btn_canvas, tooltip_text)
            
            return btn_canvas
        
        # LEWO: Przyciski trybu SVG (będą kontrolowane z głównego GUI)
        mode_frame = tk.Frame(toolbar_inner, bg=colors['layer1_bg'])
        mode_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Placeholder dla przycisków trybu - zostaną dodane przez główne GUI
        self.mode_buttons_frame = mode_frame
        self.toolbar_colors = colors  # Udostępnij kolory dla głównego GUI
        self.create_round_icon_button = create_round_icon_button  # Udostępnij funkcję
        self.create_tooltip_func = create_tooltip  # Udostępnij funkcję tooltip
        
        # Separator
        sep = tk.Frame(toolbar_inner, bg=colors['border'], width=2)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # ŚRODEK: Zoom controls
        zoom_frame = tk.Frame(toolbar_inner, bg=colors['layer1_bg'])
        zoom_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        create_round_icon_button(zoom_frame, "🔍", self.fit_to_window, 
                                "Dopasuj do okna\nAutomatycznie skaluje widok SVG")
        create_round_icon_button(zoom_frame, "➕", self.zoom_in, 
                                "Powiększ\nZwiększa zoom o 25%")
        create_round_icon_button(zoom_frame, "➖", self.zoom_out, 
                                "Pomniejsz\nZmniejsza zoom o 25%")
        create_round_icon_button(zoom_frame, "🏠", self.reset_view, 
                                "Reset widoku\nPrzywraca początkową pozycję")
        
        # Zoom level display
        self.zoom_label = tk.Label(toolbar_inner, text="100%",
                                   bg=colors['layer1_bg'],
                                   fg=colors['text'],
                                   font=('Segoe UI', 10))
        self.zoom_label.pack(side=tk.LEFT, padx=10)
        
        # Separator
        sep2 = tk.Frame(toolbar_inner, bg=colors['border'], width=2)
        sep2.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # PRAWO: Assignment controls
        assignment_frame = tk.Frame(toolbar_inner, bg=colors['layer1_bg'])
        assignment_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Przypisz Tekst
        self.assign_btn_canvas = create_round_icon_button(
            assignment_frame, "✅",
            self.assign_text_to_line,
            "Przypisz Tekst\nKliknij tekst, potem linię,\nnaciśnij przycisk")
        self.assign_btn = self.assign_btn_canvas  # Zachowaj referencję
        
        # Wyczyść Linię
        self.clear_line_btn_canvas = create_round_icon_button(
            assignment_frame, "🗑️",
            self.clear_line_assignments,
            "Wyczyść Linię\nUsuwa wszystkie przypisania\ndla wybranej linii")
        self.clear_line_btn = self.clear_line_btn_canvas  # Zachowaj referencję
        
        # Wyczyść Wybór
        create_round_icon_button(
            assignment_frame, "❌",
            self.clear_assignment_selection,
            "Wyczyść Wybór\nUsuwa aktualny wybór\ntekstu i linii")
        
        # Instructions / status
        self.instruction_label = tk.Label(toolbar_inner,
                                         text="Kliknij tekst, potem linię, naciśnij ✅",
                                         bg=colors['layer2_bg'],
                                         fg=colors['text'],
                                         font=('Segoe UI', 9, 'italic'))
        self.instruction_label.pack(side=tk.RIGHT, padx=10)
        
        # Selection info na końcu (prawy róg)
        self.selection_label = tk.Label(toolbar_inner, text="",
                                        bg=colors['layer2_bg'],
                                        fg=colors['text'],
                                        font=('Segoe UI', 9))
        self.selection_label.pack(side=tk.RIGHT, padx=10)
        
    def setup_event_bindings(self):
        """Setup event bindings for interactions"""
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux
        
        # Mouse clicks and drags
        self.canvas.bind("<Button-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # Mouse motion for hover effects
        self.canvas.bind("<Motion>", self.on_mouse_motion)
        
        # Keyboard shortcuts
        self.canvas.bind("<Key>", self.on_key_press)
        self.canvas.focus_set()
        
        # Canvas resize
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Key bindings for multi-selection
        self.canvas.bind("<Control-Button-1>", self.on_ctrl_click)
        self.canvas.bind("<Shift-Button-1>", self.on_shift_click)
        self.canvas.bind("<Delete>", self.on_delete_key)
        self.canvas.bind("<BackSpace>", self.on_delete_key)
        
    def load_svg(self, svg_path: str, preserve_viewport: bool = False):
        """Load SVG file with improved parsing
        
        Args:
            svg_path: Path to SVG file
            preserve_viewport: If True, don't reset viewport position
        """
        try:
            if not os.path.exists(svg_path):
                self.display_message("SVG file not found", "error")
                return
                
            self.current_svg_file = svg_path
            
            # Read and parse SVG
            with open(svg_path, 'r', encoding='utf-8') as f:
                self.svg_content = f.read()
            
            # Parse SVG dimensions and content bounds
            self.parse_svg_metadata()
            
            # Clear cache and interactive elements
            self.render_cache.clear()
            self.interactive_elements.clear()
            self.selected_elements.clear()
            self.needs_full_render = True
            
            # Only fit to window if we're not preserving viewport
            if not preserve_viewport:
                self.fit_to_window()
            else:
                # Just render without changing viewport
                self.render_svg()
            
        except Exception as e:
            self.display_message(f"Error loading SVG: {str(e)}", "error")
    
    def parse_svg_metadata(self):
        """Parse SVG metadata to get dimensions and bounds"""
        try:
            root = ET.fromstring(self.svg_content)
            
            # Get SVG dimensions
            width = root.get('width', '800')
            height = root.get('height', '600')
            
            # Clean dimensions (remove units)
            width = ''.join(filter(lambda x: x.isdigit() or x == '.', width)) or '800'
            height = ''.join(filter(lambda x: x.isdigit() or x == '.', height)) or '600'
            
            self.original_size = (float(width), float(height))
            
            # Calculate actual content bounds by examining all elements
            self.calculate_content_bounds(root)
            
        except Exception as e:
            print(f"Error parsing SVG metadata: {e}")
            self.original_size = (800, 600)
            self.svg_bounds = (0, 0, 800, 600)
    
    def calculate_content_bounds(self, root):
        """Calculate the actual bounds of SVG content"""
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        def update_bounds(x, y):
            nonlocal min_x, min_y, max_x, max_y
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        
        # Check all elements for their bounds
        for elem in root.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            try:
                if tag == 'line':
                    x1, y1 = float(elem.get('x1', 0)), float(elem.get('y1', 0))
                    x2, y2 = float(elem.get('x2', 0)), float(elem.get('y2', 0))
                    update_bounds(x1, y1)
                    update_bounds(x2, y2)
                    
                elif tag in ['rect', 'image']:
                    x = float(elem.get('x', 0))
                    y = float(elem.get('y', 0))
                    w = float(elem.get('width', 0))
                    h = float(elem.get('height', 0))
                    update_bounds(x, y)
                    update_bounds(x + w, y + h)
                    
                elif tag == 'circle':
                    cx = float(elem.get('cx', 0))
                    cy = float(elem.get('cy', 0))
                    r = float(elem.get('r', 0))
                    update_bounds(cx - r, cy - r)
                    update_bounds(cx + r, cy + r)
                    
                elif tag == 'text':
                    x = float(elem.get('x', 0))
                    y = float(elem.get('y', 0))
                    update_bounds(x, y)
                    # Add some padding for text
                    update_bounds(x + 50, y + 20)
                    
            except (ValueError, TypeError):
                continue
        
        # Set bounds with some padding
        if min_x != float('inf'):
            padding = 20
            self.svg_bounds = (min_x - padding, min_y - padding, 
                             max_x + padding, max_y + padding)
        else:
            self.svg_bounds = (0, 0, self.original_size[0], self.original_size[1])
    
    def get_viewport_bounds(self) -> Tuple[float, float, float, float]:
        """Get current viewport bounds in SVG coordinates with generous buffer"""
        canvas_width = max(self.canvas.winfo_width(), 100)  # Minimum width
        canvas_height = max(self.canvas.winfo_height(), 100)  # Minimum height
        
        # Convert canvas bounds to SVG coordinates
        x1 = (-self.pan_x) / self.scale
        y1 = (-self.pan_y) / self.scale
        x2 = (canvas_width - self.pan_x) / self.scale
        y2 = (canvas_height - self.pan_y) / self.scale
        
        # Dodaj BARDZO DUŻY bufor (100%) aby zawsze renderować wszystkie elementy w pobliżu
        # To zapobiega znikaniu elementów podczas zoom/pan
        viewport_width = x2 - x1
        viewport_height = y2 - y1
        buffer_x = viewport_width * 1.0  # 100% bufora!
        buffer_y = viewport_height * 1.0
        
        return (x1 - buffer_x, y1 - buffer_y, x2 + buffer_x, y2 + buffer_y)
    
    def is_element_in_viewport(self, bounds: Tuple[float, float, float, float]) -> bool:
        """Check if element bounds intersect with viewport"""
        elem_x1, elem_y1, elem_x2, elem_y2 = bounds
        view_x1, view_y1, view_x2, view_y2 = self.get_viewport_bounds()
        
        # Proste sprawdzenie przecięcia (bez dodatkowego bufora - już jest w get_viewport_bounds)
        return not (elem_x2 < view_x1 or elem_x1 > view_x2 or 
                   elem_y2 < view_y1 or elem_y1 > view_y2)
    
    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """Transform SVG coordinates to canvas coordinates"""
        canvas_x = x * self.scale + self.pan_x
        canvas_y = y * self.scale + self.pan_y
        return canvas_x, canvas_y
    
    def inverse_transform_point(self, canvas_x: float, canvas_y: float) -> Tuple[float, float]:
        """Transform canvas coordinates to SVG coordinates"""
        svg_x = (canvas_x - self.pan_x) / self.scale
        svg_y = (canvas_y - self.pan_y) / self.scale
        return svg_x, svg_y
    
    def render_svg(self):
        """Render SVG with performance optimizations"""
        if not self.svg_content:
            return
        
        try:
            # Check if we need to render
            current_params = (self.scale, self.pan_x, self.pan_y, 
                            self.canvas.winfo_width(), self.canvas.winfo_height())
            
            if (current_params == self.last_render_params and 
                not self.needs_full_render):
                return
            
            self.render_svg_elements()
            self.last_render_params = current_params
            self.needs_full_render = False
            
            # Update UI
            self.update_zoom_label()
            
        except Exception as e:
            self.display_message(f"Render error: {str(e)}", "error")
    
    def render_svg_elements(self):
        """Render SVG elements with viewport culling"""
        if not self.svg_content:
            return
        
        # Save current selection state BEFORE clearing
        selected_text_group = None  # data-assignment-group dla tekstu
        selected_line_segment_id = None  # data-segment-id dla linii
        
        if self.selected_text_element:
            selected_text_group = self.selected_text_element.assigned_group
            if not selected_text_group:
                # Fallback: użyj content tekstu
                selected_text_group = self.selected_text_element.svg_data.get('content', '')
        
        if self.selected_line_element:
            # Dla segmentów użyj data-segment-id lub data-svg-number
            attrs = self.selected_line_element.svg_data.get('attributes', {})
            selected_line_segment_id = attrs.get('data-segment-id') or attrs.get('data-svg-number')
        
        # Parse SVG
        try:
            root = ET.fromstring(self.svg_content)
        except ET.ParseError as e:
            self.display_message(f"SVG parse error: {str(e)}", "error")
            return
        
        # Clear canvas and interactive elements
        self.canvas.delete("all")
        self.interactive_elements.clear()
        
        # Get viewport for culling
        viewport = self.get_viewport_bounds()
        elements_rendered = 0
        
        # Render elements by type with priority
        element_types = [
            ('rect', self.render_rectangle),
            ('line', self.render_line),
            ('circle', self.render_circle),
            ('text', self.render_text),
            ('polyline', self.render_polyline)
        ]
        
        for element_type, render_func in element_types:
            if elements_rendered >= self.max_elements_per_frame:
                break
                
            elements = self.find_elements(root, element_type)
            for elem in elements:
                if elements_rendered >= self.max_elements_per_frame:
                    break
                
                try:
                    bounds = self.get_element_bounds(elem, element_type)
                    if bounds and self.is_element_in_viewport(bounds):
                        canvas_id = render_func(elem)
                        if canvas_id:
                            # Parse assignment group from data-assignment-group attribute
                            assignment_group = elem.get('data-assignment-group', None)
                            
                            # TYLKO line, polyline i text są klikalne (segmenty i teksty)
                            # rect i circle (kropki, trójkąty) są renderowane ale NIE dodawane do interactive_elements
                            # Wykluczamy również text elementy z class='segment-label' lub class='text-marker'
                            is_clickable = element_type in ['line', 'polyline', 'text']
                            
                            # Dodatkowe filtrowanie dla text - wykluczaj etykiety
                            if element_type == 'text':
                                elem_class = elem.get('class', '')
                                if 'segment-label' in elem_class or 'text-marker' in elem_class:
                                    is_clickable = False
                            
                            if is_clickable:
                                # Create interactive element
                                interactive_elem = InteractiveElement(
                                    element_id=elem.get('id', f"{element_type}_{elements_rendered}"),
                                    element_type=element_type,
                                    bounds=bounds,
                                    canvas_id=canvas_id,
                                    svg_data={
                                        'element': elem,
                                        'content': elem.text or '',
                                        'attributes': dict(elem.attrib)
                                    }
                                )
                                # Ustaw grupę przypisania jeśli istnieje
                                if assignment_group:
                                    interactive_elem.assigned_group = assignment_group
                                
                                self.interactive_elements[canvas_id] = interactive_elem
                            
                            elements_rendered += 1
                            
                except Exception as e:
                    continue
        
        # Update scroll region
        self.update_scroll_region()
        
        # RESTORE selection state after re-rendering
        self.selected_text_element = None
        self.selected_line_element = None
        
        if selected_text_group or selected_line_segment_id:
            for canvas_id, elem in self.interactive_elements.items():
                # Restore text selection - dopasuj po assigned_group lub content
                if selected_text_group and elem.element_type == 'text':
                    if elem.assigned_group == selected_text_group:
                        self.selected_text_element = elem
                        self.set_element_style(elem, 'selected')
                    elif not elem.assigned_group:
                        # Fallback: dopasuj po content
                        if elem.svg_data.get('content', '') == selected_text_group:
                            self.selected_text_element = elem
                            self.set_element_style(elem, 'selected')
                
                # Restore line selection - dopasuj po data-segment-id
                if selected_line_segment_id and elem.element_type in ['line', 'polyline']:
                    attrs = elem.svg_data.get('attributes', {})
                    seg_id = attrs.get('data-segment-id') or attrs.get('data-svg-number')
                    if seg_id == selected_line_segment_id:
                        self.selected_line_element = elem
                        self.set_element_style(elem, 'selected')
        
        # Display render info
        self.display_render_info(elements_rendered)
    
    def find_elements(self, root, tag_name: str):
        """Find elements with specified tag, ignoring namespace"""
        elements = []
        for elem in root.iter():
            local_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if local_tag == tag_name:
                elements.append(elem)
        return elements
    
    def get_element_bounds(self, elem, element_type: str) -> Optional[Tuple[float, float, float, float]]:
        """Get element bounds in SVG coordinates with safety margin"""
        try:
            margin = 10  # Bezpieczny margines dla lepszego renderowania
            
            if element_type == 'line':
                x1 = float(elem.get('x1', 0))
                y1 = float(elem.get('y1', 0))
                x2 = float(elem.get('x2', 0))
                y2 = float(elem.get('y2', 0))
                return (min(x1, x2) - margin, min(y1, y2) - margin, 
                       max(x1, x2) + margin, max(y1, y2) + margin)
                
            elif element_type == 'rect':
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                w = float(elem.get('width', 0))
                h = float(elem.get('height', 0))
                return (x - margin, y - margin, x + w + margin, y + h + margin)
                
            elif element_type == 'circle':
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r = float(elem.get('r', 0))
                return (cx - r - margin, cy - r - margin, 
                       cx + r + margin, cy + r + margin)
                
            elif element_type == 'text':
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                # Estimate text bounds (rough approximation)
                text_width = len(elem.text or '') * 8
                text_height = 16
                return (x - margin, y - text_height - margin, 
                       x + text_width + margin, y + margin)
            
            elif element_type == 'polyline':
                # Parse polyline points
                points_str = elem.get('points', '')
                if not points_str:
                    return None
                
                coords = []
                points = points_str.replace(',', ' ').split()
                for i in range(0, len(points) - 1, 2):
                    try:
                        x, y = float(points[i]), float(points[i + 1])
                        coords.append((x, y))
                    except (ValueError, IndexError):
                        continue
                
                if not coords:
                    return None
                
                xs = [c[0] for c in coords]
                ys = [c[1] for c in coords]
                return (min(xs) - margin, min(ys) - margin, 
                       max(xs) + margin, max(ys) + margin)
                
        except (ValueError, TypeError):
            return None
        
        return None
    
    def render_line(self, elem) -> Optional[int]:
        """Render line element"""
        try:
            x1 = float(elem.get('x1', 0))
            y1 = float(elem.get('y1', 0))
            x2 = float(elem.get('x2', 0))
            y2 = float(elem.get('y2', 0))
            
            canvas_x1, canvas_y1 = self.transform_point(x1, y1)
            canvas_x2, canvas_y2 = self.transform_point(x2, y2)
            
            stroke = elem.get('stroke', self.colors['line'])
            stroke_width = max(float(elem.get('stroke-width', 1)) * self.scale, 1)
            
            return self.canvas.create_line(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                fill=stroke, width=stroke_width, capstyle=tk.ROUND,
                tags="interactive"
            )
            
        except (ValueError, TypeError):
            return None
    
    def render_rectangle(self, elem) -> Optional[int]:
        """Render rectangle element"""
        try:
            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))
            width = float(elem.get('width', 0))
            height = float(elem.get('height', 0))
            
            canvas_x1, canvas_y1 = self.transform_point(x, y)
            canvas_x2, canvas_y2 = self.transform_point(x + width, y + height)
            
            fill = elem.get('fill', 'white')
            stroke = elem.get('stroke', 'black')
            stroke_width = max(float(elem.get('stroke-width', 1)) * self.scale, 1)
            
            return self.canvas.create_rectangle(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                fill=fill, outline=stroke, width=stroke_width,
                tags="interactive"
            )
            
        except (ValueError, TypeError):
            return None
    
    def render_circle(self, elem) -> Optional[int]:
        """Render circle element"""
        try:
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            r = max(float(elem.get('r', 0)) * self.scale, 2)
            
            canvas_cx, canvas_cy = self.transform_point(cx, cy)
            
            fill = elem.get('fill', 'white')
            stroke = elem.get('stroke', 'black')
            
            return self.canvas.create_oval(
                canvas_cx - r, canvas_cy - r, canvas_cx + r, canvas_cy + r,
                fill=fill, outline=stroke, tags="interactive"
            )
            
        except (ValueError, TypeError):
            return None
    
    def render_text(self, elem) -> Optional[int]:
        """Render text element"""
        try:
            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))
            
            canvas_x, canvas_y = self.transform_point(x, y)
            
            fill = elem.get('fill', self.colors['text'])
            font_size = max(int(float(elem.get('font-size', 12)) * self.scale), 8)
            text_content = elem.text or ''
            
            # Don't truncate text as much - let users see more
            if len(text_content) > 50:
                text_content = text_content[:47] + "..."
            
            return self.canvas.create_text(
                canvas_x, canvas_y, text=text_content,
                fill=fill, font=("Arial", font_size), anchor="w",
                tags="interactive"
            )
            
        except (ValueError, TypeError):
            return None
    
    def render_polyline(self, elem) -> Optional[int]:
        """Render polyline element"""
        try:
            points_str = elem.get('points', '')
            if not points_str:
                return None
            
            # Parse points
            coords = []
            points = points_str.replace(',', ' ').split()
            for i in range(0, len(points) - 1, 2):
                x, y = float(points[i]), float(points[i + 1])
                canvas_x, canvas_y = self.transform_point(x, y)
                coords.extend([canvas_x, canvas_y])
            
            if len(coords) < 4:  # Need at least 2 points
                return None
            
            stroke = elem.get('stroke', self.colors['line'])
            stroke_width = max(float(elem.get('stroke-width', 1)) * self.scale, 1)
            fill = elem.get('fill', '')
            
            return self.canvas.create_line(
                *coords, fill=stroke, width=stroke_width,
                smooth=False, tags="interactive"
            )
            
        except (ValueError, TypeError):
            return None
    
    # Event handlers
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        # Get mouse position in canvas coordinates
        mouse_x = event.x
        mouse_y = event.y
        
        # Convert to SVG coordinates before zoom
        svg_x, svg_y = self.inverse_transform_point(mouse_x, mouse_y)
        
        # Determine zoom direction
        if event.delta > 0 or event.num == 4:  # Zoom in
            factor = 1.2
        else:  # Zoom out
            factor = 0.8
        
        # Calculate new scale with limits
        new_scale = self.scale * factor
        new_scale = max(0.05, min(new_scale, 20.0))  # Wider zoom range
        
        if new_scale != self.scale:
            # Update scale
            self.scale = new_scale
            
            # Adjust pan to keep the same SVG point under the mouse
            self.pan_x = mouse_x - svg_x * self.scale
            self.pan_y = mouse_y - svg_y * self.scale
            
            self.needs_full_render = True
            self.render_svg()
    
    def on_mouse_press(self, event):
        """Handle mouse press for assignment mode using canvas coordinate system"""
        self.last_click_pos = (event.x, event.y)
        self.is_dragging = False
        
        # Convert widget coordinates to canvas coordinates (accounts for scrolling)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # DEBUG: Odkomentuj poniższą linię żeby debugować kliknięcia
        # print(f"Click: widget({event.x}, {event.y}) -> canvas({canvas_x}, {canvas_y})")
        
        # Try to find elements in increasingly larger areas
        clicked_element = None
        
        # First try: small area around click
        items = self.canvas.find_overlapping(canvas_x - 3, canvas_y - 3, 
                                             canvas_x + 3, canvas_y + 3)
        for item in items:
            if item in self.interactive_elements:
                clicked_element = self.interactive_elements[item]
                break
        
        # Second try: larger area if nothing found
        if not clicked_element:
            items = self.canvas.find_overlapping(canvas_x - 10, canvas_y - 10, 
                                                 canvas_x + 10, canvas_y + 10)
            for item in items:
                if item in self.interactive_elements:
                    clicked_element = self.interactive_elements[item]
                    break
        
        # Third try: use find_closest as fallback
        if not clicked_element:
            closest = self.canvas.find_closest(canvas_x, canvas_y, halo=15)
            if closest and closest[0] in self.interactive_elements:
                clicked_element = self.interactive_elements[closest[0]]
        
        if clicked_element:
            self.handle_element_click(clicked_element)
        else:
            # Click on empty space - clear assignment selection
            self.clear_assignment_selection()
    
    def on_mouse_drag(self, event):
        """Handle mouse drag for panning"""
        dx = event.x - self.last_click_pos[0]
        dy = event.y - self.last_click_pos[1]
        
        # Check if this is a drag (not just a click)
        if abs(dx) > self.drag_threshold or abs(dy) > self.drag_threshold:
            self.is_dragging = True
            
            # Pan the view
            self.pan_x += dx
            self.pan_y += dy
            
            self.needs_full_render = True
            self.render_svg()
            
        self.last_click_pos = (event.x, event.y)
    
    def on_mouse_release(self, event):
        """Handle mouse release"""
        # If not dragging, this was a click
        if not self.is_dragging:
            pass  # Click handling is done in on_mouse_press
        
        self.is_dragging = False
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for hover effects using canvas coordinate system"""
        if not self.interactive_elements:
            return
        
        # Convert widget coordinates to canvas coordinates (accounts for scrolling)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # DEBUG: Odkomentuj poniższe linie żeby debugować współrzędne
        # print(f"Mouse: widget({event.x}, {event.y}) -> canvas({canvas_x}, {canvas_y})")
        
        # Try to find elements in increasingly larger areas
        found_element = None
        
        # First try: small area around cursor
        items = self.canvas.find_overlapping(canvas_x - 3, canvas_y - 3, 
                                             canvas_x + 3, canvas_y + 3)
        # print(f"  Small area: {len(items)} items, interactive: {sum(1 for i in items if i in self.interactive_elements)}")
        for item in items:
            if item in self.interactive_elements:
                found_element = self.interactive_elements[item]
                # print(f"  Found: {found_element.element_type} id={found_element.element_id}")
                break
        
        # Second try: larger area if nothing found
        if not found_element:
            items = self.canvas.find_overlapping(canvas_x - 10, canvas_y - 10, 
                                                 canvas_x + 10, canvas_y + 10)
            # print(f"  Large area: {len(items)} items, interactive: {sum(1 for i in items if i in self.interactive_elements)}")
            for item in items:
                if item in self.interactive_elements:
                    found_element = self.interactive_elements[item]
                    # print(f"  Found: {found_element.element_type} id={found_element.element_id}")
                    break
        
        # Third try: use find_closest as fallback
        if not found_element:
            closest = self.canvas.find_closest(canvas_x, canvas_y, halo=15)
            if closest and closest[0] in self.interactive_elements:
                found_element = self.interactive_elements[closest[0]]
                # print(f"  Closest: {found_element.element_type} id={found_element.element_id}")
        
        # Handle hover state
        if found_element:
            if self.hover_element != found_element:
                # Clear previous hover group
                self.clear_hover_group()
                
                # Set new hover
                self.hover_element = found_element
                
                # Check if this element has assigned group
                if found_element.assigned_group:
                    # Highlight all elements in the group
                    self.highlight_assigned_group(found_element.assigned_group)
                else:
                    # Just highlight this element - ALE TYLKO jeśli nie jest zaznaczony
                    if found_element != self.selected_text_element and found_element != self.selected_line_element:
                        self.set_element_style(found_element, 'hover')
                
                # Update cursor
                self.canvas.config(cursor="hand2")
        else:
            # Clear hover
            if self.hover_element or self.hovered_group_elements:
                self.clear_hover_group()
                self.hover_element = None
                self.canvas.config(cursor="")
    
    def highlight_assigned_group(self, group_id: str):
        """Highlight all elements in an assigned group using colors from config"""
        from src.core import config
        
        self.hovered_group_elements.clear()
        
        for canvas_id, elem in self.interactive_elements.items():
            if elem.assigned_group == group_id:
                self.hovered_group_elements.append(elem)
                
                # NIE zmieniaj koloru jeśli element jest zaznaczony
                if elem == self.selected_text_element or elem == self.selected_line_element:
                    continue  # Zostaw kolor zaznaczenia
                
                # Apply group hover style using colors from config
                if elem.element_type == 'text':
                    color = getattr(config, 'HOVER_TEXT_COLOR', '#8B008B')  # Fioletowy
                    self.canvas.itemconfig(elem.canvas_id, fill=color)
                elif elem.element_type in ['line', 'polyline']:
                    color = getattr(config, 'HOVER_SEGMENT_COLOR', '#FFB6C1')  # Różowy
                    self.canvas.itemconfig(elem.canvas_id, fill=color, width=3)
                else:
                    color = self.colors['hover']
                    self.canvas.itemconfig(elem.canvas_id, outline=color)
    
    def clear_hover_group(self):
        """Clear hover highlighting from all group elements"""
        if self.hover_element and not self.hover_element.assigned_group:
            # NIE resetuj jeśli element jest zaznaczony
            if self.hover_element != self.selected_text_element and self.hover_element != self.selected_line_element:
                self.set_element_style(self.hover_element, 'normal')
        
        for elem in self.hovered_group_elements:
            # NIE resetuj jeśli element jest zaznaczony
            if elem != self.selected_text_element and elem != self.selected_line_element:
                self.set_element_style(elem, 'normal')
        
        self.hovered_group_elements.clear()
    
    def on_key_press(self, event):
        """Handle keyboard shortcuts"""
        if event.keysym == 'f':
            self.fit_to_window()
        elif event.keysym == 'r':
            self.reset_view()
        elif event.keysym == 'Escape':
            self.clear_selection()
    
    def on_canvas_configure(self, event):
        """Handle canvas resize"""
        if hasattr(self, 'parent'):
            self.parent.after_idle(self.render_svg)
    
    # Selection and interaction
    def select_element(self, element: InteractiveElement):
        """Select an element"""
        # Clear previous selection
        self.clear_selection()
        
        # Add to selection
        element.selected = True
        self.selected_elements.append(element)
        self.set_element_style(element, 'selected')
        
        # Update UI
        self.update_selection_label()
        
        # Notify callback
        if self.on_element_select:
            self.on_element_select(element)
    
    def clear_selection(self):
        """Clear all selections"""
        for element in self.selected_elements:
            element.selected = False
            self.set_element_style(element, 'normal')
        
        self.selected_elements.clear()
        self.update_selection_label()
    
    def set_element_style(self, element: InteractiveElement, style: str):
        """Set element visual style using colors from config"""
        from src.core import config
        
        if style == 'selected':
            # Użyj kolorów SELECTED z config
            if element.element_type == 'text':
                color = getattr(config, 'SELECTED_TEXT_COLOR', '#00FFFF')
            else:  # segment/line
                color = getattr(config, 'SELECTED_SEGMENT_COLOR', '#FFFF00')
        elif style == 'hover':
            color = self.colors['hover']
        else:
            # Return to original color
            if element.element_type == 'text':
                color = element.svg_data['attributes'].get('fill', self.colors['text'])
            else:
                color = element.svg_data['attributes'].get('stroke', self.colors['line'])
        
        # Apply style based on element type
        if element.element_type in ['line', 'polyline']:
            # Segmenty - zmiana koloru linii, grubsza linia gdy zaznaczone
            self.canvas.itemconfig(element.canvas_id, fill=color, 
                                  width=4 if style == 'selected' else 3 if style == 'hover' else 2)
        elif element.element_type == 'text':
            # Teksty - zmiana koloru wypełnienia
            self.canvas.itemconfig(element.canvas_id, fill=color)
        elif element.element_type in ['rect', 'circle']:
            self.canvas.itemconfig(element.canvas_id, outline=color)
    
    # View controls
    def fit_to_window(self):
        """Fit SVG content to window with improved algorithm"""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.parent.after(100, self.fit_to_window)
            return
        
        # Use actual content bounds instead of SVG dimensions
        content_x1, content_y1, content_x2, content_y2 = self.svg_bounds
        content_width = content_x2 - content_x1
        content_height = content_y2 - content_y1
        
        if content_width <= 0 or content_height <= 0:
            # Fallback to original size if bounds are invalid
            content_width = self.original_size[0]
            content_height = self.original_size[1]
            content_x1, content_y1 = 0, 0
        
        # Calculate scale to fit content with padding
        padding_factor = 0.9  # Leave 10% padding
        scale_x = (canvas_width * padding_factor) / content_width
        scale_y = (canvas_height * padding_factor) / content_height
        
        self.scale = min(scale_x, scale_y)
        
        # Center the content in the canvas
        # Calculate center of content in SVG coordinates
        content_center_x = (content_x1 + content_x2) / 2
        content_center_y = (content_y1 + content_y2) / 2
        
        # Pan to center the content
        self.pan_x = canvas_width / 2 - content_center_x * self.scale
        self.pan_y = canvas_height / 2 - content_center_y * self.scale
        
        self.needs_full_render = True
        self.render_svg()
    
    def zoom_in(self):
        """Zoom in by fixed factor"""
        # Zoom towards canvas center
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Get SVG point at center
        svg_x, svg_y = self.inverse_transform_point(center_x, center_y)
        
        # Update scale
        new_scale = min(self.scale * 1.5, 20.0)
        if new_scale != self.scale:
            self.scale = new_scale
            # Adjust pan to keep center point fixed
            self.pan_x = center_x - svg_x * self.scale
            self.pan_y = center_y - svg_y * self.scale
            self.needs_full_render = True
            self.render_svg()
    
    def zoom_out(self):
        """Zoom out by fixed factor"""
        # Zoom towards canvas center
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Get SVG point at center
        svg_x, svg_y = self.inverse_transform_point(center_x, center_y)
        
        # Update scale
        new_scale = max(self.scale / 1.5, 0.05)
        if new_scale != self.scale:
            self.scale = new_scale
            # Adjust pan to keep center point fixed
            self.pan_x = center_x - svg_x * self.scale
            self.pan_y = center_y - svg_y * self.scale
            self.needs_full_render = True
            self.render_svg()
    
    def reset_view(self):
        """Reset view to default"""
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.clear_selection()
        self.needs_full_render = True
        self.render_svg()
    
    # UI updates
    def update_zoom_label(self):
        """Update zoom level display"""
        zoom_percent = int(self.scale * 100)
        self.zoom_label.config(text=f"{zoom_percent}%")
    
    def update_selection_label(self):
        """Update selection info display"""
        if self.selected_elements:
            elem = self.selected_elements[0]
            text = f"Selected: {elem.element_type}"
            if elem.element_type == 'text':
                content = elem.svg_data.get('content', '')[:20]
                if content:
                    text += f" - '{content}'"
        else:
            text = "No selection"
        
        self.selection_label.config(text=text)
    
    def update_scroll_region(self):
        """Update canvas scroll region"""
        # Get bounds of all canvas items
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
    
    def display_render_info(self, elements_count: int):
        """Display rendering information"""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        info_text = f"Elements: {elements_count} | Zoom: {int(self.scale * 100)}%"
        
        # Display in bottom-right corner
        self.canvas.create_text(
            canvas_width - 10, canvas_height - 10,
            text=info_text, fill="gray", font=("Arial", 9),
            anchor="se", tags="ui_info"
        )
    
    def display_message(self, message: str, msg_type: str = "info"):
        """Display message on canvas"""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        color = {
            'info': 'blue',
            'error': 'red',
            'success': 'green'
        }.get(msg_type, 'black')
        
        self.canvas.delete("all")
        self.canvas.create_text(
            canvas_width // 2, canvas_height // 2,
            text=message, fill=color, font=("Arial", 14),
            justify=tk.CENTER, tags="message"
        )
    
    # Public interface methods
    def get_selected_elements(self) -> List[InteractiveElement]:
        """Get currently selected elements"""
        return self.selected_elements.copy()
    
    def refresh(self):
        """Force refresh of the view"""
        self.needs_full_render = True
        self.render_svg()

    def force_full_render(self):
        """Force a complete re-render (for compatibility)"""
        self.refresh()

    def get_viewport_state(self) -> Dict[str, float]:
        """Get current viewport state (scale, pan_x, pan_y)"""
        return {
            'scale': self.scale,
            'pan_x': self.pan_x,
            'pan_y': self.pan_y
        }

    def set_viewport_state(self, state: Dict[str, float]):
        """Set viewport state (scale, pan_x, pan_y)"""
        if state:
            self.scale = state.get('scale', 1.0)
            self.pan_x = state.get('pan_x', 0)
            self.pan_y = state.get('pan_y', 0)
            self.needs_full_render = True
            self.render_svg()
            self.update_zoom_label()
    
    # USUNIĘTO STARĄ create_assignment_controls - teraz wszystko w create_toolbar
    
    def set_assignment_callback(self, callback):
        """Set callback function for assignment events"""
        self.on_assignment_made = callback
    
    def clear_assignment_selection(self):
        """Clear current assignment selection"""
        if self.selected_text_element:
            self.set_element_style(self.selected_text_element, 'normal')
            self.selected_text_element = None
        
        if self.selected_line_element:
            self.set_element_style(self.selected_line_element, 'normal')
            self.selected_line_element = None
        
        self.update_assignment_buttons()
        self.update_assignment_status()
    
    def update_assignment_buttons(self):
        """Update assignment button states - zaktualizowane dla Canvas przycisków"""
        can_assign = (self.selected_text_element is not None and 
                     self.selected_line_element is not None)
        can_clear_line = self.selected_line_element is not None
        
        # Kolory
        colors = {
            'button_bg': '#333333',
            'button_disabled': '#1a1a1a',
            'accent': '#4a9eff',
            'text': '#e0e0e0',
            'text_disabled': '#666666'
        }
        
        # Enable/disable assign button (Canvas)
        if hasattr(self, 'assign_btn_canvas') and self.assign_btn_canvas:
            if can_assign:
                self.assign_btn_canvas.itemconfig(self.assign_btn_canvas.circle, fill=colors['accent'])
                self.assign_btn_canvas.itemconfig(self.assign_btn_canvas.icon_id, fill='white')
            else:
                self.assign_btn_canvas.itemconfig(self.assign_btn_canvas.circle, fill=colors['button_disabled'])
                self.assign_btn_canvas.itemconfig(self.assign_btn_canvas.icon_id, fill=colors['text_disabled'])
        
        # Enable/disable clear line button (Canvas)
        if hasattr(self, 'clear_line_btn_canvas') and self.clear_line_btn_canvas:
            if can_clear_line:
                self.clear_line_btn_canvas.itemconfig(self.clear_line_btn_canvas.circle, fill=colors['button_bg'])
                self.clear_line_btn_canvas.itemconfig(self.clear_line_btn_canvas.icon_id, fill=colors['text'])
            else:
                self.clear_line_btn_canvas.itemconfig(self.clear_line_btn_canvas.circle, fill=colors['button_disabled'])
                self.clear_line_btn_canvas.itemconfig(self.clear_line_btn_canvas.icon_id, fill=colors['text_disabled'])
    
    def assign_text_to_line(self):
        """Assign selected text to selected line"""
        if not self.selected_text_element or not self.selected_line_element:
            return
        
        # Extract text and line data
        text_content = self.selected_text_element.svg_data.get('content', '').strip()
        text_id = text_content  # Use content as ID
        
        # For line, we need to get the segment number from the displayed text
        line_element = self.selected_line_element
        
        # Create assignment data
        assignment_data = {
            'text_id': text_id,
            'text_element': self.selected_text_element,
            'line_element': self.selected_line_element,
            'action': 'assign'
        }
        
        # Notify callback if available (this should update the main GUI)
        if self.on_assignment_made:
            self.on_assignment_made(assignment_data)
        
        # Clear assignment selection
        self.clear_assignment_selection()
    
    def clear_line_assignments(self):
        """Clear all assignments for selected line"""
        if not self.selected_line_element:
            return
        
        # Extract line ID from selected line element
        line_element = self.selected_line_element
        line_id = line_element.svg_data['attributes'].get('data-segment-id')
        
        if line_id:
            # Create clear assignment data
            clear_data = {
                'line_element': self.selected_line_element,
                'segment_id': int(line_id),
                'action': 'clear_line'
            }
            
            # Notify callback if available (this should update the main GUI)
            if self.on_assignment_made:
                self.on_assignment_made(clear_data)
        
        # Keep line selected but clear text selection
        if self.selected_text_element:
            self.set_element_style(self.selected_text_element, 'normal')
            self.selected_text_element = None
        
        self.update_assignment_buttons()
        self.update_assignment_status()

    def delete_selected_elements(self):
        """Delete selected elements"""
        if not self.selected_elements:
            return
        
        # Create deletion data
        deletion = {
            'elements': self.selected_elements.copy(),
            'action': 'delete'
        }
        
        # Notify callback if available
        if self.on_element_select:
            self.on_element_select(deletion)
        
        # Clear selection
        self.clear_selection()
        self.update_assignment_buttons()
    
    def on_ctrl_click(self, event):
        """Handle Ctrl+click for multi-selection"""
        clicked_item = self.canvas.find_closest(event.x, event.y)[0]
        if clicked_item in self.interactive_elements:
            element = self.interactive_elements[clicked_item]
            
            # Toggle selection
            if element in self.selected_elements:
                self.remove_from_selection(element)
            else:
                self.add_to_selection(element)
            
            self.update_assignment_ui(element)
    
    def on_shift_click(self, event):
        """Handle Shift+click for starting box selection"""
        self.selection_start_pos = (event.x, event.y)
        self.is_box_selecting = True
        self.current_selection_mode = 'multi'
    
    def on_delete_key(self, event):
        """Handle Delete/Backspace key for deleting selection"""
        if self.selected_elements:
            self.delete_selected_elements()
    
    def add_to_selection(self, element: InteractiveElement):
        """Add element to selection"""
        if element not in self.selected_elements:
            element.selected = True
            self.selected_elements.append(element)
            self.set_element_style(element, 'selected')
            self.update_selection_label()
            self.update_assignment_buttons()
    
    def remove_from_selection(self, element: InteractiveElement):
        """Remove element from selection"""
        if element in self.selected_elements:
            element.selected = False
            self.selected_elements.remove(element)
            self.set_element_style(element, 'normal')
            self.update_selection_label()
            self.update_assignment_buttons()
    
    def update_assignment_ui(self, element: InteractiveElement):
        """Update assignment UI based on selected element"""
        if not self.assignment_mode:
            return
        
        if element.element_type == 'text':
            # Clear previous text selection
            if self.selected_text_element:
                self.set_element_style(self.selected_text_element, 'normal')
            
            self.selected_text_element = element
            self.set_element_style(element, 'selected')
            
        elif element.element_type in ['line', 'polyline']:
            # Clear previous line selection
            if self.selected_line_element:
                self.set_element_style(self.selected_line_element, 'normal')
            
            self.selected_line_element = element
            self.set_element_style(element, 'selected')
        
        self.update_assignment_buttons()
        self.update_assignment_status()
    
    def update_assignment_status(self):
        """Update assignment status display"""
        status_parts = []
        
        if self.selected_text_element:
            text_content = self.selected_text_element.svg_data.get('content', '')[:30]
            status_parts.append(f"Tekst: '{text_content}'")
        else:
            status_parts.append("Tekst: Brak")
        
        if self.selected_line_element:
            status_parts.append("Linia: Wybrana")
        else:
            status_parts.append("Linia: Brak")
        
        status = " | ".join(status_parts)
        if len(status_parts) == 2 and "Brak" not in status:
            status += " | Gotowe do przypisania!"
        
        self.selection_label.config(text=status)
    
    def handle_element_click(self, element: InteractiveElement):
        """Handle clicking on an element in assignment mode"""
        if element.element_type == 'text':
            # Clear previous text selection
            if self.selected_text_element:
                self.set_element_style(self.selected_text_element, 'normal')
            
            # Select new text
            self.selected_text_element = element
            self.set_element_style(element, 'selected')
            
        elif element.element_type in ['line', 'polyline', 'rect']:  # rect for segments
            # Clear previous line selection
            if self.selected_line_element:
                self.set_element_style(self.selected_line_element, 'normal')
            
            # Select new line
            self.selected_line_element = element
            self.set_element_style(element, 'selected')
        
        self.update_assignment_buttons()
        self.update_assignment_status()
    
