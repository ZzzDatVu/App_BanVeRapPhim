import customtkinter as ctk


DEFAULT_SNACKS = [
    {"id": "SN01", "name": "Bắp rang bơ (Lớn)", "price": 55000},
    {"id": "SN02", "name": "Bắp phô mai (Vừa)", "price": 49000},
    {"id": "SN03", "name": "Pepsi tươi (Lớn)", "price": 35000},
    {"id": "SN04", "name": "Combo Đôi (1 Bắp + 2 Nước)", "price": 99000},
]


class SnacksView(ctk.CTkToplevel):
    def __init__(self, parent, initial_quantities=None, on_confirm=None, on_back=None):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.on_back = on_back
        self.quantities = {
            item["id"]: int((initial_quantities or {}).get(item["id"], 0))
            for item in DEFAULT_SNACKS
        }
        self.qty_labels = {}

        self.title("Chọn bắp nước")
        self.geometry("540x430")
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="MENU BẮP NƯỚC",
            font=("Arial", 20, "bold"),
        ).pack(pady=(18, 12))

        container = ctk.CTkScrollableFrame(self, width=480, height=230)
        container.pack(padx=25, pady=5, fill="both", expand=True)

        for item in DEFAULT_SNACKS:
            row = ctk.CTkFrame(container)
            row.pack(fill="x", padx=8, pady=6)

            info = f"{item['name']}  —  {item['price']:,}đ".replace(",", ".")
            ctk.CTkLabel(
                row,
                text=info,
                font=("Arial", 14),
            ).pack(side="left", padx=12, pady=10)

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=10)

            ctk.CTkButton(
                right,
                text="-",
                width=32,
                height=30,
                font=("Arial", 15, "bold"),
                command=lambda sid=item["id"]: self.change_qty(sid, -1),
            ).pack(side="left", padx=4)

            lbl = ctk.CTkLabel(
                right,
                text=str(self.quantities[item["id"]]),
                width=28,
                font=("Arial", 14, "bold"),
            )
            lbl.pack(side="left", padx=4)
            self.qty_labels[item["id"]] = lbl

            ctk.CTkButton(
                right,
                text="+",
                width=32,
                height=30,
                font=("Arial", 15, "bold"),
                command=lambda sid=item["id"]: self.change_qty(sid, 1),
            ).pack(side="left", padx=4)

        self.total_label = ctk.CTkLabel(
            self,
            text="Tiền bắp nước: 0đ",
            font=("Arial", 15, "bold"),
            text_color="#22c55e",
        )
        self.total_label.pack(pady=(10, 6))
        self.refresh_total()

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(pady=(4, 16))

        ctk.CTkButton(
            action_row,
            text="← Trở về",
            width=120,
            height=38,
            font=("Arial", 13, "bold"),
            fg_color="#475569",
            hover_color="#334155",
            command=self.go_back,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            action_row,
            text="Xác nhận bắp nước",
            width=185,
            height=38,
            font=("Arial", 14, "bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self.confirm,
        ).pack(side="left", padx=6)

    def change_qty(self, snack_id, delta):
        new_val = max(0, self.quantities[snack_id] + delta)
        self.quantities[snack_id] = new_val
        self.qty_labels[snack_id].configure(text=str(new_val))
        self.refresh_total()

    def calc_total(self):
        total = 0
        for item in DEFAULT_SNACKS:
            total += item["price"] * self.quantities[item["id"]]
        return total

    def refresh_total(self):
        total = self.calc_total()
        formatted = f"{total:,}đ".replace(",", ".")
        self.total_label.configure(text=f"Tiền bắp nước: {formatted}")

    def go_back(self):
        callback = self.on_back
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        if callback:
            self.master.after(50, callback)

    def confirm(self):
        chosen = [
            {
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "qty": self.quantities[item["id"]],
                "subtotal": item["price"] * self.quantities[item["id"]],
            }
            for item in DEFAULT_SNACKS
            if self.quantities[item["id"]] > 0
        ]
        total = self.calc_total()
        qtys = dict(self.quantities)
        callback = self.on_confirm

        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

        if callback:
            self.master.after(50, lambda: callback(chosen, total, qtys))