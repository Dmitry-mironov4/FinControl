from datetime import datetime

def parse_amount(value: str) -> float:
    """
    Преобразует строку с числом в тип float, удаляя пробелы и заменяя запятую на точку.

    Аргументы:
        value (str): Строка, содержащая число (например, "1 234,56").

    Возвращает:
        float: Числовое значение, преобразованное из строки.

    Исключения:
        ValueError: Если строка не может быть преобразована в число.
    """
    raw = value.replace(" ", "").strip()
    if not raw:
        raise ValueError("Пустая строка не может быть преобразована в число")
    return float(raw.replace(",", "."))


def parse_date(value: str) -> str:
    try:            
        parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        raise ValueError("Введите корректную дату в формате ДД.ММ.ГГГГ")
    return str(parsed_date)