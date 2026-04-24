import flet as ft
import os
from components.base_page import BasePage



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
        balance = self._ctrl.get_balance()
        monthly = self._ctrl.get_monthly_balance()
        transactions = self._ctrl.get_recent_transactions(limit=5)

        controls = [
            self._balance_card(balance, monthly),
            ft.Text(
                "Быстрые действия",
                size=20,
                font_family="Montserrat Semibold",
                color="#000000",
            ),
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
                ft.Text("Графики", size=20, font_family="Montserrat Semibold", color="#000000"),
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
                            spacing = 8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "Последние операции",
                                    size=20,
                                    font_family="Montserrat Semibold",
                                    color="#000000",
                                ),
                                # Кнопка «Все →» — явный сигнал, что можно тапнуть
                                ft.Container(
                                    border_radius=20,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    gradient=ft.LinearGradient(
                                        colors=["#ffffff", "#88A2FF"],
                                        begin=ft.Alignment(-1, -1),
                                        end=ft.Alignment(1, 1),
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

    def _balance_card(self, balance, monthly):
        return ft.Container(
            height=195,
            border_radius=24,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Image(src="home/card_bg.svg", fit="fill", expand=True),
                    ft.Container(
                        padding=24,
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Общий баланс",
                                    size=20,
                                    font_family="Montserrat Semibold",
                                    color="rgba(0,0,0,0.3)",
                                ),
                                ft.Text(
                                    f"{balance['balance']:,.0f} ₽",
                                    font_family="Montserrat Semibold",
                                    size=36,
                                    color="#000000",
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            bgcolor="#E3FC87",
                                            border_radius=16,
                                            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                                            content=ft.Row(
                                                controls=[
                                                    ft.Icon(ft.Icons.ARROW_UPWARD, color="#2A4A00", size=16),
                                                    ft.Text(
                                                        f"{monthly['income']:,.0f} ₽",
                                                        font_family="Montserrat Semibold",
                                                        color="#2A4A00",
                                                        size=14,
                                                    ),
                                                ],
                                                spacing=4,
                                                tight=True,
                                            ),
                                        ),
                                        ft.Container(
                                            bgcolor="#FFEC60",
                                            border_radius=16,
                                            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                                            content=ft.Row(
                                                controls=[
                                                    ft.Icon(ft.Icons.ARROW_DOWNWARD, color="#4A3A00", size=16),
                                                    ft.Text(
                                                        f"{monthly['expense']:,.0f} ₽",
                                                        font_family="Montserrat Semibold",
                                                        color="#4A3A00",
                                                        size=14,
                                                    ),
                                                ],
                                                spacing=4,
                                                tight=True,
                                            ),
                                        ),
                                    ],
                                    spacing=8,
                                    wrap=True,
                                    run_spacing=8,
                                ),
                            ],
                            spacing=7,
                        ),
                    ),
                ],
            ),
        )

    def _graph_svg_preview(self):
        return ft.Container(
            height=180,
            border_radius=16,
            gradient=ft.LinearGradient(
                colors=["#ffffff", "#88A2FF"],
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
            ),
            padding=12,
            content=ft.Image(src=GRAPH_ASSET_SRC, fit=ft.ImageFit.CONTAIN, expand=True),
        )

    def _transactions_list(self, transactions):
        if not transactions:
            return ft.Container(
                height=80,
                expand=True,
                border_radius=16,
                gradient=ft.LinearGradient(
                    colors=["#ffffff", "#88A2FF"],
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                ),
                alignment=ft.Alignment(0, 0),
                content=ft.Text(
                    "Операций пока нет",
                    color="#000000",
                    font_family="Montserrat Semibold",
                    size=14,
                ),
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
                                    width=36, height=36,
                                    border_radius=18,
                                    bgcolor=ft.Colors.with_opacity(0.6, "#FFFFFF"),
                                    content=ft.Icon(
                                        ft.Icons.ARROW_UPWARD if is_income else ft.Icons.ARROW_DOWNWARD,
                                        color="#253A82" if is_income else ft.Colors.with_opacity(0.6, "#FF7E1C"),
                                        size=18,
                                    ),
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column([
                                    ft.Text(t['category_name'], size=15, color="#253A82", weight=ft.FontWeight.W_500, font_family="Montserrat SemiBold"),
                                    ft.Text(t['description'] or t['date'], size=13, color=ft.Colors.with_opacity(0.6, "#253A82"), font_family="Montserrat SemiBold"),
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
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
            ),
            padding=ft.Padding(left=16, right=16, top=4, bottom=4),
            content=ft.Column(rows, spacing=0),
        )

    def _quick_action_icon(self, icon, label, color, on_click=None):
        return ft.Container(
            border_radius=18,
            padding=10,
            width=78,
            on_click=on_click,
            gradient=ft.LinearGradient(
                colors=["#ffffff", "#88A2FF"],
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
            ),
            content=ft.Column(
                controls=[
                    ft.Container(
                        width=44,
                        height=44,
                        border_radius=14,
                        bgcolor=color + "33",
                        content=ft.Icon(icon, color=color, size=26),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text(
                        label,
                        font_family="Montserrat Medium",
                        size=12,
                        color="#1a1a1a",
                        text_align=ft.TextAlign.CENTER,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
            ink=True,
        )