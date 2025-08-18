"""
Zaawansowany system formatowania tekstów z obsługą operacji matematycznych
i konfigurowalnych formatów input/output
"""
import re
import math
from typing import Dict, Any, List, Tuple, Union
from src.utils.console_logger import console, logger


class AdvancedFormatter:
    """
    Zaawansowany formatter z obsługą:
    - Zmiennych: {name}, {st}, {tr}, {inv}, {mptt}, {str}, {sub}
    - Formatowania numerycznego: {inv:2} = zero-padding do 2 cyfr
    - Operacji matematycznych: {str}/2 + {str}%2
    - Dodatkowych zmiennych
    """
    
    def __init__(self):
        self.variables = {}
        self.additional_variables = {}
        
    def parse_input_format(self, text: str, input_format: str) -> Dict[str, Any]:
        """
        Parsuje tekst używając formatu input i wyciąga zmienne
        
        Args:
            text: Tekst do parsowania np. "STM2/F06/STR19"
            input_format: Format np. "{name}/F{inv:2}/STR{str:2}"
            
        Returns:
            Dict ze zmiennymi: {'name': 'STM2', 'inv': 6, 'str': 19}
        """
        try:
            # Zamień format na regex pattern
            pattern = self._format_to_regex(input_format)
            logger.debug(f"Input format '{input_format}' -> regex: '{pattern}'")
            
            # Dopasuj pattern do tekstu
            match = re.match(pattern, text)
            if not match:
                logger.warning(f"Tekst '{text}' nie pasuje do formatu '{input_format}'")
                return {}
            
            # Wyciągnij zmienne z dopasowania
            variables = {}
            var_names = self._extract_variable_names(input_format)
            
            for i, var_name in enumerate(var_names, 1):
                value = match.group(i)
                # Konwertuj na int jeśli to możliwe (oprócz 'name')
                if var_name != 'name':
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                variables[var_name] = value
                
            logger.debug(f"Sparsowane zmienne: {variables}")
            self.variables = variables
            return variables
            
        except Exception as e:
            logger.error(f"Błąd parsowania input: {e}")
            return {}
    
    def _format_to_regex(self, format_str: str) -> str:
        """
        Konwertuje format ze zmiennymi na regex pattern
        
        Args:
            format_str: "{name}/F{inv:2}/STR{str:2}"
            
        Returns:
            Regex pattern: "([^/]+)/F(\\d{1,2})/STR(\\d{1,2})"
        """
        pattern = format_str
        
        # Znajdź wszystkie zmienne w formacie {var} lub {var:padding}
        var_pattern = r'\{([^}:]+)(?::(\d+))?\}'
        variables = re.findall(var_pattern, pattern)
        
        # Zamień każdą zmienną na odpowiedni regex
        for var_name, padding in variables:
            var_regex = r'{' + var_name + (f':{padding}' if padding else '') + r'}'
            
            if var_name == 'name':
                # name może zawierać litery i cyfry, ale nie /
                replacement = r'([^/]+)'
            else:
                # Numery - 1 lub więcej cyfr (do max padding jeśli określony)
                if padding:
                    replacement = fr'(\d{{1,{padding}}})'
                else:
                    replacement = r'(\d+)'
            
            pattern = pattern.replace(var_regex, replacement)
        
        return f'^{pattern}$'
    
    def _extract_variable_names(self, format_str: str) -> List[str]:
        """Wyciąga nazwy zmiennych w kolejności występowania"""
        var_pattern = r'\{([^}:]+)(?::\d+)?\}'
        return re.findall(var_pattern, format_str)
    
    def set_additional_variable(self, var_name: str, expression: str):
        """
        Ustawia dodatkową zmienną z wyrażeniem matematycznym
        
        Args:
            var_name: Nazwa zmiennej np. 'mppt'
            expression: Wyrażenie np. '{str}/2 + {str}%2'
        """
        self.additional_variables[var_name] = expression
        logger.debug(f"Dodano zmienną {var_name} = {expression}")
    
    def _evaluate_expression(self, expression: str, variables: Dict[str, Any]) -> Union[int, str]:
        """
        Ewaluuje wyrażenie matematyczne z zmiennymi
        
        Args:
            expression: "{str}/2 + {str}%2"
            variables: {'str': 19}
            
        Returns:
            Wynik: 10 (19//2 + 19%2 = 9 + 1 = 10)
        """
        try:
            # Zamień zmienne na wartości
            eval_expr = expression
            for var_name, value in variables.items():
                var_pattern = f'{{{var_name}}}'
                eval_expr = eval_expr.replace(var_pattern, str(value))
            
            logger.debug(f"Wyrażenie '{expression}' -> '{eval_expr}'")
            
            # Bezpieczne operatory matematyczne
            safe_operators = {
                '+': lambda x, y: x + y,
                '-': lambda x, y: x - y,
                '*': lambda x, y: x * y,
                '/': lambda x, y: x // y,  # Integer division
                '%': lambda x, y: x % y,   # Modulo
            }
            
            # Prosta evaluacja wyrażeń (obsługuje +, -, *, /, %)
            # Dla bezpieczeństwa używamy ograniczonej evaluacji
            result = self._safe_eval(eval_expr)
            
            logger.debug(f"Wynik wyrażenia: {result}")
            return int(result) if isinstance(result, (int, float)) else result
            
        except Exception as e:
            logger.error(f"Błąd ewaluacji wyrażenia '{expression}': {e}")
            return 0
    
    def _safe_eval(self, expression: str) -> Union[int, float]:
        """Bezpieczna evaluacja wyrażeń matematycznych"""
        # Usuń białe znaki
        expression = expression.replace(' ', '')
        
        # Prosta implementacja dla podstawowych operacji
        # Obsługuje tylko liczby i operatory +, -, *, /, %
        if not re.match(r'^[\d+\-*/%()]+$', expression):
            raise ValueError(f"Nieprawidłowe znaki w wyrażeniu: {expression}")
        
        # Użyj eval z ograniczonym scope dla bezpieczeństwa
        allowed_names = {
            "__builtins__": {},
            "__name__": "safe_eval",
            "__file__": "safe_eval",
        }
        
        return eval(expression, allowed_names)
    
    def format_output(self, output_format: str) -> str:
        """
        Formatuje output używając zmiennych i dodatkowych zmiennych
        
        Args:
            output_format: "S{mppt:2}-{str:2}/{inv:2}"
            
        Returns:
            Sformatowany string: "S10-19/06"
        """
        try:
            # Połącz podstawowe zmienne z dodatkowymi
            all_variables = self.variables.copy()
            
            # Oblicz dodatkowe zmienne
            for var_name, expression in self.additional_variables.items():
                result = self._evaluate_expression(expression, self.variables)
                all_variables[var_name] = result
                logger.debug(f"Obliczono {var_name} = {result}")
            
            # Zamień zmienne w formacie output
            result = output_format
            
            # Znajdź wszystkie zmienne z formatowaniem
            var_pattern = r'\{([^}:]+)(?::(\d+))?\}'
            variables_in_format = re.findall(var_pattern, result)
            
            for var_name, padding in variables_in_format:
                if var_name in all_variables:
                    value = all_variables[var_name]
                    
                    # Formatuj wartość
                    if padding and isinstance(value, int):
                        formatted_value = str(value).zfill(int(padding))
                    else:
                        formatted_value = str(value)
                    
                    # Zamień w result
                    var_regex = f'{{{var_name}' + (f':{padding}' if padding else '') + '}'
                    result = result.replace(var_regex, formatted_value)
                    
                    logger.debug(f"Zastąpiono {var_regex} -> {formatted_value}")
                else:
                    logger.warning(f"Zmienna {var_name} nie została znaleziona")
            
            logger.debug(f"Output format '{output_format}' -> '{result}'")
            return result
            
        except Exception as e:
            logger.error(f"Błąd formatowania output: {e}")
            return "ERROR"
    
    @staticmethod
    def get_available_variables() -> List[Tuple[str, str]]:
        """Zwraca listę dostępnych zmiennych z opisami"""
        return [
            ('name', 'Nazwa/string (tekst)'),
            ('st', 'Numer stacji (liczba)'),
            ('tr', 'Numer tracker (liczba)'),
            ('inv', 'Numer falownika/invertera (liczba)'),
            ('mppt', 'Numer MPPT (liczba)'),
            ('str', 'Numer stringa (liczba)'),
            ('sub', 'Numer podstringa (liczba)'),
        ]
    
    @staticmethod
    def get_format_help() -> str:
        """Zwraca tekst pomocy dla formatowania"""
        return """
ZMIENNE:
{name} - nazwa/tekst (np. 'STM2')
{st}, {tr}, {inv}, {mppt}, {str}, {sub} - liczby

FORMATOWANIE NUMERYCZNE:
{inv:2} - zero-padding do 2 cyfr (01, 02, 03...)
{str:3} - zero-padding do 3 cyfr (001, 002, 003...)

PRZYKŁADY INPUT FORMAT:
{name}/F{inv:2}/STR{str:2}  → STM2/F06/STR19
{name}/{inv}-{mppt}         → STM2/6-1
INV{inv:2}-{mppt:2}         → INV06-01

PRZYKŁADY OUTPUT FORMAT:
S{mppt:2}-{str:2}/{inv:2}   → S01-19/06
{name}_{inv:2}_{str:2}      → STM2_06_19

DODATKOWE ZMIENNE (operacje matematyczne):
{str}/2 + {str}%2   → dzielenie całkowite + modulo
{inv}*10 + {mppt}   → mnożenie + dodawanie

PRZYKŁAD KOMPLETNY:
Input:  {name}/F{inv:2}/STR{str:2}
Tekst:  STM2/F06/STR19
Dodatkowa zmienna mppt = {str}/2 + {str}%2  (19/2 + 19%2 = 9+1 = 10)
Output: S{mppt:2}-{str:2}/{inv:2}
Wynik:  S10-19/06
        """


# Globalna instancja formattera
advanced_formatter = AdvancedFormatter()


def parse_text_with_advanced_format(text: str, input_format: str, 
                                   additional_vars: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Funkcja pomocnicza do parsowania tekstów z zaawansowanym formatem
    
    Args:
        text: Tekst do parsowania
        input_format: Format input
        additional_vars: Dodatkowe zmienne {'mppt': '{str}/2 + {str}%2'}
        
    Returns:
        Dict z wszystkimi zmiennymi
    """
    formatter = AdvancedFormatter()
    
    # Parsuj input
    variables = formatter.parse_input_format(text, input_format)
    if not variables:
        return {}
    
    # Dodaj dodatkowe zmienne
    if additional_vars:
        for var_name, expression in additional_vars.items():
            formatter.set_additional_variable(var_name, expression)
    
    # Zwróć wszystkie zmienne (podstawowe + dodatkowe)
    all_vars = variables.copy()
    for var_name, expression in (additional_vars or {}).items():
        result = formatter._evaluate_expression(expression, variables)
        all_vars[var_name] = result
        
    return all_vars


def format_output_with_advanced_format(variables: Dict[str, Any], output_format: str) -> str:
    """
    Funkcja pomocnicza do formatowania output
    
    Args:
        variables: Zmienne do użycia
        output_format: Format output
        
    Returns:
        Sformatowany string
    """
    formatter = AdvancedFormatter()
    formatter.variables = variables
    return formatter.format_output(output_format)
