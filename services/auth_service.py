USERS = {
    "admin": {
        "password": "123",
        "role": "admin",
        "full_name": "Cinema Manager",
    },
    "staff01": {
        "password": "123",
        "role": "staff",
        "full_name": "Ticket Staff 01",
    },
}


def authenticate(username: str, password: str) -> dict | None:
    clean_username = username.strip()
    user_record = USERS.get(clean_username)
    if not user_record or user_record["password"] != password:
        return None
    return {
        "username": clean_username,
        "role": user_record["role"],
        "full_name": user_record["full_name"],
    }


def is_admin(user: dict | None) -> bool:
    return bool(user) and user.get("role") == "admin"


def is_staff(user: dict | None) -> bool:
    return bool(user) and user.get("role") == "staff"