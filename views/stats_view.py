from tkinter import messagebox
import customtkinter as ctk

from data.models import Movie, Room, Showtime
from services.auth_service import is_admin
from services.schedule_service import build_auto_showtimes
from services.stats_service import get_admin_stats, get_staff_stats


class StatsView(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        current_user: dict,
        showtimes: list[Showtime],
        invoices: list[dict],
        movies: list[Movie],
        rooms: list[Room],
        on_updated=None,
    ):
        super().__init__(master)
        self.current_user = current_user
        self.showtimes = showtimes
        self.invoices = invoices
        self.movies = movies
        self.rooms = rooms
        self.on_updated = on_updated

        admin_mode = is_admin(current_user)
        self.title("Cinema Statistics - Admin" if admin_mode else "Cinema Occupancy - Staff")
        self.geometry("800x560")

        header_text = "ADMIN REVENUE & DEMAND DASHBOARD" if admin_mode else "STAFF CROWD & OCCUPANCY MONITOR"
        ctk.CTkLabel(self, text=header_text, font=("Arial", 19, "bold")).pack(pady=(16, 8))

        self.summary_box = ctk.CTkFrame(self)
        self.summary_box.pack(fill="x", padx=24, pady=6)

        self.lbl_summary = ctk.CTkLabel(self.summary_box, text="", font=("Arial", 14, "bold"))
        self.lbl_summary.pack(pady=12)

        self.scroll_movies = ctk.CTkScrollableFrame(self, width=740, height=380)
        self.scroll_movies.pack(fill="both", expand=True, padx=24, pady=(6, 16))

        self.render_dashboard()

    def _quick_increase_showtime(self, movie_title: str) -> None:
        movie = next((m for m in self.movies if m.title.lower() == movie_title.lower()), None)
        if not movie:
            st_match = next((st for st in self.showtimes if st.movie.title.lower() == movie_title.lower()), None)
            movie = st_match.movie if st_match else None
        if not movie:
            return

        created, _ = build_auto_showtimes(
            existing_showtimes=self.showtimes,
            rooms=self.rooms,
            movie=movie,
            count=1,
            start_time_str="10:00",
        )
        if created:
            self.showtimes.extend(created)
            if self.on_updated:
                self.on_updated()
            self.render_dashboard()
            st = created[0]
            messagebox.showinfo("Added Showtime", f"Added [{st.showtime_id}] {movie.title} in {st.room.name} at {st.start_time}.")

    def _quick_decrease_showtime(self, movie_title: str) -> None:
        candidates = [st for st in self.showtimes if st.movie.title.lower() == movie_title.lower()]
        if not candidates:
            return

        # Uu tien giam suat co it ghe dat nhat
        target = min(candidates, key=lambda st: len(st.booked_seats))
        if target.booked_seats:
            ok = messagebox.askyesno(
                "Confirm Remove",
                f"[{target.showtime_id}] already has {len(target.booked_seats)} booked seats. Remove anyway?",
            )
            if not ok:
                return

        self.showtimes.remove(target)
        if self.on_updated:
            self.on_updated()
        self.render_dashboard()
        messagebox.showinfo("Removed Showtime", f"Removed [{target.showtime_id}] ({target.room.name} - {target.start_time}).")

    def render_dashboard(self) -> None:
        for w in self.scroll_movies.winfo_children():
            w.destroy()

        admin_mode = is_admin(self.current_user)
        stats = get_admin_stats(self.showtimes, self.invoices) if admin_mode else get_staff_stats(self.showtimes)

        if admin_mode:
            summary_text = (
                f"Invoices: {stats['total_invoices']}   |   "
                f"Customers: {stats['total_customers']}/{stats['total_capacity']} ({stats['overall_occupancy']}%)   |   "
                f"Total Revenue: {stats['total_revenue']:,.0f} VND"
            )
        else:
            summary_text = (
                f"Total Customers: {stats['total_customers']}/{stats['total_capacity']}   |   "
                f"Overall Occupancy: {stats['overall_occupancy']}%"
            )
        self.lbl_summary.configure(text=summary_text)

        if not stats["movies"]:
            ctk.CTkLabel(self.scroll_movies, text="No movie showtimes available.", font=("Arial", 14)).pack(pady=24)
            return

        for idx, item in enumerate(stats["movies"], start=1):
            card = ctk.CTkFrame(self.scroll_movies)
            card.pack(fill="x", padx=8, pady=6)

            left_box = ctk.CTkFrame(card, fg_color="transparent")
            left_box.pack(side="left", padx=14, pady=10)

            ctk.CTkLabel(
                left_box,
                text=f"#{idx}  {item['title']}  ({item['showtime_count']} shows)  -  [{item['demand_label']}]",
                font=("Arial", 14, "bold"),
            ).pack(anchor="w")

            sub_line = (
                f"Customers: {item['booked_seats']}/{item['total_seats']} seats  •  "
                f"Occupancy: {item['occupancy_rate']}%"
            )
            if admin_mode:
                sub_line += f"  •  Revenue: {item['revenue']:,.0f} VND"

            ctk.CTkLabel(left_box, text=sub_line, font=("Arial", 12), text_color="#cbd5e1").pack(anchor="w", pady=(2, 0))

            if admin_mode:
                right_box = ctk.CTkFrame(card, fg_color="transparent")
                right_box.pack(side="right", padx=12, pady=10)

                ctk.CTkButton(
                    right_box,
                    text="+1 Show",
                    width=82,
                    height=30,
                    fg_color="#059669",
                    hover_color="#047857",
                    command=lambda t=item["title"]: self._quick_increase_showtime(t),
                ).pack(side="left", padx=4)

                ctk.CTkButton(
                    right_box,
                    text="-1 Show",
                    width=82,
                    height=30,
                    fg_color="#dc2626",
                    hover_color="#b91c1c",
                    command=lambda t=item["title"]: self._quick_decrease_showtime(t),
                ).pack(side="left", padx=4)