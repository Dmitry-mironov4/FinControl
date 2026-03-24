"""
subscriptions.py — Экран управления подписками.

Показывает:
- Суммарную стоимость всех подписок в месяц
- Список активных подписок (пока заглушка)
- Кнопку добавления новой подписки

Подписки — особый вид расходов: они повторяются каждый месяц
(или год) и списываются автоматически. Отдельный экран помогает
отслеживать их общую стоимость.

TODO: добавить модель Subscription (название, сумма, дата списания, период).
TODO: уведомлять за день до списания подписки.
"""
import flet as ft
from components.base_page import BasePage


class SubscriptionsPage(BasePage):
    """Экран управления регулярными подписками."""

    def __init__(self, page: ft.Page):
        """
        Параметры:
            page (ft.Page): объект страницы Flet, передаётся из main.py.
        """
        super().__init__(page, "Подписки")

    def build_body(self):
        """
        Строит тело экрана подписок.

        Структура:
            1. Карточка с суммарной стоимостью подписок в месяц.
            2. Список подписок (пока заглушка).
            3. Кнопка "+ Добавить подписку".

        Возвращает:
            ft.Column: колонка со всеми элементами экрана.
        """
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
            ft.Button(
                "＋ Добавить подписку",
                style=ft.ButtonStyle(bgcolor="#FF9800", color="#FFFFFF"),
                width=float("inf"),
            ),
        ], spacing=16)