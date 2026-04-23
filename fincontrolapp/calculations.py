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





#sim
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


#sim1

# ПРАВКА 1: поменяли порядок — days_to_salary перед daily_avg_expense
def sim_purchase(balance: float, purchase_amount: float, days_to_salary: int, daily_avg_expense: float) -> dict:
    """
    Симулятор покупки: хватит ли денег и на сколько дней хватит остатка до зарплаты.

    Параметры:
        balance: текущий баланс пользователя
        purchase_amount: сумма покупки
        days_to_salary: количество дней до следующей зарплаты (целое, >0)
        daily_avg_expense: среднедневные траты (руб./день)

    Возвращает словарь:
        {
            "can_afford": bool,
            "message": str,
            "remaining_after_purchase": float,
            "days_covered": int | None
        }
    """
    if balance < purchase_amount:
        deficit = purchase_amount - balance
        return {
            "can_afford": False,
            "message": f" Не хватает {deficit:.2f} ₽. Покупка невозможна.",
            "remaining_after_purchase": balance - purchase_amount,
            "days_covered": None
        }

    remaining = balance - purchase_amount
    if daily_avg_expense <= 0:
        days_covered = 0
    else:
        days_covered = int(remaining // daily_avg_expense)

    if days_covered >= days_to_salary:
        extra = days_covered - days_to_salary
        message = f" Денег хватит до зарплаты и ещё на {extra} дней."
    elif days_covered > 0:
        shortfall = days_to_salary - days_covered
        message = f" Денег хватит только на {days_covered} дней. До зарплаты не хватит на {shortfall} дней."
    else:
        message = f" После покупки денег не останется. До зарплаты придётся обходиться без трат."

    return {
        "can_afford": True,
        "message": message,
        "remaining_after_purchase": remaining,
        "days_covered": days_covered
    }


#sim2

def sim_goal_impact(goal_target: float, current_savings: float, monthly_savings: float, purchase_amount: float) -> dict:
    """
    Симулятор: на сколько месяцев отодвинется цель при покупке.

    Параметры:
        goal_target: желаемая сумма цели
        current_savings: текущие накопления под цель
        monthly_savings: ежемесячная сумма откладывания (руб./мес)
        purchase_amount: сумма покупки (оплачивается из накоплений)

    Возвращает словарь:
        {
            "can_afford": bool,
            "current_months": int | None,
            "new_months": int | None,
            "delay_months": int | None,
            "message": str
        }
    """
    if goal_target <= current_savings:
        return {
            "can_afford": True,
            "current_months": 0,
            "new_months": 0,
            "delay_months": 0,
            "message": "Цель уже достигнута. Покупка не повлияет."
        }

    if monthly_savings <= 0:
        return {
            "can_afford": True,
            "current_months": None,
            "new_months": None,
            "delay_months": None,
            "message": "Невозможно рассчитать: не задана сумма ежемесячных сбережений."
        }

    remaining_current = goal_target - current_savings
    current_months = math.ceil(remaining_current / monthly_savings)

    if purchase_amount > current_savings:
        deficit = purchase_amount - current_savings
        return {
            "can_afford": False,
            "current_months": current_months,
            "new_months": None,
            "delay_months": None,
            "message": f" Недостаточно накоплений для покупки. Не хватает {deficit:.2f} ₽."
        }

    new_savings = current_savings - purchase_amount
    remaining_new = goal_target - new_savings
    new_months = math.ceil(remaining_new / monthly_savings)
    delay_months = new_months - current_months

    if delay_months == 0:
        message = "Цель не отодвинется (или отодвинется менее чем на месяц)."
    elif delay_months == 1:
        message = f"Цель отодвинется на 1 месяц (было {current_months} мес., станет {new_months} мес.)."
    else:
        message = f"Цель отодвинется на {delay_months} месяцев (было {current_months} мес., станет {new_months} мес.)."

    return {
        "can_afford": True,
        "current_months": current_months,
        "new_months": new_months,
        "delay_months": delay_months,
        "message": message
    }


#sim3

def sim_new_subscription(income: float, fixed_expenses: float, current_subs: float, new_sub_cost: float) -> dict:
    """
    Симулятор: как новая подписка изменит свободный остаток и его норму (old_rate / new_rate).

    Параметры:
        income: ежемесячный доход
        fixed_expenses: обязательные расходы без учёта подписок
        current_subs: текущая сумма подписок в месяц
        new_sub_cost: стоимость новой подписки в месяц

    Возвращает словарь:
        {
            "old_free": float,
            "new_free": float,
            "old_rate": float,  # доля свободных денег от дохода (0..1)
            "new_rate": float,  # доля свободных денег от дохода (0..1)
            "delta": float,     # new_rate - old_rate (≤ 0)
            "message": str
        }
    """
    if income <= 0:
        return {
            "old_free": 0.0,
            "new_free": 0.0,
            "old_rate": 0.0,
            "new_rate": 0.0,
            "delta": 0.0,
            "message": "Доход не задан. Невозможно рассчитать."
        }

    old_free = income - fixed_expenses - current_subs
    # ПРАВКА 2: old_rate и new_rate — доля (0..1), не проценты
    # форматирование в % делается в SimulatorPage
    old_rate = old_free / income
    new_free = old_free - new_sub_cost
    new_rate = new_free / income
    delta = new_rate - old_rate

    if new_free < 0:
        warning = " Внимание: свободный остаток становится отрицательным!"
    else:
        warning = ""

    message = (f"Текущий свободный остаток: {old_free:.2f} ₽ ({old_rate * 100:.1f}% от дохода)\n"
               f"После добавления подписки: {new_free:.2f} ₽ ({new_rate * 100:.1f}% от дохода)"
               f"{warning}")

    return {
        "old_free": old_free,
        "new_free": new_free,
        "old_rate": old_rate,
        "new_rate": new_rate,
        "delta": delta,
        "message": message
    }


#sim4

# ПРАВКА 3: сигнатура приведена к задачнику
# было: (goal_target, current_savings, monthly_savings, total_expenses, category_share, cut_percent)
# стало: (monthly_expense, category_share, cut_pct, goal_remaining, income)
def sim_cut_category(monthly_expense: float, category_share: float, cut_pct: float,
                     goal_remaining: float, income: float) -> dict:
    """
    Симулятор: сокращение расходов в одной категории и ускорение достижения цели.

    Параметры:
        monthly_expense: общие ежемесячные расходы (все категории)
        category_share:  доля сокращаемой категории в общих расходах (0..1)
        cut_pct:         процент сокращения расходов в этой категории (0..100)
        goal_remaining:  сколько осталось накопить до цели (goal_target - current_savings)
        income:          ежемесячный доход

    Возвращает словарь:
        {
            "savings_per_month": float,
            "new_monthly_savings": float,
            "current_months": int | None,
            "new_months": int | None,
            "months_saved": int | None,
            "message": str
        }
    """
    monthly_savings = income - monthly_expense

    if goal_remaining <= 0:
        return {
            "savings_per_month": 0.0,
            "new_monthly_savings": monthly_savings,
            "current_months": 0,
            "new_months": 0,
            "months_saved": 0,
            "message": "Цель уже достигнута. Сокращение расходов не требуется."
        }

    if monthly_savings <= 0:
        return {
            "savings_per_month": 0.0,
            "new_monthly_savings": monthly_savings,
            "current_months": None,
            "new_months": None,
            "months_saved": None,
            "message": "Невозможно рассчитать: не задана сумма ежемесячных сбережений."
        }

    if monthly_expense <= 0:
        return {
            "savings_per_month": 0.0,
            "new_monthly_savings": monthly_savings,
            "current_months": None,
            "new_months": None,
            "months_saved": None,
            "message": "Нет регулярных расходов для сокращения."
        }

    category_expense = monthly_expense * category_share
    savings = category_expense * (cut_pct / 100.0)
    new_monthly_savings = monthly_savings + savings

    current_months = math.ceil(goal_remaining / monthly_savings)
    new_months = math.ceil(goal_remaining / new_monthly_savings) if new_monthly_savings > 0 else None

    if new_months is None:
        months_saved = None
        message = "После сокращения расходов вы перестанете откладывать – цель станет недостижимой."
    else:
        months_saved = current_months - new_months
        if months_saved == 0:
            message = f"Экономия {savings:.2f} ₽ в месяц не ускоряет достижение цели (изменение менее месяца)."
        elif months_saved == 1:
            message = f"Цель будет достигнута на 1 месяц раньше (вместо {current_months} → {new_months} мес.)."
        else:
            message = f"Цель будет достигнута на {months_saved} месяцев раньше (вместо {current_months} → {new_months} мес.)."

    return {
        "savings_per_month": savings,
        "new_monthly_savings": new_monthly_savings,
        "current_months": current_months,
        "new_months": new_months,
        "months_saved": months_saved,
        "message": message
    }
