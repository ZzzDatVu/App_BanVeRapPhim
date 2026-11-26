import customtkinter as ctk
from storage import luu_du_lieu, nap_du_lieu
from seats_view import SeatsView
from stats_view import StatsView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CinemaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cinema Booking App")
        self.geometry("900x600")

        self.ds_suat, self.ds_hoa_don = nap_du_lieu()

        ctk.CTkButton(
            self,
            text="Thống kê & Đề xuất suất",
            width=185,
            height=34,
            font=("Arial", 12, "bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.open_stats,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            self,
            text="DANH SÁCH SUẤT CHIẾU",
            font=("Arial", 22, "bold"),
        ).pack(pady=(20, 10))

        self.list_frame = ctk.CTkScrollableFrame(self, width=820, height=450)
        self.list_frame.pack(padx=30, pady=10, fill="both", expand=True)

        self.render_showtimes()

    def open_stats(self):
        StatsView(self, self.ds_suat, self.ds_hoa_don)


    def render_showtimes(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        if not self.ds_suat:
            ctk.CTkLabel(
                self.list_frame,
                text="Chưa có suất chiếu nào.",
                font=("Arial", 15),
            ).pack(pady=30)
            return

        for sc in self.ds_suat:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", padx=10, pady=8)

            info = (
                f"[{sc.ma_suat}]  {sc.phim.ten_phim}  ({sc.phim.thoi_luong})\n"
                f"Phòng: {sc.phong.ten_phong}  |  Giờ chiếu: {sc.gio_chieu}  |  "
                f"Đã đặt: {len(sc.ds_ghe_dadat)} ghế"
            )
            ctk.CTkLabel(
                row,
                text=info,
                font=("Arial", 14),
                justify="left",
            ).pack(side="left", padx=15, pady=12)

            ctk.CTkButton(
                row,
                text="Chọn ghế",
                width=120,
                height=36,
                command=lambda s=sc: self.open_seats(s),
            ).pack(side="right", padx=15)

    def open_seats(self, suat_chieu):
        SeatsView(self, suat_chieu, on_saved=self.on_seats_saved)

    def on_seats_saved(self, invoice=None):
        if invoice:
            self.ds_hoa_don.append(invoice)
        luu_du_lieu(self.ds_suat, self.ds_hoa_don)
        self.render_showtimes()


if __name__ == "__main__":
    app = CinemaApp()
    app.mainloop()