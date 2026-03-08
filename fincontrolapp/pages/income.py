import flet as ft
from components.base_page import BasePage


class IncomePage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Доходы")

    def build_body(self):
        return ft.Column([
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Column([
                    ft.Text("Основная зарплата", size=14, color="#888888"),
                    ft.Text("Не указана", size=24, weight=ft.FontWeight.BOLD, color="#4CAF50"),
                    ft.ElevatedButton("Указать зарплату", icon=ft.Icons.EDIT, bgcolor="#6C63FF", color="#FFFFFF"),
                ], spacing=8),
            ),
            ft.Text("Дополнительные доходы", size=16, weight=ft.FontWeight.W_600, color="#FFFFFF"),
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Нет записей", color="#888888", size=14),
            ),
            ft.ElevatedButton("+ Добавить доход", bgcolor="#6C63FF", color="#FFFFFF", width=float("inf")),
        ], spacing=16)