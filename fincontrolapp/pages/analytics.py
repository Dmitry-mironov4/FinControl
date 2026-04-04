"""
analytics.py — Экран аналитики финансов.

Показывает четыре блока:
1. Сводные плашки — итоги за период (доходы, расходы, экономия, норма сбережений).
2. Столбчатая диаграмма (доходы/расходы по месяцам) — через BarChart из flet_charts.
3. Линейный график накопленного баланса — через LineChart из flet_charts.
4. Структура расходов по категориям — горизонтальные прогресс-бары.

Все данные загружаются из БД через функции get_monthly_summary(),
get_expense_categories() и get_balance_over_time().
"""
import flet as ft
from flet_charts import BarChart, BarChartGroup, BarChartRod, LineChart, LineChartData, ChartPointLine
from flet_charts import ChartAxis, ChartAxisLabel
import os
from components.base_page import BasePage
from database import get_connection   # добавить импорт работы с БД
from datetime import datetime, timedelta

# ─── Функции работы с БД для аналитики ──────────────────────────────────────

def get_monthly_summary(year=None):
    """
    Возвращает список словарей с доходами и расходами по месяцам.
    Если year не указан — берёт текущий год.
    """
    conn = get_connection()
    cur = conn.cursor()
    if year is None:
        year = datetime.now().year
    
    # Получаем доходы и расходы по месяцам
    cur.execute("""
        SELECT 
            strftime('%m', date) as month_num,
            strftime('%m', date) as month,
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
        FROM transactions
        WHERE strftime('%Y', date) = ?
        GROUP BY month_num
        ORDER BY month_num
    """, (str(year),))
    
    rows = cur.fetchall()
    conn.close()
    
    # Преобразуем номер месяца в название (Янв, Фев, …)
    month_names = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                   "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    
    result = []
    for row in rows:
        month_idx = int(row["month_num"]) - 1
        result.append({
            "month": month_names[month_idx],
            "income": row["income"] or 0,
            "expense": row["expense"] or 0,
        })
    
    # Если за какой-то месяц нет данных, можно добавить нули (опционально)
    # Здесь для простоты возвращаем только те месяцы, где есть хоть одна операция.
    # Но лучше вернуть все 12 месяцев с нулями – тогда график будет полным.
    # Реализуйте по желанию.
    return result


def get_expense_categories():
    """Возвращает структуру расходов по категориям (в процентах)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE type = 'expense'
        GROUP BY category
    """)
    rows = cur.fetchall()
    total_expense = sum(row["total"] for row in rows)
    conn.close()
    
    if total_expense == 0:
        return []
    
    # Список цветов для категорий
    colors = ["#FF9800", "#2196F3", "#795548", "#00BCD4", "#F44336", "#607D8B", "#4CAF50", "#9C27B0"]
    result = []
    for i, row in enumerate(rows):
        percent = round(row["total"] / total_expense * 100)
        result.append({
            "label": row["category"],
            "value": percent,
            "color": colors[i % len(colors)]
        })
    return result


def get_balance_over_time():
    """Возвращает список накопленного баланса по месяцам (как в _balance_chart)."""
    monthly = get_monthly_summary()
    balance = 0
    balances = []
    for m in monthly:
        balance += m["income"] - m["expense"]
        balances.append(balance)
    return balances, [m["month"] for m in monthly]


def _find_graph_asset_src() -> str | None:
    """Возвращает относительный путь до SVG с графиками, если он есть в assets."""
    candidates = [
        "analytics/graphs.svg",
        "analytics/graph.svg",
        "home/graphs.svg",
        "home/graph.svg",
        "graphs.svg",
        "graph.svg",
    ]
    assets_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
    for src in candidates:
        if os.path.exists(os.path.join(assets_root, src)):
            return src
    return None


GRAPH_ASSET_SRC = _find_graph_asset_src()


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
        controls = [self._summary()]

        # Если в assets добавлен SVG-макет графиков, показываем его отдельным блоком.
        if GRAPH_ASSET_SRC:
            controls.extend([
                _title("Графики (SVG макет)"),
                _card(self._svg_graphs()),
            ])

        controls.extend([
            _title("Доходы и расходы по месяцам"),
            _card(self._bar_chart()),
            _title("Динамика баланса"),
            _card(self._balance_chart()),
            _title("Структура расходов"),
            _card(self._category_bars()),
        ])
        return ft.Column(controls, spacing=16)

    def _svg_graphs(self):
        return ft.Container(
            height=220,
            content=ft.Image(
                src=GRAPH_ASSET_SRC,
                fit=ft.ImageFit.CONTAIN,
                expand=True,
            ),
        )

    # ── Сводные плашки ────────────────────────────────────────────────────────
    def _summary(self):
        """
        Строит блок сводных плашек (4 карточки 2×2).
        Данные берутся из БД через get_monthly_summary().
        """
        monthly = get_monthly_summary()
        if not monthly:
            return self._empty_state("Нет данных для отображения сводки.")

        total_income  = sum(d["income"]  for d in monthly)
        total_expense = sum(d["expense"] for d in monthly)
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
        Использует встроенный BarChart из flet_charts.
        """
        monthly = get_monthly_summary()  # функция из шага 2
        if not monthly:
            return self._empty_state("Нет данных для построения графика доходов и расходов.")

        months = [m["month"] for m in monthly]
        incomes = [m["income"] for m in monthly]
        expenses = [m["expense"] for m in monthly]

        max_val = max(max(incomes), max(expenses))
        if max_val == 0:
            return self._empty_state("Нет операций за выбранный период.")

        # Группы баров: для каждого месяца – два бара (доход, расход)
        bar_groups = []
        for i, month in enumerate(months):
            bar_groups.append(
                BarChartGroup(
                    x=i,
                    bar_rods=[
                        BarChartRod(
                            from_y=0,
                            to_y=incomes[i],
                            width=20,
                            color=ft.colors.GREEN_400,
                            border_radius=3,
                        ),
                        BarChartRod(
                            from_y=0,
                            to_y=expenses[i],
                            width=20,
                            color=ft.colors.RED_400,
                            border_radius=3,
                        ),
                    ],
                )
            )

        # Ось X (месяцы)
        bottom_axis = ChartAxis(
            labels=[ChartAxisLabel(value=i, label=ft.Text(month, size=12)) for i, month in enumerate(months)],
            title=ft.Text("Месяц", size=14),
        )

        # Ось Y (динамическая шкала с шагом, например, 20 000 ₽)
        step = 20000
        max_label = max_val + (step - max_val % step) if max_val % step != 0 else max_val
        labels_y = [ChartAxisLabel(value=v, label=ft.Text(f"{v//1000}к", size=10))
                    for v in range(0, int(max_label) + 1, step)]
        left_axis = ChartAxis(labels=labels_y, title=ft.Text("Сумма (₽)", size=14))

        chart = BarChart(
            expand=True,
            bar_groups=bar_groups,
            bottom_axis=bottom_axis,
            left_axis=left_axis,
            horizontal_grid_lines=ft.charts.ChartGridLines(color="#2A2A36"),
        )

        # Легенда (как в старом дизайне)
        legend = ft.Row([
            ft.Row([ft.Container(width=12, height=12, bgcolor=ft.colors.GREEN_400, border_radius=3),
                    ft.Text("Доходы", size=12, color="#888888")], spacing=6),
            ft.Row([ft.Container(width=12, height=12, bgcolor=ft.colors.RED_400, border_radius=3),
                    ft.Text("Расходы", size=12, color="#888888")], spacing=6),
        ], spacing=20)

        return ft.Column([chart, legend], spacing=8)

    # ── График баланса через Stack ────────────────────────────────────────────
    def _balance_chart(self):
        """
        Линейный график накопленного баланса (доходы − расходы) по месяцам.
        Данные: get_balance_over_time() → список балансов и месяцев.
        При пустых данных — заглушка _empty_state().
        Ось Y: симметричная (от −max до +max) с шагом 20 000 ₽, подписи в тысячах.
        Линия: прямая (curved=False), толщина 3, цвет PURPLE_400.
        Возвращает LineChart из flet_charts.
        
        """
    
        balances, months = get_balance_over_time()
        if not balances or all(b == 0 for b in balances):
            return self._empty_state("Нет данных для построения графика баланса.")
        
        # Точки для линии
        points = [ChartPointLine(x=i, y=balances[i]) for i in range(len(balances))]
        line_series = LineChartData(
            data_points=points,
            stroke_width=3,
            color=ft.colors.PURPLE_400,
            curved=False,  # прямые линии между точками (как было в ручной реализации)
        )
        
        # Оси
        bottom_axis = ChartAxis(
            labels=[ChartAxisLabel(value=i, label=ft.Text(months[i], size=12)) for i in range(len(months))],
            title=ft.Text("Месяц", size=14),
        )
        
        max_bal = max(balances) if balances else 0
        min_bal = min(balances) if balances else 0
        # Делаем ось Y симметричной относительно нуля, если есть отрицательный баланс
        y_max = max(abs(max_bal), abs(min_bal)) or 1
        step = 20000
        # Округляем y_max вверх до ближайшего числа, кратного step
        max_label = ((y_max + step - 1) // step) * step
        labels_y = []
        for v in range(-max_label, max_label + 1, step):
            labels_y.append(ChartAxisLabel(value=v, label=ft.Text(f"{v//1000}к", size=10)))
        left_axis = ChartAxis(labels=labels_y, title=ft.Text("Баланс (₽)", size=14))
        
        chart = LineChart(
            expand=True,
            data_series=[line_series],
            bottom_axis=bottom_axis,
            left_axis=left_axis,
            horizontal_grid_lines=ft.charts.ChartGridLines(color="#2A2A36"),
        )
        return chart

    # ── Горизонтальные бары категорий (реальные данные из БД) ─────────────────────
    def _category_bars(self):
        """
        Строит блок горизонтальных прогресс-баров по категориям расходов.
        Данные получает из БД через get_expense_categories().
        Если категорий нет — показывает заглушку.
        """
        categories = get_expense_categories()   # получаем данные из БД
        if not categories:
            return self._empty_state("Нет данных о расходах по категориям.")

        rows = []
        for cat in categories:
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
    
    def _empty_state(self, message="Нет данных за выбранный период."):
        " Заглушка "
        return ft.Container(
            content=ft.Text(message, size=14, color="#888888", text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            height=200,
        )