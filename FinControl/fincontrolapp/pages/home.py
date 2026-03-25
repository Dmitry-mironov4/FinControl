"""
home.py — Главный экран приложения FinControl.

Показывает:
- Карточку с общим балансом (доходы и расходы суммарно)
- Блок быстрых действий (кнопки-ярлыки для частых операций)
- Список последних операций

TODO: подключить реальные данные из БД вместо заглушек "0 ₽".
"""

import flet as ft
from components.base_page import BasePage


class HomePage(BasePage):
    """Главный экран — дашборд с балансом и быстрыми действиями."""

    def __init__(self, page: ft.Page):
        """
        Параметры:
            page (ft.Page): объект страницы Flet, передаётся из main.py.
        """
        super().__init__(page, "Главная")

    def build_header(self):
        """Переопределяем заголовок страницы (AppBar)"""
        return ft.AppBar(
            title=ft.Text(
                "Главная",
                font_family="Montserrat Extrabold",
                size=36,
            ),
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            toolbar_height=30,
        )

    def build_body(self):
        """
        Строит тело главного экрана.

        Структура (сверху вниз):
            1. Карточка баланса — SVG-фон из Figma + контент поверх через ft.Stack.
            2. Быстрые действия — 4 кнопки для перехода к основным разделам.
            3. Последние операции — список транзакций (пока заглушка).

        Возвращает:
            ft.Column: прокручиваемая колонка со всеми секциями.
        """
        return ft.Column(
            controls=[
                # Карточка баланса — SVG фон + контент через Stack
                self._balance_card(),

                # Быстрые действия
                ft.Text(
                    "Быстрые действия",
                    size=20,
                    font_family="Montserrat Semibold",
                    color="#000000",
                ),
                ft.Row(
                    controls=[
                        self._quick_action_icon(
                            ft.Icons.ADD_CIRCLE_OUTLINE,
                            "Доходы",
                            "#000000",
                            lambda e: self.page_ref.data["navigate"](1),
                        ),
                        self._quick_action_icon(
                            ft.Icons.REMOVE_CIRCLE_OUTLINE,
                            "Расходы",
                            "#000000",
                            lambda e: self.page_ref.data["navigate"](1),
                        ),
                        self._quick_action_icon(
                            ft.Icons.STAR_OUTLINE,
                            "Цель",
                            "#000000",
                            lambda e: self.page_ref.data["navigate"](2),
                        ),
                        self._quick_action_icon(
                            ft.Icons.SUBSCRIPTIONS_OUTLINED,
                            "Подписки",
                            "#000000",
                            lambda e: self.page_ref.data["navigate"](4),
                        ),
                    ],
                    spacing=12,
                ),

                # Последние операции
                ft.Text(
                    "Последние операции",
                    size=20,
                    font_family="Montserrat Semibold",
                    color="#000000",
                ),
                ft.Container(
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
                ),
            ],
            spacing=20,
        )

    def _balance_card(self):
        return ft.Container(
            height=171,
            border_radius=24,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Image(
                        src="home/card_bg.svg",
                        fit="fill",
                        expand=True,
                    ),
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
                                    "0 ₽",
                                    font_family="Montserrat Semibold",
                                    size=36,
                                    color="#000000",
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            bgcolor="#E3FC87",
                                            border_radius=16,
                                            padding=ft.Padding(
                                                left=12, right=12, top=8, bottom=8
                                            ),
                                            content=ft.Row(
                                                controls=[
                                                    ft.Icon(
                                                        ft.Icons.ARROW_UPWARD,
                                                        color="#2A4A00",
                                                        size=16,
                                                    ),
                                                    ft.Text(
                                                        "Доходы: 0 ₽",
                                                        font_family="Montserrat Semibold",
                                                        color="#2A4A00",
                                                        size=14,
                                                    ),
                                                ],
                                                spacing=4,
                                            ),
                                        ),
                                        ft.Container(
                                            bgcolor="#FFEC60",
                                            border_radius=16,
                                            padding=ft.Padding(
                                                left=12, right=12, top=8, bottom=8
                                            ),
                                            content=ft.Row(
                                                controls=[
                                                    ft.Icon(
                                                        ft.Icons.ARROW_DOWNWARD,
                                                        color="#4A3A00",
                                                        size=16,
                                                    ),
                                                    ft.Text(
                                                        "Расходы: 0 ₽",
                                                        font_family="Montserrat Semibold",
                                                        color="#4A3A00",
                                                        size=14,
                                                    ),
                                                ],
                                                spacing=4,
                                            ),
                                        ),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=8,
                        ),
                    ),
                ],
            ),
        )

    def _quick_action_icon(self, icon, label, color, on_click=None):
        """
        Создаёт кнопку быстрого действия с Material Icon.

        Параметры:
            icon  (ft.Icons): иконка из библиотеки Material Icons.
            label (str):      подпись под иконкой (обрезается если не влезает).
            color (str):      цвет иконки и фона кружка в формате HEX.

        Возвращает:
            ft.Container: карточка 78×~80px с иконкой и подписью,
                          реагирует на нажатие (ink=True).
        """
        return ft.Container(
            border_radius=18,
            padding=10,
            width=78,
            on_click=on_click,
            gradient=ft.LinearGradient(
                colors=["#ffffff", "#88A2FF"],
                begin=ft.Alignment(-1, -1),  # top-left
                end=ft.Alignment(1, 1),      # bottom-right
            ),
            content=ft.Column(
                controls=[
                    ft.Container(
                        width=44,
                        height=44,
                        border_radius=14,
                        bgcolor=color + "33",  # цвет с прозрачностью ~13%
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