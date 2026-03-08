import flet as ft
from components.base_page import BasePage


class SettingsPage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Настройки")

    def build_body(self):
        return ft.Column([
            self._setting_item(ft.Icons.PERSON_OUTLINE, "Профиль", "Настройте своё имя"),
            self._setting_item(ft.Icons.NOTIFICATIONS_OUTLINED, "Уведомления", "Напоминания о расходах"),
            self._setting_item(ft.Icons.CURRENCY_RUBLE, "Валюта", "Рубль (₽)"),
            self._setting_item(ft.Icons.TELEGRAM, "Telegram-бот", "Подключить бота"),
            self._setting_item(ft.Icons.DELETE_OUTLINE, "Сбросить данные", "Удалить всё", color="#F44336"),
        ], spacing=8)

    def _setting_item(self, icon, title, subtitle, color="#FFFFFF"):
        return ft.Container(
            bgcolor="#1A1A24", border_radius=12, padding=16, ink=True,
            content=ft.Row([
                ft.Icon(icon, color=color, size=24),
                ft.Column([
                    ft.Text(title, size=15, color=color, weight=ft.FontWeight.W_500),
                    ft.Text(subtitle, size=12, color="#888888"),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#555555", size=20),
            ], spacing=12),
        )