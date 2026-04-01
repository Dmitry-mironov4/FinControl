import flet as ft
from components.base_page import BasePage
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog


class SettingsPage(BasePage):
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        super().__init__(page, "Настройки")

    def build_body(self):
        return ft.Column([
            self._setting_item(ft.Icons.PERSON_OUTLINE, "Профиль", "Настройте своё имя",
                on_click=self._open_profile_dialog),
            self._setting_item(ft.Icons.NOTIFICATIONS_OUTLINED, "Уведомления", "Напоминания о расходах",
                on_click=self._open_notifications_dialog),
            self._setting_item(ft.Icons.CURRENCY_RUBLE, "Валюта", "Рубль (₽)",
                on_click=self._open_currency_dialog),
            self._setting_item(ft.Icons.TELEGRAM, "Telegram-бот", "Подключить бота",
                on_click=self._open_telegram_dialog),
            self._setting_item(
                ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "Изменить баланс",
                "Скорректировать текущий баланс",
                on_click=lambda e: self.page_ref.data["show_balance_dialog"](),
            ),
            self._setting_item(
                ft.Icons.DELETE_OUTLINE, "Сбросить данные",
                "Удалить все транзакции, цели, подписки",
                color="#F44336", on_click=self._confirm_reset,
            ),
            self._setting_item(
                ft.Icons.NO_ACCOUNTS_OUTLINED, "Удалить аккаунт",
                "Полностью удалить профиль и все данные",
                color="#FF5252", on_click=self._confirm_delete_account,
            ),
            self._setting_item(
                ft.Icons.LOGOUT, "Выйти из аккаунта", "Сменить пользователя",
                color="#F44336", on_click=lambda e: self.page_ref.data["logout"](),
            ),
        ], spacing=8)

    def _open_profile_dialog(self, e):
        user = self._ctrl.get_user()
        username_field = ft.TextField(
            label="Имя пользователя",
            value=user["username"] or "" if user else "",
            border_color="#6C63FF",
        )
        contact_hint = (user["email"] or user["phone"] or "") if user else ""

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Профиль"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            self._ctrl.update_username(username_field.value.strip() or None)
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Имя сохранено ✓"), open=True)
            self.page_ref.update()

        dlg.content = ft.Column([
            ft.Text(contact_hint, size=12, color="#888888") if contact_hint else ft.Container(),
            username_field,
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Сохранить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_notifications_dialog(self, e):
        enabled = self.page_ref.data.get("_s_notifications", False)
        switch = ft.Switch(label="Напоминания о расходах", value=enabled, active_color="#6C63FF")
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Уведомления"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            self.page_ref.data["_s_notifications"] = switch.value
            msg = "Уведомления включены ✓" if switch.value else "Уведомления выключены"
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
            self.page_ref.update()

        dlg.content = ft.Column([
            ft.Text("Push-уведомления работают после сборки на устройстве.",
                    size=12, color="#888888"),
            switch,
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Сохранить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_currency_dialog(self, e):
        currencies = [
            ("RUB", "₽  Российский рубль"),
            ("USD", "$  Доллар США"),
            ("EUR", "€  Евро"),
            ("KZT", "₸  Казахстанский тенге"),
            ("BYN", "Br  Белорусский рубль"),
        ]
        current = self.page_ref.data.get("_s_currency", "RUB")
        dd = ft.Dropdown(
            label="Валюта", value=current, border_color="#6C63FF",
            options=[ft.dropdown.Option(code, label) for code, label in currencies],
        )
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Валюта"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            self.page_ref.data["_s_currency"] = dd.value
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Валюта сохранена ✓"), open=True)
            self.page_ref.update()

        dlg.content = ft.Column([dd], tight=True)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Сохранить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_telegram_dialog(self, e):
        import webbrowser
        bot_username = "FinControlBot"
        deep_link = "https://t.me/f1nc0ntr0l_bot#"
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Telegram-бот"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_open(e):
            try:
                webbrowser.open(deep_link)
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Column([
            ft.Text("Открой бота и нажми /start — он привяжется к твоему аккаунту.",
                    size=13, color="#CCCCCC"),
            ft.Container(
                bgcolor="#2A2A35", border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                content=ft.Text(f"@{bot_username}", size=14, color="#29B6F6",
                                weight=ft.FontWeight.W_600),
            ),
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Открыть Telegram", on_click=on_open),
        ]
        _show_dialog(self.page_ref, dlg)

    def _confirm_reset(self, e):
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Сбросить данные?"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_confirm(e):
            try:
                self._ctrl.reset_data()
                self.page_ref.snack_bar = ft.SnackBar(ft.Text("Данные удалены"), open=True)
                self.page_ref.update()
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Text("Все транзакции, цели и подписки будут удалены. Отменить нельзя.")
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color="#F44336"), on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)

    def _confirm_delete_account(self, e):
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Удалить аккаунт?"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_confirm(e):
            try:
                self._ctrl.delete_account()
                self.page_ref.snack_bar = ft.SnackBar(ft.Text("Аккаунт удален"), open=True)
                self.page_ref.update()
                self.page_ref.data["logout"]()
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Text(
            "Профиль, транзакции, цели и подписки будут удалены без возможности восстановления."
        )
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Удалить аккаунт", style=ft.ButtonStyle(color="#FF5252"),
                          on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)

    def _setting_item(self, icon, title, subtitle, color="#FFFFFF", on_click=None):
        return ft.Container(
            bgcolor="#1A1A24", border_radius=12, padding=16, ink=True,
            on_click=on_click,
            content=ft.Row([
                ft.Icon(icon, color=color, size=24),
                ft.Column([
                    ft.Text(title, size=15, color=color, weight=ft.FontWeight.W_500),
                    ft.Text(subtitle, size=12, color="#888888"),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#555555", size=20),
            ], spacing=12),
        )
