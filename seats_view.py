from tkinter import messagebox
import customtkinter as ctk
from snacks_view import SnacksView
from checkout_view import CheckoutView


class SeatsView(ctk.CTkToplevel):
    def __init__(self, parent, suat_chieu, on_saved=None):
        super().__init__(parent)
        self.suat_chieu = suat_chieu
        self.on_saved = on_saved
        self.selected_seats = set()
        self.seat_buttons = {}

        self.selected_snacks = []
        self.snack_quantities = {}
        self.snack_total = 0
        self.seats_confirmed = False

        self.title(f"Chọn ghế - {suat_chieu.phim.ten_phim} ({suat_chieu.gio_chieu})")
        self.geometry("620x540")
        self.grab_set()

        ctk.CTkLabel(
            self,
            text=f"{suat_chieu.phim.ten_phim}  |  {suat_chieu.phong.ten_phong}  |  {suat_chieu.gio_chieu}",
            font=("Arial", 16, "bold"),
        ).pack(pady=(18, 6))

        ctk.CTkLabel(
            self,
            text="▬▬▬▬ MÀN HÌNH CHIẾU ▬▬▬▬",
            font=("Arial", 13, "bold"),
            text_color="#94a3b8",
        ).pack(pady=(4, 12))

        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(pady=(0, 8))
        ctk.CTkLabel(legend, text="■ Trống", text_color="#3b82f6", font=("Arial", 12, "bold")).pack(side="left", padx=12)
        ctk.CTkLabel(legend, text="■ Đang chọn", text_color="#22c55e", font=("Arial", 12, "bold")).pack(side="left", padx=12)
        ctk.CTkLabel(legend, text="■ Đã đặt", text_color="#ef4444", font=("Arial", 12, "bold")).pack(side="left", padx=12)

        grid_frame = ctk.CTkFrame(self)
        grid_frame.pack(pady=6, padx=20)

        seats = suat_chieu.phong.lay_danh_sach_ghe_hop_le()
        cols = suat_chieu.phong.so_cot

        for idx, code in enumerate(seats):
            row = idx // cols
            col = idx % cols
            booked = code in suat_chieu.ds_ghe_dadat

            btn = ctk.CTkButton(
                grid_frame,
                text=code,
                width=68,
                height=44,
                font=("Arial", 13, "bold"),
                fg_color="#7f1d1d" if booked else "#2563eb",
                hover_color="#7f1d1d" if booked else "#1d4ed8",
                state="disabled" if booked else "normal",
                command=lambda g=code: self.toggle_seat(g),
            )
            btn.grid(row=row, column=col, padx=6, pady=6)
            self.seat_buttons[code] = btn

        self.status_label = ctk.CTkLabel(
            self,
            text="Chọn ghế trên sơ đồ rồi bấm 'Xác nhận ghế & Tiếp tục'",
            font=("Arial", 13),
        )
        self.status_label.pack(pady=(12, 10))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(2, 16))

        ctk.CTkButton(
            btn_row,
            text="← Về suất chiếu",
            width=145,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#475569",
            hover_color="#334155",
            command=self.back_to_showtimes,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="Xác nhận ghế & Tiếp tục",
            width=210,
            height=40,
            font=("Arial", 14, "bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self.confirm_and_next,
        ).pack(side="left", padx=6)

    def back_to_showtimes(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def toggle_seat(self, code):
        self.seats_confirmed = False
        btn = self.seat_buttons[code]
        if code in self.selected_seats:
            self.selected_seats.remove(code)
            btn.configure(fg_color="#2563eb", hover_color="#1d4ed8")
        else:
            self.selected_seats.add(code)
            btn.configure(fg_color="#22c55e", hover_color="#16a34a")

        seats_text = ", ".join(sorted(self.selected_seats)) if self.selected_seats else "Chưa chọn ghế nào"
        self.status_label.configure(text=f"Ghế đang chọn: {seats_text}", text_color="#e2e8f0")

    def confirm_and_next(self):
        if not self.selected_seats:
            messagebox.showwarning("Chưa chọn ghế", "Đạt chọn ít nhất 1 ghế trước nhé.")
            return

        self.seats_confirmed = True
        ds = ", ".join(sorted(self.selected_seats))
        self.status_label.configure(text=f"Đã chốt ghế: {ds}", text_color="#22c55e")

        want_snacks = messagebox.askyesno(
            "Đã xác nhận ghế",
            f"Ghế đã chọn: {ds}\n\nĐạt có muốn chọn thêm bắp nước không?",
        )
        if want_snacks:
            self.open_snacks_step()
        else:
            self.open_checkout_step()

    def open_snacks_step(self):
        def on_done(chosen, total, qtys):
            self.selected_snacks = chosen
            self.snack_total = total
            self.snack_quantities = qtys

            snack_summary = (
                ", ".join(f"{s['name']} x{s['qty']}" for s in chosen)
                if chosen else "Không chọn bắp nước"
            )
            messagebox.showinfo(
                "Đã lưu bắp nước",
                f"{snack_summary}\nTổng bắp nước: {total:,}đ".replace(",", ".")
                + "\n\nChuyển sang bước mã giảm giá & thanh toán.",
            )
            self.open_checkout_step()

        def on_back_to_seats():
            if self.winfo_exists():
                self.focus_set()

        SnacksView(
            self,
            initial_quantities=self.snack_quantities,
            on_confirm=on_done,
            on_back=on_back_to_seats,
        )

    def open_checkout_step(self):
        def handle_paid(invoice):
            messagebox.showinfo(
                "Thanh toán thành công",
                f"Mã hóa đơn: {invoice['ma_hoa_don']}\n"
                f"Tổng thanh toán: {invoice['tong_tien']:,}đ".replace(",", ".")
                + "\n\nMã QR vé đã được tạo trên màn hình.",
            )
            if self.on_saved:
                self.on_saved(invoice)

        def on_back_from_checkout():
            self.open_snacks_step()

        CheckoutView(
            self,
            suat_chieu=self.suat_chieu,
            selected_seats=self.selected_seats,
            selected_snacks=self.selected_snacks,
            snack_total=self.snack_total,
            on_paid=handle_paid,
            on_back=on_back_from_checkout,
        )