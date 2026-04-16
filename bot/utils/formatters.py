import datetime


def fmt_amount(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def format_balance(balance: float) -> str:
    formatted = f"{abs(balance):,.0f}".replace(",", " ")
    if balance < 0:
        return f"💰 Баланс: -{formatted}₽"
    return f"💰 Баланс: {formatted}₽"


def format_transaction(t: dict) -> str:
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
        date_str = str(t.get("date", ""))

    amount = float(t["amount"])
    category = t.get("category_name", "")
    description = t.get("description") or ""

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
