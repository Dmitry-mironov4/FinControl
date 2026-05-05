import flet as ft
import os
import threading
import time
from components.base_page import BasePage
from components.empty_state import empty_state



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

        # Fade out скелетон
        self._body_container.opacity = 0
        try: self._body_container.update()
        except: return

        time.sleep(0.25)

        # Подменяем контент и fade in
        self._body_container.content = self._real_body(balance, monthly, transactions)
        self._body_container.opacity = 1
        try: self._body_container.update()
        except: pass

    # ── Real content ──────────────────────────────────────────────────────────

    def _real_body(self, balance, monthly, transactions) -> ft.Column:
        controls = [
            self._balance_card(balance, monthly),
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
        ]

        if GRAPH_ASSET_SRC:
            controls.extend([
                ft.Text("Графики", size=20,
                        font_family="Montserrat Semibold", color="#000000"),
                self._graph_svg_preview(),
            ])

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

    # ── Widgets ───────────────────────────────────────────────────────────────

    def _balance_card(self, balance, monthly):
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
                                    f"{balance['balance']:,.0f} ₽",
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
                                                    ft.Text(f"{monthly['income']:,.0f} ₽",
                                                            font_family="Montserrat Semibold",
                                                            color="#2A4A00", size=14),
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
                                                    ft.Text(f"{monthly['expense']:,.0f} ₽",
                                                            font_family="Montserrat Semibold",
                                                            color="#4A3A00", size=14),
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
                                f"{'+ ' if is_income else '− '}{t['amount']:,.0f} ₽",
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