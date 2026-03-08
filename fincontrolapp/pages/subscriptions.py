import flet as ft
from components.base_page import BasePage


class SubscriptionsPage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Подписки")

    def build_body(self):
        return ft.Column([
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Column([
                    ft.Text("Сумма подписок в месяц", size=14, color="#888888"),
                    ft.Text("0 ₽", size=28, weight=ft.FontWeight.BOLD, color="#FF9800"),
                ], spacing=4),
            ),
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Подписок нет", color="#888888", size=14),
            ),
            ft.ElevatedButton("+ Добавить подписку", bgcolor="#FF9800", color="#FFFFFF", width=float("inf")),
        ], spacing=16)