import flet as ft
from components.base_page import BasePage


CATEGORIES = [
    (ft.Icons.RESTAURANT, "Еда", "#FF9800"),
    (ft.Icons.DIRECTIONS_CAR, "Транспорт", "#2196F3"),
    (ft.Icons.LOCAL_HOSPITAL, "Здоровье", "#F44336"),
    (ft.Icons.SHOPPING_BAG, "Покупки", "#9C27B0"),
    (ft.Icons.SPORTS_ESPORTS, "Развлечения", "#00BCD4"),
    (ft.Icons.HOME, "Жильё", "#795548"),
    (ft.Icons.SCHOOL, "Обучение", "#4CAF50"),
    (ft.Icons.MORE_HORIZ, "Другое", "#607D8B"),
]


class ExpensesPage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Расходы")

    def build_body(self):
        return ft.Column([
            ft.Text("Категории", size=16, weight=ft.FontWeight.W_600, color="#FFFFFF"),
            ft.GridView(
                runs_count=4,
                max_extent=90,
                spacing=10,
                run_spacing=10,
                height=200,
                controls=[self._category_card(icon, label, color) for icon, label, color in CATEGORIES],
            ),
            ft.Text("История расходов", size=16, weight=ft.FontWeight.W_600, color="#FFFFFF"),
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Нет записей", color="#888888", size=14),
            ),
            ft.ElevatedButton("+ Добавить расход", bgcolor="#F44336", color="#FFFFFF", width=float("inf")),
        ], spacing=16)

    def _category_card(self, icon, label, color):
        return ft.Container(
            bgcolor="#1A1A24", border_radius=12, padding=8, ink=True,
            content=ft.Column([
                ft.Icon(icon, color=color, size=28),
                ft.Text(label, size=11, color="#CCCCCC", text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        )