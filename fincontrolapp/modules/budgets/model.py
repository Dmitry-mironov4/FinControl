from dataclasses import dataclass
from typing import Optional


@dataclass
class Budget:
    id: Optional[int]
    user_id: int
    category_id: int
    category_name: str        # денормализовано для удобства UI
    limit_amount: float
    spent_amount: float = 0.0  # вычисляется при загрузке, не хранится в БД
    period: str = 'monthly'

    @property
    def progress_pct(self) -> float:
        """Процент использования лимита (0–100+)."""
        if self.limit_amount <= 0:
            return 0.0
        return self.spent_amount / self.limit_amount * 100

    @property
    def status_color(self) -> str:
        """Цвет индикатора: зелёный < 70%, жёлтый 70–90%, красный > 90%."""
        pct = self.progress_pct
        if pct < 70:
            return "#00B487"   # зелёный
        if pct < 90:
            return "#FFC549"   # жёлтый
        return "#FF4444"       # красный