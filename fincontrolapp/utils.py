"""Общие утилиты приложения."""

CURRENCY_SYMBOLS = {
    "RUB": "₽",
    "USD": "$",
    "EUR": "€",
    "KZT": "₸",
    "BYN": "Br",
}

CURRENCY_LABELS = {
    "RUB": "Рубль (₽)",
    "USD": "Доллар ($)",
    "EUR": "Евро (€)",
    "KZT": "Тенге (₸)",
    "BYN": "Рубль (Br)",
}


def get_currency_symbol(page) -> str:
    """Возвращает символ выбранной пользователем валюты (по умолчанию ₽)."""
    if page is None:
        return "₽"
    code = (page.data or {}).get("_s_currency", "RUB")
    return CURRENCY_SYMBOLS.get(code, "₽")
