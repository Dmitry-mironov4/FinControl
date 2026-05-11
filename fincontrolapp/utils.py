"""Общие утилиты приложения."""

CURRENCY_SYMBOLS = {
    "RUB": "₽",
    "USD": "$",
    "EUR": "€",
    "CNY": "¥",
    "GBP": "£",
    "KZT": "₸",
    "BYN": "Br",
}

CURRENCY_LABELS = {
    "RUB": "Рубль (₽)",
    "USD": "Доллар ($)",
    "EUR": "Евро (€)",
    "CNY": "Юань (¥)",
    "GBP": "Фунт (£)",
    "KZT": "Тенге (₸)",
    "BYN": "Рубль (Br)",
}


def get_currency_symbol(page) -> str:
    """Возвращает символ выбранной пользователем валюты (по умолчанию ₽)."""
    if page is None:
        return "₽"
    code = (page.data or {}).get("_s_currency", "RUB")
    return CURRENCY_SYMBOLS.get(code, "₽")


def rub_to_display(amount_rub: float, page) -> float:
    """Конвертирует рублёвую сумму из БД в отображаемую валюту."""
    if page is None:
        return amount_rub
    data = page.data or {}
    currency = data.get("_s_currency", "RUB")
    conv_mode = data.get("_s_currency_conv", "as_is")
    if currency == "RUB" or conv_mode != "convert":
        return amount_rub
    try:
        from currency import fetch_rates
        rates = fetch_rates()
        rate = rates.get(currency) if rates else None
        if rate and rate > 0:
            return round(amount_rub / rate, 2)
    except Exception:
        pass
    return amount_rub


def format_amount(amount_rub: float, page, prefix: str = "") -> str:
    """Форматирует сумму с нужным символом валюты.

    Пример: format_amount(9041, page, "+ ") → "+ 100.00 $" (USD convert)
                                              → "+ 9 041 ₽"  (RUB)
    """
    disp = rub_to_display(amount_rub, page)
    sym = get_currency_symbol(page)
    data = (page.data or {}) if page else {}
    currency = data.get("_s_currency", "RUB")
    if currency == "RUB":
        return f"{prefix}{disp:,.0f} {sym}"
    return f"{prefix}{disp:,.2f} {sym}"


def input_to_rub(amount: float, page) -> float:
    """Конвертирует введённую пользователем сумму в рубли для сохранения в БД.

    Если выбрана иностранная валюта + режим 'convert' — умножает на курс ЦБ.
    Если курс недоступен или режим 'as_is' — возвращает amount без изменений.
    """
    if page is None:
        return amount
    data = page.data or {}
    currency = data.get("_s_currency", "RUB")
    conv_mode = data.get("_s_currency_conv", "as_is")
    if currency == "RUB" or conv_mode != "convert":
        return amount
    try:
        from currency import fetch_rates
        rates = fetch_rates()
        rate = rates.get(currency) if rates else None
        if rate and rate > 0:
            return round(amount * rate, 2)
    except Exception:
        pass
    return amount
