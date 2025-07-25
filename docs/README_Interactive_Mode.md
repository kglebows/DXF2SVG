# DXF2SVG GUI - Tryb Interaktywny

## Nowe funkcje GUI v2.0

### 🆕 Sekcja "Widok SVG"

Dodano możliwość przełączania między różnymi trybami wyświetlania:

#### Dostępne tryby:
- **📊 Strukturalny (z grupami I01-I04)** - `output_structured.svg`
  - Finalny SVG z grupowaniem według inverterów
  - Grupy nazwane I01, I02, I03, I04
  - Domyślny tryb po konwersji

- **🔢 Początkowy (z numeracją)** - `output_initial.svg`  
  - SVG z numeracją elementów do debugowania
  - Pokazuje wszystkie znalezione elementy z ID
  - Przydatny do analizy procesu konwersji

- **✏️ Interaktywny (edytor przypisań)** - `interactive_assignment.svg`
  - SVG generowany przez tryb interaktywny
  - Pokazuje aktualne przypisania po edycji
  - Automatycznie wybierany po zakończeniu edycji

### 🆕 Sekcja "Tryb Interaktywny"

Pełna integracja z interaktywnym editorem przypisań:

#### Funkcjonalności:
- **🚀 Przycisk "Uruchom Edytor Przypisań"**
  - Aktywny tylko po konwersji z nieprzypisanymi tekstami
  - Uruchamia pełny tryb interaktywny w tle
  - Automatycznie przełącza na widok interaktywny po zakończeniu

- **📊 Status informacyjny**
  - Pokazuje liczbę nieprzypisanych tekstów
  - Informuje o dostępności danych do edycji
  - Aktualizuje się po każdej konwersji i edycji

- **⚠️ Ostrzeżenia**
  - Czerwony tekst pokazuje nieprzypisane teksty
  - Zielony tekst potwierdza kompletne przypisania

## Workflow pracy z trybem interaktywnym

### 1. Podstawowa konwersja
```
Wybierz DXF → Konwertuj → Sprawdź wyniki w trybie "Strukturalny"
```

### 2. Wykrycie nieprzypisanych tekstów
```
GUI automatycznie:
- ✅ Aktywuje przycisk "Uruchom Edytor Przypisań"
- ⚠️ Pokazuje liczbę nieprzypisanych tekstów
- 📝 Umożliwia przełączenie na tryb "Początkowy" do analizy
```

### 3. Interaktywna edycja
```
Kliknij "Uruchom Edytor Przypisań" →
→ Tryb interaktywny w terminalu →
→ Ręczne przypisywanie tekstów →
→ Automatyczne przełączenie na widok "Interaktywny"
```

### 4. Weryfikacja wyników
```
Przełączaj między trybami:
- "Początkowy" - sprawdź co zostało znalezione
- "Interaktywny" - sprawdź wyniki edycji  
- "Strukturalny" - sprawdź finalne grupowanie
```

## Szczegóły techniczne

### Przechowywanie danych
GUI zachowuje dane z ostatniej konwersji w `self.last_conversion_data`:
```python
{
    'assigned_data': dict,       # Przypisane stringi do inverterów
    'station_texts': list,       # Wszystkie teksty stacji
    'unassigned_texts': list,    # Nieprzypisane teksty
    'unassigned_segments': list, # Nieprzypisane segmenty
    'unassigned_polylines': list # Nieprzypisane polilinie
}
```

### Integracja z interactive_editor
- Import funkcji `interactive_assignment_menu`
- Uruchomienie w osobnym wątku (nie blokuje GUI)
- Automatyczna aktualizacja danych po edycji
- Przekierowanie na interactive_assignment.svg

### Obsługa plików SVG
```python
# Mapowanie trybów na pliki
file_mapping = {
    'structured': 'output_structured.svg',    # Grupy I01-I04
    'initial': 'output_initial.svg',         # Z numeracją
    'interactive': 'interactive_assignment.svg' # Po edycji
}
```

## Przykład użycia

### Scenariusz: Plik DXF z nieprzypisanymi tekstami

1. **Ładowanie i konwersja:**
   ```
   GUI → Wybierz input.dxf → Konwertuj
   Status: "⚠️ 3 nieprzypisane teksty"
   ```

2. **Analiza w trybie początkowym:**
   ```
   Przełącz na "Początkowy" → Sprawdź numerację elementów
   ```

3. **Interaktywna edycja:**
   ```
   Kliknij "Uruchom Edytor Przypisań" →
   Terminal: Tryb interaktywny
   → Przypisz teksty ręcznie
   ```

4. **Weryfikacja rezultatów:**
   ```
   GUI automatycznie: 
   → Przełącza na "Interaktywny"
   → Status: "✅ Brak nieprzypisanych tekstów"
   → Przełącz na "Strukturalny" dla finalnej wersji
   ```

## Korzyści nowego workflow

### ✅ Dla użytkownika:
- **Wizualna kontrola** - przełączanie między trybami wyświetlania
- **Bezproblemowa edycja** - GUI obsługuje cały proces w tle
- **Natychmiastowy feedback** - status nieprzypisanych tekstów
- **Elastyczność** - możliwość sprawdzenia każdego etapu procesu

### ✅ Dla procesu:
- **Zachowanie danych** - nie trzeba ponownie analizować DXF
- **Nieblokujący UI** - tryb interaktywny w osobnym wątku
- **Automatyzacja** - przełączanie widoków po zakończeniu edycji
- **Integralność** - jeden interfejs dla całego workflow

## Pliki wyjściowe

Po pełnym procesie otrzymujesz:

1. **`output_initial.svg`** - diagnostyczny, z numeracją
2. **`output_structured.svg`** - finalny, z grupami I01-I04  
3. **`interactive_assignment.svg`** - po ręcznej edycji (jeśli była potrzebna)
4. **`debug.log`** - szczegółowe logi całego procesu

Wszystkie pliki dostępne przez radio buttons w sekcji "Widok SVG"! 🎯
