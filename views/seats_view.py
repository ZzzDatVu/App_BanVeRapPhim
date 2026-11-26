from tkinter import messagebox
import customtkinter as ctk

from data.models import Showtime
from views.checkout_view import CheckoutView
from views.snacks_view import SnacksView


class SeatsView(ctk.CTkToplevel):
    def __init__(self, parent, showtime: Showtime, on_saved=None):
        super().__init__(parent)
        self.showtime = showtime
        self.on_saved = on_saved
        self.selected_seats: set[str] = set()
        self.seat_buttons: dict[str, ctk.CTkButton] = {}

        self.selected_snacks: list[dict] = []
        self.snack_quantities: dict[str, int] = {}
        self.snack_total: int = 0
        self.seats_confirmed: bool = False

        self.title(f"Select Seats - {showtime.movie.title} ({showtime.start_time})")
        self.geometry("620x540")
        self.grab_set()

        ctk.CTkLabel(
            self,
            text=f"{showtime.movie.title}  |  {showtime.room.name}  |  {showtime.start_time}",
            font=("Arial", 16, "bold"),
        ).pack(pady=(18, 6))

        ctk.CTkLabel(
            self,
            text="▬▬▬▬ SCREEN ▬▬▬▬",
            font=("Arial", 13, "bold"),
            text_color="#94a3b8",
        ).pack(pady=(4, 12))

        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(pady=(0, 8))
        ctk.CTkLabel(legend, text="■ Available", text_color="#3b82f6", font=("Arial", 12, "bold")).pack(side="left", padx=12)
        ctk.CTkLabel(legend, text="■ Selected", text_color="#22c55e", font=("Arial", 12, "bold")).pack(side="left", padx=12)
        ctk.CTkLabel(legend, text="■ Booked", text_color="#ef4444", font=("Arial", 12, "bold")).pack(side="left", padx=12)

        grid_frame = ctk.CTkFrame(self)
        grid_frame.pack(pady=6, padx=20)

        seats = showtime.room.get_seat_labels()
        cols = showtime.room.cols

        for idx, code in enumerate(seats):
            row = idx // cols
            col = idx % cols
            booked = code in showtime.booked_seats

            btn = ctk.CTkButton(
                grid_frame,
                text=code,
                width=68,
                height=44,
                font=("Arial", 13, "bold"),
                fg_color="#7f1d1d" if booked else "#2563eb",
                hover_color="#7f1d1d" if booked else "#1d4ed8",
                state="disabled" if booked else "normal",
                command=lambda seat_code=code: self.toggle_seat(seat_code),
            )
            btn.grid(row=row, column=col, padx=6, pady=6)
            self.seat_buttons[code] = btn

        self.lbl_status = ctk.CTkLabel(
            self,
            text="Select seats on the map, then click 'Confirm Seats & Continue'",
            font=("Arial", 13),
        )
        self.lbl_status.pack(pady=(12, 10))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(2, 16))

        ctk.CTkButton(
            btn_row,
            text="← Back to Showtimes",
            width=155,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#475569",
            hover_color="#334155",
            command=self.back_to_showtimes,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="Confirm Seats & Continue",
            width=210,
            height=40,
            font=("Arial", 14, "bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self.confirm_and_next,
        ).pack(side="left", padx=6)

    def back_to_showtimes(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def toggle_seat(self, code: str) -> None:
        self.seats_confirmed = False
        btn = self.seat_buttons[code]
        if code in self.selected_seats:
            self.selected_seats.remove(code)
            btn.configure(fg_color="#2563eb", hover_color="#1d4ed8")
        else:
            self.selected_seats.add(code)
            btn.configure(fg_color="#22c55e", hover_color="#16a34a")

        seats_text = ", ".join(sorted(self.selected_seats)) if self.selected_seats else "No seats selected"
        self.lbl_status.configure(text=f"Selected seats: {seats_text}", text_color="#e2e8f0")

    def confirm_and_next(self) -> None:
        if not self.selected_seats:
            messagebox.showwarning("No Seats Selected", "Please select at least 1 seat first.")
            return

        self.seats_confirmed = True
        seats_str = ", ".join(sorted(self.selected_seats))
        self.lbl_status.configure(text=f"Confirmed seats: {seats_str}", text_color="#22c55e")

        want_snacks = messagebox.askyesno(
            "Seats Confirmed",
            f"Selected seats: {seats_str}\n\nDo you want to add snacks or drinks?",
        )
        if want_snacks:
            self.open_snacks_step()
        else:
            self.open_checkout_step()

    def open_snacks_step(self) -> None:
        def on_done(chosen, total, qtys):
            self.selected_snacks = chosen
            self.snack_total = total
            self.snack_quantities = qtys

            snack_summary = (
                ", ".join(f"{item['name']} x{item['qty']}" for item in chosen)
                if chosen else "No snacks selected"
            )
            formatted_total = f"{total:,}đ".replace(",", ".")
            messagebox.showinfo(
                "Snacks Saved",
                f"{snack_summary}\nSnacks total: {formatted_total}\n\nProceeding to discount & checkout.",
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

    def open_checkout_step(self) -> None:
        def handle_paid(invoice: dict):
            amount = invoice.get("total_amount", invoice.get("tong_tien", 0))
            inv_id = invoice.get("invoice_id", invoice.get("ma_hoa_don", "INV"))
            formatted_amount = f"{amount:,}đ".replace(",", ".")
            messagebox.showinfo(
                "Payment Successful",
                f"Invoice ID: {inv_id}\nTotal Paid: {formatted_amount}\n\nTicket QR code is displayed on screen.",
            )
            if self.on_saved:
                self.on_saved(invoice)

        def on_back_from_checkout():
            self.open_snacks_step()

        CheckoutView(
            self,
            showtime=self.showtime,
            selected_seats=self.selected_seats,
            selected_snacks=self.selected_snacks,
            snack_total=self.snack_total,
            on_paid=handle_paid,
            on_back=on_back_from_checkout,
        )