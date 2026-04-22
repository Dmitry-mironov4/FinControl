"""
SimulatorController — прослойка между SimulatorPage и calculations.py.
Преобразует результаты sim_* функций в список метрик для рендера.
"""
from calculations import goal_analysis, sim_new_subscription, sim_cut_category


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
        monthly_surplus = monthly_income - monthly_expenses

        if monthly_surplus <= 0:
            return {
                "status": "error",
                "metrics": [
                    {"label": "Ежемесячный остаток", "value": _m(monthly_surplus), "tone": "bad"},
                    {"label": "Накопить невозможно — доход ≤ расходов", "value": "—", "tone": "bad"},
                ],
            }

        if current_savings >= cost:
            return {
                "status": "ok",
                "metrics": [
                    {"label": "Уже накоплено достаточно!", "value": _m(current_savings), "tone": "good"},
                    {"label": "Ежемесячный остаток", "value": _m(monthly_surplus), "tone": "good"},
                ],
            }

        months = goal_analysis(cost, current_savings, monthly_surplus)
        remaining = cost - current_savings
        status = "ok" if months <= 6 else "warning"
        tone = "good" if status == "ok" else "warn"

        projection = [
            min(cost, monthly_surplus * (i + 1) + current_savings)
            for i in range(months)
        ]
        return {
            "status": status,
            "metrics": [
                {"label": "Срок накопления", "value": _mo(months), "tone": tone},
                {"label": "Ежемесячный остаток", "value": _m(monthly_surplus), "tone": "neutral"},
                {"label": "Ещё не хватает", "value": _m(remaining), "tone": "neutral"},
            ],
            "projection": projection,
        }

    # ── Подписка ──────────────────────────────────────────────────────────────

    def simulate_subscription(self, subscription_cost, monthly_income,
                               monthly_expenses, months=12):
        # current_subs=0: пользователь вводит «прочие расходы» без подписок
        r = sim_new_subscription(monthly_income, monthly_expenses, 0, subscription_cost)

        if r["new_free"] < 0:
            status = "error"
        elif monthly_income > 0 and r["new_rate"] < 0.1:
            status = "warning"
        else:
            status = "ok"

        tone_new = {"ok": "good", "warning": "warn", "error": "bad"}[status]
        total_cost = subscription_cost * months
        projection = [r["new_free"] * (i + 1) for i in range(months)]

        return {
            "status": status,
            "metrics": [
                {"label": "Свободно сейчас / мес.", "value": _m(r["old_free"]), "tone": "neutral"},
                {"label": "Свободно с подпиской / мес.", "value": _m(r["new_free"]), "tone": tone_new},
                {"label": f"Потрачено за {_mo(months)}", "value": _m(total_cost), "tone": "bad"},
            ],
            "projection": projection,
        }

    # ── Цель ──────────────────────────────────────────────────────────────────

    def simulate_goal(self, goal_amount, monthly_income, monthly_expenses,
                      current_savings=0.0):
        monthly_surplus = monthly_income - monthly_expenses
        progress_pct = (current_savings / goal_amount * 100) if goal_amount > 0 else 0.0

        if monthly_surplus <= 0:
            return {
                "status": "error",
                "metrics": [
                    {"label": "Ежемесячный остаток", "value": _m(monthly_surplus), "tone": "bad"},
                    {"label": "Прогресс цели", "value": _pct(progress_pct), "tone": "warn"},
                    {"label": "Цель недостижима — доход ≤ расходов", "value": "—", "tone": "bad"},
                ],
            }

        months = goal_analysis(goal_amount, current_savings, monthly_surplus)

        if months == 0:
            return {
                "status": "ok",
                "metrics": [
                    {"label": "Цель уже достигнута!", "value": _m(current_savings), "tone": "good"},
                    {"label": "Прогресс", "value": _pct(progress_pct), "tone": "good"},
                ],
            }

        status = "ok" if months <= 12 else "warning"
        tone = "good" if status == "ok" else "warn"
        projection = [
            min(goal_amount, monthly_surplus * (i + 1) + current_savings)
            for i in range(months)
        ]
        return {
            "status": status,
            "metrics": [
                {"label": "Срок до цели", "value": _mo(months), "tone": tone},
                {"label": "Ежемесячный остаток", "value": _m(monthly_surplus), "tone": "neutral"},
                {"label": "Прогресс", "value": _pct(progress_pct), "tone": "neutral"},
            ],
            "projection": projection,
        }

    # ── Урезать ───────────────────────────────────────────────────────────────

    def simulate_cut(self, monthly_income, current_expenses, cut_percent, months=12):
        # category_share=1.0 — урезаем все расходы целиком
        # goal_remaining=monthly_income — условная цель (накопить месячный доход)
        r = sim_cut_category(
            monthly_expense=current_expenses,
            category_share=1.0,
            cut_pct=cut_percent,
            goal_remaining=monthly_income,
            income=monthly_income,
        )

        saved_monthly = r["savings_per_month"]
        new_free = r["new_monthly_savings"]
        new_expenses = current_expenses - saved_monthly
        total_extra = saved_monthly * months

        if new_free < 0:
            status = "error"
        elif monthly_income > 0 and new_free / monthly_income < 0.05:
            status = "warning"
        else:
            status = "ok"

        tone = {"ok": "good", "warning": "warn", "error": "bad"}[status]
        projection = [saved_monthly * (i + 1) for i in range(months)]

        return {
            "status": status,
            "metrics": [
                {"label": "Экономия в месяц", "value": _m(saved_monthly), "tone": "good"},
                {"label": f"Накоплено за {_mo(months)}", "value": _m(total_extra), "tone": tone},
                {"label": "Новые расходы / мес.", "value": _m(new_expenses), "tone": "neutral"},
                {"label": "Свободно после сокращения", "value": _m(new_free), "tone": tone},
            ],
            "projection": projection,
        }
