"""
GUI do konfiguracji zaawansowanego formatowania tekstów
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
from src.core.advanced_formatter import AdvancedFormatter, parse_text_with_advanced_format, format_output_with_advanced_format


class AdvancedFormatterGUI:
    """GUI do konfiguracji zaawansowanego formatowania"""
    
    def __init__(self, parent):
        self.parent = parent
        self.formatter = AdvancedFormatter()
        self.additional_vars = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        # Main frame
        main_frame = ttk.LabelFrame(self.parent, text="🔧 Zaawansowane Formatowanie Tekstów", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input format section
        input_frame = ttk.LabelFrame(main_frame, text="📥 Format Input (parsowanie tekstu)", padding=5)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Format Input:").pack(anchor=tk.W)
        self.input_format_var = tk.StringVar(value="{name}/F{inv:2}/STR{str:2}")
        self.input_format_entry = ttk.Entry(input_frame, textvariable=self.input_format_var, width=50)
        self.input_format_entry.pack(fill=tk.X, pady=(0, 5))
        
        # Test input section
        test_frame = ttk.Frame(input_frame)
        test_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(test_frame, text="Test Input:").pack(side=tk.LEFT)
        self.test_input_var = tk.StringVar(value="STM2/F06/STR19")
        test_entry = ttk.Entry(test_frame, textvariable=self.test_input_var, width=20)
        test_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        test_btn = ttk.Button(test_frame, text="🧪 Test Parsowania", command=self.test_parsing)
        test_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Parsed variables display
        self.parsed_vars_text = tk.Text(input_frame, height=3, wrap=tk.WORD)
        self.parsed_vars_text.pack(fill=tk.X, pady=(5, 0))
        
        # Additional variables section
        additional_frame = ttk.LabelFrame(main_frame, text="➕ Dodatkowe Zmienne", padding=5)
        additional_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Additional vars controls
        add_controls = ttk.Frame(additional_frame)
        add_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(add_controls, text="Zmienna:").pack(side=tk.LEFT)
        self.new_var_name = tk.StringVar(value="mppt")
        ttk.Entry(add_controls, textvariable=self.new_var_name, width=10).pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Label(add_controls, text="Wyrażenie:").pack(side=tk.LEFT)
        self.new_var_expr = tk.StringVar(value="{str}/2 + {str}%2")
        ttk.Entry(add_controls, textvariable=self.new_var_expr, width=20).pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Button(add_controls, text="➕ Dodaj", command=self.add_variable).pack(side=tk.LEFT, padx=(5, 0))
        
        # Additional vars list
        vars_list_frame = ttk.Frame(additional_frame)
        vars_list_frame.pack(fill=tk.X)
        
        self.vars_listbox = tk.Listbox(vars_list_frame, height=4)
        self.vars_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        vars_buttons = ttk.Frame(vars_list_frame)
        vars_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        ttk.Button(vars_buttons, text="🗑️ Usuń", command=self.remove_variable).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(vars_buttons, text="🧪 Test", command=self.test_variables).pack(fill=tk.X)
        
        # Output format section
        output_frame = ttk.LabelFrame(main_frame, text="📤 Format Output (SVG ID)", padding=5)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="Format Output:").pack(anchor=tk.W)
        self.output_format_var = tk.StringVar(value="S{mppt:2}-{str:2}/{inv:2}")
        self.output_format_entry = ttk.Entry(output_frame, textvariable=self.output_format_var, width=50)
        self.output_format_entry.pack(fill=tk.X, pady=(0, 5))
        
        # Output test
        output_test_frame = ttk.Frame(output_frame)
        output_test_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(output_test_frame, text="🧪 Test Output", command=self.test_output).pack(side=tk.LEFT)
        
        self.output_result_var = tk.StringVar(value="Wynik pojawi się tutaj...")
        ttk.Label(output_test_frame, textvariable=self.output_result_var, 
                  background='lightgray', relief='sunken', padding=5).pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Help section
        help_frame = ttk.LabelFrame(main_frame, text="❓ Pomoc", padding=5)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = tk.Text(help_frame, height=12, wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True)
        help_text.insert('1.0', self.formatter.get_format_help())
        help_text.config(state='disabled')
        
        # Control buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(buttons_frame, text="💾 Zapisz Konfigurację", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="📂 Wczytaj Konfigurację", command=self.load_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="🔄 Reset", command=self.reset_config).pack(side=tk.RIGHT)
        
        # Add tooltips
        self.add_tooltips()
        
    def add_tooltips(self):
        """Dodaj tooltips z pomocą"""
        try:
            from tkinter import Hovertip
            
            Hovertip(self.input_format_entry, 
                    "Format parsowania tekstu.\nPrzykład: {name}/F{inv:2}/STR{str:2}\n" +
                    "Zmienne: {name}, {inv}, {str}, {mppt}, {sub}\n" +
                    "Formatowanie: {inv:2} = zero-padding do 2 cyfr")
            
            Hovertip(self.output_format_entry,
                    "Format generowania SVG ID.\nPrzykład: S{mppt:2}-{str:2}/{inv:2}\n" +
                    "Wynik: S10-19/06")
                    
        except ImportError:
            # Hovertip nie dostępny w starszych wersjach Python
            pass
    
    def test_parsing(self):
        """Test parsowania input formatu"""
        try:
            input_format = self.input_format_var.get()
            test_text = self.test_input_var.get()
            
            if not input_format or not test_text:
                messagebox.showwarning("Uwaga", "Wypełnij format input i tekst testowy")
                return
            
            # Parsuj tekst
            variables = self.formatter.parse_input_format(test_text, input_format)
            
            if variables:
                result = "✅ Parsowanie udane!\n"
                for var_name, value in variables.items():
                    result += f"{var_name}: {value} ({type(value).__name__})\n"
            else:
                result = "❌ Parsowanie nieudane - tekst nie pasuje do formatu"
            
            self.parsed_vars_text.delete('1.0', tk.END)
            self.parsed_vars_text.insert('1.0', result)
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd parsowania: {e}")
    
    def add_variable(self):
        """Dodaj dodatkową zmienną"""
        var_name = self.new_var_name.get().strip()
        var_expr = self.new_var_expr.get().strip()
        
        if not var_name or not var_expr:
            messagebox.showwarning("Uwaga", "Wypełnij nazwę zmiennej i wyrażenie")
            return
        
        # Sprawdź czy zmienna już istnieje
        if var_name in self.additional_vars:
            if not messagebox.askyesno("Zastąpić?", f"Zmienna '{var_name}' już istnieje. Zastąpić?"):
                return
        
        self.additional_vars[var_name] = var_expr
        self.update_vars_list()
        
        # Wyczyść pola
        self.new_var_name.set("")
        self.new_var_expr.set("")
    
    def remove_variable(self):
        """Usuń wybraną zmienną"""
        selection = self.vars_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uwaga", "Wybierz zmienną do usunięcia")
            return
        
        index = selection[0]
        var_names = list(self.additional_vars.keys())
        if index < len(var_names):
            var_name = var_names[index]
            del self.additional_vars[var_name]
            self.update_vars_list()
    
    def update_vars_list(self):
        """Aktualizuj listę dodatkowych zmiennych"""
        self.vars_listbox.delete(0, tk.END)
        for var_name, expression in self.additional_vars.items():
            self.vars_listbox.insert(tk.END, f"{var_name} = {expression}")
    
    def test_variables(self):
        """Test obliczania dodatkowych zmiennych"""
        try:
            # Najpierw sparsuj input
            input_format = self.input_format_var.get()
            test_text = self.test_input_var.get()
            
            variables = self.formatter.parse_input_format(test_text, input_format)
            if not variables:
                messagebox.showerror("Błąd", "Najpierw przetestuj parsowanie input")
                return
            
            # Oblicz dodatkowe zmienne
            result = "📊 Obliczone dodatkowe zmienne:\n"
            for var_name, expression in self.additional_vars.items():
                try:
                    value = self.formatter._evaluate_expression(expression, variables)
                    result += f"{var_name} = {expression} = {value}\n"
                except Exception as e:
                    result += f"{var_name} = {expression} = BŁĄD: {e}\n"
            
            messagebox.showinfo("Test Zmiennych", result)
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd testowania zmiennych: {e}")
    
    def test_output(self):
        """Test formatowania output"""
        try:
            # Zbierz wszystkie dane
            input_format = self.input_format_var.get()
            test_text = self.test_input_var.get()
            output_format = self.output_format_var.get()
            
            if not all([input_format, test_text, output_format]):
                messagebox.showwarning("Uwaga", "Wypełnij wszystkie pola")
                return
            
            # Parsuj input
            variables = parse_text_with_advanced_format(test_text, input_format, self.additional_vars)
            
            if not variables:
                messagebox.showerror("Błąd", "Nie udało się sparsować tekstu")
                return
            
            # Formatuj output
            result = format_output_with_advanced_format(variables, output_format)
            
            self.output_result_var.set(f"✅ {result}")
            
            # Pokaż szczegóły
            details = f"📄 Szczegóły konwersji:\n\nTekst input: {test_text}\n"
            details += f"Format input: {input_format}\n\n"
            details += "Sparsowane zmienne:\n"
            for var, val in variables.items():
                details += f"  {var}: {val}\n"
            details += f"\nFormat output: {output_format}\n"
            details += f"Wynik: {result}"
            
            messagebox.showinfo("Test Output", details)
            
        except Exception as e:
            self.output_result_var.set(f"❌ Błąd: {e}")
            messagebox.showerror("Błąd", f"Błąd formatowania output: {e}")
    
    def save_config(self):
        """Zapisz konfigurację do pliku"""
        try:
            from tkinter import filedialog
            import json
            
            filename = filedialog.asksaveasfilename(
                title="Zapisz konfigurację formatera",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                config = {
                    'input_format': self.input_format_var.get(),
                    'output_format': self.output_format_var.get(),
                    'additional_variables': self.additional_vars,
                    'test_input': self.test_input_var.get()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Sukces", f"Konfiguracja zapisana do {filename}")
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać konfiguracji: {e}")
    
    def load_config(self):
        """Wczytaj konfigurację z pliku"""
        try:
            from tkinter import filedialog
            import json
            
            filename = filedialog.askopenfilename(
                title="Wczytaj konfigurację formatera",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.input_format_var.set(config.get('input_format', ''))
                self.output_format_var.set(config.get('output_format', ''))
                self.additional_vars = config.get('additional_variables', {})
                self.test_input_var.set(config.get('test_input', ''))
                
                self.update_vars_list()
                messagebox.showinfo("Sukces", f"Konfiguracja wczytana z {filename}")
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać konfiguracji: {e}")
    
    def reset_config(self):
        """Reset konfiguracji do domyślnych wartości"""
        if messagebox.askyesno("Reset", "Czy na pewno chcesz zresetować konfigurację?"):
            self.input_format_var.set("{name}/F{inv:2}/STR{str:2}")
            self.output_format_var.set("S{mppt:2}-{str:2}/{inv:2}")
            self.test_input_var.set("STM2/F06/STR19")
            self.additional_vars = {"mppt": "{str}/2 + {str}%2"}
            self.update_vars_list()
            self.output_result_var.set("Wynik pojawi się tutaj...")
    
    def get_config(self) -> Dict[str, Any]:
        """Zwróć aktualną konfigurację"""
        return {
            'input_format': self.input_format_var.get(),
            'output_format': self.output_format_var.get(),
            'additional_variables': self.additional_vars.copy()
        }


def show_advanced_formatter_window():
    """Pokaż okno konfiguracji zaawansowanego formatera"""
    root = tk.Toplevel()
    root.title("🔧 Zaawansowany Formatter Tekstów")
    root.geometry("800x700")
    root.resizable(True, True)
    
    # Dodaj przycisk zamknij i obsługę zamykania
    def on_closing():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    formatter_gui = AdvancedFormatterGUI(root)
    
    # Dodaj przycisk zamknij na dole
    close_frame = ttk.Frame(root)
    close_frame.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Button(close_frame, text="❌ Zamknij", command=on_closing).pack(side=tk.RIGHT)
    
    # Ustaw przykładową konfigurację
    formatter_gui.additional_vars = {"mppt": "{str}/2 + {str}%2"}
    formatter_gui.update_vars_list()
    
    return formatter_gui


if __name__ == "__main__":
    # Test standalone
    root = tk.Tk()
    root.withdraw()
    
    formatter_gui = show_advanced_formatter_window()
    root.mainloop()
