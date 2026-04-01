from dataclasses import dataclass

@dataclass
class User:
    id: int | None
    telegram_id: int | None
    email: str | None
    phone: str | None
    username: str
    password_hash: str
    created_at: str

