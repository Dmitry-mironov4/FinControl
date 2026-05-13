import datetime

MONTH_NAMES = [
    "", "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]
MONTH_SHORT = [
    "", "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
]


def fmt_amount(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def format_balance(balance) -> str:
    if isinstance(balance, dict):
        val = balance.get("balance", 0)
    else:
        val = float(balance)
    formatted = f"{abs(val):,.0f}".replace(",", " ")
    if val < 0:
        return f"💰 Баланс: -{formatted}₽"
    return f"💰 Баланс: {formatted}₽"


def format_transaction(t) -> str:
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    try:
        tx_date = datetime.date.fromisoformat(t["date"])
        if tx_date == today:
            date_str = "сегодня"
        elif tx_date == yesterday:
            date_str = "вчера"
        else:
            date_str = tx_date.strftime("%d.%m")
    except (ValueError, TypeError):
        date_str = str(t["date"] or "")

    amount = float(t["amount"])
    category = t["category_name"] or ""
    description = t["description"] or ""

    if t["type"] == "income":
        emoji = "📈"
        sign = "+"
    else:
        emoji = "📉"
        sign = "-"

    amount_str = f"{amount:,.0f}".replace(",", " ")
    parts = [f"{sign}{amount_str}₽", category]
    if description:
        parts.append(description)
    parts.append(date_str)

    return f"{emoji} {' · '.join(parts)}"
