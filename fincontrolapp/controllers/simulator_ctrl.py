"""
SimulatorController — прослойка между SimulatorPage и calculations.py.
Преобразует «сырые» float-результаты в список метрик для рендера.
"""
from calculations import calc_purchase, calc_subscription, calc_goal, calc_cut


# ── formatters ────────────────────────────────────────────────────────────────

def _m(v: float) -> str:
    return f"{v:,.0f} ₽".replace(",", "\u202f")   # тонкий пробел как разделитель тысяч


def _mo(v: int) -> str:
    return f"{v} мес."


def _pct(v: float) -> str:
    return f"{v:.1f}%"


# ── controller ────────────────────────────────────────────────────────────────

class SimulatorController:
    """
    Все методы возвращают dict:
        {
            "status":  "ok" | "warning" | "error",
            "metrics": [{"label": str, "value": str, "tone": str}, ...],
            "projection": [float, ...]   # опционально
        }

    tone ∈ {"neutral", "good", "warn", "bad"}
    """

    # ── Покупка ───────────────────────────────────────────────────────────────

    def simulate_purchase(self, cost, monthly_income, monthly_expenses,
                          current_savings=0.0):
        r = calc_purchase(cost, monthly_income, monthly_expenses, current_savings)
        status = r["status"]

        if status == "error":
            return {
                "status": "error",
                "metrics": [
                    {"label": "Ежемесячный остаток", "value": _m(r["monthly_savings"]), "tone": "bad"},
                    {"label": "Накопить невозможно — доход ≤ расходов", "value": "—", "tone": "bad"},
                ],
            }

        if r["months"] == 0:
            return {
                "status": "ok",
                "metrics": [
                    {"label": "Уже накоплено достаточно!", "value": _m(current_savings), "tone": "good"},
                    {"label": "Ежемесячный остаток", "value": _m(r["monthly_savings"]), "tone": "good"},
                ],
            }

        tone = "good" if status == "ok" else "warn"
        projection = [
            min(cost, r["monthly_savings"] * (i + 1) + current_savings)
            for i in range(r["months"])
        ]
        return {
            "status": status,
            "metrics": [
                {"label": "Срок накопления", "value": _mo(r["months"]), "tone": tone},
                {"label": "Ежемесячный остаток", "value": _m(r["monthly_savings"]), "tone": "neutral"},
                {"label": "Ещё не хватает", "value": _m(r["remaining"]), "tone": "neutral"},
            ],
            "projection": projection,
        }

    # ── Подписка ──────────────────────────────────────────────────────────────

    def simulate_subscription(self, subscription_cost, monthly_income,
                               monthly_expenses, months=12):
        r = calc_subscription(subscription_cost, monthly_income, monthly_expenses, months)
        status = r["status"]

        tone_new = {"ok": "good", "warning": "warn", "error": "bad"}[status]
        return {
            "status": status,
            "metrics": [
                {"label": "Свободно сейчас / мес.", "value": _m(r["monthly_free_now"]), "tone": "neutral"},
                {"label": "Свободно с подпиской / мес.", "value": _m(r["monthly_free_with_sub"]), "tone": tone_new},
                {"label": f"Потрачено за {_mo(months)}", "value": _m(r["total_cost"]), "tone": "bad"},
            ],
            "projection": r["projection"],
        }

    # ── Цель ──────────────────────────────────────────────────────────────────

    def simulate_goal(self, goal_amount, monthly_income, monthly_expenses,
                      current_savings=0.0):
        r = calc_goal(goal_amount, monthly_income, monthly_expenses, current_savings)
        status = r["status"]

        if status == "error":
            return {
                "status": "error",
                "metrics": [
                    {"label": "Ежемесячный остаток", "value": _m(r["monthly_savings"]), "tone": "bad"},
                    {"label": "Прогресс цели", "value": _pct(r["progress_pct"]), "tone": "warn"},
                    {"label": "Цель недостижима — доход ≤ расходов", "value": "—", "tone": "bad"},
                ],
            }

        if r["months"] == 0:
            return {
                "status": "ok",
                "metrics": [
                    {"label": "Цель уже достигнута!", "value": _m(current_savings), "tone": "good"},
                    {"label": "Прогресс", "value": _pct(r["progress_pct"]), "tone": "good"},
                ],
            }

        tone = "good" if status == "ok" else "warn"
        projection = [
            min(goal_amount, r["monthly_savings"] * (i + 1) + current_savings)
            for i in range(r["months"])
        ]
        return {
            "status": status,
            "metrics": [
                {"label": "Срок до цели", "value": _mo(r["months"]), "tone": tone},
                {"label": "Ежемесячный остаток", "value": _m(r["monthly_savings"]), "tone": "neutral"},
                {"label": "Прогресс", "value": _pct(r["progress_pct"]), "tone": "neutral"},
            ],
            "projection": projection,
        }

    # ── Урезать ───────────────────────────────────────────────────────────────

    def simulate_cut(self, monthly_income, current_expenses, cut_percent, months=12):
        r = calc_cut(monthly_income, current_expenses, cut_percent, months)
        status = r["status"]

        tone = {"ok": "good", "warning": "warn", "error": "bad"}[status]
        return {
            "status": status,
            "metrics": [
                {"label": "Экономия в месяц", "value": _m(r["saved_monthly"]), "tone": "good"},
                {"label": f"Накоплено за {_mo(months)}", "value": _m(r["total_extra"]), "tone": tone},
                {"label": "Новые расходы / мес.", "value": _m(r["new_expenses"]), "tone": "neutral"},
                {"label": "Свободно после сокращения", "value": _m(r["new_free"]), "tone": tone},
            ],
            "projection": r["projection"],
        }
