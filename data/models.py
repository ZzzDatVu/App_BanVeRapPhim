class Movie:
    def __init__(
        self,
        movie_id: str,
        title: str,
        duration_mins: int,
        poster_path: str = "",
        trailer_url: str = "",
    ):
        self.movie_id = movie_id
        self.title = title
        self.duration_mins = duration_mins
        self.poster_path = poster_path
        self.trailer_url = trailer_url


class Room:
    def __init__(self, room_id: str, name: str, rows: int = 5, cols: int = 5):
        self.room_id = room_id
        self.name = name
        self.rows = rows
        self.cols = cols

    @property
    def capacity(self) -> int:
        return self.rows * self.cols

    def get_seat_labels(self) -> list[str]:
        seats = []
        for r in range(self.rows):
            row_label = chr(ord("A") + r)
            for c in range(1, self.cols + 1):
                seats.append(f"{row_label}{c}")
        return seats


class Showtime:
    def __init__(
        self,
        showtime_id: str,
        movie: Movie,
        room: Room,
        start_time: str,
        booked_seats: set[str] | list[str] | None = None,
    ):
        self.showtime_id = showtime_id
        self.movie = movie
        self.room = room
        self.start_time = start_time
        self.booked_seats: set[str] = set(booked_seats) if booked_seats else set()