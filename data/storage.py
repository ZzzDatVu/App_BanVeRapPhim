import json
from pathlib import Path
from data.models import Movie, Room, Showtime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.json"

# Khai bao phong co dinh tai day; can doi hang/cot thi sua truc tiep tai day
DEFAULT_ROOMS = [
    Room(room_id="R01", name="Room 1", rows=5, cols=5),
    Room(room_id="R02", name="Room 2", rows=6, cols=7),
    Room(room_id="R03", name="Room 3", rows=7, cols=8),
]

DEFAULT_MOVIES = [
    Movie(movie_id="M01", title="Nha ba toi mot phong", duration_mins=120),
    Movie(movie_id="M02", title="Tho oi", duration_mins=127),
]


def _default_payload() -> dict:
    m1, m2 = DEFAULT_MOVIES[0], DEFAULT_MOVIES[1]
    r1 = DEFAULT_ROOMS[0]
    initial_showtimes = [
        Showtime("ST01", m1, r1, "09:00", []),
        Showtime("ST02", m2, r1, "11:30", []),
    ]
    return {
        "rooms": [
            {
                "room_id": r.room_id,
                "name": r.name,
                "rows": r.rows,
                "cols": r.cols,
            }
            for r in DEFAULT_ROOMS
        ],
        "movies": [
            {
                "movie_id": m.movie_id,
                "title": m.title,
                "duration_mins": m.duration_mins,
                "poster_path": m.poster_path,
                "trailer_url": m.trailer_url,
            }
            for m in DEFAULT_MOVIES
        ],
        "showtimes": [
            {
                "showtime_id": st.showtime_id,
                "movie": {
                    "movie_id": st.movie.movie_id,
                    "title": st.movie.title,
                    "duration_mins": st.movie.duration_mins,
                    "poster_path": st.movie.poster_path,
                    "trailer_url": st.movie.trailer_url,
                },
                "room": {
                    "room_id": st.room.room_id,
                    "name": st.room.name,
                    "rows": st.room.rows,
                    "cols": st.room.cols,
                },
                "start_time": st.start_time,
                "booked_seats": sorted(st.booked_seats),
            }
            for st in initial_showtimes
        ],
        "invoices": [],
    }


def save_data(
    showtimes: list[Showtime],
    invoices: list[dict] | None = None,
    movies: list[Movie] | None = None,
    rooms: list[Room] | None = None,
) -> None:
    room_list = rooms if rooms is not None else DEFAULT_ROOMS
    movie_list = movies if movies is not None else [st.movie for st in showtimes]

    unique_movies: dict[str, Movie] = {}
    for m in movie_list:
        unique_movies[m.title.strip().lower()] = m

    payload = {
        "rooms": [
            {
                "room_id": r.room_id,
                "name": r.name,
                "rows": r.rows,
                "cols": r.cols,
            }
            for r in room_list
        ],
        "movies": [
            {
                "movie_id": m.movie_id,
                "title": m.title,
                "duration_mins": m.duration_mins,
                "poster_path": m.poster_path,
                "trailer_url": m.trailer_url,
            }
            for m in unique_movies.values()
        ],
        "showtimes": [
            {
                "showtime_id": st.showtime_id,
                "movie": {
                    "movie_id": st.movie.movie_id,
                    "title": st.movie.title,
                    "duration_mins": st.movie.duration_mins,
                    "poster_path": st.movie.poster_path,
                    "trailer_url": st.movie.trailer_url,
                },
                "room": {
                    "room_id": st.room.room_id,
                    "name": st.room.name,
                    "rows": st.room.rows,
                    "cols": st.room.cols,
                },
                "start_time": st.start_time,
                "booked_seats": sorted(st.booked_seats),
            }
            for st in showtimes
        ],
        "invoices": invoices if invoices is not None else [],
    }

    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)


def load_data() -> tuple[list[Showtime], list[dict], list[Movie], list[Room]]:
    if not DB_PATH.exists():
        payload = _default_payload()
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)

    with open(DB_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Luon lay rows/cols tu DEFAULT_ROOMS neu trung room_id de de sua kich thuoc ngay trong code
    default_room_map = {r.room_id: r for r in DEFAULT_ROOMS}
    rooms: list[Room] = []
    for r_item in payload.get("rooms", []):
        rid = r_item["room_id"]
        if rid in default_room_map:
            d_room = default_room_map[rid]
            rooms.append(Room(d_room.room_id, d_room.name, d_room.rows, d_room.cols))
        else:
            rooms.append(
                Room(
                    room_id=rid,
                    name=r_item["name"],
                    rows=int(r_item.get("rows", 5)),
                    cols=int(r_item.get("cols", 5)),
                )
            )
    if not rooms:
        rooms = list(DEFAULT_ROOMS)

    room_by_id = {r.room_id: r for r in rooms}
    room_by_name = {r.name: r for r in rooms}

    movies: list[Movie] = [
        Movie(
            movie_id=m_item["movie_id"],
            title=m_item["title"],
            duration_mins=int(m_item.get("duration_mins", 120)),
            poster_path=m_item.get("poster_path", ""),
            trailer_url=m_item.get("trailer_url", ""),
        )
        for m_item in payload.get("movies", [])
    ]

    showtimes: list[Showtime] = []
    for st_item in payload.get("showtimes", []):
        m_data = st_item["movie"]
        movie = Movie(
            movie_id=m_data["movie_id"],
            title=m_data["title"],
            duration_mins=int(m_data.get("duration_mins", 120)),
            poster_path=m_data.get("poster_path", ""),
            trailer_url=m_data.get("trailer_url", ""),
        )

        r_data = st_item["room"]
        room = (
            room_by_id.get(r_data.get("room_id"))
            or room_by_name.get(r_data.get("name"))
            or Room(
                room_id=r_data.get("room_id", "R01"),
                name=r_data.get("name", "Room 1"),
                rows=int(r_data.get("rows", 5)),
                cols=int(r_data.get("cols", 5)),
            )
        )

        showtime = Showtime(
            showtime_id=st_item["showtime_id"],
            movie=movie,
            room=room,
            start_time=st_item["start_time"],
            booked_seats=st_item.get("booked_seats", []),
        )
        showtimes.append(showtime)

    invoices = payload.get("invoices", [])
    return showtimes, invoices, movies, rooms