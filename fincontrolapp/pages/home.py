import flet as ft
import os
import threading
import time
from datetime import datetime
from components.base_page import BasePage
from components.empty_state import empty_state
from utils import get_currency_symbol, format_amount


def _format_time_left(remind_at: str) -> str:
    """Return time left like '2 ч 15 мин', '45 мин', or 'Пора!'."""
    try:
        target = datetime.strptime(remind_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ""
    delta = target - datetime.now()
    total_seconds = int(delta.total_seconds())
    if total_seconds <= 0:
        return "Пора!"
    hours, rem = divmod(total_seconds, 3600)
    minutes = rem // 60
    if hours > 0:
        return f"{hours} ч {minutes} мин" if minutes else f"{hours} ч"
    return f"{minutes} мин"



def _find_graph_asset_src() -> str | None:
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

# ── Skeleton helpers ──────────────────────────────────────────────────────────

_SKEL_COLOR = "rgba(72,62,183,0.10)"


def _skel_box(width, height, radius=12) -> ft.Container:
    return ft.Container(
        width=width,
        height=height,
        border_radius=radius,
        bgcolor=_SKEL_COLOR,
    )


def _transaction_skel_row() -> ft.Container:
    return ft.Container(
        padding=ft.Padding(left=0, right=0, top=12, bottom=12),
        border=ft.Border(bottom=ft.BorderSide(1, "rgba(72,62,183,0.08)")),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row([
                    _skel_box(width=36, height=36, radius=18),
                    ft.Column([
                        _skel_box(width=100, height=13, radius=6),
                        _skel_box(width=70,  height=11, radius=6),
                    ], spacing=5),
                ], spacing=12),
                _skel_box(width=70, height=13, radius=6),
            ],
        ),
    )


def _skeleton_body() -> ft.Column:
    return ft.Column(
        controls=[
            # Карточка баланса
            _skel_box(width=float("inf"), height=195, radius=24),

            # Быстрые действия
            _skel_box(width=160, height=20, radius=8),
            ft.Row(
                controls=[_skel_box(width=78, height=88, radius=18) for _ in range(4)],
                spacing=12,
            ),

            # График
            _skel_box(width=120, height=20, radius=8),
            _skel_box(width=float("inf"), height=180, radius=16),

            # Транзакции
            _skel_box(width=200, height=20, radius=8),
            ft.Container(
                border_radius=16,
                bgcolor=_SKEL_COLOR,
                padding=ft.Padding(left=16, right=16, top=4, bottom=4),
                content=ft.Column(
                    controls=[_transaction_skel_row() for _ in range(4)],
                    spacing=0,
                ),
            ),
        ],
        spacing=20,
    )


# ── Page ──────────────────────────────────────────────────────────────────────

class HomePage(BasePage):

    def __init__(self, page, ctrl):
        self._ctrl = ctrl
        self._rate_widget: ft.Container | None = None
        super().__init__(page, "Главная")

    def build_header(self):
        return ft.AppBar(
            title=ft.Text(
                "Главная",
                font_family="Montserrat Extrabold",
                size=36,
            ),
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            toolbar_height=50,
        )

    def build_body(self):
        self._body_container = ft.Container(
            content=_skeleton_body(),
            opacity=1,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        )
        threading.Thread(target=self._load_data, daemon=True).start()
        return self._body_container
    def _load_data(self):
        try:
            balance      = self._ctrl.get_balance()
            monthly      = self._ctrl.get_monthly_balance()
            transactions = self._ctrl.get_recent_transactions(limit=5)
        except Exception:
            return

        # ── Загрузка настроек валюты из БД ───────────────────────────────────
        user_id = self._ctrl._user_id
        if user_id:
            try:
                from db_queries import get_user_currency
                db_currency, db_conv, db_secondary = get_user_currency(user_id)
                self.page_ref.data["_s_currency"] = db_currency
                self.page_ref.data["_s_currency_conv"] = db_conv
                self.page_ref.data["_s_secondary_currency"] = db_secondary
            except Exception:
                pass

        # Fade out скелетон
        self._body_container.opacity = 0
        try: 
            self._body_container.update()
        except Exception:  
            return

        time.sleep(0.25)

        # Подменяем контент и fade in
        self._body_container.content = self._real_body(balance, monthly, transactions)
        self._body_container.opacity = 1
        try: 
            self._body_container.update()
        except Exception:  
            pass

    # ── Real content ──────────────────────────────────────────────────────────

    def _real_body(self, balance, monthly, transactions) -> ft.Column:
        rub_balance = balance["balance"]
        rate_widget = self._build_rate_widget(rub_balance)
        top_block_controls = [self._balance_card(balance, monthly)]
        if rate_widget is not None:
            top_block_controls.append(rate_widget)
        top_block = ft.Column(controls=top_block_controls, spacing=8)

        controls = [
            top_block,
            ft.Text("Быстрые действия", size=20,
                    font_family="Montserrat Semibold", color="#000000"),
            ft.Row(
                controls=[
                    self._quick_action_icon(ft.Icons.ADD_CIRCLE_OUTLINE,     "Доходы",  "#000000", lambda e: self.page_ref.data["navigate"](5)),
                    self._quick_action_icon(ft.Icons.REMOVE_CIRCLE_OUTLINE,  "Расходы", "#000000", lambda e: self.page_ref.data["navigate"](6)),
                    self._quick_action_icon(ft.Icons.STAR_OUTLINE,           "Цель",    "#000000", lambda e: self.page_ref.data["navigate"](2)),
                    self._quick_action_icon(ft.Icons.SUBSCRIPTIONS_OUTLINED, "Подписки","#000000", lambda e: self.page_ref.data["navigate"](4)),
                ],
                spacing=12,
            ),
            ft.Container(
                border_radius=12,
                padding=ft.Padding(left=16, right=16, top=14, bottom=14),
                bgcolor="#483EB7",
                on_click=lambda e: self._show_purchase_timer_dialog(),
                ink=True,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.TIMER_OUTLINED, color="#FFFFFF", size=18),
                        ft.Text(
                            "Таймер покупки",
                            color="#FFFFFF",
                            font_family="Montserrat SemiBold",
                            size=13,
                        ),
                    ],
                ),
            ),
            *self._timer_list(),
        ]

        if GRAPH_ASSET_SRC:
            controls.extend([
                ft.Text("Графики", size=20,
                        font_family="Montserrat Semibold", color="#000000"),
                self._graph_svg_preview(),
            ])

        # ── Последние операции с видимым affordance ──────────────────────
        controls.append(
            ft.GestureDetector(
                on_tap=lambda e: self.page_ref.data["navigate"](7),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.START,
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "Последние операции",
                                    size=20,
                                    font_family="Montserrat Semibold",
                                    color="#000000",
                                ),
                                ft.Container(
                                    border_radius=20,
                                    padding=ft.Padding(left=10, right=10, top=5, bottom=5),
                                    gradient=ft.LinearGradient(
                                        colors=["#ffffff", "#88A2FF"],
                                        begin=ft.Alignment(-4, -1),
                                        end=ft.Alignment(1, 7),
                                    ),
                                    content=ft.Row(
                                        spacing=2,
                                        tight=True,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                                size=16,
                                                color="#483EB7",
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        self._transactions_list(transactions),
                    ],
                    spacing=12,
                ),
            )
        )

        return ft.Column(controls=controls, spacing=20)
    def _build_rate_widget(self, balance_rub: float) -> ft.Control:
        """Плашка: курс первой валюты ко второй + баланс во второй валюте.

        Показывается только если выбрана вторая валюта.
        """
        from utils import CURRENCY_SYMBOLS
        currency = self.page_ref.data.get("_s_currency", "RUB")
        secondary = self.page_ref.data.get("_s_secondary_currency")

        # Плашка нужна только когда есть вторая валюта
        if not secondary:
            return None

        spinner = ft.ProgressRing(width=12, height=12, stroke_width=2, color="#483EB7")
        row_controls = ft.Row(
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.CURRENCY_EXCHANGE, color="#483EB7", size=14),
                spinner,
            ],
        )

        self._rate_widget = ft.Container(
            border_radius=12,
            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            bgcolor=ft.Colors.with_opacity(0.08, "#483EB7"),
            alignment=ft.Alignment(-1, 0),
            content=row_controls,
        )

        def _load():
            from currency import fetch_rates
            rates = fetch_rates() or {}

            # Вычисляем курс первой валюты в рублях (RUB → 1.0)
            rate_primary = rates.get(currency) if currency != "RUB" else 1.0
            rate_secondary = rates.get(secondary) if secondary != "RUB" else 1.0

            parts = []

            if rate_primary is not None and rate_secondary is not None and rate_secondary > 0:
                # Курс: 1 <первая> = X <вторая>
                cross_rate = rate_primary / rate_secondary
                pri_sym = CURRENCY_SYMBOLS.get(currency, currency) if currency != "RUB" else "₽"
                sec_sym = CURRENCY_SYMBOLS.get(secondary, secondary) if secondary != "RUB" else "₽"

                # Форматируем cross_rate: для мелких значений (< 1) показываем 4 знака
                if cross_rate < 0.01:
                    rate_str = f"{cross_rate:.4f}"
                elif cross_rate < 1:
                    rate_str = f"{cross_rate:.3f}"
                else:
                    rate_str = f"{cross_rate:,.2f}"

                parts.append(ft.Text(
                    f"1 {pri_sym} = {rate_str} {sec_sym}",
                    font_family="Montserrat SemiBold",
                    size=13,
                    color="#483EB7",
                ))

                # Разделитель
                parts.append(ft.Text(
                    "·",
                    font_family="Montserrat SemiBold",
                    size=13,
                    color=ft.Colors.with_opacity(0.4, "#483EB7"),
                ))

                # Баланс во второй валюте
                # balance_rub хранится в рублях, пересчитываем через rate_secondary
                sec_balance = round(balance_rub / rate_secondary, 2)
                parts.append(ft.Text(
                    f"≈ {sec_balance:,.2f} {sec_sym}",
                    font_family="Montserrat SemiBold",
                    size=13,
                    color="#483EB7",
                ))
            else:
                parts.append(ft.Text(
                    "Курс недоступен",
                    font_family="Montserrat SemiBold",
                    size=13,
                    color="#9E9E9E",
                ))

            row_controls.controls = [
                ft.Icon(ft.Icons.CURRENCY_EXCHANGE, color="#483EB7", size=14),
                *parts,
            ]
            try:
                self._rate_widget.update()
            except Exception:
                pass

        threading.Thread(target=_load, daemon=True).start()
        return self._rate_widget

    def _balance_card(self, balance, monthly):
        # Применяем конвертацию баланса если нужно
        currency = self.page_ref.data.get("_s_currency", "RUB")
        conv_mode = self.page_ref.data.get("_s_currency_conv", "as_is")
        symbol = get_currency_symbol(self.page_ref)

        rub_balance = balance['balance']
        rub_income = monthly['income']
        rub_expense = monthly['expense']

        if currency != "RUB" and conv_mode == "convert":
            from currency import fetch_rates
            rates = fetch_rates()
            rate = rates.get(currency) if rates else None
            if rate and rate > 0:
                disp_balance = round(rub_balance / rate, 2)
                disp_income = round(rub_income / rate, 2)
                disp_expense = round(rub_expense / rate, 2)
            else:
                disp_balance, disp_income, disp_expense = rub_balance, rub_income, rub_expense
        else:
            disp_balance, disp_income, disp_expense = rub_balance, rub_income, rub_expense

        def _fmt(value: float) -> str:
            if currency == "RUB":
                return f"{value:,.0f} {symbol}"
            return f"{value:,.2f} {symbol}"

        return ft.Container(
            height=190,
            border_radius=24,
            padding=24,
            gradient=ft.LinearGradient(
                colors=["#ffffff", "#88A2FF"],
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 3),
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Общий баланс", size=20,
                        font_family="Montserrat Semibold",
                        color="rgba(0,0,0,0.3)",
                    ),
                    ft.Text(
                        _fmt(disp_balance),
                        font_family="Montserrat Semibold",
                        size=36, color="#000000",
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(
                                bgcolor="#E3FC87", border_radius=16,
                                padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.ARROW_UPWARD, color="#2A4A00", size=16),
                                        ft.Text(
                                            _fmt(disp_income),
                                            font_family="Montserrat Semibold",
                                            color="#2A4A00",
                                            size=14,
                                        ),
                                    ],
                                    spacing=8, tight=True,
                                ),
                            ),
                            ft.Container(
                                bgcolor="#FFEC60", border_radius=16,
                                padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.ARROW_DOWNWARD, color="#4A3A00", size=16),
                                        ft.Text(
                                            _fmt(disp_expense),
                                            font_family="Montserrat Semibold",
                                            color="#4A3A00",
                                            size=14,
                                        ),
                                    ],
                                    spacing=8, tight=True,
                                ),
                            ),
                        ],
                        spacing=10, wrap=True, run_spacing=8,
                    ),
                ],
                spacing=15,
            ),
        )
    def _graph_svg_preview(self):
        return ft.Container(
            height=180,
            border_radius=16,
            gradient=ft.LinearGradient(
                colors=["#ffffff", "#88A2FF"],
                begin=ft.Alignment(-4, -1),
                end=ft.Alignment(1, 7),
            ),
            padding=12,
            content=ft.Image(src=GRAPH_ASSET_SRC, fit="contain", expand=True),
        )

    def _transactions_list(self, transactions):
        if not transactions:
            return empty_state(
                icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                title="Операций пока нет",
                subtitle="Добавьте первый доход или расход",
            )

        rows = []
        for t in transactions:
            is_income = t['type'] == 'income'
            rows.append(
                ft.Container(
                    padding=ft.Padding(left=0, right=0, top=10, bottom=10),
                    border=ft.Border(bottom=ft.BorderSide(1, "#E0E0E0")),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row([
                                ft.Container(
                                    width=36, height=36, border_radius=18,
                                    bgcolor=ft.Colors.with_opacity(0.6, "#FFFFFF"),
                                    content=ft.Icon(
                                        ft.Icons.ARROW_UPWARD if is_income else ft.Icons.ARROW_DOWNWARD,
                                        color="#253A82" if is_income else ft.Colors.with_opacity(0.6, "#FF7E1C"),
                                        size=18,
                                    ),
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column([
                                    ft.Text(t['category_name'], size=15, color="#253A82",
                                            weight=ft.FontWeight.W_500,
                                            font_family="Montserrat SemiBold"),
                                    ft.Text(t['description'] or t['date'], size=13,
                                            color=ft.Colors.with_opacity(0.6, "#253A82"),
                                            font_family="Montserrat SemiBold"),
                                ], spacing=2),
                            ], spacing=12),
                            ft.Text(
                                format_amount(t['amount'], self.page_ref, '+ ' if is_income else '− '),
                                color="#253A82" if is_income else ft.Colors.with_opacity(0.6, "#FF7E1C"),
                                size=15, font_family="Montserrat SemiBold",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                    ),
                )
            )

        return ft.Container(
            border_radius=16,
            gradient=ft.LinearGradient(
                colors=["#ffffff", "#88A2FF"],
                begin=ft.Alignment(-4, -1),
                end=ft.Alignment(1, 7),
            ),
            padding=ft.Padding(left=16, right=16, top=4, bottom=4),
            content=ft.Column(rows, spacing=0),
        )

    def _timer_list(self) -> list:
        """Список активных таймеров с остатком времени справа. Пусто — пустой список."""
        from db_queries import get_active_purchase_timers, delete_purchase_timer
        uid = self._ctrl._user_id
        if not uid:
            return []
        timers = get_active_purchase_timers(uid)
        if not timers:
            return []

        def make_dismiss_handler(timer_id):
            def on_dismiss(e):
                delete_purchase_timer(timer_id, uid)
                self.refresh()
            return on_dismiss

        rows = []
        for t in timers:
            time_left = _format_time_left(t["remind_at"])
            is_due = time_left == "Пора!"

            row_content = ft.Container(
                bgcolor="#FFFFFF",
                padding=ft.Padding(left=14, right=14, top=10, bottom=10),
                border=ft.Border(bottom=ft.BorderSide(1, "#E8E8F0")),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=10,
                            tight=True,
                            controls=[
                                ft.Icon(ft.Icons.TIMER_OUTLINED, size=18, color="#483EB7"),
                                ft.Text(
                                    t["item_name"],
                                    font_family="Montserrat SemiBold",
                                    size=14,
                                    color="#1a1a1a",
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                        ),
                        ft.Text(
                            time_left,
                            font_family="Montserrat SemiBold",
                            size=13,
                            color="#E53935" if is_due else "#483EB7",
                        ),
                    ],
                ),
            )

            rows.append(
                ft.Dismissible(
                    content=row_content,
                    background=ft.Container(
                        bgcolor="#FFEBEE",
                        padding=ft.Padding(left=20, right=20, top=0, bottom=0),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            controls=[
                                ft.Icon(ft.Icons.DELETE_OUTLINE, color="#E53935", size=22),
                            ],
                        ),
                    ),
                    on_dismiss=make_dismiss_handler(t["id"]),
                )
            )

        return [
            ft.Container(
                border_radius=16,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                gradient=ft.LinearGradient(
                    colors=["#ffffff", "#88A2FF"],
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                ),
                padding=ft.Padding(left=0, right=0, top=4, bottom=4),
                content=ft.Column(rows, spacing=0),
            )
        ]

    def _show_purchase_timer_dialog(self):
        from datetime import datetime, timedelta
        from db_queries import create_purchase_timer
        from components import show_dialog, close_dialog

        item_field = ft.TextField(
            label="Название товара",
            text_style=ft.TextStyle(font_family="Montserrat Medium"),
            label_style=ft.TextStyle(font_family="Montserrat Medium"),
            border_color="#6976EB",
        )
        amount_field = ft.TextField(
            label="Цена (₽)",
            keyboard_type=ft.KeyboardType.NUMBER,
            text_style=ft.TextStyle(font_family="Montserrat Medium"),
            label_style=ft.TextStyle(font_family="Montserrat Medium"),
            border_color="#6976EB",
        )
        hours_field = ft.TextField(
            label="Напомнить через (часов)",
            value="24",
            keyboard_type=ft.KeyboardType.NUMBER,
            text_style=ft.TextStyle(font_family="Montserrat Medium"),
            label_style=ft.TextStyle(font_family="Montserrat Medium"),
            border_color="#6976EB",
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Таймер покупки", font_family="Montserrat SemiBold"),
        )

        def on_save(e):
            item = (item_field.value or "").strip()
            if not item:
                return
            try:
                amount = float((amount_field.value or "0").replace(",", "."))
                hours = int(hours_field.value or "24")
            except ValueError:
                return
            if amount <= 0 or hours <= 0:
                return

            remind_at = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            uid = self._ctrl._user_id
            if uid:
                create_purchase_timer(uid, item, amount, remind_at)

            close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(
                ft.Text(
                    f"Напомню про «{item}» через {hours} ч.",
                    font_family="Montserrat Medium",
                ),
                open=True,
            )
            self.refresh()

        def on_cancel(e):
            close_dialog(self.page_ref, dlg)

        dlg.content = ft.Column(
            controls=[item_field, amount_field, hours_field],
            tight=True,
            spacing=12,
        )
        dlg.actions = [
            ft.TextButton(
                "Отмена",
                on_click=on_cancel,
                style=ft.ButtonStyle(
                    color="#483EB7",
                    text_style=ft.TextStyle(font_family="Montserrat SemiBold"),
                ),
            ),
            ft.TextButton(
                "Создать",
                on_click=on_save,
                style=ft.ButtonStyle(
                    color="#483EB7",
                    text_style=ft.TextStyle(font_family="Montserrat SemiBold"),
                ),
            ),
        ]

        show_dialog(self.page_ref, dlg)

    def _quick_action_icon(self, icon, label, color, on_click=None):
        return ft.Container(
            border_radius=18,
            padding=10,
            width=58,
            on_click=on_click,
            gradient=ft.LinearGradient(
                colors=["#ffffff", "#88A2FF"],
                begin=ft.Alignment(-4, -1),
                end=ft.Alignment(1, 7),
            ),
            content=ft.Icon(icon, color=color, size=28),
            alignment=ft.Alignment(0, 0),
            ink=True,
        )