from datetime import datetime
import customtkinter as ctk
import qrcode

TICKET_PRICE = 75000

PROMO_CODES = {
    "SINHVIEN": {"type": "percent", "value": 15, "desc": "Giảm 15% tổng đơn"},
    "GIAM20K": {"type": "fixed", "value": 20000, "desc": "Giảm thẳng 20.000đ"},
    "RAPPHIM50": {"type": "fixed", "value": 50000, "desc": "Giảm thẳng 50.000đ"},
}


def fmt_vnd(amount):
    return f"{int(amount):,}đ".replace(",", ".")


class CheckoutView(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        suat_chieu,
        selected_seats,
        selected_snacks,
        snack_total,
        on_paid=None,
        on_back=None,
    ):
        super().__init__(parent)
        self.suat_chieu = suat_chieu
        self.selected_seats = sorted(list(selected_seats))
        self.selected_snacks = selected_snacks
        self.snack_total = snack_total
        self.on_paid = on_paid
        self.on_back = on_back

        self.ticket_total = len(self.selected_seats) * TICKET_PRICE
        self.discount_amount = 0
        self.applied_code = ""
        self.qr_ctk_image = None

        self.title("Thanh toán & Xuất vé QR")
        self.geometry("560x670")
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="XÁC NHẬN ĐẶT VÉ & THANH TOÁN",
            font=("Arial", 19, "bold"),
        ).pack(pady=(16, 10))

        info_box = ctk.CTkFrame(self)
        info_box.pack(fill="x", padx=25, pady=6)

        snacks_text = (
            ", ".join(f"{s['name']} x{s['qty']}" for s in self.selected_snacks)
            if self.selected_snacks
            else "Không chọn"
        )

        details = (
            f"Phim: {suat_chieu.phim.ten_phim}\n"
            f"Suất: {suat_chieu.phong.ten_phong}  |  {suat_chieu.gio_chieu}\n"
            f"Ghế ({len(self.selected_seats)}): {', '.join(self.selected_seats)}\n"
            f"Bắp nước: {snacks_text}"
        )
        ctk.CTkLabel(
            info_box,
            text=details,
            font=("Arial", 13),
            justify="left",
        ).pack(anchor="w", padx=15, pady=12)

        promo_frame = ctk.CTkFrame(self, fg_color="transparent")
        promo_frame.pack(fill="x", padx=25, pady=(8, 2))

        self.promo_entry = ctk.CTkEntry(
            promo_frame,
            placeholder_text="Nhập mã giảm giá (VD: SINHVIEN, GIAM20K)",
            height=36,
        )
        self.promo_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            promo_frame,
            text="Áp dụng",
            width=100,
            height=36,
            command=self.apply_promo,
        ).pack(side="right")

        self.promo_msg = ctk.CTkLabel(
            self,
            text="Mã gợi ý: SINHVIEN (-15%), GIAM20K (-20.000đ)",
            font=("Arial", 12),
            text_color="#94a3b8",
        )
        self.promo_msg.pack(anchor="w", padx=28, pady=(2, 8))

        price_box = ctk.CTkFrame(self)
        price_box.pack(fill="x", padx=25, pady=6)

        self.price_label = ctk.CTkLabel(
            price_box,
            text="",
            font=("Arial", 14),
            justify="left",
        )
        self.price_label.pack(anchor="w", padx=15, pady=10)
        self.refresh_summary()

        pay_row = ctk.CTkFrame(self, fg_color="transparent")
        pay_row.pack(pady=(10, 8))

        self.back_btn = ctk.CTkButton(
            pay_row,
            text="← Trở về",
            width=120,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#475569",
            hover_color="#334155",
            command=self.go_back,
        )
        self.back_btn.pack(side="left", padx=6)

        self.pay_btn = ctk.CTkButton(
            pay_row,
            text="Thanh toán & Xuất mã QR",
            width=210,
            height=40,
            font=("Arial", 14, "bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self.confirm_payment,
        )
        self.pay_btn.pack(side="left", padx=6)

        self.qr_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.qr_frame.pack(pady=6)

    def calc_final_total(self):
        subtotal = self.ticket_total + self.snack_total
        return max(0, subtotal - self.discount_amount)

    def refresh_summary(self):
        subtotal = self.ticket_total + self.snack_total
        final_total = self.calc_final_total()
        text = (
            f"Tiền vé ({len(self.selected_seats)} x {fmt_vnd(TICKET_PRICE)}): {fmt_vnd(self.ticket_total)}\n"
            f"Tiền bắp nước: {fmt_vnd(self.snack_total)}\n"
            f"Tạm tính: {fmt_vnd(subtotal)}\n"
            f"Giảm giá: -{fmt_vnd(self.discount_amount)}\n"
            f"TỔNG THANH TOÁN: {fmt_vnd(final_total)}"
        )
        self.price_label.configure(text=text)

    def apply_promo(self):
        code = self.promo_entry.get().strip().upper()
        if not code:
            self.discount_amount = 0
            self.applied_code = ""
            self.promo_msg.configure(text="Vui lòng nhập mã giảm giá.", text_color="#facc15")
            self.refresh_summary()
            return

        promo = PROMO_CODES.get(code)
        if not promo:
            self.discount_amount = 0
            self.applied_code = ""
            self.promo_msg.configure(text="Mã giảm giá không hợp lệ!", text_color="#ef4444")
            self.refresh_summary()
            return

        subtotal = self.ticket_total + self.snack_total
        if promo["type"] == "percent":
            self.discount_amount = int(subtotal * promo["value"] / 100)
        else:
            self.discount_amount = min(subtotal, promo["value"])

        self.applied_code = code
        self.promo_msg.configure(
            text=f"Đã áp dụng mã {code}: {promo['desc']}",
            text_color="#22c55e",
        )
        self.refresh_summary()

    def go_back(self):
        callback = self.on_back
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        if callback:
            self.master.after(50, callback)

    def confirm_payment(self):
        trung = set(self.selected_seats) & self.suat_chieu.ds_ghe_dadat
        if trung:
            self.promo_msg.configure(
                text=f"Ghế {', '.join(sorted(trung))} vừa có người đặt mất rồi!",
                text_color="#ef4444",
            )
            return

        self.suat_chieu.ds_ghe_dadat.update(self.selected_seats)

        ma_hd = "HD" + datetime.now().strftime("%Y%m%d%H%M%S")
        invoice = {
            "ma_hoa_don": ma_hd,
            "thoi_gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ma_suat": self.suat_chieu.ma_suat,
            "ten_phim": self.suat_chieu.phim.ten_phim,
            "phong": self.suat_chieu.phong.ten_phong,
            "gio_chieu": self.suat_chieu.gio_chieu,
            "ghe": self.selected_seats,
            "bap_nuoc": self.selected_snacks,
            "ma_giam_gia": self.applied_code,
            "giam_gia": self.discount_amount,
            "tong_tien": self.calc_final_total(),
        }

        if self.on_paid:
            self.on_paid(invoice)

        self.pay_btn.configure(state="disabled", text="Đã thanh toán thành công")
        self.back_btn.configure(state="disabled")
        self.promo_entry.configure(state="disabled")
        self.show_qr(invoice)

    def show_qr(self, invoice):
        for w in self.qr_frame.winfo_children():
            w.destroy()

        qr_payload = (
            f"MA VE: {invoice['ma_hoa_don']} | "
            f"PHIM: {invoice['ten_phim']} | "
            f"SUAT: {invoice['gio_chieu']} ({invoice['phong']}) | "
            f"GHE: {', '.join(invoice['ghe'])} | "
            f"TONG: {fmt_vnd(invoice['tong_tien'])}"
        )

        qr_img = qrcode.make(qr_payload).get_image().convert("RGB")
        self.qr_ctk_image = ctk.CTkImage(light_image=qr_img, dark_image=qr_img, size=(165, 165))

        ctk.CTkLabel(
            self.qr_frame,
            text=f"Mã hóa đơn: {invoice['ma_hoa_don']} — Quét QR tại quầy soát vé",
            font=("Arial", 12, "bold"),
            text_color="#38bdf8",
        ).pack(pady=(2, 6))

        ctk.CTkLabel(self.qr_frame, text="", image=self.qr_ctk_image).pack()