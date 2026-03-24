"""
goals.py — Экран финансовых целей.

Показывает:
- Список активных целей с прогрессом накоплений (пока заглушка)
- Кнопку создания новой цели

Пример цели: "Накопить на MacBook — 120 000 ₽, собрано 45 000 ₽".

TODO: добавить модель Goal (название, сумма, текущий прогресс, дата).
TODO: показывать прогресс-бар для каждой цели.
"""
import flet as ft
from components.base_page import BasePage


class GoalsPage(BasePage):
    """Экран финансовых целей — список накоплений с прогрессом."""

    def __init__(self, page: ft.Page):
        """
        Параметры:
            page (ft.Page): объект страницы Flet, передаётся из main.py.
        """
        super().__init__(page, "Цели")

    def build_body(self):
        """
        Строит тело экрана целей.

        Структура:
            1. Список целей с прогресс-барами (пока заглушка).
            2. Кнопка "+ Создать цель".

        Возвращает:
            ft.Column: колонка со всеми элементами экрана.
        """
        return ft.Column([
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Целей пока нет", color="#888888", size=14),
            ),
            ft.Button(
                "＋ Создать цель",
                style=ft.ButtonStyle(bgcolor="#6C63FF", color="#FFFFFF"),
                width=float("inf"),
            ),
        ], spacing=16)