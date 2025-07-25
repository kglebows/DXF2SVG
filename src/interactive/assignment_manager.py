#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralny menedżer przypisań - ujednolicona baza danych dla wszystkich operacji
"""

from typing import Dict, List, Tuple, Optional
from src.utils.console_logger import logger

class AssignmentManager:
    """
    Centralny menedżer wszystkich przypisań, numeracji i danych.
    Wszystkie operacje na przypisaniach przechodzą przez tę klasę.
    """
    
    def __init__(self):
        """
        Inicjalizacja pustego menedżera - dane będą załadowane później
        """
        self.original_assigned_data = {}
        self.current_assigned_data = {}
        self.station_texts = []
        self.unassigned_texts = []
        self.unassigned_segments = []
        self.all_texts = []
        self.all_segments = []
        
        # Lista zmian dla GUI
        self.assignment_changes = {
            'new_assignments': [],
            'skipped_texts': []
        }
        
        # Cache numeracji SVG
        self._svg_numbering_cache = None
        
        logger.info("AssignmentManager utworzony (dane nie załadowane)")
    
    def initialize_from_data(self, assigned_data: Dict, all_texts: List, all_segments: List, 
                           unassigned_texts: List, unassigned_segments: List):
        """
        Inicjalizacja z danymi z konwersji DXF lub GUI
        """
        self.original_assigned_data = assigned_data.copy()
        self.current_assigned_data = assigned_data.copy()
        self.all_texts = all_texts.copy()
        self.all_segments = all_segments.copy()
        self.unassigned_texts = unassigned_texts.copy()
        self.unassigned_segments = unassigned_segments.copy()
        
        # station_texts to wszystkie teksty minus nieprzypisane
        unassigned_text_ids = {t.get('id') for t in unassigned_texts}
        self.station_texts = [t for t in all_texts if t.get('id') not in unassigned_text_ids]
        
        # Reset zmian
        self.assignment_changes = {
            'new_assignments': [],
            'skipped_texts': []
        }
        
        # Przebuduj numerację
        self._rebuild_svg_numbering()
        
        logger.info(f"AssignmentManager zainicjalizowany: {len(self.all_texts)} tekstów, {len(self.all_segments)} segmentów")
        
        # Debug: pokaż przykłady ID
        if self.all_texts:
            sample_text_ids = [t.get('id', 'BRAK_ID') for t in self.all_texts[:3]]
            logger.debug(f"Przykładowe ID tekstów: {sample_text_ids}")
        
        if self.all_segments:
            sample_segment_ids = [s.get('id', 'BRAK_ID') for s in self.all_segments[:3]]
            logger.debug(f"Przykładowe ID segmentów: {sample_segment_ids}")
    
    def _rebuild_svg_numbering(self):
        """Przebuduj numerację SVG dla wszystkich segmentów"""
        self._svg_numbering_cache = {}
        svg_counter = 1
        
        # Najpierw przypisane segmenty (w kolejności z assigned_data)
        for inverter_id, strings in self.current_assigned_data.items():
            for string_name, segments in strings.items():
                if isinstance(segments, list):
                    for segment in segments:
                        seg_id = segment.get('id')
                        if seg_id is not None:
                            self._svg_numbering_cache[seg_id] = svg_counter
                            svg_counter += 1
        
        # Potem nieprzypisane segmenty
        for segment in self.unassigned_segments:
            seg_id = segment.get('id')
            if seg_id is not None and seg_id not in self._svg_numbering_cache:
                self._svg_numbering_cache[seg_id] = svg_counter
                svg_counter += 1
        
        logger.info(f"Przebudowano numerację SVG: {len(self._svg_numbering_cache)} segmentów")
    
    def get_svg_number(self, segment_id: int) -> int:
        """Pobierz numer SVG dla segmentu"""
        if self._svg_numbering_cache is None:
            self._rebuild_svg_numbering()
        return self._svg_numbering_cache.get(segment_id, 0)
    
    def get_all_segments_with_svg_numbers(self) -> List[Dict]:
        """Pobierz wszystkie segmenty z numerami SVG"""
        all_segments = []
        
        # Przypisane segmenty
        for inverter_id, strings in self.current_assigned_data.items():
            for string_name, segments in strings.items():
                if isinstance(segments, list):
                    for segment in segments:
                        segment_copy = segment.copy()
                        segment_copy['svg_number'] = self.get_svg_number(segment.get('id'))
                        segment_copy['is_assigned'] = True
                        segment_copy['assigned_to'] = string_name
                        all_segments.append(segment_copy)
        
        # Nieprzypisane segmenty
        for segment in self.unassigned_segments:
            segment_copy = segment.copy()
            segment_copy['svg_number'] = self.get_svg_number(segment.get('id'))
            segment_copy['is_assigned'] = False
            segment_copy['assigned_to'] = None
            all_segments.append(segment_copy)
        
        return sorted(all_segments, key=lambda x: x.get('svg_number', 0))
    
    def get_text_with_segment_info(self, text_id: str) -> Dict:
        """Pobierz informacje o tekście z numerami przypisanych segmentów"""
        # Znajdź tekst w station_texts
        text_data = None
        for text in self.station_texts:
            if text.get('id') == text_id:
                text_data = text.copy()
                break
        
        if not text_data:
            return None
        
        # Sprawdź czy jest przypisany
        is_assigned = text_id in [t.get('id') for t in self.unassigned_texts]
        text_data['is_unassigned'] = is_assigned
        
        # Znajdź przypisane segmenty
        assigned_segments = []
        for inverter_id, strings in self.current_assigned_data.items():
            if text_id in strings:
                segments = strings[text_id]
                if isinstance(segments, list):
                    for segment in segments:
                        seg_info = segment.copy()
                        seg_info['svg_number'] = self.get_svg_number(segment.get('id'))
                        assigned_segments.append(seg_info)
                break
        
        text_data['assigned_segments'] = assigned_segments
        
        # Format wyświetlania z numerami segmentów
        if assigned_segments:
            segment_numbers = [str(seg['svg_number']) for seg in assigned_segments]
            if len(segment_numbers) == 1:
                text_data['display_format'] = f"{text_id} (#{segment_numbers[0]})"
            else:
                text_data['display_format'] = f"{text_id} (#{segment_numbers[0]}-#{segment_numbers[-1]})"
        else:
            if is_assigned:
                text_data['display_format'] = f"{text_id} (NIEPRZYPISANY)"
            else:
                text_data['display_format'] = f"{text_id}"
        
        return text_data
    
    def assign_text_to_segment(self, text_id: str, segment_id: int) -> Dict:
        """
        Przypisz tekst do segmentu. Zwraca informacje o operacji.
        """
        result = {
            'success': False,
            'message': '',
            'was_reassignment': False,
            'removed_assignments': []
        }
        
        # Sprawdź czy elementy istnieją
        text_exists = any(t.get('id') == text_id for t in self.all_texts)
        segment_exists = any(s.get('id') == segment_id for s in self.all_segments)
        
        logger.debug(f"Sprawdzanie istnienia: tekst '{text_id}' = {text_exists}, segment #{segment_id} = {segment_exists}")
        logger.debug(f"Dostępne teksty: {len(self.all_texts)}, dostępne segmenty: {len(self.all_segments)}")
        
        if not text_exists:
            result['message'] = f"Tekst '{text_id}' nie istnieje w bazie danych"
            logger.warning(f"Tekst nie znaleziony: {text_id}")
            return result
            
        if not segment_exists:
            result['message'] = f"Segment #{segment_id} nie istnieje w bazie danych"
            logger.warning(f"Segment nie znaleziony: {segment_id}")
            return result
        
        # Sprawdź statusy
        text_was_unassigned = text_id in [t.get('id') for t in self.unassigned_texts]
        segment_was_unassigned = segment_id in [s.get('id') for s in self.unassigned_segments]
        
        result['was_reassignment'] = not (text_was_unassigned and segment_was_unassigned)
        
        # Usuń stare przypisania segmentu
        for inv_id, strings in self.current_assigned_data.items():
            for str_id, segments in strings.items():
                if isinstance(segments, list):
                    original_count = len(segments)
                    self.current_assigned_data[inv_id][str_id] = [
                        s for s in segments if s.get('id') != segment_id
                    ]
                    if len(self.current_assigned_data[inv_id][str_id]) < original_count:
                        result['removed_assignments'].append(f"segment #{segment_id} z {str_id}")
        
        # Usuń stare przypisania tekstu - tylko jeśli to przepisanie (reassignment)
        # NIE usuwaj automatycznie wszystkich przypisań - teksty mogą być przypisane do wielu segmentów
        old_assignments_removed = []
        
        # Tylko jeśli użytkownik chce przepisać tekst z jednego miejsca na drugie
        # TO DO: W przyszłości można dodać checkbox "Usuń stare przypisania" w GUI
        # Na razie zachowujemy istniejące przypisania i dodajemy nowe
        
        logger.debug(f"Zachowuję istniejące przypisania tekstu {text_id} i dodaję nowe do segmentu #{segment_id}")
        
        # Znajdź segment do przypisania
        segment_data = None
        for segment in self.all_segments:
            if segment.get('id') == segment_id:
                segment_data = segment.copy()
                break
        
        if not segment_data:
            result['message'] = f"Nie znaleziono danych segmentu #{segment_id}"
            logger.warning(f"Dane segmentu nie znalezione: {segment_id}")
            return result
        
        # Dodaj nowe przypisanie - znajdź istniejący tekst lub utwórz nowy
        target_inverter = None
        
        # Sprawdź czy tekst jest już przypisany gdzieś
        for inv_id, strings in self.current_assigned_data.items():
            if text_id in strings:
                target_inverter = inv_id
                break
        
        # Jeśli tekst nie jest jeszcze przypisany, użyj pierwszego dostępnego invertera
        if target_inverter is None:
            target_inverter = list(self.current_assigned_data.keys())[0] if self.current_assigned_data else "I01"
            if target_inverter not in self.current_assigned_data:
                self.current_assigned_data[target_inverter] = {}
        
        # Upewnij się, że tekst ma listę segmentów
        if text_id not in self.current_assigned_data[target_inverter]:
            self.current_assigned_data[target_inverter][text_id] = []
        
        # Sprawdź czy segment już nie jest przypisany do tego tekstu
        existing_segment_ids = [s.get('id') for s in self.current_assigned_data[target_inverter][text_id]]
        if segment_id not in existing_segment_ids:
            self.current_assigned_data[target_inverter][text_id].append(segment_data)
            logger.debug(f"Dodano segment #{segment_id} do tekstu {text_id} w inverterze {target_inverter}")
        else:
            logger.debug(f"Segment #{segment_id} już jest przypisany do tekstu {text_id}")
            result['message'] = f"Segment #{segment_id} już jest przypisany do tekstu {text_id}"
            return result
        
        # Usuń z list nieprzypisanych
        if text_was_unassigned:
            self.unassigned_texts = [t for t in self.unassigned_texts if t.get('id') != text_id]
        if segment_was_unassigned:
            self.unassigned_segments = [s for s in self.unassigned_segments if s.get('id') != segment_id]
        
        # Znajdź dane tekstu
        text_data = None
        for text in self.all_texts:
            if text.get('id') == text_id:
                text_data = text.copy()
                break
        
        # Dodaj do listy zmian z pełnymi danymi
        self.assignment_changes['new_assignments'].append({
            'text': text_data,
            'segment': segment_data,
            'text_id': text_id,
            'segment_id': segment_id,
            'was_reassignment': result['was_reassignment']
        })
        
        # Przebuduj numerację
        self._rebuild_svg_numbering()
        
        result['success'] = True
        # Sprawdź ile segmentów ma teraz ten tekst
        total_segments = 0
        for inv_id, strings in self.current_assigned_data.items():
            if text_id in strings:
                total_segments += len(strings[text_id])
        
        if total_segments == 1:
            result['message'] = f"Przypisano {text_id} do segmentu #{segment_id}"
        else:
            result['message'] = f"Dodano segment #{segment_id} do tekstu {text_id} (łącznie {total_segments} segmentów)"
        
        logger.info(result['message'])
        return result
    
    def remove_assignment(self, text_id: str, segment_id: int) -> Dict:
        """
        Usuń konkretne przypisanie tekstu do segmentu.
        Przydatne gdy tekst ma wiele segmentów i chcemy usunąć tylko jeden.
        """
        result = {'success': False, 'message': ''}
        
        found = False
        for inv_id, strings in self.current_assigned_data.items():
            if text_id in strings:
                original_count = len(strings[text_id])
                strings[text_id] = [s for s in strings[text_id] if s.get('id') != segment_id]
                
                if len(strings[text_id]) < original_count:
                    found = True
                    # Jeśli tekst nie ma już żadnych segmentów, usuń go całkowicie
                    if len(strings[text_id]) == 0:
                        del strings[text_id]
                        # Dodaj tekst z powrotem do nieprzypisanych
                        text_data = next((t for t in self.all_texts if t.get('id') == text_id), None)
                        if text_data and text_data not in self.unassigned_texts:
                            self.unassigned_texts.append(text_data)
                        result['message'] = f"Usunięto ostatni segment #{segment_id} z tekstu {text_id} - tekst wrócił do nieprzypisanych"
                    else:
                        result['message'] = f"Usunięto segment #{segment_id} z tekstu {text_id} (pozostało {len(strings[text_id])} segmentów)"
                    break
        
        if found:
            # Dodaj segment z powrotem do nieprzypisanych
            segment_data = next((s for s in self.all_segments if s.get('id') == segment_id), None)
            if segment_data and segment_data not in self.unassigned_segments:
                self.unassigned_segments.append(segment_data)
            
            self._rebuild_svg_numbering()
            result['success'] = True
            logger.info(result['message'])
        else:
            result['message'] = f"Nie znaleziono przypisania tekstu {text_id} do segmentu #{segment_id}"
            
        return result

    def skip_text(self, text_id: str) -> Dict:
        """Pomiń tekst (usuń z nieprzypisanych)"""
        result = {'success': False, 'message': ''}
        
        text_was_unassigned = text_id in [t.get('id') for t in self.unassigned_texts]
        
        if not text_was_unassigned:
            # Usuń z przypisań
            for inv_id in list(self.current_assigned_data.keys()):
                if text_id in self.current_assigned_data[inv_id]:
                    del self.current_assigned_data[inv_id][text_id]
                    result['message'] = f"Usunięto i pominięto tekst {text_id}"
                    break
        else:
            self.unassigned_texts = [t for t in self.unassigned_texts if t.get('id') != text_id]
            result['message'] = f"Pominięto tekst {text_id}"
        
        self.assignment_changes['skipped_texts'].append(text_id)
        self._rebuild_svg_numbering()
        
        result['success'] = True
        logger.info(result['message'])
        return result
    
    def reset_to_original(self):
        """Zresetuj do stanu początkowego"""
        self.current_assigned_data = self.original_assigned_data.copy()
        # Przywróć oryginalne listy nieprzypisanych (trzeba je zrekonstruować)
        # To nie jest trywialne, bo musimy porównać z original_assigned_data
        self.assignment_changes = {'new_assignments': [], 'skipped_texts': []}
        self._rebuild_svg_numbering()
        logger.info("Zresetowano do stanu początkowego")
    
    def get_statistics(self) -> Dict:
        """Pobierz statystyki przypisań"""
        total_texts = len(self.station_texts)
        unassigned_texts_count = len(self.unassigned_texts)
        assigned_texts_count = total_texts - unassigned_texts_count
        
        all_segments = self.get_all_segments_with_svg_numbers()
        total_segments = len(all_segments)
        unassigned_segments_count = len(self.unassigned_segments)
        assigned_segments_count = total_segments - unassigned_segments_count
        
        new_assignments = len(self.assignment_changes['new_assignments'])
        skipped_texts = len(self.assignment_changes['skipped_texts'])
        
        return {
            'total_texts': total_texts,
            'assigned_texts': assigned_texts_count,
            'unassigned_texts': unassigned_texts_count,
            'total_segments': total_segments,
            'assigned_segments': assigned_segments_count,
            'unassigned_segments': unassigned_segments_count,
            'new_assignments': new_assignments,
            'skipped_texts': skipped_texts
        }
