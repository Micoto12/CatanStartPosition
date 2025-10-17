# gui_menu.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging

from data_io.load_map import load_map_from_json
from data_io.load_structure import load_structure
from core.search import (
    find_best_single_placement,
    find_best_start,
    find_best_city_given_my_settlement,
    calculate_resource_rarity
)
from utils.helpers import build_hex_id_to_data
import config

class CatanCalculationMenu:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Расчёт стартовой позиции")
        self.window.geometry("700x600")

        # Загружаем данные
        try:
            self.map_data = load_map_from_json("map_data.json")
            self.structure = load_structure("structure.json")
            self.hex_id_to_data = build_hex_id_to_data(self.map_data, self.structure)
            self.occupied_vertices = set()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")
            self.window.destroy()
            return

        self.create_widgets()

    def create_widgets(self):
        # Верхняя панель: управление
        control_frame = tk.Frame(self.window)
        control_frame.pack(pady=10, padx=10, fill=tk.X)

        # Занятые вершины
        tk.Label(control_frame, text="Занятые вершины (через запятую):").grid(row=0, column=0, sticky=tk.W)
        self.occupied_entry = tk.Entry(control_frame, width=40)
        self.occupied_entry.grid(row=0, column=1, padx=5)
        tk.Button(control_frame, text="Применить", command=self.set_occupied).grid(row=0, column=2)

        # Текущие занятые
        self.occupied_label = tk.Label(control_frame, text="Текущие: нет", fg="gray")
        self.occupied_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Тип расчёта
        tk.Label(control_frame, text="Тип расчёта:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.calc_type = tk.StringVar(value="settlement")
        ttk.Radiobutton(control_frame, text="Поселение", variable=self.calc_type, value="settlement").grid(row=3, column=0, sticky=tk.W)
        ttk.Radiobutton(control_frame, text="Город", variable=self.calc_type, value="city").grid(row=3, column=1, sticky=tk.W)
        ttk.Radiobutton(control_frame, text="Пара (город+поселение)", variable=self.calc_type, value="pair").grid(row=4, column=0, sticky=tk.W)
        ttk.Radiobutton(control_frame, text="Город с моим поселением", variable=self.calc_type, value="city_with_my").grid(row=4, column=1, sticky=tk.W)

        # Поле для ID своего поселения (появляется при выборе)
        self.my_settlement_label = tk.Label(control_frame, text="Ваша вершина:")
        self.my_settlement_entry = tk.Entry(control_frame, width=10)

        # Кнопка расчёта
        tk.Button(control_frame, text="Рассчитать", command=self.run_calculation, bg="#4CAF50", fg="white").grid(row=5, column=0, pady=10, columnspan=3)

        # Результат
        self.result_text = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, width=80, height=20)
        self.result_text.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)

        # Обработка изменения типа расчёта
        self.calc_type.trace("w", self.toggle_my_settlement_input)

    def toggle_my_settlement_input(self, *args):
        if self.calc_type.get() == "city_with_my":
            self.my_settlement_label.grid(row=4, column=2, padx=(10, 0))
            self.my_settlement_entry.grid(row=4, column=3)
        else:
            self.my_settlement_label.grid_forget()
            self.my_settlement_entry.grid_forget()

    def set_occupied(self):
        user_input = self.occupied_entry.get().strip()
        if not user_input:
            self.occupied_vertices = set()
            self.occupied_label.config(text="Текущие: нет")
            return

        try:
            self.occupied_vertices = {int(x.strip()) for x in user_input.split(",")}
            self.occupied_label.config(text=f"Текущие: {sorted(self.occupied_vertices)}")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите числа через запятую (например: 12,45,67)")

    def run_calculation(self):
        calc_type = self.calc_type.get()
        self.result_text.delete(1.0, tk.END)

        try:
            if calc_type == "settlement":
                best = find_best_single_placement(self.structure, self.hex_id_to_data, self.occupied_vertices, is_city=False)
                self.show_single_result(best, "поселение")

            elif calc_type == "city":
                best = find_best_single_placement(self.structure, self.hex_id_to_data, self.occupied_vertices, is_city=True)
                self.show_single_result(best, "город")

            elif calc_type == "pair":
                best_pair = find_best_start(self.structure, self.hex_id_to_data, self.occupied_vertices)
                self.show_pair_result(best_pair)

            elif calc_type == "city_with_my":
                if not self.occupied_vertices:
                    messagebox.showwarning("Предупреждение", "Сначала укажите чужие занятые вершины.")
                    return
                try:
                    my_id = int(self.my_settlement_entry.get().strip())
                except ValueError:
                    messagebox.showerror("Ошибка", "Введите корректный ID вашей вершины.")
                    return
                if my_id in self.occupied_vertices:
                    messagebox.showwarning("Предупреждение", "Ваша вершина не должна быть в списке чужих.")
                    return
                best = find_best_city_given_my_settlement(
                    self.structure, self.hex_id_to_data, self.occupied_vertices, my_id
                )
                self.show_city_with_my_result(best, my_id)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Расчёт завершился с ошибкой:\n{e}")
            if config.DEBUG:
                import traceback
                self.result_text.insert(tk.END, traceback.format_exc())

    def show_single_result(self, best, obj_name):
        if not best:
            self.result_text.insert(tk.END, f"❌ Нет доступных мест для {obj_name}а.\n")
            return

        self.result_text.insert(tk.END, f"✅ Лучшее место для {obj_name}:\n")
        self.result_text.insert(tk.END, f"Вершина: {best['top_id']}\n")
        self.result_text.insert(tk.END, f"Ресурсы: {best['resources']}\n")
        self.result_text.insert(tk.END, f"Числа: {best['numbers']}\n")
        self.result_text.insert(tk.END, f"Оценка: {best['total']:.1f}\n\n")

        self.show_resource_rarity()

    def show_pair_result(self, best_pair):
        if not best_pair:
            self.result_text.insert(tk.END, "❌ Нет допустимых пар.\n")
            return

        self.result_text.insert(tk.END, "✅ Лучшая пара:\n")
        self.result_text.insert(tk.END, f"Город: {best_pair['city']['top_id']} | {best_pair['city']['resources']} | {best_pair['city']['numbers']}\n")
        self.result_text.insert(tk.END, f"Поселение: {best_pair['settlement']['top_id']} | {best_pair['settlement']['resources']} | {best_pair['settlement']['numbers']}\n")
        missing = best_pair.get("missing_resources", [])
        if missing:
            self.result_text.insert(tk.END, f"⚠️ Отсутствуют ресурсы: {missing}\n")
        else:
            self.result_text.insert(tk.END, "✅ Все 5 ресурсов!\n")
        self.result_text.insert(tk.END, f"Итог: {best_pair['total']:.1f}\n\n")
        self.show_resource_rarity()

    def show_city_with_my_result(self, best, my_id):
        if not best:
            self.result_text.insert(tk.END, "❌ Нет доступных мест для города.\n")
            return

        self.result_text.insert(tk.END, "✅ Лучшее место для города с учётом вашего поселения:\n")
        self.result_text.insert(tk.END, f"Ваше поселение: {best['settlement']['top_id']} | {best['settlement']['resources']} | {best['settlement']['numbers']}\n")
        self.result_text.insert(tk.END, f"Город: {best['city']['top_id']} | {best['city']['resources']} | {best['city']['numbers']}\n")
        missing = best.get("missing_resources", [])
        if missing:
            self.result_text.insert(tk.END, f"⚠️ Отсутствуют ресурсы: {missing}\n")
        else:
            self.result_text.insert(tk.END, "✅ Все 5 ресурсов!\n")
        self.result_text.insert(tk.END, f"Оценка: {best['total']:.1f}\n\n")
        self.show_resource_rarity()

    def show_resource_rarity(self):
        resource_total, _ = calculate_resource_rarity(self.structure, self.hex_id_to_data)
        self.result_text.insert(tk.END, "\n📊 Дефицит ресурсов (чем меньше — тем ценнее):\n")
        for res, total in sorted(resource_total.items(), key=lambda x: x[1]):
            self.result_text.insert(tk.END, f"  {res}: {total}\n")