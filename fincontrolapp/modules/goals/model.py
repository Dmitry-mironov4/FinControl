from dataclasses import dataclass

@dataclass
class Goal:
    id: int | None
    user_id: int
    name: str
    target_amount: float
    current_amount: float = 0.0
    deadline: str | None = None
    created_at: str | None = None