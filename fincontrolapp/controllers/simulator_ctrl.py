"""
SimulatorController — прослойка между SimulatorPage и calculations.py.
"""
from calculations import sim_purchase, sim_new_subscription, sim_goal_impact, sim_cut_category


def _m(v: float) -> str:
    return f"{v:,.0f} ₽"

def _mo(v: int) -> str:
    return f"{v} мес."

def _pct(v: float) -> str:
    return f"{v:.1f}%"


class SimulatorController:

    # ── Покупка ───────────────────────────────────────────────────────────────
    # sim_purchase(balance, purchase_amount, days_to_salary, daily_avg_expense)

    def simulate_purchase(self, cost, monthly_income, monthly_expenses,
                          current_savings=0.0):
        daily_avg = monthly_expenses / 30
        days_to_salary = 30
        r = sim_purchase(
            balance=current_savings,
            purchase_amount=cost,
            days_to_salary=days_to_salary,
            daily_avg_expense=daily_avg,
        )
        monthly_free = monthly_income - monthly_expenses
        status = "ok" if r["can_afford"] else "error"
        if not r["can_afford"]:
            return {
                "status": "error",
                "metrics": [
                    {"label": "Не хватает", "value": _m(cost - current_savings), "tone": "bad"},
                    {"label": "Текущий баланс", "value": _m(current_savings), "tone": "neutral"},
                    {"label": r["message"], "value": "—", "tone": "bad"},
                ],
            }

        months_needed = max(0, (cost - current_savings) / monthly_free) if monthly_free > 0 else None
        tone = "good" if (months_needed is not None and months_needed <= 6) else "warn"
        projection = []
        if monthly_free > 0 and months_needed:
            projection = [
                min(cost, current_savings + monthly_free * (i + 1))
                for i in range(int(months_needed) + 1)
            ]
        return {
            "status": "ok" if (months_needed is not None and months_needed <= 12) else "warning",
            "metrics": [
                {"label": "Остаток после покупки", "value": _m(r["remaining_after_purchase"]), "tone": tone},
                {"label": "Дней хватит", "value": f"{r['days_covered']} дн." if r["days_covered"] is not None else "—", "tone": tone},
                {"label": "Свободно в месяц", "value": _m(monthly_free), "tone": "neutral"},
            ],
            "projection": projection,
        }

    # ── Подписка ──────────────────────────────────────────────────────────────
    # sim_new_subscription(income, fixed_expenses, current_subs, new_sub_cost)

    def simulate_subscription(self, subscription_cost, monthly_income,
                               monthly_expenses, months=12):
        r = sim_new_subscription(
            income=monthly_income,
            fixed_expenses=monthly_expenses,
            current_subs=0.0,
            new_sub_cost=subscription_cost,
        )
        total_cost = subscription_cost * months
        free_with = r["new_free"] * months
        status = "error" if r["new_free"] < 0 else ("warning" if r["new_rate"] < 0.1 else "ok")
        tone_new = "bad" if r["new_free"] < 0 else ("warn" if r["new_rate"] < 0.1 else "good")
        projection = [r["old_free"] * i - subscription_cost * i for i in range(1, months + 1)]
        return {
            "status": status,
            "metrics": [
                {"label": "Свободно сейчас / мес.", "value": _m(r["old_free"]), "tone": "neutral"},
                {"label": "Свободно с подпиской / мес.", "value": _m(r["new_free"]), "tone": tone_new},
                {"label": f"Потрачено за {_mo(months)}", "value": _m(total_cost), "tone": "bad"},
                {"label": "Доля свободных денег", "value": _pct(r["new_rate"] * 100), "tone": tone_new},
            ],
            "projection": projection,
        }

    # ── Цель ──────────────────────────────────────────────────────────────────
    # sim_goal_impact(goal_target, current_savings, monthly_savings, purchase_amount)

    def simulate_goal(self, goal_amount, monthly_income, monthly_expenses,
                      current_savings=0.0):
        monthly_savings = monthly_income - monthly_expenses
        if monthly_savings <= 0:
            return {
                "status": "error",
                "metrics": [
                    {"label": "Ежемесячный остаток", "value": _m(monthly_savings), "tone": "bad"},
                    {"label": "Цель недостижима — доход ≤ расходов", "value": "—", "tone": "bad"},
                ],
            }
        r = sim_goal_impact(
            goal_target=goal_amount,
            current_savings=current_savings,
            monthly_savings=monthly_savings,
            purchase_amount=0.0,
        )
        progress_pct = (current_savings / goal_amount * 100) if goal_amount > 0 else 0
        months = r.get("current_months") or 0
        status = "ok" if months <= 12 else ("warning" if months <= 36 else "error")
        tone = "good" if months <= 12 else ("warn" if months <= 36 else "bad")
        projection = [
            min(goal_amount, current_savings + monthly_savings * (i + 1))
            for i in range(months or 1)
        ]
        if months == 0:
            return {
                "status": "ok",
                "metrics": [
                    {"label": "Цель уже достигнута!", "value": _m(current_savings), "tone": "good"},
                    {"label": "Прогресс", "value": _pct(progress_pct), "tone": "good"},
                ],
            }
        return {
            "status": status,
            "metrics": [
                {"label": "Срок до цели", "value": _mo(months), "tone": tone},
                {"label": "Ежемесячный остаток", "value": _m(monthly_savings), "tone": "neutral"},
                {"label": "Прогресс", "value": _pct(progress_pct), "tone": "neutral"},
            ],
            "projection": projection,
        }

    # ── Урезать ───────────────────────────────────────────────────────────────
    # sim_cut_category(monthly_expense, category_share, cut_pct, goal_remaining, income)

    def simulate_cut(self, monthly_income, current_expenses, cut_percent, months=12):
        r = sim_cut_category(
            monthly_expense=current_expenses,
            category_share=1.0,
            cut_pct=cut_percent,
            goal_remaining=current_expenses * months,
            income=monthly_income,
        )
        status = "ok" if r["months_saved"] and r["months_saved"] > 0 else "warning"
        tone = "good" if status == "ok" else "warn"
        saved_monthly = r["savings_per_month"]
        new_expenses = current_expenses - saved_monthly
        new_free = monthly_income - new_expenses
        projection = [new_free * (i + 1) for i in range(months)]
        return {
            "status": status,
            "metrics": [
                {"label": "Экономия в месяц", "value": _m(saved_monthly), "tone": "good"},
                {"label": f"Доп. накопления за {_mo(months)}", "value": _m(saved_monthly * months), "tone": tone},
                {"label": "Новые расходы / мес.", "value": _m(new_expenses), "tone": "neutral"},
                {"label": "Свободно после сокращения", "value": _m(new_free), "tone": tone},
            ],
            "projection": projection,
        }