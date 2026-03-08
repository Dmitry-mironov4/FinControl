import flet as ft
from components.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Главная")

    def build_body(self):
        return ft.Column(
            controls=[
                # Карточка баланса
                ft.Container(
                    bgcolor="#1A1A24",
                    border_radius=16,
                    padding=24,
                    content=ft.Column([
                        ft.Text("Общий баланс", size=14, color="#888888"),
                        ft.Text("0 ₽", size=36, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                        ft.Row([
                            ft.Container(
                                bgcolor="#1E3A2F",
                                border_radius=8,
                                padding=ft.padding.symmetric(8, 12),
                                content=ft.Row([
                                    ft.Icon(ft.Icons.ARROW_UPWARD, color="#4CAF50", size=16),
                                    ft.Text("Доходы: 0 ₽", color="#4CAF50", size=13),
                                ], spacing=4),
                            ),
                            ft.Container(
                                bgcolor="#3A1E1E",
                                border_radius=8,
                                padding=ft.padding.symmetric(8, 12),
                                content=ft.Row([
                                    ft.Icon(ft.Icons.ARROW_DOWNWARD, color="#F44336", size=16),
                                    ft.Text("Расходы: 0 ₽", color="#F44336", size=13),
                                ], spacing=4),
                            ),
                        ], spacing=8),
                    ], spacing=8),
                ),

                # Быстрые действия
                ft.Text("Быстрые действия", size=16, weight=ft.FontWeight.W_600, color="#FFFFFF"),
                ft.Row([
                    self._quick_action(ft.Icons.ADD_CIRCLE_OUTLINE, "Доход", "#4CAF50"),
                    self._quick_action(ft.Icons.REMOVE_CIRCLE_OUTLINE, "Расход", "#F44336"),
                    self._quick_action(ft.Icons.STAR_OUTLINE, "Цель", "#6C63FF"),
                    self._quick_action(ft.Icons.SUBSCRIPTIONS_OUTLINED, "Подписка", "#FF9800"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

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
            scroll=ft.ScrollMode.AUTO,
        )

    def _quick_action(self, icon, label, color):
        return ft.Container(
            bgcolor="#1A1A24",
            border_radius=12,
            padding=12,
            width=78,
            content=ft.Column([
                ft.Icon(icon, color=color, size=28),
                ft.Text(label, size=12, color="#CCCCCC", text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            ink=True,
        )