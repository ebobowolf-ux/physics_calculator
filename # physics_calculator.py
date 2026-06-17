import tkinter as tk
from tkinter import ttk, scrolledtext
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime
import os

class PhysicalQuantity(ABC):
    def __init__(self, name: str, value: float = 0.0, unit: str = ""):
        self.name = name
        self.value = value
        self.unit = unit
        self._conversion_factors = {}
    
    @abstractmethod
    def calculate(self, **kwargs) -> float:
        pass
    
    def convert_to(self, target_unit: str) -> float:
        if target_unit not in self._conversion_factors:
            raise ValueError(f"Неизвестная единица: {target_unit}")
        return self.value * self._conversion_factors[target_unit]

class Speed(PhysicalQuantity):
    def __init__(self):
        super().__init__("Скорость", unit="м/с")
        self._conversion_factors = {
            "м/с": 1.0, "км/ч": 3.6, "м/мин": 60.0, "км/мин": 0.06
        }
    
    def calculate(self, s: float = None, t: float = None) -> float:
        if s is None or t is None:
            raise ValueError("Нужны путь и время")
        if t == 0:
            raise ZeroDivisionError("Время не может быть нулевым")
        self.value = np.divide(s, t)
        return self.value

class Work(PhysicalQuantity):
    def __init__(self):
        super().__init__("Работа", unit="Дж")
        self._conversion_factors = {
            "Дж": 1.0, "кДж": 0.001, "ккал": 0.0002388459, "эВ": 6.242e18
        }
    
    def calculate(self, F: float = None, d: float = None) -> float:
        if F is None or d is None:
            raise ValueError("Нужны сила и расстояние")
        self.value = np.multiply(F, d)
        return self.value

class Acceleration(PhysicalQuantity):
    def __init__(self):
        super().__init__("Ускорение", unit="м/с²")
        self._conversion_factors = {
            "м/с²": 1.0, "км/ч²": 12960.0, "g": 0.1019716
        }
    
    def calculate(self, v: float = None, v0: float = 0, t: float = None) -> float:
        if v is None or t is None:
            raise ValueError("Нужны конечная скорость и время")
        if t == 0:
            raise ZeroDivisionError("Время не может быть нулевым")
        self.value = np.divide(np.subtract(v, v0), t)
        return self.value

class CalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор физических величин")
        self.root.geometry("800x650")
        self.root.configure(bg='#2b2b2b')
        
        self.history = []
        self.current_model = None
        self.history_file = "history.csv"
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#2b2b2b', foreground='white', font=('Arial', 10))
        style.configure('TButton', background='#4a6fa5', foreground='white', font=('Arial', 10, 'bold'))
        style.map('TButton', background=[('active', '#5a7fb5')])
        style.configure('TEntry', fieldbackground='#3c3c3c', foreground='white')
        style.configure('TCombobox', fieldbackground='#3c3c3c', foreground='white')
        
        self.create_widgets()
        self.load_history()
    
    def create_widgets(self):
        title = tk.Label(self.root, text="Калькулятор физических величин", 
                         font=('Arial', 16, 'bold'), fg='#4a6fa5', bg='#2b2b2b')
        title.pack(pady=10)
        
        frame_top = tk.Frame(self.root, bg='#2b2b2b')
        frame_top.pack(pady=5)
        
        tk.Label(frame_top, text="Величина:", font=('Arial', 10), fg='white', bg='#2b2b2b').pack(side=tk.LEFT, padx=5)
        
        self.quantity_var = tk.StringVar(value="Скорость (v = s/t)")
        self.quantity_combo = ttk.Combobox(frame_top, textvariable=self.quantity_var, 
                                           values=["Скорость (v = s/t)", "Работа (A = F*s)", "Ускорение (a = dv/t)"],
                                           width=25, state='readonly')
        self.quantity_combo.pack(side=tk.LEFT, padx=5)
        self.quantity_combo.bind('<<ComboboxSelected>>', self.on_quantity_changed)
        
        self.frame_params = tk.LabelFrame(self.root, text="Параметры", font=('Arial', 10, 'bold'),
                                         fg='white', bg='#2b2b2b', bd=2)
        self.frame_params.pack(pady=10, padx=20, fill='x')
        
        self.entries = {}
        self.labels = {}
        
        self.labels['s'] = tk.Label(self.frame_params, text="Путь (м):", fg='white', bg='#2b2b2b')
        self.entries['s'] = ttk.Entry(self.frame_params, width=15)
        self.labels['t'] = tk.Label(self.frame_params, text="Время (с):", fg='white', bg='#2b2b2b')
        self.entries['t'] = ttk.Entry(self.frame_params, width=15)
        
        self.labels['F'] = tk.Label(self.frame_params, text="Сила (Н):", fg='white', bg='#2b2b2b')
        self.entries['F'] = ttk.Entry(self.frame_params, width=15)
        self.labels['d'] = tk.Label(self.frame_params, text="Расстояние (м):", fg='white', bg='#2b2b2b')
        self.entries['d'] = ttk.Entry(self.frame_params, width=15)
        
        self.labels['v'] = tk.Label(self.frame_params, text="Конечная скорость (м/с):", fg='white', bg='#2b2b2b')
        self.entries['v'] = ttk.Entry(self.frame_params, width=15)
        self.labels['v0'] = tk.Label(self.frame_params, text="Начальная скорость (м/с):", fg='white', bg='#2b2b2b')
        self.entries['v0'] = ttk.Entry(self.frame_params, width=15)
        self.entries['v0'].insert(0, "0")
        
        self.labels['s'].grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.entries['s'].grid(row=0, column=1, padx=5, pady=5)
        self.labels['t'].grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.entries['t'].grid(row=0, column=3, padx=5, pady=5)
        
        for key in ['F', 'd', 'v', 'v0']:
            self.labels[key].grid_remove()
            self.entries[key].grid_remove()
        
        frame_buttons = tk.Frame(self.root, bg='#2b2b2b')
        frame_buttons.pack(pady=10)
        
        tk.Label(frame_buttons, text="Конвертировать в:", fg='white', bg='#2b2b2b').pack(side=tk.LEFT, padx=5)
        
        self.conv_var = tk.StringVar(value="км/ч")
        self.conv_combo = ttk.Combobox(frame_buttons, textvariable=self.conv_var,
                                       values=["км/ч", "м/мин", "км/мин"], width=10, state='readonly')
        self.conv_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_buttons, text="Вычислить", command=self.on_calculate).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_buttons, text="Конвертировать", command=self.on_convert).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_buttons, text="Очистить", command=self.on_clear).pack(side=tk.LEFT, padx=5)
        
        self.result_label = tk.Label(self.root, text="Результат: ---", font=('Arial', 12, 'bold'),
                                    fg='#6abf6a', bg='#1e1e1e', relief='sunken', padx=10, pady=10)
        self.result_label.pack(pady=10, padx=20, fill='x')
        
        frame_history = tk.LabelFrame(self.root, text="История расчётов", font=('Arial', 10, 'bold'),
                                     fg='white', bg='#2b2b2b', bd=2)
        frame_history.pack(pady=10, padx=20, fill='both', expand=True)
        
        self.history_text = scrolledtext.ScrolledText(frame_history, height=6, bg='#1e1e1e', fg='#d4d4d4',
                                                     font=('Courier New', 9))
        self.history_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        frame_history_buttons = tk.Frame(frame_history, bg='#2b2b2b')
        frame_history_buttons.pack(pady=5)
        
        ttk.Button(frame_history_buttons, text="Сохранить историю", command=self.save_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_history_buttons, text="Очистить историю", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(self.root, text="Готов", fg='#aaa', bg='#1e1e1e', relief='sunken')
        self.status_label.pack(fill='x', side=tk.BOTTOM)
    
    def on_quantity_changed(self, event=None):
        for key in self.labels:
            self.labels[key].grid_remove()
            self.entries[key].grid_remove()
        
        index = self.quantity_combo.current()
        
        if index == 0:
            self.labels['s'].grid(row=0, column=0, padx=5, pady=5, sticky='e')
            self.entries['s'].grid(row=0, column=1, padx=5, pady=5)
            self.labels['t'].grid(row=0, column=2, padx=5, pady=5, sticky='e')
            self.entries['t'].grid(row=0, column=3, padx=5, pady=5)
            self.conv_combo['values'] = ["км/ч", "м/мин", "км/мин"]
            self.conv_var.set("км/ч")
        elif index == 1:
            self.labels['F'].grid(row=0, column=0, padx=5, pady=5, sticky='e')
            self.entries['F'].grid(row=0, column=1, padx=5, pady=5)
            self.labels['d'].grid(row=0, column=2, padx=5, pady=5, sticky='e')
            self.entries['d'].grid(row=0, column=3, padx=5, pady=5)
            self.conv_combo['values'] = ["кДж", "ккал", "эВ"]
            self.conv_var.set("кДж")
        else:
            self.labels['v'].grid(row=0, column=0, padx=5, pady=5, sticky='e')
            self.entries['v'].grid(row=0, column=1, padx=5, pady=5)
            self.labels['v0'].grid(row=0, column=2, padx=5, pady=5, sticky='e')
            self.entries['v0'].grid(row=0, column=3, padx=5, pady=5)
            self.labels['t'].grid(row=1, column=0, padx=5, pady=5, sticky='e')
            self.entries['t'].grid(row=1, column=1, padx=5, pady=5)
            self.conv_combo['values'] = ["км/ч²", "g"]
            self.conv_var.set("км/ч²")
        
        self.result_label.config(text="Результат: ---")
        self.status_label.config(text="Выберите параметры")
    
    def on_calculate(self):
        try:
            index = self.quantity_combo.current()
            
            if index == 0:
                s = float(self.entries['s'].get())
                t = float(self.entries['t'].get())
                model = Speed()
                model.calculate(s=s, t=t)
            elif index == 1:
                F = float(self.entries['F'].get())
                d = float(self.entries['d'].get())
                model = Work()
                model.calculate(F=F, d=d)
            else:
                v = float(self.entries['v'].get())
                v0 = float(self.entries['v0'].get() or 0)
                t = float(self.entries['t'].get())
                model = Acceleration()
                model.calculate(v=v, v0=v0, t=t)
            
            self.current_model = model
            self.result_label.config(text=f"Результат: {model.value:.6f} {model.unit}")
            self.result_label.config(fg='#6abf6a')
            
            entry = f"{datetime.now().strftime('%H:%M:%S')} | {model.name}: {model.value:.4f} {model.unit}"
            self.history.append(entry)
            self.update_history_display()
            
            self.status_label.config(text=f"Вычислено: {model.value:.4f} {model.unit}")
            
        except ValueError:
            self.result_label.config(text="Ошибка: введите числовые значения", fg='#ff6b6b')
            self.status_label.config(text="Ошибка ввода")
        except ZeroDivisionError as e:
            self.result_label.config(text=f"Ошибка: {str(e)}", fg='#ff6b6b')
        except Exception as e:
            self.result_label.config(text=f"Ошибка: {str(e)}", fg='#ff6b6b')
    
    def on_convert(self):
        if self.current_model is None:
            self.status_label.config(text="Сначала выполните вычисление")
            return
        try:
            target = self.conv_var.get()
            converted = self.current_model.convert_to(target)
            self.result_label.config(
                text=f"{self.current_model.value:.6f} {self.current_model.unit} = {converted:.6f} {target}"
            )
            self.result_label.config(fg='#6abf6a')
            self.status_label.config(text=f"Конвертировано в {target}")
        except Exception as e:
            self.status_label.config(text=f"Ошибка: {str(e)}")
    
    def on_clear(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.entries['v0'].insert(0, "0")
        self.result_label.config(text="Результат: ---", fg='#6abf6a')
        self.current_model = None
        self.status_label.config(text="Поля очищены")
    
    def update_history_display(self):
        self.history_text.delete(1.0, tk.END)
        self.history_text.insert(1.0, "\n".join(self.history[-20:]))
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                f.write("Время,Действие\n")
                for entry in self.history:
                    parts = entry.split(" | ", 1)
                    if len(parts) == 2:
                        f.write(f"{parts[0]},{parts[1]}\n")
            self.status_label.config(text=f"История сохранена в {self.history_file}")
        except Exception as e:
            self.status_label.config(text=f"Ошибка сохранения: {str(e)}")
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[1:]
                    for line in lines:
                        parts = line.strip().split(",", 1)
                        if len(parts) == 2:
                            self.history.append(f"{parts[0]} | {parts[1]}")
                self.update_history_display()
                self.status_label.config(text=f"Загружено {len(self.history)} записей")
        except:
            pass
    
    def clear_history(self):
        self.history.clear()
        self.history_text.delete(1.0, tk.END)
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        self.status_label.config(text="История очищена")

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorGUI(root)
    root.mainloop()