from dataclasses import dataclass

@dataclass
class Transaction:
    id: int | None
    user_id: int
    type: str  # 'income' or 'expense'
    amount: float
    category_id: int
    description: str | None
    date: str  # ISO format date string
    is_recurring: bool = False
    created_at: str | None = None 

