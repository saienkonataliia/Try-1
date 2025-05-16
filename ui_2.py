import tkinter as tk
from tkinter import messagebox, simpledialog
from db import *
from utils import rectangles_overlap, is_within_bounds

class RoomManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Планувальник кімнат")
        self.geometry("600x400")

        self.listbox = tk.Listbox(self, width=50)
        self.listbox.pack(pady=10)

        tk.Button(self, text="Оновити", command=self.load_rooms).pack()
        tk.Button(self, text="Додати кімнату", command=self.add_room_dialog).pack()
        tk.Button(self, text="Видалити кімнату", command=self.delete_room_dialog).pack()
        tk.Button(self, text="Переглянути кімнату", command=self.view_room).pack()

        self.load_rooms()

    def load_rooms(self):
        self.listbox.delete(0, tk.END)
        for room in get_rooms():
            self.listbox.insert(tk.END, f"{room[1]} ({room[0]}): {room[2]/PIXELS_PER_METER:.2f}x{room[3]/PIXELS_PER_METER:.2f} м")

    def add_room_dialog(self):
        name = simpledialog.askstring("Назва кімнати", "Введіть назву кімнати:")
        if not name: return
        try:
            width = int(float(simpledialog.askstring("Ширина (м)", "Введіть ширину:") or 0) * PIXELS_PER_METER)
            height = int(float(simpledialog.askstring("Висота (м)", "Введіть висоту:") or 0) * PIXELS_PER_METER)
            add_room(name, width, height)
            self.load_rooms()
        except Exception:
            messagebox.showerror("Помилка", "Некоректні дані")

    def delete_room_dialog(self):
        if not self.listbox.curselection(): return
        room_id = int(self.listbox.get(self.listbox.curselection()[0]).split(" (")[1].split(")")[0])
        if messagebox.askyesno("Підтвердження", "Видалити кімнату з меблями?"):
            delete_room(room_id)
            self.load_rooms()

    def view_room(self):
        if not self.listbox.curselection(): return
        room_id = int(self.listbox.get(self.listbox.curselection()[0]).split(" (")[1].split(")")[0])
        room = get_room_by_id(room_id)
        if room:
            RoomCanvas(*room)

class RoomCanvas(tk.Toplevel):
    def __init__(self, room_id, name, width, height):
        super().__init__()
        self.title(name)
        self.room_id = room_id
        self.width = width
        self.height = height
        self.geometry(f"{width + 20}x{height + 180}")
        self.canvas = tk.Canvas(self, width=width, height=height, bg="white")
        self.canvas.pack()

        self.furniture_items = {}
        self.drag_data = {"x": 0, "y": 0, "item": None, "id": None}
        self.selected_item_id = None
        self.pending_action = None

        tk.Button(self, text="Додати меблі", command=self.add_furniture).pack()
        tk.Button(self, text="Редагувати меблі", command=lambda: self.set_pending_action("edit")).pack()
        tk.Button(self, text="Обертати меблі", command=lambda: self.set_pending_action("rotate")).pack()
        tk.Button(self, text="Видалити меблі", command=lambda: self.set_pending_action("delete")).pack()
        tk.Button(self, text="Змінити розмір кімнати", command=self.resize_room).pack()
        tk.Button(self, text="Зберегти план", command=self.save_room_view).pack()

        self.refresh()

    def refresh(self):
        self.canvas.delete("all")
        self.selected_item_id = None
        self.furniture_items.clear()
        self.canvas.create_rectangle(0, 0, self.width, self.height, outline="black")
        for item in get_furniture_by_room(self.room_id):
            x, y, w, h, angle = item[5], item[6], item[3], item[4], item[7]
            r = self.canvas.create_rectangle(x, y, x + w, y + h, fill="lightblue", outline="black", width=2)
            t = self.canvas.create_text(x + w / 2, y + h / 2, text=item[2])
            self.furniture_items[r] = {"id": item[0], "text": t, "dx": w, "dy": h, "angle": angle}
            self.canvas.tag_bind(r, "<Button-1>", self.on_select)
            self.canvas.tag_bind(r, "<ButtonPress-1>", self.on_drag_start)
            self.canvas.tag_bind(r, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(r, "<ButtonRelease-1>", self.on_drop)

    def set_pending_action(self, action):
        self.pending_action = action
        self.furniture_list = tk.Toplevel(self)
        self.furniture_list.title("Оберіть меблі")
        tk.Label(self.furniture_list, text="Оберіть меблі для операції:").pack()

        listbox = tk.Listbox(self.furniture_list)
        id_name_map = {}
        for canvas_id, data in self.furniture_items.items():
            item_id = data["id"]
            name = self.canvas.itemcget(data["text"], "text")
            id_name_map[item_id] = canvas_id
            listbox.insert(tk.END, f"{item_id}: {name}")

        listbox.pack()

        def apply():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Увага", "Не вибрано меблі")
                return
            selected_text = listbox.get(selection[0])
            selected_id = int(selected_text.split(":")[0])
            for canvas_id, data in self.furniture_items.items():
                if data["id"] == selected_id:
                    self.selected_item_id = canvas_id
                    break
            if self.pending_action == "edit":
                self.edit_furniture()
            elif self.pending_action == "rotate":
                self.rotate_furniture()
            elif self.pending_action == "delete":
                self.delete_furniture()
            self.pending_action = None
            self.furniture_list.destroy()

        tk.Button(self.furniture_list, text="Застосувати", command=apply).pack()

    def on_select(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        if item not in self.furniture_items:
            return
        self.selected_item_id = item
        self.canvas.itemconfig(item, outline="red")

        if self.pending_action == "edit":
            self.edit_furniture()
        elif self.pending_action == "rotate":
            self.rotate_furniture()
        elif self.pending_action == "delete":
            self.delete_furniture()
        self.pending_action = None

    def on_drag_start(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        self.drag_data = {"item": item, "x": event.x, "y": event.y, "id": self.furniture_items[item]["id"]}
        self.selected_item_id = item

    def on_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.canvas.move(self.drag_data["item"], dx, dy)
        self.canvas.move(self.furniture_items[self.drag_data["item"]]["text"], dx, dy)
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y

    def on_drop(self, event):
        item = self.drag_data["item"]
        if item not in self.furniture_items:
            return
        self.selected_item_id = item
        x1, y1, x2, y2 = self.canvas.coords(item)
        x = int(x1)
        y = int(y1)
        w = self.furniture_items[item]["dx"]
        h = self.furniture_items[item]["dy"]

        if not is_within_bounds(x, y, w, h, self.width, self.height):
            messagebox.showwarning("Увага", "Меблі виходять за межі кімнати")
            self.refresh()
            return

        for other_id, data in self.furniture_items.items():
            if other_id == item:
                continue
            ox1 = self.canvas.coords(other_id)[0]
            oy1 = self.canvas.coords(other_id)[1]
            ow = data["dx"]
            oh = data["dy"]
            if rectangles_overlap(x, y, w, h, ox1, oy1, ow, oh):
                messagebox.showwarning("Увага", "Меблі перетинаються з іншими")
                self.refresh()
                return

        update_furniture_position(self.drag_data["id"], x, y)
        self.refresh()

    def add_furniture(self):
        name = simpledialog.askstring("Назва меблів", "Введіть назву:")
        try:
            w = int(float(simpledialog.askstring("Ширина (м)", "Введіть ширину:") or 0) * PIXELS_PER_METER)
            h = int(float(simpledialog.askstring("Висота (м)", "Введіть висоту:") or 0) * PIXELS_PER_METER)
            x = int(float(simpledialog.askstring("X (м)", "Введіть X:") or 0) * PIXELS_PER_METER)
            y = int(float(simpledialog.askstring("Y (м)", "Введіть Y:") or 0) * PIXELS_PER_METER)
            if not is_within_bounds(x, y, w, h, self.width, self.height):
                raise ValueError("За межами кімнати")
            for other in get_furniture_by_room(self.room_id):
                if rectangles_overlap(x, y, w, h, other[5], other[6], other[3], other[4]):
                    raise ValueError("Перетин меблів")
            add_furniture(self.room_id, name, w, h, x, y)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def edit_furniture(self):
        if not self.selected_item_id or self.selected_item_id not in self.furniture_items:
            messagebox.showerror("Помилка", "Оберіть меблі")
            return
        data = self.furniture_items[self.selected_item_id]
        try:
            name = simpledialog.askstring("Назва", "Нова назва:", initialvalue=self.canvas.itemcget(data["text"], "text"))
            w = int(float(simpledialog.askstring("Ширина (м)", "Нова ширина:", initialvalue=data["dx"] / PIXELS_PER_METER)) * PIXELS_PER_METER)
            h = int(float(simpledialog.askstring("Висота (м)", "Нова висота:", initialvalue=data["dy"] / PIXELS_PER_METER)) * PIXELS_PER_METER)
            update_furniture(data["id"], name, w, h)
            self.selected_item_id = None
            self.refresh()
        except Exception:
            messagebox.showerror("Помилка", "Некоректні дані")

    def rotate_furniture(self):
        if not self.selected_item_id or self.selected_item_id not in self.furniture_items:
            messagebox.showerror("Помилка", "Оберіть меблі")
            return
        data = self.furniture_items[self.selected_item_id]
        try:
            angle = int(simpledialog.askstring("Кут", "Кут повороту (90/180/270/360):", initialvalue=data["angle"] or 0)) % 360
            if angle not in (90, 180, 270, 0):
                raise ValueError("Кут має бути 0, 90, 180 або 270")

            new_w, new_h = data["dx"], data["dy"]
            if angle in (90, 270):
                new_w, new_h = data["dy"], data["dx"]

            update_furniture_angle(data["id"], angle)
            update_furniture(data["id"], self.canvas.itemcget(data["text"], "text"), new_w, new_h)
            data["angle"] = angle
            self.selected_item_id = None
            self.refresh()
        except Exception:
            messagebox.showerror("Помилка", "Некоректні дані або кут")
        except Exception:
            messagebox.showerror("Помилка", "Некоректні дані")
        except Exception:
            messagebox.showerror("Помилка", "Некоректні дані")

    def delete_furniture(self):
        if not self.selected_item_id or self.selected_item_id not in self.furniture_items:
            messagebox.showerror("Помилка", "Оберіть меблі")
            return
        delete_furniture(self.furniture_items[self.selected_item_id]["id"])
        self.selected_item_id = None
        self.refresh()

    def save_room_view(self):
        try:
            self.canvas.postscript(file=f"room_{self.room_id}.ps")
            messagebox.showinfo("Збережено", f"Зображення кімнати збережено як room_{self.room_id}.ps")
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def resize_room(self):
        try:
            new_w = int(float(simpledialog.askstring("Ширина (м)", "Нова ширина:", initialvalue=self.width / PIXELS_PER_METER)) * PIXELS_PER_METER)
            new_h = int(float(simpledialog.askstring("Висота (м)", "Нова висота:", initialvalue=self.height / PIXELS_PER_METER)) * PIXELS_PER_METER)
            update_room(self.room_id, new_w, new_h)
            self.canvas.config(width=new_w, height=new_h)
            self.width = new_w
            self.height = new_h
            self.geometry(f"{new_w + 20}x{new_h + 180}")
            self.refresh()
        except Exception:
            messagebox.showerror("Помилка", "Некоректні дані")
