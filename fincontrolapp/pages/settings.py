import flet as ft
from components.base_page import BasePage
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog


class SettingsPage(BasePage):
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        super().__init__(page, "Настройки")

    def build_header(self):
        return ft.AppBar(
            title=ft.Text(
                "Настройки",
                font_family="Montserrat Extrabold",
                size=36,
            ),
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            toolbar_height=50,
        )

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
                color=ft.Colors.with_opacity(0.8, "#FF7E1C"), on_click=self._confirm_reset,
            ),
            self._setting_item(
                ft.Icons.NO_ACCOUNTS_OUTLINED, "Удалить аккаунт",
                "Полностью удалить профиль и все данные",
                color=ft.Colors.with_opacity(0.8, "#FF7E1C"), on_click=self._confirm_delete_account,
            ),
            self._setting_item(
                ft.Icons.LOGOUT, "Выйти из аккаунта", "Сменить пользователя",
                color=ft.Colors.with_opacity(0.8, "#FF7E1C"), on_click=lambda e: self.page_ref.data["logout"](),
            ),
        ], spacing=8)

    def _open_profile_dialog(self, e):
        user = self._ctrl.get_user()
        username_field = ft.TextField(
            label="Имя пользователя",
            text_style=ft.TextStyle(font_family="Montserrat Medium"),
            label_style=ft.TextStyle(font_family="Montserrat Medium"),
            value=user["username"] or "" if user else "",
            border_color="#6976EB",
        )
        contact_hint = (user["email"] or user["phone"] or "") if user else ""
 
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Профиль", font_family="Montserrat SemiBold"))
 
        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)
 
        def on_submit(e):
            self._ctrl.update_username(username_field.value.strip() or None)
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Имя сохранено ✓", font_family="Montserrat SemiBold"), open=True)
            self.page_ref.update()
 
        dlg.content = ft.Column([
            ft.Text(contact_hint, size=12, color=ft.Colors.with_opacity(0.6, "#000000"), font_family="Montserrat SemiBold") if contact_hint else ft.Container(),
            username_field,
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Сохранить",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)
 
    def _open_notifications_dialog(self, e):
        enabled = self.page_ref.data.get("_s_notifications", False)
        switch = ft.Switch(value=enabled, active_color="#6976EB")
        switch_row = ft.Row([switch,ft.Text("Напоминания о расходах", font_family="Montserrat SemiBold", size=13, color=ft.Colors.with_opacity(0.6, "#000000")),
        ], spacing=8)
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Уведомления", font_family="Montserrat SemiBold"))
 
        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)
 
        def on_submit(e):
            self.page_ref.data["_s_notifications"] = switch.value
            msg = "Уведомления включены ✓" if switch.value else "Уведомления выключены"
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text(msg, font_family="Montserrat SemiBold"), open=True)
            self.page_ref.update()
 
        dlg.content = ft.Column([
            ft.Text("Push-уведомления работают после сборки на устройстве.",
                    size=12, color=ft.Colors.with_opacity(0.6, "#000000"), font_family="Montserrat SemiBold"),
            switch_row,
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Сохранить",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_submit),
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
            label="Валюта", value=current, border_color="#6976EB",
            options=[ft.dropdown.Option(code, label) for code, label in currencies],
        )
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Валюта", font_family="Montserrat SemiBold"))
 
        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)
 
        def on_submit(e):
            self.page_ref.data["_s_currency"] = dd.value
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Валюта сохранена ✓", font_family="Montserrat SemiBold"), open=True)
            self.page_ref.update()
 
        dlg.content = ft.Column([dd], tight=True)
        dlg.actions = [
            ft.TextButton("Отмена",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Сохранить",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)
 
    def _open_telegram_dialog(self, e):
        import webbrowser
        bot_username = "FinControlBot"
        deep_link = "https://t.me/f1nc0ntr0l_bot#"
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Telegram-бот", font_family="Montserrat SemiBold"))
 
        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)
 
        def on_open(e):
            try:
                webbrowser.open(deep_link)
            finally:
                _close_dialog(self.page_ref, dlg)
 
        dlg.content = ft.Column([
            ft.Text("Открой бота и нажми /start — он привяжется к твоему аккаунту.",
                    size=13, color=ft.Colors.with_opacity(0.6, "#000000"), font_family="Montserrat SemiBold"),
            ft.Container(
                bgcolor="#6976EB", border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                content=ft.Text(f"@{bot_username}", size=14, color="#000000",
                                weight=ft.FontWeight.W_600, font_family="Montserrat SemiBold"),
            ),
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Открыть Telegram",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_open),
        ]
        _show_dialog(self.page_ref, dlg)
 
    def _confirm_reset(self, e):
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Сбросить данные?", font_family="Montserrat SemiBold"))
 
        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)
 
        def on_confirm(e):
            try:
                self._ctrl.reset_data()
                self.page_ref.snack_bar = ft.SnackBar(ft.Text("Данные удалены", font_family="Montserrat SemiBold"), open=True)
                self.page_ref.update()
            finally:
                _close_dialog(self.page_ref, dlg)
 
        dlg.content = ft.Text("Все транзакции, цели и подписки будут удалены. Отменить нельзя.", color=ft.Colors.with_opacity(0.6, "#000000"),font_family="Montserrat SemiBold")
        dlg.actions = [
            ft.TextButton("Отмена", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")),on_click=on_cancel),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color=ft.Colors.with_opacity(0.8, "#FF7E1C"),text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)
 
    def _confirm_delete_account(self, e):
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Удалить аккаунт?", font_family="Montserrat SemiBold"))
 
        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)
 
        def on_confirm(e):
            try:
                self._ctrl.delete_account()
                self.page_ref.snack_bar = ft.SnackBar(ft.Text("Аккаунт удален", font_family="Montserrat SemiBold"), open=True)
                self.page_ref.update()
                self.page_ref.data["logout"]()
            finally:
                _close_dialog(self.page_ref, dlg)
 
        dlg.content = ft.Text(
            "Профиль, транзакции, цели и подписки будут удалены без возможности восстановления."
        , font_family="Montserrat SemiBold",color=ft.Colors.with_opacity(0.6, "#000000"))
        dlg.actions = [
            ft.TextButton("Отмена",style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Удалить аккаунт", style=ft.ButtonStyle(text_style=ft.TextStyle(font_family="Montserrat SemiBold"),color=ft.Colors.with_opacity(0.8, "#FF7E1C")),
                          on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)

    def _setting_item(self, icon, title, subtitle, color="#000000", on_click=None):
        return ft.Container(
            gradient=ft.RadialGradient(
                colors=["#ffffff", "#88A2FF"],
                center=ft.Alignment(0.3, 0.9),
                radius=5.0,
                stops=[0.0, 0.8],
            ),
            border_radius=12, padding=16, ink=True,
            on_click=on_click,
            content=ft.Row([
                ft.Icon(icon, color=color, size=24),
                ft.Column([
                    ft.Text(
                        title,
                        size=15,
                        color=color,
                        font_family="Montserrat SemiBold",
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Text(
                        subtitle,
                        size=12,
                        color=ft.Colors.with_opacity(0.6, "#000000"),
                        font_family="Montserrat SemiBold",
                    ),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.with_opacity(0.6, "#000000"), size=20),
            ], spacing=12),
        )