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

    def build_body(self):
        """
        Строит тело главного экрана.

        Структура (сверху вниз):
            1. Карточка баланса  — SVG-фон из Figma + контент поверх через ft.Stack.
            2. Быстрые действия  — 4 кнопки для перехода к основным разделам.
            3. Последние операции — список транзакций (пока заглушка).

        Возвращает:
            ft.Column: прокручиваемая колонка со всеми секциями.
        """
        return ft.Column(
            controls=[
                # Карточка баланса — SVG фон + контент через Stack
                self._balance_card(),

                # Быстрые действия
                ft.Text("Быстрые действия", size=16, weight=ft.FontWeight.W_600, color="#FFFFFF"),
                ft.Row([
                    self._quick_action_icon(ft.Icons.ADD_CIRCLE_OUTLINE,     "Доходы",  "#4CAF50", lambda e: self.page_ref.data["navigate"](1)),
                    self._quick_action_icon(ft.Icons.REMOVE_CIRCLE_OUTLINE,  "Расходы", "#F44336", lambda e: self.page_ref.data["navigate"](1)),
                    self._quick_action_icon(ft.Icons.STAR_OUTLINE,           "Цель",    "#6C63FF", lambda e: self.page_ref.data["navigate"](2)),
                    self._quick_action_icon(ft.Icons.SUBSCRIPTIONS_OUTLINED, "Подписка","#FF9800", lambda e: self.page_ref.data["navigate"](4)),
                ], spacing=12),

                # Последние операции
                ft.Text("Последние операции", size=16, weight=ft.FontWeight.W_600, color="#FFFFFF"),
                ft.Container(
                    bgcolor="#1A1A24",
                    border_radius=16,
                    padding=16,
                    content=ft.Text("Операций пока нет", color="#888888", size=14),
                ),
            ],
            spacing=16,
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
                        content=ft.Column([
                            ft.Text("Общий баланс", size=14, color="rgba(0,0,0,0.5)"),
                            ft.Text("0 ₽", size=36, weight=ft.FontWeight.BOLD, color="#000000"),
                            ft.Row([
                                ft.Container(
                                    bgcolor="#E3FC87",
                                    border_radius=16,
                                    padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.ARROW_UPWARD, color="#2A4A00", size=16),
                                        ft.Text("Доходы: 0 ₽", color="#2A4A00", size=13,
                                                weight=ft.FontWeight.W_500),
                                    ], spacing=4),
                                ),
                                ft.Container(
                                    bgcolor="#FFEC60",
                                    border_radius=16,
                                    padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.ARROW_DOWNWARD, color="#4A3A00", size=16),
                                        ft.Text("Расходы: 0 ₽", color="#4A3A00", size=13,
                                                weight=ft.FontWeight.W_500),
                                    ], spacing=4),
                                ),
                            ], spacing=8),
                        ], spacing=8),
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
            border_radius=12,
            padding=12,
            width=78,
            on_click=on_click,
            content=ft.Column([
                ft.Container(
                    width=40,
                    height=40,
                    border_radius=20,
                    bgcolor=color + "22",  # цвет с прозрачностью ~13%
                    content=ft.Icon(icon, color=color, size=24),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Text(
                    label, size=12, color="#CCCCCC",
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            ink=True,
        )