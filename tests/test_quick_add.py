"""
Тесты для функции parse_quick_input из bot/handlers/quick_add.py
Запуск: pytest tests/test_quick_add.py -v
"""
import pytest
from bot.handlers.quick_add import parse_quick_input


@pytest.mark.parametrize("text, expected", [
    # 1. Категория с запятой как разделитель
    (
        "+500 Еда, поели в маке",
        {"amount": 500.0, "tx_type": "income", "category_raw": "Еда", "description": "поели в маке"},
    ),
    # 2. Категория с двоеточием как разделитель
    (
        "+500 Еда: поели в маке",
        {"amount": 500.0, "tx_type": "income", "category_raw": "Еда", "description": "поели в маке"},
    ),
    # 3. Только категория — без описания
    (
        "+500 кофе",
        {"amount": 500.0, "tx_type": "income", "category_raw": "кофе", "description": ""},
    ),
    # 4. Тире (em-dash) между категорией и описанием, расход
    (
        "-1200 Транспорт — метро",
        {"amount": 1200.0, "tx_type": "expense", "category_raw": "Транспорт", "description": "метро"},
    ),
    # 5. Категория и описание через пробел, без знаков препинания
    (
        "+500 Еда поели в маке",
        {"amount": 500.0, "tx_type": "income", "category_raw": "Еда", "description": "поели в маке"},
    ),
    # 6. Дробная сумма (через запятую) + расход
    (
        "-99,50 Развлечения кино с другом",
        {"amount": 99.5, "tx_type": "expense", "category_raw": "Развлечения", "description": "кино с другом"},
    ),
    # 7. Дробная сумма (через точку)
    (
        "+15000.50 Зарплата аванс",
        {"amount": 15000.5, "tx_type": "income", "category_raw": "Зарплата", "description": "аванс"},
    ),
    # Edge: нет знака «+» или «-» — невалидный ввод
    (
        "500 кофе",
        None,
    ),
    # Edge: знак есть, но нет категории — невалидный ввод
    (
        "+500",
        None,
    ),
])
def test_parse_quick_input(text: str, expected):
    result = parse_quick_input(text)
    assert result == expected
