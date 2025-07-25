"""
Narzędzia geometryczne i matematyczne
"""
import math
from typing import List, Dict, Tuple
from src.utils.console_logger import console, logger
from src.core.config import STATION_ID

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Oblicz odległość euklidesową między dwoma punktami"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def find_texts_by_location(segment: Dict, texts: List[Dict], search_radius: float, location_mode: str = "any") -> List[Dict]:
    """
    Znajdź teksty w określonym położeniu względem segmentu
    location_mode: "above", "below", "any"
    """
    seg_start = segment['start']
    seg_end = segment['end']
    seg_center = ((seg_start[0] + seg_end[0]) / 2, (seg_start[1] + seg_end[1]) / 2)
    seg_y = seg_center[1]
    
    candidates = []
    
    for text in texts:
        text_pos = text['pos']
        distance = calculate_distance(seg_center, text_pos)
        
        # Sprawdź odległość
        if distance <= search_radius:
            text_y = text_pos[1]
            
            # Sprawdź położenie względem segmentu
            if location_mode == "above" and text_y <= seg_y:
                continue  # Tekst jest poniżej segmentu (bo Y maleje w górę)
            elif location_mode == "below" and text_y >= seg_y:
                continue  # Tekst jest powyżej segmentu
            elif location_mode == "any":
                pass  # Akceptuj wszystkie
            
            candidates.append({
                'text': text,
                'distance': distance,
                'relative_y': 'above' if text_y > seg_y else 'below'
            })
    
    # Sortuj według odległości
    candidates.sort(key=lambda x: x['distance'])
    return [c['text'] for c in candidates]

def find_nearby_assigned_strings(target_text: Dict, inverter_data: Dict, texts: List, max_distance: float = 50.0) -> List[Dict]:
    """
    Znajdź już przypisane stringi w pobliżu nieprzypisanego tekstu
    Returns: Lista stringów posortowana według odległości
    """
    nearby_strings = []
    target_pos = target_text['pos']
    
    for inv_id, strings in inverter_data.items():
        for str_id, segments in strings.items():
            if not segments:
                continue
                
            # Znajdź tekst przypisany do tego stringa
            assigned_text = None
            for text in texts:
                if text.get('station') == STATION_ID and text['id'] == str_id:
                    assigned_text = text
                    break
            
            if not assigned_text:
                continue
                
            # Oblicz środek stringa na podstawie segmentów
            all_points = []
            for seg in segments:
                all_points.extend([seg['start'], seg['end']])
            
            if all_points:
                center_x = sum(p[0] for p in all_points) / len(all_points)
                center_y = sum(p[1] for p in all_points) / len(all_points)
                center = (center_x, center_y)
                
                distance = calculate_distance(target_pos, center)
                
                if distance <= max_distance:
                    nearby_strings.append({
                        'string_id': str_id,
                        'inverter_id': inv_id,
                        'assigned_text': assigned_text,
                        'segments': segments,
                        'center': center,
                        'distance': distance,
                        'segment_count': len(segments)
                    })
    
    # Sortuj według odległości
    nearby_strings.sort(key=lambda x: x['distance'])
    return nearby_strings

def swap_text_assignment(target_text: Dict, chosen_string: Dict, inverter_data: Dict) -> Dict:
    """
    Zamień przypisanie tekstu ze stringiem
    Returns: Tekst który został odłączony od stringa
    """
    old_text = chosen_string['assigned_text']
    string_id = chosen_string['string_id']
    inverter_id = chosen_string['inverter_id']
    
    logger.info(f"ZAMIANA: Tekst '{target_text['id']}' -> String '{string_id}', "
               f"odłączany tekst: '{old_text['id']}'")
    
    # Znajdź odpowiedni inverter i string w danych
    for inv_id, strings in inverter_data.items():
        if inv_id == inverter_id:
            # Usuń stary string (z starym ID)
            if old_text['id'] in strings:
                segments = strings[old_text['id']]
                del strings[old_text['id']]
                
                # Dodaj string z nowym ID
                strings[target_text['id']] = segments
                break
    
    return old_text

def swap_string_assignments(inverter_data: Dict, text1_id: str, text2_id: str) -> bool:
    """
    Zamienia przypisania między dwoma tekstami - prostsze API do użycia w głównym pliku
    """
    logger.info(f"Próba zamiany przypisań: '{text1_id}' <-> '{text2_id}'")
    
    # Znajdź oba teksty w przypisaniach
    text1_segments = None
    text2_segments = None
    text1_inv = None
    text2_inv = None
    
    for inv_id, strings in inverter_data.items():
        if text1_id in strings:
            text1_segments = strings[text1_id]
            text1_inv = inv_id
        if text2_id in strings:
            text2_segments = strings[text2_id]
            text2_inv = inv_id
    
    # Sprawdź czy oba teksty są przypisane
    if text1_segments is None:
        logger.error(f"Tekst '{text1_id}' nie jest przypisany do żadnego stringa")
        return False
    
    if text2_segments is None:
        logger.error(f"Tekst '{text2_id}' nie jest przypisany do żadnego stringa")
        return False
    
    # Wykonaj zamianę
    try:
        # Usuń oba przypisania
        del inverter_data[text1_inv][text1_id]
        del inverter_data[text2_inv][text2_id]
        
        # Dodaj w zamienionej kolejności
        inverter_data[text1_inv][text2_id] = text1_segments
        inverter_data[text2_inv][text1_id] = text2_segments
        
        logger.info(f"Pomyślnie zamieniono przypisania: '{text1_id}' <-> '{text2_id}'")
        return True
        
    except Exception as e:
        logger.error(f"Błąd podczas zamiany przypisań: {e}")
        return False

def validate_final_assignments(inverter_data: Dict, texts: List) -> Tuple[List, List]:
    """
    Sprawdza, które teksty i stringi są finalnie osierocone
    Returns: (orphaned_texts, orphaned_strings)
    """
    # Zbierz wszystkie teksty które finalnie mają przypisane stringi
    assigned_text_ids = set()
    assigned_polyline_indices = set()
    
    for inv_id, strings in inverter_data.items():
        for str_id, segments in strings.items():
            if segments:  # Jeśli string ma segmenty
                # Znajdź tekst odpowiadający temu string ID
                for text in texts:
                    if text.get('station') == STATION_ID and text['id'] == str_id:
                        assigned_text_ids.add(text['id'])
                        # Zapisz indeksy polilinii używanych przez ten string
                        for seg in segments:
                            assigned_polyline_indices.add(seg['polyline_idx'])
                        break
    
    # Znajdź osierocone teksty (stacji docelowej, które nie mają finalnie stringów)
    orphaned_texts = []
    for text in texts:
        if text.get('station') == STATION_ID and text['id'] not in assigned_text_ids:
            orphaned_texts.append(text)
    
    logger.info(f"Walidacja finalna: {len(assigned_text_ids)} tekstów ma przypisane stringi")
    logger.info(f"Walidacja finalna: {len(orphaned_texts)} tekstów jest osieroconych")
    
    return orphaned_texts, list(assigned_polyline_indices)

def find_main_cluster(points: List[Tuple[float, float]], distance_threshold: float = 100.0) -> Tuple[float, float]:
    """Znajdź środek głównej grupy punktów (usuwa odstające) - zwraca współrzędne środka"""
    if not points:
        return (0.0, 0.0)
    
    if len(points) == 1:
        return points[0]
        
    sorted_x = sorted(p[0] for p in points)
    sorted_y = sorted(p[1] for p in points)
    median_x = sorted_x[len(sorted_x)//2]
    median_y = sorted_y[len(sorted_y)//2]
    
    cluster = []
    for point in points:
        distance = math.sqrt((point[0]-median_x)**2 + (point[1]-median_y)**2)
        if distance < distance_threshold:
            cluster.append(point)
    
    if not cluster:
        cluster = points  # Jeśli żaden punkt nie jest w klastrze, użyj wszystkich
    
    # Zwróć średnią pozycję klastra
    avg_x = sum(p[0] for p in cluster) / len(cluster)
    avg_y = sum(p[1] for p in cluster) / len(cluster)
    
    return (avg_x, avg_y)
