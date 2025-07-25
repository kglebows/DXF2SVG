"""
Moduł logowania kolorowego do konsoli z emoji i progress barami
"""
import os
import time
import logging

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

class ConsoleLogger:
    """Kolorowe logowanie do konsoli z emoji i progress barami"""
    
    def __init__(self):
        self.step_count = 0
        self.total_steps = 10  # Będzie aktualizowane dynamicznie
        
    def set_total_steps(self, total: int):
        self.total_steps = total
        
    def progress_bar(self, current: int, total: int, width: int = 30) -> str:
        """Generuje progress bar"""
        if total == 0:
            return "█" * width
        
        filled = int(width * current / total)
        bar = "█" * filled + "▓" * (width - filled)
        percent = (current / total) * 100
        return f"[{bar}] {percent:5.1f}%"
    
    def header(self, message: str):
        """Nagłówek sekcji"""
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🚀 {message.upper()}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'='*80}{Colors.RESET}")
        
    def step(self, message: str, emoji: str = "⚡"):
        """Krok procesu - uproszczony bez paska postępu"""
        self.step_count += 1
        print(f"{Colors.BRIGHT_BLUE}{emoji} Step {self.step_count}: {Colors.BRIGHT_WHITE}{message}{Colors.RESET}")
        
    def success(self, message: str, count: int = None):
        """Sukces z opcjonalnym licznikiem"""
        count_str = f" ({count})" if count is not None else ""
        print(f"{Colors.BRIGHT_GREEN}✅ {message}{count_str}{Colors.RESET}")
        
    def warning(self, message: str, count: int = None):
        """Ostrzeżenie z opcjonalnym licznikiem"""
        count_str = f" ({count})" if count is not None else ""
        print(f"{Colors.BRIGHT_YELLOW}⚠️  {message}{count_str}{Colors.RESET}")
        
    def error(self, message: str):
        """Błąd"""
        print(f"{Colors.BRIGHT_RED}❌ {message}{Colors.RESET}")
        
    def info(self, message: str, emoji: str = "ℹ️"):
        """Informacja"""
        print(f"{Colors.BRIGHT_CYAN}{emoji} {message}{Colors.RESET}")
        
    def print(self, message: str, end: str = '\n'):
        """Zwykłe wypisywanie tekstu"""
        print(message, end=end)
        
    def processing(self, message: str, current: int = None, total: int = None):
        """Przetwarzanie z opcjonalnym progress barem - kompatybilny z Windows/PowerShell"""
        if current is not None and total is not None:
            progress = self.progress_bar(current, total, 30)
            # Dla Windows/PowerShell - resetuj linię i wypisz
            print(f"\r{' ' * 80}\r{Colors.BRIGHT_CYAN}📊 {message} {progress}{Colors.RESET}", end='', flush=True)
            # Jeśli to koniec, przejdź do nowej linii
            if current == total:
                print()  # Nowa linia po zakończeniu
        else:
            print(f"\r{' ' * 80}\r{Colors.BRIGHT_CYAN}📊 {message}...{Colors.RESET}", end='', flush=True)
            
    def result(self, label: str, value, color=Colors.BRIGHT_WHITE):
        """Wynik z etykietą"""
        print(f"{Colors.BRIGHT_MAGENTA}📊 {label}: {color}{value}{Colors.RESET}")
        
    def separator(self):
        """Separator"""
        print(f"{Colors.DIM}{'─' * 80}{Colors.RESET}")
        
    def summary_header(self):
        """Nagłówek podsumowania"""
        print(f"\n{Colors.BG_BLUE}{Colors.BRIGHT_WHITE} 📋 PODSUMOWANIE WYNIKÓW {Colors.RESET}")
        print(f"{Colors.BRIGHT_BLUE}{'─' * 80}{Colors.RESET}")

def setup_logging():
    """Konfiguracja systemu logowania - konsola + plik"""
    
    # Próba usunięcia poprzedniego pliku debug.log
    try:
        if os.path.exists('debug.log'):
            os.remove('debug.log')
    except PermissionError:
        # Jeśli plik jest zablokowany, użyj innej nazwy
        timestamp = int(time.time())
        debug_filename = f'debug_{timestamp}.log'
    else:
        debug_filename = 'debug.log'
    
    # Główny logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Wyczyść poprzednie handlery
    logger.handlers.clear()
    
    # Formatter dla pliku - bardzo szczegółowy
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler dla pliku - wszystko
    file_handler = logging.FileHandler(debug_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Dodaj handlery
    logger.addHandler(file_handler)
    
    # Wyłącz domyślne wypisywanie na konsolę
    logger.propagate = False
    
    return logger

# Globalne instancje
console = ConsoleLogger()
logger = setup_logging()
