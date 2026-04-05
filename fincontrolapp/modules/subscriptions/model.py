from dataclasses import dataclass

@dataclass
class Subscription:
    id: int | None
    user_id: int
    name: str
    amount: float
    charge_day: int
    period: str
    start_date: str
    created_at: str | None
