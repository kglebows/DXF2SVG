"""
Główna aplikacja konwersji DXF->SVG dla stacji ZIEB
Bazowana na działającym systemie ZIEA, rozbudowana modularnie
"""

import ezdxf
import svgwrite
from collections import defaultdict
from scipy.spatial import KDTree
from typing import List, Dict, Tuple, Any
import math
import sys
import os

# Importy modułów własnych
from src.utils.console_logger import console, logger
from src.core.config import *
from src.core.geometry_utils import calculate_distance, find_texts_by_location
from src.svg.svg_generator import generate_svg, generate_interactive_svg, generate_structured_svg
from src.interactive.interactive_editor import interactive_assignment_menu

def extract_texts_from_dxf(doc, layer_text) -> List[Dict[str, Any]]:
    """Ekstraktuje teksty z pliku DXF z odpowiedniej warstwy"""
    console.processing("Ekstraktacja tekstów z DXF")
    texts = []
    mspace = doc.modelspace()
    
    # Używaj MTEXT z odpowiedniej warstwy (jak w starym kodzie)
    text_entities = list(mspace.query(f'MTEXT[layer=="{layer_text}"]'))
    console.info(f"Tekstów na warstwie {layer_text}", len(text_entities))
    logger.info(f"Znaleziono {len(text_entities)} tekstów na warstwie {layer_text}")
    
    for mtext in text_entities:
        try:
            text_content = clean_dxf_text(mtext.plain_text())
            if text_content:
                position = (mtext.dxf.insert.x, mtext.dxf.insert.y)
                texts.append({
                    'id': text_content,
                    'pos': position,
                    'raw_text': mtext.plain_text()
                })
        except AttributeError:
            continue
    
    return texts

def extract_polylines_from_dxf(doc, layer_line, y_tolerance=0.01, segment_min_width=0) -> List[Dict[str, Any]]:
    """Ekstraktuje polilinie z pliku DXF z odpowiedniej warstwy i konwertuje je na segmenty"""
    polylines = []
    polyline_id = 1
    global_segment_id = 1  # Globalny licznik ID segmentów
    
    mspace = doc.modelspace()
    
    # Pobierz polilinie z odpowiedniej warstwy
    lwpolylines = list(mspace.query(f'LWPOLYLINE[layer=="{layer_line}"]'))
    console.info(f"Polilinii na warstwie {layer_line}", len(lwpolylines))
    logger.info(f"Znaleziono {len(lwpolylines)} polilinii na warstwie {layer_line}")
    
    for lwpolyline in lwpolylines:
        try:
            # Pobierz punkty polilinii
            points = list(lwpolyline.vertices())
            if len(points) < 2:
                continue
                
            # Znajdź poziome segmenty
            polyline_segments = []
            
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]
                
                # Sprawdź czy segment jest poziomy (różnica Y mniejsza niż tolerancja)
                if abs(start[1] - end[1]) <= y_tolerance:
                    # Upewnij się, że segment ma minimalną szerokość
                    if abs(start[0] - end[0]) >= segment_min_width:
                        # Określ długość segmentu
                        length = calculate_distance(start, end)
                        
                        polyline_segments.append({
                            'id': global_segment_id,  # Użyj globalnego ID
                            'start': (start[0], start[1]),
                            'end': (end[0], end[1]),
                            'length': length,
                            'polyline_idx': polyline_id
                        })
                        global_segment_id += 1  # Zwiększ globalny licznik
            
            if polyline_segments:  # Tylko jeśli ma poziome segmenty
                # Oblicz centrum polilini
                all_x = [p[0] for p in points]
                all_y = [p[1] for p in points]
                center = (sum(all_x) / len(all_x), sum(all_y) / len(all_y))
                
                # Oblicz długość
                total_length = 0
                for seg in polyline_segments:
                    length = calculate_distance(seg['start'], seg['end'])
                    total_length += length
                
                polylines.append({
                    'id': polyline_id,
                    'segments': polyline_segments,
                    'center': center,
                    'polyline_idx': polyline_id - 1,  # Dla kompatybilności ze starym kodem
                    'segment_count': len(polyline_segments),
                    'total_length': total_length
                })
                
        except Exception as e:
            logger.error(f"Błąd przetwarzania polilinii: {e}")
            continue
            
        polyline_id += 1
    
    console.success("Segmentów poziomych znalezionych", sum(len(p['segments']) for p in polylines))
    console.success("Polilinii z poziomymi segmentami", len(polylines))
    return polylines

def find_closest_texts_to_polylines(texts: List[Dict], polylines: List[Dict], station_id: str, search_radius: float = 6.0, text_location: str = "above") -> List[Dict]:
    """Znajdź najbliższe teksty do każdej polilinii - automatyczne przypisywanie z uwzględnieniem TEXT_LOCATION"""
    console.processing("Rozpoczęcie automatycznego przypisywania na podstawie odległości")
    logger.info("Rozpoczęcie algorytmu automatycznego przypisywania tekstów do polilinii")
    
    assignments = []
    used_texts = set()
    used_polylines = set()
    
    # Przefiltruj teksty dla docelowej stacji
    station_texts = [t for t in texts if parse_text_to_dict(t['id'], station_id) and parse_text_to_dict(t['id'], station_id).get('station') == station_id]
    console.info(f"Tekstów dla stacji {station_id}", len(station_texts))
    logger.info(f"Używany parametr TEXT_LOCATION: {text_location}")
    logger.info(f"Używany parametr SEARCH_RADIUS: {search_radius}")
    
    # Oblicz macierz odległości między tekstami a segmentami polilinii (z uwzględnieniem TEXT_LOCATION)
    console.processing("Obliczanie macierzy odległości z uwzględnieniem położenia tekstów")
    distance_matrix = []
    
    total_combinations = 0
    for polyline in polylines:
        total_combinations += len(polyline['segments']) * len(station_texts)
    
    processed = 0
    
    for poly_idx, polyline in enumerate(polylines):
        for segment in polyline['segments']:
            # Użyj find_texts_by_location z parametrem TEXT_LOCATION
            nearby_texts = find_texts_by_location(segment, station_texts, search_radius, text_location)
            
            for text in nearby_texts:
                text_idx = station_texts.index(text)
                seg_center = ((segment['start'][0] + segment['end'][0]) / 2, 
                             (segment['start'][1] + segment['end'][1]) / 2)
                distance = calculate_distance(text['pos'], seg_center)
                
                distance_matrix.append({
                    'text': text,
                    'text_idx': text_idx,
                    'polyline': polyline,
                    'poly_idx': poly_idx,
                    'segment': segment,
                    'distance': distance
                })
                
            processed += len(nearby_texts)
            
            if processed % 50 == 0 or processed >= total_combinations * 0.9:
                progress = min(processed, total_combinations)
                console.processing("Obliczanie odległości", progress, total_combinations)
    
    logger.info(f"Obliczono {len(distance_matrix)} kombinacji odległości (z uwzględnieniem TEXT_LOCATION={TEXT_LOCATION})")
    
    # Grupuj według polilinii - przypisz najlepszy tekst do każdej polilinii
    console.processing("Grupowanie i wybór najlepszych przypisań")
    polyline_candidates = defaultdict(list)
    
    for entry in distance_matrix:
        polyline_candidates[entry['poly_idx']].append(entry)
    
    # Dla każdej polilinii wybierz najlepszy tekst
    for poly_idx, candidates in polyline_candidates.items():
        # Sortuj według odległości
        candidates.sort(key=lambda x: x['distance'])
        
        # Znajdź pierwszy dostępny tekst
        for candidate in candidates:
            text_idx = candidate['text_idx']
            
            if text_idx not in used_texts and poly_idx not in used_polylines:
                assignments.append({
                    'text': candidate['text'],
                    'polyline': candidate['polyline'],
                    'distance': candidate['distance']
                })
                used_texts.add(text_idx)
                used_polylines.add(poly_idx)
                
                logger.info(f"PRZYPISANO: Tekst '{candidate['text']['id']}' -> "
                           f"String z polilinii {candidate['polyline']['polyline_idx']} "
                           f"(odległość: {candidate['distance']:.2f}, położenie: {text_location})")
                break
    
    console.processing("Przypisywanie", len(assignments), min(len(station_texts), len(polylines)))
    console.success("Automatyczne przypisywanie zakończone", len(assignments))
    return assignments

def process_dxf(input_file: str, config_params: Dict = None) -> Tuple[Dict, List, List, List, List]:
    """Główna funkcja przetwarzania pliku DXF"""
    console.processing("Ładowanie pliku DXF")
    
    # Ustaw domyślne parametry jeśli nie przekazano konfiguracji
    if config_params is None:
        from src.core.config import LAYER_TEXT, LAYER_LINE, STATION_ID, Y_TOLERANCE, SEGMENT_MIN_WIDTH, SEARCH_RADIUS, TEXT_LOCATION
        config_params = {
            'LAYER_TEXT': LAYER_TEXT,
            'LAYER_LINE': LAYER_LINE,
            'STATION_ID': STATION_ID,
            'Y_TOLERANCE': Y_TOLERANCE,
            'SEGMENT_MIN_WIDTH': SEGMENT_MIN_WIDTH,
            'SEARCH_RADIUS': SEARCH_RADIUS,
            'TEXT_LOCATION': TEXT_LOCATION
        }
    
    try:
        doc = ezdxf.readfile(input_file)
        console.success("Plik DXF załadowany")
        logger.info(f"Pomyślnie załadowano plik DXF: {input_file}")
    except Exception as e:
        console.error(f"Błąd ładowania pliku DXF: {e}")
        logger.error(f"Błąd ładowania pliku DXF {input_file}: {e}")
        raise
    
    # Ekstraktuj teksty i polilinie z parametrami z konfiguracji
    console.step("Ekstraktacja tekstów", "📝")
    all_texts = extract_texts_from_dxf(doc, config_params['LAYER_TEXT'])
    console.result("Wszystkich tekstów znaleziono", len(all_texts))
    
    console.step("Ekstraktacja polilinii", "📏")
    polylines = extract_polylines_from_dxf(doc, config_params['LAYER_LINE'], 
                                          config_params['Y_TOLERANCE'], 
                                          config_params['SEGMENT_MIN_WIDTH'])
    console.result("Segmentów znaleziono", sum(len(p['segments']) for p in polylines))
    console.result("Polilinii (stringów) znaleziono", len(polylines))
    
    # Parsuj teksty dla docelowej stacji
    station_texts = []
    for text in all_texts:
        parsed = parse_text_to_dict(text['id'], config_params['STATION_ID'])
        if parsed and parsed.get('station') == config_params['STATION_ID']:
            text.update(parsed)  # Dodaj sparsowane dane do tekstu
            station_texts.append(text)
    
    console.result(f"Tekstów dla stacji {config_params['STATION_ID']} znaleziono", len(station_texts))
    
    # Automatyczne przypisywanie z parametrami z konfiguracji
    console.step("Faza 1: Automatyczne przypisywanie na podstawie odległości", "🤖")
    assignments = find_closest_texts_to_polylines(all_texts, polylines, 
                                                 config_params['STATION_ID'],
                                                 config_params['SEARCH_RADIUS'], 
                                                 config_params['TEXT_LOCATION'])
    
    # Buduj strukturę danych invertera
    inverter_data = defaultdict(lambda: defaultdict(list))
    assigned_text_ids = set()
    assigned_polyline_indices = set()
    
    for assignment in assignments:
        text = assignment['text']
        polyline = assignment['polyline']
        
        # Dodaj segmenty do odpowiedniego invertera
        parsed_text = parse_text_to_dict(text['id'], config_params['STATION_ID'])
        if parsed_text:
            inverter_id = parsed_text.get('inverter', 'UNKNOWN')
            inverter_data[inverter_id][text['id']].extend(polyline['segments'])
            assigned_text_ids.add(text['id'])
            assigned_polyline_indices.add(polyline['polyline_idx'])
    
    console.result("Przypisanych stringów", len(assignments))
    
    # Znajdź nieprzypisane elementy
    unassigned_texts = [t for t in station_texts if t['id'] not in assigned_text_ids]
    unassigned_polylines = [p for p in polylines if p['polyline_idx'] not in assigned_polyline_indices]
    
    # Konwertuj nieprzypisane polilinie na segmenty dla SVG
    unassigned_segments = []
    for polyline in unassigned_polylines:
        unassigned_segments.extend(polyline['segments'])
    
    console.result("Nieprzypisanych tekstów", len(unassigned_texts))
    console.result("Nieprzypisanych stringów", len(unassigned_polylines))
    
    return dict(inverter_data), station_texts, unassigned_texts, unassigned_segments, unassigned_polylines

def main(input_file=None, config_params=None):
    """Główna funkcja programu"""
    try:
        # Konfiguracja kolorowego logowania terminala
        console.header("DXF TO SVG CONVERTER - Stacja ZIEB")
        
        console.step("Inicjalizacja systemu", "⚙️ ")
        logger.info("="*80)
        logger.info("URUCHOMIENIE DXF TO SVG CONVERTER - ZIEB")
        logger.info("="*80)
        
        console.step("Wyświetlanie konfiguracji formatów tekstów", "📋")
        print_format_info()  # Wyświetl informacje o formatach
        
        console.step("Rozpoczęcie przetwarzania pliku DXF", "📂")
        
        # Użyj przekazanego pliku lub domyślnego
        if input_file is None:
            input_file = "input.dxf"
        
        # Przetwórz DXF z przekazanymi parametrami konfiguracji
        assigned_data, station_texts, unassigned_texts, unassigned_segments, unassigned_polylines = process_dxf(input_file, config_params)
        
        console.step("Generowanie początkowego SVG (podgląd)", "🎨")  
        
        # Generuj interaktywny SVG z numeracją
        interactive_svg_path = "output_initial.svg"
        generate_interactive_svg(
            assigned_data, 
            station_texts,
            unassigned_texts, 
            unassigned_segments,
            interactive_svg_path,
            config_params['STATION_ID']
        )
        
        # ========================================================================
        # KROK 8: INTERAKTYWNY TRYB EDYCJI (NOWA FUNKCJONALNOŚĆ!)
        # ========================================================================
        
        if unassigned_texts:
            console.step("Wykryto nieprzypisane teksty - oferowanie trybu interaktywnego", "✏️")
            console.info(f"Nieprzypisanych tekstów: {len(unassigned_texts)}")
            
            # Zapytaj użytkownika czy chce wejść w tryb interaktywny
            try:
                from src.utils.console_logger import Colors
                choice = input(f"\n{Colors.BRIGHT_CYAN}Czy chcesz uruchomić interaktywny tryb edycji? (t/N): {Colors.RESET}").strip().lower()
                
                if choice in ['t', 'tak', 'y', 'yes']:
                    console.step("Uruchamianie trybu interaktywnego", "🚀")
                    
                    # Uruchom interaktywny tryb z parametrem station_id
                    changes = interactive_assignment_menu(unassigned_texts, unassigned_segments, assigned_data, station_texts, config_params['STATION_ID'])
                    
                    # Po zmianach wygeneruj finalne SVG
                    final_svg_path = "output_final.svg"
                    console.step("Generowanie finalnego SVG po edycji", "🎨")
                    generate_interactive_svg(assigned_data, station_texts, unassigned_texts, unassigned_segments, final_svg_path, config_params['STATION_ID'])
                    
                    console.success(f"Finalne SVG zapisane: {final_svg_path}")
                    
                    # Zaktualizowane statystyki
                    updated_unassigned = []
                    assigned_text_ids = set()
                    for inv_strings in assigned_data.values():
                        assigned_text_ids.update(inv_strings.keys())
                    
                    for text in unassigned_texts:
                        if text['id'] not in assigned_text_ids:
                            updated_unassigned.append(text)
                    
                    final_assigned_count = len(station_texts) - len(updated_unassigned)
                    
                    console.header("FINALNE WYNIKI PO EDYCJI")
                    console.success("Tekstów przypisanych", final_assigned_count)
                    if updated_unassigned:
                        console.warning("Tekstów nieprzypisanych", len(updated_unassigned))
                    console.success("SVG zaktualizowany", final_svg_path)
                else:
                    console.info("Pominięto tryb interaktywny")
                    
            except KeyboardInterrupt:
                console.info("Przerwano przez użytkownika")
        else:
            console.success("Wszystkie teksty zostały automatycznie przypisane!", "🎉")
        
        # ========================================================================
        # GENEROWANIE STRUKTURALNEGO SVG (NOWA FUNKCJONALNOŚĆ!)
        # ========================================================================
        console.step("Generowanie strukturalnego SVG (format finalny)", "🏗️")
        structured_svg_path = "output_structured.svg"
        generate_structured_svg(
            assigned_data, 
            station_texts,
            unassigned_texts, 
            unassigned_segments,
            structured_svg_path,
            config_params['STATION_ID']
        )
        console.success("Strukturalny SVG utworzony", structured_svg_path)
        
        # Podsumowanie końcowe
        console.header("RAPORT KOŃCOWY")
        
        total_strings = sum(len(strings) for strings in assigned_data.values())
        total_texts = len(station_texts)
        
        console.success("Przetworzonych tekstów (stacja docelowa)", total_texts)
        console.success("Utworzonych stringów", total_strings) 
        console.success("SVG podstawowy zapisany", interactive_svg_path)
        console.success("SVG strukturalny zapisany", structured_svg_path)
        
        if unassigned_texts:
            console.warning("Nieprzypisanych tekstów", len(unassigned_texts))
            console.info("Możesz użyć interfejsu interaktywnego do ręcznego przypisywania")
        else:
            console.success("Wszystkie teksty zostały przypisane!", "🎉")
            
        logger.info("="*80)
        logger.info("ZAKOŃCZENIE PRZETWARZANIA - SUKCES")
        logger.info(f"Przetworzonych tekstów: {total_texts}")
        logger.info(f"Utworzonych stringów: {total_strings}")
        logger.info(f"Nieprzypisanych tekstów: {len(unassigned_texts)}")
        logger.info("="*80)
        
    except FileNotFoundError:
        console.error(f"Nie można znaleźć pliku: {input_file}")
    except PermissionError:
        console.error(f"Brak uprawnień do odczytu pliku: {input_file}")
    except Exception as e:
        import traceback
        console.error(f"Nieoczekiwany błąd: {str(e)}")
        traceback.print_exc()
        logger.error(f"Nieoczekiwany błąd w main(): {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
