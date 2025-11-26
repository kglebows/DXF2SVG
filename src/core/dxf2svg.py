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

def merge_segments_in_polylines(polylines: List[Dict], gap_tolerance: float = 1.0, max_merge_distance: float = 5.0) -> List[Dict]:
    """
    Łączy sąsiadujące poziome segmenty w każdej polilinii osobno w logiczne stringi.
    
    Args:
        polylines: Lista polilinii z segmentami
        gap_tolerance: Tolerancja przerw między segmentami (Y)
        max_merge_distance: Maksymalna odległość między punktami końcowymi do łączenia (X)
    
    Returns:
        Lista polilinii z połączonymi segmentami
    """
    merged_polylines = []
    
    for polyline in polylines:
        segments = polyline['segments']
        if not segments:
            merged_polylines.append(polyline)
            continue
            
        # WAŻNE: Łącz segmenty tylko w ramach tej samej polilinii!
        # Sortuj segmenty wg współrzędnej X (od lewej do prawej)
        sorted_segments = sorted(segments, key=lambda s: min(s['start'][0], s['end'][0]))
        
        merged_segments = []
        
        # Iteracyjnie łącz segmenty - rozpocznij od pierwszego
        i = 0
        while i < len(sorted_segments):
            current_segment = sorted_segments[i].copy()
            current_segment['merged_from'] = [current_segment['id']]
            
            # Sprawdź czy możemy połączyć z kolejnymi segmentami
            j = i + 1
            while j < len(sorted_segments):
                next_segment = sorted_segments[j]
                
                # Sprawdź czy segmenty mogą być połączone
                can_merge = False
                
                # Sprawdź czy segmenty są w podobnej wysokości (Y)
                current_y = (current_segment['start'][1] + current_segment['end'][1]) / 2
                next_y = (next_segment['start'][1] + next_segment['end'][1]) / 2
                y_diff = abs(current_y - next_y)
                
                if y_diff <= gap_tolerance:
                    # Sprawdź odległość X między końcem current a początkiem next
                    current_right = max(current_segment['start'][0], current_segment['end'][0])
                    next_left = min(next_segment['start'][0], next_segment['end'][0])
                    x_gap = next_left - current_right
                    
                    # Sprawdź też odwrotnie - może next jest przed current
                    next_right = max(next_segment['start'][0], next_segment['end'][0])
                    current_left = min(current_segment['start'][0], current_segment['end'][0])
                    x_gap_reverse = current_left - next_right
                    
                    if x_gap <= max_merge_distance and x_gap >= -max_merge_distance:
                        can_merge = True
                
                if can_merge:
                    # Połącz segmenty - rozszerz current_segment
                    new_left = min(current_segment['start'][0], current_segment['end'][0], 
                                 next_segment['start'][0], next_segment['end'][0])
                    new_right = max(current_segment['start'][0], current_segment['end'][0],
                                  next_segment['start'][0], next_segment['end'][0])
                    
                    # Aktualizuj current_segment jako nowy połączony segment
                    current_segment['start'] = (new_left, current_segment['start'][1])
                    current_segment['end'] = (new_right, current_segment['end'][1])
                    current_segment['length'] += next_segment['length'] + abs(x_gap)
                    current_segment['merged_from'].append(next_segment['id'])
                    
                    # Usuń połączony segment z listy
                    sorted_segments.pop(j)
                    # Nie zwiększaj j, bo kolejny segment przesunął się w dół
                else:
                    j += 1
            
            # Dodaj aktualny segment (może połączony) do wyników
            merged_segments.append(current_segment)
            i += 1
        
        # Stwórz nową polilinię z połączonymi segmentami
        merged_polyline = polyline.copy()
        merged_polyline['segments'] = merged_segments
        merged_polyline['segment_count'] = len(merged_segments)
        merged_polyline['total_length'] = sum(s['length'] for s in merged_segments)
        
        merged_polylines.append(merged_polyline)
        
        # Loguj informacje o łączeniu
        original_count = len(segments)
        merged_count = len(merged_segments)
        if merged_count != original_count:
            logger.debug(f"Polilinia {polyline['id']}: {original_count} → {merged_count} segmentów po łączeniu")
    
    return merged_polylines

def extract_polylines_from_dxf(doc, layer_line, y_tolerance=0.01, segment_min_width=0, 
                              polyline_processing_mode="individual_segments",
                              segment_merge_gap_tolerance=1.0,
                              max_merge_distance=5.0) -> List[Dict[str, Any]]:
    """Ekstraktuje polilinie z pliku DXF z odpowiedniej warstwy i konwertuje je na segmenty"""
    polylines = []
    polyline_id = 1
    global_segment_id = 1  # Globalny licznik ID segmentów
    
    # Statystyki diagnostyczne
    total_segments_found = 0
    rejected_not_horizontal = 0
    rejected_too_short = 0
    
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
                total_segments_found += 1
                
                y_diff = abs(start[1] - end[1])
                x_diff = abs(start[0] - end[0])
                
                # Sprawdź czy segment jest poziomy (różnica Y mniejsza niż tolerancja)
                if y_diff <= y_tolerance:
                    # Upewnij się, że segment ma minimalną szerokość
                    if x_diff >= segment_min_width:
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
                    else:
                        rejected_too_short += 1
                        logger.debug(f"Odrzucono segment za krótki: x_diff={x_diff:.4f} < {segment_min_width}")
                else:
                    rejected_not_horizontal += 1
                    if rejected_not_horizontal <= 10:  # Loguj tylko pierwsze 10
                        logger.debug(f"Odrzucono segment nie-poziomy: y_diff={y_diff:.4f} > {y_tolerance}, x_diff={x_diff:.2f}")
            
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
    
    accepted_segments = sum(len(p['segments']) for p in polylines)
    console.success("Segmentów poziomych znalezionych", accepted_segments)
    console.success("Polilinii z poziomymi segmentami", len(polylines))
    
    # Loguj statystyki diagnostyczne
    logger.info(f"STATYSTYKI EKSTRAKCJI SEGMENTÓW:")
    logger.info(f"  - Wszystkich segmentów w poliliniach: {total_segments_found}")
    logger.info(f"  - Zaakceptowanych (poziomych): {accepted_segments}")
    logger.info(f"  - Odrzuconych (nie-poziomych, y_diff > {y_tolerance}): {rejected_not_horizontal}")
    logger.info(f"  - Odrzuconych (za krótkich, x_diff < {segment_min_width}): {rejected_too_short}")
    
    if rejected_not_horizontal > 0:
        logger.warning(f"WAŻNE: {rejected_not_horizontal} segmentów odrzuconych jako nie-poziome! Może zwiększyć Y_TOLERANCE?")
    
    # Obsługa różnych trybów przetwarzania polilinii
    if polyline_processing_mode == "merge_segments":
        logger.info(f"Używam trybu łączenia segmentów z tolerancją przerw: {segment_merge_gap_tolerance}")
        polylines = merge_segments_in_polylines(polylines, segment_merge_gap_tolerance, max_merge_distance)
        
        # Zaktualizuj statystyki po łączeniu
        merged_segments = sum(len(p['segments']) for p in polylines)
        logger.info(f"Po łączeniu segmentów: {merged_segments} segmentów w {len(polylines)} poliliniach")
        console.result("Segmentów po łączeniu", merged_segments)
    else:
        logger.info("Używam trybu indywidualnych segmentów (bez łączenia)")
    
    return polylines

def find_closest_texts_to_polylines(texts: List[Dict], polylines: List[Dict], station_id: str, search_radius: float = 6.0, text_location: str = "above", use_advanced_formatting: bool = False, valid_station_ids: set = None) -> List[Dict]:
    """Znajdź najbliższe teksty do każdej polilinii - automatyczne przypisywanie z uwzględnieniem TEXT_LOCATION"""
    console.processing("Rozpoczęcie automatycznego przypisywania na podstawie odległości")
    logger.info("Rozpoczęcie algorytmu automatycznego przypisywania tekstów do polilinii")
    
    assignments = []
    used_texts = set()
    used_polylines = set()
    
    # NOWE: Użyj przekazanego zbioru station_ids lub fallback do pojedynczego
    if valid_station_ids is None:
        valid_station_ids = {station_id} if station_id else set()
    
    # Przefiltruj teksty dla docelowej stacji/stacji
    if use_advanced_formatting:
        # W zaawansowanym formatowaniu filtrujemy po zmiennej 'name' z variables
        if valid_station_ids:
            station_texts = []
            for t in texts:
                parsed = parse_text_to_dict(t['id'], station_id)
                if parsed:
                    text_station = parsed.get('variables', {}).get('name', '')
                    if text_station in valid_station_ids:
                        # WAŻNE: Aktualizuj tekst o dane parsed (włącznie z output_format)
                        t.update(parsed)
                        station_texts.append(t)
            console.info(f"Tekstów dla stacji {', '.join(valid_station_ids)} (zaawansowane formatowanie)", len(station_texts))
        else:
            # Jeśli nie podano station_ids, używamy wszystkich tekstów
            station_texts = texts
            console.info(f"Wszystkich tekstów (zaawansowane formatowanie, brak filtra)", len(station_texts))
    else:
        # W formatowaniu legacy filtrujemy po station_id
        station_texts = []
        for t in texts:
            parsed = parse_text_to_dict(t['id'], station_id)
            if parsed and parsed.get('station') in valid_station_ids:
                # Aktualizuj tekst o dane parsed
                t.update(parsed)
                station_texts.append(t)
        console.info(f"Tekstów dla stacji {', '.join(valid_station_ids)}", len(station_texts))
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
            'TEXT_LOCATION': TEXT_LOCATION,
            'TEXT_FORMATS_LIST': globals().get('TEXT_FORMATS_LIST', []),
            'USE_ADVANCED_FORMATTING': globals().get('USE_ADVANCED_FORMATTING', False)
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
                                          config_params['SEGMENT_MIN_WIDTH'],
                                          config_params.get('POLYLINE_PROCESSING_MODE', 'individual_segments'),
                                          config_params.get('SEGMENT_MERGE_GAP_TOLERANCE', 1.0),
                                          config_params.get('MAX_MERGE_DISTANCE', 5.0))
    console.result("Segmentów znaleziono", sum(len(p['segments']) for p in polylines))
    console.result("Polilinii (stringów) znaleziono", len(polylines))
    
    # Parsuj teksty dla docelowej stacji
    station_texts = []
    
    # Pobierz flagę zaawansowanego formatowania z parametrów lub użyj globalnej
    use_advanced_formatting = config_params.get('USE_ADVANCED_FORMATTING', False)
    
    # WAŻNE: Jeśli TEXT_FORMATS_LIST nie jest w config_params, pobierz z globals (z config module)
    if 'TEXT_FORMATS_LIST' not in config_params:
        config_params['TEXT_FORMATS_LIST'] = globals().get('TEXT_FORMATS_LIST', [])
    
    # NOWE: Pobierz wszystkie station_id z formatowań (multi-format support)
    valid_station_ids = set()
    if use_advanced_formatting:
        text_formats_list = config_params.get('TEXT_FORMATS_LIST', [])
        logger.debug(f"use_advanced_formatting={use_advanced_formatting}, TEXT_FORMATS_LIST length={len(text_formats_list)}")
        if text_formats_list:
            for fmt in text_formats_list:
                station_id_fmt = fmt.get('station_id', '')
                logger.debug(f"Format '{fmt.get('name')}' ma station_id='{station_id_fmt}'")
                if station_id_fmt:
                    valid_station_ids.add(station_id_fmt)
        else:
            # Backward compatibility: użyj pojedynczego STATION_ID
            logger.debug(f"TEXT_FORMATS_LIST jest pusta, używam STATION_ID={config_params['STATION_ID']}")
            valid_station_ids.add(config_params['STATION_ID'])
    else:
        # Legacy: zawsze tylko jeden STATION_ID
        logger.debug(f"use_advanced_formatting=False, używam STATION_ID={config_params['STATION_ID']}")
        valid_station_ids.add(config_params['STATION_ID'])
    
    console.info(f"Filtrowanie tekstów dla stacji: {', '.join(valid_station_ids)}")
    logger.debug(f"valid_station_ids set = {valid_station_ids}")
    
    for text in all_texts:
        parsed = parse_text_to_dict(text['id'], config_params['STATION_ID'])
        if parsed:
            # W zaawansowanym formatowaniu filtrujemy po zmiennej 'name'
            if use_advanced_formatting:
                # Sprawdź czy 'name' z variables pasuje do któregokolwiek station_id
                # WAŻNE: Jeśli parsed ma 'variables' (advanced parsing), użyj zmiennej 'name'
                # W przeciwnym razie (legacy parsing fallback), użyj pola 'station'
                if 'variables' in parsed:
                    text_station = parsed.get('variables', {}).get('name', '')
                else:
                    # Fallback na legacy parsing - użyj pola 'station'
                    text_station = parsed.get('station', '')
                
                logger.debug(f"advanced mode - text_station='{text_station}', in valid_station_ids={text_station in valid_station_ids}")
                if text_station in valid_station_ids:
                    text.update(parsed)  # Dodaj sparsowane dane do tekstu
                    station_texts.append(text)
            else:
                # W legacy formatowaniu filtrujemy po station
                if parsed.get('station') in valid_station_ids:
                    text.update(parsed)  # Dodaj sparsowane dane do tekstu
                    station_texts.append(text)
    
    console.result(f"Tekstów dla stacji {', '.join(valid_station_ids)} znaleziono", len(station_texts))
    
    # Automatyczne przypisywanie z parametrami z konfiguracji
    console.step("Faza 1: Automatyczne przypisywanie na podstawie odległości", "🤖")
    assignments = find_closest_texts_to_polylines(all_texts, polylines, 
                                                 config_params['STATION_ID'],
                                                 config_params['SEARCH_RADIUS'], 
                                                 config_params['TEXT_LOCATION'],
                                                 use_advanced_formatting,
                                                 valid_station_ids)
    
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
