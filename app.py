import webbrowser
import customtkinter as ctk

from data.models import Showtime
from data.storage import load_data, save_data
from services.auth_service import is_admin
from views.admin_view import AdminShowtimesView
from views.login_view import LoginWindow, safe_destroy
from views.seats_view import SeatsView
from views.stats_view import StatsView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CinemaApp(ctk.CTk):
    def __init__(self, current_user: dict, on_logout):
        super().__init__()
        self.current_user = current_user
        self.on_logout = on_logout

        self.title("Cinema Booking App")
        self.geometry("860x600")

        self.showtimes, self.invoices, self.movies, self.rooms = load_data()

        self._build_header()
        self._build_main_body()
        self.render_showtimes()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=20, pady=(16, 8))

        role_label = "ADMIN" if is_admin(self.current_user) else "STAFF"
        user_info = f"Cinema System  |  {self.current_user['full_name']} ({role_label})"
        ctk.CTkLabel(header, text=user_info, font=("Arial", 16, "bold")).pack(side="left", padx=14, pady=12)

        ctk.CTkButton(
            header,
            text="Logout",
            width=90,
            fg_color="#475569",
            hover_color="#334155",
            command=self.handle_logout,
        ).pack(side="right", padx=(6, 14), pady=10)

        ctk.CTkButton(
            header,
            text="Statistics",
            width=110,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.open_stats,
        ).pack(side="right", padx=6, pady=10)

        if is_admin(self.current_user):
            ctk.CTkButton(
                header,
                text="Manage Showtimes",
                width=145,
                fg_color="#059669",
                hover_color="#047857",
                command=self.open_admin_showtimes,
            ).pack(side="right", padx=6, pady=10)

    def _build_main_body(self) -> None:
        ctk.CTkLabel(
            self,
            text="TODAY'S SHOWTIMES",
            font=("Arial", 18, "bold"),
        ).pack(anchor="w", padx=24, pady=(8, 6))

        self.scroll_showtimes = ctk.CTkScrollableFrame(self, width=800, height=450)
        self.scroll_showtimes.pack(fill="both", expand=True, padx=20, pady=(0, 18))

    def persist_and_refresh(self) -> None:
        save_data(self.showtimes, self.invoices, self.movies, self.rooms)
        self.render_showtimes()

    def render_showtimes(self) -> None:
        for widget in self.scroll_showtimes.winfo_children():
            widget.destroy()

        if not self.showtimes:
            ctk.CTkLabel(
                self.scroll_showtimes,
                text="No showtimes available.",
                font=("Arial", 14),
            ).pack(pady=30)
            return

        sorted_showtimes = sorted(self.showtimes, key=lambda st: (st.start_time, st.room.room_id))
        for st in sorted_showtimes:
            card = ctk.CTkFrame(self.scroll_showtimes)
            card.pack(fill="x", padx=8, pady=6)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=14, pady=10)

            ctk.CTkLabel(
                info_frame,
                text=f"[{st.showtime_id}]  {st.movie.title}  ({st.movie.duration_mins} mins)",
                font=("Arial", 15, "bold"),
            ).pack(anchor="w")

            available = st.room.capacity - len(st.booked_seats)
            sub_text = (
                f"Room: {st.room.name} ({st.room.rows}x{st.room.cols})   |   "
                f"Time: {st.start_time}   |   Available: {available}/{st.room.capacity} seats"
            )
            ctk.CTkLabel(
                info_frame,
                text=sub_text,
                font=("Arial", 12),
                text_color="#cbd5e1",
            ).pack(anchor="w", pady=(3, 0))

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=12, pady=10)

            if st.movie.trailer_url:
                ctk.CTkButton(
                    btn_frame,
                    text="Trailer",
                    width=75,
                    fg_color="#6d28d9",
                    hover_color="#5b21b6",
                    command=lambda url=st.movie.trailer_url: webbrowser.open(url),
                ).pack(side="left", padx=4)

            ctk.CTkButton(
                btn_frame,
                text="Select Seats",
                width=115,
                command=lambda target=st: self.open_seats_view(target),
            ).pack(side="left", padx=4)

    def open_seats_view(self, showtime: Showtime) -> None:
        def on_booking_saved(invoice: dict) -> None:
            if invoice:
                self.invoices.append(invoice)
            self.persist_and_refresh()

        SeatsView(
            self,
            showtime=showtime,
            on_saved=on_booking_saved,
        )

    def open_stats(self) -> None:
        StatsView(
            self,
            current_user=self.current_user,
            showtimes=self.showtimes,
            invoices=self.invoices,
            movies=self.movies,
            rooms=self.rooms,
            on_updated=self.persist_and_refresh,
        )

    def open_admin_showtimes(self) -> None:
        AdminShowtimesView(
            self,
            showtimes=self.showtimes,
            movies=self.movies,
            rooms=self.rooms,
            on_updated=self.persist_and_refresh,
        )

    def handle_logout(self) -> None:
        callback = self.on_logout
        safe_destroy(self)
        callback()


def run_app() -> None:
    def launch_login() -> None:
        login_win = LoginWindow(on_login_success=launch_main)
        login_win.mainloop()

    def launch_main(user: dict) -> None:
        main_win = CinemaApp(current_user=user, on_logout=launch_login)
        main_win.mainloop()

    launch_login()


if __name__ == "__main__":
    run_app()