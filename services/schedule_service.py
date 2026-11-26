from datetime import datetime
from data.models import Movie, Room, Showtime

CLEANING_BUFFER_MINS = 15


def parse_time_to_mins(time_str: str) -> int:
    dt = datetime.strptime(time_str.strip(), "%H:%M")
    return dt.hour * 60 + dt.minute


def format_mins_to_time(total_mins: int) -> str:
    wrapped = total_mins % (24 * 60)
    return f"{wrapped // 60:02d}:{wrapped % 60:02d}"


def generate_next_showtime_id(showtimes: list[Showtime]) -> str:
    index = len(showtimes) + 1
    while any(st.showtime_id == f"ST{index:02d}" for st in showtimes):
        index += 1
    return f"ST{index:02d}"


def get_showtime_window(showtime: Showtime, buffer_mins: int = CLEANING_BUFFER_MINS) -> tuple[int, int]:
    start = parse_time_to_mins(showtime.start_time)
    end = start + int(showtime.movie.duration_mins) + buffer_mins
    return start, end


def has_room_conflict(
    showtimes: list[Showtime],
    room: Room,
    start_time_str: str,
    duration_mins: int,
    buffer_mins: int = CLEANING_BUFFER_MINS,
) -> tuple[bool, Showtime | None]:
    new_start = parse_time_to_mins(start_time_str)
    new_end = new_start + int(duration_mins) + buffer_mins

    for st in showtimes:
        if st.room.room_id != room.room_id and st.room.name != room.name:
            continue
        old_start, old_end = get_showtime_window(st, buffer_mins=buffer_mins)
        if new_start < old_end and old_start < new_end:
            return True, st
    return False, None


def find_next_available_time(
    showtimes: list[Showtime],
    room: Room,
    preferred_time_str: str,
    duration_mins: int,
    buffer_mins: int = CLEANING_BUFFER_MINS,
) -> str:
    candidate = parse_time_to_mins(preferred_time_str)
    dur = int(duration_mins)

    while True:
        new_end = candidate + dur + buffer_mins
        conflict_end = None

        for st in showtimes:
            if st.room.room_id != room.room_id and st.room.name != room.name:
                continue
            old_start, old_end = get_showtime_window(st, buffer_mins=buffer_mins)
            if candidate < old_end and old_start < new_end:
                conflict_end = max(conflict_end or 0, old_end)

        if conflict_end is None:
            return format_mins_to_time(candidate)
        candidate = conflict_end


def calculate_occupancy_rate(showtimes: list[Showtime], movie_title: str | None = None) -> float:
    filtered = [
        st for st in showtimes
        if movie_title is None or st.movie.title.strip().lower() == movie_title.strip().lower()
    ]
    total_seats = sum(st.room.capacity for st in filtered)
    if total_seats == 0:
        return 0.0
    booked = sum(len(st.booked_seats) for st in filtered)
    return (booked / total_seats) * 100.0


HOT_MOVIE_OCCUPANCY_THRESHOLD = 70.0


def build_auto_showtimes(
    existing_showtimes: list[Showtime],
    rooms: list[Room],
    movie: Movie,
    count: int,
    start_time_str: str,
    buffer_mins: int = CLEANING_BUFFER_MINS,
) -> tuple[list[Showtime], str]:
    if not rooms or count <= 0:
        return [], "normal"

    current_occ = calculate_occupancy_rate(existing_showtimes, movie_title=movie.title)
    if current_occ >= HOT_MOVIE_OCCUPANCY_THRESHOLD:
        strategy = "peak"
        ordered_rooms = sorted(rooms, key=lambda r: r.capacity, reverse=True)
    else:
        strategy = "normal"
        ordered_rooms = list(rooms)

    working_list = list(existing_showtimes)
    created: list[Showtime] = []
    current_slot = start_time_str

    for i in range(count):
        target_room = ordered_rooms[i % len(ordered_rooms)]
        valid_time = find_next_available_time(
            showtimes=working_list,
            room=target_room,
            preferred_time_str=current_slot,
            duration_mins=movie.duration_mins,
            buffer_mins=buffer_mins,
        )
        new_id = generate_next_showtime_id(working_list)
        new_st = Showtime(
            showtime_id=new_id,
            movie=movie,
            room=target_room,
            start_time=valid_time,
            booked_seats=[],
        )
        working_list.append(new_st)
        created.append(new_st)

        if (i + 1) % len(ordered_rooms) == 0:
            current_slot = format_mins_to_time(
                parse_time_to_mins(valid_time) + int(movie.duration_mins) + buffer_mins
            )

    return created, strategy