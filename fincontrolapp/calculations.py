import math

def savings_rate(income, expense):
    if income == 0:
        return 0.0
    return (income - expense) / income * 100.0

def moving_average(values, n):
    if not values:
        return 0.0
    window = values[-n:] if len(values) >= n else values
    return sum(window) / len(window)

def linear_forecast(values, steps):
    n = len(values)
    if n < 2:
        return None
    x = list(range(n))
    y = values
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    b = numerator / denominator if denominator != 0 else 0.0
    a = y_mean - b * x_mean
    forecast = [a + b * (n + i) for i in range(steps)]
    return forecast

def goal_analysis(target, current, monthly_savings):
    if current >= target:
        return 0
    if monthly_savings <= 0:
        return None
    return math.ceil((target - current) / monthly_savings)

def subscription_load(subscriptions_total, income):
    if income == 0:
        return 0.0
    return (subscriptions_total / income) * 100.0


"""
TODO (Настя): заменить заглушки реальными формулами.
Сигнатуры функций и структуры возвращаемых dict менять нельзя —
на них завязаны SimulatorController и SimulatorPage.
"""


def calc_purchase(cost: float, monthly_income: float, monthly_expenses: float,
                  current_savings: float = 0.0) -> dict:
    """
    Сколько месяцев копить на покупку.

    Параметры:
        cost             — стоимость покупки (₽)
        monthly_income   — ежемесячный доход (₽)
        monthly_expenses — ежемесячные расходы (₽)
        current_savings  — уже накоплено (₽), по умолчанию 0

    Возвращает dict с ключами:
        months          — число месяцев (int) или None если копить невозможно
        monthly_savings — свободный остаток в месяц (float)
        remaining       — сколько ещё не хватает (float)
        status          — "ok" | "warning" | "error"
    """
    # TODO (Настя): реализовать формулу
    #   monthly_savings = monthly_income - monthly_expenses
    #   remaining = max(0, cost - current_savings)
    #   если remaining <= 0 → months = 0, status = "ok"
    #   если monthly_savings <= 0 → months = None, status = "error"
    #   иначе → months = ceil(remaining / monthly_savings)
    #   status = "ok" если monthly_savings/monthly_income >= 0.15, иначе "warning"
    raise NotImplementedError("calc_purchase ещё не реализована")


def calc_subscription(subscription_cost: float, monthly_income: float,
                      monthly_expenses: float, months: int = 12) -> dict:
    """
    Как регулярная подписка влияет на бюджет за период.

    Параметры:
        subscription_cost — стоимость подписки в месяц (₽)
        monthly_income    — ежемесячный доход (₽)
        monthly_expenses  — прочие расходы без подписки (₽)
        months            — период анализа в месяцах, по умолчанию 12

    Возвращает dict с ключами:
        monthly_free_now      — свободный остаток без подписки (float)
        monthly_free_with_sub — свободный остаток с подпиской (float)
        total_cost            — суммарные расходы на подписку за период (float)
        months                — период анализа (int)
        status                — "ok" | "warning" | "error"
        projection            — список накоплений по месяцам (list[float], длина = months)
    """
    # TODO (Настя): реализовать формулу
    #   base_free = monthly_income - monthly_expenses
    #   new_free  = base_free - subscription_cost
    #   total_cost = subscription_cost * months
    #   status = "error" если new_free < 0
    #   status = "warning" если new_free/monthly_income < 0.10
    #   иначе status = "ok"
    #   projection = [max(0, new_free) * (i+1) for i in range(months)]
    raise NotImplementedError("calc_subscription ещё не реализована")


def calc_goal(goal_amount: float, monthly_income: float, monthly_expenses: float,
              current_savings: float = 0.0) -> dict:
    """
    Когда будет достигнута финансовая цель.

    Параметры:
        goal_amount      — целевая сумма (₽)
        monthly_income   — ежемесячный доход (₽)
        monthly_expenses — ежемесячные расходы (₽)
        current_savings  — уже накоплено (₽), по умолчанию 0

    Возвращает dict с ключами (все ключи calc_purchase плюс):
        progress_pct    — процент уже накопленного от цели (float, 0–100)
        goal_amount     — целевая сумма (float)
        current_savings — уже накоплено (float)
    """
    # TODO (Настя): реализовать формулу
    #   Вызвать calc_purchase(goal_amount, ...) и добавить три поля:
    #   progress_pct    = current_savings / goal_amount * 100 (если goal_amount > 0)
    #   goal_amount     = goal_amount
    #   current_savings = current_savings
    raise NotImplementedError("calc_goal ещё не реализована")


def calc_cut(monthly_income: float, current_expenses: float,
             cut_percent: float, months: int = 12) -> dict:
    """
    Эффект от сокращения расходов на cut_percent % за период.

    Параметры:
        monthly_income    — ежемесячный доход (₽)
        current_expenses  — текущие расходы (₽)
        cut_percent       — на сколько % сократить расходы (0–100)
        months            — период анализа в месяцах, по умолчанию 12

    Возвращает dict с ключами:
        saved_monthly — экономия в месяц (float)
        new_expenses  — расходы после сокращения (float)
        old_free      — свободный остаток до сокращения (float)
        new_free      — свободный остаток после сокращения (float)
        total_extra   — дополнительные накопления за период (float)
        months        — период анализа (int)
        status        — "ok" | "warning" | "error"
        projection    — список накоплений по месяцам (list[float], длина = months)
    """
    # TODO (Настя): реализовать формулу
    #   new_expenses  = current_expenses * (1 - cut_percent / 100)
    #   saved_monthly = current_expenses - new_expenses
    #   old_free      = monthly_income - current_expenses
    #   new_free      = monthly_income - new_expenses
    #   total_extra   = saved_monthly * months
    #   status = "error"   если new_free <= 0
    #   status = "warning" если new_free/monthly_income < 0.15
    #   иначе status = "ok"
    #   projection = [new_free * (i+1) for i in range(months)]
    raise NotImplementedError("calc_cut ещё не реализована")