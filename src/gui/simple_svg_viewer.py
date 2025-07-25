#!/usr/bin/env python3
"""
Uproszczona wersja SVGViewer - bez skomplikowanego renderowania PIL
Proste wyświetlanie informacji o SVG jak w wersji konsolowej
"""
import tkinter as tk
from tkinter import ttk
import os
import xml.etree.ElementTree as ET

class SimpleSVGViewer:
    """Prosty komponent do wyświetlania informacji o SVG"""
    
    def __init__(self, parent):
        self.parent = parent
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.svg_content = None
        self.original_size = (800, 600)
        
        # Uproszczony cache
        self.last_render_params = None
        self._force_full_render = False
        
        # Canvas z scrollbarami
        self.canvas_frame = ttk.Frame(parent)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas
        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        
        # Scrollbary
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Układ
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Obsługa zoomowania myszką
        self.canvas.bind("<Button-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan_image)
        self.canvas.bind("<MouseWheel>", self.zoom)
        
        # Zmienne do przesuwania
        self.last_x = 0
        self.last_y = 0
        
    def load_svg(self, svg_path):
        """Ładowanie pliku SVG"""
        try:
            if not os.path.exists(svg_path):
                self.canvas.delete("all")
                self.canvas.create_text(400, 300, text="Brak pliku SVG", 
                                      font=("Arial", 16), fill="gray")
                return
                
            # Zapisz ścieżkę do pliku
            self.current_svg_file = svg_path
                
            # Czytanie SVG
            with open(svg_path, 'r', encoding='utf-8') as f:
                self.svg_content = f.read()
            
            # Parsowanie rozmiarów SVG
            try:
                root = ET.fromstring(self.svg_content)
                width = root.get('width', '800')
                height = root.get('height', '600')
                
                # Usuń jednostki (px, pt, itp.)
                width = ''.join(filter(str.isdigit, width.split('.')[0])) or '800'
                height = ''.join(filter(str.isdigit, height.split('.')[0])) or '600'
                
                self.original_size = (int(width), int(height))
            except:
                self.original_size = (800, 600)
            
            self.render_svg()
            
        except Exception as e:
            self.canvas.delete("all")
            self.canvas.create_text(400, 300, text=f"Błąd ładowania SVG:\n{str(e)}", 
                                  font=("Arial", 12), fill="red")
    
    def render_svg(self):
        """Proste renderowanie SVG - tylko informacje tekstowe"""
        if not self.svg_content:
            return
            
        try:
            self.render_svg_simple()
        except Exception as e:
            self.canvas.delete("all")
            self.canvas.create_text(400, 300, text=f"Błąd renderowania:\n{str(e)}", 
                                  font=("Arial", 12), fill="red")
    
    def render_svg_simple(self):
        """Proste wyświetlanie SVG - bez skomplikowanego renderowania PIL"""
        try:
            # Parametry renderowania
            render_params = (self.scale, self.pan_x, self.pan_y, len(self.svg_content or ""))
            
            # Sprawdź cache
            if render_params == self.last_render_params and hasattr(self, 'svg_displayed'):
                return
            
            # Sprawdź rozmiar pliku SVG
            svg_size_kb = len(self.svg_content) / 1024
            
            # Wyczyść canvas
            self.canvas.delete("all")
            
            # Rozmiar canvas
            canvas_width = self.canvas.winfo_width() or 800
            canvas_height = self.canvas.winfo_height() or 600
            
            # OPCJA 1: Spróbuj wyświetlić rzeczywisty SVG jako HTML w tkinter
            try:
                # Prosta konwersja SVG do podstawowych elementów tkinter
                self.render_svg_as_tkinter_elements()
                return
            except Exception as e:
                print(f"Błąd renderowania SVG jako tkinter: {e}")
                # Kontynuuj z informacjami tekstowymi jako fallback
            
            # FALLBACK: Proste wyświetlanie informacji o SVG - jak w wersji konsolowej
            info_text = f"📄 SVG PODGLĄD (FALLBACK)\n\n"
            info_text += f"Plik: {os.path.basename(getattr(self, 'current_svg_file', 'unknown'))}\n"
            info_text += f"Rozmiar pliku: {svg_size_kb:.1f} KB\n"
            info_text += f"Wymiary: {self.original_size[0]}×{self.original_size[1]}px\n"
            info_text += f"Zoom: {int(self.scale*100)}%\n\n"
            
            # Policz elementy SVG (jak w wersji konsolowej)
            line_count = self.svg_content.count('<line')
            circle_count = self.svg_content.count('<circle')
            text_count = self.svg_content.count('<text')
            rect_count = self.svg_content.count('<rect')
            polyline_count = self.svg_content.count('<polyline')
            
            info_text += f"📊 Elementy SVG:\n"
            info_text += f"• Linie: {line_count}\n"
            info_text += f"• Kółka: {circle_count}\n"
            info_text += f"• Prostokąty: {rect_count}\n"
            info_text += f"• Poliline: {polyline_count}\n"
            info_text += f"• Teksty: {text_count}\n\n"
            
            info_text += f"❌ Nie udało się wyświetlić SVG\n"
            info_text += f"Fallback do informacji tekstowych\n"
            info_text += f"Użyj 'Pełny render' aby wymusić renderowanie"
            
            # Narysuj ramkę
            self.canvas.create_rectangle(10, 10, canvas_width-10, canvas_height-10, 
                                       outline='orange', fill='white', width=2)
            
            # Wyświetl informacje
            self.canvas.create_text(canvas_width//2, canvas_height//2, 
                                  text=info_text, 
                                  font=("Courier New", 10), justify=tk.CENTER,
                                  fill="orange")
            
            # Zaktualizuj scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Zapisz parametry dla cache
            self.last_render_params = render_params
            self.svg_displayed = True
            
        except Exception as e:
            # Fallback
            canvas_width = self.canvas.winfo_width() or 800
            canvas_height = self.canvas.winfo_height() or 600
            
            self.canvas.delete("all")
            self.canvas.create_rectangle(10, 10, canvas_width-10, canvas_height-10, 
                                       outline='red', fill='white')
            
            self.canvas.create_text(canvas_width//2, canvas_height//2, 
                                  text=f"❌ Błąd wyświetlania SVG\n\n{str(e)}", 
                                  font=("Arial", 12), justify=tk.CENTER, fill="red")
    
    def render_svg_as_tkinter_elements(self):
        """Renderuj SVG bezpośrednio jako elementy tkinter Canvas"""
        import xml.etree.ElementTree as ET
        
        # Parsuj SVG
        root = ET.fromstring(self.svg_content)
        
        # Rozmiar canvas
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        
        # Prosta skala do dopasowania SVG do canvas
        svg_width = self.original_size[0]
        svg_height = self.original_size[1]
        
        scale_x = (canvas_width - 20) / svg_width * self.scale
        scale_y = (canvas_height - 20) / svg_height * self.scale
        scale = min(scale_x, scale_y)
        
        # Offset dla wyśrodkowania
        offset_x = 10 + self.pan_x
        offset_y = 10 + self.pan_y
        
        def transform_x(x): return offset_x + float(x) * scale
        def transform_y(y): return offset_y + float(y) * scale
        
        # Wyczyść canvas
        self.canvas.delete("all")
        
        # Funkcja pomocnicza do szukania elementów z uwzględnieniem namespace
        def find_elements(element, tag_name):
            """Znajdź elementy z określonym tagiem, ignorując namespace"""
            elements = []
            for elem in element.iter():
                local_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if local_tag == tag_name:
                    elements.append(elem)
            return elements
        
        # Renderuj linie
        lines_rendered = 0
        for line in find_elements(root, 'line'):
            try:
                x1 = transform_x(line.get('x1', 0))
                y1 = transform_y(line.get('y1', 0))
                x2 = transform_x(line.get('x2', 0))
                y2 = transform_y(line.get('y2', 0))
                
                stroke = line.get('stroke', 'black')
                stroke_width = max(float(line.get('stroke-width', 1)) * scale, 1)
                
                self.canvas.create_line(x1, y1, x2, y2, 
                                      fill=stroke, width=stroke_width)
                lines_rendered += 1
                
                # Ogranicz liczbę elementów dla wydajności
                if lines_rendered > 1000:
                    break
                    
            except (ValueError, TypeError) as e:
                continue
        
        # Renderuj prostokąty
        rects_rendered = 0
        for rect in find_elements(root, 'rect'):
            try:
                x = transform_x(rect.get('x', 0))
                y = transform_y(rect.get('y', 0))
                width = float(rect.get('width', 0)) * scale
                height = float(rect.get('height', 0)) * scale
                
                fill = rect.get('fill', 'white')
                stroke = rect.get('stroke', 'black')
                
                self.canvas.create_rectangle(x, y, x + width, y + height,
                                           fill=fill, outline=stroke)
                rects_rendered += 1
                
                # Ogranicz liczbę elementów
                if rects_rendered > 500:
                    break
                    
            except (ValueError, TypeError) as e:
                continue
        
        # Renderuj kółka
        circles_rendered = 0  
        for circle in find_elements(root, 'circle'):
            try:
                cx = transform_x(circle.get('cx', 0))
                cy = transform_y(circle.get('cy', 0))
                r = max(float(circle.get('r', 0)) * scale, 2)
                
                fill = circle.get('fill', 'white')
                stroke = circle.get('stroke', 'black')
                
                self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                      fill=fill, outline=stroke)
                circles_rendered += 1
                
                # Ogranicz liczbę elementów
                if circles_rendered > 500:
                    break
                    
            except (ValueError, TypeError) as e:
                continue
        
        # Renderuj teksty (zwiększamy limit)
        texts_rendered = 0
        for text_elem in find_elements(root, 'text'):
            try:
                if texts_rendered > 500:  # Zwiększony limit tekstów
                    break
                    
                x = transform_x(text_elem.get('x', 0))
                y = transform_y(text_elem.get('y', 0))
                
                fill = text_elem.get('fill', 'black')
                font_size = max(int(float(text_elem.get('font-size', 12)) * scale), 6)  # Mniejszy minimalny rozmiar
                text_content = text_elem.text or ''
                
                # Nie skracaj tekstów tak bardzo - pokaż więcej
                if len(text_content) > 30:  # Zwiększony limit długości
                    text_content = text_content[:27] + "..."
                
                self.canvas.create_text(x, y, text=text_content, 
                                      fill=fill, font=("Arial", font_size))
                texts_rendered += 1
                
            except (ValueError, TypeError) as e:
                continue
        
        # Dodaj informacje o renderowaniu w rogu
        info = f"📊 Renderowane: {lines_rendered}L {rects_rendered}R {circles_rendered}C {texts_rendered}T"
        self.canvas.create_text(10, canvas_height-20, text=info, 
                              fill="blue", font=("Arial", 8), anchor="sw")
        
        # Zapisz parametry dla cache
        self.last_render_params = (self.scale, self.pan_x, self.pan_y, len(self.svg_content or ""))
        self.svg_displayed = True
    
    def zoom(self, event):
        """Obsługa zoomowania"""
        # Kierunek zoomowania
        if event.delta > 0 or event.num == 4:  # Zoom in
            factor = 1.1
        else:  # Zoom out
            factor = 0.9
        
        # Ograniczenia zoomowania
        new_scale = self.scale * factor
        if 0.1 <= new_scale <= 5.0:
            self.scale = new_scale
            self.render_svg()
    
    def start_pan(self, event):
        """Początek przesuwania"""
        self.last_x = event.x
        self.last_y = event.y
    
    def pan_image(self, event):
        """Przesuwanie obrazu"""
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        
        self.pan_x += dx
        self.pan_y += dy
        
        self.render_svg()
        
        self.last_x = event.x
        self.last_y = event.y
    
    def reset_view(self):
        """Reset widoku"""
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.last_render_params = None
        self.render_svg()
    
    def fit_to_window(self):
        """Dopasuj do okna"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Standardowe dopasowanie
        scale_multiplier = 0.9
        
        scale_x = canvas_width / self.original_size[0]
        scale_y = canvas_height / self.original_size[1]
        
        self.scale = min(scale_x, scale_y) * scale_multiplier
        
        self.pan_x = 0
        self.pan_y = 0
        
        self.last_render_params = None
        self.render_svg()
    
    def force_full_render(self):
        """Wymuś pełne renderowanie"""
        self._force_full_render = True
        self.last_render_params = None
        self.render_svg()
        self._force_full_render = False
