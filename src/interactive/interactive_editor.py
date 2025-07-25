"""
Moduł interaktywnego trybu edycji dla systemu ZIEB
Pozwala na ręczne przypisywanie tekstów do stringów
"""

from typing import List, Dict, Tuple
from src.utils.console_logger import console, logger, Colors
from src.core.config import *
from src.core.geometry_utils import calculate_distance
from src.svg.svg_generator import generate_interactive_svg
import time

# Globalna zmienna dla aktualnego STATION_ID (ustawiana w interactive_assignment_menu)
CURRENT_STATION_ID = None

def get_current_station_id():
    """Zwraca aktualny station_id lub domyślny z config"""
    global CURRENT_STATION_ID
    if CURRENT_STATION_ID is not None:
        return CURRENT_STATION_ID
    else:
        from src.core.config import STATION_ID
        return STATION_ID

def find_nearby_assigned_strings(target_text: Dict, inverter_data: Dict, texts: List, max_distance: float = 100.0) -> List[Dict]:
    """
    Znajdź już przypisane stringi w pobliżu nieprzypisanego tekstu
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

def assign_text_to_new_string(target_text: Dict, unassigned_segments: List, inverter_data: Dict, segment_idx: int) -> bool:
    """
    Przypisz tekst do nieprzypisanego segmentu
    """
    if segment_idx < 0 or segment_idx >= len(unassigned_segments):
        return False
        
    segment = unassigned_segments[segment_idx]
    
    # Znajdź odpowiedni inverter (używamy pierwszego dostępnego)
    inverter_id = list(inverter_data.keys())[0] if inverter_data else "I01"
    
    if inverter_id not in inverter_data:
        inverter_data[inverter_id] = {}
    
    # Dodaj nowy string
    inverter_data[inverter_id][target_text['id']] = [segment]
    
    # Usuń segment z nieprzypisanych
    unassigned_segments.remove(segment)
    
    logger.info(f"Przypisano tekst '{target_text['id']}' do nowego stringa (segment {segment_idx+1})")
    return True

def create_custom_string(target_text: Dict, custom_id: str, inverter_data: Dict) -> bool:
    """
    Stwórz nowy string z custom ID
    """
    # Znajdź odpowiedni inverter (używamy pierwszego dostępnego)
    inverter_id = list(inverter_data.keys())[0] if inverter_data else "I01"
    
    if inverter_id not in inverter_data:
        inverter_data[inverter_id] = {}
    
    # Stwórz pusty string (bez segmentów geometrycznych)
    inverter_data[inverter_id][custom_id] = []
    
    logger.info(f"Stworzono nowy string '{custom_id}' dla tekstu '{target_text['id']}'")
    return True

def get_all_segments_with_numbers(inverter_data: Dict, unassigned_segments: List) -> List[Dict]:
    """
    Pobierz wszystkie segmenty z ich globalnymi numerami
    """
    segments_list = []
    segment_number = 1
    
    # Przypisane segmenty
    for inverter_id, strings in inverter_data.items():
        for string_name, segments in strings.items():
            for seg_idx, segment in enumerate(segments):
                segments_list.append({
                    'number': segment_number,
                    'type': 'assigned',
                    'segment': segment,
                    'string_id': string_name,
                    'inverter_id': inverter_id,
                    'seg_idx_in_string': seg_idx
                })
                segment_number += 1
    
    # Nieprzypisane segmenty
    for seg_idx, segment in enumerate(unassigned_segments):
        segments_list.append({
            'number': segment_number,
            'type': 'unassigned',
            'segment': segment,
            'unassigned_idx': seg_idx
        })
        segment_number += 1
    
    return segments_list

def get_orphaned_strings(inverter_data: Dict, texts: List, station_id: str = None) -> List[Dict]:
    """
    Znajdź stringi, które nie mają przypisanego tekstu
    """
    # Użyj station_id z parametru lub domyślnego z config
    if station_id is None:
        from src.core.config import STATION_ID
        station_id = STATION_ID
        
    orphaned_strings = []
    
    for inverter_id, strings in inverter_data.items():
        for string_id, segments in strings.items():
            # Sprawdź czy jest tekst o takim ID
            text_exists = any(text.get('station') == station_id and text['id'] == string_id for text in texts)
            
            if not text_exists:
                orphaned_strings.append({
                    'string_id': string_id,
                    'inverter_id': inverter_id,
                    'segments': segments,
                    'segment_count': len(segments)
                })
    
    return orphaned_strings

def handle_segment_editing(inverter_data: Dict, unassigned_segments: List, texts: List) -> Dict:
    """
    Obsługuje edycję przypisań segmentów
    """
    console.header("EDYCJA PRZYPISAŃ SEGMENTÓW")
    
    # Pobierz wszystkie segmenty z numerami
    all_segments = get_all_segments_with_numbers(inverter_data, unassigned_segments)
    
    if not all_segments:
        console.error("Brak segmentów do edycji")
        return None
    
    console.info(f"Dostępnych segmentów: {len(all_segments)}")
    
    # Pokaż listę segmentów
    for seg_info in all_segments:
        status = "PRZYPISANY" if seg_info['type'] == 'assigned' else "NIEPRZYPISANY"
        if seg_info['type'] == 'assigned':
            print(f"  {Colors.BRIGHT_CYAN}#{seg_info['number']:2d}. {status:12s} -> {seg_info['string_id']:25s}{Colors.RESET}")
        else:
            print(f"  {Colors.BRIGHT_YELLOW}#{seg_info['number']:2d}. {status:12s}{Colors.RESET}")
    
    try:
        segment_choice = int(input(f"\n{Colors.BRIGHT_WHITE}Wybierz numer segmentu do edycji: {Colors.RESET}")) 
        
        # Znajdź segment
        selected_segment = None
        for seg_info in all_segments:
            if seg_info['number'] == segment_choice:
                selected_segment = seg_info
                break
        
        if not selected_segment:
            console.error("Nieprawidłowy numer segmentu")
            return None
        
        console.info(f"EDYCJA SEGMENTU #{selected_segment['number']}")
        
        # Przygotuj listę wszystkich tekstów (przypisanych i nieprzypisanych)
        all_texts = []
        
        # Przypisane teksty
        for text in texts:
            if text.get('station') == STATION_ID:
                all_texts.append({
                    'text': text,
                    'type': 'assigned',
                    'display': f"{text['id']} (PRZYPISANY)"
                })
        
        # Nieprzypisane teksty (jeśli są)
        unassigned_texts_list = [t for t in texts if t.get('station') == STATION_ID and not any(
            string_id == t['id'] for inv_strings in inverter_data.values() for string_id in inv_strings.keys()
        )]
        
        for text in unassigned_texts_list:
            all_texts.append({
                'text': text,
                'type': 'unassigned',
                'display': f"{text['id']} (NIEPRZYPISANY)"
            })
        
        # Sortuj alfabetycznie
        all_texts.sort(key=lambda x: x['text']['id'])
        
        console.info("Dostępne teksty:")
        for i, text_info in enumerate(all_texts):
            color = Colors.BRIGHT_GREEN if text_info['type'] == 'assigned' else Colors.BRIGHT_YELLOW
            print(f"  {color}{i+1:2d}. {text_info['display']}{Colors.RESET}")
        
        print(f"  {Colors.BRIGHT_RED}{len(all_texts)+1:2d}. USUŃ SEGMENT{Colors.RESET}")
        print(f"  {Colors.BRIGHT_RED}{len(all_texts)+2:2d}. ANULUJ{Colors.RESET}")
        
        text_choice = int(input(f"\n{Colors.BRIGHT_WHITE}Wybierz tekst do przypisania: {Colors.RESET}")) - 1
        
        if text_choice == len(all_texts):
            # Usuń segment
            return remove_segment(selected_segment, inverter_data, unassigned_segments)
        elif text_choice == len(all_texts) + 1:
            # Anuluj
            console.info("Anulowano edycję segmentu")
            return None
        elif 0 <= text_choice < len(all_texts):
            # Przypisz do wybranego tekstu
            selected_text = all_texts[text_choice]
            return assign_segment_to_text(selected_segment, selected_text, inverter_data, unassigned_segments, texts)
        else:
            console.error("Nieprawidłowy wybór")
            return None
            
    except (ValueError, KeyboardInterrupt):
        console.error("Przerwano lub nieprawidłowy wybór")
        return None

def remove_segment(segment_info: Dict, inverter_data: Dict, unassigned_segments: List) -> Dict:
    """
    Usuń segment z systemu
    """
    confirm = input(f"\n{Colors.BRIGHT_RED}Czy na pewno usunąć segment #{segment_info['number']}? (t/N): {Colors.RESET}").strip().lower()
    
    if confirm not in ['t', 'tak', 'y', 'yes']:
        console.info("Anulowano usuwanie segmentu")
        return None
    
    if segment_info['type'] == 'assigned':
        # Usuń z przypisanego stringa
        inverter_id = segment_info['inverter_id']
        string_id = segment_info['string_id']
        seg_idx = segment_info['seg_idx_in_string']
        
        if inverter_id in inverter_data and string_id in inverter_data[inverter_id]:
            segments = inverter_data[inverter_id][string_id]
            if seg_idx < len(segments):
                removed_segment = segments.pop(seg_idx)
                
                # Jeśli string nie ma już segmentów, usuń go
                if not segments:
                    del inverter_data[inverter_id][string_id]
                    logger.info(f"Usunięto pusty string '{string_id}' po usunięciu ostatniego segmentu")
                
                logger.info(f"Usunięto segment #{segment_info['number']} ze stringa '{string_id}'")
                console.success(f"Usunięto segment #{segment_info['number']}")
                
                return {
                    'action': 'segment_removed',
                    'segment_number': segment_info['number'],
                    'from_string': string_id
                }
    else:
        # Usuń z nieprzypisanych segmentów
        seg_idx = segment_info['unassigned_idx']
        if seg_idx < len(unassigned_segments):
            removed_segment = unassigned_segments.pop(seg_idx)
            logger.info(f"Usunięto nieprzypisany segment #{segment_info['number']}")
            console.success(f"Usunięto segment #{segment_info['number']}")
            
            return {
                'action': 'unassigned_segment_removed',
                'segment_number': segment_info['number']
            }
    
    console.error("Nie można usunąć segmentu")
    return None

def assign_segment_to_text(segment_info: Dict, text_info: Dict, inverter_data: Dict, unassigned_segments: List, texts: List) -> Dict:
    """
    Przypisz segment do wybranego tekstu
    """
    target_text = text_info['text']
    target_text_id = target_text['id']
    
    console.info(f"Przypisywanie segmentu #{segment_info['number']} do tekstu '{target_text_id}'")
    
    # Znajdź lub stwórz string dla tego tekstu
    target_inverter = list(inverter_data.keys())[0] if inverter_data else "I01"
    if target_inverter not in inverter_data:
        inverter_data[target_inverter] = {}
    
    # Pobierz segment
    segment = segment_info['segment']
    
    # Usuń segment z obecnego miejsca
    if segment_info['type'] == 'assigned':
        # Usuń z obecnego stringa
        old_inverter = segment_info['inverter_id']
        old_string = segment_info['string_id']
        seg_idx = segment_info['seg_idx_in_string']
        
        if old_inverter in inverter_data and old_string in inverter_data[old_inverter]:
            segments = inverter_data[old_inverter][old_string]
            if seg_idx < len(segments):
                segments.pop(seg_idx)
                
                # Jeśli string został pusty, usuń go
                if not segments:
                    del inverter_data[old_inverter][old_string]
                    logger.info(f"Usunięto pusty string '{old_string}' po przeniesieniu ostatniego segmentu")
    else:
        # Usuń z nieprzypisanych
        seg_idx = segment_info['unassigned_idx']
        if seg_idx < len(unassigned_segments):
            unassigned_segments.pop(seg_idx)
    
    # Dodaj segment do docelowego stringa
    if target_text_id not in inverter_data[target_inverter]:
        inverter_data[target_inverter][target_text_id] = []
    
    inverter_data[target_inverter][target_text_id].append(segment)
    
    logger.info(f"Przypisano segment #{segment_info['number']} do tekstu '{target_text_id}'")
    console.success(f"Przypisano segment #{segment_info['number']} do '{target_text_id}'")
    
    return {
        'action': 'segment_reassigned',
        'segment_number': segment_info['number'],
        'to_text': target_text_id,
        'from_location': segment_info.get('string_id', 'NIEPRZYPISANY')
    }

def handle_orphaned_strings(inverter_data: Dict, texts: List) -> Dict:
    """
    Obsługuje zarządzanie osieroconymi stringami
    """
    console.header("ZARZĄDZANIE OSIEROCONYMI STRINGAMI")
    
    orphaned = get_orphaned_strings(inverter_data, texts)
    
    if not orphaned:
        console.success("Brak osieroconych stringów!")
        return None
    
    console.info(f"Znaleziono {len(orphaned)} osieroconych stringów:")
    
    for i, string_info in enumerate(orphaned):
        print(f"  {Colors.BRIGHT_YELLOW}{i+1:2d}. {string_info['string_id']:25s} ({string_info['segment_count']} segmentów){Colors.RESET}")
    
    print(f"\n{Colors.BRIGHT_CYAN}Opcje:{Colors.RESET}")
    print(f"  {Colors.BRIGHT_WHITE}1-{len(orphaned)}: Edytuj wybrany string{Colors.RESET}")
    print(f"  {Colors.BRIGHT_WHITE}A: Usuń wszystkie osierocone stringi{Colors.RESET}")
    print(f"  {Colors.BRIGHT_WHITE}0: Powrót{Colors.RESET}")
    
    try:
        choice = input(f"\n{Colors.BRIGHT_WHITE}Wybierz opcję: {Colors.RESET}").strip().upper()
        
        if choice == "0":
            return None
        elif choice == "A":
            return remove_all_orphaned_strings(orphaned, inverter_data)
        elif choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(orphaned):
                selected_string = orphaned[choice_num - 1]
                return handle_single_orphaned_string(selected_string, inverter_data, texts)
            else:
                console.error("Nieprawidłowy numer")
                return None
        else:
            console.error("Nieprawidłowy wybór")
            return None
            
    except (ValueError, KeyboardInterrupt):
        console.error("Przerwano lub nieprawidłowy wybór")
        return None

def handle_single_orphaned_string(string_info: Dict, inverter_data: Dict, texts: List) -> Dict:
    """
    Obsługuje pojedynczy osierocony string
    """
    string_id = string_info['string_id']
    console.info(f"EDYCJA OSIEROCONEGO STRINGA: {string_id}")
    
    print(f"\n{Colors.BRIGHT_CYAN}Opcje:{Colors.RESET}")
    print(f"  {Colors.BRIGHT_GREEN}1. Przypisz do istniejącego tekstu{Colors.RESET}")
    print(f"  {Colors.BRIGHT_YELLOW}2. Stwórz nowy tekst{Colors.RESET}")
    print(f"  {Colors.BRIGHT_RED}3. Usuń string{Colors.RESET}")
    print(f"  {Colors.BRIGHT_WHITE}4. Anuluj{Colors.RESET}")
    
    try:
        choice = int(input(f"\n{Colors.BRIGHT_WHITE}Wybierz opcję (1-4): {Colors.RESET}"))
        
        if choice == 1:
            return assign_orphaned_to_existing_text(string_info, inverter_data, texts)
        elif choice == 2:
            return create_text_for_orphaned_string(string_info, texts, inverter_data)
        elif choice == 3:
            return remove_orphaned_string(string_info, inverter_data)
        elif choice == 4:
            console.info("Anulowano edycję stringa")
            return None
        else:
            console.error("Nieprawidłowy wybór")
            return None
            
    except (ValueError, KeyboardInterrupt):
        console.error("Przerwano lub nieprawidłowy wybór")
        return None

def assign_orphaned_to_existing_text(string_info: Dict, inverter_data: Dict, texts: List) -> Dict:
    """
    Przypisz osierocony string do istniejącego tekstu
    """
    # Znajdź nieprzypisane teksty
    assigned_text_ids = set()
    for inv_strings in inverter_data.values():
        assigned_text_ids.update(inv_strings.keys())
    
    unassigned_texts = [t for t in texts if t.get('station') == STATION_ID and t['id'] not in assigned_text_ids]
    
    if not unassigned_texts:
        console.error("Brak nieprzypisanych tekstów")
        return None
    
    console.info("Dostępne nieprzypisane teksty:")
    for i, text in enumerate(unassigned_texts):
        print(f"  {Colors.BRIGHT_GREEN}{i+1:2d}. {text['id']}{Colors.RESET}")
    
    try:
        text_choice = int(input(f"\n{Colors.BRIGHT_WHITE}Wybierz tekst: {Colors.RESET}")) - 1
        
        if 0 <= text_choice < len(unassigned_texts):
            selected_text = unassigned_texts[text_choice]
            
            # Zmień ID stringa
            old_string_id = string_info['string_id']
            new_string_id = selected_text['id']
            inverter_id = string_info['inverter_id']
            
            # Przenieś segmenty
            segments = inverter_data[inverter_id][old_string_id]
            del inverter_data[inverter_id][old_string_id]
            inverter_data[inverter_id][new_string_id] = segments
            
            logger.info(f"Przypisano osierocony string '{old_string_id}' do tekstu '{new_string_id}'")
            console.success(f"Przypisano string do tekstu '{new_string_id}'")
            
            return {
                'action': 'orphaned_assigned',
                'old_string_id': old_string_id,
                'new_string_id': new_string_id,
                'text': selected_text
            }
        else:
            console.error("Nieprawidłowy wybór tekstu")
            return None
            
    except (ValueError, KeyboardInterrupt):
        console.error("Przerwano lub nieprawidłowy wybór")
        return None

def create_text_for_orphaned_string(string_info: Dict, texts: List, inverter_data: Dict) -> Dict:
    """
    Stwórz nowy tekst dla osieroconego stringa
    """
    custom_text_id = input(f"{Colors.BRIGHT_WHITE}Podaj ID dla nowego tekstu: {Colors.RESET}").strip()
    
    if not custom_text_id:
        console.error("Nie podano ID tekstu")
        return None
    
    # Sprawdź czy tekst już istnieje
    if any(t['id'] == custom_text_id for t in texts):
        console.error(f"Tekst '{custom_text_id}' już istnieje")
        return None
    
    # Stwórz nowy tekst (pozycja dummy)
    new_text = {
        'id': custom_text_id,
        'pos': (0, 0),  # Pozycja dummy
        'station': STATION_ID
    }
    texts.append(new_text)
    
    # Zmień ID stringa
    old_string_id = string_info['string_id']
    inverter_id = string_info['inverter_id']
    
    segments = inverter_data[inverter_id][old_string_id]
    del inverter_data[inverter_id][old_string_id]
    inverter_data[inverter_id][custom_text_id] = segments
    
    logger.info(f"Stworzono nowy tekst '{custom_text_id}' dla osieroconego stringa '{old_string_id}'")
    console.success(f"Stworzono tekst '{custom_text_id}' dla stringa")
    
    return {
        'action': 'text_created_for_orphaned',
        'old_string_id': old_string_id,
        'new_text_id': custom_text_id,
        'created_text': new_text
    }

def remove_orphaned_string(string_info: Dict, inverter_data: Dict) -> Dict:
    """
    Usuń osierocony string
    """
    string_id = string_info['string_id']
    confirm = input(f"\n{Colors.BRIGHT_RED}Czy na pewno usunąć string '{string_id}' z {string_info['segment_count']} segmentami? (t/N): {Colors.RESET}").strip().lower()
    
    if confirm not in ['t', 'tak', 'y', 'yes']:
        console.info("Anulowano usuwanie stringa")
        return None
    
    inverter_id = string_info['inverter_id']
    del inverter_data[inverter_id][string_id]
    
    logger.info(f"Usunięto osierocony string '{string_id}' z {string_info['segment_count']} segmentami")
    console.success(f"Usunięto string '{string_id}'")
    
    return {
        'action': 'orphaned_removed',
        'string_id': string_id,
        'segment_count': string_info['segment_count']
    }

def remove_all_orphaned_strings(orphaned_strings: List, inverter_data: Dict) -> Dict:
    """
    Usuń wszystkie osierocone stringi
    """
    total_segments = sum(s['segment_count'] for s in orphaned_strings)
    confirm = input(f"\n{Colors.BRIGHT_RED}Czy na pewno usunąć wszystkie {len(orphaned_strings)} osieroconych stringów ({total_segments} segmentów)? (t/N): {Colors.RESET}").strip().lower()
    
    if confirm not in ['t', 'tak', 'y', 'yes']:
        console.info("Anulowano usuwanie stringów")
        return None
    
    removed_count = 0
    for string_info in orphaned_strings:
        inverter_id = string_info['inverter_id']
        string_id = string_info['string_id']
        
        if inverter_id in inverter_data and string_id in inverter_data[inverter_id]:
            del inverter_data[inverter_id][string_id]
            removed_count += 1
    
    logger.info(f"Usunięto {removed_count} osieroconych stringów ({total_segments} segmentów)")
    console.success(f"Usunięto {removed_count} osieroconych stringów")
    
    return {
        'action': 'all_orphaned_removed',
        'removed_count': removed_count,
        'total_segments': total_segments
    }

def handle_string_swap(inverter_data: Dict, texts: List) -> Dict:
    """
    Obsługuje zamianę przypisań między dwoma stringami
    """
    console.header("ZAMIANA PRZYPISAŃ MIĘDZY STRINGAMI")
    
    # Zbierz wszystkie przypisane stringi
    assigned_strings = []
    for inv_id, strings in inverter_data.items():
        for str_id, segments in strings.items():
            # Znajdź tekst przypisany do tego stringa
            assigned_text = None
            for text in texts:
                if text.get('station') == STATION_ID and text['id'] == str_id:
                    assigned_text = text
                    break
            
            if assigned_text:
                assigned_strings.append({
                    'string_id': str_id,
                    'inverter_id': inv_id,
                    'assigned_text': assigned_text,
                    'segments': segments,
                    'segment_count': len(segments)
                })
    
    if len(assigned_strings) < 2:
        console.error("Potrzeba co najmniej 2 przypisanych stringów do zamiany")
        return None
    
    console.info(f"Dostępnych stringів do zamiany: {len(assigned_strings)}")
    
    # Pokaż listę przypisanych stringów
    for i, string_info in enumerate(assigned_strings):
        segments_info = f"({string_info['segment_count']} segmentów)" if string_info['segments'] else "(brak segmentów)"
        print(f"  {Colors.BRIGHT_CYAN}{i+1:2d}. {string_info['string_id']:25s} -> {string_info['assigned_text']['id']:25s} {segments_info}{Colors.RESET}")
    
    try:
        print(f"\n{Colors.BRIGHT_WHITE}Wybierz pierwszy string do zamiany:{Colors.RESET}")
        choice1 = int(input("Numer pierwszego stringa: ")) - 1
        
        if not (0 <= choice1 < len(assigned_strings)):
            console.error("Nieprawidłowy numer pierwszego stringa")
            return None
        
        print(f"\n{Colors.BRIGHT_WHITE}Wybierz drugi string do zamiany:{Colors.RESET}")
        choice2 = int(input("Numer drugiego stringa: ")) - 1
        
        if not (0 <= choice2 < len(assigned_strings)):
            console.error("Nieprawidłowy numer drugiego stringa")
            return None
        
        if choice1 == choice2:
            console.error("Nie można zamienić stringa z samym sobą")
            return None
        
        string1 = assigned_strings[choice1]
        string2 = assigned_strings[choice2]
        
        # Potwierdź zamianę
        console.info("PODGLĄD ZAMIANY:")
        print(f"  {Colors.BRIGHT_YELLOW}String 1: {string1['string_id']} -> {string1['assigned_text']['id']}{Colors.RESET}")
        print(f"  {Colors.BRIGHT_YELLOW}String 2: {string2['string_id']} -> {string2['assigned_text']['id']}{Colors.RESET}")
        print(f"\n  {Colors.BRIGHT_GREEN}Po zamianie:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}String 1: {string1['string_id']} -> {string2['assigned_text']['id']}{Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}String 2: {string2['string_id']} -> {string1['assigned_text']['id']}{Colors.RESET}")
        
        confirm = input(f"\n{Colors.BRIGHT_WHITE}Potwierdź zamianę (t/N): {Colors.RESET}").strip().lower()
        
        if confirm not in ['t', 'tak', 'y', 'yes']:
            console.info("Anulowano zamianę")
            return None
        
        # Wykonaj zamianę
        # 1. Zapisz segmenty obu stringów
        segments1 = string1['segments']
        segments2 = string2['segments']
        
        # 2. Usuń oba stringi z inverter_data
        if string1['string_id'] in inverter_data[string1['inverter_id']]:
            del inverter_data[string1['inverter_id']][string1['string_id']]
        if string2['string_id'] in inverter_data[string2['inverter_id']]:
            del inverter_data[string2['inverter_id']][string2['string_id']]
        
        # 3. Dodaj stringi z zamienionymi ID tekstów
        inverter_data[string1['inverter_id']][string2['assigned_text']['id']] = segments1
        inverter_data[string2['inverter_id']][string1['assigned_text']['id']] = segments2
        
        logger.info(f"ZAMIANA STRINGÓW: '{string1['string_id']}' <-> '{string2['string_id']}' "
                   f"(teksty: '{string1['assigned_text']['id']}' <-> '{string2['assigned_text']['id']}')")
        
        console.success(f"Zamieniono przypisania stringów!")
        console.result("String 1", f"{string1['string_id']} -> {string2['assigned_text']['id']}", Colors.BRIGHT_GREEN)
        console.result("String 2", f"{string2['string_id']} -> {string1['assigned_text']['id']}", Colors.BRIGHT_GREEN)
        
        return {
            'action': 'string_swap',
            'string1': string1,
            'string2': string2,
            'text1_new': string2['assigned_text'],
            'text2_new': string1['assigned_text']
        }
        
    except (ValueError, KeyboardInterrupt):
        console.error("Przerwano lub nieprawidłowy wybór")
        return None

def interactive_assignment_menu(unassigned_texts: List, unassigned_segments: List, inverter_data: Dict, texts: List, station_id: str = None) -> Dict:
    """
    Główne menu interaktywnego trybu edycji
    """
    # Użyj station_id z parametru lub domyślnego z config
    if station_id is None:
        from src.core.config import STATION_ID
        station_id = STATION_ID
    
    # Ustaw globalną zmienną CURRENT_STATION_ID dla pozostałych funkcji
    global CURRENT_STATION_ID
    CURRENT_STATION_ID = station_id
        
    console.header("INTERAKTYWNY TRYB EDYCJI PRZYPISAŃ")
    
    # Sprawdź czy są osierocone stringi
    orphaned_strings = get_orphaned_strings(inverter_data, texts, station_id)
    if orphaned_strings:
        console.warning(f"Znaleziono {len(orphaned_strings)} osieroconych stringów (bez przypisanych tekstów)")
    
    # Wybór trybu pracy
    console.info("WYBÓR TRYBU PRACY:")
    print(f"  {Colors.BRIGHT_GREEN}1. Rozpocznij od nieprzypisanych tekstów{Colors.RESET}")
    print(f"  {Colors.BRIGHT_CYAN}2. Rozpocznij od edycji segmentów{Colors.RESET}")
    if orphaned_strings:
        print(f"  {Colors.BRIGHT_YELLOW}3. Rozpocznij od osieroconych stringów{Colors.RESET}")
    
    try:
        mode_choice = input(f"\n{Colors.BRIGHT_WHITE}Wybierz tryb (1-{'3' if orphaned_strings else '2'}): {Colors.RESET}").strip()
        
        if mode_choice == "2":
            # Tryb edycji segmentów
            return segment_editing_mode(unassigned_texts, unassigned_segments, inverter_data, texts, station_id)
        elif mode_choice == "3" and orphaned_strings:
            # Tryb osieroconych stringów
            return orphaned_strings_mode(unassigned_texts, unassigned_segments, inverter_data, texts, station_id)
        else:
            # Domyślny tryb tekstów (lub nieprawidłowy wybór)
            if mode_choice not in ["1"]:
                console.info("Nieprawidłowy wybór, rozpoczynam od tekstów")
            return text_editing_mode(unassigned_texts, unassigned_segments, inverter_data, texts, station_id)
            
    except (ValueError, KeyboardInterrupt):
        console.info("Rozpoczynam domyślny tryb (teksty)")
        return text_editing_mode(unassigned_texts, unassigned_segments, inverter_data, texts)

def text_editing_mode(unassigned_texts: List, unassigned_segments: List, inverter_data: Dict, texts: List, station_id: str = None) -> Dict:
    """
    Tryb edycji rozpoczynający od nieprzypisanych tekstów
    """
    changes = {
        'swaps': [],
        'new_assignments': [],
        'custom_strings': [],
        'skipped': []
    }
    
    # Generuj interaktywny SVG na początku
    temp_svg_path = "interactive_assignment.svg"
    console.step("Generowanie SVG do podglądu", "🎨")
    generate_interactive_svg(inverter_data, texts, unassigned_texts, unassigned_segments, temp_svg_path, station_id)
    
    console.info(f"📍 OTWÓRZ PLIK: {temp_svg_path}", "🔍")
    console.separator()
    print(f"  {Colors.BRIGHT_BLUE}• Niebieskie linie z numerami segmentów = PRZYPISANE{Colors.RESET}")
    print(f"  {Colors.BRIGHT_MAGENTA}• Różowe linie z numerami = NIEPRZYPISANE segmenty{Colors.RESET}")
    print(f"  {Colors.BRIGHT_GREEN}• Zielone kropki = nieprzypisane teksty{Colors.RESET}")
    console.separator()
    
    remaining_texts = unassigned_texts.copy()
    
    while remaining_texts:
        # Regeneruj SVG po każdej zmianie
        console.step("Aktualizacja SVG", "🔄")
        generate_interactive_svg(inverter_data, texts, remaining_texts, unassigned_segments, temp_svg_path, station_id)
        
        console.info(f"NIEPRZYPISANYCH TEKSTÓW: {len(remaining_texts)}", "📝")
        
        if not remaining_texts:
            break
            
        # Pokaż listę nieprzypisanych tekstów - WSZYSTKIE
        for i, text in enumerate(remaining_texts):
            x, y = text['pos']
            print(f"  {Colors.BRIGHT_YELLOW}{i+1:2d}. {text['id']:20s} @ ({x:6.1f}, {y:6.1f}){Colors.RESET}")
        
        print(f"\n{Colors.BRIGHT_CYAN}Opcje:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}1-{len(remaining_texts)}: Edytuj wybrany tekst{Colors.RESET}")
            
        print(f"  {Colors.BRIGHT_WHITE}X: Zamiana przypisań między stringami{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}G: Edycja przypisań segmentów{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}O: Zarządzanie osieroconymi stringami{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}A: Przetwórz wszystkie automatycznie{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}S: Statystyki{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}0: Zakończ{Colors.RESET}")
        
        try:
            choice = input(f"\n{Colors.BRIGHT_WHITE}Wybierz opcję: {Colors.RESET}").strip().upper()
            
            if choice == "0":
                console.info("Kończenie trybu interaktywnego")
                break
            elif choice == "X":
                # Zamiana przypisań między stringami
                result = handle_string_swap(inverter_data, texts)
                if result:
                    changes['swaps'].append(result)
                continue
            elif choice == "G":
                # Edycja przypisań segmentów
                result = handle_segment_editing(inverter_data, unassigned_segments, texts)
                if result:
                    if result['action'] in ['segment_reassigned', 'segment_removed', 'unassigned_segment_removed']:
                        changes['new_assignments'].append(result)
                continue
            elif choice == "O":
                # Zarządzanie osieroconymi stringami
                result = handle_orphaned_strings(inverter_data, texts)
                if result:
                    changes['custom_strings'].append(result)
                continue
            elif choice == "A":
                # Automatycznie przetwórz wszystkie pozostałe
                result = auto_process_remaining_texts(remaining_texts, unassigned_segments, inverter_data, texts)
                changes['new_assignments'].extend(result['new_assignments'])
                remaining_texts.clear()
                break
            elif choice == "S":
                show_statistics(inverter_data, texts, remaining_texts, unassigned_segments)
                continue
            elif choice.isdigit():
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(remaining_texts):
                    selected_text = remaining_texts[choice_num - 1]
                    result = process_single_text_interactive(selected_text, remaining_texts, unassigned_segments, inverter_data, texts)
                    if result:
                        if result['action'] == 'swap':
                            changes['swaps'].append(result)
                        elif result['action'] == 'assign':
                            changes['new_assignments'].append(result)
                        elif result['action'] == 'custom':
                            changes['custom_strings'].append(result)
                        elif result['action'] == 'skip':
                            changes['skipped'].append(result)
                        
                        # Usuń z listy jeśli został przetworzony
                        if result['action'] != 'skip':
                            remaining_texts.remove(selected_text)
                else:
                    console.error("Nieprawidłowy numer")
            else:
                console.error("Nieprawidłowy wybór")
                
        except (ValueError, KeyboardInterrupt):
            console.info("Przerwano przez użytkownika")
            break
    
    # Finalne podsumowanie
    console.header("PODSUMOWANIE ZMIAN")
    console.result("Zamiany tekstów", len(changes['swaps']), Colors.BRIGHT_CYAN)
    console.result("Nowe przypisania", len(changes['new_assignments']), Colors.BRIGHT_GREEN)
    console.result("Custom stringi", len(changes['custom_strings']), Colors.BRIGHT_YELLOW)
    console.result("Pominięte", len(changes['skipped']), Colors.BRIGHT_RED)
    
    return changes

def process_single_text_interactive(target_text: Dict, remaining_texts: List, unassigned_segments: List, inverter_data: Dict, texts: List) -> Dict:
    """
    Przetwarzaj pojedynczy tekst interaktywnie
    """
    console.info(f"EDYCJA TEKSTU: {target_text['id']}", "🎯")
    x, y = target_text['pos']
    console.result("Pozycja", f"({x:.1f}, {y:.1f})", Colors.BRIGHT_GREEN)
    
    # Znajdź pobliskie stringi
    nearby_assigned = find_nearby_assigned_strings(target_text, inverter_data, texts, max_distance=50.0)
    
    console.separator()
    print(f"{Colors.BRIGHT_CYAN}Opcje:{Colors.RESET}")
    option = 1
    
    # Opcja 1: Zamiana z istniejącym stringiem
    if nearby_assigned:
        print(f"  {Colors.BRIGHT_YELLOW}{option}. Zamień z istniejącym stringiem{Colors.RESET}")
        for i, string_info in enumerate(nearby_assigned):  # Pokaż wszystkie najbliższe
            print(f"     {Colors.DIM}{i+1}. {string_info['string_id']} ({string_info['distance']:.1f}){Colors.RESET}")
        option += 1
    
    # Opcja 2: Przypisz do nieprzypisanego segmentu
    if unassigned_segments:
        print(f"  {Colors.BRIGHT_CYAN}{option}. Przypisz do nieprzypisanego segmentu (dostępne: {len(unassigned_segments)}){Colors.RESET}")
        option += 1
    
    # Opcja 3: Stwórz custom string
    print(f"  {Colors.BRIGHT_CYAN}{option}. Stwórz nowy string z własnym ID{Colors.RESET}")
    custom_option = option
    option += 1
    
    # Opcja 4: Pomiń
    print(f"  {Colors.BRIGHT_RED}{option}. Pomiń ten tekst{Colors.RESET}")
    skip_option = option
    
    try:
        choice = input(f"\n{Colors.BRIGHT_WHITE}Wybierz opcję (1-{option}): {Colors.RESET}").strip()
        choice_num = int(choice)
        
        current_option = 1
        
        # Obsłuż zamianę
        if nearby_assigned and choice_num == current_option:
            if len(nearby_assigned) == 1:
                chosen_string = nearby_assigned[0]
            else:
                console.info("Dostępne stringi do zamiany:")
                for i, string_info in enumerate(nearby_assigned):
                    print(f"  {i+1}. {string_info['string_id']} -> {string_info['assigned_text']['id']} (odległość: {string_info['distance']:.1f})")
                
                string_choice = int(input("Wybierz string: ")) - 1
                if 0 <= string_choice < len(nearby_assigned):
                    chosen_string = nearby_assigned[string_choice]
                else:
                    console.error("Nieprawidłowy wybór")
                    return None
            
            old_text = swap_text_assignment(target_text, chosen_string, inverter_data)
            remaining_texts.append(old_text)  # Dodaj odłączony tekst do nieprzypisanych
            
            console.success(f"Zamieniono: '{target_text['id']}' ↔ '{old_text['id']}'")
            return {
                'action': 'swap',
                'text': target_text,
                'old_text': old_text,
                'string_id': chosen_string['string_id']
            }
            
        current_option += 1 if nearby_assigned else 0
        
        # Obsłuż przypisanie do nieprzypisanego segmentu
        if unassigned_segments and choice_num == current_option:
            segment_choice = int(input(f"Numer segmentu (1-{len(unassigned_segments)}): ")) - 1
            if assign_text_to_new_string(target_text, unassigned_segments, inverter_data, segment_choice):
                console.success(f"Przypisano '{target_text['id']}' do segmentu {segment_choice+1}")
                return {
                    'action': 'assign',
                    'text': target_text,
                    'segment_index': segment_choice
                }
            else:
                console.error("Nieprawidłowy numer segmentu")
                return None
                
        current_option += 1 if unassigned_segments else 0
        
        # Obsłuż custom string
        if choice_num == custom_option:
            custom_id = input(f"{Colors.BRIGHT_WHITE}Podaj ID dla nowego stringa: {Colors.RESET}").strip()
            if custom_id and create_custom_string(target_text, custom_id, inverter_data):
                console.success(f"Stworzono nowy string '{custom_id}'")
                return {
                    'action': 'custom',
                    'text': target_text,
                    'custom_id': custom_id
                }
            else:
                console.error("Błąd tworzenia custom stringa")
                return None
        
        # Obsłuż pomijanie
        if choice_num == skip_option:
            console.info(f"Pominięto tekst '{target_text['id']}'")
            return {
                'action': 'skip',
                'text': target_text
            }
            
    except (ValueError, KeyboardInterrupt):
        console.error("Przerwano lub nieprawidłowy wybór")
        return None
    
    return None

def auto_process_remaining_texts(remaining_texts: List, unassigned_segments: List, inverter_data: Dict, texts: List) -> Dict:
    """
    Automatycznie przypisz pozostałe teksty do dostępnych segmentów
    """
    console.step("Automatyczne przetwarzanie pozostałych tekstów", "🤖")
    
    result = {
        'new_assignments': [],
        'custom_strings': []
    }
    
    # Przypisz teksty do dostępnych segmentów
    segment_idx = 0
    for text in remaining_texts:
        if segment_idx < len(unassigned_segments):
            if assign_text_to_new_string(text, unassigned_segments, inverter_data, segment_idx):
                result['new_assignments'].append({
                    'text': text,
                    'segment_index': segment_idx
                })
            segment_idx += 1
        else:
            # Jeśli brakuje segmentów, stwórz custom string
            custom_id = f"CUSTOM_{text['id']}"
            if create_custom_string(text, custom_id, inverter_data):
                result['custom_strings'].append({
                    'text': text,
                    'custom_id': custom_id
                })
    
    console.success(f"Automatycznie przetworzono {len(result['new_assignments']) + len(result['custom_strings'])} tekstów")
    return result

def show_statistics(inverter_data: Dict, texts: List, remaining_texts: List, unassigned_segments: List):
    """
    Pokaż aktualną statystykę przypisań
    """
    console.header("STATYSTYKI SYSTEMU")
    
    assigned_count = len([t for t in texts if t.get('station') == STATION_ID]) - len(remaining_texts)
    total_texts = len([t for t in texts if t.get('station') == STATION_ID])
    
    console.result("Tekstów docelowej stacji", total_texts, Colors.BRIGHT_WHITE)
    console.result("Tekstów przypisanych", assigned_count, Colors.BRIGHT_GREEN)
    console.result("Tekstów nieprzypisanych", len(remaining_texts), Colors.BRIGHT_RED)
    console.result("Nieprzypisanych segmentów", len(unassigned_segments), Colors.BRIGHT_YELLOW)
    
    # Postęp w procentach
    progress = (assigned_count / total_texts) * 100 if total_texts > 0 else 0
    console.result("Postęp przypisań", f"{progress:.1f}%", Colors.BRIGHT_CYAN)
    
    console.separator()
    
    # Pokaż stringi
    total_strings = sum(len(strings) for strings in inverter_data.values())
    console.result("Łączna liczba stringów", total_strings, Colors.BRIGHT_MAGENTA)
    
    for inv_id, strings in inverter_data.items():
        console.result(f"Inverter {inv_id}", len(strings), Colors.BRIGHT_BLUE)
    
    # Pokaż osierocone stringi
    orphaned_strings = get_orphaned_strings(inverter_data, texts)
    if orphaned_strings:
        console.result("Osierocone stringi", len(orphaned_strings), Colors.BRIGHT_RED)

def segment_editing_mode(unassigned_texts: List, unassigned_segments: List, inverter_data: Dict, texts: List, station_id: str = None) -> Dict:
    """
    Tryb edycji rozpoczynający od segmentów
    """
    console.info("TRYB EDYCJI SEGMENTÓW")
    
    changes = {
        'swaps': [],
        'new_assignments': [],
        'custom_strings': [],
        'skipped': []
    }
    
    # Generuj interaktywny SVG
    temp_svg_path = "interactive_assignment.svg"
    console.step("Generowanie SVG do podglądu", "🎨")
    generate_interactive_svg(inverter_data, texts, unassigned_texts, unassigned_segments, temp_svg_path, station_id)
    
    console.info(f"📍 OTWÓRZ PLIK: {temp_svg_path}", "🔍")
    console.separator()
    print(f"  {Colors.BRIGHT_BLUE}• Niebieskie linie z numerami segmentów = PRZYPISANE{Colors.RESET}")
    print(f"  {Colors.BRIGHT_MAGENTA}• Różowe linie z numerami = NIEPRZYPISANE segmenty{Colors.RESET}")
    print(f"  {Colors.BRIGHT_GREEN}• Zielone kropki = nieprzypisane teksty{Colors.RESET}")
    console.separator()
    
    while True:
        # Regeneruj SVG po każdej zmianie
        console.step("Aktualizacja SVG", "🔄")
        generate_interactive_svg(inverter_data, texts, unassigned_texts, unassigned_segments, temp_svg_path, station_id)
        
        print(f"\n{Colors.BRIGHT_CYAN}Opcje trybu segmentów:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}G: Edytuj przypisanie segmentu{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}X: Zamiana przypisań między stringami{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}O: Zarządzanie osieroconymi stringami{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}T: Przełącz na tryb tekstów{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}S: Statystyki{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}0: Zakończ{Colors.RESET}")
        
        try:
            choice = input(f"\n{Colors.BRIGHT_WHITE}Wybierz opcję: {Colors.RESET}").strip().upper()
            
            if choice == "0":
                console.info("Kończenie trybu edycji segmentów")
                break
            elif choice == "G":
                result = handle_segment_editing(inverter_data, unassigned_segments, texts)
                if result:
                    changes['new_assignments'].append(result)
            elif choice == "X":
                result = handle_string_swap(inverter_data, texts)
                if result:
                    changes['swaps'].append(result)
            elif choice == "O":
                result = handle_orphaned_strings(inverter_data, texts)
                if result:
                    changes['custom_strings'].append(result)
            elif choice == "T":
                # Przełącz na tryb tekstów
                console.info("Przełączanie na tryb tekstów...")
                text_changes = text_editing_mode(unassigned_texts, unassigned_segments, inverter_data, texts)
                # Połącz zmiany
                for key in changes:
                    changes[key].extend(text_changes.get(key, []))
                break
            elif choice == "S":
                show_statistics(inverter_data, texts, unassigned_texts, unassigned_segments)
            else:
                console.error("Nieprawidłowy wybór")
                
        except (ValueError, KeyboardInterrupt):
            console.info("Przerwano przez użytkownika")
            break
    
    return changes

def orphaned_strings_mode(unassigned_texts: List, unassigned_segments: List, inverter_data: Dict, texts: List, station_id: str = None) -> Dict:
    """
    Tryb rozpoczynający od zarządzania osieroconymi stringami
    """
    console.info("TRYB OSIEROCONYCH STRINGÓW")
    
    changes = {
        'swaps': [],
        'new_assignments': [],
        'custom_strings': [],
        'skipped': []
    }
    
    # Generuj interaktywny SVG
    temp_svg_path = "interactive_assignment.svg"
    console.step("Generowanie SVG do podglądu", "🎨")
    generate_interactive_svg(inverter_data, texts, unassigned_texts, unassigned_segments, temp_svg_path, station_id)
    
    console.info(f"📍 OTWÓRZ PLIK: {temp_svg_path}", "🔍")
    
    while True:
        # Sprawdź czy są jeszcze osierocone stringi
        orphaned_strings = get_orphaned_strings(inverter_data, texts)
        if not orphaned_strings:
            console.success("Wszystkie osierocone stringi zostały obsłużone!")
            break
        
        # Regeneruj SVG po każdej zmianie
        console.step("Aktualizacja SVG", "🔄")
        generate_interactive_svg(inverter_data, texts, unassigned_texts, unassigned_segments, temp_svg_path, station_id)
        
        print(f"\n{Colors.BRIGHT_CYAN}Opcje trybu osieroconych stringów:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}O: Zarządzaj osieroconymi stringami ({len(orphaned_strings)}){Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}G: Edytuj przypisanie segmentu{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}X: Zamiana przypisań między stringami{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}T: Przełącz na tryb tekstów{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}S: Statystyki{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}0: Zakończ{Colors.RESET}")
        
        try:
            choice = input(f"\n{Colors.BRIGHT_WHITE}Wybierz opcję: {Colors.RESET}").strip().upper()
            
            if choice == "0":
                console.info("Kończenie trybu osieroconych stringów")
                break
            elif choice == "O":
                result = handle_orphaned_strings(inverter_data, texts)
                if result:
                    changes['custom_strings'].append(result)
            elif choice == "G":
                result = handle_segment_editing(inverter_data, unassigned_segments, texts)
                if result:
                    changes['new_assignments'].append(result)
            elif choice == "X":
                result = handle_string_swap(inverter_data, texts)
                if result:
                    changes['swaps'].append(result)
            elif choice == "T":
                # Przełącz na tryb tekstów
                console.info("Przełączanie na tryb tekstów...")
                text_changes = text_editing_mode(unassigned_texts, unassigned_segments, inverter_data, texts)
                # Połącz zmiany
                for key in changes:
                    changes[key].extend(text_changes.get(key, []))
                break
            elif choice == "S":
                show_statistics(inverter_data, texts, unassigned_texts, unassigned_segments)
            else:
                console.error("Nieprawidłowy wybór")
                
        except (ValueError, KeyboardInterrupt):
            console.info("Przerwano przez użytkownika")
            break
    
    return changes

def get_unassigned_texts(texts: List, inverter_data: Dict, station_id: str = None) -> List[Dict]:
    '''
    Zwraca listę nieprzypisanych tekstów dla stacji
    '''
    from src.core.config import parse_text_to_dict
    
    # Użyj station_id z parametru lub domyślnego z config
    if station_id is None:
        from src.core.config import STATION_ID
        station_id = STATION_ID
    
    assigned_ids = set()
    
    # Zbierz wszystkie ID przypisanych stringów
    for inv_id, strings in inverter_data.items():
        for str_id, segments in strings.items():
            if segments:  # Tylko stringi z segmentami
                assigned_ids.add(str_id)
    
    # Znajdź nieprzypisane teksty
    unassigned = []
    for text in texts:
        # Parsuj ID tekstu i sprawdź czy należy do docelowej stacji
        parsed = parse_text_to_dict(text['id'], station_id)
        if (parsed and parsed.get('station') == station_id and 
            text['id'] not in assigned_ids):
            unassigned.append(text)
    
    return unassigned


def get_unassigned_segments(all_segments: List, inverter_data: Dict) -> List[Dict]:
    '''
    Zwraca listę nieprzypisanych segmentów
    '''
    assigned_segments = set()
    
    # Zbierz wszystkie przypisane segmenty
    for inv_id, strings in inverter_data.items():
        for str_id, segments in strings.items():
            for seg in segments:
                # Używamy tupli współrzędnych jako unikalny identyfikator
                seg_id = (seg['start'][0], seg['start'][1], seg['end'][0], seg['end'][1])
                assigned_segments.add(seg_id)
    
    # Znajdź nieprzypisane segmenty
    unassigned = []
    for seg in all_segments:
        seg_id = (seg['start'][0], seg['start'][1], seg['end'][0], seg['end'][1])
        if seg_id not in assigned_segments:
            unassigned.append(seg)
    
    return unassigned
