# map_editor.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import math
from gui_menu import CatanCalculationMenu

# Цвета ресурсов
RESOURCE_COLORS = {
    "mountains": "#808080",
    "hills": "#8B4513",
    "forest": "#228B22",
    "pasture": "#90EE90",
    "fields": "#FFD700",
    "desert": "#FFFACD"
}

HEX_COORDS = [
    # Центральный ромб (1-е "кольцо", 4 гекса)
    (0, 0), (1, 0), (0, 1), (-1, 1),

    (-1, 0), (1, 1), (2, 0), (2,-1), (0, -1), (0, 2), (1, -1), (-1, 2), (-2, 1), (-2, 2),

    (3, 0), (2, 1), (1, 2), (0, 3), (-1, 3), (-2, 3), (-3, 3), (-3, 2), (-3, 1), (-2, 0), (-1, -1), (0, -2), (1, -2), (2, -2), (3, -2), (3, -1)  
]
HEX_COORDS = list(set(HEX_COORDS))  # Уникальные

RESOURCES = ["mountains", "fields", "hills", "pasture", "forest", "desert"]
NUMBERS = [2, 3, 4, 5, 6, 8, 9, 10, 11, 12]

class CatanMapEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Catan — твоя система координат")
        self.hex_data = {}
        self.hex_items = {}

        # Параметры отрисовки
        self.HEX_SIZE = 45
        self.CANVAS_WIDTH = 600
        self.CANVAS_HEIGHT = 600
        self.OFFSET_X = 300
        self.OFFSET_Y = 300

        self.canvas = tk.Canvas(root, width=self.CANVAS_WIDTH, height=self.CANVAS_HEIGHT, bg="lightblue")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        control_frame = tk.Frame(root, width=200, padx=10, pady=10)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(control_frame, text="Редактор по твоей сетке", font=("Arial", 12, "bold")).pack(pady=(0, 15))

        self.export_btn = tk.Button(control_frame, text="Начать расчет", command=self.start_calculation, height=2)
        self.export_btn.pack(pady=5, fill=tk.X)

        self.clear_btn = tk.Button(control_frame, text="Очистить всё", command=self.clear_all, height=2)
        self.clear_btn.pack(pady=5, fill=tk.X)

        self.draw_hexes()
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def coord_to_pixel(self, x, y):
        """Переводит (x, y) в пиксельные координаты (flat-top)"""
        q, r = x, y
        size = self.HEX_SIZE
        cx = size * 1.5 * q
        cy = size * math.sqrt(3) * (r + q / 2)
        return cx + self.OFFSET_X, cy + self.OFFSET_Y

    def hexagon_points(self, cx, cy, size):
        """Точки шестиугольника с плоской стороной сверху"""
        points = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.radians(angle_deg)
            px = cx + size * math.cos(angle_rad)
            py = cy + size * math.sin(angle_rad)
            points.extend([px, py])
        return points

    def point_in_polygon(self, x, y, poly):
        n = len(poly) // 2
        inside = False
        p1x, p1y = poly[0], poly[1]
        for i in range(1, n + 1):
            p2x, p2y = poly[(i % n) * 2], poly[(i % n) * 2 + 1]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def draw_hexes(self):
        for (x, y) in HEX_COORDS:
            cx, cy = self.coord_to_pixel(x, y)
            points = self.hexagon_points(cx, cy, self.HEX_SIZE)
            poly_id = self.canvas.create_polygon(points, outline="black", fill="white", width=2)
            text_id = self.canvas.create_text(cx, cy, text="", font=("Arial", 10, "bold"))
            self.hex_items[(x, y)] = (poly_id, text_id)

    def on_canvas_click(self, event):
        clicked_hex = None
        for (x, y), (poly_id, _) in self.hex_items.items():
            if self.point_in_polygon(event.x, event.y, self.canvas.coords(poly_id)):
                clicked_hex = (x, y)
                break
        if clicked_hex:
            self.open_edit_dialog(clicked_hex)

    def open_edit_dialog(self, coord):
        x, y = coord
        current = self.hex_data.get((x, y), {"resource": "desert", "number": 7})

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Гекс {x},{y}")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Ресурс:").pack(pady=(10, 0))
        resource_var = tk.StringVar(value=current["resource"])
        resource_combo = ttk.Combobox(dialog, textvariable=resource_var, values=RESOURCES, state="readonly")
        resource_combo.pack()

        tk.Label(dialog, text="Число:").pack(pady=(10, 0))
        number_var = tk.StringVar(value=str(current["number"]))
        number_combo = ttk.Combobox(dialog, textvariable=number_var, state="readonly")
        number_combo.pack()

        def update_numbers(*args):
            res = resource_var.get()
            if res == "desert":
                number_combo.config(values=[7])
                number_var.set("7")
            else:
                number_combo.config(values=[str(n) for n in NUMBERS])
                if number_var.get() not in [str(n) for n in NUMBERS]:
                    number_var.set(str(NUMBERS[0]))
        resource_var.trace("w", update_numbers)
        update_numbers()

        def save():
            try:
                number = int(number_var.get())
                resource = resource_var.get()
                self.hex_data[(x, y)] = {"resource": resource, "number": number}
                poly_id, text_id = self.hex_items[(x, y)]
                color = RESOURCE_COLORS.get(resource, "white")
                self.canvas.itemconfig(poly_id, fill=color)
                self.canvas.itemconfig(text_id, text=str(number))
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверные данные: {e}")

        tk.Button(dialog, text="Сохранить", command=save, width=15).pack(pady=15)

    def export_json(self):
        if not self.hex_data:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта!")
            return

        # Формируем данные
        output = {
            "hexes": {
                f"{x},{y}": {"resource": data["resource"], "number": data["number"]}
                for (x, y), data in self.hex_data.items()
            }
        }

        try:
            # Сохраняем в файл map_data.json в текущей директории
            with open("test_map_data.json", "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Успех", "Карта успешно сохранена в файл:\nmap_data.json")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def start_calculation(self):
        # Сохраняем карту
        self.export_json()

        # Запускаем GUI-меню расчёта
        try:
            CatanCalculationMenu(self.root)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить расчёт:\n{e}")

    def clear_all(self):
        if messagebox.askyesno("Очистка", "Удалить все данные с карты?"):
            self.hex_data.clear()
            for (x, y), (poly_id, text_id) in self.hex_items.items():
                self.canvas.itemconfig(poly_id, fill="white")
                self.canvas.itemconfig(text_id, text="")

# Функция для запуска редактора извне
def open_map_editor():
    root = tk.Tk()
    app = CatanMapEditor(root)
    root.mainloop()