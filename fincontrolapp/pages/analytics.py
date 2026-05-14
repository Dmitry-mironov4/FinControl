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
from flet_charts.line_chart_data_point import LineChartDataPointTooltip
from flet_charts.line_chart import LineChartTooltip
from flet_charts import (
    BarChart, BarChartGroup, BarChartRod, BarChartRodTooltip,
    LineChart, LineChartData, LineChartDataPoint,
    ChartGridLines, ChartAxis, ChartAxisLabel,
)
from flet_charts.bar_chart import BarChartTooltip
from datetime import datetime, date
from database import get_connection
from components.base_page import BasePage
from utils import get_currency_symbol


MONTH_NAMES = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
               "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]

CATEGORY_COLORS = [
    "#FFC549", "#483EB7", "#FF7684", "#00B487",
    "#C80D00", "#6DD0F0", "#775Aff", "#9C27B0",
]

MIN_MONTHS = 2


def get_available_years(user_id: int) -> list[int]:
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
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT
                   strftime('%m', date)                                    AS m,
                   SUM(CASE WHEN type='income'  THEN amount ELSE 0 END)   AS income,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END)   AS expense
               FROM transactions
               WHERE user_id = ? AND strftime('%Y', date) = ?
               GROUP BY m
               ORDER BY m ASC""",
            (user_id, str(year)),
        ).fetchall()

    db_data = {}
    for r in rows:
        db_data[int(r["m"])] = {
            "income":  r["income"]  or 0.0,
            "expense": r["expense"] or 0.0,
        }

    result = []
    for month_num in range(1, 13):
        d = db_data.get(month_num, {"income": 0.0, "expense": 0.0})
        result.append({
            "month":   MONTH_NAMES[month_num - 1],
            "income":  d["income"],
            "expense": d["expense"],
        })
    return result



def get_expense_breakdown_by_year(user_id: int, year: int) -> list[dict]:
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


def get_expense_breakdown_by_period(user_id: int, start_date: str, end_date: str) -> list[dict]:
    """Разбивка расходов по категориям за произвольный период."""
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
        {"label": r["category"], "value": round(r["total"] / total * 100), "color": palette[i % len(palette)]}
        for i, r in enumerate(rows)
    ]


def period_dates(period: str, year: int | None = None) -> tuple[str, str]:
    """Возвращает (start, end) для периода.
    Если year задан и он не текущий — точка отсчёта 31 декабря того года.
    """
    today = date.today()
    anchor = today if (year is None or year == today.year) else date(year, 12, 31)
    end = anchor.isoformat()
    if period == "month":
        start = anchor.replace(day=1).isoformat()
    elif period == "quarter":
        month = anchor.month - 2
        yr = anchor.year
        if month <= 0:
            month += 12
            yr -= 1
        start = date(yr, month, 1).isoformat()
    elif period == "half":
        month = anchor.month - 6
        yr = anchor.year
        if month <= 0:
            month += 12
            yr -= 1
        start = date(yr, month, 1).isoformat()
    elif period == "year":
        start = anchor.replace(month=1, day=1).isoformat()
    else:  # all
        start = "2000-01-01"
        end = date.today().isoformat()
    return start, end


def get_trend_6months(user_id: int, year: int | None = None) -> list[dict]:
    """Доходы и расходы за последние 6 месяцев выбранного года.
    Если year не задан или это текущий год — считает от сегодня.
    """
    today = date.today()
    anchor = today if (year is None or year == today.year) else date(year, 12, 31)

    start_month = anchor.month - 5
    start_year = anchor.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y', date) AS yr, strftime('%m', date) AS mo,
                      SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
                      SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
               FROM transactions
               WHERE user_id = ? AND date BETWEEN ? AND ?
               GROUP BY yr, mo
               ORDER BY yr, mo""",
            (user_id, f"{start_year}-{start_month:02d}-01", anchor.isoformat()),
        ).fetchall()

    db_data = {
        (int(r["yr"]), int(r["mo"])): {"income": r["income"] or 0.0, "expense": r["expense"] or 0.0}
        for r in rows
    }

    results = []
    for i in range(5, -1, -1):
        m = anchor.month - i
        y = anchor.year
        while m <= 0:
            m += 12
            y -= 1
        d = db_data.get((y, m), {"income": 0.0, "expense": 0.0})
        results.append({"month": MONTH_NAMES[m - 1], "income": d["income"], "expense": d["expense"]})
    return results


# ─── UI-helpers ──────────────────────────────────────────────────────────────

def _title(text: str) -> ft.Text:
    return ft.Text(text, size=16, font_family="Montserrat SemiBold",
                   weight=ft.FontWeight.W_600, color="#000000")


def _card(content: ft.Control) -> ft.Container:
    return ft.Container(
        border=ft.Border.all(1.5, ft.Colors.with_opacity(0.06, "#483EB7")),
        bgcolor=ft.Colors.with_opacity(0.2, "#483EB7"),
        border_radius=16,
        padding=20,
        content=content,
    )


def _stub(message: str) -> ft.Container:
    return ft.Container(
        height=130,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            [
                ft.Icon(ft.Icons.BAR_CHART_OUTLINED, color="#3A3A50", size=44),
                ft.Text(
                    message,
                    size=13,
                    font_family="Montserrat SemiBold",
                    color="#666677",
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
    )


def _has_enough_data(monthly: list[dict]) -> bool:
    non_zero = sum(1 for d in monthly if d["income"] > 0 or d["expense"] > 0)
    return non_zero >= MIN_MONTHS


class AnalyticsPage(BasePage):

    def __init__(self, page: ft.Page, user_id: int | None = None, budget_controller=None):
        self.user_id = user_id
        self._budget_ctrl = budget_controller
        self.selected_year = datetime.now().year
        self.current_period = "month"
        self.period_container = ft.Container()
        super().__init__(page, "Аналитика")
        self._reload_period_data(self.current_period)

    def build_header(self):
        return ft.AppBar(
            title=ft.Text(
                "Аналитика",
                font_family="Montserrat Extrabold",
                size=36,
            ),
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            toolbar_height=50,
        )

    def _build_chart_controls(self) -> list[ft.Control]:
        monthly = get_monthly_summary(self.user_id, self.selected_year)
        enough  = _has_enough_data(monthly)

        controls = [self._summary(monthly)]

        controls.append(_title("Доходы и расходы по месяцам"))
        controls.append(
            _card(self._bar_chart(monthly)) if enough
            else _card(_stub("Добавьте хотя бы 2 месяца данных,\nчтобы увидеть диаграмму"))
        )

        controls.append(_title("Динамика баланса"))
        controls.append(
            _card(self._balance_chart(monthly)) if enough
            else _card(_stub("Добавьте хотя бы 2 месяца данных,\nчтобы увидеть график баланса"))
        )

        # Структура расходов (с фильтром по периоду)
        controls.append(_title("Структура расходов"))
        period_dropdown = ft.Dropdown(
            value=self.current_period,
            width=160,
            text_style=ft.TextStyle(font_family="Montserrat Medium", size=13, color="#000000"),
            options=[
                ft.dropdown.Option(key="all", text="Все время"),
                ft.dropdown.Option(key="year", text="Год"),
                ft.dropdown.Option(key="half", text="Полгода"),
                ft.dropdown.Option(key="quarter", text="Квартал"),
                ft.dropdown.Option(key="month", text="Месяц"),
            ],
            on_select=lambda e: self._reload_period_data(e.control.value),
            bgcolor="#F0F0F0", border_color="#483EB7",
        )
        period_block = ft.Container(
            content=ft.Column([
                ft.Row([period_dropdown], alignment=ft.MainAxisAlignment.END),
                self.period_container,
            ], spacing=10),
            padding=ft.Padding.all(16),
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.2, "#483EB7"),
        )
        controls.append(period_block)

        # Бюджеты по категориям
        self._budget_container = ft.Container(
            content=self._build_budget_section()
        )
        controls.append(self._budget_container)

        controls.append(_title("Тренд 6 месяцев"))
        controls.append(_card(self._trend_6months_chart()))

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
                    [ft.Text("Год:", font_family="Montserrat SemiBold",
                             size=20, color="#000000"), self._year_row],
                    spacing=10,
                ),
                self._charts_col,
            ],
        )

    def _render_year_buttons(self, years: list[int]) -> None:
        def _btn(y: int) -> ft.Container:
            active = (y == self.selected_year)
            return ft.Container(
                content=ft.Text(
                    str(y),
                    font_family="Montserrat SemiBold",
                    size=13,
                    color="#483EB7" if active else "#A8A8A8",
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                border_radius=20,
                gradient=ft.RadialGradient(
                    colors=["#ffffff", "#88A2FF"],
                    center=ft.Alignment(0.2, -0.2),
                    radius=5.0,
                    stops=[0.0, 0.8],
                ) if active else None,
                bgcolor=None if active else "rgba(108,99,255,0.1)",
                on_click=self._make_year_handler(y),
                ink=True,
            )

        self._year_row.controls = [_btn(y) for y in years]

    def _make_year_handler(self, year: int):
        def handler(_):
            self.selected_year = year
            years = get_available_years(self.user_id)
            self._render_year_buttons(years)
            self._charts_col.controls = self._build_chart_controls()
            self._reload_period_data(self.current_period)
            self.page_ref.update()
        return handler

    def _summary(self, monthly: list[dict]) -> ft.Column:
        total_income  = sum(d["income"]  for d in monthly)
        total_expense = sum(d["expense"] for d in monthly)
        savings       = total_income - total_expense
        savings_pct   = round(savings / total_income * 100) if total_income else 0

        sym = get_currency_symbol(self.page_ref)

        def fmt(v: float) -> str:
            return f"{int(v):,}".replace(",", " ") + f" {sym}"

        def tile(label, value, color, icon):
            return ft.Container(
                expand=True,
                border=ft.Border.all(1.5, ft.Colors.with_opacity(0.06, "#483EB7")),
                bgcolor=ft.Colors.with_opacity(0.1, "#483EB7"),
                border_radius=14,
                padding=16,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=color, size=18),
                        ft.Text(label, font_family="Montserrat SemiBold",
                                size=14, color="#888888"),
                    ], spacing=6),
                    ft.Text(fmt(value), size=16, font_family="Montserrat SemiBold",
                            weight=ft.FontWeight.BOLD, color=color),
                ], spacing=6),
            )

        return ft.Column([
            ft.Row([
                tile("Доходы",  total_income,
                     ft.Colors.with_opacity(0.6, "#23CF01"), ft.Icons.TRENDING_UP),
                tile("Расходы", total_expense,
                     ft.Colors.with_opacity(0.6, "#FF7E1C"), ft.Icons.TRENDING_DOWN),
            ], spacing=10),
            ft.Row([
                tile("Экономия", savings,
                     "#6C63FF" if savings >= 0 else "#FF5252",
                     ft.Icons.SAVINGS_OUTLINED if savings >= 0 else ft.Icons.TRENDING_DOWN),
                ft.Container(
                    expand=True,
                    border=ft.Border.all(1.5, ft.Colors.with_opacity(0.06, "#483EB7")),
                    bgcolor=ft.Colors.with_opacity(0.1, "#483EB7"),
                    border_radius=14,
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PERCENT, color="#483EB7", size=18),
                            ft.Text("Норма сбережений", font_family="Montserrat SemiBold",
                                    size=12, color="#888888", expand=True),
                        ], spacing=6),
                        ft.ProgressBar(
                            value=min(1.0, max(0, savings_pct) / 100),
                            bgcolor=ft.Colors.with_opacity(0.6, "#483EB7"),
                            color="#483EB7",
                            height=8,
                            border_radius=4,
                        ),
                        ft.Text(f"{savings_pct}% от доходов",
                                font_family="Montserrat SemiBold",
                                size=13,
                                color=ft.Colors.with_opacity(0.6, "#483EB7")),
                    ], spacing=6),
                ),
            ], spacing=10),
        ], spacing=10)

    def _bar_chart(self, monthly: list[dict]) -> ft.Column:
        months   = [d["month"]  for d in monthly]
        incomes  = [d["income"] for d in monthly]
        expenses = [d["expense"] for d in monthly]
        n        = len(months)
        sym      = get_currency_symbol(self.page_ref)

        bar_w   = 20
        max_val = max(max(incomes), max(expenses), 1)
        max_y   = max_val * 1.25

        groups = [
            BarChartGroup(
                x=i,
                rods=[
                    BarChartRod(
                        from_y=0, to_y=incomes[i],
                        width=bar_w,
                        color=ft.Colors.with_opacity(0.6, "#23CF01"),
                        border_radius=3,
                        tooltip=BarChartRodTooltip(
                            text=f"↑ {incomes[i]:,.0f} {sym}",
                            text_style=ft.TextStyle(
                                color="#FFFFFF", size=12,
                                font_family="Montserrat SemiBold",
                            ),
                        ),
                    ),
                    BarChartRod(
                        from_y=0, to_y=expenses[i],
                        width=bar_w,
                        color=ft.Colors.with_opacity(0.6, "#FF7E1C"),
                        border_radius=3,
                        tooltip=BarChartRodTooltip(
                            text=f"↓ {expenses[i]:,.0f} {sym}",
                            text_style=ft.TextStyle(
                                color="#FFFFFF", size=12,
                                font_family="Montserrat SemiBold",
                            ),
                        ),
                    ),
                ],
            )
            for i in range(n)
        ]

        bottom_axis = ChartAxis(
            labels=[
                ChartAxisLabel(
                    value=i,
                    label=ft.Text(
                        months[i],
                        font_family="Montserrat SemiBold",
                        size=11,
                        color=ft.Colors.with_opacity(0.9, "#483EB7"),
                    ),
                )
                for i in range(n)
            ],
            label_size=32,
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
                            tooltip=BarChartTooltip(
                                bgcolor=ft.Colors.with_opacity(0.4, "#483EB7"),
                                border_radius=5,
                            ),
                            horizontal_grid_lines=ChartGridLines(
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
                    ft.Text("Доходы", font_family="Montserrat SemiBold",
                            size=12, color=ft.Colors.with_opacity(0.9, "#483EB7")),
                ], spacing=6),
                ft.Row([
                    ft.Container(width=12, height=12,
                                 bgcolor=ft.Colors.with_opacity(0.6, "#FF7E1C"),
                                 border_radius=3),
                    ft.Text("Расходы", font_family="Montserrat SemiBold",
                            size=12, color=ft.Colors.with_opacity(0.9, "#483EB7")),
                ], spacing=6),
            ], spacing=20),
        ], spacing=10)

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
        sym     = get_currency_symbol(self.page_ref)

        points = [
            LineChartDataPoint(
                x=i,
                y=balances[i],
                tooltip=LineChartDataPointTooltip(
                    text=f"{balances[i]:,.0f} {sym}",
                    text_style=ft.TextStyle(
                        color="#FFFFFF",
                        size=12,
                        font_family="Montserrat SemiBold",
                    ),
                ),
            )
            for i in range(n)
        ]

        series = LineChartData(
            points=points,
            stroke_width=3,
            color="#483EB7",
            curved=False,
        )

        bottom_axis = ChartAxis(
            labels=[
                ChartAxisLabel(
                    value=i,
                    label=ft.Text(
                        months[i],
                        font_family="Montserrat SemiBold",
                        size=11,
                        color=ft.Colors.with_opacity(0.9, "#483EB7"),
                    ),
                )
                for i in range(n)
            ],
            label_size=32,
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
                        tooltip=LineChartTooltip(
                            bgcolor=ft.Colors.with_opacity(0.4, "#483EB7"),
                            border_radius=5,
                        ),
                        horizontal_grid_lines=ChartGridLines(
                            color=ft.Colors.with_opacity(0.09, "#483EB7"),
                        ),
                        expand=True,
                    ),
                ),
            ],
        )

    def _category_bars(self, categories: list[dict]) -> ft.Column:
        rows = []
        for cat in categories:
            rows.append(ft.Column([
                ft.Row([
                    ft.Text(cat["label"], font_family="Montserrat SemiBold",
                            size=13, color=ft.Colors.with_opacity(0.9, "#483EB7"),
                            expand=True),
                    ft.Text(f"{cat['value']}%", font_family="Montserrat SemiBold",
                            size=13, color=cat["color"], weight=ft.FontWeight.W_600),
                ]),
                ft.ProgressBar(
                    value=cat["value"] / 100,
                    bgcolor=ft.Colors.with_opacity(0.09, "#483EB7"),
                    color=cat["color"],
                    height=8,
                    border_radius=4,
                ),
            ], spacing=6))
        return ft.Column(rows, spacing=14)

    # ── Секция бюджетов ──────────────────────────────────────────────────────
    def _build_budget_section(self) -> ft.Control:
        if not self._budget_ctrl:
            return ft.Container()

        budgets = self._budget_ctrl.get_budgets(year=self.selected_year)
        currency = get_currency_symbol(self.page_ref)

        def open_dialog(budget=None):
            categories = self._budget_ctrl.get_expense_categories()
            if not categories:
                return

            amount_field = ft.TextField(
                label=f"Лимит ({currency})",
                keyboard_type=ft.KeyboardType.NUMBER,
                text_style=ft.TextStyle(font_family="Montserrat Medium"),
                label_style=ft.TextStyle(font_family="Montserrat Medium"),
                border_color="#6976EB",
                value=str(int(budget.limit_amount)) if budget else "",
            )
            cat_dropdown = ft.Dropdown(
                label="Категория",
                value=str(budget.category_id) if budget else None,
                options=[ft.dropdown.Option(key=str(c["id"]), text=c["name"]) for c in categories],
                text_style=ft.TextStyle(font_family="Montserrat Medium"),
                label_style=ft.TextStyle(font_family="Montserrat Medium"),
                border_color="#6976EB",
                disabled=budget is not None,
            )
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Бюджет по категории", font_family="Montserrat SemiBold"),
            )

            def on_save(e):
                raw = (amount_field.value or "").strip()
                cat_id_str = cat_dropdown.value
                if not raw or not cat_id_str:
                    return
                try:
                    limit = float(raw.replace(",", "."))
                except ValueError:
                    return
                if limit <= 0:
                    return
                self._budget_ctrl.set_budget(int(cat_id_str), limit)
                from components import close_dialog
                close_dialog(self.page_ref, dlg)
                self._refresh_budget_section()

            def on_delete(e):
                if budget:
                    self._budget_ctrl.delete_budget(budget.id)
                from components import close_dialog
                close_dialog(self.page_ref, dlg)
                self._refresh_budget_section()

            def on_cancel(e):
                from components import close_dialog
                close_dialog(self.page_ref, dlg)

            dlg.content = ft.Column(
                controls=[cat_dropdown, amount_field],
                tight=True, spacing=12,
            )
            actions = [
                ft.TextButton("Отмена", on_click=on_cancel,
                    style=ft.ButtonStyle(color="#483EB7",
                        text_style=ft.TextStyle(font_family="Montserrat SemiBold"))),
                ft.TextButton("Сохранить", on_click=on_save,
                    style=ft.ButtonStyle(color="#483EB7",
                        text_style=ft.TextStyle(font_family="Montserrat SemiBold"))),
            ]
            if budget:
                actions.insert(1, ft.TextButton("Удалить", on_click=on_delete,
                    style=ft.ButtonStyle(color="#F44336",
                        text_style=ft.TextStyle(font_family="Montserrat SemiBold"))))
            dlg.actions = actions
            from components import show_dialog
            show_dialog(self.page_ref, dlg)

        # Строки бюджетов
        if not budgets:
            budget_rows = [
                ft.Container(
                    content=ft.Text(
                        "Нет бюджетов. Нажмите + чтобы задать лимит.",
                        color=ft.Colors.with_opacity(0.6, "#483EB7"),
                        font_family="Montserrat Medium",
                        size=13,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding.symmetric(vertical=16),
                )
            ]
        else:
            budget_rows = []
            for b in budgets:
                pct = min(b.progress_pct, 100)
                budget_rows.append(
                    ft.GestureDetector(
                        on_tap=lambda e, budget=b: open_dialog(budget),
                        content=ft.Column([
                            ft.Row([
                                ft.Text(b.category_name, font_family="Montserrat SemiBold",
                                        size=13, color=ft.Colors.with_opacity(0.9, "#483EB7"), expand=True),
                                ft.Text(
                                    f"{b.spent_amount:,.0f} / {b.limit_amount:,.0f} {currency}",
                                    font_family="Montserrat Medium",
                                    size=12, color=ft.Colors.with_opacity(0.6, "#483EB7"),
                                ),
                            ]),
                            ft.ProgressBar(
                                value=pct / 100,
                                bgcolor=ft.Colors.with_opacity(0.1, "#483EB7"),
                                color=b.status_color,
                                height=8,
                                border_radius=ft.BorderRadius.all(4),
                            ),
                            ft.Text(
                                f"{b.progress_pct:.0f}% использовано",
                                font_family="Montserrat Medium",
                                size=11,
                                color=ft.Colors.with_opacity(0.5, "#483EB7"),
                            ),
                        ], spacing=6),
                    )
                )

        add_btn = ft.TextButton(
            "+ Добавить",
            style=ft.ButtonStyle(color="#483EB7",
                text_style=ft.TextStyle(font_family="Montserrat SemiBold")),
            on_click=lambda e: open_dialog(),
        )

        return ft.Column([
            ft.Row([
                _title("Бюджеты по категориям"),
                add_btn,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            _card(ft.Column(budget_rows, spacing=14)),
        ], spacing=6)

    def _reload_period_data(self, period: str):
        self.current_period = period
        start, end = period_dates(period, self.selected_year)
        breakdown = get_expense_breakdown_by_period(self.user_id, start, end)
        self.period_container.content = (
            self._category_bars(breakdown) if breakdown
            else _stub("Нет расходов за выбранный период")
        )
        try:
            self.period_container.update()
        except RuntimeError:
            pass

    def _trend_6months_chart(self) -> ft.Control:
        trend = get_trend_6months(self.user_id, self.selected_year)
        if not trend or all(d["income"] == 0 and d["expense"] == 0 for d in trend):
            return _stub("Недостаточно данных для тренда (нужно минимум 2 месяца)")

        months = [d["month"] for d in trend]
        incomes = [d["income"] for d in trend]
        expenses = [d["expense"] for d in trend]
        n = len(months)
        max_val = max(max(incomes), max(expenses), 1)
        sym = get_currency_symbol(self.page_ref)

        income_points = [
            LineChartDataPoint(
                x=i, y=incomes[i],
                tooltip=LineChartDataPointTooltip(
                    text=f"↑ {incomes[i]:,.0f} {sym}",
                    text_style=ft.TextStyle(color="#FFFFFF", size=12, font_family="Montserrat SemiBold"),
                ),
            )
            for i in range(n)
        ]
        expense_points = [
            LineChartDataPoint(
                x=i, y=expenses[i],
                tooltip=LineChartDataPointTooltip(
                    text=f"↓ {expenses[i]:,.0f} {sym}",
                    text_style=ft.TextStyle(color="#FFFFFF", size=12, font_family="Montserrat SemiBold"),
                ),
            )
            for i in range(n)
        ]

        income_series = LineChartData(points=income_points, stroke_width=2, color="#23CF01", curved=True)
        expense_series = LineChartData(points=expense_points, stroke_width=2, color="#FF7E1C", curved=True)

        bottom_axis = ChartAxis(
            labels=[
                ChartAxisLabel(
                    value=i,
                    label=ft.Text(months[i], font_family="Montserrat SemiBold", size=11,
                                  color=ft.Colors.with_opacity(0.9, "#483EB7")),
                )
                for i in range(n)
            ],
        )

        return ft.Column([
            ft.Row(
                scroll=ft.ScrollMode.ALWAYS,
                controls=[
                    ft.Container(
                        width=max(360, n * 70),
                        height=300,
                        content=LineChart(
                            data_series=[income_series, expense_series],
                            bottom_axis=bottom_axis,
                            min_x=-0.5, max_x=n - 0.5,
                            min_y=0, max_y=max_val * 1.25,
                            horizontal_grid_lines=ChartGridLines(
                                color=ft.Colors.with_opacity(0.09, "#483EB7")
                            ),
                            tooltip=LineChartTooltip(
                                bgcolor=ft.Colors.with_opacity(0.4, "#483EB7"),
                                border_radius=5,
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

    def _refresh_budget_section(self):
        """Перерисовывает только секцию бюджетов без перестройки всей страницы."""
        self._budget_container.content = self._build_budget_section()
        self._budget_container.update()
