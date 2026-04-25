import flet as ft
from components.base_page import BasePage
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog
from utils import CURRENCY_LABELS


class SettingsPage(BasePage):
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        self._username_text: ft.Text | None = None
        self._initials_text: ft.Text | None = None
        self._currency_subtitle: ft.Text | None = None
        super().__init__(page, "Настройки")

    @staticmethod
    def _calc_initials(username: str) -> str:
        parts = (username or "User").strip().split()
        if not parts:
            return "U"
        return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()

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
        currency_code = (self.page_ref.data or {}).get("_s_currency", "RUB")
        currency_label = CURRENCY_LABELS.get(currency_code, CURRENCY_LABELS["RUB"])
        self._currency_subtitle = ft.Text(
            currency_label,
            size=12,
            color=ft.Colors.with_opacity(0.6, "#000000"),
            font_family="Montserrat SemiBold",
        )

        return ft.Column([
            self._build_avatar_block(),
            # ── Группа: Аккаунт ──────────────────────────────────────────
            self._section_header("Аккаунт"),
            self._group([
                self._setting_item(ft.Icons.PERSON_OUTLINE, "Профиль", "Настройте своё имя",
                    on_click=self._open_profile_dialog),
                self._setting_item(ft.Icons.NOTIFICATIONS_OUTLINED, "Уведомления", "Напоминания о расходах",
                    on_click=self._open_notifications_dialog, divider=True),
                self._setting_item(ft.Icons.CURRENCY_RUBLE, "Валюта", self._currency_subtitle,
                    on_click=self._open_currency_dialog, divider=True),
                self._setting_item(ft.Icons.TELEGRAM, "Telegram-бот", "Подключить бота",
                    on_click=self._open_telegram_dialog, divider=True),
            ]),

            # ── Группа: Баланс ───────────────────────────────────────────
            self._section_header("Баланс"),
            self._group([
                self._setting_item(
                    ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "Изменить баланс",
                    "Скорректировать текущий баланс",
                    on_click=lambda e: self.page_ref.data["show_balance_dialog"](),
                ),
            ]),

            # ── Группа: Опасная зона ─────────────────────────────────────
            self._section_header("Опасная зона"),
            self._group([
                self._setting_item(
                    ft.Icons.DELETE_OUTLINE, "Сбросить данные",
                    "Удалить все транзакции, цели, подписки",
                    color=ft.Colors.with_opacity(0.8, "#FF7E1C"), on_click=self._confirm_reset,
                ),
                self._setting_item(
                    ft.Icons.NO_ACCOUNTS_OUTLINED, "Удалить аккаунт",
                    "Полностью удалить профиль и все данные",
                    color=ft.Colors.with_opacity(0.8, "#FF7E1C"), on_click=self._confirm_delete_account,
                    divider=True,
                ),
                self._setting_item(
                    ft.Icons.LOGOUT, "Выйти из аккаунта", "Сменить пользователя",
                    color=ft.Colors.with_opacity(0.8, "#FF7E1C"),
                    on_click=lambda e: self.page_ref.data["logout"](),
                    divider=True,
                ),
            ]),
        ], spacing=4)

    # ── Вспомогательные методы ───────────────────────────────────────────

    def _build_avatar_block(self) -> ft.Container:
        user = self._ctrl.get_user()
        username = (user["username"] or "User") if user else "User"
        contact = (user["email"] or user["phone"] or "") if user else ""
        initials = self._calc_initials(username)

        self._username_text = ft.Text(
            username,
            size=18,
            font_family="Montserrat SemiBold",
            color="#000000",
            weight=ft.FontWeight.W_600,
        )
        self._initials_text = ft.Text(
            initials,
            size=24,
            font_family="Montserrat SemiBold",
            color="#483EB7",
            weight=ft.FontWeight.BOLD,
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=18,
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.06, "#483EB7")),
            bgcolor=ft.Colors.with_opacity(0.04, "#483EB7"),
            content=ft.Row([
                ft.Container(
                    width=64, height=64,
                    border_radius=32,
                    gradient=ft.LinearGradient(
                        colors=["#ffffff", "#88A2FF"],
                        begin=ft.Alignment(-1, -1),
                        end=ft.Alignment(1, 1),
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=self._initials_text,
                ),
                ft.Column([
                    self._username_text,
                    ft.Text(
                        contact,
                        size=13,
                        font_family="Montserrat SemiBold",
                        color=ft.Colors.with_opacity(0.5, "#000000"),
                    ) if contact else ft.Container(),
                ], spacing=2),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    def _section_header(self, label: str) -> ft.Container:
        """Заголовок группы (серый текст, как 'Account' / 'Preferences' на картинке)."""
        return ft.Container(
            padding=ft.padding.only(left=4, top=12, bottom=4),
            content=ft.Text(
                label,
                size=12,
                color=ft.Colors.with_opacity(0.45, "#000000"),
                font_family="Montserrat SemiBold",
                weight=ft.FontWeight.W_600,
            ),
        )

    def _group(self, items: list) -> ft.Container:
        """Обёртка группы — белая карточка с закруглёнными углами."""
        return ft.Container(
            gradient=ft.RadialGradient(
                colors=["#ffffff", "#88A2FF"],
                center=ft.Alignment(0.3, 0.9),
                radius=7.0,
                stops=[0.0, 0.8],
            ),
            border_radius=12,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(items, spacing=0, tight=True),
        )

    def _setting_item(self, icon, title, subtitle, color="#000000",
                      on_click=None, divider: bool = False):
        """
        Один пункт настроек внутри группы.
        divider=True добавляет тонкую разделительную линию сверху.
        subtitle может быть строкой или готовым ft.Text — это позволяет
        обновлять подзаголовок без перестроения всей страницы.
        """
        subtitle_widget = subtitle if isinstance(subtitle, ft.Text) else ft.Text(
            subtitle,
            size=12,
            color=ft.Colors.with_opacity(0.6, "#000000"),
            font_family="Montserrat SemiBold",
        )
        row = ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            ink=True,
            on_click=on_click,
            content=ft.Row([
                ft.Icon(icon, color=color, size=22),
                ft.Column([
                    ft.Text(
                        title,
                        size=15,
                        color=color,
                        font_family="Montserrat SemiBold",
                        weight=ft.FontWeight.W_600,
                    ),
                    subtitle_widget,
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT,
                        color=ft.Colors.with_opacity(0.45, "#000000"), size=20),
            ], spacing=12),
        )

        if not divider:
            return row

        return ft.Column([
            ft.Divider(height=1, thickness=0.5,
                       color=ft.Colors.with_opacity(0.12, "#000000")),
            row,
        ], spacing=0, tight=True)

    # ── Диалоги (без изменений) ──────────────────────────────────────────

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
            try:
                self._ctrl.update_username(username_field.value.strip() or None)
            except Exception:
                self._show_error("Не удалось сохранить имя")
                return
            new_name = (username_field.value or "").strip() or "User"
            if self._username_text is not None:
                self._username_text.value = new_name
                try:
                    self._username_text.update()
                except Exception:
                    pass
            if self._initials_text is not None:
                self._initials_text.value = self._calc_initials(new_name)
                try:
                    self._initials_text.update()
                except Exception:
                    pass
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Имя сохранено ✓", font_family="Montserrat SemiBold"), open=True)
            self.page_ref.update()


        dlg.content = ft.Column([
            ft.Text(contact_hint, size=12, color=ft.Colors.with_opacity(0.6, "#000000"),
                    font_family="Montserrat SemiBold") if contact_hint else ft.Container(),
            username_field,
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Сохранить", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)
 
    def _open_notifications_dialog(self, e):
        enabled = self.page_ref.data.get("_s_notifications", False)
        switch = ft.Switch(value=enabled, active_color="#6976EB")
        switch_row = ft.Row([switch, ft.Text("Напоминания о расходах",
            font_family="Montserrat SemiBold", size=13,
            color=ft.Colors.with_opacity(0.6, "#000000"))], spacing=8)
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Уведомления", font_family="Montserrat SemiBold"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)
 
        def on_submit(e):
            self.page_ref.data["_s_notifications"] = switch.value
            msg = "Уведомления включены" if switch.value else "Уведомления выключены"
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text(msg, font_family="Montserrat SemiBold"), open=True)
            self.page_ref.update()


        dlg.content = ft.Column([
            ft.Text("Push-уведомления работают после сборки на устройстве.",
                    size=12, color=ft.Colors.with_opacity(0.6, "#000000"), font_family="Montserrat SemiBold"),
            switch_row,
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Сохранить", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_submit),
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
        dd = ft.Dropdown(label="Валюта", value=current, border_color="#6976EB",
            options=[ft.dropdown.Option(code, label) for code, label in currencies])
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Валюта", font_family="Montserrat SemiBold"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)
 
        def on_submit(e):
            self.page_ref.data["_s_currency"] = dd.value
            if self._currency_subtitle is not None:
                self._currency_subtitle.value = CURRENCY_LABELS.get(
                    dd.value, CURRENCY_LABELS["RUB"]
                )
                try:
                    self._currency_subtitle.update()
                except Exception:
                    pass
            _close_dialog(self.page_ref, dlg)
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Валюта сохранена ✓", font_family="Montserrat SemiBold"), open=True)
            self.page_ref.update()


        dlg.content = ft.Column([dd], tight=True)
        dlg.actions = [
            ft.TextButton("Отмена", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Сохранить", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)
 
    def _open_telegram_dialog(self, e):
        import webbrowser
        user_id = self._ctrl._user_id
        if user_id is None:
            self._show_error("Не удалось получить данные пользователя")
            return
        deep_link = f"https://t.me/F1nC0ntrolBot?start={user_id}"
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Telegram-бот", font_family="Montserrat SemiBold"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_open(e):
            try:
                webbrowser.open(deep_link)
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Column([
            ft.Text("Нажми «Открыть Telegram» — бот автоматически привяжет твой аккаунт.",
                    size=13, color=ft.Colors.with_opacity(0.6, "#000000"), font_family="Montserrat SemiBold"),
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

        dlg.content = ft.Text("Все транзакции, цели и подписки будут удалены. Отменить нельзя.",
            color=ft.Colors.with_opacity(0.6, "#000000"), font_family="Montserrat SemiBold")
        dlg.actions = [
            ft.TextButton("Отмена", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color=ft.Colors.with_opacity(0.8, "#FF7E1C"),
                text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_confirm),
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
            except Exception:
                self._show_error("Не удалось удалить аккаунт")
            finally:
                _close_dialog(self.page_ref, dlg)
 
        dlg.content = ft.Text(
            "Профиль, транзакции, цели и подписки будут удалены без возможности восстановления.",
            font_family="Montserrat SemiBold", color=ft.Colors.with_opacity(0.6, "#000000"))
        dlg.actions = [
            ft.TextButton("Отмена", style=ft.ButtonStyle(color="#483EB7", text_style=ft.TextStyle(font_family="Montserrat SemiBold")), on_click=on_cancel),
            ft.TextButton("Удалить аккаунт", style=ft.ButtonStyle(
                text_style=ft.TextStyle(font_family="Montserrat SemiBold"),
                color=ft.Colors.with_opacity(0.8, "#FF7E1C")), on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)
