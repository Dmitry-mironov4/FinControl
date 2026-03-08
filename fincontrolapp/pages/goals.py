import flet as ft
from components.base_page import BasePage


class GoalsPage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Цели")

    def build_body(self):
        return ft.Column([
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Целей пока нет", color="#888888", size=14),
            ),
            ft.ElevatedButton("+ Создать цель", bgcolor="#6C63FF", color="#FFFFFF", width=float("inf")),
        ], spacing=16)