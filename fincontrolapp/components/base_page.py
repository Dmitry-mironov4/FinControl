import flet as ft


class BasePage(ft.Container):
    """Базовый класс для всех страниц приложения"""

    def __init__(self, page: ft.Page, title: str, **kwargs):
        super().__init__(**kwargs)
        self.page_ref = page
        self.page_title = title
        self.expand = True
        self.bgcolor = "#0F0F14"
        self.padding = ft.padding.only(left=16, right=16, top=16, bottom=8)
        self.content = ft.Column(
            controls=[self.build_header(), self.build_body()],
            expand=True,
            spacing=16,
        )

    def build_header(self):
        return ft.Text(
            self.page_title,
            size=28,
            weight=ft.FontWeight.BOLD,
            color="#FFFFFF",
        )

    def build_body(self):
        """Переопределяется в каждой странице"""
        return ft.Container()