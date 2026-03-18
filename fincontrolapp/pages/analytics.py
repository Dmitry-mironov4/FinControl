"""
analytics.py — Экран аналитики финансов.

Показывает четыре блока:
1. Сводные плашки   — итоги за период: доходы, расходы, экономия, норма сбережений.
2. Столбчатая диаграмма — доходы vs расходы по месяцам (нарисована через ft.Stack).
3. График баланса   — накопленный баланс по месяцам (точки + линии через ft.Stack).
4. Структура расходов — горизонтальные прогресс-бары по категориям.

Почему графики нарисованы вручную:
    Flet 0.82.0 не содержит встроенных chart-виджетов (BarChart, LineChart).
    Они появились в более поздних версиях. Поэтому графики построены
    через ft.Stack с абсолютным позиционированием (параметры left, top).

Как подключить реальные данные:
    Замени константы MONTHLY_DATA и EXPENSE_CATEGORIES в начале файла
    на вызовы функций из модуля работы с БД, например:
        MONTHLY_DATA = db.get_monthly_summary(year=2024)

Константы:
    CHART_H  (int): высота области графика в пикселях.
    LABEL_H  (int): высота строки с подписями месяцев.
    BAR_W    (int): ширина одного столбца диаграммы.
    BAR_GAP  (int): зазор между парой столбцов (доход/расход).
    COL_W    (int): суммарная ширина одной колонки (BAR_W * 2 + BAR_GAP).
"""
import flet as ft
from components.base_page import BasePage


# ─── Тестовые данные (заменить на реальные из БД) ───────────────────────────
MONTHLY_DATA = [
    {"month": "Янв", "income": 85000, "expense": 52000},
    {"month": "Фев", "income": 90000, "expense": 61000},
    {"month": "Мар", "income": 78000, "expense": 45000},
    {"month": "Апр", "income": 95000, "expense": 70000},
    {"month": "Май", "income": 102000, "expense": 68000},
    {"month": "Июн", "income": 88000, "expense": 55000},
]

EXPENSE_CATEGORIES = [
    {"label": "Еда",         "value": 28, "color": "#FF9800"},
    {"label": "Транспорт",   "value": 15, "color": "#2196F3"},
    {"label": "Жильё",       "value": 25, "color": "#795548"},
    {"label": "Развлечения", "value": 12, "color": "#00BCD4"},
    {"label": "Здоровье",    "value": 10, "color": "#F44336"},
    {"label": "Другое",      "value": 10, "color": "#607D8B"},
]

CHART_H   = 160   # высота области баров
LABEL_H   = 20    # высота подписей месяцев
BAR_W     = 13    # ширина одного бара
BAR_GAP   = 3     # зазор между парой баров
COL_W     = BAR_W * 2 + BAR_GAP   # ширина одной колонки (пара баров)
# ─────────────────────────────────────────────────────────────────────────────


def _title(text):
    return ft.Text(text, size=16, weight=ft.FontWeight.W_600, color="#FFFFFF")


def _card(content):
    return ft.Container(
        bgcolor="#1A1A24", border_radius=16, padding=20, content=content,
    )


class AnalyticsPage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Аналитика")

    def build_body(self):
        """
        Собирает тело экрана аналитики из четырёх секций.

        Возвращает:
            ft.Column: прокручиваемая колонка со всеми блоками.
        """
        return ft.Column([
            self._summary(),
            _title("Доходы и расходы по месяцам"),
            _card(self._bar_chart()),
            _title("Динамика баланса"),
            _card(self._balance_chart()),
            _title("Структура расходов"),
            _card(self._category_bars()),
        ], spacing=16)

    # ── Сводные плашки ────────────────────────────────────────────────────────
    def _summary(self):
        """
        Строит блок сводных плашек (4 карточки 2×2).

        Карточки: Доходы, Расходы, Экономия, Норма сбережений.
        Значения берутся из MONTHLY_DATA путём суммирования.

        Возвращает:
            ft.Column: две строки по две карточки.
        """
        total_income  = sum(d["income"]  for d in MONTHLY_DATA)
        total_expense = sum(d["expense"] for d in MONTHLY_DATA)
        savings       = total_income - total_expense
        savings_pct   = round(savings / total_income * 100) if total_income else 0

        def fmt(v):
            return f"{v:,}".replace(",", " ") + " ₽"

        def tile(label, value, color, icon):
            return ft.Container(
                expand=True, bgcolor="#1A1A24", border_radius=14, padding=16,
                content=ft.Column([
                    ft.Row([ft.Icon(icon, color=color, size=18),
                            ft.Text(label, size=12, color="#888888")], spacing=6),
                    ft.Text(fmt(value), size=16, weight=ft.FontWeight.BOLD, color=color),
                ], spacing=6),
            )

        return ft.Column([
            ft.Row([
                tile("Доходы",  total_income,  "#4CAF50", ft.Icons.TRENDING_UP),
                tile("Расходы", total_expense, "#F44336", ft.Icons.TRENDING_DOWN),
            ], spacing=10),
            ft.Row([
                tile("Экономия", savings, "#6C63FF", ft.Icons.SAVINGS_OUTLINED),
                ft.Container(
                    expand=True, bgcolor="#1A1A24", border_radius=14, padding=16,
                    content=ft.Column([
                        ft.Row([ft.Icon(ft.Icons.PERCENT, color="#FF9800", size=18),
                                ft.Text("Норма сбережений", size=12, color="#888888")],
                               spacing=6),
                        ft.ProgressBar(value=savings_pct / 100, bgcolor="#2A2A36",
                                       color="#FF9800", height=8, border_radius=4),
                        ft.Text(f"{savings_pct}% от доходов", size=13, color="#FF9800"),
                    ], spacing=6),
                ),
            ], spacing=10),
        ], spacing=10)

    # ── Столбчатая диаграмма через Stack ─────────────────────────────────────
    def _bar_chart(self):
        """
        Строит столбчатую диаграмму доходов и расходов по месяцам.

        Реализация через ft.Stack с абсолютным позиционированием:
        - Каждый бар — ft.Container с рассчитанной высотой и позицией top/left.
        - Высота бара = (значение / максимум) * CHART_H.
        - Бары растут снизу вверх: top = CHART_H - высота_бара.
        - Горизонтальная сетка — тонкие контейнеры height=1 с bgcolor="#2A2A36".

        Переменные:
            total_w (int): предполагаемая ширина контейнера (~320px для телефона).
            step    (int): шаг между центрами колонок = total_w // n.
            x_center(int): горизонтальный центр текущей колонки.

        Возвращает:
            ft.Column: Stack с барами + строка легенды.
        """
        n       = len(MONTHLY_DATA)
        max_val = max(max(d["income"], d["expense"]) for d in MONTHLY_DATA)

        # Общая ширина: считаем сколько места нужно, потом равномерно распределяем
        # Используем expand + Stack с абсолютными отступами через left
        total_w = 320  # примерная ширина контейнера на телефоне
        step    = total_w // n

        stack_items = []

        # Сетка
        for i in range(5):
            y = int(CHART_H / 4 * i)
            stack_items.append(
                ft.Container(
                    height=1, bgcolor="#2A2A36",
                    left=0, right=0, top=y,
                )
            )

        # Бары
        for i, d in enumerate(MONTHLY_DATA):
            h_inc = max(4, int(d["income"]  / max_val * CHART_H))
            h_exp = max(4, int(d["expense"] / max_val * CHART_H))
            x_center = int(step * i + step / 2)

            # Бар доходов
            stack_items.append(ft.Container(
                width=BAR_W, height=h_inc,
                bgcolor="#4CAF50",
                border_radius=ft.BorderRadius(
                    top_left=3, top_right=3, bottom_left=0, bottom_right=0),
                left=x_center - BAR_W - BAR_GAP // 2,
                top=CHART_H - h_inc,
            ))
            # Бар расходов
            stack_items.append(ft.Container(
                width=BAR_W, height=h_exp,
                bgcolor="#F44336",
                border_radius=ft.BorderRadius(
                    top_left=3, top_right=3, bottom_left=0, bottom_right=0),
                left=x_center + BAR_GAP // 2,
                top=CHART_H - h_exp,
            ))
            # Подпись месяца
            stack_items.append(ft.Container(
                content=ft.Text(d["month"], size=10, color="#888888",
                                text_align=ft.TextAlign.CENTER),
                width=40,
                left=x_center - 20,
                top=CHART_H + 6,
            ))

        return ft.Column([
            ft.Container(
                height=CHART_H + LABEL_H + 10,
                content=ft.Stack(stack_items, expand=True),
            ),
            ft.Row([
                ft.Row([
                    ft.Container(width=12, height=12, bgcolor="#4CAF50", border_radius=3),
                    ft.Text("Доходы", size=12, color="#888888"),
                ], spacing=6),
                ft.Row([
                    ft.Container(width=12, height=12, bgcolor="#F44336", border_radius=3),
                    ft.Text("Расходы", size=12, color="#888888"),
                ], spacing=6),
            ], spacing=20),
        ], spacing=8)

    # ── График баланса через Stack ────────────────────────────────────────────
    def _balance_chart(self):
        """
        Строит линейный график накопленного баланса.

        Алгоритм:
            1. Считаем накопленный баланс: balance += income - expense для каждого месяца.
            2. Нормируем значения в диапазон [0, CHART_H] через функцию norm_y().
            3. Рисуем горизонтальные линии сетки.
            4. Соединяем соседние точки горизонтальными сегментами (упрощённая линия).
            5. Рисуем точки (кружки) и подписи значений над ними.

        norm_y(v) — переводит значение баланса в координату top:
            top = 0 означает верх контейнера (большие значения),
            top = CHART_H означает низ (маленькие значения).

        Возвращает:
            ft.Container: контейнер фиксированной высоты со Stack внутри.
        """
        balance = 0
        balances = []
        for d in MONTHLY_DATA:
            balance += d["income"] - d["expense"]
            balances.append(balance)

        n     = len(balances)
        max_b = max(balances)
        min_b = min(balances)
        rng   = max_b - min_b or 1

        total_w = 320
        step    = total_w // n

        def norm_y(v):
            # возвращает top (0 = верх, CHART_H = низ)
            return CHART_H - int((v - min_b) / rng * (CHART_H - 20)) - 10

        stack_items = []

        # Сетка
        for i in range(4):
            stack_items.append(ft.Container(
                height=1, bgcolor="#2A2A36",
                left=0, right=0,
                top=int(CHART_H / 3 * i),
            ))

        # Линия между точками
        for i in range(n - 1):
            x1 = int(step * i + step / 2)
            x2 = int(step * (i + 1) + step / 2)
            y1 = norm_y(balances[i])
            y2 = norm_y(balances[i + 1])
            y_top  = min(y1, y2)
            y_bot  = max(y1, y2)
            seg_h  = max(2, y_bot - y_top)
            seg_w  = x2 - x1

            stack_items.append(ft.Container(
                width=seg_w, height=2,
                bgcolor="#6C63FF",
                left=x1,
                top=int((y1 + y2) / 2),
            ))

        # Точки и подписи
        for i, (b, d) in enumerate(zip(balances, MONTHLY_DATA)):
            x = int(step * i + step / 2)
            y = norm_y(b)

            # Точка
            stack_items.append(ft.Container(
                width=10, height=10,
                bgcolor="#6C63FF",
                border_radius=5,
                border=ft.border.all(2, "#FFFFFF"),
                left=x - 5,
                top=y - 5,
            ))
            # Значение над точкой
            stack_items.append(ft.Container(
                content=ft.Text(f"{b // 1000}к", size=9, color="#6C63FF",
                                text_align=ft.TextAlign.CENTER),
                width=36, left=x - 18,
                top=max(0, y - 20),
            ))
            # Подпись месяца снизу
            stack_items.append(ft.Container(
                content=ft.Text(d["month"], size=10, color="#888888",
                                text_align=ft.TextAlign.CENTER),
                width=36, left=x - 18,
                top=CHART_H + 4,
            ))

        return ft.Container(
            height=CHART_H + LABEL_H + 10,
            content=ft.Stack(stack_items, expand=True),
        )

    # ── Горизонтальные бары категорий ─────────────────────────────────────────
    def _category_bars(self):
        """
        Строит блок горизонтальных прогресс-баров по категориям расходов.

        Каждая строка содержит:
            - Название категории (слева)
            - Процент от общих расходов (справа, цветной)
            - ft.ProgressBar шириной во всю карточку

        Данные берутся из константы EXPENSE_CATEGORIES.

        Возвращает:
            ft.Column: список строк с прогресс-барами.
        """
        rows = []
        for cat in EXPENSE_CATEGORIES:
            rows.append(ft.Column([
                ft.Row([
                    ft.Text(cat["label"], size=13, color="#CCCCCC", expand=True),
                    ft.Text(f"{cat['value']}%", size=13, color=cat["color"],
                            weight=ft.FontWeight.W_600),
                ]),
                ft.ProgressBar(value=cat["value"] / 100, bgcolor="#2A2A36",
                               color=cat["color"], height=8, border_radius=4),
            ], spacing=6))
        return ft.Column(rows, spacing=14)