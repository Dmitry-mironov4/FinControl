"""
income.py — Экран доходов.

Показывает:
- Карточку с основной зарплатой (кнопка "Указать зарплату")
- Список дополнительных доходов (пока заглушка)
- Кнопку добавления нового дохода

TODO: сохранять зарплату в БД и отображать реальное значение.
TODO: реализовать список дополнительных доходов.
"""
import flet as ft
from components.base_page import BasePage


class IncomePage(BasePage):
    """Экран доходов: зарплата и дополнительные поступления."""

    def __init__(self, page: ft.Page):
        """
        Параметры:
            page (ft.Page): объект страницы Flet, передаётся из main.py.
        """
        super().__init__(page, "Доходы")

    def build_body(self):
        """
        Строит тело экрана доходов.

        Структура:
            1. Карточка основной зарплаты с кнопкой редактирования.
            2. Заголовок "Дополнительные доходы".
            3. Список доп. доходов (пока заглушка).
            4. Кнопка "+ Добавить доход".

        Возвращает:
            ft.Column: колонка со всеми элементами экрана.
        """
        return ft.Column([
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Column([
                    ft.Text("Основная зарплата", size=14, color="#888888"),
                    ft.Text("Не указана", size=24, weight=ft.FontWeight.BOLD, color="#4CAF50"),
                    ft.Button(
                        "Указать зарплату",
                        icon=ft.Icons.EDIT,
                        style=ft.ButtonStyle(bgcolor="#6C63FF", color="#FFFFFF"),
                    ),
                ], spacing=8),
            ),
            ft.Text("Дополнительные доходы", size=16, weight=ft.FontWeight.W_600, color="#FFFFFF"),
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Нет записей", color="#888888", size=14),
            ),
            ft.Button(
                "＋ Добавить доход",
                style=ft.ButtonStyle(bgcolor="#6C63FF", color="#FFFFFF"),
                width=float("inf"),
            ),
        ], spacing=16)