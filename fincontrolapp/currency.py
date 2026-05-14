"""Получение курсов валют с API ЦБ РФ (daily_json.js) с кешированием на 1 час.

Использует только стандартную библиотеку Python (urllib + json) — без зависимостей.
"""
import json
import time
import urllib.request

# ─── кеш в памяти ────────────────────────────────────────────────────────────
_CACHE: dict | None = None
_CACHE_TS: float = 0.0
_CACHE_TTL: float = 3600.0  # секунды

SUPPORTED: tuple = ("USD", "EUR", "CNY", "GBP", "KZT", "BYN")
_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


def fetch_rates() -> dict | None:
    """Возвращает словарь курсов к рублю для поддерживаемых валют.

    Пример: {"USD": 90.41, "EUR": 98.12, "CNY": 12.34, "GBP": 114.50}

    Результат кешируется на 1 час. При сетевой ошибке или таймауте
    возвращает None без исключений.
    """
    global _CACHE, _CACHE_TS
    now = time.monotonic()
    if _CACHE is not None and (now - _CACHE_TS) < _CACHE_TTL:
        return _CACHE
    try:
        req = urllib.request.Request(
            _API_URL,
            headers={"User-Agent": "FinControl/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        valute = data.get("Valute", {})
        rates: dict = {}
        for code in SUPPORTED:
            entry = valute.get(code)
            if entry:
                nominal = entry.get("Nominal", 1) or 1
                rates[code] = round(entry["Value"] / nominal, 2)
        _CACHE = rates
        _CACHE_TS = now
        return rates
    except Exception:
        return None
