from data.models import Showtime

HOT_OCCUPANCY_THRESHOLD = 70.0
LOW_OCCUPANCY_THRESHOLD = 30.0


def _extract_invoice_revenue(invoice: dict) -> float:
    for key in ("total_amount", "final_total", "total", "tong_tien", "thanh_tien"):
        if key in invoice and invoice[key] is not None:
            try:
                return float(invoice[key])
            except (TypeError, ValueError):
                pass
    return 0.0


def _extract_invoice_movie_title(invoice: dict) -> str:
    for key in ("movie_title", "ten_phim", "title"):
        if invoice.get(key):
            return str(invoice[key]).strip()
    return ""


def get_staff_stats(showtimes: list[Showtime]) -> dict:
    total_booked = sum(len(st.booked_seats) for st in showtimes)
    total_capacity = sum(st.room.capacity for st in showtimes)
    overall_occupancy = (total_booked / total_capacity * 100.0) if total_capacity else 0.0

    movie_groups: dict[str, dict] = {}
    for st in showtimes:
        title = st.movie.title
        entry = movie_groups.setdefault(
            title,
            {
                "title": title,
                "showtime_count": 0,
                "booked_seats": 0,
                "total_seats": 0,
            },
        )
        entry["showtime_count"] += 1
        entry["booked_seats"] += len(st.booked_seats)
        entry["total_seats"] += st.room.capacity

    movies_summary = []
    for item in movie_groups.values():
        occ = (item["booked_seats"] / item["total_seats"] * 100.0) if item["total_seats"] else 0.0
        if occ >= HOT_OCCUPANCY_THRESHOLD:
            demand_label = "HOT"
        elif occ >= LOW_OCCUPANCY_THRESHOLD:
            demand_label = "NORMAL"
        else:
            demand_label = "QUIET"

        movies_summary.append(
            {
                "title": item["title"],
                "showtime_count": item["showtime_count"],
                "booked_seats": item["booked_seats"],
                "total_seats": item["total_seats"],
                "occupancy_rate": round(occ, 1),
                "demand_label": demand_label,
            }
        )

    movies_summary.sort(key=lambda x: x["occupancy_rate"], reverse=True)

    return {
        "total_customers": total_booked,
        "total_capacity": total_capacity,
        "overall_occupancy": round(overall_occupancy, 1),
        "movies": movies_summary,
    }


def get_admin_stats(showtimes: list[Showtime], invoices: list[dict]) -> dict:
    base_stats = get_staff_stats(showtimes)
    total_revenue = sum(_extract_invoice_revenue(inv) for inv in invoices)

    revenue_by_movie: dict[str, float] = {}
    for inv in invoices:
        title = _extract_invoice_movie_title(inv)
        if title:
            revenue_by_movie[title.lower()] = revenue_by_movie.get(title.lower(), 0.0) + _extract_invoice_revenue(inv)

    admin_movies = []
    for item in base_stats["movies"]:
        occ = item["occupancy_rate"]
        if occ >= HOT_OCCUPANCY_THRESHOLD:
            action_hint = "INCREASE"
        elif occ < LOW_OCCUPANCY_THRESHOLD and item["showtime_count"] > 1:
            action_hint = "DECREASE"
        else:
            action_hint = "KEEP"

        admin_movies.append(
            {
                **item,
                "revenue": revenue_by_movie.get(item["title"].lower(), 0.0),
                "action_hint": action_hint,
            }
        )

    return {
        **base_stats,
        "total_invoices": len(invoices),
        "total_revenue": total_revenue,
        "movies": admin_movies,
    }