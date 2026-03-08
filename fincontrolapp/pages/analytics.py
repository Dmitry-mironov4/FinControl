import flet as ft
from components.base_page import BasePage


class AnalyticsPage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Аналитика")

    def build_body(self):
        return ft.Column([
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=24,
                content=ft.Column([
                    ft.Icon(ft.Icons.BAR_CHART, size=48, color="#6C63FF"),
                    ft.Text("Графики появятся после добавления данных", color="#888888", size=14, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            ),
        ], spacing=16)