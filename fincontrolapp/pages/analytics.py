import flet as ft
from flet_charts import (
    BarChart,
    BarChartGroup,
    BarChartRod,
    LineChart,
    LineChartData,
    LineChartDataPoint,
    ChartGridLines,
    ChartAxis,
    ChartAxisLabel
)

from components.base_page import BasePage
from database import get_connection
from datetime import datetime


# ─────────────────────────────────────────────
# DB функции
# ─────────────────────────────────────────────

def get_available_years(user_id=None):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT DISTINCT strftime('%Y', date) as year
        FROM transactions
    """

    params = []

    if user_id:
        query += " WHERE user_id=?"
        params.append(user_id)

    cur.execute(query, tuple(params))

    years = [int(row["year"]) for row in cur.fetchall()]

    conn.close()

    return sorted(years)


def get_monthly_summary(user_id=None, year=None):
    conn = get_connection()
    cur = conn.cursor()

    if year is None:
        year = datetime.now().year

    query = """
        SELECT 
            strftime('%m', date) as month_num,
            SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
        FROM transactions
        WHERE strftime('%Y', date)=?
    """

    params = [str(year)]

    if user_id:
        query += " AND user_id=?"
        params.append(user_id)

    query += """
        GROUP BY month_num
        ORDER BY month_num
    """

    cur.execute(query, tuple(params))

    rows = cur.fetchall()

    conn.close()

    month_names = [
        "Янв","Фев","Мар","Апр",
        "Май","Июн","Июл","Авг",
        "Сен","Окт","Ноя","Дек"
    ]

    result = []

    for row in rows:
        idx = int(row["month_num"]) - 1

        result.append({
            "month": month_names[idx],
            "income": row["income"] or 0,
            "expense": row["expense"] or 0
        })

    return result


def get_balance_over_time(user_id=None, year=None):

    monthly = get_monthly_summary(
        user_id=user_id,
        year=year
    )

    balance = 0

    balances = []

    for m in monthly:
        balance += m["income"] - m["expense"]
        balances.append(balance)

    months = [m["month"] for m in monthly]

    return balances, months


def get_expense_categories(user_id=None):

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            c.name as category,
            SUM(t.amount) as total
        FROM transactions t
        JOIN categories c 
            ON t.category_id=c.id
        WHERE t.type='expense'
    """

    params = []

    if user_id:
        query += " AND t.user_id=?"
        params.append(user_id)

    query += """
        GROUP BY c.id,c.name
    """

    cur.execute(query, tuple(params))

    rows = cur.fetchall()

    total_expense = sum(
        row["total"] for row in rows
    )

    conn.close()

    if total_expense == 0:
        return []

    colors = [
        "#FF9800",
        "#2196F3",
        "#795548",
        "#00BCD4",
        "#F44336",
        "#607D8B",
        "#4CAF50",
        "#9C27B0"
    ]

    result = []

    for i, row in enumerate(rows):

        percent = round(
            row["total"] / total_expense * 100
        )

        result.append({
            "label": row["category"],
            "value": percent,
            "color": colors[i % len(colors)]
        })

    return result


# ─────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────

def _title(text):
    return ft.Text(
        text,
        size=16,
        weight=ft.FontWeight.W_600,
        color="#FFFFFF"
    )


def _card(content):
    return ft.Container(
        bgcolor="#1A1A24",
        border_radius=16,
        padding=20,
        content=content
    )


# ─────────────────────────────────────────────
# AnalyticsPage
# ─────────────────────────────────────────────

class AnalyticsPage(BasePage):

    def __init__(self, page: ft.Page, user_id=None):

        self.user_id = user_id

        self.selected_year = datetime.now().year

        super().__init__(
            page,
            "Аналитика"
        )


    # ─────────────────────────────────────────

    def build_body(self):

        years = get_available_years(
            self.user_id
        )

        self.year_dropdown = ft.Dropdown(
            width=120,
            value=str(self.selected_year),
            options=[
                ft.dropdown.Option(str(y))
                for y in years
            ]
        )

        self.year_dropdown.on_change = self.on_year_change

        controls = [

            ft.Row(
                [
                    ft.Text(
                        "Выберите год:",
                        color="#FFFFFF"
                    ),
                    self.year_dropdown
                ],
                spacing=10
            ),

            self._summary(),

            _title("Доходы и расходы по месяцам"),
            _card(self._bar_chart()),

            _title("Динамика баланса"),
            _card(self._balance_chart()),

            _title("Структура расходов"),
            _card(self._category_bars())

        ]

        return ft.Column(
            scroll="vertical",
            controls=controls
        )


    # ─────────────────────────────────────────

    def on_year_change(self, e):

        self.selected_year = int(
            e.control.value
        )

        self.page.controls.clear()

        self.page.add(
            self.build_body()
        )


    # ─────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────

    def _summary(self):

        monthly = get_monthly_summary(
            user_id=self.user_id,
            year=self.selected_year
        )

        if not monthly:
            return self._empty_state(
                "Нет данных для сводки."
            )

        total_income = sum(
            d["income"] for d in monthly
        )

        total_expense = sum(
            d["expense"] for d in monthly
        )

        savings = (
            total_income - total_expense
        )

        savings_pct = (
            round(
                savings / total_income * 100
            )
            if total_income
            else 0
        )

        fmt = lambda v: (
            f"{v:,}"
            .replace(",", " ")
            + " ₽"
        )

        def tile(label, value, color, icon):

            return ft.Container(
                expand=True,
                bgcolor="#1A1A24",
                border_radius=14,
                padding=16,

                content=ft.Column(
                    [

                        ft.Row(
                            [
                                ft.Icon(
                                    icon,
                                    color=color,
                                    size=18
                                ),
                                ft.Text(
                                    label,
                                    size=12,
                                    color="#888888"
                                )
                            ],
                            spacing=6
                        ),

                        ft.Text(
                            fmt(value),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=color
                        )

                    ],
                    spacing=6
                )
            )

        return ft.Column(

            [

                ft.Row(
                    [
                        tile(
                            "Доходы",
                            total_income,
                            "#4CAF50",
                            ft.Icons.TRENDING_UP
                        ),

                        tile(
                            "Расходы",
                            total_expense,
                            "#F44336",
                            ft.Icons.TRENDING_DOWN
                        )
                    ],
                    spacing=10
                ),

                ft.Row(
                    [

                        tile(
                            "Экономия",
                            savings,
                            "#6C63FF",
                            ft.Icons.SAVINGS_OUTLINED
                        ),

                        ft.Container(
                            expand=True,
                            bgcolor="#1A1A24",
                            border_radius=14,
                            padding=16,

                            content=ft.Column(
                                [

                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.PERCENT,
                                                color="#FF9800",
                                                size=18
                                            ),

                                            ft.Text(
                                                "Норма сбережений",
                                                size=12,
                                                color="#888888"
                                            )
                                        ],
                                        spacing=6
                                    ),

                                    ft.ProgressBar(
                                        value=max(
                                            0,
                                            savings_pct
                                        ) / 100,

                                        bgcolor="#2A2A36",

                                        color="#FF9800",

                                        height=8,

                                        border_radius=4
                                    ),

                                    ft.Text(
                                        f"{savings_pct}% от доходов",
                                        size=13,
                                        color="#FF9800"
                                    )

                                ],
                                spacing=6
                            )
                        )

                    ],
                    spacing=10
                )

            ],

            spacing=10
        )


    # ─────────────────────────────────────────
    # BAR CHART
    # ─────────────────────────────────────────

    def _bar_chart(self):

        monthly = get_monthly_summary(
            self.user_id,
            self.selected_year
        )

        if not monthly:
            return self._empty_state(
                "Нет данных."
            )

        months = [m["month"] for m in monthly]

        incomes = [m["income"] for m in monthly]

        expenses = [m["expense"] for m in monthly]

        num = len(months)

        bar_width = 20

        group_width = (
            2 * bar_width + 20
        )

        chart_width = max(
            400,
            num * group_width
        )

        max_value = max(
            max(incomes),
            max(expenses),
            1
        )

        max_y = max_value * 1.25

        groups = []

        for i in range(num):

            groups.append(

                BarChartGroup(

                    x=i,

                    rods=[

                        BarChartRod(
                            from_y=0,
                            to_y=incomes[i],
                            width=bar_width,
                            color=ft.Colors.GREEN_400,
                            border_radius=3
                        ),

                        BarChartRod(
                            from_y=0,
                            to_y=expenses[i],
                            width=bar_width,
                            color=ft.Colors.RED_400,
                            border_radius=3
                        )

                    ]

                )

            )

        bottom_axis = ChartAxis(

            labels=[
                ChartAxisLabel(
                    value=i,
                    label=ft.Text(
                        months[i],
                        size=12,
                        color="#FFFFFF"  # ← белый цвет подписей
                    )
                )
                for i in range(num)
            ],

            title=ft.Text("Месяц")
        )

        chart = ft.Container(

            width=chart_width,

            height=320,

            content=BarChart(

                groups=groups,

                bottom_axis=bottom_axis,

                max_y=max_y,

                horizontal_grid_lines=ChartGridLines(
                    color="#2A2A36"
                )

            )

        )

        return ft.Row(
            scroll="always",
            controls=[chart]
        )


    # ─────────────────────────────────────────
    # LINE CHART
    # ─────────────────────────────────────────

    def _balance_chart(self):

        balances, months = get_balance_over_time(
            self.user_id,
            self.selected_year
        )

        if not balances:
            return self._empty_state(
                "Нет данных."
            )

        num = len(months)

        # ── ширина графика
        chart_width = max(
            400,
            num * 70   # немного шире точки
        )

        # ── запас сверху (для tooltip)
        max_value = max(balances)
        min_value = min(balances)

        max_y = max_value * 1.25
        min_y = min_value * 1.1 if min_value < 0 else 0

        # ── создаём точки
        points = [
            LineChartDataPoint(
                x=i,
                y=balances[i]
            )
            for i in range(num)
        ]

        series = LineChartData(
            points=points,
            stroke_width=3,
            color=ft.Colors.PURPLE_400,
            curved=False
        )

        # ── подписи месяцев с белым цветом
        bottom_axis = ChartAxis(

            labels=[
                ChartAxisLabel(
                    value=i,
                    label=ft.Text(
                        months[i],
                        size=12,
                        color="#FFFFFF"  # ← белый цвет подписей
                    )
                )
                for i in range(num)
            ],

            title=ft.Text("Месяц")
        )

        chart = ft.Container(

            width=chart_width,

            height=320,

            content=LineChart(

                data_series=[series],

                bottom_axis=bottom_axis,

                # ── ВАЖНО: боковые отступы
                min_x=-0.5,
                max_x=num - 0.5,

                min_y=min_y,
                max_y=max_y,

                horizontal_grid_lines=ChartGridLines(
                    color="#2A2A36"
                ),

                expand=True
            )

        )

        return ft.Row(
            scroll="always",
            controls=[chart]
        )


    # ─────────────────────────────────────────

    def _category_bars(self):

        categories = get_expense_categories(
            self.user_id
        )

        if not categories:
            return self._empty_state(
                "Нет данных."
            )

        rows = []

        for cat in categories:

            rows.append(

                ft.Column(

                    [

                        ft.Row(
                            [

                                ft.Text(
                                    cat["label"],
                                    size=13,
                                    color="#CCCCCC",
                                    expand=True
                                ),

                                ft.Text(
                                    f"{cat['value']}%",
                                    size=13,
                                    color=cat["color"],
                                    weight=ft.FontWeight.W_600
                                )

                            ]
                        ),

                        ft.ProgressBar(
                            value=cat["value"] / 100,
                            bgcolor="#2A2A36",
                            color=cat["color"],
                            height=8,
                            border_radius=4
                        )

                    ],

                    spacing=6

                )

            )

        return ft.Column(
            rows,
            spacing=14
        )


    # ─────────────────────────────────────────

    def _empty_state(self, message):

        return ft.Container(

            content=ft.Text(
                message,
                size=14,
                color="#888888"
            ),

            alignment=ft.Alignment.CENTER,

            height=200

        )