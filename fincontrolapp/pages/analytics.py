"""
analytics.py — Экран аналитики финансов.

Показывает:
1. Сводные плашки (доходы, расходы, экономия, норма сбережений)
2. Столбчатая диаграмма доходов и расходов по месяцам выбранного года (BarChart)
3. Линейный график накопленного баланса (LineChart)
4. Структура расходов за период (прогресс-бары) — вместо pie chart
5. Тренд 6 месяцев (доходы и расходы за последние полгода) — LineChart с двумя линиями
"""

import flet as ft
from flet import charts
from datetime import datetime, date, timedelta
from database import get_connection
from components.base_page import BasePage

# ─── Константы ───────────────────────────────────────────────────────────────
MONTH_NAMES = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
               "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]

CATEGORY_COLORS = [
    "#FFC549", "#483EB7", "#FF7684", "#00B487",
    "#C80D00", "#6DD0F0", "#775Aff", "#9C27B0",
]

MIN_MONTHS = 2

# ─── DB-функции ──────────────────────────────────────────────────────────────
def get_available_years(user_id: int) -> list[int]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT strftime('%Y', date) AS y FROM transactions WHERE user_id = ? ORDER BY y",
            (user_id,),
        ).fetchall()
    years = [int(r["y"]) for r in rows if r["y"]]
    current = datetime.now().year
    if current not in years:
        years.append(current)
    return sorted(years)


def get_monthly_summary(user_id: int, year: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT strftime('%m', date) AS m,
                      SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
                      SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
               FROM transactions
               WHERE user_id = ? AND strftime('%Y', date) = ?
               GROUP BY m ORDER BY m ASC""",
            (user_id, str(year)),
        ).fetchall()
    db_data = {}
    for r in rows:
        db_data[int(r["m"])] = {"income": r["income"] or 0.0, "expense": r["expense"] or 0.0}
    result = []
    for month_num in range(1, 13):
        d = db_data.get(month_num, {"income": 0.0, "expense": 0.0})
        result.append({
            "month": MONTH_NAMES[month_num-1],
            "income": d["income"],
            "expense": d["expense"],
        })
    return result


def get_expense_breakdown_by_year(user_id: int, year: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT c.name AS category, SUM(t.amount) AS total
               FROM transactions t JOIN categories c ON t.category_id = c.id
               WHERE t.user_id = ? AND t.type = 'expense' AND strftime('%Y', t.date) = ?
               GROUP BY c.id, c.name ORDER BY total DESC""",
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


def get_expense_breakdown_by_period(user_id: int, start_date: str, end_date: str) -> list[dict]:
    """Возвращает список категорий с процентами за указанный период (для прогресс-баров)."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT c.name AS category, SUM(t.amount) AS total
               FROM transactions t JOIN categories c ON t.category_id = c.id
               WHERE t.user_id = ? AND t.type = 'expense' AND t.date BETWEEN ? AND ?
               GROUP BY c.id, c.name ORDER BY total DESC""",
            (user_id, start_date, end_date),
        ).fetchall()
    total = sum(r["total"] for r in rows) or 0
    if total == 0:
        return []
    palette = ["#6976EB", "#FF7684", "#00B487", "#FFB347", "#9B59B6", "#5DADE2"]
    return [
        {
            "label": r["category"],
            "value": round(r["total"] / total * 100),
            "color": palette[i % len(palette)],
        }
        for i, r in enumerate(rows)
    ]


def get_trend_6months(user_id: int) -> list[dict]:
    """Доходы и расходы за последние 6 месяцев (включая текущий)."""
    today = date.today()
    results = []
    # Идём от 5 месяцев назад до текущего
    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        # Первый день месяца
        start = f"{year}-{month:02d}-01"
        # Последний день месяца
        next_month = date(year, month, 28) + timedelta(days=4)  # хак для получения следующего месяца
        last_day = (next_month - timedelta(days=next_month.day)).day
        end = f"{year}-{month:02d}-{last_day:02d}"
        with get_connection() as conn:
            row = conn.execute(
                """SELECT
                      SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS income,
                      SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
                   FROM transactions
                   WHERE user_id = ? AND date BETWEEN ? AND ?""",
                (user_id, start, end),
            ).fetchone()
        results.append({
            "month": MONTH_NAMES[month-1],
            "income": row["income"] or 0.0,
            "expense": row["expense"] or 0.0,
        })
    return results


# ─── UI-helpers ──────────────────────────────────────────────────────────────
def _title(text: str) -> ft.Text:
    return ft.Text(text, size=16, font_family="Montserrat SemiBold", weight=ft.FontWeight.W_600, color="#000000")


def _card(content: ft.Control) -> ft.Container:
    return ft.Container(
        border=ft.border.all(1.5, ft.Colors.with_opacity(0.06, "#483EB7")),
        bgcolor=ft.Colors.with_opacity(0.2, "#483EB7"),
        border_radius=16, padding=20, content=content,
    )


def _stub(message: str) -> ft.Container:
    return ft.Container(
        height=130, alignment=ft.Alignment(0, 0),
        content=ft.Column([
            ft.Icon(ft.Icons.BAR_CHART_OUTLINED, color="#3A3A50", size=44),
            ft.Text(message, size=13, font_family="Montserrat SemiBold",
                    color="#666677", text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
    )


def _has_enough_data(monthly: list[dict]) -> bool:
    non_zero = sum(1 for d in monthly if d["income"] > 0 or d["expense"] > 0)
    return non_zero >= MIN_MONTHS


def period_dates(period: str) -> tuple[str, str]:
    today = date.today()
    end = today.isoformat()
    if period == 'month':
        start = today.replace(day=1).isoformat()
    elif period == 'quarter':
        month = today.month - 3
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        start = date(year, month, 1).isoformat()
    elif period == 'half':
        month = today.month - 6
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        start = date(year, month, 1).isoformat()
    else:  # 'year'
        start = today.replace(month=1, day=1).isoformat()
    return start, end


# ─── AnalyticsPage ───────────────────────────────────────────────────────────
class AnalyticsPage(BasePage):
    def __init__(self, page: ft.Page, user_id: int | None = None):
        self.user_id = user_id
        self.current_period = "month"
        self.period_container = ft.Container()  # для прогресс-баров периода
        self.selected_year = datetime.now().year
        super().__init__(page, "Аналитика")
        self._reload_period_data(self.current_period)

    def build_header(self):
        return ft.AppBar(
            title=ft.Text("Аналитика", font_family="Montserrat Extrabold", size=36),
            center_title=False, bgcolor=ft.Colors.TRANSPARENT,
            elevation=0, toolbar_height=50,
        )

    def _build_chart_controls(self) -> list[ft.Control]:
        monthly = get_monthly_summary(self.user_id, self.selected_year)
        categories_year = get_expense_breakdown_by_year(self.user_id, self.selected_year)
        enough = _has_enough_data(monthly)

        controls = [self._summary(monthly)]

        # 1. Доходы и расходы по месяцам (столбчатая)
        controls.append(_title("Доходы и расходы по месяцам"))
        controls.append(
            _card(self._bar_chart(monthly)) if enough
            else _card(_stub("Добавьте хотя бы 2 месяца данных"))
        )

        # 2. Динамика баланса (линейный график)
        controls.append(_title("Динамика баланса"))
        controls.append(
            _card(self._balance_chart(monthly)) if enough
            else _card(_stub("Добавьте хотя бы 2 месяца данных"))
        )

        # 3. Структура расходов за год (прогресс-бары)
        controls.append(_title("Структура расходов (год)"))
        controls.append(
            _card(self._category_bars(categories_year)) if categories_year
            else _card(_stub("Нет расходов за выбранный год"))
        )

        # 4. Структура расходов за период (прогресс-бары с фильтром)
        controls.append(_title("Структура расходов за период"))
        period_dropdown = ft.Dropdown(
            value=self.current_period,
            width=160,
            text_style=ft.TextStyle(font_family="Montserrat Medium", size=13, color="#000000"),
            options=[
                ft.dropdown.Option(key="month", text="Месяц"),
                ft.dropdown.Option(key="quarter", text="Квартал"),
                ft.dropdown.Option(key="half", text="Полгода"),
                ft.dropdown.Option(key="year", text="Год"),
            ],
            on_change=lambda e: self._reload_period_data(e.control.value),
            bgcolor="#F0F0F0", border_color="#483EB7",
        )
        period_block = ft.Container(
            content=ft.Column([
                ft.Row([period_dropdown], alignment=ft.MainAxisAlignment.END),
                self.period_container,
            ], spacing=10),
            padding=ft.padding.all(16), margin=ft.margin.only(top=12),
            border_radius=16, bgcolor=ft.Colors.with_opacity(0.2, "#483EB7"),
        )
        controls.append(period_block)

        # 5. Тренд 6 месяцев
        controls.append(_title("Тренд 6 месяцев"))
        controls.append(_card(self._trend_6months_chart()))

        return controls

    def build_body(self) -> ft.Column:
        years = get_available_years(self.user_id)
        self._charts_col = ft.Column(controls=self._build_chart_controls(), spacing=10)
        self._year_row = ft.Row(spacing=8)
        self._render_year_buttons(years)
        return ft.Column(
            scroll="vertical", spacing=10,
            controls=[
                ft.Row([
                    ft.Text("Год:", font_family="Montserrat SemiBold", size=20, color="#000000"),
                    self._year_row
                ], spacing=10),
                self._charts_col,
            ],
        )

    def _render_year_buttons(self, years: list[int]) -> None:
        def _btn(y: int) -> ft.Container:
            active = (y == self.selected_year)
            return ft.Container(
                content=ft.Text(str(y), font_family="Montserrat SemiBold", size=13,
                                color="#483EB7" if active else "#A8A8A8",
                                text_align=ft.TextAlign.CENTER),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                border_radius=20,
                gradient=ft.RadialGradient(
                    colors=["#ffffff", "#88A2FF"], center=ft.Alignment(0, -0.2),
                    radius=2.5, stops=[0.0, 0.8]
                ) if active else None,
                bgcolor=None if active else "rgba(108,99,255,0.1)",
                on_click=self._make_year_handler(y), ink=True,
            )
        self._year_row.controls = [_btn(y) for y in years]

    def _make_year_handler(self, year: int):
        def handler(e):
            self.selected_year = year
            self._render_year_buttons(get_available_years(self.user_id))
            self._charts_col.controls = self._build_chart_controls()
            self.page_ref.update()
        return handler

    # --- Сводные плашки ---
    def _summary(self, monthly: list[dict]) -> ft.Column:
        total_income = sum(d["income"] for d in monthly)
        total_expense = sum(d["expense"] for d in monthly)
        savings = total_income - total_expense
        savings_pct = round(savings / total_income * 100) if total_income else 0

        def fmt(v): return f"{int(v):,}".replace(",", " ") + " ₽"

        def tile(label, value, color, icon):
            return ft.Container(
                expand=True,
                border=ft.border.all(1.5, ft.Colors.with_opacity(0.06, "#483EB7")),
                bgcolor=ft.Colors.with_opacity(0.1, "#483EB7"),
                border_radius=14, padding=16,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=color, size=18),
                        ft.Text(label, font_family="Montserrat SemiBold", size=14, color="#888888"),
                    ], spacing=6),
                    ft.Text(fmt(value), size=16, font_family="Montserrat SemiBold",
                            weight=ft.FontWeight.BOLD, color=color),
                ], spacing=6),
            )

        return ft.Column([
            ft.Row([
                tile("Доходы", total_income, ft.Colors.with_opacity(0.6, "#23CF01"), ft.Icons.TRENDING_UP),
                tile("Расходы", total_expense, ft.Colors.with_opacity(0.6, "#FF7E1C"), ft.Icons.TRENDING_DOWN),
            ], spacing=10),
            ft.Row([
                tile("Экономия", savings, "#6C63FF", ft.Icons.SAVINGS_OUTLINED),
                ft.Container(
                    expand=True,
                    border=ft.border.all(1.5, ft.Colors.with_opacity(0.06, "#483EB7")),
                    bgcolor=ft.Colors.with_opacity(0.1, "#483EB7"),
                    border_radius=14, padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PERCENT, color="#483EB7", size=18),
                            ft.Text("Норма сбережений", font_family="Montserrat SemiBold",
                                    size=12, color="#888888", expand=True),
                        ], spacing=6),
                        ft.ProgressBar(
                            value=max(0, savings_pct)/100,
                            bgcolor=ft.Colors.with_opacity(0.6, "#483EB7"),
                            color="#483EB7", height=8, border_radius=4,
                        ),
                        ft.Text(f"{savings_pct}% от доходов", font_family="Montserrat SemiBold",
                                size=13, color=ft.Colors.with_opacity(0.6, "#483EB7")),
                    ], spacing=6),
                ),
            ], spacing=10),
        ], spacing=10)

    # --- Столбчатая диаграмма (flet.charts) ---
    def _bar_chart(self, monthly: list[dict]) -> ft.Column:
        months = [d["month"] for d in monthly]
        incomes = [d["income"] for d in monthly]
        expenses = [d["expense"] for d in monthly]
        n = len(months)
        bar_w = 20
        max_val = max(max(incomes), max(expenses), 1)
        max_y = max_val * 1.25

        groups = [
            charts.BarChartGroup(
                x=i,
                rods=[
                    charts.BarChartRod(
                        from_y=0, to_y=incomes[i], width=bar_w,
                        color=ft.Colors.with_opacity(0.6, "#23CF01"), border_radius=3,
                        tooltip=f"↑ {incomes[i]:,.0f} ₽",
                    ),
                    charts.BarChartRod(
                        from_y=0, to_y=expenses[i], width=bar_w,
                        color=ft.Colors.with_opacity(0.6, "#FF7E1C"), border_radius=3,
                        tooltip=f"↓ {expenses[i]:,.0f} ₽",
                    ),
                ],
            )
            for i in range(n)
        ]

        bottom_axis = charts.ChartAxis(
            labels=[
                charts.ChartAxisLabel(
                    value=i,
                    label=ft.Text(months[i], font_family="Montserrat SemiBold", size=11,
                                  color=ft.Colors.with_opacity(0.9, "#483EB7")),
                )
                for i in range(n)
            ],
        )

        chart_width = max(360, n * (bar_w*2 + 28))

        return ft.Column([
            ft.Row(
                scroll="always",
                controls=[
                    ft.Container(
                        width=chart_width,
                        height=300,
                        content=charts.BarChart(
                            groups=groups,
                            bottom_axis=bottom_axis,
                            max_y=max_y,
                            horizontal_grid_lines=charts.ChartGridLines(
                                color=ft.Colors.with_opacity(0.1, "#483EB7"),
                            ),
                        ),
                    ),
                ],
            ),
            ft.Row([
                ft.Row([
                    ft.Container(width=12, height=12,
                                 bgcolor=ft.Colors.with_opacity(0.6, "#23CF01"),
                                 border_radius=3),
                    ft.Text("Доходы", font_family="Montserrat SemiBold", size=12,
                            color=ft.Colors.with_opacity(0.9, "#483EB7")),
                ], spacing=6),
                ft.Row([
                    ft.Container(width=12, height=12,
                                 bgcolor=ft.Colors.with_opacity(0.6, "#FF7E1C"),
                                 border_radius=3),
                    ft.Text("Расходы", font_family="Montserrat SemiBold", size=12,
                            color=ft.Colors.with_opacity(0.9, "#483EB7")),
                ], spacing=6),
            ], spacing=20),
        ], spacing=10)

    # --- Линейный график баланса (накопленный) ---
    def _balance_chart(self, monthly: list[dict]) -> ft.Row:
        balance = 0
        balances = []
        months = []
        for d in monthly:
            balance += d["income"] - d["expense"]
            balances.append(balance)
            months.append(d["month"])
        n = len(months)
        if n == 0:
            return ft.Row([ft.Text("Нет данных")])
        max_val = max(balances) if balances else 0
        min_val = min(balances) if balances else 0
        max_y = max_val * 1.25 if max_val > 0 else 1
        min_y = min_val * 1.1 if min_val < 0 else 0
        points = [charts.LineChartDataPoint(x=i, y=balances[i]) for i in range(n)]
        series = charts.LineChartData(points=points, stroke_width=3, color="#483EB7", curved=False)
        bottom_axis = charts.ChartAxis(
            labels=[
                charts.ChartAxisLabel(
                    value=i,
                    label=ft.Text(months[i], font_family="Montserrat SemiBold", size=11,
                                  color=ft.Colors.with_opacity(0.9, "#483EB7")),
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
                    content=charts.LineChart(
                        data_series=[series],
                        bottom_axis=bottom_axis,
                        min_x=-0.5, max_x=n-0.5,
                        min_y=min_y, max_y=max_y,
                        horizontal_grid_lines=charts.ChartGridLines(
                            color=ft.Colors.with_opacity(0.09, "#483EB7")
                        ),
                        expand=True,
                    ),
                ),
            ],
        )

    # --- Прогресс-бары (горизонтальные) для любой категории ---
    def _category_bars(self, categories: list[dict]) -> ft.Column:
        if not categories:
            return ft.Column([ft.Text("Нет данных", color="#666677")], spacing=10)
        rows = []
        for cat in categories:
            rows.append(ft.Column([
                ft.Row([
                    ft.Text(cat["label"], font_family="Montserrat SemiBold", size=13,
                            color=ft.Colors.with_opacity(0.9, "#483EB7"), expand=True),
                    ft.Text(f"{cat['value']}%", font_family="Montserrat SemiBold", size=13,
                            color=cat["color"], weight=ft.FontWeight.W_600),
                ]),
                ft.ProgressBar(
                    value=cat["value"]/100,
                    bgcolor=ft.Colors.with_opacity(0.09, "#483EB7"),
                    color=cat["color"],
                    height=8, border_radius=4,
                ),
            ], spacing=6))
        return ft.Column(rows, spacing=14)

    # --- Обновление данных для периода (прогресс-бары) ---
    def _reload_period_data(self, period: str):
        self.current_period = period
        start, end = period_dates(period)
        breakdown = get_expense_breakdown_by_period(self.user_id, start, end)
        if breakdown:
            self.period_container.content = self._category_bars(breakdown)
        else:
            self.period_container.content = _stub("Нет расходов за выбранный период")
        self.period_container.update()

    # --- Тренд 6 месяцев (две линии) ---
    def _trend_6months_chart(self) -> ft.Control:
        trend = get_trend_6months(self.user_id)
        if not trend or all(d["income"] == 0 and d["expense"] == 0 for d in trend):
            return _stub("Недостаточно данных для тренда (нужно минимум 2 месяца)")

        months = [d["month"] for d in trend]
        incomes = [d["income"] for d in trend]
        expenses = [d["expense"] for d in trend]
        n = len(months)

        max_val = max(max(incomes), max(expenses), 1)
        max_y = max_val * 1.25

        income_points = [charts.LineChartDataPoint(x=i, y=incomes[i]) for i in range(n)]
        expense_points = [charts.LineChartDataPoint(x=i, y=expenses[i]) for i in range(n)]

        income_series = charts.LineChartData(
            points=income_points, stroke_width=2, color="#23CF01", curved=True
        )
        expense_series = charts.LineChartData(
            points=expense_points, stroke_width=2, color="#FF7E1C", curved=True
        )

        bottom_axis = charts.ChartAxis(
            labels=[
                charts.ChartAxisLabel(
                    value=i,
                    label=ft.Text(months[i], font_family="Montserrat SemiBold", size=11,
                                  color=ft.Colors.with_opacity(0.9, "#483EB7")),
                )
                for i in range(n)
            ],
        )

        chart_width = max(360, n * 70)

        return ft.Column([
            ft.Row(
                scroll="always",
                controls=[
                    ft.Container(
                        width=chart_width,
                        height=300,
                        content=charts.LineChart(
                            data_series=[income_series, expense_series],
                            bottom_axis=bottom_axis,
                            min_x=-0.5, max_x=n-0.5,
                            min_y=0, max_y=max_y,
                            horizontal_grid_lines=charts.ChartGridLines(
                                color=ft.Colors.with_opacity(0.09, "#483EB7")
                            ),
                            expand=True,
                        ),
                    ),
                ],
            ),
            ft.Row([
                ft.Row([
                    ft.Container(width=12, height=3, bgcolor="#23CF01"),
                    ft.Text("Доходы", font_family="Montserrat Medium", size=12,
                            color=ft.Colors.with_opacity(0.9, "#483EB7")),
                ], spacing=6),
                ft.Row([
                    ft.Container(width=12, height=3, bgcolor="#FF7E1C"),
                    ft.Text("Расходы", font_family="Montserrat Medium", size=12,
                            color=ft.Colors.with_opacity(0.9, "#483EB7")),
                ], spacing=6),
            ], spacing=20),
        ], spacing=10)
