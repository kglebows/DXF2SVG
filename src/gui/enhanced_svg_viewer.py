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
from typing import Optional, Dict, List, Tuple, Any, Callable


class InteractiveElement:
    """Represents an interactive SVG element"""
    def __init__(self, element_id: str, element_type: str, bounds: Tuple[float, float, float, float], 
                 canvas_id: int, svg_data: Dict[str, Any]):
        self.element_id = element_id
        self.element_type = element_type  # 'text', 'line', 'rect', etc.
        self.bounds = bounds  # (x1, y1, x2, y2)
        self.canvas_id = canvas_id
        self.svg_data = svg_data
        self.selected = False


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
        self.viewport_buffer = 50  # Buffer around viewport for smoother panning
        self.max_elements_per_frame = 2000  # Limit elements per render frame
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
            'background': '#FFFFFF'
        }
        
        # Mouse interaction
        self.last_click_pos = (0, 0)
        self.is_dragging = False
        self.drag_threshold = 5  # pixels
        
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
        """Create toolbar with controls"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Zoom controls
        ttk.Button(toolbar, text="Fit to Window", command=self.fit_to_window).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Reset View", command=self.reset_view).pack(side=tk.LEFT, padx=(0, 5))
        
        # Zoom level display
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Selection info
        self.selection_label = ttk.Label(toolbar, text="No selection")
        self.selection_label.pack(side=tk.RIGHT)
        
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
        
    def load_svg(self, svg_path: str):
        """Load SVG file with improved parsing"""
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
            
            # Initial render with fit to window
            self.fit_to_window()
            
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
        """Get current viewport bounds in SVG coordinates"""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        # Convert canvas bounds to SVG coordinates
        x1 = (-self.pan_x) / self.scale
        y1 = (-self.pan_y) / self.scale
        x2 = (canvas_width - self.pan_x) / self.scale
        y2 = (canvas_height - self.pan_y) / self.scale
        
        # Add buffer for smoother panning
        buffer = self.viewport_buffer / self.scale
        return (x1 - buffer, y1 - buffer, x2 + buffer, y2 + buffer)
    
    def is_element_in_viewport(self, bounds: Tuple[float, float, float, float]) -> bool:
        """Check if element bounds intersect with viewport"""
        elem_x1, elem_y1, elem_x2, elem_y2 = bounds
        view_x1, view_y1, view_x2, view_y2 = self.get_viewport_bounds()
        
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
                            self.interactive_elements[canvas_id] = interactive_elem
                            elements_rendered += 1
                            
                except Exception as e:
                    continue
        
        # Update scroll region
        self.update_scroll_region()
        
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
        """Get element bounds in SVG coordinates"""
        try:
            if element_type == 'line':
                x1 = float(elem.get('x1', 0))
                y1 = float(elem.get('y1', 0))
                x2 = float(elem.get('x2', 0))
                y2 = float(elem.get('y2', 0))
                return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                
            elif element_type == 'rect':
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                w = float(elem.get('width', 0))
                h = float(elem.get('height', 0))
                return (x, y, x + w, y + h)
                
            elif element_type == 'circle':
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r = float(elem.get('r', 0))
                return (cx - r, cy - r, cx + r, cy + r)
                
            elif element_type == 'text':
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                # Estimate text bounds (rough approximation)
                text_width = len(elem.text or '') * 8
                text_height = 16
                return (x, y - text_height, x + text_width, y)
                
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
        # Get mouse position for zoom center
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        # Determine zoom direction
        if event.delta > 0 or event.num == 4:  # Zoom in
            factor = 1.2
        else:  # Zoom out
            factor = 0.8
        
        # Calculate new scale with limits
        new_scale = self.scale * factor
        new_scale = max(0.05, min(new_scale, 20.0))  # Wider zoom range
        
        if new_scale != self.scale:
            # Zoom towards mouse position
            old_scale = self.scale
            self.scale = new_scale
            
            # Adjust pan to zoom towards mouse position
            scale_factor = new_scale / old_scale
            self.pan_x = mouse_x - (mouse_x - self.pan_x) * scale_factor
            self.pan_y = mouse_y - (mouse_y - self.pan_y) * scale_factor
            
            self.needs_full_render = True
            self.render_svg()
    
    def on_mouse_press(self, event):
        """Handle mouse press"""
        self.last_click_pos = (event.x, event.y)
        self.is_dragging = False
        
        # Check for element selection
        clicked_item = self.canvas.find_closest(event.x, event.y)[0]
        if clicked_item in self.interactive_elements:
            self.select_element(self.interactive_elements[clicked_item])
        else:
            # Click on empty space - clear selection
            self.clear_selection()
    
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
        """Handle mouse motion for hover effects"""
        if self.is_dragging:
            return
        
        # Find element under cursor
        item = self.canvas.find_closest(event.x, event.y)[0]
        
        if item in self.interactive_elements:
            elem = self.interactive_elements[item]
            if self.hover_element != elem:
                # Clear previous hover
                if self.hover_element:
                    self.set_element_style(self.hover_element, 'normal')
                
                # Set new hover
                self.hover_element = elem
                self.set_element_style(elem, 'hover')
                
                # Update cursor
                self.canvas.config(cursor="hand2")
        else:
            # Clear hover
            if self.hover_element:
                self.set_element_style(self.hover_element, 'normal')
                self.hover_element = None
                self.canvas.config(cursor="")
    
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
        # Trigger re-render after resize
        self.root.after_idle(self.render_svg)
    
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
        """Set element visual style"""
        if style == 'selected':
            color = self.colors['selected']
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
            self.canvas.itemconfig(element.canvas_id, fill=color, width=3 if style != 'normal' else 1)
        elif element.element_type == 'text':
            self.canvas.itemconfig(element.canvas_id, fill=color)
        elif element.element_type in ['rect', 'circle']:
            self.canvas.itemconfig(element.canvas_id, outline=color)
    
    # View controls
    def fit_to_window(self):
        """Fit SVG content to window with improved algorithm"""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, self.fit_to_window)
            return
        
        # Use actual content bounds instead of SVG dimensions
        content_x1, content_y1, content_x2, content_y2 = self.svg_bounds
        content_width = content_x2 - content_x1
        content_height = content_y2 - content_y1
        
        if content_width <= 0 or content_height <= 0:
            return
        
        # Calculate scale to fit content with padding
        padding_factor = 0.95  # Leave 5% padding
        scale_x = (canvas_width * padding_factor) / content_width
        scale_y = (canvas_height * padding_factor) / content_height
        
        self.scale = min(scale_x, scale_y)
        
        # Center the content
        scaled_width = content_width * self.scale
        scaled_height = content_height * self.scale
        
        self.pan_x = (canvas_width - scaled_width) / 2 - content_x1 * self.scale
        self.pan_y = (canvas_height - scaled_height) / 2 - content_y1 * self.scale
        
        self.needs_full_render = True
        self.render_svg()
    
    def zoom_in(self):
        """Zoom in by fixed factor"""
        new_scale = min(self.scale * 1.5, 20.0)
        if new_scale != self.scale:
            self.scale = new_scale
            self.needs_full_render = True
            self.render_svg()
    
    def zoom_out(self):
        """Zoom out by fixed factor"""
        new_scale = max(self.scale / 1.5, 0.05)
        if new_scale != self.scale:
            self.scale = new_scale
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
