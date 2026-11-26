from datetime import datetime
import customtkinter as ctk
import qrcode

from data.models import Showtime

TICKET_PRICE = 75000

PROMO_CODES = {
    "SINHVIEN": {"type": "percent", "value": 15, "desc": "15% off total order"},
    "GIAM20K": {"type": "fixed", "value": 20000, "desc": "20.000đ off"},
    "RAPPHIM50": {"type": "fixed", "value": 50000, "desc": "50.000đ off"},
}


def fmt_vnd(amount: int | float) -> str:
    return f"{int(amount):,}đ".replace(",", ".")


class CheckoutView(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        showtime: Showtime,
        selected_seats,
        selected_snacks,
        snack_total: int,
        on_paid=None,
        on_back=None,
    ):
        super().__init__(parent)
        self.showtime = showtime
        self.selected_seats = sorted(list(selected_seats))
        self.selected_snacks = selected_snacks
        self.snack_total = snack_total
        self.on_paid = on_paid
        self.on_back = on_back

        self.ticket_total = len(self.selected_seats) * TICKET_PRICE
        self.discount_amount = 0
        self.applied_code = ""
        self.qr_ctk_image = None

        self.title("Checkout & Ticket QR")
        self.geometry("560x670")
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="BOOKING CONFIRMATION & PAYMENT",
            font=("Arial", 19, "bold"),
        ).pack(pady=(16, 10))

        info_box = ctk.CTkFrame(self)
        info_box.pack(fill="x", padx=25, pady=6)

        snacks_text = (
            ", ".join(f"{s['name']} x{s['qty']}" for s in self.selected_snacks)
            if self.selected_snacks
            else "None"
        )

        details = (
            f"Movie: {showtime.movie.title}\n"
            f"Showtime: {showtime.room.name}  |  {showtime.start_time}\n"
            f"Seats ({len(self.selected_seats)}): {', '.join(self.selected_seats)}\n"
            f"Snacks: {snacks_text}"
        )
        ctk.CTkLabel(
            info_box,
            text=details,
            font=("Arial", 13),
            justify="left",
        ).pack(anchor="w", padx=15, pady=12)

        promo_frame = ctk.CTkFrame(self, fg_color="transparent")
        promo_frame.pack(fill="x", padx=25, pady=(8, 2))

        self.entry_promo = ctk.CTkEntry(
            promo_frame,
            placeholder_text="Promo code (e.g. SINHVIEN, GIAM20K)",
            height=36,
        )
        self.entry_promo.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            promo_frame,
            text="Apply",
            width=100,
            height=36,
            command=self.apply_promo,
        ).pack(side="right")

        self.lbl_promo_msg = ctk.CTkLabel(
            self,
            text="Suggested codes: SINHVIEN (-15%), GIAM20K (-20.000đ)",
            font=("Arial", 12),
            text_color="#94a3b8",
        )
        self.lbl_promo_msg.pack(anchor="w", padx=28, pady=(2, 8))

        price_box = ctk.CTkFrame(self)
        price_box.pack(fill="x", padx=25, pady=6)

        self.lbl_price = ctk.CTkLabel(
            price_box,
            text="",
            font=("Arial", 14),
            justify="left",
        )
        self.lbl_price.pack(anchor="w", padx=15, pady=10)
        self.refresh_summary()

        pay_row = ctk.CTkFrame(self, fg_color="transparent")
        pay_row.pack(pady=(10, 8))

        self.btn_back = ctk.CTkButton(
            pay_row,
            text="← Back",
            width=120,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#475569",
            hover_color="#334155",
            command=self.go_back,
        )
        self.btn_back.pack(side="left", padx=6)

        self.btn_pay = ctk.CTkButton(
            pay_row,
            text="Pay & Generate QR",
            width=210,
            height=40,
            font=("Arial", 14, "bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self.confirm_payment,
        )
        self.btn_pay.pack(side="left", padx=6)

        self.qr_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.qr_frame.pack(pady=6)

    def calc_final_total(self) -> int:
        subtotal = self.ticket_total + self.snack_total
        return max(0, subtotal - self.discount_amount)

    def refresh_summary(self) -> None:
        subtotal = self.ticket_total + self.snack_total
        final_total = self.calc_final_total()
        text = (
            f"Tickets ({len(self.selected_seats)} x {fmt_vnd(TICKET_PRICE)}): {fmt_vnd(self.ticket_total)}\n"
            f"Snacks: {fmt_vnd(self.snack_total)}\n"
            f"Subtotal: {fmt_vnd(subtotal)}\n"
            f"Discount: -{fmt_vnd(self.discount_amount)}\n"
            f"TOTAL AMOUNT: {fmt_vnd(final_total)}"
        )
        self.lbl_price.configure(text=text)

    def apply_promo(self) -> None:
        code = self.entry_promo.get().strip().upper()
        if not code:
            self.discount_amount = 0
            self.applied_code = ""
            self.lbl_promo_msg.configure(text="Please enter a promo code.", text_color="#facc15")
            self.refresh_summary()
            return

        promo = PROMO_CODES.get(code)
        if not promo:
            self.discount_amount = 0
            self.applied_code = ""
            self.lbl_promo_msg.configure(text="Invalid promo code!", text_color="#ef4444")
            self.refresh_summary()
            return

        subtotal = self.ticket_total + self.snack_total
        if promo["type"] == "percent":
            self.discount_amount = int(subtotal * promo["value"] / 100)
        else:
            self.discount_amount = min(subtotal, promo["value"])

        self.applied_code = code
        self.lbl_promo_msg.configure(
            text=f"Applied {code}: {promo['desc']}",
            text_color="#22c55e",
        )
        self.refresh_summary()

    def go_back(self) -> None:
        callback = self.on_back
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        if callback:
            self.master.after(50, callback)

    def confirm_payment(self) -> None:
        conflict_seats = set(self.selected_seats) & self.showtime.booked_seats
        if conflict_seats:
            self.lbl_promo_msg.configure(
                text=f"Seats {', '.join(sorted(conflict_seats))} were just booked!",
                text_color="#ef4444",
            )
            return

        self.showtime.booked_seats.update(self.selected_seats)

        invoice_id = "INV" + datetime.now().strftime("%Y%m%d%H%M%S")
        final_total = self.calc_final_total()
        invoice = {
            "invoice_id": invoice_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "showtime_id": self.showtime.showtime_id,
            "movie_title": self.showtime.movie.title,
            "room_name": self.showtime.room.name,
            "start_time": self.showtime.start_time,
            "seats": self.selected_seats,
            "snacks": self.selected_snacks,
            "promo_code": self.applied_code,
            "discount": self.discount_amount,
            "total_amount": final_total,
        }

        if self.on_paid:
            self.on_paid(invoice)

        self.btn_pay.configure(state="disabled", text="Paid Successfully")
        self.btn_back.configure(state="disabled")
        self.entry_promo.configure(state="disabled")
        self.show_qr(invoice)

    def show_qr(self, invoice: dict) -> None:
        for widget in self.qr_frame.winfo_children():
            widget.destroy()

        qr_payload = (
            f"INVOICE: {invoice['invoice_id']} | "
            f"MOVIE: {invoice['movie_title']} | "
            f"TIME: {invoice['start_time']} ({invoice['room_name']}) | "
            f"SEATS: {', '.join(invoice['seats'])} | "
            f"TOTAL: {fmt_vnd(invoice['total_amount'])}"
        )

        qr_img = qrcode.make(qr_payload).get_image().convert("RGB")
        self.qr_ctk_image = ctk.CTkImage(light_image=qr_img, dark_image=qr_img, size=(165, 165))

        ctk.CTkLabel(
            self.qr_frame,
            text=f"Invoice: {invoice['invoice_id']} — Scan QR at ticket gate",
            font=("Arial", 12, "bold"),
            text_color="#38bdf8",
        ).pack(pady=(2, 6))

        ctk.CTkLabel(self.qr_frame, text="", image=self.qr_ctk_image).pack()