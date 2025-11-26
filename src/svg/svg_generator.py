"""
Generator SVG dla systemu ZIEB z poprawionymi rozmiarami tekstów
"""

import svgwrite
import math
from typing import List, Dict, Tuple
from src.utils.console_logger import console, logger
from src.core.geometry_utils import find_main_cluster
import src.core.config as config

def generate_svg(inverter_data: Dict, texts: List, unassigned_texts: List, unassigned_segments: List, output_path: str, station_id: str = None) -> None:
    """Generuje podstawowy SVG z poprawionymi rozmiarami tekstów"""
    console.processing("Generowanie SVG")
    logger.info(f"Rozpoczęcie generowania SVG: {output_path}")
    
    # Użyj station_id z parametru lub domyślnego z config
    if station_id is None:
        from src.core.config import STATION_ID
        station_id = STATION_ID
    
    if not inverter_data and not texts and not unassigned_texts and not unassigned_segments:
        console.warning("Brak danych do wygenerowania SVG")
        return

    # Zbierz wszystkie punkty dla określenia granic
    all_points = []
    
    # Punkty z przypisanych segmentów
    for inverter in inverter_data.values():
        for segments in inverter.values():
            for seg in segments:
                all_points.append(seg['start'])
                all_points.append(seg['end'])
    
    # Punkty z nieprzypisanych segmentów
    for seg in unassigned_segments:
        all_points.append(seg['start'])
        all_points.append(seg['end'])
    
    # Punkty z tekstów
    for text in texts + unassigned_texts:
        all_points.append(text['pos'])
    
    if not all_points:
        console.error("Brak punktów do wyświetlenia")
        return

    # Usuń outliers przed obliczaniem granic - filtruj odległe elementy
    console.processing("Filtrowanie odległych elementów (outliers)")
    logger.info(f"Punktów przed filtrowaniem outlierów: {len(all_points)}")
    
    # Znajdź główny klaster punktów i usuń outliers
    main_cluster_center = find_main_cluster(all_points, config.CLUSTER_DISTANCE_THRESHOLD)
    
    # Filtruj punkty - zostaw tylko te w głównym klastrze
    filtered_points = []
    outliers_count = 0
    for point in all_points:
        distance = math.sqrt((point[0] - main_cluster_center[0])**2 + (point[1] - main_cluster_center[1])**2)
        if distance <= config.CLUSTER_DISTANCE_THRESHOLD:
            filtered_points.append(point)
        else:
            outliers_count += 1
    
    if outliers_count > 0:
        logger.info(f"Usunięto {outliers_count} odległych elementów (outliers)")
        console.info(f"Usunięto outliers", f"{outliers_count} elementów")
    
    # Użyj przefiltrowanych punktów do obliczania granic
    if not filtered_points:
        logger.warning("Wszystkie punkty zostały uznane za outliers - używam oryginalnych punktów")
        filtered_points = all_points
    
    logger.info(f"Punktów po filtrowaniu outlierów: {len(filtered_points)}")

    # Znajdź granice na podstawie przefiltrowanych punktów
    min_x = min(point[0] for point in filtered_points)
    max_x = max(point[0] for point in filtered_points)
    min_y = min(point[1] for point in filtered_points)
    max_y = max(point[1] for point in filtered_points)
    
    # Margines
    margin = config.MARGIN
    width = max_x - min_x + 2 * margin
    height = max_y - min_y + 2 * margin
    
    # Skalowanie
    def scale_x(x): return x - min_x + margin
    def scale_y(y): return height - (y - min_y + margin)  # Odwrócenie osi Y
    
    # Tworzenie SVG
    dwg = svgwrite.Drawing(output_path, size=(f"{width}px", f"{height}px"))
    
    console.info("Rysowanie przypisanych elementów")
    
    # Grupuj elementy
    assigned_group = dwg.g(id='assigned_elements')
    unassigned_group = dwg.g(id='unassigned_elements')
    
    # Rysuj przypisane segmenty
    for inverter_id, strings in inverter_data.items():
        for string_name, segments in strings.items():
            for seg in segments:
                start = (scale_x(seg['start'][0]), scale_y(seg['start'][1]))
                end = (scale_x(seg['end'][0]), scale_y(seg['end'][1]))
                
                assigned_group.add(dwg.line(
                    start=start,
                    end=end,
                    stroke=config.ASSIGNED_SEGMENT_COLOR,
                    stroke_width=config.MPTT_HEIGHT
                ))
                
                # Dodaj środek segmentu jeśli włączone (CZARNA KROPKA)
                if config.SHOW_ELEMENT_POINTS:
                    mid_x = (seg['start'][0] + seg['end'][0]) / 2
                    mid_y = (seg['start'][1] + seg['end'][1]) / 2
                    
                    assigned_group.add(dwg.circle(
                        center=(scale_x(mid_x), scale_y(mid_y)),
                        r=config.DOT_RADIUS,
                        fill='#000000',  # czarny
                        opacity=0.8,
                        class_='segment-marker',
                        pointer_events='none'  # NIE klikalne
                    ))
                    
                if config.SHOW_ASSIGNED_SEGMENT_LABELS:
                    # Numer segmentu przy LEWEJ krawędzi
                    left_x = seg['start'][0]
                    left_y = seg['start'][1]
                    
                    assigned_group.add(dwg.text(
                        string_name,
                        insert=(scale_x(left_x), scale_y(left_y)+config.TEXT_SIZE/2),
                        text_anchor="start",  # Wyrównanie do lewej
                        fill=config.TEXT_SEGMENT_COLOR,
                        font_size=config.TEXT_SIZE,
                        opacity=config.TEXT_OPACITY,
                        pointer_events='none'  # NIE klikalne
                    ))
    
    # Rysuj nieprzypisane segmenty
    for i, seg in enumerate(unassigned_segments):
        start = (scale_x(seg['start'][0]), scale_y(seg['start'][1]))
        end = (scale_x(seg['end'][0]), scale_y(seg['end'][1]))
        
        unassigned_group.add(dwg.line(
            start=start,
            end=end,
            stroke=config.UNASSIGNED_SEGMENT_COLOR,
            stroke_width=config.MPTT_HEIGHT
        ))
        
        # Dodaj środek segmentu jeśli włączone (CZARNA KROPKA)
        if config.SHOW_ELEMENT_POINTS:
            mid_x = (seg['start'][0] + seg['end'][0]) / 2
            mid_y = (seg['start'][1] + seg['end'][1]) / 2
            
            unassigned_group.add(dwg.circle(
                center=(scale_x(mid_x), scale_y(mid_y)),
                r=config.DOT_RADIUS,
                fill='#000000',  # czarny
                opacity=0.8,
                class_='segment-marker',
                pointer_events='none'  # NIE klikalne
            ))
            
        if config.SHOW_UNASSIGNED_SEGMENT_LABELS:
            # Numer segmentu przy LEWEJ krawędzi
            left_x = seg['start'][0]
            left_y = seg['start'][1]
            
            unassigned_group.add(dwg.text(
                str(i+1),
                insert=(scale_x(left_x), scale_y(left_y)+config.TEXT_SIZE/2),
                text_anchor="start",  # Wyrównanie do lewej
                fill=config.TEXT_SEGMENT_COLOR,
                font_size=config.TEXT_SIZE,
                opacity=config.TEXT_OPACITY,
                pointer_events='none'  # NIE klikalne
            ))
    
    # Rysuj teksty przypisane - czarne kropki zamiast kolorowych
    if config.SHOW_ELEMENT_POINTS:
        for text in texts:
            from src.core.config import parse_text_to_dict
            parsed = parse_text_to_dict(text['id'], station_id)
            if parsed and parsed.get('station') == station_id:
                pos_x, pos_y = text['pos']
                # Czarna kropka
                assigned_group.add(dwg.circle(
                    center=(scale_x(pos_x), scale_y(pos_y)),
                    r=config.DOT_RADIUS,
                    fill='#000000',  # czarny
                    opacity=0.8,
                    class_='text-marker',
                    pointer_events='none'  # NIE klikalne
                ))
                
            if config.SHOW_TEXT_LABELS:
                assigned_group.add(dwg.text(
                    text['id'],
                    insert=(scale_x(pos_x) + size*2, scale_y(pos_y)+config.TEXT_SIZE/2),
                    fill=config.TEXT_COLOR_ASSIGNED,
                    font_size=config.TEXT_SIZE,
                    opacity=0.5,
                    pointer_events='none'  # NIE klikalne
                ))
    
    # Rysuj nieprzypisane teksty - czarne kropki zamiast kolorowych
    if config.SHOW_ELEMENT_POINTS:
        for text in unassigned_texts:
            pos_x, pos_y = text['pos']
            # Czarna kropka
            unassigned_group.add(dwg.circle(
                center=(scale_x(pos_x), scale_y(pos_y)),
                r=config.DOT_RADIUS,
                fill='#000000',  # czarny
                opacity=0.8,
                class_='text-marker',
                pointer_events='none'  # NIE klikalne
            ))
            
            if config.SHOW_TEXT_LABELS:
                unassigned_group.add(dwg.text(
                    text['id'],
                    insert=(scale_x(pos_x) + config.DOT_RADIUS*2, scale_y(pos_y)+config.TEXT_SIZE/2),
                    fill=config.TEXT_COLOR_UNASSIGNED,
                    opacity=0.5,
                    font_size=config.TEXT_SIZE,
                    pointer_events='none'  # NIE klikalne
                ))
    
    # Dodaj grupy do SVG
    dwg.add(assigned_group)
    dwg.add(unassigned_group)
    
    # Zapisz plik
    dwg.save()
    
    console.success(f"SVG zapisany: {output_path}")
    logger.info(f"SVG wygenerowany pomyślnie: {output_path}")

def simplify_text_id(text_id: str, station_id: str = None) -> str:
    """
    Uprość wyświetlanie ID tekstu do formatu <falownik>/<MPPT>/<STRING>
    """
    from src.core.config import parse_text_to_dict
    
    try:
        parsed = parse_text_to_dict(text_id, station_id)
        if parsed:
            inverter = parsed.get('inverter', 'I?')
            mppt = parsed.get('mppt', 'M?')
            string = parsed.get('string', 'S?')
            return f"{inverter}/{mppt}/{string}"
        return text_id[:10] + "..." if len(text_id) > 10 else text_id
    except:
        return text_id[:10] + "..." if len(text_id) > 10 else text_id

def generate_interactive_svg(inverter_data: Dict, texts: List, unassigned_texts: List, unassigned_segments: List, output_path: str, station_id: str = None) -> None:
    """
    Generuje SVG z numerami dla nieprzypisanych stringów - gotowy do interaktywnego edytowania
    """
    # Użyj station_id z parametru lub domyślnego z config
    if station_id is None:
        from src.core.config import STATION_ID
        station_id = STATION_ID
        
    console.processing("Generowanie interaktywnego SVG z numeracją")
    logger.info(f"Rozpoczęcie generowania interaktywnego SVG: {output_path}")
    
    # ZAWSZE generuj SVG, nawet jeśli nie ma nieprzypisanych elementów
    if not inverter_data and not texts and not unassigned_texts and not unassigned_segments:
        console.warning("Brak danych - generuję pusty SVG")
        logger.warning("Brak danych do generowania SVG - tworzę pusty plik.")
        # Utwórz pusty SVG zamiast wychodzić
        dwg = svgwrite.Drawing(output_path, size=(f"{config.SVG_WIDTH}px", f"{config.SVG_HEIGHT}px"))
        dwg.add(dwg.text("Brak danych do wyświetlenia", insert=(50, 50), fill="black", font_size="16px"))
        dwg.save()
        logger.info(f"Pusty SVG utworzony: {output_path}")
        return

    # Zbierz wszystkie punkty
    console.processing("Obliczanie wymiarów i skalowania")
    all_points = []
    
    # Punkty z przypisanych segmentów
    for inverter in inverter_data.values():
        for segments in inverter.values():
            for seg in segments:
                all_points.append(seg['start'])
                all_points.append(seg['end'])
    
    # Punkty z nieprzypisanych segmentów
    for seg in unassigned_segments:
        all_points.append(seg['start'])
        all_points.append(seg['end'])
    
    # Punkty z tekstów (tylko docelowa stacja)
    for text in texts:
        from src.core.config import parse_text_to_dict
        parsed = parse_text_to_dict(text['id'], station_id)
        if parsed and parsed.get('station') == station_id:
            all_points.append(text['pos'])
    
    # Punkty z nieprzypisanych tekstów
    for text in unassigned_texts:
        all_points.append(text['pos'])
    
    if not all_points:
        console.error("Brak punktów do skalowania")
        logger.error(f"DEBUG: all_points jest puste. inverter_data keys: {list(inverter_data.keys()) if inverter_data else 'BRAK'}")
        logger.error(f"DEBUG: texts count: {len(texts)}, unassigned_texts: {len(unassigned_texts)}, unassigned_segments: {len(unassigned_segments)}")
        # Utwórz pusty SVG zamiast wychodzić
        dwg = svgwrite.Drawing(output_path, size=(f"{config.SVG_WIDTH}px", f"{config.SVG_HEIGHT}px"))
        dwg.add(dwg.text("Brak punktów do skalowania", insert=(50, 50), fill="red", font_size="16px"))
        dwg.save()
        logger.info(f"Pusty SVG utworzony (brak punktów): {output_path}")
        return

    # Usuń outliers przed obliczaniem granic - filtruj odległe elementy
    console.processing("Filtrowanie odległych elementów (outliers)")
    logger.info(f"Punktów przed filtrowaniem outlierów: {len(all_points)}")
    
    # Znajdź główny klaster punktów i usuń outliers
    main_cluster_center = find_main_cluster(all_points, config.CLUSTER_DISTANCE_THRESHOLD)
    
    # Filtruj punkty - zostaw tylko te w głównym klastrze
    filtered_points = []
    outliers_count = 0
    for point in all_points:
        distance = math.sqrt((point[0] - main_cluster_center[0])**2 + (point[1] - main_cluster_center[1])**2)
        if distance <= config.CLUSTER_DISTANCE_THRESHOLD:
            filtered_points.append(point)
        else:
            outliers_count += 1
    
    if outliers_count > 0:
        logger.info(f"Usunięto {outliers_count} odległych elementów (outliers)")
        console.info(f"Usunięto outliers", f"{outliers_count} elementów")
    
    # Użyj przefiltrowanych punktów do obliczania granic
    if not filtered_points:
        logger.warning("Wszystkie punkty zostały uznane za outliers - używam oryginalnych punktów")
        filtered_points = all_points
    
    logger.info(f"Punktów po filtrowaniu outlierów: {len(filtered_points)}")

    # Znajdź granice na podstawie przefiltrowanych punktów
    min_x = min(point[0] for point in filtered_points)
    max_x = max(point[0] for point in filtered_points)
    min_y = min(point[1] for point in filtered_points)
    max_y = max(point[1] for point in filtered_points)
    
    # Margines
    margin = config.MARGIN
    width = max_x - min_x + 2 * margin
    height = max_y - min_y + 2 * margin
    
    # Funkcje skalowania
    def scale_x(x): return x - min_x + margin
    def scale_y(y): return height - (y - min_y + margin)  # Odwrócenie osi Y
    
    # Tworzenie SVG z większymi rozmiarami dla lepszej czytelności
    # WAŻNE: Wyłączamy walidację aby móc używać atrybutów data-*
    dwg = svgwrite.Drawing(output_path, size=(f"{width}px", f"{height}px"), profile='tiny', debug=False)
    
    console.info("Rysowanie przypisanych elementów")
    
    # Grupuj elementy
    assigned_group = dwg.g(id='assigned_elements')
    unassigned_segments_group = dwg.g(id='unassigned_segments')  
    unassigned_texts_group = dwg.g(id='unassigned_texts')
    
    # PRZYPISANE ELEMENTY - kolorowo z numeracją segmentów
    segment_global_index = 1  # Globalny licznik segmentów
    segment_id_to_svg_number = {}  # Mapa segment_id -> numer SVG
    drawn_segments = set()  # Zbiór już narysowanych segmentów
    segment_to_text = {}  # Mapa segment_id -> text_id dla grup przypisań
    
    # Najpierw zbierz wszystkie unikalne segmenty z przypisań
    all_assigned_segments = {}  # segment_id -> segment_data
    for inverter_id, strings in inverter_data.items():
        for string_name, segments in strings.items():
            for seg in segments:
                if 'id' in seg:
                    segment_id = seg['id']
                    if segment_id not in all_assigned_segments:
                        all_assigned_segments[segment_id] = seg
                    # Zapisz mapowanie segment -> text dla grup
                    segment_to_text[segment_id] = string_name
    
    # Rysuj każdy segment tylko raz
    logger.info(f"Rysowanie {len(all_assigned_segments)} przypisanych segmentów")
    for segment_id, seg in all_assigned_segments.items():
        # Zapisz mapowanie segment_id -> numer SVG
        segment_id_to_svg_number[segment_id] = segment_global_index
        
        start = (scale_x(seg['start'][0]), scale_y(seg['start'][1]))
        end = (scale_x(seg['end'][0]), scale_y(seg['end'][1]))
        
        line_element = dwg.line(
            start=start,
            end=end,
            stroke=config.ASSIGNED_SEGMENT_COLOR,
            stroke_width=config.MPTT_HEIGHT
        )
        # Dodaj atrybuty data-* bezpośrednio do elementu
        line_element.attribs['data-segment-id'] = str(segment_id)
        line_element.attribs['data-svg-number'] = str(segment_global_index)
        # Dodaj grupę przypisania (text_id) dla hover highlight
        if segment_id in segment_to_text:
            line_element.attribs['data-assignment-group'] = segment_to_text[segment_id]
        assigned_group.add(line_element)
        
        # Dodaj czarne kropki na środkach segmentów jeśli włączone
        if config.SHOW_ELEMENT_POINTS:
            mid_x = (seg['start'][0] + seg['end'][0]) / 2
            mid_y = (seg['start'][1] + seg['end'][1]) / 2
            
            circle_element = dwg.circle(
                center=(scale_x(mid_x), scale_y(mid_y)),
                r=config.DOT_RADIUS,
                fill='#000000',  # Czarne kropki
                opacity=0.8,
                class_='segment-marker',
                pointer_events='none'  # NIE klikalne
            )
            assigned_group.add(circle_element)
        
        # Numery segmentów - kontrolowane osobnym togglem
        if config.SHOW_ASSIGNED_SEGMENT_LABELS:
            # Numer segmentu przy LEWEJ krawędzi
            left_x = seg['start'][0]
            left_y = seg['start'][1]
            
            label_element = dwg.text(
                f"#{segment_global_index}",
                insert=(scale_x(left_x), scale_y(left_y)+config.TEXT_SIZE*0.25),
                text_anchor="start",
                fill=config.TEXT_SEGMENT_COLOR,
                font_size=config.TEXT_SIZE*0.5,
                opacity=0.5,
                class_='segment-label',
                pointer_events='none'  # NIE klikalne
            )
            assigned_group.add(label_element)
        
        segment_global_index += 1
    
    # PRZYPISANE TEKSTY - tylko te które mają przypisane segmenty
    console.info(f"Renderowanie przypisanych tekstów")
    assigned_texts_count = 0
    
    # Zbierz ID przypisanych tekstów
    assigned_text_ids = set()
    for inv_segments in inverter_data.values():
        assigned_text_ids.update(inv_segments.keys())
    
    # MULTI-FORMAT SUPPORT: Pobierz wszystkie station_ids z TEXT_FORMATS_LIST
    from src.core import config as config_module
    valid_station_ids = set()
    text_formats_list = getattr(config_module, 'TEXT_FORMATS_LIST', [])
    if text_formats_list:
        for fmt in text_formats_list:
            sid = fmt.get('station_id', '')
            if sid:
                valid_station_ids.add(sid)
    else:
        # Fallback - tylko pojedynczy station_id
        valid_station_ids.add(station_id)
    
    for text_data in texts:
        from src.core.config import parse_text_to_dict
        parsed = parse_text_to_dict(text_data['id'], station_id)
        if parsed:
            # Sprawdź czy text należy do któregokolwiek z formatowań
            text_station = None
            if 'variables' in parsed:
                text_station = parsed.get('variables', {}).get('name', '')
            else:
                text_station = parsed.get('station', '')
            
            if text_station in valid_station_ids:
                text_id = text_data['id']
            
            # Renderuj tylko przypisane teksty
            if text_id in assigned_text_ids:
                x, y = text_data['pos']
                
                # Czarne kropki dla tekstów (jeśli włączone)
                if config.SHOW_ELEMENT_POINTS:
                    circle_element = dwg.circle(
                        center=(scale_x(x), scale_y(y)),
                        r=config.DOT_RADIUS,
                        fill='#000000',  # Czarna kropka
                        opacity=0.8,
                        class_='text-marker',
                        pointer_events='none'  # NIE klikalne
                    )
                    # Dodaj grupę przypisania do kropki tekstu
                    circle_element.attribs['data-assignment-group'] = text_id
                    assigned_group.add(circle_element)
                
                # Znajdź przypisane segmenty dla tego tekstu i ich numery SVG
                segment_numbers = []
                
                for inv_segments in inverter_data.values():
                    if text_id in inv_segments:
                        segments = inv_segments[text_id]
                        if isinstance(segments, list):
                            # Użyj mapy segment_id -> svg_number
                            for segment in segments:
                                segment_id = segment.get('id')
                                if segment_id in segment_id_to_svg_number:
                                    svg_number = segment_id_to_svg_number[segment_id]
                                    segment_numbers.append(str(svg_number))
                        break
                
                # Format: ZIEB/F01/MPPT1/S01 (#10 #11 #12 #13 #14) - lista zamiast zakresu
                if segment_numbers:
                    # Wypisz wszystkie numery oddzielone spacjami
                    segments_info = f"({' '.join(f'#{num}' for num in segment_numbers)})"
                    
                    # INTERACTIVE SVG ZAWSZE POKAZUJE ORYGINALNY TEKST Z DXF
                    # Formatowanie (output_format) jest tylko dla finalnego SVG
                    display_text = f"{text_data['id']} {segments_info}"
                    
                    text_element = dwg.text(
                        display_text, 
                        insert=(scale_x(x) + config.DOT_RADIUS*1.5, scale_y(y)+config.TEXT_SIZE*0.3),
                        fill=config.TEXT_COLOR_ASSIGNED,
                        opacity=0.6,  # Zwiększona przejrzystość
                        font_size=config.TEXT_SIZE*0.6  # Mniejszy rozmiar
                    )
                    # Dodaj grupę przypisania do etykiety tekstu
                    text_element.attribs['data-assignment-group'] = text_id
                    assigned_group.add(text_element)
                    assigned_texts_count += 1
                # Jeśli tekst nie ma segment_numbers, zostanie pominięty tutaj
                # i wyrenderowany jako nieprzypisany (jeśli jest w unassigned_texts)
    
    console.info(f"Wyrenderowano {assigned_texts_count} przypisanych tekstów")
    logger.info(f"Narysowano {segment_global_index - 1} przypisanych segmentów")
    
    # NIEPRZYPISANE SEGMENTY z numeracją globalną - RYSUJ WSZYSTKIE, duplikaty na żółto
    unassigned_count = 0
    skipped_count = 0
    for seg in unassigned_segments:
        segment_id = seg.get('id')
        
        # Sprawdź czy segment jest duplikatem (już przypisany)
        is_duplicate = segment_id in all_assigned_segments
        
        # NIE POMIJAJ - rysuj z innym kolorem
        if is_duplicate:
            # Rysuj duplikat na ŻÓŁTO
            color = "#FFFF00"  # Żółty dla duplikatów
            skipped_count += 1
            logger.info(f"Rysowanie duplikatu segmentu #{segment_id} na żółto")
        else:
            # Normalny nieprzypisany segment  
            color = config.UNASSIGNED_SEGMENT_COLOR
            
        # Dodaj do mapy numeracji
        global_segment_number = segment_global_index + unassigned_count
        if segment_id:
            segment_id_to_svg_number[segment_id] = global_segment_number
            
        start = (scale_x(seg['start'][0]), scale_y(seg['start'][1]))
        end = (scale_x(seg['end'][0]), scale_y(seg['end'][1]))
        
        line_element = dwg.line(
            start=start,
            end=end,
            stroke=color,  # Użyj koloru zależnego od statusu
            stroke_width=config.MPTT_HEIGHT
        )
        # Dodaj atrybuty data-* bezpośrednio do elementu
        # ZAWSZE używaj prawdziwego segment_id, nie unassigned_count!
        line_element.attribs['data-segment-id'] = str(segment_id) if segment_id else ''
        line_element.attribs['data-svg-number'] = str(global_segment_number)
        unassigned_segments_group.add(line_element)
        
        # Czarne kropki na środkach segmentów (jeśli włączone)
        mid_x = (seg['start'][0] + seg['end'][0]) / 2
        mid_y = (seg['start'][1] + seg['end'][1]) / 2
        
        if config.SHOW_ELEMENT_POINTS:
            circle_element = dwg.circle(
                center=(scale_x(mid_x), scale_y(mid_y)),
                r=config.DOT_RADIUS,
                fill='#000000',  # Czarna kropka
                opacity=0.8,
                class_='segment-marker',
                pointer_events='none'  # NIE klikalne
            )
            unassigned_segments_group.add(circle_element)

        # Numery segmentów - kontrolowane osobnym togglem
        if config.SHOW_UNASSIGNED_SEGMENT_LABELS:
            label_element = dwg.text(
                f"#{global_segment_number}",
                insert=(scale_x(mid_x), scale_y(mid_y)+config.TEXT_SIZE*0.25),
                text_anchor="middle",
                fill=config.TEXT_SEGMENT_COLOR,
                opacity=0.7,
                font_size=config.TEXT_SIZE*0.6,
                class_='segment-label',
                pointer_events='none'  # NIE klikalne
            )
            unassigned_segments_group.add(label_element)
        
        unassigned_count += 1
    
    logger.info(f"Narysowano {unassigned_count} nieprzypisanych segmentów (w tym {skipped_count} duplikatów na żółto)")
    logger.info(f"SUMA: {segment_global_index - 1} przypisanych + {unassigned_count} nieprzypisanych = {segment_global_index - 1 + unassigned_count} segmentów")
    logger.info(f"WAŻNE: Duplikaty ({skipped_count}) są teraz rysowane na ŻÓŁTO zamiast pomijane!")
    
    # NIEPRZYPISANE TEKSTY - z pełnymi nazwami
    console.info(f"Renderowanie {len(unassigned_texts)} nieprzypisanych tekstów")
    unassigned_texts_count = 0
    for text_data in unassigned_texts:
        x, y = text_data['pos']
        
        # Czarne kropki dla nieprzypisanych tekstów (jeśli włączone)
        if config.SHOW_ELEMENT_POINTS:
            circle_element = dwg.circle(
                center=(scale_x(x), scale_y(y)),
                r=config.DOT_RADIUS,
                fill='#000000',  # Czarna kropka
                opacity=0.8,
                class_='text-marker',
                pointer_events='none'  # NIE klikalne
            )
            unassigned_texts_group.add(circle_element)
        
        # Format: ZIEB/F01/MPPT1/S01 (bez dodatkowego napisu - kolor już informuje)
        # INTERACTIVE SVG ZAWSZE POKAZUJE ORYGINALNY TEKST Z DXF
        display_text = text_data['id']
        
        unassigned_texts_group.add(dwg.text(
            display_text,
            insert=(scale_x(x) + config.DOT_RADIUS*1.8, scale_y(y)+config.TEXT_SIZE*0.3),
            fill=config.TEXT_COLOR_UNASSIGNED,
            font_size=config.TEXT_SIZE*0.7,  # Mniejszy rozmiar
            opacity=0.8
        ))
        unassigned_texts_count += 1
    
    console.info(f"Wyrenderowano {unassigned_texts_count} nieprzypisanych tekstów")
    
    # Dodaj wszystkie grupy
    dwg.add(assigned_group)
    dwg.add(unassigned_segments_group)
    dwg.add(unassigned_texts_group)
    
    # Zapisz plik
    dwg.save()
    
    console.success(f"Interaktywny SVG zapisany: {output_path}")
    logger.info(f"Interaktywny SVG wygenerowany: {output_path}")


def generate_structured_svg(inverter_data: Dict, texts: List, unassigned_texts: List, unassigned_segments: List, output_path: str, station_id: str = None) -> None:
    """
    Generuje strukturalny SVG - tylko grupy falowników i stringi
    Bez opisów i kropek, z optymalnym wykorzystaniem miejsca
    """
    console.processing("Generowanie strukturalnego SVG (format finalny)")
    logger.info(f"Rozpoczęcie generowania strukturalnego SVG: {output_path}")
    logger.info(f"🔧 DEBUG: Aktualna wartość config.MPTT_HEIGHT = {config.MPTT_HEIGHT}")
    
    # Użyj station_id z parametru lub domyślnego z config
    if station_id is None:
        from src.core.config import STATION_ID
        station_id = STATION_ID
    
    if not inverter_data and not texts and not unassigned_texts and not unassigned_segments:
        console.error("Brak danych do generowania strukturalnego SVG")
        logger.warning("Brak danych do generowania strukturalnego SVG.")
        return

    # Zbierz wszystkie punkty z przypisanych segmentów - TYLKO PRZYPISANE!
    all_points = []
    for inverter in inverter_data.values():
        for segments in inverter.values():
            for seg in segments:
                all_points.append(seg['start'])
                all_points.append(seg['end'])
    
    # STRUCTURED SVG - nie uwzględniamy nieprzypisanych segmentów
    
    if not all_points:
        console.error("Brak punktów do skalowania")
        return

    # Usuń outliers przed obliczaniem granic - filtruj odległe elementy
    console.processing("Filtrowanie odległych elementów (outliers)")
    logger.info(f"Punktów przed filtrowaniem outlierów: {len(all_points)}")
    
    # Znajdź główny klaster punktów i usuń outliers
    main_cluster_center = find_main_cluster(all_points, config.CLUSTER_DISTANCE_THRESHOLD)
    
    # Filtruj punkty - zostaw tylko te w głównym klastrze
    filtered_points = []
    outliers_count = 0
    for point in all_points:
        distance = math.sqrt((point[0] - main_cluster_center[0])**2 + (point[1] - main_cluster_center[1])**2)
        if distance <= config.CLUSTER_DISTANCE_THRESHOLD:
            filtered_points.append(point)
        else:
            outliers_count += 1
    
    if outliers_count > 0:
        logger.info(f"Usunięto {outliers_count} odległych elementów (outliers)")
        console.info(f"Usunięto outliers", f"{outliers_count} elementów")
    
    # Użyj przefiltrowanych punktów do obliczania granic
    if not filtered_points:
        logger.warning("Wszystkie punkty zostały uznane za outliers - używam oryginalnych punktów")
        filtered_points = all_points
    
    logger.info(f"Punktów po filtrowaniu outlierów: {len(filtered_points)}")

    # Znajdź granice danych na podstawie przefiltrowanych punktów
    all_x = [p[0] for p in filtered_points]
    all_y = [p[1] for p in filtered_points]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    # Dodaj margines
    margin = config.MARGIN
    min_x -= margin
    max_x += margin
    min_y -= margin
    max_y += margin
    
    # Oblicz wymiary danych
    data_width = max_x - min_x
    data_height = max_y - min_y
    
    # Skaluj do zadanej rozdzielczości zachowując proporcje
    scale_factor_x = config.SVG_WIDTH / data_width
    scale_factor_y = config.SVG_HEIGHT / data_height
    
    # Użyj mniejszego współczynnika aby zachować proporcje
    scale_factor = min(scale_factor_x, scale_factor_y)
    
    # Oblicz rzeczywiste wymiary SVG z zachowaniem proporcji
    scaled_width = data_width * scale_factor
    scaled_height = data_height * scale_factor
    
    # Dodaj dodatkowy margines do viewBox aby upewnić się że wszystko jest widoczne
    # (elementy jak stroke, rectangle height mogą wykraczać poza obliczone granice)
    viewbox_padding = 20  # pixels
    viewbox_width = scaled_width + viewbox_padding * 2
    viewbox_height = scaled_height + viewbox_padding * 2
    
    # Funkcje skalowania do zadanej rozdzielczości
    # Uwzględnij padding w transformacji - wszystkie koordynaty będą >= viewbox_padding
    def scale_x(x): return (x - min_x) * scale_factor + viewbox_padding
    def scale_y(y): return viewbox_height - viewbox_padding - ((y - min_y) * scale_factor)  # Odwrócenie osi Y z paddingiem

    console.processing("Tworzenie strukturalnego dokumentu SVG")
    
    # KROK 1: Oblicz rzeczywiste granice WSZYSTKICH elementów które będą wyrenderowane
    # Iteruj przez wszystkie segmenty aby znaleźć min/max współrzędnych w przestrzeni SVG
    console.processing("Obliczanie rzeczywistych granic wyrenderowanych elementów")
    rendered_min_x = float('inf')
    rendered_max_x = float('-inf')
    rendered_min_y = float('inf')
    rendered_max_y = float('-inf')
    
    for inv_id, strings in inverter_data.items():
        for str_id, segments in strings.items():
            for seg in segments:
                x1, y1 = seg['start']
                x2, y2 = seg['end']
                y_val = min(y1, y2)
                
                # Oblicz pozycje w SVG
                segment_width = abs(x2 - x1)
                if segment_width > 2:
                    gap = segment_width * 0.01
                    actual_width = segment_width - gap
                    x_start = min(x1, x2) + gap/2
                else:
                    actual_width = segment_width
                    x_start = min(x1, x2)
                
                segment_height = config.MPTT_HEIGHT * scale_factor
                
                # Przekształć współrzędne do przestrzeni SVG
                svg_x = scale_x(x_start)
                svg_y = scale_y(y_val) - segment_height/2
                svg_width = actual_width * scale_factor
                svg_height = segment_height
                
                # Aktualizuj granice
                rendered_min_x = min(rendered_min_x, svg_x)
                rendered_max_x = max(rendered_max_x, svg_x + svg_width)
                rendered_min_y = min(rendered_min_y, svg_y)
                rendered_max_y = max(rendered_max_y, svg_y + svg_height)
    
    # Dodaj padding do rzeczywistych granic
    final_padding = 20
    final_min_x = rendered_min_x - final_padding
    final_min_y = rendered_min_y - final_padding
    final_width = (rendered_max_x - rendered_min_x) + 2 * final_padding
    final_height = (rendered_max_y - rendered_min_y) + 2 * final_padding
    
    logger.info(f"Rzeczywiste granice elementów: X[{rendered_min_x:.1f}, {rendered_max_x:.1f}], Y[{rendered_min_y:.1f}, {rendered_max_y:.1f}]")
    logger.info(f"ViewBox z paddingiem: {final_min_x:.1f} {final_min_y:.1f} {final_width:.1f} {final_height:.1f}")
    
    # KROK 2: Utwórz SVG z viewBox dopasowanym do rzeczywistych granic
    # Twórz SVG w zadanej rozdzielczości z viewBox dla dobrego skalowania
    dwg = svgwrite.Drawing(
        output_path, 
        size=(f"{config.SVG_WIDTH}px", f"{config.SVG_HEIGHT}px"),
        viewBox=f"{final_min_x} {final_min_y} {final_width} {final_height}",
        profile='tiny',  # Redukuj walidację, aby umożliwić custom data-* attributes dla tooltipów
        debug=False
    )
    logger.info(f"Generowanie strukturalnego SVG: {config.SVG_WIDTH}x{config.SVG_HEIGHT}px, viewBox: {final_min_x:.1f} {final_min_y:.1f} {final_width:.1f}x{final_height:.1f}, skala: {scale_factor:.2f}")
    
    # Najpierw przeanalizuj wszystkie stringi i pogrupuj według strukturalnych ID falowników
    console.processing("Analiza strukturalnych ID i grupowanie według falowników")
    structural_groups = {}  # inv_id -> [(str_id, segments, structural_id), ...]
    
    # Zbiór do śledzenia unikalnych segmentów (deduplikacja)
    seen_segments = set()
    duplicates_found = 0
    
    for inv_id, strings in inverter_data.items():
        for str_id, segments in strings.items():
            # Parsuj tekst żeby uzyskać strukturalne ID
            parsed_text = config.parse_text_to_dict(str_id, station_id)
            if parsed_text:
                # Jeśli używamy zaawansowanego formatowania, przekaż oryginalny tekst
                if config.USE_ADVANCED_FORMATTING:
                    # Dodaj oryginalny tekst do parsed_text
                    parsed_text['original_text'] = str_id
                
                structural_id = config.get_svg_id(parsed_text)
                # Wyciągnij ID falownika ze strukturalnego ID (część po "/")
                if "/" in structural_id:
                    structural_inv_id = structural_id.split("/")[1]
                else:
                    structural_inv_id = inv_id  # fallback do oryginalnego
                logger.debug(f"String {str_id} -> strukturalne ID: {structural_id} -> falownik: {structural_inv_id}")
            else:
                structural_id = str_id
                structural_inv_id = inv_id  # fallback do oryginalnego
                logger.warning(f"Nie można sparsować tekstu {str_id}, używam oryginalnego ID")
            
            # Filtruj duplikaty segmentów
            unique_segments = []
            for seg in segments:
                # Utwórz unikalny klucz dla segmentu (pozycja start i end)
                seg_key = (round(seg['start'][0], 3), round(seg['start'][1], 3), 
                          round(seg['end'][0], 3), round(seg['end'][1], 3))
                
                if seg_key not in seen_segments:
                    seen_segments.add(seg_key)
                    unique_segments.append(seg)
                else:
                    duplicates_found += 1
                    logger.debug(f"Znaleziono duplikat segmentu: {seg_key} w stringu {str_id}")
            
            if unique_segments:  # Tylko dodaj jeśli są unikalne segmenty
                # Dodaj do odpowiedniej grupy strukturalnej z prefiksem I (Inverter)
                group_id = f"I{structural_inv_id}"
                if group_id not in structural_groups:
                    structural_groups[group_id] = []
                structural_groups[group_id].append((str_id, unique_segments, structural_id))
    
    if duplicates_found > 0:
        logger.warning(f"Usunięto {duplicates_found} duplikatów segmentów")
        console.warning(f"Usunięto {duplicates_found} duplikatów segmentów")
    
    logger.info(f"Znaleziono {len(structural_groups)} strukturalnych grup falowników: {list(structural_groups.keys())}")
    
    # Rysuj grupy zgodnie ze strukturalnymi ID
    console.processing("Rysowanie strukturalnych grup falowników")
    strings_drawn = 0
    
    for group_id, string_data_list in structural_groups.items():
        inv_group = dwg.g(id=group_id)
        logger.info(f"Przetwarzanie strukturalnej grupy: {group_id} z {len(string_data_list)} stringami")
        
        for str_id, segments, structural_id in string_data_list:
            # Rysuj każdy segment stringa z optymalną szerokością
            for seg in segments:
                x1, y1 = seg['start']
                x2, y2 = seg['end']
                y_val = min(y1, y2)
                
                # Oblicz szerokość segmentu z małą przerwą (1% szerokości)
                segment_width = abs(x2 - x1)
                if segment_width > 2:  # Tylko jeśli segment ma rozsądną szerokość
                    gap = segment_width * 0.01  # 1% na przerwy
                    actual_width = segment_width - gap
                    x_start = min(x1, x2) + gap/2  # Wyśrodkuj przerwę
                else:
                    actual_width = segment_width
                    x_start = min(x1, x2)
                
                # Utworz prostokąt reprezentujący segment - wysokość używa MPTT_HEIGHT
                # ID pozostaje czyste bez dodawania _seg0 itp.
                segment_height = config.MPTT_HEIGHT * scale_factor  # Użyj konfigurowalnej wysokości
                
                # Pobierz segment_id przed utworzeniem prostokąta
                segment_id = seg.get('id')
                
                rect = dwg.rect(
                    insert=(scale_x(x_start), scale_y(y_val) - segment_height/2),
                    size=(actual_width * scale_factor, segment_height),
                    fill=config.ASSIGNED_SEGMENT_COLOR,
                    stroke="black",
                    stroke_width=0.1 * scale_factor,
                    id=structural_id
                )
                
                # Dodaj custom atrybuty BEZPOŚREDNIO do attribs (omija walidację)
                rect.attribs['data-string-id'] = str_id
                rect.attribs['data-structural-id'] = structural_id
                if segment_id:
                    rect.attribs['data-segment-id'] = str(segment_id)
                
                inv_group.add(rect)
            strings_drawn += 1
        dwg.add(inv_group)
    
    console.success("Strukturalnych stringów narysowanych", strings_drawn)

    # STRUCTURED SVG - nie rysujemy nieprzypisanych segmentów!
    # Finalny SVG zawiera tylko w pełni skonfigurowane struktury

    console.processing("Zapisywanie strukturalnego pliku SVG")
    dwg.save()
    console.success("Strukturalny plik SVG zapisany pomyślnie", output_path)
    logger.info(f"Zapisano strukturalny SVG: {output_path} ({scaled_width:.1f}x{scaled_height:.1f}px w {config.SVG_WIDTH}x{config.SVG_HEIGHT}px)")
