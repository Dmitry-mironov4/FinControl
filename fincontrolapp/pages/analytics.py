"""
analytics.py — Экран аналитики финансов.

Показывает четыре блока:
1. Сводные плашки       — итоги за выбранный год: доходы, расходы, экономия, норма сбережений.
2. Столбчатая диаграмма — доходы vs расходы по месяцам (flet_charts BarChart).
3. График баланса       — накопленный баланс по месяцам (flet_charts LineChart).
4. Структура расходов   — горизонтальные прогресс-бары по категориям.

Данные берутся из БД через функции этого же модуля:
    get_monthly_summary(user_id, year)         — суммы доходов/расходов по месяцам.
    get_expense_breakdown_by_year(user_id, year) — разбивка расходов по категориям.
    get_available_years(user_id)               — список лет с транзакциями.

Если данных меньше чем за MIN_MONTHS месяцев — показывается заглушка
«Добавьте хотя бы 2 месяца данных».

Фильтр по году: Dropdown в шапке. При смене года пересчитываются только графики,
структура страницы (навигация, фон, AppBar) не затрагивается.
"""

import flet as ft
from flet_charts import (
    BarChart, BarChartGroup, BarChartRod,
    LineChart, LineChartData, LineChartDataPoint,
    ChartGridLines, ChartAxis, ChartAxisLabel,
)
from datetime import datetime
from database import get_connection
from components.base_page import BasePage


# ─── Константы ───────────────────────────────────────────────────────────────

MONTH_NAMES = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
               "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]

CATEGORY_COLORS = [
    "#FF9800", "#2196F3", "#795548", "#00BCD4",
    "#F44336", "#607D8B", "#4CAF50", "#9C27B0",
]

# Минимум месяцев с данными для отображения графиков
MIN_MONTHS = 2


# ─── DB-функции ──────────────────────────────────────────────────────────────

def get_available_years(user_id: int) -> list[int]:
    """Возвращает отсортированный список лет, за которые есть транзакции."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT DISTINCT strftime('%Y', date) AS y
               FROM transactions
               WHERE user_id = ?
               ORDER BY y""",
            (user_id,),
        ).fetchall()
    years = [int(r["y"]) for r in rows if r["y"]]
    current = datetime.now().year
    if current not in years:
        years.append(current)
    return sorted(years)


def get_monthly_summary(user_id: int, year: int) -> list[dict]:
    """
    Суммы доходов и расходов по каждому месяцу выбранного года.

    Возвращает список словарей:
        month   — короткое название месяца ("Янв", "Фев", …)
        income  — сумма доходов за месяц
        expense — сумма расходов за месяц
    """
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT
                   strftime('%m', date)                                    AS m,
                   SUM(CASE WHEN type='income'  THEN amount ELSE 0 END)   AS income,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END)   AS expense
               FROM transactions
               WHERE user_id = ? AND strftime('%Y', date) = ?
               GROUP BY m
               ORDER BY m""",
            (user_id, str(year)),
        ).fetchall()

    result = []
    for r in rows:
        idx = int(r["m"]) - 1
        result.append({
            "month":   MONTH_NAMES[idx],
            "income":  r["income"]  or 0.0,
            "expense": r["expense"] or 0.0,
        })
    return result


def get_expense_breakdown_by_year(user_id: int, year: int) -> list[dict]:
    """
    Разбивка расходов по категориям за выбранный год.

    Возвращает список словарей:
        label — название категории
        value — доля в % от суммарных расходов
        color — цвет для отображения
    """
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT c.name AS category, SUM(t.amount) AS total
               FROM transactions t
               JOIN categories c ON t.category_id = c.id
               WHERE t.user_id = ?
                 AND t.type = 'expense'
                 AND strftime('%Y', t.date) = ?
               GROUP BY c.id, c.name
               ORDER BY total DESC""",
            (user_id, str(year)),
        ).fetchall()

    total = sum(r["total"] for r in rows) or 0
    if total == 0:
        return []

    return [
        {
            "label": r["category"],
            "value": round(r["total"] / total * 100),
            "color": CATEGORY_COLORS[i % len(CATEGORY_COLORS)],
        }
        for i, r in enumerate(rows)
    ]


# ─── UI-helpers ──────────────────────────────────────────────────────────────

def _title(text: str) -> ft.Text:
    return ft.Text(text, size=16, weight=ft.FontWeight.W_600, color="#FFFFFF")


def _card(content: ft.Control) -> ft.Container:
    return ft.Container(
        bgcolor="#1A1A24", border_radius=16, padding=20, content=content,
    )


def _stub(message: str) -> ft.Container:
    """Заглушка при недостатке данных."""
    return ft.Container(
        height=130,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            [
                ft.Icon(ft.Icons.BAR_CHART_OUTLINED, color="#3A3A50", size=44),
                ft.Text(
                    message,
                    size=13, color="#666677",
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
    )


def _has_enough_data(monthly: list[dict]) -> bool:
    return len(monthly) >= MIN_MONTHS


# ─── AnalyticsPage ───────────────────────────────────────────────────────────

class AnalyticsPage(BasePage):

    def __init__(self, page: ft.Page, user_id: int | None = None):
        self.user_id = user_id
        self.selected_year = datetime.now().year
        super().__init__(page, "Аналитика")

    # ── Построение тела ──────────────────────────────────────────────────────

    def _build_chart_controls(self) -> list[ft.Control]:
        """Собирает все блоки с данными для текущего self.selected_year."""
        monthly    = get_monthly_summary(self.user_id, self.selected_year)
        categories = get_expense_breakdown_by_year(self.user_id, self.selected_year)
        enough     = _has_enough_data(monthly)

        controls = [self._summary(monthly)]

        # Доходы / расходы по месяцам
        controls.append(_title("Доходы и расходы по месяцам"))
        controls.append(
            _card(self._bar_chart(monthly)) if enough
            else _card(_stub("Добавьте хотя бы 2 месяца данных,\nчтобы увидеть диаграмму"))
        )

        # Динамика баланса
        controls.append(_title("Динамика баланса"))
        controls.append(
            _card(self._balance_chart(monthly)) if enough
            else _card(_stub("Добавьте хотя бы 2 месяца данных,\nчтобы увидеть график баланса"))
        )

        # Структура расходов
        controls.append(_title("Структура расходов"))
        controls.append(
            _card(self._category_bars(categories)) if categories
            else _card(_stub("Нет расходов за выбранный год"))
        )

        return controls

    def build_body(self) -> ft.Column:
        years = get_available_years(self.user_id)

        self._charts_col = ft.Column(
            controls=self._build_chart_controls(),
            spacing=10,
        )

        self._year_row = ft.Row(spacing=8)
        self._render_year_buttons(years)

        return ft.Column(
            scroll="vertical",
            spacing=10,
            controls=[
                ft.Row(
                    [ft.Text("Год:", color="#FFFFFF"), self._year_row],
                    spacing=10,
                ),
                self._charts_col,
            ],
        )

    def _render_year_buttons(self, years: list[int]) -> None:
        self._year_row.controls = [
            ft.ElevatedButton(
                str(y),
                on_click=self._make_year_handler(y),
                style=ft.ButtonStyle(
                    bgcolor="#6C63FF" if y == self.selected_year else "#2A2A35",
                    color="#FFFFFF",
                ),
            )
            for y in years
        ]

    def _make_year_handler(self, year: int):
        def handler(e):
            self.selected_year = year
            years = get_available_years(self.user_id)
            self._render_year_buttons(years)
            self._charts_col.controls = self._build_chart_controls()
            self.page_ref.update()
        return handler

    def _on_year_change(self, e: ft.ControlEvent) -> None:
        pass

    # ── Сводные плашки ───────────────────────────────────────────────────────

    def _summary(self, monthly: list[dict]) -> ft.Column:
        total_income  = sum(d["income"]  for d in monthly)
        total_expense = sum(d["expense"] for d in monthly)
        savings       = total_income - total_expense
        savings_pct   = round(savings / total_income * 100) if total_income else 0

        def fmt(v: float) -> str:
            return f"{int(v):,}".replace(",", " ") + " ₽"

        def tile(label, value, color, icon):
            return ft.Container(
                expand=True, bgcolor="#1A1A24", border_radius=14, padding=16,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=color, size=18),
                        ft.Text(label, size=12, color="#888888"),
                    ], spacing=6),
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
                        ft.Row([
                            ft.Icon(ft.Icons.PERCENT, color="#FF9800", size=18),
                            ft.Text("Норма сбережений", size=12, color="#888888"),
                        ], spacing=6),
                        ft.ProgressBar(
                            value=max(0, savings_pct) / 100,
                            bgcolor="#2A2A36", color="#FF9800",
                            height=8, border_radius=4,
                        ),
                        ft.Text(f"{savings_pct}% от доходов", size=13, color="#FF9800"),
                    ], spacing=6),
                ),
            ], spacing=10),
        ], spacing=10)

    # ── Столбчатая диаграмма (flet_charts BarChart) ──────────────────────────

    def _bar_chart(self, monthly: list[dict]) -> ft.Column:
        months   = [d["month"]  for d in monthly]
        incomes  = [d["income"] for d in monthly]
        expenses = [d["expense"] for d in monthly]
        n        = len(months)

        bar_w   = 20
        max_val = max(max(incomes), max(expenses), 1)
        max_y   = max_val * 1.25

        groups = [
            BarChartGroup(
                x=i,
                rods=[
                    BarChartRod(from_y=0, to_y=incomes[i],
                                width=bar_w, color=ft.Colors.GREEN_400, border_radius=3),
                    BarChartRod(from_y=0, to_y=expenses[i],
                                width=bar_w, color=ft.Colors.RED_400,   border_radius=3),
                ],
            )
            for i in range(n)
        ]

        bottom_axis = ChartAxis(
            labels=[
                ChartAxisLabel(
                    value=i,
                    label=ft.Text(months[i], size=11, color="#CCCCCC"),
                )
                for i in range(n)
            ],
        )

        chart_width = max(360, n * (bar_w * 2 + 28))

        return ft.Column([
            ft.Row(
                scroll="always",
                controls=[
                    ft.Container(
                        width=chart_width,
                        height=300,
                        content=BarChart(
                            groups=groups,
                            bottom_axis=bottom_axis,
                            max_y=max_y,
                            horizontal_grid_lines=ChartGridLines(color="#2A2A36"),
                        ),
                    ),
                ],
            ),
            # Легенда
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
        ], spacing=10)

    # ── Линейный график баланса (flet_charts LineChart) ───────────────────────

    def _balance_chart(self, monthly: list[dict]) -> ft.Row:
        balance  = 0
        balances = []
        months   = []
        for d in monthly:
            balance += d["income"] - d["expense"]
            balances.append(balance)
            months.append(d["month"])

        n       = len(months)
        max_val = max(balances)
        min_val = min(balances)
        max_y   = max_val * 1.25 if max_val > 0 else 1
        min_y   = min_val * 1.1  if min_val < 0 else 0

        points = [LineChartDataPoint(x=i, y=balances[i]) for i in range(n)]

        series = LineChartData(
            points=points,
            stroke_width=3,
            color=ft.Colors.PURPLE_400,
            curved=False,
        )

        bottom_axis = ChartAxis(
            labels=[
                ChartAxisLabel(
                    value=i,
                    label=ft.Text(months[i], size=11, color="#CCCCCC"),
                )
                for i in range(n)
            ],
        )

        chart_width = max(360, n * 70)

        return ft.Row(
            scroll="always",
            controls=[
                ft.Container(
                    width=chart_width,
                    height=300,
                    content=LineChart(
                        data_series=[series],
                        bottom_axis=bottom_axis,
                        min_x=-0.5,  max_x=n - 0.5,
                        min_y=min_y, max_y=max_y,
                        horizontal_grid_lines=ChartGridLines(color="#2A2A36"),
                        expand=True,
                    ),
                ),
            ],
        )

    # ── Горизонтальные бары категорий ────────────────────────────────────────

    def _category_bars(self, categories: list[dict]) -> ft.Column:
        rows = []
        for cat in categories:
            rows.append(ft.Column([
                ft.Row([
                    ft.Text(cat["label"], size=13, color="#CCCCCC", expand=True),
                    ft.Text(f"{cat['value']}%", size=13, color=cat["color"],
                            weight=ft.FontWeight.W_600),
                ]),
                ft.ProgressBar(
                    value=cat["value"] / 100,
                    bgcolor="#2A2A36", color=cat["color"],
                    height=8, border_radius=4,
                ),
            ], spacing=6))
        return ft.Column(rows, spacing=14)