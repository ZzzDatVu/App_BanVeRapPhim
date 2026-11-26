from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk

from data.models import Movie, Room, Showtime
from services.schedule_service import (
    CLEANING_BUFFER_MINS,
    build_auto_showtimes,
    generate_next_showtime_id,
    has_room_conflict,
)


class AdminShowtimesView(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        showtimes: list[Showtime],
        movies: list[Movie],
        rooms: list[Room],
        on_updated,
    ):
        super().__init__(master)
        self.title("Showtime Management (Admin)")
        self.geometry("820x640")
        self.showtimes = showtimes
        self.movies = movies
        self.rooms = rooms
        self.on_updated = on_updated

        ctk.CTkLabel(
            self,
            text="SHOWTIME MANAGEMENT (ADD / REMOVE)",
            font=("Arial", 19, "bold"),
        ).pack(pady=(14, 8))

        self.mode_switch = ctk.CTkSegmentedButton(
            self,
            values=["Auto Schedule", "Manual Schedule"],
            command=self.render_form_panel,
        )
        self.mode_switch.set("Auto Schedule")
        self.mode_switch.pack(pady=(0, 8))

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="x", padx=24, pady=4)
        self.render_form_panel("Auto Schedule")

        ctk.CTkLabel(
            self,
            text="Current Showtimes (sorted by Room & Time)",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=26, pady=(10, 4))

        self.scroll_showtimes = ctk.CTkScrollableFrame(self, width=760, height=280)
        self.scroll_showtimes.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self.render_showtimes_list()

    def _get_or_create_movie(
        self,
        title: str,
        duration_mins: int = 120,
        poster_path: str = "",
        trailer_url: str = "",
    ) -> Movie:
        clean_title = title.strip()
        for m in self.movies:
            if m.title.strip().lower() == clean_title.lower():
                if poster_path:
                    m.poster_path = poster_path
                if trailer_url:
                    m.trailer_url = trailer_url
                return m

        next_idx = len(self.movies) + 1
        while any(m.movie_id == f"M{next_idx:02d}" for m in self.movies):
            next_idx += 1

        new_movie = Movie(
            movie_id=f"M{next_idx:02d}",
            title=clean_title,
            duration_mins=duration_mins,
            poster_path=poster_path,
            trailer_url=trailer_url,
        )
        self.movies.append(new_movie)
        return new_movie

    def render_form_panel(self, mode: str) -> None:
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        movie_titles = [m.title for m in self.movies] or ["New Movie"]
        room_names = [f"{r.name} ({r.rows}x{r.cols})" for r in self.rooms] or ["Room 1 (5x5)"]

        if mode == "Auto Schedule":
            ctk.CTkLabel(
                self.form_frame,
                text="Auto-assign across rooms (Hot >= 70% prioritizes largest room; 15m cleaning buffer)",
                font=("Arial", 12, "bold"),
            ).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(8, 6))

            self.cmb_auto_movie = ctk.CTkComboBox(self.form_frame, values=movie_titles, width=220)
            self.cmb_auto_movie.set(movie_titles[0])
            self.cmb_auto_movie.grid(row=1, column=0, padx=(12, 6), pady=6)

            self.cmb_auto_count = ctk.CTkComboBox(
                self.form_frame,
                values=["1 show", "2 shows", "3 shows", "4 shows"],
                width=120,
            )
            self.cmb_auto_count.set("2 shows")
            self.cmb_auto_count.grid(row=1, column=1, padx=6, pady=6)

            self.entry_auto_start = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Start time (e.g. 10:00)",
                width=165,
            )
            self.entry_auto_start.insert(0, "10:00")
            self.entry_auto_start.grid(row=1, column=2, padx=6, pady=6)

            ctk.CTkButton(
                self.form_frame,
                text="Auto Assign",
                width=145,
                height=34,
                fg_color="#2563eb",
                hover_color="#1d4ed8",
                command=self.handle_auto_add,
            ).grid(row=1, column=3, padx=(6, 12), pady=6)

            # Optional fields for new movie duration / poster / trailer
            self.entry_auto_duration = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Duration mins if new (120)",
                width=220,
            )
            self.entry_auto_duration.grid(row=2, column=0, padx=(12, 6), pady=(2, 10))

            self.entry_auto_poster = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Poster path (optional)",
                width=295,
            )
            self.entry_auto_poster.grid(row=2, column=1, columnspan=2, padx=6, pady=(2, 10), sticky="ew")

            self.entry_auto_trailer = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Trailer URL (optional)",
                width=145,
            )
            self.entry_auto_trailer.grid(row=2, column=3, padx=(6, 12), pady=(2, 10))

        else:
            ctk.CTkLabel(
                self.form_frame,
                text="Manually pick room and start time (checks room conflicts + 15m cleaning)",
                font=("Arial", 12, "bold"),
            ).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(8, 6))

            self.entry_manual_id = ctk.CTkEntry(
                self.form_frame,
                placeholder_text=f"ID (e.g. {generate_next_showtime_id(self.showtimes)})",
                width=140,
            )
            self.entry_manual_id.grid(row=1, column=0, padx=(12, 6), pady=6)

            self.cmb_manual_movie = ctk.CTkComboBox(self.form_frame, values=movie_titles, width=210)
            self.cmb_manual_movie.set(movie_titles[0])
            self.cmb_manual_movie.grid(row=1, column=1, padx=6, pady=6)

            self.cmb_manual_room = ctk.CTkComboBox(self.form_frame, values=room_names, width=165)
            self.cmb_manual_room.set(room_names[0])
            self.cmb_manual_room.grid(row=1, column=2, padx=6, pady=6)

            self.entry_manual_time = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Time (e.g. 14:30)",
                width=145,
            )
            self.entry_manual_time.grid(row=1, column=3, padx=(6, 12), pady=6)

            self.entry_manual_duration = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Duration mins if new (120)",
                width=210,
            )
            self.entry_manual_duration.grid(row=2, column=1, padx=6, pady=(2, 10))

            ctk.CTkButton(
                self.form_frame,
                text="+ Add Showtime",
                width=145,
                height=34,
                fg_color="#059669",
                hover_color="#047857",
                command=self.handle_manual_add,
            ).grid(row=2, column=3, padx=(6, 12), pady=(2, 10))

    def handle_auto_add(self) -> None:
        title = self.cmb_auto_movie.get().strip()
        if not title:
            messagebox.showwarning("Missing Info", "Please select or enter a movie title.")
            return

        start_str = self.entry_auto_start.get().strip()
        try:
            datetime.strptime(start_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Please use HH:MM format (e.g. 10:00).")
            return

        raw_dur = self.entry_auto_duration.get().strip()
        duration_mins = int(raw_dur) if raw_dur.isdigit() else 120
        poster = self.entry_auto_poster.get().strip()
        trailer = self.entry_auto_trailer.get().strip()

        movie = self._get_or_create_movie(title, duration_mins, poster, trailer)
        count = int(self.cmb_auto_count.get().split()[0])

        created, strategy = build_auto_showtimes(
            existing_showtimes=self.showtimes,
            rooms=self.rooms,
            movie=movie,
            count=count,
            start_time_str=start_str,
            buffer_mins=CLEANING_BUFFER_MINS,
        )
        self.showtimes.extend(created)
        self.render_showtimes_list()
        if self.on_updated:
            self.on_updated()

        mode_note = "Priority Largest Rooms (Hot Movie)" if strategy == "peak" else "Even Room Rotation (Normal)"
        summary = "\n".join(f"[{st.showtime_id}] {st.room.name} - {st.start_time}" for st in created)
        messagebox.showinfo("Auto Scheduled", f"Mode: {mode_note}\n\n{summary}")

    def handle_manual_add(self) -> None:
        showtime_id = self.entry_manual_id.get().strip() or generate_next_showtime_id(self.showtimes)
        title = self.cmb_manual_movie.get().strip()
        room_label = self.cmb_manual_room.get().strip()
        time_str = self.entry_manual_time.get().strip()

        if not title or not time_str:
            messagebox.showwarning("Missing Info", "Please enter movie title and start time.")
            return

        if any(st.showtime_id == showtime_id for st in self.showtimes):
            messagebox.showerror("Duplicate ID", f"Showtime ID '{showtime_id}' already exists.")
            return

        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Please use HH:MM format (e.g. 14:30).")
            return

        selected_room = next(
            (r for r in self.rooms if room_label.startswith(r.name)),
            self.rooms[0],
        )
        raw_dur = self.entry_manual_duration.get().strip()
        duration_mins = int(raw_dur) if raw_dur.isdigit() else 120
        movie = self._get_or_create_movie(title, duration_mins)

        conflict, existing = has_room_conflict(
            showtimes=self.showtimes,
            room=selected_room,
            start_time_str=time_str,
            duration_mins=movie.duration_mins,
            buffer_mins=CLEANING_BUFFER_MINS,
        )
        if conflict and existing:
            messagebox.showwarning(
                "Room Conflict",
                f"{selected_room.name} already has [{existing.showtime_id}] {existing.movie.title} "
                f"at {existing.start_time} (including {CLEANING_BUFFER_MINS}m cleaning).",
            )
            return

        new_st = Showtime(showtime_id, movie, selected_room, time_str, [])
        self.showtimes.append(new_st)
        self.entry_manual_id.delete(0, "end")
        self.entry_manual_time.delete(0, "end")

        self.render_showtimes_list()
        if self.on_updated:
            self.on_updated()
        messagebox.showinfo("Success", f"Added [{showtime_id}] {movie.title} in {selected_room.name} at {time_str}.")

    def handle_delete(self, showtime: Showtime) -> None:
        if showtime.booked_seats:
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Showtime [{showtime.showtime_id}] has {len(showtime.booked_seats)} booked seats. Delete anyway?",
            )
            if not confirm:
                return

        self.showtimes.remove(showtime)
        self.render_showtimes_list()
        if self.on_updated:
            self.on_updated()

    def render_showtimes_list(self) -> None:
        for widget in self.scroll_showtimes.winfo_children():
            widget.destroy()

        if not self.showtimes:
            ctk.CTkLabel(
                self.scroll_showtimes,
                text="No showtimes scheduled yet.",
                font=("Arial", 13),
            ).pack(pady=20)
            return

        sorted_list = sorted(self.showtimes, key=lambda st: (st.room.room_id, st.start_time))
        for st in sorted_list:
            row = ctk.CTkFrame(self.scroll_showtimes)
            row.pack(fill="x", padx=6, pady=5)

            info = (
                f"[{st.showtime_id}]  {st.movie.title} ({st.movie.duration_mins}m)  |  "
                f"{st.room.name} ({st.room.capacity} seats)  |  {st.start_time}  |  "
                f"Booked: {len(st.booked_seats)}/{st.room.capacity}"
            )
            ctk.CTkLabel(row, text=info, font=("Arial", 13)).pack(side="left", padx=12, pady=8)

            ctk.CTkButton(
                row,
                text="Remove",
                width=85,
                height=30,
                fg_color="#dc2626",
                hover_color="#b91c1c",
                command=lambda target=st: self.handle_delete(target),
            ).pack(side="right", padx=12)